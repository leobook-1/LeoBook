# Leo
**Manufacturer**: Emenike Chinenye James  
**Powered by**: Grok 4, Qwen3-VL & Custom Llama Server

"""
Leo v3.2: Elite Autonomous Betting Agent (Manufacturer: Emenike Chinenye James)

A comprehensive AI-powered system that observes, analyzes, predicts, and executes betting strategies with advanced self-healing capabilities.

The prime objective of this Agent is to handle all sports analysis and betting accurately, enabling passive income from sports betting without constant manual interaction.

OVERVIEW:
Leo combines advanced data analysis, machine learning, and automated execution. The system features a hybrid AI architecture using local Qwen3-VL for routine vision tasks and xAI's Grok 4 for high-precision selector discovery and complex UI mapping.

LATEST UPDATES (v3.2.0):
- **v2.7 Algorithm Compliance**: Full implementation of the "Harvest -> Execute" strategy for maximum reliability.
- **Fractional Kelly Staking**: Precise risk-aware staking (0.25 * Kelly) clamped for bankroll safety.
- **Centralized Audit Logging**: All financial movements and cycle statuses are logged to `DB/audit_log.csv`.
- **Live Telegram Integration**: Semi-automated withdrawal flow and interactive monitoring.
    - Commands: `/balance`, `/status`, `/summary`, `/help`.
    - Approval: Reply **YES**/**NO** to withdrawal proposals.
- **Outcome Synchronization**: Phase 0 reviews now cross-sync results between prediction and match registries.

CORE ARCHITECTURE:
- **Dual-Browser System**: Persistent login sessions for Flashscore and Football.com.
- **Phase 2a (Harvest)**: Extracts individual booking codes from match URLs with odds verification (>= 1.20).
- **Phase 2b (Execute)**: Builds and places multi-bet accumulators via shareCode injection.
- **Self-Healing UI**: Automated selector discovery via Grok 4 and robust slip clearing with fatal escalation.
- **Modular Data Layer**: Optimized CSV storage with absolute pathing and centralized audit trails.

MAIN WORKFLOW:
1. INFRASTRUCTURE INIT:
   - **Windows**: `.\Mind\run_split_model.bat` or `USE_GROK_API=true` in `.env`.
   - **Initialization**: `init_csvs()` sets up the audit log and registries.

2. OBSERVE & DECIDE (Phases 0 & 1):
   - **Phase 0 (Review)**: Cross-syncs past outcomes and updates momentum weights.
   - **Phase 1 (Analysis)**: Generates high-confidence predictions via the Rule Engine.

3. ACT: PHASE 2 (Harvest -> Execute):
   - **Phase 2a (Harvest)**: Navigates to prediction URLs and extracts booking codes.
   - **Phase 2b (Execute)**: Injects codes via URL to build a multi-bet and places it using Kelly staking.
   - **Financial Safety**: Every placement is verified by balance delta checks and logged to an audit file.

4. VERIFY & WITHDRAW (Phase 3):
   - **Withdrawal**: Checks triggers (₦10k balance) and maintained bankroll floor (₦5,000).
   - **Audit**: Finalizes the cycle by logging `CYCLE_COMPLETE` after recording all events.

SUPPORTED BETTING MARKETS:
1. 1X2 | 2. Double Chance | 3. Draw No Bet | 4. BTTS | 5. Over/Under | 6. Goal Ranges | 7. Correct Score | 8. Clean Sheet | 9. Asian Handicap | 10. Combo Bets | 11. Team O/U

SYSTEM COMPONENTS:
- **Leo.py**: Main controller orchestrating the "Observe, Decide, Act" core loop.
- **Neo/**: The Brain (Model + Intelligence + Visual Analyzer).
- **Helpers/**: Utility systems (Audit, DB, Matcher, Navigator).
- **DB/**: Central data storage including the dynamic `audit_log.csv` and `knowledge.json`.

MAINTENANCE:
- Monitor **`DB/audit_log.csv`** for real-time financial transparency.
- Review **`walkthrough.md`** for detailed implementation logs of current session.
"""
