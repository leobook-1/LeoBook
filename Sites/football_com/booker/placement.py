"""
Bet Placement Orchestration
Handles adding selections to the slip and finalizing accumulators with robust verification.
"""

import asyncio
from typing import List, Dict
from playwright.async_api import Page
from Helpers.Site_Helpers.site_helpers import get_main_frame
from Helpers.DB_Helpers.db_helpers import update_prediction_status
from Helpers.utils import log_error_state, capture_debug_snapshot
from Neo.selector_manager import SelectorManager
from Neo.intelligence import fb_universal_popup_dismissal as neo_popup_dismissal
from .ui import robust_click, wait_for_condition
from .mapping import find_market_and_outcome
from .slip import get_bet_slip_count, clear_bet_slip

async def ensure_bet_insights_collapsed(page: Page):
    """Ensure the bet insights widget is collapsed."""
    try:
        arrow_sel = SelectorManager.get_selector_strict("fb_match_page", "match_smart_picks_arrow_expanded")
        if arrow_sel and await page.locator(arrow_sel).count() > 0 and await page.locator(arrow_sel).is_visible():
            print("    [UI] Collapsing Bet Insights widget...")
            await page.locator(arrow_sel).first.click()
            await asyncio.sleep(1)
    except Exception:
        pass

async def expand_collapsed_market(page: Page, market_name: str):
    """If a market is found but collapsed, expand it."""
    try:
        # Use knowledge.json key for generic market header or title
        # Then filter by text
        header_sel = SelectorManager.get_selector_strict("fb_match_page", "market_header")
        if header_sel:
             # Find header containing market name
             target_header = page.locator(header_sel).filter(has_text=market_name).first
             if await target_header.count() > 0:
                 # Check if it needs expansion (often indicated by an icon or state, but clicking usually toggles)
                 # We can just click it if we don't see outcomes.
                 # Heuristic: Validating visibility of outcomes is better done by the caller.
                 # This function explicitly toggles.
                 print(f"    [Market] Clicking market header for '{market_name}' to ensure expansion...")
                 await robust_click(target_header, page)
                 await asyncio.sleep(1)
    except Exception as e:
        print(f"    [Market] Expansion failed: {e}")

