# telegram_bridge.py: Telegram Bot integration for remote control and alerts.
# Refactored for Clean Architecture (v2.7)
# This script handles status commands and withdrawal approval flows.

import os
import asyncio
from datetime import datetime as dt
from telegram.ext import Application, MessageHandler, CommandHandler, filters
from telegram import Update
from Core.System.lifecycle import state

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

pending_withdrawal = {
    "active": False,
    "amount": 0.0,
    "proposed_at": None,
    "chat_id": TELEGRAM_CHAT_ID,
    "approved": False
}

# Global application instance to avoid multiple getUpdates/polling conflicts
_app_instance = None

async def cmd_start(update: Update, context):
    """Intro message."""
    await update.message.reply_text(
        "🦁 **Leo v2.7 Active**\n"
        "I am your autonomous betting agent. Use /help to see available commands."
    )

async def cmd_balance(update: Update, context):
    """Last known balance."""
    balance = state.get("current_balance", 0.0)
    await update.message.reply_text(f"💰 **Current Balance:** ₦{balance:,.2f}")

async def cmd_status(update: Update, context):
    """Current system status."""
    msg = (
        f"📊 **System Status**\n"
        f"Cycle: #{state.get('cycle_count', 0)}\n"
        f"Phase: {state.get('current_phase', 'N/A')}\n"
        f"Last Action: {state.get('last_action', 'N/A')}\n"
        f"Booked this cycle: {state.get('booked_this_cycle', 0)}\n"
        f"Failed this cycle: {state.get('failed_this_cycle', 0)}"
    )
    await update.message.reply_text(msg)

async def cmd_help(update: Update, context):
    """Help menu."""
    msg = (
        "❓ **Available Commands:**\n"
        "/balance - Check latest account balance\n"
        "/status - Current operation phase and cycle stats\n"
        "/summary - Brief recap of the last 24h audit\n"
        "/help - Show this menu\n\n"
        "Reply **YES** or **NO** to withdrawal proposals."
    )
    await update.message.reply_text(msg)

async def cmd_summary(update: Update, context):
    """Audit summary for last 24h."""
    from Data.Access.db_helpers import AUDIT_LOG_CSV
    if not os.path.exists(AUDIT_LOG_CSV):
        await update.message.reply_text("📂 No audit logs found yet.")
        return
        
    try:
        with open(AUDIT_LOG_CSV, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            recent = lines[-5:] # Last 5 events
            msg = "🕒 **Recent History (Audit Log):**\n" + "".join(recent)
            await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"❌ Error reading logs: {e}")

async def handle_withdrawal_reply(update: Update, context):
    global pending_withdrawal

    if not pending_withdrawal["active"]:
        return

    if update.effective_chat.id != pending_withdrawal["chat_id"]:
        return  # Security: only authorized chat

    text = update.message.text.strip().upper()

    if text == "YES":
        await update.message.reply_text("✅ APPROVED – Executing withdrawal now.")
        pending_withdrawal["approved"] = True
        pending_withdrawal["active"] = False

    elif text in ["NO", "CANCEL"]:
        await update.message.reply_text("❌ CANCELLED – No withdrawal performed.")
        pending_withdrawal["active"] = False
    else:
        await update.message.reply_text("Reply only **YES** or **NO**/**CANCEL** please.")

async def start_telegram_listener():
    global _app_instance
    if not TELEGRAM_TOKEN or TELEGRAM_CHAT_ID == 0:
        print("   [Telegram Warning] Missing TOKEN or CHAT_ID in .env. Integration disabled.")
        return

    try:
        if _app_instance is not None:
             print("   [Telegram] Listener already running.")
             return

        _app_instance = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Command Handlers
        _app_instance.add_handler(CommandHandler("start", cmd_start))
        _app_instance.add_handler(CommandHandler("balance", cmd_balance))
        _app_instance.add_handler(CommandHandler("status", cmd_status))
        _app_instance.add_handler(CommandHandler("help", cmd_help))
        _app_instance.add_handler(CommandHandler("summary", cmd_summary))
        
        # Message Handlers
        _app_instance.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_withdrawal_reply))
        
        # Start polling in background (v2.7 non-blocking)
        await _app_instance.initialize()
        await _app_instance.start()
        if not _app_instance.updater.running:
            await _app_instance.updater.start_polling(drop_pending_updates=True)
        print(f"   [Telegram] Listener started for chat_id: {TELEGRAM_CHAT_ID}")
    except Exception as e:
        print(f"   [Telegram Error] Could not start listener: {e}")
        _app_instance = None

async def withdrawal_timeout_checker():
    await asyncio.sleep(1800)  # 30 mins
    global pending_withdrawal, _app_instance
    if pending_withdrawal["active"]:
        pending_withdrawal["active"] = False
        try:
            if _app_instance:
                await _app_instance.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="⏰ Withdrawal proposal timed out (30 min) – cancelled.")
        except: pass
        print("   [Telegram] Proposal timed out.")

async def send_proposal_message(amount: float):
    """Sends the proposal message to Telegram."""
    global _app_instance
    message = (
        f"🚨 Withdrawal Proposal\n"
        f"Amount: ₦{amount:,.2f}\n"
        f"Reason: Auto after win\n"
        f"Current balance: ₦{state['current_balance']:,.2f}\n"
        f"Reply **YES** to approve (30 min timeout)\n"
        f"Reply **NO** or **CANCEL** to reject"
    )

    try:
        if _app_instance:
            await _app_instance.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
            print(f"   [Telegram] Proposal sent for ₦{amount:.2f}")
        else:
            print("   [Telegram] Skipping proposal send: Bot listener not running.")
    except Exception as e:
        print(f"   [Telegram Error] Failed to send message: {e}")
        raise e
