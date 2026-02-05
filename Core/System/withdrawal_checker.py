# withdrawal_checker.py: Logic for managing automated withdrawal proposals.
# Refactored for Clean Architecture (v2.7)
# This script monitors balance and triggers Telegram notifications for wins.

import asyncio
from datetime import datetime as dt
from pathlib import Path
from Core.System.lifecycle import state, log_audit_state, log_state
from Core.System.telegram_bridge import pending_withdrawal, send_proposal_message, withdrawal_timeout_checker
from Data.Access.db_helpers import log_audit_event

def calculate_proposed_amount(balance: float, latest_win: float) -> float:
    """v2.7 Calculation: Min(30% balance, 50% latest win)."""
    val = min(balance * 0.30, latest_win * 0.50)
    # Ensure min 500 and floor of 5,000 remains
    if balance - val < 5000:
        val = balance - 5000
    
    return max(0.0, float(int(val))) # Round to whole number

def get_latest_win() -> float:
    """Retrieves the latest win amount from audit logs or state."""
    return state.get("last_win_amount", 5000.0)

async def check_triggers(page=None) -> bool:
    """v2.7 Triggers."""
    balance = state.get("current_balance", 0.0)
    if balance >= 10000 and get_latest_win() >= 5000:
        return True
    return False

async def propose_withdrawal(amount: float):
    global pending_withdrawal
    if pending_withdrawal["active"]:
        return

    pending_withdrawal.update({
        "active": True,
        "amount": amount,
        "proposed_at": dt.now(),
        "approved": False
    })

    try:
        await send_proposal_message(amount)
        asyncio.create_task(withdrawal_timeout_checker())
    except Exception:
        pending_withdrawal["active"] = False

async def execute_withdrawal(amount: float):
    """Executes the withdrawal using an isolated browser context (v2.7)."""
    print(f"   [Execute] Starting Telegram-approved withdrawal for ₦{amount:.2f}...")
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        # We need a browser context, preferably reusing persistent session
        user_data_dir = Path("Data/Auth/ChromeData_v3").absolute()
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                headless=True,
                viewport={'width': 375, 'height': 612}
            )
            page = await context.new_page()
            
            from Modules.FootballCom.booker.withdrawal import check_and_perform_withdrawal
            success = await check_and_perform_withdrawal(page, state["current_balance"], last_win_amount=amount*2)
            
            if success:
                log_state("Withdrawal", f"Executed ₦{amount:,.2f}", "Approved via Telegram")
                log_audit_event("WITHDRAWAL_EXECUTED", f"Approved via Telegram: ₦{amount}", state["current_balance"], state["current_balance"]-amount, amount)
                state["last_withdrawal_time"] = dt.now()
            else:
                print("   [Execute Error] Withdrawal process failed.")
                
            await context.close()
        except Exception as e:
            print(f"   [Execute Error] Failed to launch context for withdrawal: {e}")
