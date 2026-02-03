"""
Single Match Booking Module (Phase 2a: Harvest)
Responsible for booking a single match to extract a booking code.
Focuses on reliability, retries, and clean state.
"""

import asyncio
import re
from typing import Dict, Tuple, Optional
from playwright.async_api import Page
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
import logging

from Helpers.Site_Helpers.site_helpers import get_main_frame
from Helpers.utils import log_error_state
from Neo.selector_manager import SelectorManager
from Neo.intelligence import fb_universal_popup_dismissal as neo_popup_dismissal
from .ui import robust_click
from .mapping import find_market_and_outcome
from .slip import force_clear_slip, get_bet_slip_count


# --- RETRY CONFIGURATION ---
def log_retry_attempt(retry_state):
    print(f"      [Booking Retry] Attempt {retry_state.attempt_number} failed. Retrying...")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    before_sleep=log_retry_attempt
)
async def book_single_match(page: Page, match_data: Dict) -> Tuple[Optional[str], Optional[str]]:
    """
    Orchestrates the booking of a single match.
    Returns: (booking_code, booking_url) or (None, None)
    
    Steps:
    1. Force Clear Slip (Pre-condition)
    2. Navigate to Match
    3. Add Selection
    4. Verify Odds (Safety)
    5. Click "Book Bet"
    6. Extract Code & URL
    7. Force Clear Slip (Post-condition)
    """
    booking_code = None
    booking_url = None
    
    match_label = f"{match_data.get('home_team')} vs {match_data.get('away_team')}"
    match_url = match_data.get('url') # From Football.com registry
    
    if not match_url:
        print(f"    [Error] No URL for {match_label}")
        return None, None

    print(f"\n   [Harvest] Booking: {match_label}")

    try:
        # 1. Clean Slate
        try:
            await force_clear_slip(page)
        except Exception as e:
            # If we can't clear slip initially, risky to proceed.
            print(f"    [Critical] Failed initial slip clear for {match_label}: {e}")
            raise e # Retry at loop level or fail

        # 2. Navigation
        await page.goto(match_url, wait_until='domcontentloaded', timeout=45000)
        await asyncio.sleep(2)
        await neo_popup_dismissal(page, match_url)
        
        # 3. Add Selection
        # Reuse mapping logic
        # We need the prediction info. Assumes match_data has prediction info merged OR passed in separately.
        # In the caller (Leo.py), we should merge prediction info into match_data for this function.
        
        m_name, o_name = await find_market_and_outcome(match_data)
        if not m_name:
            print(f"    [Skip] Measurement failed: Could not map market for {match_label}")
            return None, None

        # Search for Market
        # ... (Reusing placement logic)
        search_icon = SelectorManager.get_selector_strict("fb_match_page", "search_icon")
        search_input = SelectorManager.get_selector_strict("fb_match_page", "search_input")
            
        if search_icon and search_input and await page.locator(search_icon).isVisible():
             await robust_click(page.locator(search_icon).first, page)
             await page.locator(search_input).fill(m_name)
             await page.keyboard.press("Enter")
             await asyncio.sleep(1)

        # Find Outcome Button
        # Heuristic: Look for button with outcome text inside market container
        # This is simplified; ideally we use robust find_outcome from placement.py if exposed
        # For now, implementing direct search logic consistent with placement.py
        
        outcome_found = False
        # Try generic robust click on text
        outcome_btn = page.locator(f"div.outcome-button:has-text('{o_name}')").first
        # Fallback
        if await outcome_btn.count() == 0:
             outcome_btn = page.locator(f"span:text-is('{o_name}')").first
        
        if await outcome_btn.count() > 0 and await outcome_btn.is_visible():
             print(f"    [Selection] Clicking {o_name}...")
             await robust_click(outcome_btn, page)
             await asyncio.sleep(1)
             
             # Verify added to slip
             if await get_bet_slip_count(page) > 0:
                 outcome_found = True
        
        if not outcome_found:
             print(f"    [Fail] Could not select outcome {o_name}")
             return None, None
            
        # 4. Book Bet
        # Open Slip if needed (usually handled by book flow?)
        # We need to click "Book Bet" which is usually in the slip footer
        
        # Ensure slip is visible/minimized handle
        # Assuming mobile view, slip might be a footer bar
        
        book_btn_sel = SelectorManager.get_selector_strict("fb_match_page", "book_bet_button") # e.g. "Book a bet"
        if not book_btn_sel:
             book_btn_sel = "button:has-text('Book a bet')" 
             
        book_btn = page.locator(book_btn_sel).first
        
        if await book_btn.count() > 0 and await book_btn.is_visible():
            await robust_click(book_btn, page)
            print("    [Action] Clicked 'Book a bet'")
            
            # 5. Extract Code
            # Wait for modal
            code_display_sel = SelectorManager.get_selector_strict("fb_match_page", "booking_code_display") or "div.booking-code-text"
            try:
                await page.wait_for_selector(code_display_sel, timeout=10000)
                code_el = page.locator(code_display_sel).first
                booking_code = await code_el.inner_text()
                booking_code = booking_code.strip()
                print(f"    [Success] Booking Code: {booking_code}")
                
                # Close Modal
                close_btn = page.locator("button.close-modal, div.close-icon").first
                if await close_btn.count() > 0:
                    await close_btn.click()
                    
            except Exception as e:
                print(f"    [Error] Booking code modal did not appear or parseable: {e}")
                
        else:
            print("    [Error] 'Book a bet' button not found.")
            
        # 6. Final Cleanup
        await force_clear_slip(page)
        
        return booking_code, booking_url  # URL might be None for now if not extractable easily

    except Exception as e:
        print(f"    [Booking Error] {match_label}: {e}")
        # Try to clean up anyway
        try:
             await force_clear_slip(page)
        except: 
             pass
        raise e # Retrigger retry
