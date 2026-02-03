# Sites/flashscore.py

import re
import asyncio
from datetime import datetime as dt, timedelta
from zoneinfo import ZoneInfo

from playwright.async_api import Browser, Page, Playwright

from Helpers.DB_Helpers.db_helpers import (
    get_last_processed_info, save_schedule_entry, save_team_entry, 
    save_standings, save_region_league_entry, save_prediction,
    get_all_schedules, get_standings
)
from Helpers.Site_Helpers.site_helpers import fs_universal_popup_dismissal, click_next_day
from Helpers.utils import BatchProcessor, log_error_state
from Neo.intelligence import analyze_page_and_update_selectors, get_selector_auto
from Neo.selector_manager import SelectorManager
from Helpers.Site_Helpers.Extractors.h2h_extractor import extract_h2h_data, save_extracted_h2h_to_schedules, activate_h2h_tab
from Helpers.Site_Helpers.Extractors.standings_extractor import extract_standings_data, activate_standings_tab
from Neo.model import RuleEngine
from Helpers.constants import NAVIGATION_TIMEOUT, WAIT_FOR_LOAD_STATE_TIMEOUT
from Helpers.monitor import PageMonitor
from Scripts.recommend_bets import get_recommendations

# --- CONFIGURATION ---
NIGERIA_TZ = ZoneInfo("Africa/Lagos")

# --- RETRY CONFIGURATION ---
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
import logging

# --- RETRY CONFIGURATION ---
# Robust retry configuration using Tenacity
def log_retry_attempt(retry_state):
    print(f"      [Retry] Extraction failed (attempt {retry_state.attempt_number}), retrying...")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1.5, min=4, max=15),
    retry=retry_if_exception_type(Exception),
    before_sleep=log_retry_attempt
)
async def extract_h2h_with_retry(page, home_team, away_team):
    """Robust H2H extraction with backoff."""
    if await activate_h2h_tab(page):
        return await extract_h2h_data(page, home_team, away_team)
    return {}

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1.5, min=4, max=15),
    retry=retry_if_exception_type(Exception),
     before_sleep=log_retry_attempt
)
async def extract_standings_with_retry(page, match_label):
    """Robust Standings extraction with backoff."""
    if await activate_standings_tab(page, match_label):
        return await extract_standings_data(page, match_label)
    return []


async def process_match_task(match_data: dict, browser: Browser):
    """
    Worker function to process a single match in a new page/context.
    """
    # Optimize context creation
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36",
        timezone_id="Africa/Lagos",
        viewport={"width": 360, "height": 800} # Mobile viewport
    )
    # Block heavy resources
    await context.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2}", lambda route: route.abort())
    
    page = await context.new_page()
    PageMonitor.attach_listeners(page)
    match_label = f"{match_data.get('home_team', 'unknown')}_vs_{match_data.get('away_team', 'unknown')}"

    try:
        print(f"    [Batch Start] {match_data['home_team']} vs {match_data['away_team']}")
        
        # Initialize results to avoid UnboundLocalError
        h2h_data = {}
        standings_data = []
        standings_league = "Unknown"

        full_match_url = f"{match_data['match_link']}"
        await page.goto(full_match_url, wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT)
        
        # --- H2H Extraction ---
        try:
            h2h_data = await extract_h2h_with_retry(page, match_data.get('home_team'), match_data.get('away_team'))
            # Save H2H immediately to avoid data loss
            if h2h_data:
                await save_extracted_h2h_to_schedules(h2h_data)
        except Exception as e:
            print(f"    [H2H Fail] Could not extract H2H after retries for {match_label}: {e}")
            h2h_data = {}

        # --- Standings Extraction ---
        try:
            standings_result = await extract_standings_with_retry(page, match_label)
            standings_data = standings_result.get("standings", [])
            standings_league = standings_result.get("region_league", "Unknown")
            
            if standings_result.get("has_draw_table"):
                print(f"      [Skip] Match has draw table, skipping.")
                return False
                
            if standings_data and standings_league != "Unknown":
                save_standings(standings_data, standings_league)
        except Exception as e:
            print(f"    [Standings Fail] Could not extract Standings for {match_label}: {e}")
            standings_data = []

        # --- Process Data & Predict ---
        h2h_league = h2h_data.get("region_league", "Unknown")
        final_league = standings_league if standings_league != "Unknown" else h2h_league

        if final_league != "Unknown":
            match_data["region_league"] = final_league

            # Parse region and league to save to region_league.csv
            if " - " in final_league:
                region, league = final_league.split(" - ", 1)
                save_region_league_entry({
                    'region': region.strip(),
                    'league_name': league.strip()
                })

        analysis_input = {
            "match_data": match_data,
            "h2h_data": h2h_data, 
            "standings": standings_data
        }
        prediction = RuleEngine.analyze(analysis_input)

        if prediction.get("type", "SKIP") != "SKIP":
            save_prediction(match_data, prediction)
            print(f"    [Prediction] {match_data['home_team']} vs {match_data['away_team']} -> {prediction['type']} ({prediction['confidence']})")
            return True
        else:
            print(f"      [NO Signal] {match_label}")
            return False

    except Exception as e:
        print(f"      [Error] Match failed {match_label}: {e}")
        await log_error_state(page, f"process_match_task_{match_label}", str(e))
    finally:
        try:
            await asyncio.sleep(1.0) # Optimized from 5.0
            if context:
                await context.close()
        except:
            pass



