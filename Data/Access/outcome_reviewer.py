# outcome_reviewer.py: Post-match results extraction and accuracy reporting.
# Refactored for Clean Architecture (v2.7)
# This script updates predictions with final scores to calculate model performance.

"""
Outcome Reviewer Module
Core review processing and outcome analysis system.
Responsible for managing the review workflow, CSV operations, and outcome tracking.
"""

import asyncio
import csv
import os
import pandas as pd
import pytz
from datetime import datetime as dt, timedelta
from typing import List, Dict, Any, Optional

from .health_monitor import HealthMonitor
from playwright.async_api import Playwright


# --- CONFIGURATION ---
BATCH_SIZE = 10      # How many matches to review at the same time
LOOKBACK_LIMIT = 5000 # Only check the last 500 eligible matches to prevent infinite backlogs
ENRICHMENT_CONCURRENCY = 10 # Concurrency for enriching past H2H matches

# --- PRODUCTION CONFIGURATION ---
PRODUCTION_MODE = True  # Set to True in production environment
MAX_RETRIES = 3          # Maximum retry attempts for failed operations
HEALTH_CHECK_INTERVAL = 300  # Health check every 5 minutes
ERROR_THRESHOLD = 10     # Alert if more than 10 errors in health check window

# Version and compatibility
VERSION = "2.6.0"
COMPATIBLE_MODELS = ["2.5", "2.6"]  # Compatible with these model versions

# --- IMPORTS ---
from .db_helpers import (
    PREDICTIONS_CSV, SCHEDULES_CSV, TEAMS_CSV, REGION_LEAGUE_CSV, 
    FB_MATCHES_CSV, files_and_headers, save_team_entry, save_region_league_entry
)
from .csv_operations import upsert_entry, _read_csv, _write_csv
from .sync_manager import SyncManager
from Core.Intelligence.intelligence import get_selector_auto, get_selector


