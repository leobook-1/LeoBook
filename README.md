# LeoBook

**Developer**: Matterialless LLC
**Chief Engineer**: Emenike Chinenye James
**Powered by**: Grok 4.1 & Gemini 3
**Architecture**: Clean Architecture v2.9 (Orchestrator → Module → Data)

---

## What Is LeoBook?

LeoBook is an **autonomous sports prediction and betting system** with two halves:

| Component | Tech | Purpose |
|-----------|------|---------|
| `Leo.py` | Python 3.12 + Playwright | Data extraction, AI prediction, odds harvesting, automated bet placement, withdrawal management |
| `leobookapp/` | Flutter/Dart | Cross-platform app displaying predictions, accuracy reports, and recommendations |

Leo.py is a **pure orchestrator** — zero business logic. All logic lives in the modules it imports. It runs in an infinite cycle (default every 6 hours).

For the complete file inventory and step-by-step execution trace, see [LeoBook_Technical_Master_Report.md](LeoBook_Technical_Master_Report.md).

---

## System Architecture

```
Leo.py (Orchestrator)
├── Prologue: Cloud Sync → Outcome Review → Enrichment → Accuracy
├── Chapter 1: Flashscore Extraction → AI Prediction → Odds Harvesting → Recommendations
├── Chapter 2: Automated Bet Placement → Withdrawal Management
├── Chapter 3: Chief Engineer Oversight & Health Check
└── Live Streamer: Parallel 60s LIVE score streaming → status propagation
```

### Core Modules

- **`Core/Intelligence/`** — AI prediction engine (ML model, rule engine, learning engine, AIGO self-healing)
- **`Core/Browser/`** — Playwright automation and data extractors (H2H, standings, league pages)
- **`Core/System/`** — Lifecycle, monitoring, withdrawal checker
- **`Modules/Flashscore/`** — Schedule extraction, match processing, offline reprediction, **live score streaming**
- **`Modules/FootballCom/`** — Betting platform automation (login, navigation, odds, booking, bet placement)
- **`Data/Access/`** — CSV CRUD, Supabase sync, outcome review, accuracy calculation
- **`Scripts/`** — Enrichment pipeline, recommendation engine, maintenance utilities

### AIGO (AI-Guided Operation) — Self-Healing Framework (v5.0)

Five-phase recovery cascade for every browser interaction (~8-18% reach Phase 3):

0. **Context Discovery** — selector lookup from `knowledge.json`
1. **Reinforcement Learning** — memory-based strategy selection
2. **Visual Analysis** — multi-strategy matching (CSS → XPath → text → fuzzy)
3. **Expert Consultation** — Grok API multimodal analysis (screenshot + DOM → primary + backup paths)
4. **Self-Healing** — persist AI-discovered selectors to `knowledge.json` for future cycles

See [AIGO_Learning_Guide.md](AIGO_Learning_Guide.md) for the full pipeline specification.

---

## Supported Betting Markets

1X2 · Double Chance · Draw No Bet · BTTS · Over/Under · Goal Ranges · Correct Score · Clean Sheet · Asian Handicap · Combo Bets · Team O/U

---

## Project Structure

```
LeoBook/
├── Leo.py                  # Orchestrator (275 lines, zero logic)
├── Core/
│   ├── Browser/            # Playwright automation + extractors (5 files)
│   ├── Intelligence/       # AI engine, AIGO, selectors (29 files)
│   ├── System/             # Lifecycle, monitoring, withdrawal (4 files)
│   └── Utils/              # Constants, page monitor, error logging (3 files)
├── Modules/
│   ├── Flashscore/         # Sports data extraction + live streamer (7 files)
│   └── FootballCom/        # Betting platform automation (20 files)
├── Scripts/                # Enrichment pipeline + utilities (13 files)
├── Data/
│   ├── Access/             # Data access layer (11 files)
│   ├── Store/              # CSV/JSON data stores (19 files)
│   └── Supabase/           # Cloud schema + migrations (2 files)
├── Config/
│   └── knowledge.json      # CSS selector knowledge base (32 KB)
├── leobookapp/             # Flutter frontend (56 Dart files)
└── StitchLeoBookHomeScoresNews/  # UI design mockups
```

---

## LeoBook App (Flutter)

Elite, cross-platform betting dashboard with:

- **Supabase Backend** — Cloud-native data for instant global access
- **Brand Enrichment** — Team crests, region flags, league URLs
- **Offline Caching** — `shared_preferences` persistence for offline viewing
- **Responsive Design** — `LayoutBuilder` breakpoints, proportional scaling, `Responsive` constants
- **Material 3** — Dynamic color theming with dark mode
- **Liquid Glass UI** — Premium frosted-glass containers, blur effects, performance toggle
- **4-Tab Match System** — ALL | LIVE | FINISHED | SCHEDULED with mutually exclusive 2.5hr time rule
- **Live Accuracy Tags** — Fed by `outcome_correct` column from predictions pipeline

---

## Quick Start

### Backend (Leo.py)

```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env  # Configure API keys
python Leo.py
```

### Frontend (leobookapp)

```bash
cd leobookapp
flutter pub get
flutter run -d chrome  # or: flutter run (mobile)
```

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `GROK_API_KEY` | xAI Grok API for AIGO expert consultation |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Supabase service role key (Python backend, full write access) |
| `SUPABASE_ANON_KEY` | Supabase anon key (Flutter app, read-only via RLS) |
| `LLM_API_URL` | Local Leo AI server fallback (optional) |
| `LEO_CYCLE_WAIT_HOURS` | Hours between cycles (default: 6) |

---

## Documentation

| Document | Purpose |
|----------|---------|
| [LeoBook_Technical_Master_Report.md](LeoBook_Technical_Master_Report.md) | Complete file inventory, execution trace, data flow diagrams |
| [leobook_algorithm.md](leobook_algorithm.md) | Algorithm reference — every function call mapped to its module |
| [AIGO_Learning_Guide.md](AIGO_Learning_Guide.md) | Self-healing framework specification (5-phase pipeline) |
| [SUPABASE_SETUP.md](SUPABASE_SETUP.md) | Supabase setup, credentials, Flutter config |
| [SUPABASE_SYNC_REQUIREMENTS.md](SUPABASE_SYNC_REQUIREMENTS.md) | SyncManager technical spec, conflict resolution, performance |
| [LeoBook Developer Tasks.txt](LeoBook%20Developer%20Tasks.txt) | Roadmap with implementation status |

---

## Maintenance

- Monitor `Data/Store/audit_log.csv` for real-time event transparency
- Monitor `Data/Store/live_scores.csv` for live match streaming data
- Use `python Scripts/recommend_bets.py --save` to manually generate recommendations
- Use `python Scripts/enrich_all_schedules.py --limit 50` for targeted enrichment
- Check Chapter 3 oversight reports in Supabase `audit_events` table
- Live streamer runs automatically in parallel — check `[Streamer]` logs
