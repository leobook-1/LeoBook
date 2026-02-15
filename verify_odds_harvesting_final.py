import asyncio
import os
import sys
from unittest.mock import MagicMock, patch, AsyncMock

async def test_odds_harvesting():
    print("Testing Odds Harvesting and Progressive Sync (Final)...")
    
    # Mask env vars for module import side-effects
    os.environ["FB_PHONE"] = "123"
    os.environ["FB_PASSWORD"] = "abc"
    
    # Mocking all imports that could have side effects
    mock_db = MagicMock()
    mock_db.get_site_match_id.return_value = "site_123"
    mock_db.update_prediction_status = MagicMock()
    mock_db.update_site_match_status = MagicMock()
    
    mock_sync = MagicMock()
    mock_sync.run_full_sync = AsyncMock()
    
    mock_slip = MagicMock()
    mock_slip.force_clear_slip = AsyncMock()
    
    mock_intel = MagicMock()
    mock_intel.fb_universal_popup_dismissal = AsyncMock()
    mock_intel.get_selector_auto = AsyncMock(return_value=".test-sel")
    
    mock_mapping = MagicMock()
    mock_mapping.find_market_and_outcome = AsyncMock(return_value=("Over/Under", "Over 2.5"))

    with patch.dict('sys.modules', {
        'Data.Access.db_helpers': mock_db,
        'Data.Access.sync_manager': mock_sync,
        'Modules.FootballCom.booker.ui': MagicMock(),
        'Modules.FootballCom.booker.mapping': mock_mapping,
        'Modules.FootballCom.booker.slip': mock_slip,
        'Core.Intelligence.intelligence': mock_intel,
        'Core.Browser.site_helpers': MagicMock(),
        'Core.Utils.utils': MagicMock(),
        'Core.Utils.monitor': MagicMock(),
        'Core.System.lifecycle': MagicMock()
    }):
        # Now import the function under test
        from Modules.FootballCom.booker.booking_code import harvest_booking_codes
        
        # Patch internal functions of the SAME module
        with patch('Modules.FootballCom.booker.booking_code.ensure_bet_insights_collapsed', new_callable=AsyncMock), \
             patch('Modules.FootballCom.booker.booking_code.find_and_click_outcome', new_callable=AsyncMock) as mock_click, \
             patch('Modules.FootballCom.booker.booking_code.extract_booking_details', new_callable=AsyncMock) as mock_extract_code, \
             patch('Modules.FootballCom.booker.booking_code.save_booking_code', new_callable=AsyncMock):

            mock_page = MagicMock()
            target_date = "15.02.2026"
            
            # Mock data (15 matches to trigger sync at 10 and at the end)
            mock_matched_urls = {f'fs_{i}': f'https://football.com/match_{i}' for i in range(15)}
            mock_day_preds = [
                {'fixture_id': f'fs_{i}', 'home_team': f'Home {i}', 'away_team': f'Away {i}', 'prediction': 'OVER 2.5'}
                for i in range(15)
            ]
            
            mock_click.return_value = (True, 1.85)
            mock_extract_code.return_value = "ABC123"
            
            # Mock page.goto
            mock_page.goto = AsyncMock()
            
            # Mock locator behavior for "book_bet_button"
            mock_locator = MagicMock()
            mock_locator.count = AsyncMock(return_value=1)
            mock_locator.first = MagicMock()
            mock_locator.first.scroll_into_view_if_needed = AsyncMock()
            mock_locator.first.click = AsyncMock()
            mock_page.locator.return_value = mock_locator

            # Run harvest
            await harvest_booking_codes(mock_page, mock_matched_urls, mock_day_preds, target_date)
            
            # Verify sync trigger (should be called at 10 and at the end)
            print(f"  Sync calls: {mock_sync.run_full_sync.call_count}")
            assert mock_sync.run_full_sync.call_count == 2
            
            # Verify update calls
            assert mock_db.update_prediction_status.call_count == 15
            assert mock_db.update_site_match_status.call_count == 15
            
            # Verify odds passed to updates
            last_call_args = mock_db.update_prediction_status.call_args[1]
            assert last_call_args['odds'] == '1.85'
            
    print("[SUCCESS] Final odds harvesting and progressive sync verified.\n")

if __name__ == "__main__":
    asyncio.run(test_odds_harvesting())