def _load_schedule_db() -> Dict[str, Dict]:
    """Loads the schedules.csv into a dictionary for quick lookups."""
    schedule_db = {}
    if not os.path.exists(SCHEDULES_CSV):
        return {}
    with open(SCHEDULES_CSV, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('fixture_id'):
                schedule_db[row['fixture_id']] = row
    return schedule_db


def get_predictions_to_review() -> List[Dict]:
    """
    Reads the predictions CSV using pandas and returns a list of matches that 
    are in the past (Africa/Lagos timezone) and still have a 'pending' status.
    """
    if not os.path.exists(PREDICTIONS_CSV):
        print(f"[Error] Predictions file not found at: {PREDICTIONS_CSV}")
        return []

    try:
        # 1. Load predictions with pandas
        df = pd.read_csv(PREDICTIONS_CSV, dtype=str).fillna('')
        
        if df.empty:
            return []

        # 2. Filter for 'pending' status
        df = df[df['status'] == 'pending']
        if df.empty:
            return []

        # 3. Handle Date/Time Parsing
        # Format in CSV is 14.02.2026 for date, 15:00 for match_time
        def parse_dt(row):
            try:
                d_str = row.get('date') or row.get('Date')
                t_str = row.get('match_time')
                if not d_str or not t_str or t_str == 'N/A':
                    return pd.NaT
                return dt.strptime(f"{d_str} {t_str}", "%d.%m.%Y %H:%M")
            except:
                return pd.NaT

        df['scheduled_dt'] = df.apply(parse_dt, axis=1)
        df = df.dropna(subset=['scheduled_dt'])

        # 4. Timezone Awareness (Africa/Lagos)
        lagos_tz = pytz.timezone('Africa/Lagos')
        now_lagos = dt.now(lagos_tz)
        
        # Localize scheduled_dt if naive (usually it is)
        df['scheduled_dt'] = df['scheduled_dt'].apply(lambda x: lagos_tz.localize(x) if x.tzinfo is None else x)

        # 5. Filter for past matches (scheduled_time < current_time)
        to_review_df = df[df['scheduled_dt'] < now_lagos]
        
        # Limit to LOOKBACK_LIMIT
        if len(to_review_df) > LOOKBACK_LIMIT:
            to_review_df = to_review_df.tail(LOOKBACK_LIMIT)

        # Return as list of dicts
        return to_review_df.to_dict('records')

    except Exception as e:
        print(f"[Error] get_predictions_to_review logic failed: {e}")
        return []

def get_schedules_to_update(full_refresh=False) -> List[Dict]:
    """
    Reads the schedules CSV and returns entries that need enrichment.
    """
    if not os.path.exists(SCHEDULES_CSV):
        return []

    to_update = []
    with open(SCHEDULES_CSV, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if full_refresh:
                to_update.append(row)
                continue
            
            # Enrich if missing URLs or status is unknown
            status = row.get('status', row.get('match_status', '')).lower()
            if not row.get('match_link'):
                continue
                
            if status in ['', 'scheduled', 'pending', 'unknown'] or not row.get('home_team_id'):
                to_update.append(row)

    print(f"[Chapter 0] Found {len(to_update)} schedule entries to enrich/update.")
    return to_update

def smart_parse_datetime(dt_str: str):
    """
    Attempts to parse date/time which might be merged or in various formats.
    Example: '12.02.2026 15:00' or '12.02.202615:00'
    """
    dt_str = dt_str.strip()
    # Remove day of week if present (e.g. 'Thu 12.02.2026')
    if len(dt_str) > 10 and not dt_str[0].isdigit():
        dt_str = " ".join(dt_str.split()[1:])

    # Handle merged: 12.02.202615:00 -> 12.02.2026 15:00
    if len(dt_str) == 15 and dt_str[10].isdigit():
        dt_str = dt_str[:10] + " " + dt_str[10:]
    
    try:
        # Standard format
        parts = dt_str.split()
        if len(parts) == 2:
            d_part, t_part = parts
            # Keep original DD.MM.YYYY for local CSV compatibility
            # (SyncManager handles YYYY-MM-DD conversion for Supabase)
            return d_part, t_part
    except:
        pass
    return None, None


def save_single_outcome(match_data: Dict, new_status: str):
    """
    Atomic Upsert to save the review result.
    """
    temp_file = PREDICTIONS_CSV + '.tmp'
    updated = False
    row_id_key = 'ID' if 'ID' in match_data else 'fixture_id'
    target_id = match_data.get(row_id_key)

    try:
        with open(PREDICTIONS_CSV, 'r', encoding='utf-8', newline='') as infile, \
             open(temp_file, 'w', encoding='utf-8', newline='') as outfile:

            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames
            if fieldnames is None: 
                fieldnames = files_and_headers[PREDICTIONS_CSV]

            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                current_id = row.get('ID') or row.get('fixture_id')

                if current_id == target_id:
                    row['status'] = new_status
                    row['actual_score'] = match_data.get('actual_score', row.get('actual_score', 'N/A'))
                    
                    # Update scores if available in match_data (from schedules)
                    if 'home_score' in match_data and 'away_score' in match_data:
                        row['actual_score'] = f"{match_data['home_score']}-{match_data['away_score']}"

                    if new_status in ['reviewed', 'finished']:
                        from .review_outcomes import evaluate_prediction as final_eval
                        prediction = row.get('prediction', '')
                        actual_score = row.get('actual_score', '')
                        
                        try:
                            h_core, a_core = actual_score.split('-')
                            is_correct = final_eval(prediction, h_core, a_core)
                            row['outcome_correct'] = str(is_correct)
                            
                            # Immediate Sync (Real-time update)
                            print(f"      [Cloud] Immediate sync for {target_id}...")
                            asyncio.create_task(SyncManager().batch_upsert('predictions', [row]))
                        except Exception as eval_err:
                            print(f"      [Eval Error] {eval_err}")

                    updated = True

                writer.writerow(row)

        if updated:
            os.replace(temp_file, PREDICTIONS_CSV)
            if new_status == 'reviewed' and target_id:
                _sync_outcome_to_site_registry(target_id, match_data)
        else:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    except Exception as e:
        HealthMonitor.log_error("csv_save_error", f"Failed to save CSV: {e}", "high")
        print(f"    [File Error] Failed to write CSV: {e}")

def sync_schedules_to_predictions():
    """
    Ensures all entries in schedules.csv exist in predictions.csv.
    """
    if not os.path.exists(SCHEDULES_CSV) or not os.path.exists(PREDICTIONS_CSV):
        return

    schedules = _read_csv(SCHEDULES_CSV)
    predictions = _read_csv(PREDICTIONS_CSV)
    pred_ids = {p.get('fixture_id') for p in predictions if p.get('fixture_id')}

    added_count = 0
    for s in schedules:
        fid = s.get('fixture_id')
        if fid and fid not in pred_ids:
            # Create a shell prediction entry
            new_pred = {
                'fixture_id': fid,
                'date': s.get('date'),
                'match_time': s.get('match_time'),
                'region_league': s.get('region_league'),
                'home_team': s.get('home_team'),
                'away_team': s.get('away_team'),
                'home_team_id': s.get('home_team_id'),
                'away_team_id': s.get('away_team_id'),
                'prediction': 'PENDING',
                'confidence': 'Low',
                'status': s.get('status', 'pending'),
                'match_link': s.get('match_link'),
                'actual_score': f"{s.get('home_score', '')}-{s.get('away_score', '')}" if s.get('home_score') else 'N/A'
            }
            upsert_entry(PREDICTIONS_CSV, new_pred, files_and_headers[PREDICTIONS_CSV], 'fixture_id')
            added_count += 1
    
    if added_count > 0:
        print(f"  [Sync] Added {added_count} missing entries from schedules to predictions.")


def _sync_outcome_to_site_registry(fixture_id: str, match_data: Dict):
    """v2.7 Sync: Updates fb_matches.csv when a prediction is reviewed."""
    if not os.path.exists(FB_MATCHES_CSV):
        return

    try:
        # 1. Determine WON/LOST
        actual_score = match_data.get('actual_score', '')
        prediction = match_data.get('prediction', '')
        home_team = match_data.get('home_team', '')
        away_team = match_data.get('away_team', '')
        
        is_correct = evaluate_prediction(prediction, actual_score, home_team, away_team)
        if is_correct is None: return
        
        outcome_status = "WON" if is_correct else "LOST"
        
        # 2. Update site registry
        rows = _read_csv(FB_MATCHES_CSV)
        sync_count = 0
        for row in rows:
            if str(row.get('fixture_id')) == str(fixture_id):
                row['status'] = outcome_status
                sync_count += 1
        
        if sync_count > 0:
            _write_csv(FB_MATCHES_CSV, rows, files_and_headers[FB_MATCHES_CSV])
            print(f"    [Sync] Updated {sync_count} records in fb_matches.csv to {outcome_status}")
            
    except Exception as e:
        print(f"    [Sync Error] Failed to sync outcome: {e}")


async def process_enrichment_task(match: Dict, browser, semaphore: asyncio.Semaphore) -> None:
    """
    Task to enrich a schedule entry with full match details.
    """
    async with semaphore:
        from playwright.async_api import async_playwright
        from Core.Browser.site_helpers import fs_universal_popup_dismissal
        from Core.Utils.utils import log_error_state
        from Core.Intelligence.intelligence import get_selector_auto, get_selector

        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        await context.route("**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2}", lambda route: route.abort())
        page = await context.new_page()

        url = match.get('match_link')
        if not url:
            await context.close()
            return

        if not url.startswith('http'):
            url = f"https://www.flashscore.com{url}"

        try:
            print(f"  [Enriching] {match.get('home_team')} vs {match.get('away_team')}")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await fs_universal_popup_dismissal(page)

            # --- 1. Extract Detailed Status & Score ---
            status_text = "Scheduled"
            try:
                status_sel = "div.fixedHeaderDuel__detailStatus"
                status_text = await page.locator(status_sel).first.inner_text(timeout=5000)
            except:
                pass
            
            final_score = await get_final_score(page)
            
            # --- 2. Extract Team Info ---
            home_team_link = page.locator("a.duelParticipant__home a.participant__participantName").first
            away_team_link = page.locator("a.duelParticipant__away a.participant__participantName").first
            
            try:
                home_url = await home_team_link.get_attribute('href', timeout=5000)
                home_name = await home_team_link.inner_text()
                home_id = home_url.split('/')[-2] if home_url else ''
                
                away_url = await away_team_link.get_attribute('href', timeout=5000)
                away_name = await away_team_link.inner_text()
                away_id = away_url.split('/')[-2] if away_url else ''
                
                if home_id:
                    save_team_entry({
                        'team_id': home_id,
                        'team_name': home_name,
                        'team_url': home_url,
                        'rl_ids': match.get('region_league')
                    })
                if away_id:
                    save_team_entry({
                        'team_id': away_id,
                        'team_name': away_name,
                        'team_url': away_url,
                        'rl_ids': match.get('region_league')
                    })
                
                match['home_team_id'] = home_id
                match['away_team_id'] = away_id
            except:
                pass

            # --- 3. Extract League Info ---
            try:
                # Breadcrumbs: Flashscore.com / Football / ENGLAND / Premier League
                breadcrumb_sel = "span.breadcrumb__item"
                items = await page.locator(breadcrumb_sel).all_inner_texts()
                if len(items) >= 4:
                    region = items[2].strip()
                    league = items[3].strip()
                    
                    league_link = page.locator("span.breadcrumb__item >> a").last
                    league_url = await league_link.get_attribute('href')
                    
                    save_region_league_entry({
                        'region': region,
                        'league': league,
                        'league_url': league_url
                    })
                    match['region_league'] = f"{region}: {league}"
            except:
                pass

            # --- 4. Smart Date/Time Detection ---
            try:
                dt_sel = "div.duelParticipant__startTime"
                dt_text = await page.locator(dt_sel).inner_text()
                std_date, std_time = smart_parse_datetime(dt_text)
                if std_date:
                    match['date'] = std_date
                    match['match_time'] = std_time
            except:
                pass

            # Finalize status mapping
            if "finish" in status_text.lower() or "ft" in status_text.lower():
                match['status'] = 'FINISHED'
                if final_score and '-' in final_score:
                    parts = final_score.split('-')
                    match['home_score'] = parts[0]
                    match['away_score'] = parts[1]
            elif "postp" in status_text.lower():
                match['status'] = 'POSTPONED'
            elif "canc" in status_text.lower():
                match['status'] = 'CANCELED'
            elif "live" in status_text.lower():
                match['status'] = 'LIVE'
            else:
                match['status'] = 'SCHEDULED'

            # Upsert back to schedules.csv
            upsert_entry(SCHEDULES_CSV, match, files_and_headers[SCHEDULES_CSV], 'fixture_id')
            print(f"    [Updated] {match.get('fixture_id')}: {match['status']} {final_score or ''}")

        except Exception as e:
            print(f"    [Error] Enrichment failed for {match.get('fixture_id')}: {e}")
        finally:
            await context.close()


async def process_review_task(match: Dict, browser, semaphore: asyncio.Semaphore) -> Optional[Dict]:
    """
    Task to review a single past prediction using an isolated context.
    Returns the updated match dict if successful for batch syncing.
    """
    async with semaphore:
        from Core.Browser.site_helpers import fs_universal_popup_dismissal

        # isolated headless context
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        await context.route("**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2}", lambda route: route.abort())
        page = await context.new_page()

        url = match.get('match_link')
        if not url:
            save_single_outcome(match, 'review_failed')
            await context.close()
            return None

        if not url.startswith('http'):
            url = f"https://www.flashscore.com{url}"

        try:
            print(f"  [Reviewing] {match.get('home_team')} vs {match.get('away_team')}")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await fs_universal_popup_dismissal(page)

            final_score = await get_final_score(page)
            
            if final_score == "Error":
                save_single_outcome(match, 'review_failed')
                return None
            elif final_score == "Match_POSTPONED":
                save_single_outcome(match, 'match_postponed')
                return None
            elif final_score != "NOT_FINISHED":
                match['actual_score'] = final_score
                # Update status to 'finished' as requested
                save_single_outcome(match, 'finished')
                print(f"    [Result] {match.get('home_team')} {final_score} {match.get('away_team')}", flush=True)
                return match

            return None

        except Exception as e:
            print(f"    [Error] Review failed: {e}")
            save_single_outcome(match, 'review_failed')
            return None
        finally:
            await context.close()


async def get_league_url(page):
    """
    Extracts the league URL from the match page. Returns empty string if not found.
    """
    try:
        # Look for breadcrumb links to league
        league_link_sel = "a[href*='/football/'][href$='/']"
        league_link = page.locator(league_link_sel).first
        # Use shorter timeout to prevent hanging
        LEAGUE_TIMEOUT = 10000  # 10 seconds
        href = await league_link.get_attribute('href', timeout=LEAGUE_TIMEOUT)
        if href:
            return href
    except:
        pass
    return ""


async def get_final_score(page):
    """
    Extracts the final score. Returns 'Error' if not found.
    """
    try:
        # Check Status
        status_selector = get_selector("fs_match_page", "meta_match_status") or "div.fixedHeaderDuel__detailStatus"
        try:
            from Core.Utils.constants import WAIT_FOR_LOAD_STATE_TIMEOUT
            status_text = await page.locator(status_selector).first.inner_text(timeout=30000)
            ERROR_HEADER = page.get_by_text("Error:", exact=True)
            ERROR_MESSAGE = page.get_by_text("The requested page can't be displayed. Please try again later.")
            
            if "postponed" in status_text.lower():
                return "Match_POSTPONED"   

            # Check if both are visible
            is_error_visible = (await ERROR_HEADER.is_visible()) and (await ERROR_MESSAGE.is_visible())
            if is_error_visible:
                return "Error"
            
        except:             
            status_text = "finished"

        if "finished" not in status_text.lower() and "aet" not in status_text.lower() and "pen" not in status_text.lower():
            return "NOT_FINISHED"

        # Extract Score
        home_score_sel = get_selector("fs_match_page", "header_score_home") or "div.detailScore__wrapper > span:nth-child(1)"
        away_score_sel = get_selector("fs_match_page", "header_score_away") or "div.detailScore__wrapper > span:nth-child(3)"

        # Use shorter timeout for score extraction to prevent hanging
        SCORE_TIMEOUT = 30000  # 30 seconds
        home_score = await page.locator(home_score_sel).first.inner_text(timeout=SCORE_TIMEOUT)
        away_score = await page.locator(away_score_sel).first.inner_text(timeout=SCORE_TIMEOUT)

        final_score = f"{home_score.strip() if home_score else ''}-{away_score.strip() if away_score else ''}"
        return final_score

    except Exception as e:
        HealthMonitor.log_error("score_extraction_error", f"Failed to extract score: {e}", "medium")
        return "Error"


def update_region_league_url(region_league: str, url: str):
    """
    Updates the url for a region_league in region_league.csv.
    Parses the region_league string to create proper region_league_id.
    """
    if not region_league or not url or " - " not in region_league:
        return

    # Ensure URL is absolute
    if url.startswith('/'):
        url = f"https://www.flashscore.com{url}"

    # Parse region and league from "REGION - LEAGUE" format
    region, league_name = region_league.split(" - ", 1)

    # Create composite ID matching the save_region_league_entry format
    region_league_id = f"{region}_{league_name}".replace(' ', '_').replace('-', '_').upper()

    entry = {
        'region_league_id': region_league_id,
        'region': region.strip(),
        'league_name': league_name.strip(),
        'url': url
    }
    upsert_entry(REGION_LEAGUE_CSV, entry, files_and_headers[REGION_LEAGUE_CSV], 'region_league_id')


async def run_review_process(playwright: Playwright):
    """Main review process orchestration"""
    print("--- LEO V2.6: Outcome Review Engine (Concurrent) ---")
    
    # 1. Review Predictions (Calculates model accuracy)
    matches_to_review = get_predictions_to_review()
    
    # 2. Enrich Schedules (Chapter 0 upgrade)
    schedules_to_update = get_schedules_to_update()

    if not matches_to_review and not schedules_to_update:
        print("--- Nothing to review or enrich. ---")
        return

    browser = await playwright.chromium.launch(
        headless=True,
        args=["--disable-dev-shm-usage", "--no-sandbox", "--disable-gpu"]
    )

    try:
        sem = asyncio.Semaphore(BATCH_SIZE)
        
        if matches_to_review:
            print(f"[Processing] Starting concurrent review for {len(matches_to_review)} matches...")
            sync_manager = SyncManager()
            
            # Process reviews in batches to handle periodic sync
            for i in range(0, len(matches_to_review), 10):
                batch_chunk = matches_to_review[i:i+10]
                tasks = [asyncio.create_task(process_review_task(m, browser, sem)) for m in batch_chunk]
                results = await asyncio.gather(*tasks)
                
                # Filter successful results for sync
                reviewed_rows = [r for r in results if r is not None]
                if reviewed_rows:
                    print(f"   [Sync] Periodic Upsert: Sending {len(reviewed_rows)} reviewed entries to Cloud...", flush=True)
                    await sync_manager.batch_upsert('predictions', reviewed_rows)

        # 1. Enrichment tasks (if any)
        if schedules_to_update:
            print(f"[Processing] Starting batch enrichment for {len(schedules_to_update)} schedules...", flush=True)
            enrich_tasks = [asyncio.create_task(process_enrichment_task(s, browser, sem)) for s in schedules_to_update]
            await asyncio.gather(*enrich_tasks)

        # 3. Final Sync
        sync_schedules_to_predictions()

        # Update learning weights based on reviewed outcomes
        if matches_to_review:
            try:
                from Core.Intelligence.model import update_learning_weights
                updated_weights = update_learning_weights()
                print(f"--- Learning Engine: Updated {len(updated_weights)-1} rule weights ---")
            except Exception as e:
                HealthMonitor.log_error("learning_update_error", f"Failed to update learning weights: {e}", "medium")
                print(f"--- Learning Engine Error: {e} ---")
            
    finally:
        await browser.close()

    # 4. Accuracy Generation (Prologue Page 3)
    try:
        from .review_outcomes import run_accuracy_generation
        await run_accuracy_generation()
    except Exception as e:
        print(f"--- Accuracy Generation Error: {e} ---")

    print("--- Review Process Complete ---")
