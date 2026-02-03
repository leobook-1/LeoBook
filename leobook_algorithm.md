# LeoBook Execution Path & Algorithm (v2.1)

## 1. High-Level Linear Overview

LeoBook executes a continuous infinite loop managed by `Leo.py`. Upon startup, it initializes CSV databases and ensures the local AI server (`Mind/llama-server`) is running. It then enters **Phase 0 (Review)** to analyze past bets. **Phase 1 (Analysis)** launches a headless browser for Flashscore, employing a "Scorched Earth" CSS injection to permanently hide all cookie banners and overlays. It extracts match data using the restored, reliable "Old Method" (day-only scan), generating predictions via the `RuleEngine`. **Phase 2 (Booking)** implements the **"Harvest & Execute"** strategy: matches are visited individually in a persistent mobile context to generate and save "Booking Codes" (Phase 2a), which are then combined into a single multi-bet (Phase 2b). This prevents slip-clogging and maximizes reliability. The cycle concludes with **Phase 3 (Sleep)** for 6 hours.

---

## 2. Detailed Technical Flow

### **STARTUP (Leo.py)**
*   **Action**: Run `python Leo.py`
*   **Init**: `init_csvs()` creates `predictions.csv`, `site_matches.csv`, `withdrawals.csv` and `football_com_matches.csv`.
*   **AI Server**: `start_ai_server()` checks `http://127.0.0.1:8080/health`. If down, launches `run_split_model.bat/sh` and polls for 120s.

### **PHASE 0: REVIEW (Helpers/DB_Helpers/review_outcomes.py)**
*   **Function**: `run_review_process()`
*   **Filter**: Get matches where `booking_status` == 'booked' AND `match_time` < Now.
*   **Subprocess**: `print_accuracy_report()` calculates Win/Loss ratios from `predictions.csv`.

### **PHASE 1: ANALYSIS (Sites/flashscore.py)**
*   **Restoration**: Reverted to original reliable day-only scan (v1.0 baseline).
*   **Hardening**: 
    1. **CSS Injection**: Global injection of `display: none !important` for `#onetrust-consent-sdk` and related IDs.
    2. **DOM Removal**: Recursive JS removal of blocking overlays.
    3. **CSS Restoration**: Restored CSS loading to ensure site stability and layout integrity.
*   **Workflow**:
    *   Navigate to "Scheduled" tab.
    *   Extract fixtures for current day.
    *   **Batch Worker**: `process_match_task` (Concurrent Tabs)
        *   Navigate to match link.
        *   **H2H**: `activate_h2h_tab` (with `force=True` click) -> `extract_h2h_data`.
        *   **Standings**: `activate_standings_tab` -> `extract_standings_data`.
        *   **Prediction**: `RuleEngine.analyze` -> `save_prediction` to `predictions.csv`.

### **PHASE 2: BOOKING (Sites/football_com/football_com.py)**
*   **Strategy**: **Harvest & Execute**
*   **Phase 2a: Harvest (`booking_code.py`)**:
    *   Iterate through pending predictions.
    *   Navigate to match.
    *   **Force Clear**: Call `force_clear_slip` (Removes all items, verifies 0).
    *   **Selection**: Search Market -> Click Outcome.
    *   **Booking**: Click "Book Bet" -> Extract Code/URL.
    *   **Save**: Update `football_com_matches.csv` with the booking code.
*   **Phase 2b: Execute (`placement.py`)**:
    *   Load all harvested codes.
    *   Visit `?shareCode=[CODE]` URLs to build multi-bet slip instantly.
    *   **Placement**: Verify balance -> Set stake -> Place -> Confirm.
    *   **Security**: If slip clearing fails repeatedly, system deletes `storage_state.json` to force session restart.

### **MANUAL MODULE: WITHDRAWAL (`Sites/football_com/booker/withdrawal.py`)**
*   **Workflow**: Pre-check balance -> Submit Amount -> Extract Confirmation Data (Bank/Account) -> Input PIN (Digit-by-digit) -> Verify "Pending" status -> Save to `withdrawals.csv`.

### **PHASE 3: CYCLE COMPLETION (Leo.py)**
*   **Action**: `asyncio.sleep(6 * 3600)`.

---

## 3. Data Flow Summary Table

| Data Entity | Storage Location | Key Operations |
| :--- | :--- | :--- |
| **Schedule** | `DB/schedules.csv` | Fixture tracking |
| **Predictions**| `DB/predictions.csv` | RuleEngine output |
| **Booking Codes**| `DB/football_com_matches.csv`| Harvested codes for execution |
| **Withdrawals**| `DB/withdrawals.csv` | Financial history |
| **Knowledge**  | `DB/knowledge.json` | Persistent Selector Memory |
| **Auth State** | `DB/Auth/storage_state.json`| Playwright session persistence |
| **Log Files**  | `Logs/` | Terminal output + Error screenshots |
