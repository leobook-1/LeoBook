# review_outcomes.py: Entry point for reviewing match results (Phase 0).
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
from .prediction_evaluator import evaluate_prediction
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