async def extract_matches_from_page(page: Page) -> list:
    """
    Executes JavaScript on the page to extract all match data for the visible day.
    Ensures all selectors are up to date before extraction.
    """
    print("    [Extractor] Extracting match data from page...")
    # Batch update all selectors for fs_home_page context before use
    #await analyze_page_and_update_selectors(page, "fs_home_page", force_refresh=False)

    selectors = {
        "match_rows": SelectorManager.get_selector("fs_home_page", "match_rows"),
        "match_row_home_team_name": SelectorManager.get_selector("fs_home_page", "match_row_home_team_name"),
        "match_row_away_team_name": SelectorManager.get_selector("fs_home_page", "match_row_away_team_name"),
        "league_header": SelectorManager.get_selector("fs_home_page", "league_header"),
        "league_category": SelectorManager.get_selector("fs_home_page", "league_category"),
        "league_title": SelectorManager.get_selector("fs_home_page", "league_title_link"),
    }

    return await page.evaluate(
        r"""(selectors) => {
            const matches = [];
            const rows = document.querySelectorAll(selectors.match_rows);

            rows.forEach((row) => {
                const linkEl = row.querySelector('a.eventRowLink') || row.querySelector('a');
                const homeEl = selectors.match_row_home_team_name ? row.querySelector(selectors.match_row_home_team_name) : null;
                let skip_match = false;
                const awayEl = selectors.match_row_away_team_name ? row.querySelector(selectors.match_row_away_team_name) : null;
                const timeEl = row.querySelector('.event__time');
                const rowId = row.getAttribute('id');
                const cleanId = rowId ? rowId.replace('g_1_', '') : null;

                let regionLeague = 'Unknown';
                try {
                    let prev = row.previousElementSibling;
                    while (prev) {
                        if ((selectors.league_header && prev.matches(selectors.league_header)) || prev.classList.contains('event__header')) {
                            const regionEl = selectors.league_category ? prev.querySelector(selectors.league_category) : prev.querySelector('.event__title--type');
                            const leagueEl = selectors.league_title ? prev.querySelector(selectors.league_title) : prev.querySelector('.event__title--name');
                            if (regionEl && leagueEl) {
                                regionLeague = regionEl.innerText.trim() + ' - ' + leagueEl.innerText.trim();
                                const headerText = prev.innerText.toLowerCase();
                                if (headerText.includes('draw')) {
                                    skip_match = true;
                                }
                            } else {
                                regionLeague = prev.innerText.trim().replace(/[\\r\\n]+/g, ' - ');
                            }
                            break;
                        }
                        prev = prev.previousElementSibling;
                    }
                } catch (e) {
                    regionLeague = 'Error Extracting';
                }
                if (linkEl && homeEl && awayEl && cleanId && !skip_match) {
                    const matchLink = linkEl.getAttribute('href');

                    let homeTeamId = null;
                    let awayTeamId = null;
                    let homeTeamUrl = null;
                    let awayTeamUrl = null;

                    if (matchLink) {
                        // 1. Clean the link to handle both relative and absolute URLs
                        // This regex removes everything up to and including "/match/football/"
                        const cleanPath = matchLink.replace(/^(.*\/match\/football\/)/, '');

                        // 2. Now split only the remaining parts (Teams and IDs)
                        // cleanPath is now "gardnersville-ENOwpmY9/heaven-eleven-rZt0bocF/?mid=dzjg0ibm"
                        const parts = cleanPath.split('/').filter(p => p);

                        if (parts.length >= 2) {
                            const homeSegment = parts[0]; // Now this is correctly "gardnersville-ENOwpmY9"
                            const awaySegment = parts[1]; // Now this is correctly "heaven-eleven-rZt0bocF"

                            // Your extraction logic remains the same and is correct:
                            const homeSlug = homeSegment.substring(0, homeSegment.lastIndexOf('-'));
                            homeTeamId = homeSegment.substring(homeSegment.lastIndexOf('-') + 1);

                            const awaySlug = awaySegment.substring(0, awaySegment.lastIndexOf('-'));
                            awayTeamId = awaySegment.substring(awaySegment.lastIndexOf('-') + 1);

                            homeTeamUrl = `https://www.flashscore.com/team/${homeSlug}/${homeTeamId}/`;
                            awayTeamUrl = `https://www.flashscore.com/team/${awaySlug}/${awayTeamId}/`;
                        }
                    }


                    matches.push({
                        id: cleanId,
                        match_link: matchLink,
                        home_team_id: homeTeamId, away_team_id: awayTeamId,
                        home_team_url: homeTeamUrl, away_team_url: awayTeamUrl,
                        home_team: homeEl.innerText.trim(), away_team: awayEl.innerText.trim(),
                        time: timeEl ? timeEl.innerText.trim() : 'N/A',
                        region_league: regionLeague
                    });
                }
            });
            return matches;
        }""", selectors)


