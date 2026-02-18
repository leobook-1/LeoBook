# LeoBook v2.9 Algorithm & Codebase Reference

> **Version**: 2.9 · **Last Updated**: 2026-02-18 · **Architecture**: Clean Architecture (Orchestrator → Module → Data)

This document maps the **execution flow** of [Leo.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Leo.py) to specific files and functions. For the complete file inventory, see [LeoBook_Technical_Master_Report.md](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/LeoBook_Technical_Master_Report.md).

---

## System Architecture

Leo.py is a **pure orchestrator** (275 lines, zero business logic). It runs an infinite `while True` loop, executing 4 phases sequentially every `LEO_CYCLE_WAIT_HOURS` (default 6h).

```
Leo.py (Orchestrator)
├── Prologue: Cloud Sync → Outcome Review → Enrichment → Accuracy → Final Sync
├── Chapter 1: Flashscore Extraction → AI Prediction → Odds Harvesting → Recommendations
├── Chapter 2: Automated Bet Placement → Withdrawal Management
├── Chapter 3: Chief Engineer Oversight & Health Check
└── Live Streamer: Parallel 60s LIVE score streaming (asyncio.create_task)
```

---

## Prologue: Enrichment & Cloud Sync

**Objective**: Sync with cloud, review past outcomes, enrich metadata, compute accuracy.

### Page 1: Cloud Handshake & Review

1. [sync_manager.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Data/Access/sync_manager.py): `SyncManager.sync_on_startup()` — bi-directional Supabase ↔ CSV sync
2. [review_outcomes.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Data/Access/review_outcomes.py): `run_review_process()` — orchestrates outcome review
   - [outcome_reviewer.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Data/Access/outcome_reviewer.py): `get_predictions_to_review()` → `process_review_task()` (concurrent, 5 workers) → navigates to Flashscore → extracts final score → marks W/L/D
   - [prediction_evaluator.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Data/Access/prediction_evaluator.py): `evaluate_prediction()` — resolves bet outcome
3. [prediction_accuracy.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Data/Access/prediction_accuracy.py): `print_accuracy_report()` — generates performance report

### Page 2: Metadata Enrichment

1. [enrich_all_schedules.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Scripts/enrich_all_schedules.py): `enrich_all_schedules(extract_standings=True)` — visits all match URLs in `schedules.csv` (22k+), extracts:
   - Team IDs, crests, URLs → `teams.csv`
   - Region ↔ league mappings → `region_league.csv`
   - League standings → `standings.csv`
   - Missing datetime, scores → `schedules.csv` backfill

### Page 3: Accuracy & Final Sync

1. [review_outcomes.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Data/Access/review_outcomes.py): `run_accuracy_generation()` — compute accuracy reports → `accuracy_reports.csv`
2. [sync_manager.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Data/Access/sync_manager.py): `run_full_sync("Prologue Final")` — push all local changes to Supabase

---

## Chapter 1: Discovery & Prediction

**Objective**: Extract today's matches, generate AI predictions, harvest odds, generate recommendations.

### Page 1: Flashscore Extraction & AI Prediction

1. [manager.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Modules/Flashscore/manager.py): `run_flashscore_analysis()` — launches browser, navigates to Flashscore
2. [fs_schedule.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Modules/Flashscore/fs_schedule.py): `extract_matches_from_page()` — scrapes today's fixtures (IDs, URLs, teams, times)
3. [fs_processor.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Modules/Flashscore/fs_processor.py): `process_match_task()` — concurrent worker (5 workers) per match:
   - Navigates to match page
   - [h2h_extractor.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Core/Browser/Extractors/h2h_extractor.py): `extract_h2h_data()` — parses match history
   - [standings_extractor.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Core/Browser/Extractors/standings_extractor.py): `extract_standings_data()` — parses league tables
4. [intelligence.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Core/Intelligence/intelligence.py): `make_prediction()` — orchestrates AI prediction:
   - [ml_model.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Core/Intelligence/ml_model.py): `MLModel.predict()` — RandomForest/XGBoost pattern matching
   - [goal_predictor.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Core/Intelligence/goal_predictor.py): `predict_goals_distribution()` — Poisson probability calculation
   - [rule_engine.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Core/Intelligence/rule_engine.py): `RuleEngine.analyze()` — applies user-defined rules
   - [tag_generator.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Core/Intelligence/tag_generator.py): generates labels (`HIGH_CONFIDENCE`, `UPSET_ALERT`, `FORM_S2+`)
   - [betting_markets.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Core/Intelligence/betting_markets.py): `select_best_market()` — chooses optimal market (1X2, O/U, BTTS, etc.)
5. [db_helpers.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Data/Access/db_helpers.py): `save_prediction()` → `predictions.csv`

### Page 2: Odds Harvesting

1. [fb_manager.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Modules/FootballCom/fb_manager.py): `run_odds_harvesting()` — launches Football.com session
2. [fb_session.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Modules/FootballCom/fb_session.py): `launch_browser_with_retry()` — persistent auth session
3. [navigator.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Modules/FootballCom/navigator.py): `load_or_create_session()`, `extract_balance()` — validates account state
4. [fb_url_resolver.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Modules/FootballCom/fb_url_resolver.py): `resolve_urls()` — fuzzy-matches Flashscore → Football.com URLs
   - [matcher.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Modules/FootballCom/matcher.py): Team name fuzzy matching (Levenshtein + AI batch prompt)
