# Leo
**Manufacturer**: Emenike Chinenye James  
**Powered by**: DeepMind x Grok 4 Hybrid Architecture


"""
Leo v3.2: Elite Autonomous Betting Agent
A production-grade "Observe, Decide, Act" system with hardened extraction and reliable betting execution.

OVERVIEW:
Leo is an intelligent football prediction system that combines advanced data analysis, machine learning, and automated betting execution. The system features a hybrid AI architecture using local multimodal models for routine vision tasks and xAI's Grok 4 for high-precision selector discovery and complex UI mapping.

LATEST UPDATES (v3.2.0):
- **Phase 1 Restoration**: Flashscore analysis reverted to the high-reliability "Old Method" (Day-only scan).
- **Hardened Extraction**: Implementation of "Scorched Earth" CSS injection to permanently eliminate cookie banners and click-intercepting overlays.
- **Harvest & Execute Strategy**: Phase 2 now splits into "Harvest Codes (Single)" and "Execute Multi-Bet (Pooled Codes)" for maximum slip stability.
- **Defensive JS Layer**: Match data extraction now includes defensive JavaScript execution to handle missing selectors without crashing.
- **Improved Navigator**: Optimized mobile context with adaptive resource blocking (restoring CSS for site stability).

CORE ARCHITECTURE:
- **Dual-Browser Engine**: Playwright-managed Chromium (Headless for Flashscore, Persistent Mobile for Football.com).
- **RuleEngine (Neo/model.py)**: Deterministic logic combining xG, H2H, and standings data for high-confidence predictions.
- **Persistent AI Discovery**: Auto-healing mechanism using Grok 4 to map visual elements to selectors on failure.
- **Modular DB**: Absolute-pathed CSV system for decentralized match tracking and outcome review.

MAIN WORKFLOW:
1. REVIEW (Phase 0):
   - Monitors past matches in `site_matches.csv`.
   - Evaluates performance and prints real-time accuracy reports.

2. ANALYSIS (Phase 1):
   - Scrapes Flashscore using hardened multi-layered popup dismissal.
   - Extracts H2H (10 matches) and Standings data.
   - RuleEngine generates high-confidence predictions.

3. HARVEST (Phase 2a):
   - Visits matches individually on Football.com.
   - Generates and extracts single-match booking codes.
   - Prevents betslip pollution by clearing slip after each match.

4. EXECUTE (Phase 2b):
   - Pools harvested codes into a single multi-bet construction.
   - Verifies balance and places the accumulator securely.

SUPPORTED BETTING MARKETS:
- 1X2, Double Chance, DNB
- BTTS, Over/Under (0.5 - 5.5)
- Correct Score, Clean Sheet
- Combo Bets & Asian Handicap

MAINTENANCE:
- Recommendations are auto-generated after every Phase 1 cycle in `DB/RecommendedBets/`.
- System logs exhaustive debug snapshots (HTML/PNG) in `Logs/Error` on failure.
"""
