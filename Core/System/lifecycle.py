# lifecycle.py: Global state management and application lifecycle control.
# Refactored for Clean Architecture (v2.7)
# This script manages phase transitions, audit logging, and process initialization.

import os
import sys
import argparse
from datetime import datetime as dt
from Data.Access.db_helpers import init_csvs
from Core.Utils.utils import Tee, LOG_DIR

state = {
    "cycle_start_time": None, 
    "cycle_count": 0,
    "current_phase": "Startup",
    "last_action": "Init",
    "next_expected": "Startup Checks",
    "why_this_step": "System initialization",
    "expected_outcome": "Ready to start",
    "ai_server_ready": False,
    "llm_needed_for_this_cycle": False, 
    "pending_count": 0,
    "booked_this_cycle": 0,
    "failed_this_cycle": 0,
    "current_balance": 0.0,
    "last_win_amount": 5000.0, # Heuristic
    "error_log": []
}

def log_state(phase=None, action=None, next_step=None, why=None, expect=None):
    """Updates and prints the current system state."""
    global state
    if phase: state["current_phase"] = phase
    if action: state["last_action"] = action
    if next_step: state["next_expected"] = next_step
    if why: state["why_this_step"] = why
    if expect: state["expected_outcome"] = expect
    
    print(f"   [STATE] {state['current_phase']} | Done: {state['last_action']} | Next: {state['next_expected']} | Why: {state['why_this_step']}")

def log_audit_state(phase: str, action: str, details: str = ""):
    """Central state logger — prints to console and appends to audit_log.csv"""
    timestamp = dt.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"[{timestamp}] [STATE] {phase} | Action: {action} | {details}"
    print(message)
    
    from Data.Access.db_helpers import append_to_csv
    append_to_csv("audit_log.csv", {
        "timestamp": timestamp,
        "event_type": "STATE",
        "description": f"{phase} - {action} - {details}",
        "balance_before": "",
        "balance_after": "",
        "stake": "",
        "status": "INFO"
    })

def setup_terminal_logging(args):
    """Sets up Tee logging to file."""
    # Set timeout
    if args:
        os.environ["PLAYWRIGHT_TIMEOUT"] = "3600000"

    TERMINAL_LOG_DIR = LOG_DIR / "Terminal"
    TERMINAL_LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
    log_file_path = TERMINAL_LOG_DIR / f"leo_session_{timestamp}.log"

    log_file = open(log_file_path, "w", encoding="utf-8")
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = Tee(original_stdout, log_file)
    sys.stderr = Tee(original_stderr, log_file)
    
    return log_file, original_stdout, original_stderr

def parse_args():
    parser = argparse.ArgumentParser(description="LeoBook Prediction System")
    parser.add_argument('--offline-repredict', action='store_true',
                       help='Run offline reprediction using stored data instead of scraping')
    return parser.parse_args()
