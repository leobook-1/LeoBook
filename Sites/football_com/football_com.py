"""
Football.com Main Orchestrator
Coordinates all sub-modules to execute the complete booking workflow.
"""

import asyncio
import os
import subprocess
import sys
from datetime import datetime as dt, timedelta
from pathlib import Path
from typing import List, Dict, Optional

from playwright.async_api import Browser, Playwright

from Helpers.constants import WAIT_FOR_LOAD_STATE_TIMEOUT

from .navigator import load_or_create_session, navigate_to_schedule, select_target_date, extract_balance, log_page_title
from .extractor import extract_league_matches
from .matcher import match_predictions_with_site, filter_pending_predictions
from .booker import place_bets_for_matches, finalize_accumulator, clear_bet_slip
from Helpers.DB_Helpers.db_helpers import (
    PREDICTIONS_CSV, 
    update_prediction_status, 
    load_site_matches, 
    save_site_matches, 
    update_site_match_status,
    get_site_match_id
)
from Helpers.utils import log_error_state
from Helpers.monitor import PageMonitor


async def cleanup_chrome_processes():
    """Automatically terminate conflicting Chrome processes before launch."""
    try:
        if os.name == 'nt':
            # Windows
            subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True)
            print("  [Cleanup] Cleaned up Chrome processes.")
        else:
            # Unix-like systems
            subprocess.run(["pkill", "-f", "chrome"], capture_output=True)
            print("  [Cleanup] Cleaned up Chrome processes.")
    except Exception as e:
        print(f"  [Cleanup] Warning: Could not cleanup Chrome processes: {e}")


async def launch_browser_with_retry(playwright: Playwright, user_data_dir: Path, max_retries: int = 3):
    """Launch browser with retry logic and exponential backoff."""
    base_timeout = 60000  # 60 seconds starting timeout
    backoff_multiplier = 1.2

    for attempt in range(max_retries):
        timeout = int(base_timeout * (backoff_multiplier ** attempt))
        print(f"  [Launch] Attempt {attempt + 1}/{max_retries} with {timeout}ms timeout...")

        try:
            # Simplified, faster arguments
            chrome_args = [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--disable-infobars",
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-service-autorun",
                "--password-store=basic"
            ]

            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                headless=False,
                args=chrome_args,
                ignore_default_args=["--enable-automation"],
                viewport={'width': 375, 'height': 612}, # iPhone X
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
                timeout=timeout
            )

            print(f"  [Launch] Browser launched successfully on attempt {attempt + 1}!")
            return context

        except Exception as e:
            print(f"  [Launch] Attempt {attempt + 1} failed: {e}")

            if attempt < max_retries - 1:
                # Cleanup before next attempt
                await cleanup_chrome_processes()

                # Remove lock files
                lock_file = user_data_dir / "SingletonLock"
                if lock_file.exists():
                    try:
                        lock_file.unlink()
                        print(f"  [Launch] Removed SingletonLock before retry.")
                    except Exception as lock_e:
                        print(f"  [Launch] Could not remove lock file: {lock_e}")

                # Wait before retry with exponential backoff
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                print(f"  [Launch] Waiting {wait_time}s before next attempt...")
                await asyncio.sleep(wait_time)
            else:
                print(f"  [Launch] All {max_retries} attempts failed.")
                raise e


