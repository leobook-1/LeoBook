# league_page_extractor.py: Extract league metadata and match URLs from a league's page.
# Part of LeoBook Core — Browser Extractors
#
# Functions: extract_league_match_urls(), get_active_leagues_from_main(), extract_league_metadata()
# Called by: enrich_match_metadata.py, Scripts/enrich_leagues.py

import asyncio
from typing import List, Dict, Any
from playwright.async_api import Page, TimeoutError
from Core.Intelligence.selector_manager import SelectorManager
from Core.Browser.site_helpers import fs_universal_popup_dismissal

CTX = "fs_league_page"


async def extract_league_match_urls(page: Page, league_url: str, mode: str = "results") -> List[str]:
    """
    Visits a league page (results or fixtures) and harvests all match URLs.
    """
    target_url = league_url.rstrip('/')
    if mode == "results":
        if not target_url.endswith("/results"):
            target_url += "/results/"
    else:
        if not target_url.endswith("/fixtures"):
            target_url += "/fixtures/"

    print(f"      [League Extractor] Visiting: {target_url}")

    try:
        await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(2)
        await fs_universal_popup_dismissal(page)

        # 1. Expand all matches ("Show more matches")
        show_more_sel = SelectorManager.get_selector(CTX, "show_more_matches") or ".event__more"
        max_expansions = 10
        expansions = 0

        while expansions < max_expansions:
            try:
                show_more_btn = page.locator(show_more_sel)
                if await show_more_btn.is_visible(timeout=5000):
                    await show_more_btn.click()
                    await asyncio.sleep(2)
                    expansions += 1
                else:
                    break
            except:
                break

        # 2. Extract Match IDs/Links using SelectorManager
        match_row_sel = SelectorManager.get_selector(CTX, "match_row") or "[id^='g_1_']"
        js_code = """(matchRowSel) => {
            const links = new Set();
            document.querySelectorAll(matchRowSel).forEach(el => {
                const id = el.id.replace('g_1_', '');
                if (id) links.add(`/match/${id}/#/match-summary`);
            });
            return Array.from(links);
        }"""

        match_links = await page.evaluate(js_code, match_row_sel)
        print(f"      [League Extractor] Found {len(match_links)} match URLs on page.")
        return match_links

    except Exception as e:
        print(f"      [League Extractor Error] Failed to process {target_url}: {e}")
        return []


async def get_active_leagues_from_main(page: Page) -> List[Dict[str, str]]:
    """
    Optional: Scrapes the main page to find all 'live' or 'today' league URLs.
    """
    try:
        js_code = """() => {
            const leagues = [];
            document.querySelectorAll('.event__header').forEach(el => {
                const link = el.querySelector('a.event__title--link');
                const title = el.querySelector('.event__title--name');
                if (link && title) {
                    leagues.push({ name: title.innerText.trim(), url: link.href });
                }
            });
            return leagues;
        }"""
        return await page.evaluate(js_code)
    except:
        return []


async def extract_league_metadata(page: Page) -> Dict[str, str]:
    """
    Extracts league metadata from the league page header using SelectorManager.
    All selectors come from knowledge.json 'fs_league_page' context.
    """
    try:
        crest_sel = SelectorManager.get_selector(CTX, "league_crest") or "img.heading__logo"
        flag_sel = SelectorManager.get_selector(CTX, "region_flag") or ".breadcrumb__flag"
        name_sel = SelectorManager.get_selector(CTX, "league_name") or ".heading__name"
        region_sel = SelectorManager.get_selector(CTX, "region_name") or ".breadcrumb__link"

        # Try to extract league_id hash from URL
        # e.g. https://www.flashscore.com/football/england/premier-league/OEEq9Yvp/
        current_url = page.url
        league_id_hash = ""
        if "#/" in current_url:
            try:
                hash_part = current_url.split("#/")[1].split("/")[0]
                if hash_part and len(hash_part) >= 8:
                    league_id_hash = hash_part
            except:
                pass

        js_code = """(selectors) => {
            const { crestSel, flagSel, nameSel, regionSel } = selectors;

            // League crest: <img class="heading__logo" src="...">
            const league_crest = document.querySelector(crestSel)?.src || '';

            // Region flag: <span class="breadcrumb__flag flag fl_198"> (CSS sprite)
            const flagEl = document.querySelector(flagSel);
            let region_flag = '';
            if (flagEl) {
                const flClass = Array.from(flagEl.classList).find(c => c.startsWith('fl_'));
                if (flClass) region_flag = flClass;
            }

            // Breadcrumb links: 1st is Football, 2nd is Region
            const links = document.querySelectorAll(regionSel);
            const region = links.length > 1 ? links[1].innerText.trim() : '';
            const region_url = links.length > 1 ? links[1].href : '';

            // League name
            const league_name = document.querySelector(nameSel)?.innerText.trim() || '';

            return { league_crest, region_flag, region, region_url, league_name };
        }"""
        data = await page.evaluate(js_code, {
            "crestSel": crest_sel,
            "flagSel": flag_sel,
            "nameSel": name_sel,
            "regionSel": region_sel
        })
        
        # If we didn't find the hash in the URL already, return what we have
        if league_id_hash:
            data["league_id"] = league_id_hash
            
        return data
    except:
        return {}

