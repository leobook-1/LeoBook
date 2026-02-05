# manager.py: Orchestration layer for Flashscore data extraction.
# Refactored for Clean Architecture (v2.7)
# This script coordinates schedule harvesting, match extraction, and result reviews.

"""
Flashscore Orchestrator
Pure coordinator of Phase 1 Analysis.
"""

import asyncio
from datetime import datetime as dt, timedelta
from zoneinfo import ZoneInfo
from playwright.async_api import Playwright

from Data.Access.db_helpers import (
    get_last_processed_info, save_schedule_entry, save_team_entry
)
from Core.Browser.site_helpers import fs_universal_popup_dismissal, click_next_day
from Core.Utils.utils import BatchProcessor
from Core.Utils.monitor import PageMonitor
from Core.Intelligence.selector_manager import SelectorManager
from Scripts.recommend_bets import get_recommendations
from Core.Utils.constants import NAVIGATION_TIMEOUT, WAIT_FOR_LOAD_STATE_TIMEOUT

# Modular Imports
from .fs_schedule import extract_matches_from_page
from .fs_processor import process_match_task
from .fs_offline import run_flashscore_offline_repredict

NIGERIA_TZ = ZoneInfo("Africa/Lagos")

async def run_flashscore_analysis(playwright: Playwright):
    """
    Main function to handle Flashscore data extraction and analysis.
    Coordinates browser launch, navigation, schedule extraction, and batch processing.
    """
    print("\n--- Running Flashscore Analysis ---")

    browser = await playwright.chromium.launch(
        headless=True,
        args=["--disable-dev-shm-usage", "--no-sandbox", "--disable-gpu"]
    )

    context = None
    try:
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            timezone_id="Africa/Lagos"
        )
        page = await context.new_page()
        PageMonitor.attach_listeners(page)
        processor = BatchProcessor(max_concurrent=5)

        total_cycle_predictions = 0

        # --- Navigation ---
        print("  [Navigation] Going to Flashscore...")
        for attempt in range(5):
            try:
                await page.goto("https://www.flashscore.com/football/", wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT)
                print("  [Navigation] Flashscore loaded successfully.")
                break 
            except Exception as e:
                print(f"  [Navigation Error] Attempt {attempt + 1}/5 failed: {e}")
                if attempt < 4:
                    await asyncio.sleep(5)
                else:
                    print(f"  [Critical] All navigation attempts failed.")
                    await context.close()
                    return
                    
        await fs_universal_popup_dismissal(page, "fs_home_page")

        last_processed_info = get_last_processed_info()

        # --- Daily Loop ---
        for day_offset in range(1):
            target_date = dt.now(NIGERIA_TZ) + timedelta(days=day_offset)
            target_full = target_date.strftime("%d.%m.%Y")
            
            if day_offset > 0:
                match_row_sel = await SelectorManager.get_selector_auto(page, "fs_home_page", "match_rows")
                if not match_row_sel or not await click_next_day(page, match_row_sel):
                    break
                await asyncio.sleep(2)

            if last_processed_info.get('date_obj') and target_date.date() < last_processed_info['date_obj']:
                continue

            print(f"\n--- ANALYZING DATE: {target_full} ---")
            await fs_universal_popup_dismissal(page, "fs_home_page")

            try:
                scheduled_tab_sel = await SelectorManager.get_selector_auto(page, "fs_home_page", "tab_scheduled")
                if scheduled_tab_sel and await page.locator(scheduled_tab_sel).is_visible(timeout=WAIT_FOR_LOAD_STATE_TIMEOUT):
                    await page.click(scheduled_tab_sel)
                    await asyncio.sleep(2.0)
            except Exception:
                pass

            await fs_universal_popup_dismissal(page, "fs_home_page")
            matches_data = await extract_matches_from_page(page)
            
            # --- Cleaning & Sorting ---
            for m in matches_data:
                original_time_str = m.get('time')
                if original_time_str:
                    clean_time_str = original_time_str.split('\n')[0].strip()
                    m['time'] = clean_time_str if clean_time_str and clean_time_str != 'N/A' else 'N/A'

            matches_data.sort(key=lambda x: x.get('time', '23:59'))

            # --- Save to DB & Filter ---
            valid_matches = []
            now_time = dt.now(NIGERIA_TZ).time()
            is_today = target_date.date() == dt.now(NIGERIA_TZ).date()

            for m in matches_data:
                m['date'] = target_full
                save_schedule_entry({
                    'fixture_id': m.get('id'), 'date': m.get('date'), 'match_time': m.get('time'),
                    'region_league': m.get('region_league'), 'home_team': m.get('home_team'),
                    'away_team': m.get('away_team'), 'home_team_id': m.get('home_team_id'),
                    'away_team_id': m.get('away_team_id'), 'match_status': 'scheduled',
                    'match_link': m.get('match_link')
                })
                save_team_entry({'team_id': m.get('home_team_id'), 'team_name': m.get('home_team'), 'region_league': m.get('region_league'), 'team_url': m.get('home_team_url')})
                save_team_entry({'team_id': m.get('away_team_id'), 'team_name': m.get('away_team'), 'region_league': m.get('region_league'), 'team_url': m.get('away_team_url')})

                if is_today:
                    try:
                        if m.get('time') and m['time'] != 'N/A' and dt.strptime(m['time'], '%H:%M').time() > now_time:
                            valid_matches.append(m)
                    except ValueError:
                        pass
                else:
                    valid_matches.append(m)

            print(f"    [Matches Found] {len(valid_matches)} valid fixtures.")

            # --- Resume Logic ---
            if last_processed_info.get('date') == target_full:
                last_id = last_processed_info.get('id')
                try:
                    found_index = [i for i, match in enumerate(valid_matches) if match.get('id') == last_id][0]
                    valid_matches = valid_matches[found_index + 1:]
                except IndexError:
                    pass

            # --- Batch Processing ---
            if valid_matches:
                print(f"    [Batching] Processing {len(valid_matches)} matches concurrently...")
                results = await processor.run_batch(valid_matches, process_match_task, browser=browser)
                total_cycle_predictions += sum(1 for r in results if r)
            else:
                print("    [Info] No new matches to process.")

    finally:
        if context is not None:
            await context.close()
        if 'browser' in locals():
             await browser.close()
             
    print(f"\n--- Flashscore Analysis Complete: {total_cycle_predictions} new predictions found. ---")
    
    # Trigger Recommendations
    print("\n   [Auto] Generating betting recommendations for today...")
    get_recommendations(save_to_file=True)

