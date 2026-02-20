import asyncio
from playwright.async_api import async_playwright
import os

async def diagnostic():
    async with async_playwright() as p:
        iphone_12 = p.devices['iPhone 12']
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(**iphone_12)
        page = await context.new_page()
        
        url = "https://www.flashscore.com/football/"
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(10)
        
        # Click Summary (ALL) tab
        try:
            await page.locator('.filters__tab[data-analytics-alias="summary"]').click()
            await asyncio.sleep(5)
        except:
            print("Summary tab not found or failed to click")

        # Click Show More
        try:
            btn = page.locator('.wclIcon__leagueShowMoreCont button').first
            if await btn.count() > 0:
                await btn.click()
                print("Clicked Show More")
                await asyncio.sleep(5)
        except:
            pass

        # Inspect elements
        html = await page.evaluate("""() => {
            const container = document.querySelector('.sportName.soccer') || document.body;
            const items = Array.from(container.children).slice(0, 30).map(el => ({
                tag: el.tagName,
                classes: el.className,
                id: el.id,
                text: el.innerText.substring(0, 50)
            }));
            return items;
        }""")
        
        print("First 30 children of sport container:")
        for item in html:
            print(f"[{item['tag']}] id={item['id']} class={item['classes']} text={item['text']}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(diagnostic())
