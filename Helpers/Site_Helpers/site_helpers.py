# Helpers/site_helpers.py

import asyncio # Keep asyncio for async operations
from typing import Optional # Keep Optional for type hinting
from playwright.async_api import Page, TimeoutError, Frame # Import Frame
from Neo.intelligence import get_selector

async def fs_universal_popup_dismissal(page: Page, context: str = "fs_generic"):
    """Universal pop-up dismissal for Flashscore."""
    await accept_cookies_robust(page)
    await kill_cookie_banners(page) # Scorched earth removal

    try:
        understand_selectors = [
            get_selector(context, 'tooltip_i_understand_button'),
            "button:has-text('I understand')",
        ]
        for sel in understand_selectors:
            if sel:
                btn = page.locator(sel).first
                if await btn.count() > 0 and await btn.is_visible(timeout=2000):
                    await btn.click(timeout=2000, force=True)
                    print(f"    [Popup Handler] Clicked 'I understand' button via: {sel}")
                    await asyncio.sleep(0.5)
                    return # Assume one popup is enough for now
    except Exception:
        pass

async def kill_cookie_banners(page: Page):
    """Forcefully removes cookie banners and overlays from the DOM and injects CSS to keep them hidden."""
    try:
        # Inject CSS to hide banners permanently
        await page.add_style_tag(content="""
            #onetrust-consent-sdk, 
            .onetrust-pc-dark-filter, 
            #onetrust-banner-sdk,
            .ot-sdk-container,
            [id^="sp_message_container"],
            #onetrust-pc-sdk,
            .ot-pc-refuse-all-handler {
                display: none !important;
                visibility: hidden !important;
                opacity: 0 !important;
                pointer-events: none !important;
                z-index: -9999 !important;
            }
            body { 
                overflow: auto !important; 
            }
        """)
        
        # Also try to remove existing ones
        await page.evaluate("""() => {
            const selectors = [
                '#onetrust-consent-sdk', 
                '.onetrust-pc-dark-filter', 
                '#onetrust-banner-sdk',
                '.ot-sdk-container',
                '[id^="sp_message_container"]',
                '#onetrust-pc-sdk'
            ];
            selectors.forEach(s => {
                const els = document.querySelectorAll(s);
                els.forEach(el => el.remove());
            });
            document.body.style.overflow = 'auto';
            document.documentElement.style.overflow = 'auto';
        }""")
    except Exception:
        pass

async def accept_cookies_robust(page: Page):
    """Handles cookie consent dialogs across different patterns."""
    try:
        # Direct OneTrust ID check
        for ot_id in ["#onetrust-accept-btn-handler", "#accept-recommended-btn-handler"]:
            btn = page.locator(ot_id)
            if await btn.is_visible(timeout=1000):
                await btn.click()
                print(f"    [Cookies] Accepted via OneTrust ID: {ot_id}")
                # Wait for the main banner/sdk to hide
                try:
                    await page.locator("#onetrust-consent-sdk").wait_for(state="hidden", timeout=5000)
                except:
                    pass
                await asyncio.sleep(0.5)
                return
    except Exception:
        pass

    # Generic OneTrust Banner Check
    try:
        banner = page.locator("#onetrust-consent-sdk")
        if await banner.is_visible(timeout=500):
            # Try to click any "Accept" or "Allow" button inside the SDK
            for btn_text in ["Accept All", "Allow All", "I Accept", "Accept"]:
                btn = banner.get_by_role("button", name=btn_text, exact=True).first
                if await btn.is_visible(timeout=500):
                    await btn.click()
                    print(f"    [Cookies] Accepted via OneTrust text: {btn_text}")
                    # Wait for the banner to actually disappear to avoid click interception
                    try:
                        await banner.wait_for(state="hidden", timeout=5000)
                    except:
                        pass
                    return
    except Exception:
        pass

    try:
        cookie_sel = get_selector('fs_home_page', 'cookie_accept_button')
        if cookie_sel and await page.locator(cookie_sel).is_visible(timeout=1000):
            await page.locator(cookie_sel).click()
            print(f"    [Cookies] Accepted via AI selector")
            await asyncio.sleep(0.5)
            return
    except Exception:
        pass

    try:
        for text in ["Accept All", "I Agree", "Allow All", "Accept Cookies", "I Accept"]:
            btn = page.get_by_role("button", name=text, exact=True).first
            if await btn.is_visible(timeout=500):
                await btn.click()
                print(f"    [Cookies] Accepted via text: {text}")
                return
    except Exception:
        pass

async def click_next_day(page: Page, match_row_selector: str) -> bool:
    """Clicks the next day button in calendar."""
    print("  [Navigation] Clicking next day...")
    await accept_cookies_robust(page)
    next_sel = get_selector('fs_home_page', 'next_day_button')
    if next_sel:
        try:
            btn = page.locator(next_sel).first
            if await btn.is_visible(timeout=5000):
                await btn.click()
                await page.wait_for_load_state("domcontentloaded", timeout=30000)
                print(f"    [Success] Next day clicked and page updated.")
                return True
        except Exception as e:
            print(f"    [Error] Click next day failed: {e}")
    return False


async def fb_universal_popup_dismissal(page: Page, context: str = "fb_generic", monitor_forever: bool = False):
    """Universal pop-up dismissal for Football.com - NOW USING MODULAR HANDLER."""
    print(f"[DEBUG] fb_universal_popup_dismissal called with context='{context}', monitor_forever={monitor_forever}")

    try:
        # Import the new modular popup handler
        from Neo.popup_handler import PopupHandler

        # Create handler instance
        handler = PopupHandler()
        print("[DEBUG] Modular PopupHandler instantiated successfully")

        # Convert monitor_forever to monitor_interval (0 = single run, >0 = continuous)
        monitor_interval = 30 if monitor_forever else 0

        # Call the new modular handler
        result = await handler.fb_universal_popup_dismissal(page, context, None, monitor_interval)
        print(f"[DEBUG] Modular handler returned: success={result.get('success', False)}, method={result.get('method', 'unknown')}")

        # Return boolean for backward compatibility
        return result.get('success', False)

    except Exception as e:
        print(f"[DEBUG] Error in modular handler: {e}")
        import traceback
        traceback.print_exc()
        return False
            


async def get_main_frame(page: Page) -> Optional[Page | Frame]:
    """
    Checks for the presence of the main 'app' iframe and returns the content frame if it exists.
    Otherwise, it returns the original page object.
    """
    try:
        iframe_locator = page.locator("#app")
        if await iframe_locator.count() > 0:
            iframe_element = await iframe_locator.element_handle()
            frame = await iframe_element.content_frame()
            if frame:
                await frame.wait_for_load_state('networkidle', timeout=30000)
                print("  [Frame] Switched to main #app iframe.")
                return frame
    except Exception:
        print("  [Frame] No #app iframe found, using main page.")
    return page
