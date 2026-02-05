# fb_url_resolver.py: Match discovery and URL mapping for Football.com.
# Refactored for Clean Architecture (v2.7)
# This script executes search/navigation to find specific match pages.

from playwright.async_api import Page
from Data.Access.db_helpers import (
    load_site_matches, save_site_matches, update_site_match_status
)
from .navigator import navigate_to_schedule, select_target_date
from .extractor import extract_league_matches
from .matcher import match_predictions_with_site

async def resolve_urls(page: Page, target_date: str, day_preds: list) -> dict:
    """
    Resolves URLs for predictions by checking cache, then scraping if needed.
    Returns: mapped_urls {fixture_id: url}
    """
    cached_site_matches = load_site_matches(target_date)
    matched_urls = {}
    unmatched_predictions = []

    for pred in day_preds:
        fid = str(pred.get('fixture_id'))
        cached_match = next((m for m in cached_site_matches if m.get('fixture_id') == fid), None)
        if cached_match and cached_match.get('url'):
            if cached_match.get('booking_status') != 'booked':
                matched_urls[fid] = cached_match.get('url')
        else:
            unmatched_predictions.append(pred)

    if unmatched_predictions:
        print(f"  [Registry] Resolving {len(unmatched_predictions)} unmatched URLs...")
        await navigate_to_schedule(page)
        if await select_target_date(page, target_date):
            site_matches = await extract_league_matches(page, target_date)
            if site_matches:
                save_site_matches(site_matches)
                cached_site_matches = load_site_matches(target_date)
                new_mappings = await match_predictions_with_site(unmatched_predictions, cached_site_matches)
                for fid, url in new_mappings.items():
                    matched_urls[fid] = url
                    site_match = next((m for m in cached_site_matches if m.get('url') == url), None)
                    if site_match:
                        update_site_match_status(site_match['site_match_id'], 'pending', fixture_id=fid)

    return matched_urls
