"""
Betslip Management
Handles counting and clearing of the betslip with robust, self-healing logic.
"""

import re
import asyncio
from playwright.async_api import Page
from .ui import robust_click
from Neo.selector_manager import SelectorManager

async def get_bet_slip_count(page: Page) -> int:
    """Extract current number of bets in the slip using dynamic selector."""
    # Use fb_match_page as it contains the betslip keys
    count_sel = SelectorManager.get_selector_strict("fb_match_page", "betslip_bet_count")
    
    if count_sel:
        try:
            if await page.locator(count_sel).count() > 0:
                text = await page.locator(count_sel).first.inner_text(timeout=2000)
                count = int(re.sub(r'\D', '', text) or 0)
                if count > 0:
                    return count
        except Exception as e:
            # print(f"    [Slip] Count selector failed: {count_sel} - {e}")
            pass

    return 0

async def clear_bet_slip(page: Page):
    """
    Ensure the bet slip is empty before starting a new session using dynamic selectors.
    Aggressively tries to open slip and clear it.
    """
    # print("    [Slip] Checking if bet slip needs clearing...")
    try:
        count = await get_bet_slip_count(page)
        if count > 0:
            print(f"    [Slip] {count} bets detected. Opening slip to clear...")

            # 1. Open Slip
            # Try multiple trigger selectors from knowledge.json keys
            trigger_keys = ["slip_trigger_button", "betslip_trigger_by_attribute", "bet_slip_fab_icon_button"]
            slip_opened = False
            
            for key in trigger_keys:
                sel = SelectorManager.get_selector_strict("fb_match_page", key) or SelectorManager.get_selector_strict("fb_global", key)
                if sel and await page.locator(sel).count() > 0 and await page.locator(sel).first.is_visible():
                     await robust_click(page.locator(sel).first, page)
                     slip_opened = True
                     await asyncio.sleep(2)
                     break
            
            if not slip_opened:
                print("    [Slip] Warning: Could not open bet slip to clear.")
                return

            # 2. Click Remove All
            clear_sel = SelectorManager.get_selector_strict("fb_match_page", "betslip_remove_all")
            if clear_sel and await page.locator(clear_sel).count() > 0:
                await page.locator(clear_sel).first.click()
                await asyncio.sleep(1)
                
                # 3. Confirm Removal (if dialog appears)
                confirm_sel = SelectorManager.get_selector_strict("fb_match_page", "confirm_bet_button")
                if confirm_sel and await page.locator(confirm_sel).count() > 0 and await page.locator(confirm_sel).first.is_visible():
                    await page.locator(confirm_sel).first.click()
                    await asyncio.sleep(1)
                
                print("    [Slip] Clicked remove all.")
            else:
                 print("    [Slip] Remove all button not found.")

            # 4. Verify Cleared
            new_count = await get_bet_slip_count(page)
            if new_count == 0:
                print("    [Slip] Successfully cleared bets.")
            else:
                print(f"    [Slip] Warning: Slip still has {new_count} bets after clear attempt.")

            # 5. Close Slip
            try:
                await page.keyboard.press("Escape")
                
                # Check for explicit close button
                close_icon = SelectorManager.get_selector_strict("fb_match_page", "betslip_close_button")
                if close_icon and await page.locator(close_icon).count() > 0:
                     await page.locator(close_icon).first.click()
            except:
                pass
        else:
            # print("    [Slip] Bet slip is already empty.")
            pass
            
    except Exception as e:
        print(f"    [Slip Warning] Failed to clear slip: {e}")

async def force_clear_slip(page: Page):
    """
    Aggressively ensures the bet slip is empty. 
    Retries clearing logic 3 times. 
    Raises Exception if slip cannot be cleared (triggering session reset).
    """
    for attempt in range(3):
        try:
            count = await get_bet_slip_count(page)
            if count == 0:
                return # Successfully cleared
            
            print(f"    [Slip] Force Clear Attempt {attempt+1}/3: Found {count} items.")
            await clear_bet_slip(page)
            
            # Double check
            await asyncio.sleep(1.0)
            if await get_bet_slip_count(page) == 0:
                print("    [Slip] Force clear successful.")
                return

        except Exception as e:
            print(f"    [Slip Error] Attempt {attempt+1} failed: {e}")
            await asyncio.sleep(2.0)
    
    # If we reach here, we failed
    raise Exception("CRITICAL: Failed to clear bet slip after 3 attempts. Session tainted.")
