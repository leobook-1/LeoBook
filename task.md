# Task Checklist - LeoBook Algorithm Upgrade

- [x] **Startup & Initialization**
    - [x] Update `Leo.py` with strict phase loop (completed).
    - [x] Update `Leo.py` state tracking (pending full implementation).
    - [x] Update `init_csvs` in `db_helpers.py` (Add fields: football_com_url, booking_code, booking_url, status).

- [x] **Phase 2: Booking (Refactored)**
    - [x] **State & Orchestration**:
        - [x] Move AI server logic to "on-demand" usage.
        - [x] Implement global state logging in `Leo.py`.
    - [x] **Slip Management**:
        - [x] Implement `force_clear_slip` (retries + delete session on failure).
    - [x] **Phase 2a: Harvest (Single)**:
        - [x] Create `booking_code.py` -> `book_single_match` logic.
        - [x] Validate odds >= 1.20.
        - [x] Extract code/url and save to CSV.
        - [x] Investigate `Leo.py` around line 47.
        [x] Fix the unmatched brace in `Leo.py`.
        [x] Fix `ImportError` for `book_single_match` in `football_com` (renamed to `harvest_single_match_code`).
        [x] Fix `SyntaxError` in `placement.py` (removed stray backticks).
        [x] Fix Telegram event loop conflict in `Leo.py`.
        [x] Update `requirements.txt` with latest dependencies.
        [x] Fix indentation error in `matcher.py` (Done).
        [ ] Verify the complete system startup.
    - [x] **Phase 2b: Execution (Multi)**:
        - [x] Update `football_com.py` to drive Harvest -> Execute loop.
        - [x] Update `placement.py` -> `place_multi_bet_from_codes`.
        - [x] Enforce stake rules (min N1, max 50% bal).
    - [x] **Withdrawal**:
        - [x] Update `withdrawal.py` with min/max rules (min 500, max 30% bal).

- [x] **Phase 2 Robustness Upgrades**
    - [x] **AI Matcher**: Increase LLM timeout and optimize retry logic (Done).
    - [x] **Timezone Sync**: Align `predictions.csv` and site to Nigerian Time (UTC+1) (Done).
    - [x] **Market Discovery**: Implement search-based discovery (Click Search -> Input -> Enter) (Done).
    - [x] **Navigation**: Improve `football_com` selector robustness (Done).
    - [x] **Architecture**: Remove local LLM server and enforce OpenRouter (Done).
    - [ ] Copy artifacts to project root.
    - [ ] Verify no changes made to Phase 0 or Phase 1.
