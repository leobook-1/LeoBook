"""
Booker Package
Exposes core modules for UI, Mapping, Slip, and Placement.
"""

from .ui import handle_page_overlays, robust_click, dismiss_overlays, wait_for_element
from .mapping import find_market_and_outcome
from .slip import get_bet_slip_count, force_clear_slip
from .booking_code import place_bets_for_matches
from .placement import place_multi_bet_from_codes
from .withdrawal import check_and_perform_withdrawal

__all__ = [
    'handle_page_overlays',
    'robust_click',
    'dismiss_overlays',
    'wait_for_element',
    'find_market_and_outcome',
    'get_bet_slip_count',
    'force_clear_slip',
    'place_bets_for_matches',
    'place_multi_bet_from_codes',
    'check_and_perform_withdrawal'
]
