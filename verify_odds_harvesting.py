import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_odds_harvesting():
    print("Testing Odds Harvesting and Progressive Sync (Refined)...")
    
    # 1. Mask environment variables for initial import side-effects
    with patch.dict(os.environ, {"FB_PHONE": "123", "FB_PASSWORD": "abc"}):
        import Modules.FootballCom.booker.booking_code as bc

    # 2. Patch the specific dependencies inside the booking_code module
    # These need to be AsyncMock because they are awaited
    with patch('Modules.FootballCom.booker.booking_code.force_clear_slip', new_callable=AsyncMock) as mock_clear, \
         patch('Modules.FootballCom.booker.booking_code.run_full_sync', new_callable=AsyncMock) as mock_sync, \
         patch('Modules.FootballCom.booker.booking_code.neo_popup_dismissal', new_callable=AsyncMock) as mock_popup, \
         patch('Modules.FootballCom.booker.booking_code.ensure_bet_insights_collapsed', new_callable=AsyncMock) as mock_collapse, \
         patch('Modules.FootballCom.booker.booking_code.find_market_and_outcome', new_callable=AsyncMock) as mock_market, \
         patch('Modules.FootballCom.booker.booking_code.find_and_click_outcome', new_callable=AsyncMock) as mock_click, \
         patch('Modules.FootballCom.booker.booking_code.get_selector_auto', new_callable=AsyncMock) as mock_sel, \
         patch('Modules.FootballCom.booker.booking_code.extract_booking_details', new_callable=AsyncMock) as mock_extract, \
         patch('Modules.FootballCom.booker.booking_code.update_prediction_status') as mock_update_pred, \
         patch('Modules.FootballCom.booker.booking_code.update_site_match_status') as mock_update_site, \
         patch('Modules.FootballCom.booker.booking_code.get_site_match_id', return_value="site_123") as mock_id, \
         patch('Modules.FootballCom.booker.booking_code.save_booking_code', new_callable=AsyncMock) as mock_save:

        mock_page = MagicMock()
        target_date = "15.02.2026"
        
        # Define mock behavior
        mock_market.return_value = ("Over/Under", "Over 2.5")
        mock_click.return_value = (True, 1.85)
        mock_sel.return_value = ".book-btn"
        mock_extract.return_value = "ABC123"
        
        # Mock locator behavior for "book_bet_button"
        mock_locator = MagicMock()
        mock_locator.count = AsyncMock(return_value=1)
        mock_locator.first = MagicMock()
        mock_locator.first.scroll_into_view_if_needed = AsyncMock()
        mock_locator.first.click = AsyncMock()
        mock_page.locator.return_value = mock_locator
        mock_page.goto = AsyncMock()

        # Mock data (15 matches to trigger sync at 10)
        mock_matched_urls = {f'fs_{i}': f'https://football.com/match_{i}' for i in range(15)}
        mock_day_preds = [
            {'fixture_id': f'fs_{i}', 'home_team': f'Home {i}', 'away_team': f'Away {i}', 'prediction': 'OVER 2.5'}
            for i in range(15)
        ]

        # Execute
        print(f"  Running harvest for {len(mock_day_preds)} matches...")
        await bc.harvest_booking_codes(mock_page, mock_matched_urls, mock_day_preds, target_date)
        
        # Assertions
        print(f"  Sync calls: {mock_sync.call_count}")
        assert mock_sync.call_count == 2, f"Expected 2 sync calls, got {mock_sync.call_count}"
        
        assert mock_update_pred.call_count == 15
        assert mock_update_site.call_count == 15
        
        # Verify odds string conversion
        last_args = mock_update_pred.call_args[1]
        assert last_args['odds'] == "1.85", f"Expected '1.85', got {last_args['odds']}"
        
        print(f"  [SUCCESS] All {len(mock_day_preds)} matches processed and synced.")

if __name__ == "__main__":
    try:
        asyncio.run(test_odds_harvesting())
    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
