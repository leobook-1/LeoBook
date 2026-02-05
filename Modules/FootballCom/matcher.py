# matcher.py: Multi-stage team name matching logic.
# Refactored for Clean Architecture (v2.7)
# This script combines difflib and LLM matching to resolve fixture URLs.

"""
Matcher Module
Handles matching predictions.csv data with extracted Football.com matches using Leo AI.
"""

import csv
import difflib
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

from pathlib import Path
from Data.Access.db_helpers import PREDICTIONS_CSV, update_prediction_status
# Import LLM matcher conditionally
try:
    import Core.Intelligence.llm_matcher as llm_module
    HAS_LLM = True
except ImportError:
    llm_module = None
    HAS_LLM = False
    print("  [Matcher] Warning: LLM dependencies not found. Falling back to simple fuzzy matching.")

# Import RapidFuzz for faster and more accurate fuzzy matching
try:
    from rapidfuzz import fuzz, process
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False
    print("  [Matcher] Warning: RapidFuzz not found. Falling back to difflib.")


async def filter_pending_predictions() -> List[Dict]:
    """Load and filter predictions that are pending booking."""
    pending_predictions = []
    csv_path = Path(PREDICTIONS_CSV)
    if csv_path.exists():
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            pending_predictions = [row for row in reader if row.get('status') == 'pending']
    print(f"  [Matcher] Found {len(pending_predictions)} pending predictions.")
    return pending_predictions


def normalize_team_name(name: str) -> str:
    """Basic normalization: lower, strip, remove common suffixes/prefixes."""
    if not name:
        return ""
    name = name.lower().strip()
    # Remove common suffixes like FC, AFC, CF, etc. and Brazilian state abbreviations
    suffixes = [
        'fc', 'afc', 'cf', 'sc', 'ac', 'club', 'united', 'city', 'athletic', 'fb',
        'sp', 'rj', 'mg', 'rs', 'pr', 'ba', 'ce', 'pe', 'go', 'sc', 'pb', 'rn', 'al', 'se', 'mt', 'ms', 'pa', 'am'
    ]
    for suffix in suffixes:
        if name.endswith(' ' + suffix):
            name = name[:-len(suffix)-1].strip()
        elif name.endswith(' ' + suffix + ')'): # handle (SP)
             name = name[:-len(suffix)-2].strip()
        elif name == suffix:
            name = ""
    return name


def calculate_similarity(str1: str, str2: str) -> float:
    """Calculate similarity using RapidFuzz (token_set_ratio) or fallback to difflib."""
    if not str1 or not str2:
        return 0.0
    norm1 = normalize_team_name(str1)
    norm2 = normalize_team_name(str2)
    if HAS_RAPIDFUZZ:
        try:
            from rapidfuzz import fuzz
            return fuzz.token_set_ratio(norm1, norm2) / 100.0
        except ImportError:
            return difflib.SequenceMatcher(None, norm1, norm2).ratio()
    else:
        return difflib.SequenceMatcher(None, norm1, norm2).ratio()


def build_match_string(region_league: str, home: str, away: str, date: str, time: str) -> str:
    """
    Build a canonical full match string for holistic comparison:
    "Region - League: Home Team vs Away Team - Date - Time"
    """
    return f"{region_league}: {home} vs {away} - {date} - {time}".strip().lower()


def parse_match_datetime(date_str: str, time_str: str, is_site_format: bool = False) -> Optional[datetime]:
    """
    Parse date and time strings into a datetime object (assumed UTC for predictions, displayed UTC+1 for site).
    """
    if not date_str or not time_str:
        return None

    time_str = time_str.strip()
    date_str = date_str.strip()

    if is_site_format:
        # Site time_str can be "14:00", "Live", "45'", or "17 Dec, 20:30"
        try:
            # Case 1: "17 Dec, 20:30"
            if ',' in time_str:
                parts = time_str.split(',', 1)
                site_date_part = parts[0].strip()   # e.g. "17 Dec"
                site_time_part = parts[1].strip()   # e.g. "20:30"
                
                # Try to parse the date part to get day and month
                # Football.com uses "17 Dec"
                dt_site_date = datetime.strptime(site_date_part, "%d %b")
                dt_site_time = datetime.strptime(site_time_part, "%H:%M")
                
                # Use year from date_str (targetDate)
                target_year = datetime.strptime(date_str, "%d.%m.%Y").year
                return datetime(target_year, dt_site_date.month, dt_site_date.day, dt_site_time.hour, dt_site_time.minute)

            # Case 2: "14:00"
            if ':' in time_str:
                dt_time = datetime.strptime(time_str.strip(), "%H:%M")
                dt_date = datetime.strptime(date_str, "%d.%m.%Y")
                return datetime(dt_date.year, dt_date.month, dt_date.day, dt_time.hour, dt_time.minute)

            # Case 3: "Live", "45'", etc. (Treat as "now" on the target date)
            dt_date = datetime.strptime(date_str, "%d.%m.%Y")
            return datetime(dt_date.year, dt_date.month, dt_date.day, datetime.now().hour, datetime.now().minute)

        except Exception as e:
            # print(f"    [Time Parse Error] Failed to parse site time '{time_str}' with date '{date_str}': {e}")
            return None
    else:
        try:
            return datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")
        except ValueError:
            return None


