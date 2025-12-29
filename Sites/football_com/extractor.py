"""
Extractor Module
Handles extraction of leagues and matches from Football.com schedule pages.
"""

import asyncio
from typing import List, Dict

from playwright.async_api import Page

from Neo.selector_manager import SelectorManager
from Neo.intelligence import get_selector
from Helpers.constants import WAIT_FOR_LOAD_STATE_TIMEOUT


async def extract_league_matches(page: Page, target_date: str) -> List[Dict]:
    """Iterates through all league headers, expands them, and extracts matches for a specific date."""
    print("  [Harvest] Starting 'Expand & Harvest' sequence...")
    all_matches = []
    
    league_header_sel = get_selector("fb_schedule_page", "league_header") or ".league-title-wrapper"
    match_card_sel = get_selector("fb_schedule_page", "match_rows") or ".match-card-section.match-card"
    match_url_sel = get_selector("fb_schedule_page", "match_url") or ".match-card > a.card-link"
    league_title_sel = get_selector("fb_schedule_page", "league_title_link") or ".league-link"

    try:
        league_headers = await page.locator(league_header_sel).all()
        print(f"  [Harvest] Found {len(league_headers)} league headers.")

        for i, header_locator in enumerate(league_headers):
            try:
                # Extract League Name
                league_element = header_locator.locator(league_title_sel).first
                if await league_element.is_visible():
                    league_text = (await league_element.inner_text(timeout=WAIT_FOR_LOAD_STATE_TIMEOUT)).strip().replace('\n', ' - ')
                elif await header_locator.locator("h4").count() > 0:
                    league_text = (await header_locator.locator("h4").first.inner_text()).strip().replace('\n', ' - ')
                else:
                    league_text = f"Unknown League {i+1}"
                
                print(f"  -> Processing League {i+1}: {league_text}")

                # Check expansion state
                wrapper_class = await header_locator.get_attribute("class")
                is_collapsed = "collapsed" in str(wrapper_class)

                if is_collapsed:
                    print(f"    -> {league_text}: clicked to expand.")
                    await header_locator.click()
                    await asyncio.sleep(2.0) # Wait for animation
                    
                    # Double check if it expanded
                    wrapper_class_after = await header_locator.get_attribute("class")
                    if "collapsed" in str(wrapper_class_after):
                         print(f"    -> {league_text}: Still collapsed. Clicking again to expand...")
                         await header_locator.click()
                         await asyncio.sleep(2.0)
                         print(f"    -> {league_text}: Clicked to expand.")
                else:
                    print(f"    -> {league_text}: Already expanded. Extracting matches...")

                # Extract Matches from Sibling Container
                matches_container = await header_locator.evaluate_handle('(el) => el.nextElementSibling')
                if matches_container:
                    matches_in_section = await matches_container.evaluate("""(container, args) => {
                        const { selectors, leagueText } = args;
                        const results = [];
                        const cards = container.querySelectorAll(selectors.match_card_sel);
                        cards.forEach(card => {
                            const homeEl = card.querySelector('.home-team-name');
                            const awayEl = card.querySelector('.away-team-name');
                            const timeEl = card.querySelector('.time');
                            const linkEl = card.querySelector(selectors.match_url_sel) || card.closest('a');
                            
                            if (homeEl && awayEl) {
                                results.push({ 
                                    home: homeEl.innerText.trim(), 
                                    away: awayEl.innerText.trim(), 
                                    time: timeEl ? timeEl.innerText.trim() : "N/A", 
                                    league: leagueText, 
                                    url: linkEl ? linkEl.href : "", 
                                    date: args.targetDate 
                                });
                            }
                        });
                        return results;
                    }""", {"selectors": {"match_card_sel": match_card_sel, "match_url_sel": match_url_sel}, "leagueText": league_text, "targetDate": target_date})
                    
                    if matches_in_section:
                        all_matches.extend(matches_in_section)
                        print(f"    -> {league_text}: Extracted {len(matches_in_section)} matches.")
                    else:
                        print(f"    -> {league_text}: No matches found in section.")
                
                # Close section after processing to keep page clean/performant
                wrapper_class_final = await header_locator.get_attribute("class")
                if "collapsed" not in str(wrapper_class_final):
                     await header_locator.click()
                     print(f"    -> {league_text}: Closing expanded section.")
                     await asyncio.sleep(1)

            except Exception as e:
                print(f"    [Harvest Error] Failed to process a league header: {e}")
    except Exception as e:
        print(f"  [Harvest] Overall harvesting error: {e}")

    print(f"  [Harvest] Total matches found: {len(all_matches)}")
    return all_matches
 

async def validate_match_data(matches: List[Dict]) -> List[Dict]:
    """Validate and clean extracted match data."""
    valid_matches = []
    for match in matches:
        if all(k in match for k in ['home', 'away', 'url', 'league']):
            # Basic validation
            if match['home'] and match['away'] and match['url']:
                valid_matches.append(match)
        else:
            print(f"    [Validation] Skipping invalid match: {match}")
    print(f"  [Validation] {len(valid_matches)}/{len(matches)} matches valid.")
    return valid_matches
