# LeoBook Execution Path & Algorithm (v2.7)

## 1. High-Level Linear Overview

LeoBook executes a continuous infinite loop managed by `Leo.py`. Upon startup, it initializes CSV databases, including the central **Audit Log**, and sets up a global **State Dictionary** for cycle-long awareness. It then enters **Phase 0 (Review)** to analyze past bets, synchronize outcomes (WON/LOST) across all registries, and print accuracy reports. **Phase 1 (Analysis)** produces predictions. **Phase 2 (Booking)** follows the **Harvest -> Execute** strategy for Football.com: it first gathers individual booking codes (Harvest) and then builds a multi-bet accumulator via shareCode injection (Execute). This phase uses **Fractional Kelly Staking** for risk-aware sizing. **Phase 3 (Withdrawal)** checks advanced triggers (Balance >= 10k) and processes withdrawals while maintaining a strict **₦5,000 bankroll floor**. Every critical financial event is recorded in `DB/audit_log.csv`.

---

## 2. Detailed Textual Flowchart

### **STARTUP (Leo.py)**
*   **Action**: Run `python Leo.py`
*   **Initialization**: `init_csvs()` ensures `audit_log.csv` and match registries are ready.
*   **State**: `state["current_balance"]` and `state["cycle_count"]` initialized.

### **PHASE 0: REVIEW (Leo.py -> review_outcomes.py)**
*   **Action**: Harvest results from past matches.
*   **Sync**: Update WON/LOST status in both `predictions.csv` and `football_com_matches.csv`.
*   **Report**: Generate accuracy metrics and momentum weighting.

### **PHASE 1: ANALYSIS (Leo.py -> flashscore.py)**
*   **Action**: Scrape H2H/Standings -> Generate predictions -> Save as `pending`.

### **PHASE 2: BOOKING (Leo.py -> football_com.py)**
*   **Step 1: Session & Force Slip Clear**
    *   **Function**: `force_clear_slip(page)`
    *   **Escalation**: 3 retries. On final failure, delete `storage_state.json` and raise `FatalSessionError` to force a hard restart.
*   **Step 2: PHASE 2a - HARVEST (booking_code.py)**
    *   **Function**: `harvest_single_match_code(page, match, prediction)`
    *   **Logic**: Navigate -> `select_outcome` (Market search + expansion) -> **Odds Check (>= 1.20)** -> Book -> Extract Code/URL.
    *   **Status**: Mark as `harvested` in `football_com_matches.csv`.
*   **Step 3: PHASE 2b - EXECUTE (placement.py)**
    *   **Function**: `place_multi_bet_from_codes(page, harvested_matches, balance)`
    *   **Logic**: 
        1. Inject up to 12 codes via URL.
        2. Verify slip counter.
        3. **Kelly Staking**: `0.25 * ((probability * odds - 1) / (odds - 1))`.
        4. Clamp: Min (max(1% balance, ₦1)), Max (50% balance).
        5. Place -> Confirm -> Verify Balance Delta -> Audit Log.
    *   **Status**: Mark as `booked` in all registries.

### **PHASE 3: WITHDRAWAL & CYCLE END (Leo.py -> withdrawal.py)**
*   **Triggers**:
    *   Balance >= ₦10,000.
    *   Significant 7-day net win.
*   **Process (Semi-Automated)**:
    *   Leo proposes withdrawal via **Telegram (@LeoBookBot)**.
    *   **Approval Loop**: Polling listener waits 30 mins for user reply ("YES"/"NO").
    *   **Execution**: On "YES", Leo opens an isolated browser context to perform the withdrawal while maintaining the **₦5,000 floor**.
    *   **Timeout**: Auto-cancels and logs if no reply within 30 mins.
*   **Cycle End**: Log `CYCLE_COMPLETE` to audit log and sleep for 6 hours.

---

## 3. Data Flow Summary Table

| Data Entity | Primary Storage | Key Logic |
| :--- | :--- | :--- |
| **Audit Log** | `DB/audit_log.csv` | Central truth for all financial movements. |
| **Predictions** | `DB/predictions.csv` | Cross-syncs with site matches during Phase 0 review. |
| **Site Matches** | `DB/football_com_matches.csv`| Tracks `harvested` codes and execution status. |
| **State** | In-Memory (`Leo.state`) | Real-time balance and cycle tracking. |
| **Session** | `DB/ChromeData_v3` | Aggressively cleared if UI becomes inconsistent. |
| **Stake Model** | Fractional Kelly (0.25) | Balances growth with high-reliability risk management. |

---

### **TELEGRAM INTERFACE (v2.7)**
*   **Proactive Commands**:
    *   `/balance`: Returns the last known account balance.
    *   `/status`: Returns current phase, cycle count, and success/fail metrics.
    *   `/summary`: Shows the last 5 entries from the Audit Log.
    *   `/help`: Lists available interaction options.
*   **Approval Flow**:
    *   Leo proposes withdrawal -> User replies **YES**/**NO** -> Isolated execution.
