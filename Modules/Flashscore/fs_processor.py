# fs_processor.py: Match processing and prediction generation flow.
# Refactored for Clean Architecture (v2.7)
# This script orchestrates the full extraction/analysis pipeline for a single match.

import asyncio
from playwright.async_api import Browser
from Data.Access.db_helpers import save_prediction, save_region_league_entry, save_standings
from Core.Browser.site_helpers import fs_universal_popup_dismissal
from Core.Browser.Extractors.h2h_extractor import extract_h2h_data, activate_h2h_tab, save_extracted_h2h_to_schedules
from Core.Browser.Extractors.standings_extractor import extract_standings_data, activate_standings_tab
from Core.Utils.monitor import PageMonitor
from Core.Utils.utils import log_error_state
from Core.Utils.constants import NAVIGATION_TIMEOUT, WAIT_FOR_LOAD_STATE_TIMEOUT
from Core.Intelligence.model import RuleEngine
from .fs_utils import retry_extraction

async def process_match_task(match_data: dict, browser: Browser):
    """
    Worker function to process a single match in a new page/context.
    """
    context = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Mobile Safari/537.36"
        ),
        timezone_id="Africa/Lagos"
    )
    page = await context.new_page()
    PageMonitor.attach_listeners(page)
    match_label = f"{match_data.get('home_team', 'unknown')}_vs_{match_data.get('away_team', 'unknown')}"

    try:
        print(f"    [Batch Start] {match_data['home_team']} vs {match_data['away_team']}: {match_data['date']} - {match_data['time']}")

        full_match_url = f"{match_data['match_link']}"
        await page.goto(full_match_url, wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT)
        await asyncio.sleep(2.0)

        await fs_universal_popup_dismissal(page, "fs_match_page")
        await page.wait_for_load_state("domcontentloaded", timeout=WAIT_FOR_LOAD_STATE_TIMEOUT)
        await fs_universal_popup_dismissal(page, "fs_match_page")

        # --- H2H Tab & Expansion ---
        h2h_data = {}
        if await activate_h2h_tab(page):
            try:
                show_more_selector = "button:has-text('Show more matches'), a:has-text('Show more matches')"
                try:
                    await page.wait_for_selector(show_more_selector, timeout=WAIT_FOR_LOAD_STATE_TIMEOUT)
                    show_more_buttons = page.locator(show_more_selector).first 
                    if await show_more_buttons.count() > 0:
                        print("    [H2H Expansion] Expanding available match history...")
                        try:
                            await show_more_buttons.click(timeout=WAIT_FOR_LOAD_STATE_TIMEOUT)
                            await asyncio.sleep(2.0)
                            second_button = page.locator(show_more_selector).nth(1)
                            if await second_button.count() > 0:
                                await second_button.click(timeout=WAIT_FOR_LOAD_STATE_TIMEOUT)
                                await asyncio.sleep(1.0)
                        except Exception:
                            print("    [H2H Expansion] Some expansion buttons failed, but continuing...")
                except Exception:
                    print("    [H2H Expansion] No expansion buttons found or failed to load.")

                await asyncio.sleep(3.0)
                h2h_data = await retry_extraction(extract_h2h_data, page, match_data['home_team'], match_data['away_team'], "fs_h2h_tab")

                h2h_count = len(h2h_data.get("home_last_10_matches", [])) + len(h2h_data.get("away_last_10_matches", [])) + len(h2h_data.get("head_to_head", []))
                print(f"      [OK H2H] H2H tab data extracted for {match_label} ({h2h_count} matches found)")

                await save_extracted_h2h_to_schedules(h2h_data)

            except Exception as e:
                print(f"      [Warning] Failed to fully load/expand H2H tab for {match_label}: {e}")
        else:
            print(f"      [Warning] H2H tab inaccessible for {match_label}")

        # --- Data Quality Validation ---
        home_form_count = len(h2h_data.get("home_last_10_matches", []))
        away_form_count = len(h2h_data.get("away_last_10_matches", []))
        
        if home_form_count < 3 or away_form_count < 3:
            print(f"      [Data Quality] Skipped {match_label}: Insufficient form data (Home: {home_form_count}, Away: {away_form_count})")
            return False

        # --- Standings Tab ---
        standings_data = []
        standings_league = "Unknown"
        
        if await activate_standings_tab(page):
            try:
                standings_result = await retry_extraction(extract_standings_data, page)
                standings_data = standings_result.get("standings", [])
                standings_league = standings_result.get("region_league", "Unknown")
                if standings_league == "Unknown":
                    standings_league = h2h_data.get("region_league", "Unknown")
                standings_league_url = standings_result.get("league_url", "")
                if standings_result.get("has_draw_table"):
                    print(f"      [Skip] Match has draw table, skipping.")
                    return False
                if standings_data and standings_league != "Unknown":
                    for row in standings_data:
                        row['url'] = standings_league_url
                    save_standings(standings_data, standings_league)
                    print(f"      [OK Standing] Standings tab data extracted for {standings_league}")
            except Exception as e:
                print(f"      [Warning] Failed to load Standings tab for {match_label}: {e}")

        # --- Process Data & Predict ---
        h2h_league = h2h_data.get("region_league", "Unknown")
        final_league = standings_league if standings_league != "Unknown" else h2h_league

        if final_league != "Unknown":
            match_data["region_league"] = final_league
            print(f"      [Extractor Validation] Updated League to: {final_league}")

            if " - " in final_league:
                region, league = final_league.split(" - ", 1)
                save_region_league_entry({
                    'region': region.strip(),
                    'league_name': league.strip()
                })

        if standings_data:
            save_standings(standings_data, final_league)
            print(f"      [OK Standing] Standings tab data extracted for {final_league}")

        analysis_input = {"h2h_data": h2h_data, "standings": standings_data}
        prediction = RuleEngine.analyze(analysis_input)

        if prediction.get("type", "SKIP") != "SKIP":
            save_prediction(match_data, prediction)
            print(f"            [OK Signal] {match_label}")
            return True
        else:
            print(f"      [NO Signal] {match_label}")
            return False

    except Exception as e:
        print(f"      [Error] Match failed {match_label}: {e}")
        await log_error_state(page, f"process_match_task_{match_label}", e)
        return False
    finally:
        await asyncio.sleep(1.0)
        await context.close()
