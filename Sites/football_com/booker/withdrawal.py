import csv
import asyncio
from datetime import datetime
from pathlib import Path
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from Neo.selector_manager import SelectorManager
from .ui import robust_click
# Adjusted import: navigator is in the parent directory (Sites/football_com)
from ..navigator import extract_balance

WITHDRAWALS_CSV = Path("DB/withdrawals.csv")
MIN_WITHDRAWAL = 1000
MAX_WITHDRAWAL = 999999

async def withdraw_amount(page: Page, amount: str = "100", pin: str = "1234", reason: str = "40% of bet win"):
    """
    Full withdrawal flow:
    1. Enter amount -> Submit
    2. Extract data from confirmation dialog
    3. Confirm
    4. Enter PIN
    5. Wait for "Pending Request" dialog
    6. Verify balance decreased by exactly `amount`
    7. If successful -> save to withdrawals.csv
    """
    # --- Validation ---
    try:
        amount_float = float(amount.replace(',', ''))
        if amount_float < MIN_WITHDRAWAL:
            print(f"[Withdraw] Aborting: Amount {amount} is below minimum {MIN_WITHDRAWAL}")
            return
        if amount_float > MAX_WITHDRAWAL:
             print(f"[Withdraw] Aborting: Amount {amount} exceeds maximum {MAX_WITHDRAWAL}")
             return
    except ValueError:
        print(f"[Withdraw] Aborting: Invalid amount format '{amount}'")
        return

    pre_balance = await extract_balance(page)
    print(f"[Withdraw] Starting. Pre-balance: {pre_balance}")
    
    if pre_balance < amount_float:
         print(f"[Withdraw] Aborting: Insufficient balance ({pre_balance}) for withdrawal of {amount}")
         return

    # --- Stage 1: Enter amount & submit ---
    amount_sel = SelectorManager.get_selector("fb_withdraw_page", "amount_input")
    await page.fill(amount_sel, amount)

    submit_sel = SelectorManager.get_selector("fb_withdraw_page", "withdraw_submit_button")
    await page.wait_for_selector(f"{submit_sel}:not(.is-disabled)", timeout=15000)
    await robust_click(page.locator(submit_sel).first, page)

    # --- Stage 2: Confirmation dialog - extract data first ---
    await page.wait_for_selector(
        SelectorManager.get_selector("fb_withdraw_page", "confirm_dialog_wrapper"),
        timeout=15000
    )

    # Extract data **before** confirming
    amount_confirmed = await page.locator(
        SelectorManager.get_selector("fb_withdraw_page", "confirm_amount_value")
    ).inner_text()

    bank_confirmed = await page.locator(
        SelectorManager.get_selector("fb_withdraw_page", "confirm_bank_value")
    ).inner_text()

    account_confirmed = await page.locator(
        SelectorManager.get_selector("fb_withdraw_page", "confirm_account_value")
    ).inner_text()

    account_name_confirmed = await page.locator(
        SelectorManager.get_selector("fb_withdraw_page", "confirm_account_name_value")
    ).inner_text()

    print(f"[Withdraw Confirm] Amount: {amount_confirmed} | Bank: {bank_confirmed}")
    print(f"                 Account: {account_confirmed} | Name: {account_name_confirmed}")

    # Confirm
    confirm_btn_sel = SelectorManager.get_selector("fb_withdraw_page", "confirm_confirm_button")
    await robust_click(page.locator(confirm_btn_sel).first, page)

    # --- Stage 3: Enter PIN ---
    pin_fields_sel = SelectorManager.get_selector("fb_withdraw_page", "pin_input_fields")
    pin_fields = page.locator(pin_fields_sel)

    # Wait for pin fields to be visible
    await page.wait_for_selector(pin_fields_sel, timeout=10000)

    for i, digit in enumerate(pin):
        await pin_fields.nth(i).fill(digit)
        await asyncio.sleep(0.3)  # small delay to mimic human

    pin_confirm_sel = SelectorManager.get_selector("fb_withdraw_page", "pin_confirm_button")
    await page.wait_for_selector(f"{pin_confirm_sel}:not(.is-disabled)", timeout=10000)
    await robust_click(page.locator(pin_confirm_sel).first, page)

    # --- Stage 4: Wait for success dialog "Pending Request" ---
    try:
        await page.wait_for_selector(
            SelectorManager.get_selector("fb_withdraw_page", "success_dialog_wrapper"),
            timeout=25000
        )

        success_title = await page.locator(
            SelectorManager.get_selector("fb_withdraw_page", "success_title")
        ).inner_text()

        if "Pending Request" not in success_title:
            raise Exception("Success dialog appeared but title is not 'Pending Request'")

        print("[Withdraw] Success dialog detected -> Pending Request")

    except PlaywrightTimeoutError:
        raise Exception("No 'Pending Request' dialog appeared after PIN -> likely failed")

    # --- Final Verification: Balance must decrease by exactly the amount ---
    await asyncio.sleep(3)  # give backend time to process
    post_balance = await extract_balance(page)

    withdrawn_amount = float(amount_confirmed.replace(",", ""))
    expected_post = pre_balance - withdrawn_amount

    if abs(post_balance - expected_post) > 0.1:  # small tolerance for rounding
        raise Exception(
            f"Balance verification failed. "
            f"Pre: {pre_balance}, Expected post: {expected_post}, Actual: {post_balance}"
        )

    print(f"[Withdraw] Balance verification OK: {pre_balance} -> {post_balance}")

    # --- Save successful withdrawal to CSV ---
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "amount": amount_confirmed,
        "bank": bank_confirmed,
        "account_number": account_confirmed,
        "account_name": account_name_confirmed,
        "balance_before": pre_balance,
        "balance_after": post_balance,
        "reason": reason
    }

    WITHDRAWALS_CSV.parent.mkdir(parents=True, exist_ok=True)
    file_exists = WITHDRAWALS_CSV.exists()

    with open(WITHDRAWALS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=record.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(record)

    print(f"[Withdraw] Successfully saved record to {WITHDRAWALS_CSV}")

    # Optional: click "Transaction" or "Home" button to leave dialog
    try:
        await page.locator(
            SelectorManager.get_selector("fb_withdraw_page", "success_home_btn")
        ).click(timeout=5000)
    except:
        pass  # not critical