async def run_football_com_booking(playwright: Playwright):
    """
    Main function to handle Football.com login, match mapping, and bet placement.
    Orchestrates the entire booking workflow using modular components.
    """
    print("\n--- Running Football.com Booking (Phase 2) ---")

    # 1. Filter pending predictions
    pending_predictions = await filter_pending_predictions()
    if not pending_predictions:
        print("  [Info] No pending predictions to book.")
        return

    # Group predictions by date (only future dates)
    predictions_by_date = {}
    today = dt.now().date()
    for pred in pending_predictions:
        date_str = pred.get('date')
        if date_str:
            try:
                pred_date = dt.strptime(date_str, "%d.%m.%Y").date()
                if pred_date >= today:
                    if date_str not in predictions_by_date:
                        predictions_by_date[date_str] = []
                    predictions_by_date[date_str].append(pred)
            except ValueError:
                continue  # Skip invalid dates

    if not predictions_by_date:
        print("  [Info] No predictions found.")
        return

    print(f"  [Info] Dates with predictions: {sorted(predictions_by_date.keys())}")

    user_data_dir = Path("DB/ChromeData_v3").absolute()
    user_data_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"  [System] Launching Persistent Context for Football.com... (Data Dir: {user_data_dir})")

    # Initial cleanup
    await cleanup_chrome_processes()

    context = None
    page = None

    try:
        # Use optimized launch with retry logic
        context = await launch_browser_with_retry(playwright, user_data_dir, max_retries=3)
    except Exception as launch_e:
        print(f"  [CRITICAL ERROR] Failed to launch browser: {launch_e}")
        return

    try:
        # 2. Load or create session
        _, page = await load_or_create_session(context)
        await log_page_title(page, "Session Loaded")
        
        # Activate Vigilance
        PageMonitor.attach_listeners(page)

        # 2b. Clear any existing bets in the slip
        await clear_bet_slip(page)

        # 3. Extract balance
        balance = await extract_balance(page)
        print(f"  [Balance] Current balance: NGN {balance}")

        # 4. Process each day's predictions
        for target_date, day_predictions in sorted(predictions_by_date.items()):
            if not page or page.is_closed():
                print("  [Fatal] Browser connection lost or page closed. Aborting cycle.")
                break

            print(f"\n--- Booking Process for Date: {target_date} ---")

            # --- REGISTRY & HARVEST (Phase 2a) ---
            print("\n   [Phase 2a: Harvest] Validating matches and extracting codes...")
            
            cached_site_matches = load_site_matches(target_date)
            matched_urls = {} # fixture_id -> url
            verified_predictions = [] # List of preds that have a booking URL/code

            # 2a-1: Identify Unmatched
            unmatched_predictions = []
            for pred in day_predictions:
                fid = str(pred.get('fixture_id'))
                cached_match = next((m for m in cached_site_matches if m.get('fixture_id') == fid), None)
                
                if cached_match and cached_match.get('url'):
                    if cached_match.get('booking_status') == 'booked':
                         # Already fully booked? Reuse logic if needed
                         pass
                    
                    matched_urls[fid] = cached_match.get('url')
                    # Check if we have booked it (Harvested)
                    if cached_match.get('booking_code'):
                         print(f"    [Harvest] {fid} already has code: {cached_match.get('booking_code')}")
                         verified_predictions.append(pred)
                    else:
                         # Has URL but NO code -> Needs Harvest
                         unmatched_predictions.append(pred) # Re-purpose list for 'Needs Harvest'
                else:
                    # No URL -> Scrape -> Match -> Then Needs Harvest
                    unmatched_predictions.append(pred)

            # 2a-2: Scrape & Match Missing URLs
            # Filter distinct unconnected predictions
            preds_needing_url = [p for p in unmatched_predictions if str(p.get('fixture_id')) not in matched_urls]
            
            if preds_needing_url:
                print(f"    [Registry] {len(preds_needing_url)} predictions need URL matching...")
                try:
                    await navigate_to_schedule(page)
                    if await select_target_date(page, target_date):
                        site_matches = await extract_league_matches(page, target_date)
                        if site_matches:
                            save_site_matches(site_matches)
                            cached_site_matches = load_site_matches(target_date)
                            
                            new_mappings = await match_predictions_with_site(preds_needing_url, cached_site_matches)
                            for fid, url in new_mappings.items():
                                matched_urls[fid] = url
                                # Update registry connection
                                match_obj = next((m for m in cached_site_matches if m.get('url') == url), None)
                                if match_obj:
                                    update_site_match_status(match_obj['site_match_id'], 'pending', fixture_id=fid)
                except Exception as e:
                     print(f"    [Harvest Error] Match extraction failed: {e}")

            # 2a-3: Execute Single Booking (Harvest) for those with URL but no Code
            preds_to_harvest = [p for p in day_predictions if str(p.get('fixture_id')) in matched_urls]
            # Exclude already verified
            preds_to_harvest = [p for p in preds_to_harvest if p not in verified_predictions]

            print(f"    [Harvest] Attempting to harvest codes for {len(preds_to_harvest)} matches...")
            
            for pred in preds_to_harvest:
                fid = str(pred.get('fixture_id'))
                url = matched_urls.get(fid)
                
                # Construct composite match data
                match_data = {
                    'home_team': pred.get('home_team'), 
                    'away_team': pred.get('away_team'),
                    'url': url,
                    # Pass prediction details for mapping
                    'prediction': pred.get('prediction'),
                    'home_team_id': pred.get('home_team_id'), 
                    'away_team_id': pred.get('away_team_id')
                }

                try:
                    code, b_url = await book_single_match(page, match_data)
                    
                    if code:
                        print(f"    [Harvest] Success! {fid} -> Code: {code}")
                        # Update Registry
                        # Find site_match_id
                        match_obj = next((m for m in cached_site_matches if m.get('url') == url), None)
                        if match_obj:
                            update_site_match_status(
                                match_obj['site_match_id'], 
                                'harvested', 
                                booking_code=code, 
                                booking_url=b_url
                            )
                        verified_predictions.append(pred)
                    else:
                        print(f"    [Harvest] Failed to get code for {fid}")
                except Exception as e:
                    print(f"    [Harvest Error] {fid}: {e}")

            # --- EXECUTE (Phase 2b) ---
            print(f"\n   [Phase 2b: Execute] Building Accumulator with {len(verified_predictions)} verified selections...")
            
            if verified_predictions:
                 # Execute Booking using the matched URLs (validated by Harvest)
                 await place_bets_for_matches(page, matched_urls, verified_predictions, target_date)
            else:
                 print("    [Execute] No verified matches to book.")

    except Exception as e:
        print(f"[FATAL BOOKING ERROR] {e}")
        if page:
            await log_error_state(page, "football_com_fatal", e)
    finally:
        if context:
            await context.close()
