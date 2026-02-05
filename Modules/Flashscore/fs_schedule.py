# fs_schedule.py: Daily match list extraction for Flashscore.
# Refactored for Clean Architecture (v2.7)
# This script scrapes upcoming fixtures and their relative URLs.

import asyncio
from typing import List
from playwright.async_api import Page
from Core.Intelligence.selector_manager import SelectorManager

async def extract_matches_from_page(page: Page) -> list:
    """
    Executes JavaScript on the page to extract all match data for the visible day.
    """
    print("    [Extractor] Extracting match data from page...")

    selectors = {
        "match_rows": SelectorManager.get_selector("fs_home_page", "match_rows"),
        "match_row_home_team_name": SelectorManager.get_selector("fs_home_page", "match_row_home_team_name"),
        "match_row_away_team_name": SelectorManager.get_selector("fs_home_page", "match_row_away_team_name"),
        "league_header": SelectorManager.get_selector("fs_home_page", "league_header"),
        "league_category": SelectorManager.get_selector("fs_home_page", "league_category"),
        "league_title": SelectorManager.get_selector("fs_home_page", "league_title_link"),
    }

    return await page.evaluate(
        r"""(selectors) => {
            const matches = [];
            const rows = document.querySelectorAll(selectors.match_rows);

            rows.forEach((row) => {
                const linkEl = row.querySelector('a.eventRowLink') || row.querySelector('a');
                const homeEl = selectors.match_row_home_team_name ? row.querySelector(selectors.match_row_home_team_name) : null;
                let skip_match = false;
                const awayEl = selectors.match_row_away_team_name ? row.querySelector(selectors.match_row_away_team_name) : null;
                const timeEl = row.querySelector('.event__time');
                const rowId = row.getAttribute('id');
                const cleanId = rowId ? rowId.replace('g_1_', '') : null;

                let regionLeague = 'Unknown';
                try {
                    let prev = row.previousElementSibling;
                    while (prev) {
                        if ((selectors.league_header && prev.matches(selectors.league_header)) || prev.classList.contains('event__header')) {
                            const regionEl = selectors.league_category ? prev.querySelector(selectors.league_category) : prev.querySelector('.event__title--type');
                            const leagueEl = selectors.league_title ? prev.querySelector(selectors.league_title) : prev.querySelector('.event__title--name');
                            if (regionEl && leagueEl) {
                                regionLeague = regionEl.innerText.trim() + ' - ' + leagueEl.innerText.trim();
                                const headerText = prev.innerText.toLowerCase();
                                if (headerText.includes('draw')) {
                                    skip_match = true;
                                }
                            } else {
                                regionLeague = prev.innerText.trim().replace(/[\\r\\n]+/g, ' - ');
                            }
                            break;
                        }
                        prev = prev.previousElementSibling;
                    }
                } catch (e) {
                    regionLeague = 'Error Extracting';
                }
                if (linkEl && homeEl && awayEl && cleanId && !skip_match) {
                    const matchLink = linkEl.getAttribute('href');

                    let homeTeamId = null;
                    let awayTeamId = null;
                    let homeTeamUrl = null;
                    let awayTeamUrl = null;

                    if (matchLink) {
                        const cleanPath = matchLink.replace(/^(.*\/match\/football\/)/, '');
                        const parts = cleanPath.split('/').filter(p => p);

                        if (parts.length >= 2) {
                            const homeSegment = parts[0];
                            const awaySegment = parts[1];
                            const homeSlug = homeSegment.substring(0, homeSegment.lastIndexOf('-'));
                            homeTeamId = homeSegment.substring(homeSegment.lastIndexOf('-') + 1);
                            const awaySlug = awaySegment.substring(0, awaySegment.lastIndexOf('-'));
                            awayTeamId = awaySegment.substring(awaySegment.lastIndexOf('-') + 1);

                            homeTeamUrl = `https://www.flashscore.com/team/${homeSlug}/${homeTeamId}/`;
                            awayTeamUrl = `https://www.flashscore.com/team/${awaySlug}/${awayTeamId}/`;
                        }
                    }

                    matches.push({
                        id: cleanId,
                        match_link: matchLink,
                        home_team_id: homeTeamId, away_team_id: awayTeamId,
                        home_team_url: homeTeamUrl, away_team_url: awayTeamUrl,
                        home_team: homeEl.innerText.trim(), away_team: awayEl.innerText.trim(),
                        time: timeEl ? timeEl.innerText.trim() : 'N/A',
                        region_league: regionLeague
                    });
                }
            });
            return matches;
        }""", selectors)