5. [booking_code.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Modules/FootballCom/booker/booking_code.py): `harvest_booking_codes()` — visits each match, clicks outcome, extracts booking code, clears slip
6. Uses **AIGO** (`interaction_engine` → `aigo_engine`) for resilient UI actions when selectors fail

### Page 3: Final Sync & Recommendations

1. [sync_manager.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Data/Access/sync_manager.py): `run_full_sync("Chapter 1 Final")` — push predictions to Supabase
2. [recommend_bets.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Scripts/recommend_bets.py): `get_recommendations(save_to_file=True)` — ranks predictions by confidence × market reliability → saves `recommended.json` + updates `predictions.csv`

---

## Chapter 2: Automated Booking & Funds

**Objective**: Place bets from harvested codes and manage bankroll.

### Page 1: Automated Booking

1. [fb_manager.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Modules/FootballCom/fb_manager.py): `run_automated_booking()` — launches Football.com session
2. [placement.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Modules/FootballCom/booker/placement.py): `place_multi_bet_from_codes()`:
   - Loops through harvested codes for the date
   - Injects codes via the bookmaker's "m-m" URL
   - Verifies slip count matches expected
   - Calculates **Fractional Kelly Stake** based on total balance (min ₦100, max 50% balance)
   - Places & confirms bet
   - Updates `predictions.csv` to `status: booked`
3. Uses **AIGO** for bet slip interactions (`slip_aigo.py`)

### Page 2: Funds & Withdrawal

1. [navigator.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Modules/FootballCom/navigator.py): `extract_balance()` — extracts post-booking balance
2. [withdrawal_checker.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Core/System/withdrawal_checker.py): `check_triggers()` — evaluates withdrawal conditions (profit threshold, time since last)
3. [withdrawal_checker.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Core/System/withdrawal_checker.py): `propose_withdrawal()` → `check_withdrawal_approval()` → `execute_withdrawal()`
4. [withdrawal.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Modules/FootballCom/booker/withdrawal.py): `withdraw_amount()`:
   - Enforces ₦5,000 bankroll floor
   - Executes withdrawal flow (PIN entry, confirmation, verification)
   - Logs to audit trail

---

## Chapter 3: Chief Engineer Oversight

**Objective**: System health monitoring and reporting.

1. [monitoring.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Core/System/monitoring.py): `run_chapter_3_oversight()`:
   - `perform_health_check()` — checks:
     - Data store integrity (`predictions.csv` freshness)
     - Error count this cycle
     - Account balance status
     - Prediction volume (≥5 expected daily)
     - Bet placement success rate
   - `generate_oversight_report()` — formats report with cycle count, uptime, balance, health status
   - Logs `OVERSIGHT_REPORT` event to Supabase via `log_audit_event()`

---

## Live Streamer (Parallel)

**Objective**: Stream live scores every 60 seconds and propagate status changes to schedules + predictions.

Runs in parallel with the main cycle via `asyncio.create_task()` at the Playwright level.

1. [fs_live_streamer.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Modules/Flashscore/fs_live_streamer.py): `live_score_streamer()` — launches headless browser, clicks LIVE tab
   - `_extract_live_matches()` — JavaScript evaluation to scrape live scores, minutes, statuses
   - `_propagate_status_updates()` — updates `schedules.csv` and `predictions.csv`:
     - Marks fixtures as `live` with current scores
     - Detects finished matches (>2.5hrs past kickoff) and marks `finished`
     - Computes `outcome_correct` for finished predictions
   - [db_helpers.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Data/Access/db_helpers.py): `save_live_score_entry()` — upserts to `live_scores.csv`
   - Syncs to Supabase `live_scores` table via `SyncManager.batch_upsert()`
   - Self-healing: page reload on extraction errors, full navigation reset on failures

---

## Self-Healing & Resilience Layer (AIGO v5.0)

This layer operates **globally across all chapters**. See [AIGO_Learning_Guide.md](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/AIGO_Learning_Guide.md) for the full 5-phase pipeline.

| Component | File | Key Function |
|-----------|------|-------------|
| **AIGO Engine** | [aigo_engine.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Core/Intelligence/aigo_engine.py) | `invoke_aigo()` — Grok API expert consultation |
| **Interaction Engine** | [interaction_engine.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Core/Intelligence/interaction_engine.py) | `execute_smart_action()` — 5-phase cascade executor |
| **Selector Manager** | [selector_manager.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Core/Intelligence/selector_manager.py) | `get_selector_strict()` — AI-powered selector retrieval |
| **Visual Analyzer** | [visual_analyzer.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Core/Intelligence/visual_analyzer.py) | `analyze_page_and_update_selectors()` — screenshot + DOM analysis |
| **Memory Manager** | [memory_manager.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Core/Intelligence/memory_manager.py) | `store_memory()` — reinforcement learning patterns |
| **Popup Handler** | [popup_handler.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Core/Intelligence/popup_handler.py) | `fb_universal_popup_dismissal()` — overlay removal |

---

## Supported Betting Markets

1. 1X2 | 2. Double Chance | 3. Draw No Bet | 4. BTTS | 5. Over/Under | 6. Goal Ranges | 7. Correct Score | 8. Clean Sheet | 9. Asian Handicap | 10. Combo Bets | 11. Team O/U

---

**Chief Engineer**: Emenike Chinenye James
**Source of Truth**: Refactored Clean Architecture (v2.9)
