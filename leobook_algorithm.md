# LeoBook v3.5 Algorithm & Codebase Reference

> **Version**: 3.5 · **Last Updated**: 2026-02-26 · **Architecture**: High-Velocity Concurrent Architecture (Shared Locking + Parallel Pipeline)

This document maps the **execution flow** of [Leo.py](Leo.py) to specific files and functions.

---

## System Architecture

Leo.py is a **pure orchestrator**. It runs an infinite `while True` loop, splitting the cycle into three phases:
Leo.py (Orchestrator) v3.5
├── Phase 1 (Sequential Prerequisite):
│   └── Cloud Sync → Outcome Review → Accuracy report
├── Phase 2 (Parallel Execution Group):
│   ├── Task A: Parallel League Enrichment (Multi-Page Playwright)
│   ├── Task B: Async Search Dictionary Building
│   └── Task C: Main Chapter Pipeline (Extraction → Prediction → Booking)
├── Phase 3 (Sequential Oversight):
│   └── Chief Engineer Oversight → Withdrawal Management
└── Live Streamer: Background Parallel Task (Always-On)

---

## Live Streamer (Parallel v2.1)

**Objective**: Absolute real-time parity between Flashscore LIVE tab and the Flutter app.

Runs in parallel with the main cycle via `asyncio.create_task()`.

1. **Extraction**: [fs_live_streamer.py](Modules/Flashscore/fs_live_streamer.py) `live_score_streamer()`
   - Captures live scores, minutes, and statuses every 60s.
   - **v2.1 Robustness Fix**: Uses `extrasaction='ignore'` in CSV writer to handle schema drift.
2. **Status Propagation**: 
   - Marks fixtures as `live` in `predictions.csv`.
   - Detects `finished` matches (kickoff + 2.5h) even if the main cycle is sleeping.
   - Computes real-time `outcome_correct` for immediate app updates.
3. **App Handshake**: Upserts to `live_scores` table in Supabase via `SyncManager.batch_upsert()`.

---

## High-Velocity Concurrency (v3.5)

**Objective**: Maximize execution throughput while maintaining absolute data integrity.

1. **Parallel Orchestration**: `Leo.py` uses `asyncio.gather()` to run long-running enrichment and dictionary building in parallel with the main prediction pipeline.
2. **Concurrent Scrapers**: `enrich_leagues.py` implements multi-page processing, spawning up to `MAX_CONCURRENCY` browser pages simultaneously to process multiple leagues.
3. **Shared Locking (CSV_LOCK)**: All persistent data access is protected by a global `asyncio.Lock` in [db_helpers.py](Data/Access/db_helpers.py). This prevents race conditions when multiple scripts attempt to write to `teams.csv` or `region_league.csv` at the same time.
4. **Async Strategy**:
   - `build_search_dict.py`: Converted to fully async with `asyncio.to_thread` for LLM calls.
   - `enrich_leagues.py`: Refactored into worker tasks managing their own async contexts.

---

## Prediction Pipeline (Chapter 1)

1. **Discovery**: [fs_schedule.py](Modules/Flashscore/fs_schedule.py) extracts fixture IDs.
   - **v3.2 Robustness**: Implements 2-tier header expansion retry (JS bulk + Locator fallback) to ensure 100% fixture visibility.
2. **Analysis**: [fs_processor.py](Modules/Flashscore/fs_processor.py) collects H2H and Standings data.
3. **Core Engine**: [rule_engine.py](Core/Intelligence/rule_engine.py) `analyze()`
   - **Rule Logic**: [rule_config.py](Core/Intelligence/rule_config.py) defines the v3.0 logic constraints.
   - **Poisson Predictor**: [goal_predictor.py](Core/Intelligence/goal_predictor.py) handles O/U and BTTS probabilities.

---

## 5. Adaptive Learning Intelligence

**Objective**: Continuous evolution of prediction rule weights based on historical accuracy.

1. **Feedback Loop**: [outcome_reviewer.py](Data/Access/outcome_reviewer.py) calls `LearningEngine.update_weights()` after every review batch.
2. **Analysis**: [learning_engine.py](Core/Intelligence/learning_engine.py) matches `predictions.csv` outcomes against the reasoning tags used.
3. **Weight Evolution**:
   - Success triggers **positive reinforcement** for specific weights.
   - Failure triggers **penalty** and weight reduction.
   - Updates `learning_weights.json` (per-league) and syncs to Supabase.
4. **Integration**: `RuleEngine.analyze()` loads these adaptive weights via `LearningEngine.load_weights(region_league)`.

---

## 6. UI Documentation (Flutter v3.0)

See [leobookapp/README.md](leobookapp/README.md) for the "Telegram-grade" design specification.
