import asyncio
from playwright.async_api import async_playwright
import os

async def probe():
    async with async_playwright() as p:
        # iPhone 12 emulation
        iphone_12 = p.devices['iPhone 12']
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(**iphone_12)
        page = await context.new_page()
        
        url = "https://www.flashscore.com/football/"
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(10)
        
        # Check for Summary (ALL) tab
        summary_tab = page.locator('.filters__tab[data-analytics-alias="summary"]')
        if await summary_tab.count() > 0:
            print("Found Summary Tab, clicking...")
            await summary_tab.click()
            await asyncio.sleep(5)
        
        # Check for Show More button
        show_more = page.locator('.wclIcon__leagueShowMoreCont button')
        if await show_more.count() > 0:
            print(f"Found {await show_more.count()} 'Show More' buttons.")
            text = await show_more.first.inner_text()
            print(f"First button text: {text}")
        
        # Dump some match-like structures
        matches = await page.locator('.event__match').count()
        print(f"Found {matches} elements with class '.event__match'")
        
        rows = await page.locator('.eventRow').count()
        print(f"Found {rows} elements with class '.eventRow' (Alternative mobile match class)")
        
        leagues = await page.locator('.headerLeague__wrapper').count()
        print(f"Found {leagues} elements with class '.headerLeague__wrapper'")

        await page.screenshot(path="mobile_probe.png")
        print("Screenshot saved to mobile_probe.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(probe())
