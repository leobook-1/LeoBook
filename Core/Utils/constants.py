# constants.py: Centralized timeout and configuration constants.
# Refactored for Clean Architecture (v2.7)
# This script provides global settings for navigations and waits.

"""
LeoBook Constants
Centralized timeout and configuration constants.
"""

# Timeout Constants (in milliseconds)
NAVIGATION_TIMEOUT = 180000  # 3 minutes for page navigation (balanced between speed and reliability)
WAIT_FOR_LOAD_STATE_TIMEOUT = 90000  # 1.5 minutes for load state operations