async def place_bets_for_matches(page: Page, matched_urls: Dict[str, str], day_predictions: List[Dict], target_date: str):
    """Visit matched URLs and place bets with strict verification."""
    MAX_BETS = 40
    processed_urls = set()

    for match_id, match_url in matched_urls.items():
        # Check betslip limit
        if await get_bet_slip_count(page) >= MAX_BETS:
            print(f"[Info] Slip full ({MAX_BETS}). Finalizing accumulator.")
            success = await finalize_accumulator(page, target_date)
            if success:
                # If finalized, we can continue filling a new slip?
                # User flow suggests one slip per day usually, but let's assume valid.
                pass
            else:
                 print("[Error] Failed to finalize accumulator. Aborting further bets.")
                 break

        if not match_url or match_url in processed_urls: continue
        
        pred = next((p for p in day_predictions if str(p.get('fixture_id', '')) == str(match_id)), None)
        if not pred or pred.get('prediction') == 'SKIP': continue

        processed_urls.add(match_url)
        print(f"[Match] Processing: {pred['home_team']} vs {pred['away_team']}")

        try:
            # 1. Navigation
            await page.goto(match_url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(3)
            await neo_popup_dismissal(page, match_url)
            await ensure_bet_insights_collapsed(page)

            # 2. Market Mapping
            m_name, o_name = await find_market_and_outcome(pred)
            if not m_name:
                print(f"    [Info] No market mapping for {pred.get('prediction')}")
                continue

            # 3. Search for Market
            search_icon = SelectorManager.get_selector_strict("fb_match_page", "search_icon")
            search_input = SelectorManager.get_selector_strict("fb_match_page", "search_input")
            
            if search_icon and search_input:
                if await page.locator(search_icon).count() > 0:
                    await robust_click(page.locator(search_icon).first, page)
                    await asyncio.sleep(1)
                    
                    await page.locator(search_input).fill(m_name)
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(2)
                    
                    # Handle Collapsed Market: Try to find header and click if outcomes not immediately obvious
                    # (Skipping complex check, just click header if name exists)
                    await expand_collapsed_market(page, m_name)

                    # 4. Select Outcome
                    # Try strategies: Exact Text Button -> Row contains text
                    outcome_added = False
                    initial_count = await get_bet_slip_count(page)
                    
                    # Strategy A: Button with precise text
                    outcome_btn = page.locator(f"button:text-is('{o_name}'), div[role='button']:text-is('{o_name}')").first
                    if await outcome_btn.count() > 0 and await outcome_btn.is_visible():
                         print(f"    [Selection] Found outcome button '{o_name}'")
                         await robust_click(outcome_btn, page)
                    else:
                         # Strategy B: Row based fallback
                         row_sel = SelectorManager.get_selector_strict("fb_match_page", "match_market_table_row")
                         if row_sel:
                             # Find row containing outcome text
                             target_row = page.locator(row_sel).filter(has_text=o_name).first
                             if await target_row.count() > 0:
                                  print(f"    [Selection] Found outcome row for '{o_name}'")
                                  await robust_click(target_row, page)
                    
                    # 5. Verification Loop
                    for _ in range(3):
                        await asyncio.sleep(1)
                        new_count = await get_bet_slip_count(page)
                        if new_count > initial_count:
                            print(f"    [Success] Outcome '{o_name}' added. Slip count: {new_count}")
                            outcome_added = True
                            update_prediction_status(match_id, target_date, 'added_to_slip')
                            break
                    
                    if not outcome_added:
                        print(f"    [Error] Failed to add outcome '{o_name}'. Slip count did not increase.")
                        update_prediction_status(match_id, target_date, 'failed_add')
                
                else:
                    print("    [Error] Search icon not found.")
            else:
                 print("    [Error] Search selectors missing configuration.")

        except Exception as e:
            print(f"    [Match Error] {e}")
            await capture_debug_snapshot(page, f"error_{match_id}", str(e))

async def finalize_accumulator(page: Page, target_date: str) -> bool:
    """Finalize the betslip with mandatory constraints."""
    print(f"[Betting] Finalizing accumulator for {target_date}...")
    
    try:
        # Pre-check Balance
        from ..navigator import extract_balance
        pre_balance = await extract_balance(page)
        print(f"    [Balance] Pre-bet: {pre_balance}")

        # 1. Open Slip
        slip_trigger = SelectorManager.get_selector_strict("fb_match_page", "slip_trigger_button")
        if slip_trigger and await page.locator(slip_trigger).count() > 0:
             await robust_click(page.locator(slip_trigger).first, page)
             await asyncio.sleep(3)

        # 2. Select Multiple Tab
        multi_tab = SelectorManager.get_selector_strict("fb_match_page", "slip_tab_multiple")
        if multi_tab and await page.locator(multi_tab).count() > 0:
             await robust_click(page.locator(multi_tab).first, page)
             await asyncio.sleep(1)

        # 3. Enter Stake (1 Naira)
        stake_input = SelectorManager.get_selector_strict("fb_match_page", "betslip_stake_input") or SelectorManager.get_selector_strict("fb_match_page", "betslip_stake_input_by_attribute")
        if stake_input and await page.locator(stake_input).count() > 0:
             await page.locator(stake_input).first.fill("1")
             await page.keyboard.press("Enter")
             await asyncio.sleep(1)
        else:
             print("    [Error] Stake input not found!")
             return False

        # 4. Place Bet
        place_btn = SelectorManager.get_selector_strict("fb_match_page", "betslip_place_bet_button") or SelectorManager.get_selector_strict("fb_match_page", "place_bet_button_by_attribute")
        if place_btn and await page.locator(place_btn).count() > 0:
             print("    [Booking] Clicking Place Bet...")
             await robust_click(page.locator(place_btn).first, page)
             await asyncio.sleep(3)
        else:
             print("    [Error] Place bet button not found!")
             return False

        # 5. Confirm (if dialog)
        confirm_btn = SelectorManager.get_selector_strict("fb_match_page", "confirm_bet_button") or SelectorManager.get_selector_strict("fb_match_page", "confirm_bet_button_by_attribute")
        if confirm_btn and await page.locator(confirm_btn).count() > 0:
             if await page.locator(confirm_btn).first.is_visible():
                  print("    [Booking] Confirming bet...")
                  await robust_click(page.locator(confirm_btn).first, page)
                  await asyncio.sleep(5)

        # 6. Post-Verification (Balance & Code)
        # Wait for booking code
        booking_code = await extract_booking_details(page)
        
        # Mandatory Balance Check
        post_balance = await extract_balance(page)
        print(f"    [Balance] Post-bet: {post_balance}")
        
        if post_balance < pre_balance:
             print("    [Verification] Balance decreased. Booking confirmed.")
             
             # Save Screenshot
             from Helpers.utils import take_screenshot
             await take_screenshot(page, f"booking_success_{target_date}")
             return True
        else:
             print("    [Verification FAILED] Balance matched pre-bet balance. Bet likely NOT placed.")
             return False

    except Exception as e:
        await log_error_state(page, "finalize_fatal", e)
        return False

async def extract_booking_details(page: Page) -> str:
    """Extract and return the booking code if visible."""
    code_sel = SelectorManager.get_selector_strict("fb_match_page", "booking_code_text")
    booking_code = "UNKNOWN"
    if code_sel:
         try:
             await page.wait_for_selector(code_sel, state="visible", timeout=15000)
             booking_code = await page.locator(code_sel).first.inner_text()
             print(f"    [Success] Booking Code: {booking_code}")
         except:
             print("    [Warning] Booking code element not found or timed out.")
    return booking_code