async def run_flashscore_analysis(playwright: Playwright):
    """
    Main function to handle Flashscore data extraction and analysis.
    """
    print("\n--- Running Flashscore Analysis ---")

    browser = await playwright.chromium.launch(
        headless=True,
        args=["--disable-dev-shm-usage", "--no-sandbox", "--disable-gpu"]
    )

    context = None
    try:
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            ),
            timezone_id="Africa/Lagos"
        )
        page = await context.new_page()
        PageMonitor.attach_listeners(page)
        processor = BatchProcessor(max_concurrent=5)

        total_cycle_predictions = 0

        # --- Navigation & Calibration ---
        print("  [Navigation] Going to Flashscore...")
        # Retry loop for initial navigation to handle network flakes and bot detection
        MAX_RETRIES = 5
        for attempt in range(MAX_RETRIES):
            try:
                await page.goto("https://www.flashscore.com/football/", wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT)
                print("  [Navigation] Flashscore loaded successfully.")
                break  # Exit loop on success
            except Exception as e:
                print(f"  [Navigation Error] Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    print("  Retrying in 5 seconds...")
                    await asyncio.sleep(5)
                else:
                    print(f"  [Critical] All navigation attempts failed. Exiting analysis.")
                    await context.close()
                    return
                    
        #await analyze_page_and_update_selectors(page, "fs_home_page")
        await fs_universal_popup_dismissal(page, "fs_home_page")

        last_processed_info = get_last_processed_info()

        # --- Daily Loop ---
        for day_offset in range(1):
            target_date = dt.now(NIGERIA_TZ) + timedelta(days=day_offset)
            target_full = target_date.strftime("%d.%m.%Y")
            
            if day_offset > 0:
                match_row_sel = await SelectorManager.get_selector_auto(page, "fs_home_page", "match_rows")
                if not match_row_sel or not await click_next_day(page, match_row_sel):
                    print("  [Critical] Daily navigation failed. Stopping session.")
                    break
                await asyncio.sleep(2)

            if last_processed_info.get('date_obj') and target_date.date() < last_processed_info['date_obj']:
                print(f"\n--- SKIPPING DAY: {target_full} (advancing to resume date) ---")
                continue

            print(f"\n--- ANALYZING DATE: {target_full} ---")
            # Selector analysis now handled in extract_matches_from_page for batching
            await fs_universal_popup_dismissal(page, "fs_home_page")

            try:
                scheduled_tab_sel = await SelectorManager.get_selector_auto(page, "fs_home_page", "tab_scheduled")
                if scheduled_tab_sel and await page.locator(scheduled_tab_sel).is_visible(timeout=WAIT_FOR_LOAD_STATE_TIMEOUT):
                    await page.click(scheduled_tab_sel)
                    print("    [Info] Clicked scheduled tab.")
                    await asyncio.sleep(2.0)
            except Exception:
                print("    [Info] Could not click Scheduled tab.")

            await fs_universal_popup_dismissal(page, "fs_home_page")
            matches_data = await extract_matches_from_page(page)
            
            # --- TIME CLEANING, ADJUSTMENT & SORTING ---
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
                        pass # Ignore matches with invalid time format for today
                else:
                    valid_matches.append(m)

            if is_today:
                print(f"    [Time Filter] Removed {len(matches_data) - len(valid_matches)} past matches for today.")
            
            print(f"    [Matches Found] {len(valid_matches)} valid fixtures. (Sorted by Time)")

            # --- Resume Logic ---
            if last_processed_info.get('date') == target_full:
                last_id = last_processed_info.get('id')
                print(f"    [Resume] Checking for last processed ID: {last_id} on this date.")
                try:
                    found_index = [i for i, match in enumerate(valid_matches) if match.get('id') == last_id][0]
                    print(f"    [Resume] Match found at index {found_index}. Skipping {found_index + 1} previously processed matches.")
                    valid_matches = valid_matches[found_index + 1:]
                except IndexError:
                    print(f"    [Resume] Last processed ID {last_id} not found in current scan. Proceeding with all {len(valid_matches)} valid matches found (already time-filtered).")
                    # We do not slice here because valid_matches is already filtered by time (> now) for today.
                    # If we lost the ID (e.g. because of time gap), we simply pick up everything that is currently valid.
                     

            # --- Batch Processing ---
            if valid_matches:
                print(f"    [Batching] Processing {len(valid_matches)} matches concurrently...")
                results = await processor.run_batch(valid_matches, process_match_task, browser=browser)
                total_cycle_predictions += sum(1 for r in results if r)
            else:
                print("    [Info] No new matches to process for this day.")

    finally:
        if context is not None:
            await context.close()
        if 'browser' in locals():
             await browser.close()
             
    print(f"\n--- Flashscore Analysis Complete: {total_cycle_predictions} new predictions found. ---")
    
    # --- Trigger Recommendations ---
    print("\n   [Auto] Generating betting recommendations for today...")
    get_recommendations(save_to_file=True)
    
    return


async def run_flashscore_offline_repredict(playwright: Playwright):
    """
    Offline reprediction mode: Uses stored CSV data to generate/update predictions
    for matches starting more than 1 hour from now.
    """
    print("\n   [Offline] Starting offline reprediction engine...")
    
    all_schedules = get_all_schedules()
    if not all_schedules:
        print("    [Offline Error] No schedules found in database.")
        return

    # Filter for scheduled matches
    scheduled_matches = [m for m in all_schedules if m.get('match_status') == 'scheduled']
    
    now = dt.now(NIGERIA_TZ)
    threshold = now + timedelta(hours=1)
    
    to_process = []
    for m in scheduled_matches:
        try:
            date_str = m.get('date')
            time_str = m.get('match_time')
            if not date_str or not time_str or time_str == 'N/A':
                continue
                
            match_dt = dt.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M").replace(tzinfo=NIGERIA_TZ)
            if match_dt > threshold:
                to_process.append(m)
        except Exception:
            continue

    print(f"    [Offline] Found {len(to_process)} future matches (> 1 hour away) to repredict.")
    
    if not to_process:
        return

    # Sort historical matches once
    def parse_date(d_str):
        try:
            return dt.strptime(d_str, "%d.%m.%Y")
        except:
            return dt.min

    historical_matches = [m for m in all_schedules if m.get('match_status') != 'scheduled' and m.get('home_score') not in ('', 'N/A', None) and m.get('away_score') not in ('', 'N/A', None)]
    
    historical_matches.sort(key=lambda x: parse_date(x.get('date', '')), reverse=True)

    total_repredicted = 0
    for m in to_process:
        home_team = m.get('home_team')
        away_team = m.get('away_team')
        region_league = m.get('region_league', 'Unknown')
        match_label = f"{home_team} vs {away_team}"

        # 1. Build H2H Data with proper mapping for AI engine
        home_last_10 = []
        away_last_10 = []
        h2h_list = []
        
        for hist in historical_matches:
            h_home = hist.get('home_team')
            h_away = hist.get('away_team')
            
            # Create mapped match object
            hs = hist.get('home_score', '0')
            ascore = hist.get('away_score', '0')
            try:
                hsi = int(hs)
                asi = int(ascore)
                winner = "Home" if hsi > asi else "Away" if asi > hsi else "Draw"
            except:
                winner = "Draw"
                
            mapped_hist = {
                "date": hist.get("date"),
                "home": h_home,
                "away": h_away,
                "score": f"{hs}-{ascore}",
                "winner": winner
            }

            # Home team last 10
            if (h_home == home_team or h_away == home_team) and len(home_last_10) < 10:
                home_last_10.append(mapped_hist)
                
            # Away team last 10
            if (h_home == away_team or h_away == away_team) and len(away_last_10) < 10:
                away_last_10.append(mapped_hist)
                
            # H2H
            if ((h_home == home_team and h_away == away_team) or (h_home == away_team and h_away == home_team)):
                h2h_list.append(mapped_hist)

        h2h_data = {
            "home_team": home_team,
            "away_team": away_team,
            "home_last_10_matches": home_last_10,
            "away_last_10_matches": away_last_10,
            "head_to_head": h2h_list,
            "region_league": region_league
        }

        # 2. Get Standings with proper type conversion
        raw_standings = get_standings(region_league)
        standings_data = []
        for s in raw_standings:
            try:
                standings_data.append({
                    "team_name": s.get("team_name"),
                    "position": int(s.get("position", 0)),
                    "goal_difference": int(s.get("goal_difference", 0)),
                    "goals_for": int(s.get("goals_for", 0)),
                    "goals_against": int(s.get("goals_against", 0))
                })
            except:
                continue

        # 3. Data Quality Validation
        if len(home_last_10) < 3 or len(away_last_10) < 3:
            continue

        # 4. Predict
        analysis_input = {"h2h_data": h2h_data, "standings": standings_data}
        try:
            prediction = RuleEngine.analyze(analysis_input)
            
            if prediction.get("type", "SKIP") != "SKIP":
                # Ensure match_data has necessary keys for save_prediction
                match_data_for_save = m.copy()
                match_data_for_save['id'] = m.get('fixture_id')
                match_data_for_save['time'] = m.get('match_time')
                
                save_prediction(match_data_for_save, prediction)
                total_repredicted += 1
                if total_repredicted % 10 == 0:
                    print(f"    [Offline] Repredicted {total_repredicted} matches...")
        except Exception as e:
            print(f"      [Offline Error] Failed predicting {match_label}: {e}")

    print(f"\n--- Offline Reprediction Complete: {total_repredicted} matches repredicted. ---")
    
    # --- Trigger Recommendations ---
    print("\n   [Auto] Generating betting recommendations after offline update...")
    get_recommendations(save_to_file=True)