async def match_predictions_with_site(day_predictions: List[Dict], site_matches: List[Dict]) -> Dict[str, str]:
    """
    Match predictions to site matches primarily by holistic string similarity on the full
    "Region - League: Home vs Away - Date - Time" descriptor, with datetime priority and optional LLM fallback.
    """
    # Filter out predictions for matches that have already started or start in < 10 mins (Safety Buffer)
    # Both predictions.csv and site are in Nigerian Time (UTC+1)
    # Both predictions.csv and site are in Nigerian Time (UTC+1)
    now_nigeria = datetime.utcnow() + timedelta(hours=1)
    cutoff_time = now_nigeria + timedelta(minutes=10)
    print(f"  [Matcher] Filtering matches before {cutoff_time.strftime('%H:%M')} (Nigeria Time + 10m buffer)")
    future_predictions = []
    for pred in day_predictions:
        pred_date = pred.get('date', '').strip()
        pred_time = pred.get('match_time', '').strip()
        pred_dt = parse_match_datetime(pred_date, pred_time, is_site_format=False)
        if pred_dt and pred_dt > (now_nigeria + timedelta(minutes=10)):
            future_predictions.append(pred)

    if not future_predictions:
        print("  [Matcher] No future pending predictions found within Nigerian Time (UTC+1).")
        return {}

    day_predictions = future_predictions
    print(f"  [Matcher] Attempting to match {len(day_predictions)} future predictions (Nigerian Time).")

    # Initialise LLM matcher once if available
    llm_matcher: Optional[Any] = None
    if HAS_LLM and llm_module:
        try:
            llm_matcher = llm_module.SemanticMatcher()
            print("  [Matcher] LLM Semantic Matcher initialized.")
        except Exception as e:
            print(f"  [Matcher] Failed to initialise LLM matcher: {e}")

    # --- Pre-filter Site Matches ---
    # Remove matches with empty or suspiciously short names (e.g. " vs ")
    valid_site_matches = []
    for m in site_matches:
            # Handle both DB format (home_team/away_team) and matcher format (home/away)
            h = m.get('home', '') or m.get('home_team', '')
            a = m.get('away', '') or m.get('away_team', '')
            h = h.strip() if h else ''
            a = a.strip() if a else ''
            if len(h) < 2 or len(a) < 2:
                continue
            valid_site_matches.append(m)
    
    if len(valid_site_matches) < len(site_matches):
        print(f"  [Matcher] Filtered out {len(site_matches) - len(valid_site_matches)} invalid site matches (empty names).")
    site_matches = valid_site_matches

    mapping: Dict[str, str] = {}

    used_site_urls = set()

    for pred in day_predictions:
        pred_id = str(pred.get('fixture_id', ''))
        pred_region_league = pred.get('region_league', '').strip()
        pred_home = pred.get('home_team', '').strip()
        pred_away = pred.get('away_team', '').strip()
        pred_date = pred.get('date', '').strip()
        pred_time = pred.get('match_time', '').strip()

        pred_full_str = build_match_string(pred_region_league, pred_home, pred_away, pred_date, pred_time)

        pred_dt = parse_match_datetime(pred_date, pred_time, is_site_format=False)

        # Phase 1: Score all candidates
        candidates = []
        for site_match in site_matches:
            site_url = site_match.get('url', '')
            if not site_url or site_url in used_site_urls:
                continue

            site_region_league = site_match.get('league', '').strip()
            # Handle both DB format (home_team/away_team) and matcher format (home/away)
            site_home = site_match.get('home', '') or site_match.get('home_team', '')
            site_away = site_match.get('away', '') or site_match.get('away_team', '')
            site_home = site_home.strip()
            site_away = site_away.strip()
            site_date = site_match.get('date', '').strip()
            site_time = site_match.get('time', '').strip()

            site_full_str = build_match_string(site_region_league, site_home, site_away, site_date, site_time)
            full_similarity = calculate_similarity(pred_full_str, site_full_str)

            # 1. League Similarity Check (Penalty if disjoint)
            league_sim = calculate_similarity(pred_region_league, site_region_league)
            league_penalty = -0.15 if league_sim < 0.82 else 0.0

            # 2. Direction Check (Home/Away Swap Prevention)
            # Compare home-home and away-away vs home-away and away-home
            h_h_sim = calculate_similarity(pred_home, site_home)
            a_a_sim = calculate_similarity(pred_away, site_away)
            
            h_a_sim = calculate_similarity(pred_home, site_away)
            a_h_sim = calculate_similarity(pred_away, site_home)
            
            # If swapped similarity is significantly higher than direct similarity, it's likely a swap
            is_swapped = (h_a_sim + a_h_sim) > (h_h_sim + a_a_sim + 0.3)
            swap_penalty = -0.5 if is_swapped else 0.0

            # 3. Datetime Bonus (Synced to Nigerian Time)
            site_dt = parse_match_datetime(site_date, site_time, is_site_format=True)

            time_bonus = 0.0
            if pred_dt and site_dt:
                time_diff_minutes = abs((pred_dt - site_dt).total_seconds()) / 60
                if time_diff_minutes <= 30: 
                    time_bonus = 0.35 
                elif time_diff_minutes <= 90:
                    time_bonus = 0.15
            
            base_score = full_similarity
            total_score = base_score + time_bonus + league_penalty + swap_penalty
            
            candidates.append({
                'match': site_match,
                'total_score': total_score,
                'base_score': base_score,
                'full_str': site_full_str,
                'dt': site_dt
            })

        # Phase 2: Select Top Candidate
        if not candidates:
            print(f"  ✗ No candidates found for prediction {pred_id} ({pred_home} vs {pred_away})")
            continue
            
        candidates.sort(key=lambda x: x['total_score'], reverse=True)
        top = candidates[0]
        
        # Phase 3: LLM Verification (Only for the single best candidate if borderline)
        final_match_found = False

        if top['total_score'] >= 0.94: # Raised slightly
            final_match_found = True
            print(f"    [Matcher] Strong match found: {pred_home} vs {pred_away} (Score: {top['total_score']:.3f})")
        elif top['total_score'] >= 0.78:  # Raised slightly
            final_match_found = True
            print(f"    [Matcher] High confidence match found: {pred_home} vs {pred_away} (Score: {top['total_score']:.3f})")
        elif top['total_score'] >= 0.60 and llm_matcher:
            # Borderline case: Ask AI
            m = top['match']
            site_home = m.get('home', '') or m.get('home_team', '')
            site_away = m.get('away', '') or m.get('away_team', '')
            print(f"    [LLM Check] Verifying borderline candidate: Pred '{pred_home} vs {pred_away}' ↔ Site '{site_home} vs {site_away}' (Score: {top['total_score']:.3f})")

            llm_result = await llm_matcher.is_match(
                f"{pred_home} vs {pred_away} in {pred_region_league}",
                f"{site_home} vs {site_away} in {m.get('league', '')}",
                league=pred_region_league
            )

            # Handle upgraded LLM Response (True/False or Dict with confidence)
            if isinstance(llm_result, dict):
                is_match_val = llm_result.get('is_match')
                confidence = llm_result.get('confidence', 0)
                if is_match_val is True and confidence >= 85:
                    print(f"      -> AI confirmed match! (Confidence: {confidence}%)")
                    final_match_found = True
                else:
                    print(f"      -> AI rejected match (Confidence: {confidence}%).")
            elif llm_result is True:
                print("      -> AI confirmed match!")
                final_match_found = True
            elif llm_result is False:
                print("      -> AI rejected match.")
            else:
                # LLM failed/timeout - Tiered fallback
                if top['total_score'] >= 0.82: # Higher threshold for timeout acceptance
                    print("      -> AI timeout, but very high score - accepting match!")
                    final_match_found = True
                else:
                    print("      -> AI timeout, score too low - rejecting match.")

        if final_match_found:
            site_url = top['match'].get('url')
            mapping[pred_id] = site_url
            used_site_urls.add(site_url)
            time_str = pred_dt.strftime('%Y-%m-%d %H:%M') if pred_dt else 'N/A'
            m = top['match']
            site_home = m.get('home', '') or m.get('home_team', '')
            site_away = m.get('away', '') or m.get('away_team', '')
            print(f"  [OK] Matched prediction {pred_id} ({pred_home} vs {pred_away} @ {time_str}) "
                  f"-> {site_home} vs {site_away} (score {top['total_score']:.3f})")
        else:
            if top['total_score'] > 0.5: # Only print if there was a somewhat reasonable candidate
                print(f"  [X] No reliable match found for prediction {pred_id} ({pred_home} vs {pred_away}). Top candidate score {top['total_score']:.3f} was rejected or too low.")
            else:
                print(f"  [X] No reliable match found for prediction {pred_id} ({pred_home} vs {pred_away}). All candidates too low.")


    print(f"  [Matcher] Matching complete: {len(mapping)}/{len(day_predictions)} predictions matched.")
    return mapping
