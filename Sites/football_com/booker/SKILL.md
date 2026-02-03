---
name: Football.com Booking Flow Optimization
description: Detailed instruction set for implementing the robust, self-healing booking flow for Phase 2 on football.com.
---

# Instruction Set for AI Agent – Football.com Booking Phase 2

**Objective**  
Implement a robust, self-healing booking flow that places accumulator bets with minimal user interaction, maximum reliability, and clear failure recovery.

**Core Principles**  
1. **Zero Hardcoded Selectors**: Every selector matches a key in `knowledge.json`. Use `get_selector()` or `get_selector_auto()`. If missing, log error and skip/raise.  
2. **Explicit Verification**: Every critical action (Search, Expand, Click, Place) must be verified immediately after execution (e.g. visibility check, betslip count increase).  
3. **No Magic Waits**: Never rely on fixed `asyncio.sleep()`. Wait for network idle, element visibility, or DOM change.  
4. **Explicit Logic**: No "self-healing" libraries (like `tenacity`). Use explicit `for attempt in range(2)` loops with `asyncio.sleep(1)` and logging.  
5. **Mandatory Post-Checks**: Balance decrease check is **mandatory**. Booking code extraction is **mandatory**.

## Phase 2 – Exact Sequence & Decision Points

### Step 0 – Pre-Booking State Validation (Navigator)
- **Check Login**:
  ```python
  not_logged_in_sel = get_selector("fb_global", "not_logged_in_indicator")
  if await page.locator(not_logged_in_sel).is_visible(timeout=4000):
      await ensure_logged_in(page)
  ```
- **Check Balance**: Call `extract_balance(page)`. Store as `pre_bet_balance`.
- **Clear Slip**: Aggressively clear existing bets (see Step 4).

### Step 1 – Navigate to Match Page (Booker)
For each prediction:
- `await page.goto(matched_url, wait_until="networkidle", timeout=30000)`
- **Verify Page**:
  ```python
  header_sel = get_selector("fb_match_page", "match_header")
  await page.wait_for_selector(header_sel, state="visible", timeout=15000)
  ```
- **Dismiss Overlays**:
  ```python
  await fb_universal_popup_dismissal(page)
  await dismiss_overlays(page)
  ```

### Step 2 – Collapse Interfering Widgets
- **Collapse Bet Insights**:
  ```python
  header_sel = get_selector("fb_match_page", "match_smart_picks_dropdown") 
  # Ensure "match_smart_picks_dropdown" is in knowledge.json
  arrow_sel = get_selector("fb_match_page", "match_smart_picks_arrow_expanded") 
  # Check if expanded arrow exists
  if await page.locator(arrow_sel).count() > 0:
      await page.locator(header_sel).first.click()
      await page.wait_for_selector(arrow_sel, state="hidden", timeout=4000)
  ```

### Step 3 – Market & Outcome Selection (Critical)

**a. Open Market Search**
   ```python
   search_icon_sel = get_selector("fb_match_page", "search_icon")
   if search_icon_sel:
       await robust_click(page.locator(search_icon_sel).first, page)
   ```

**b. Type Market Name**
   ```python
   search_input_sel = get_selector("fb_global", "search_input")
   await page.fill(search_input_sel, market_name)
   await page.press(search_input_sel, "Enter")
   await page.wait_for_load_state("networkidle", timeout=8000)
   ```

**c. Handle Collapsed Results** (Expansion)
   - After search, the market might be visible but collapsed.
   - **Action**: Look for the market title text and click it if visible.
   ```python
   # Dynamic selector: precise text match for market name to find the header
   market_title_sel = f':text-is("{market_name}")' 
   if await page.locator(market_title_sel).is_visible(timeout=5000):
        print(f"    [Market] Expanding potential collapsed market: {market_name}")
        await robust_click(page.locator(market_title_sel).first, page)
        await asyncio.sleep(1) # Allow expansion animation
   ```

**d. Locate & Click Outcome**
   ```python
   # Try specific candidates in order
   outcome_candidates = [
       f'button:has-text("{outcome_name}")',
       f'div:has-text("{outcome_name}")',
       f'span:has-text("{outcome_name}")'
   ]
   clicked = False
   for cand in outcome_candidates:
       loc = page.locator(cand).first
       if await loc.count() > 0 and await loc.is_visible(timeout=3000):
           await robust_click(loc, page)
           clicked = True
           break
   
   if not clicked:
       # Fallback: Row-based lookup (requires key in knowledge.json)
       row_sel = get_selector("fb_match_page", "match_market_table_row")
       fallback_loc = page.locator(f"{row_sel}:has-text('{outcome_name}')").first
       if await fallback_loc.count() > 0:
            await fallback_loc.click()
   ```

**e. Verify Selection**
   - **Mandatory**: Check betslip count increased.
   ```python
   initial_count = await get_bet_slip_count(page)
   for _ in range(2): # Explicit 2 retries
       if await get_bet_slip_count(page) > initial_count:
           break
       await asyncio.sleep(1)
   else:
       raise BookingFailedError(f"Outcome '{outcome_name}' not added to slip.")
   ```

### Step 4 – Bet Slip Management & Finalization

- **Open Slip**:
  ```python
  trigger_sel = get_selector("fb_match_page", "slip_trigger_button") or get_selector("fb_global", "bet_slip_fab_icon_button")
  await robust_click(page.locator(trigger_sel).first, page)
  ```

- **Select Multiple Tab**:
  ```python
  multi_sel = get_selector("fb_match_page", "slip_tab_multiple")
  await page.locator(multi_sel).first.click()
  ```

- **Enter Stake**:
  ```python
  stake_sel = get_selector("fb_match_page", "stake_input")
  await page.fill(stake_sel, "1")
  await page.press(stake_sel, "Enter")
  ```

- **Place Bet**:
  ```python
  place_sel = get_selector("fb_match_page", "betslip_place_bet_button")
  await page.locator(place_sel).first.click()
  ```

- **Confirm**:
  ```python
  confirm_sel = get_selector("fb_match_page", "confirm_bet_button")
  await page.locator(confirm_sel).first.click()
  ```

### Step 5 – Post-Placement Verification (Mandatory)

1. **Booking Code**:
   ```python
   code_sel = get_selector("fb_booking_share_page", "booking_code_text")
   await page.wait_for_selector(code_sel, state="visible", timeout=20000)
   booking_code = await page.locator(code_sel).inner_text()
   ```
2. **Balance Check**:
   ```python
   new_balance = await extract_balance(page)
   if new_balance >= pre_bet_balance:
       # Log severe warning or raise error if critical
       raise BookingFailedError("Balance did not decrease. Bet might not be placed.")
   ```
3. **Save**: Record code in DB and screenshot.

## Failure recovery
- Catch errors for specific matches.
- If match booking fails, log, skip, and ensure slip is cleared for next match.
- **Always** attempt `await clear_bet_slip(page)` in `finally` block or error handler.
