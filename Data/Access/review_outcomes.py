# review_outcomes.py: Entry point for reviewing match results (Chapter 0).
# Refactored for Clean Architecture (v2.7)
# This script initiates the outcome review process for pending predictions.

"""
LeoBook Review Outcomes System v2.6.0
Modular outcome review and evaluation system.

This module provides a unified interface to the review system components:
- Health monitoring and alerting
- Data validation and quality assurance
- Prediction evaluation for all betting markets
- Core review processing and outcome tracking
"""

# Import all modular components
from .health_monitor import HealthMonitor
from .data_validator import DataValidator
import pandas as pd
from datetime import datetime, timedelta
import pytz
import os
import uuid
from .db_helpers import PREDICTIONS_CSV, ACCURACY_REPORTS_CSV, log_audit_event, upsert_entry, files_and_headers
from .sync_manager import SyncManager

def evaluate_prediction(predicted_type: str, home_score: str, away_score: str) -> int:
    """
    Evaluates if a prediction was correct (1) or not (0).
    Supported types: OVER_2.5, UNDER_2.5, BTTS_YES, BTTS_NO, HOME_WIN, AWAY_WIN, DRAW.
    """
    try:
        h = int(home_score)
        a = int(away_score)
        total = h + a
        pt = predicted_type.upper().strip()

        if pt == "OVER_2.5":
            return 1 if total > 2.5 else 0
        elif pt == "UNDER_2.5":
            return 1 if total < 2.5 else 0
        elif pt == "BTTS_YES":
            return 1 if h > 0 and a > 0 else 0
        elif pt == "BTTS_NO":
            return 1 if h == 0 or a == 0 else 0
        elif pt == "HOME_WIN":
            return 1 if h > a else 0
        elif pt == "AWAY_WIN":
            return 1 if a > h else 0
        elif pt == "DRAW":
            return 1 if h == a else 0
        
        # Fallback for complex strings (e.g., from old prediction_evaluator)
        from .prediction_evaluator import evaluate_prediction as legacy_eval
        # Note: legacy_eval takes (prediction, actual_score, home_team, away_team)
        # Here we just have predicted_type, home_score, away_score.
        # We'll try to adapt or just return 0 for safety if not strictly one of the above.
        return 0
    except:
        return 0

    return match


async def run_accuracy_generation():
    """
    Aggregates performance metrics from predictions.csv for the last 24h.
    Logs to audit_log.csv and upserts to Supabase 'accuracy_reports'.
    """
    if not os.path.exists(PREDICTIONS_CSV):
        return

    print("\n   [ACCURACY] Generating performance metrics (Last 24h)...")
    try:
        df = pd.read_csv(PREDICTIONS_CSV, dtype=str).fillna('')
        if df.empty:
            print("   [ACCURACY] No predictions found.")
            return

        # 1. Date Filter (Last 24h)
        lagos_tz = pytz.timezone('Africa/Lagos')
        now_lagos = datetime.now(lagos_tz)
        yesterday_lagos = now_lagos - timedelta(days=1)

        def parse_updated(ts):
            try:
                # pandas to_datetime is flexible with ISO formats
                dt = pd.to_datetime(ts)
                if dt.tzinfo is None:
                    return lagos_tz.localize(dt)
                return dt.astimezone(lagos_tz)
            except:
                return pd.NaT

        df['updated_dt'] = df['last_updated'].apply(parse_updated)
        df_24h = df[(df['updated_dt'] >= yesterday_lagos) & (df['status'].isin(['reviewed', 'finished']))].copy()

        if df_24h.empty:
            print("   [ACCURACY] No predictions reviewed in the last 24h.")
            return

        # 2. Aggregates
        volume = len(df_24h)
        correct_count = (df_24h['outcome_correct'] == '1').sum()
        win_rate = (correct_count / volume) * 100 if volume > 0 else 0

        # Return Calculation (1-unit flat stake)
        total_return = 0
        for _, row in df_24h.iterrows():
            try:
                odds = float(row.get('odds', 0))
                if odds <= 0: odds = 2.0 # Default conservative odds
                
                if row['outcome_correct'] == '1':
                    total_return += (odds - 1)
                else:
                    total_return -= 1
            except:
                pass
        
        return_pct = (total_return / volume) * 100 if volume > 0 else 0

        # 3. Persistence (Local CSV)
        report_id = str(uuid.uuid4())[:8]
        report_row = {
            'report_id': report_id,
            'timestamp': now_lagos.isoformat(),
            'volume': str(volume),
            'win_rate': f"{win_rate:.2f}",
            'return_pct': f"{return_pct:.2f}",
            'period': 'last_24h',
            'last_updated': now_lagos.isoformat()
        }
        
        # Save to accuracy_reports.csv
        upsert_entry(ACCURACY_REPORTS_CSV, report_row, files_and_headers[ACCURACY_REPORTS_CSV], 'report_id')

        # Log to audit_log.csv
        log_audit_event(
            event_type='ACCURACY_REPORT',
            description=f"Generated report {report_id}: Volume={volume}, WinRate={win_rate:.1f}%, Return={return_pct:.1f}%",
            status='success'
        )

        # 4. Immediate Cloud Sync
        sync = SyncManager()
        if sync.supabase:
            print(f"   [SYNC] Pushing accuracy report {report_id} to Supabase...")
            await sync.batch_upsert('accuracy_reports', [report_row])
            print("   [SUCCESS] Accuracy metrics synchronized.")

    except Exception as e:
        print(f"   [ACCURACY ERROR] {e}")


from .outcome_reviewer import (
    get_predictions_to_review,
    save_single_outcome,
    process_review_task,
    run_review_process
)

# Legacy compatibility - expose main functions at module level
__all__ = [
    'HealthMonitor',
    'DataValidator',
    'evaluate_prediction',
    'get_predictions_to_review',
    'save_single_outcome',
    'process_review_task',
    'run_review_process'
]

# Version information
__version__ = "2.6.0"
__compatible_models__ = ["2.5", "2.6"]
