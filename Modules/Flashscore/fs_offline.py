# fs_offline.py: Reprediction loop using stored data.
# Refactored for Clean Architecture (v2.7)
# This script re-runs the rule engine on matches already extracted to CSV.

from datetime import datetime as dt, timedelta
from zoneinfo import ZoneInfo
from playwright.async_api import Playwright
from Data.Access.db_helpers import get_all_schedules, get_standings, save_prediction
from Scripts.recommend_bets import get_recommendations
from Core.Intelligence.model import RuleEngine

NIGERIA_TZ = ZoneInfo("Africa/Lagos")

async def run_flashscore_offline_repredict(playwright: Playwright):
    """
    Offline reprediction mode: Uses stored CSV data.
    """
    print("\n   [Offline] Starting offline reprediction engine...")
    
    all_schedules = get_all_schedules()
    if not all_schedules:
        print("    [Offline Error] No schedules found in database.")
        return

    # Filter for scheduled matches
    scheduled_matches = [m for m in all_schedules if m.get('match_status') == 'scheduled']
    
    now = dt.now(NIGERIA_TZ)
    threshold = now + timedelta(hours=1)
    
    to_process = []
    for m in scheduled_matches:
        try:
            date_str = m.get('date')
            time_str = m.get('match_time')
            if not date_str or not time_str or time_str == 'N/A':
                continue
                
            match_dt = dt.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M").replace(tzinfo=NIGERIA_TZ)
            if match_dt > threshold:
                to_process.append(m)
        except Exception:
            continue

    print(f"    [Offline] Found {len(to_process)} future matches (> 1 hour away) to repredict.")
    
    if not to_process:
        return

    # Sort historical matches once
    def parse_date(d_str):
        try:
            return dt.strptime(d_str, "%d.%m.%Y")
        except:
            return dt.min

    historical_matches = [m for m in all_schedules if m.get('match_status') != 'scheduled' and m.get('home_score') not in ('', 'N/A', None) and m.get('away_score') not in ('', 'N/A', None)]
    historical_matches.sort(key=lambda x: parse_date(x.get('date', '')), reverse=True)

    total_repredicted = 0
    for m in to_process:
        home_team = m.get('home_team')
        away_team = m.get('away_team')
        region_league = m.get('region_league', 'Unknown')
        match_label = f"{home_team} vs {away_team}"

        # 1. Build H2H Data
        home_last_10 = []
        away_last_10 = []
        h2h_list = []
        
        for hist in historical_matches:
            h_home = hist.get('home_team')
            h_away = hist.get('away_team')
            hs = hist.get('home_score', '0')
            ascore = hist.get('away_score', '0')
            try:
                hsi = int(hs)
                asi = int(ascore)
                winner = "Home" if hsi > asi else "Away" if asi > hsi else "Draw"
            except:
                winner = "Draw"
                
            mapped_hist = {
                "date": hist.get("date"),
                "home": h_home,
                "away": h_away,
                "score": f"{hs}-{ascore}",
                "winner": winner
            }

            if (h_home == home_team or h_away == home_team) and len(home_last_10) < 10:
                home_last_10.append(mapped_hist)
            if (h_home == away_team or h_away == away_team) and len(away_last_10) < 10:
                away_last_10.append(mapped_hist)
            if ((h_home == home_team and h_away == away_team) or (h_home == away_team and h_away == home_team)):
                h2h_list.append(mapped_hist)

        h2h_data = {
            "home_team": home_team,
            "away_team": away_team,
            "home_last_10_matches": home_last_10,
            "away_last_10_matches": away_last_10,
            "head_to_head": h2h_list,
            "region_league": region_league
        }

        # 2. Get Standings
        raw_standings = get_standings(region_league)
        standings_data = []
        for s in raw_standings:
            try:
                standings_data.append({
                    "team_name": s.get("team_name"),
                    "position": int(s.get("position", 0)),
                    "goal_difference": int(s.get("goal_difference", 0)),
                    "goals_for": int(s.get("goals_for", 0)),
                    "goals_against": int(s.get("goals_against", 0))
                })
            except:
                continue

        # 3. Data Quality Validation
        if len(home_last_10) < 3 or len(away_last_10) < 3:
            continue

        # 4. Predict
        analysis_input = {"h2h_data": h2h_data, "standings": standings_data}
        try:
            prediction = RuleEngine.analyze(analysis_input)
            
            if prediction.get("type", "SKIP") != "SKIP":
                match_data_for_save = m.copy()
                match_data_for_save['id'] = m.get('fixture_id')
                match_data_for_save['time'] = m.get('match_time')
                
                save_prediction(match_data_for_save, prediction)
                total_repredicted += 1
                if total_repredicted % 10 == 0:
                    print(f"    [Offline] Repredicted {total_repredicted} matches...")
        except Exception as e:
            print(f"      [Offline Error] Failed predicting {match_label}: {e}")

    print(f"\n--- Offline Reprediction Complete: {total_repredicted} matches repredicted. ---")
    
    print("\n   [Auto] Generating betting recommendations after offline update...")
    get_recommendations(save_to_file=True)
