import asyncio
import os
import sys
from unittest.mock import MagicMock, patch, AsyncMock

print("Stage 1: Script started")

async def test_minimal():
    print("Stage 2: inside test_minimal")
    
    # Mask env vars
    os.environ["FB_PHONE"] = "123"
    os.environ["FB_PASSWORD"] = "abc"
    
    print("Stage 3: importing booking_code")
    try:
        # Mocking all imports that could have side effects
        with patch.dict('sys.modules', {
            'Data.Access.db_helpers': MagicMock(),
            'Data.Access.sync_manager': MagicMock(),
            'Core.Intelligence.intelligence': MagicMock(),
            'Core.Intelligence.selector_manager': MagicMock(),
            'Core.Browser.site_helpers': MagicMock(),
            'Core.Utils.utils': MagicMock(),
            'Core.Utils.monitor': MagicMock(),
            'Core.System.lifecycle': MagicMock()
        }):
            from Modules.FootballCom.booker.booking_code import harvest_booking_codes
            print("Stage 4: harvest_booking_codes imported successfully")
            
            # Simple test call with all dependencies patched
            with patch('Modules.FootballCom.booker.booking_code.force_clear_slip', new_callable=AsyncMock), \
                 patch('Modules.FootballCom.booker.booking_code.run_full_sync', new_callable=AsyncMock), \
                 patch('Modules.FootballCom.booker.booking_code.neo_popup_dismissal', new_callable=AsyncMock), \
                 patch('Modules.FootballCom.booker.booking_code.ensure_bet_insights_collapsed', new_callable=AsyncMock), \
                 patch('Modules.FootballCom.booker.booking_code.find_market_and_outcome', new_callable=AsyncMock), \
                 patch('Modules.FootballCom.booker.booking_code.find_and_click_outcome', new_callable=AsyncMock), \
                 patch('Modules.FootballCom.booker.booking_code.get_selector_auto', new_callable=AsyncMock), \
                 patch('Modules.FootballCom.booker.booking_code.extract_booking_details', new_callable=AsyncMock), \
                 patch('Modules.FootballCom.booker.booking_code.update_prediction_status'), \
                 patch('Modules.FootballCom.booker.booking_code.update_site_match_status'), \
                 patch('Modules.FootballCom.booker.booking_code.save_booking_code', new_callable=AsyncMock):
                
                print("Stage 5: Starting harvest_booking_codes call")
                await harvest_booking_codes(MagicMock(), {}, {}, "15.02.2026")
                print("Stage 6: harvest_booking_codes call completed")
                
    except Exception as e:
        print(f"Error during import/execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Stage 0: Main block")
    asyncio.run(test_minimal())
    print("Stage 7: Finished")
