# Supabase Sync — Technical Specification

> **Version**: 2.8 · **Last Updated**: 2026-02-17 · **Status**: Fully Implemented & Automated

## Overview

LeoBook v2.8 uses **automatic bi-directional sync** between local CSV data stores and Supabase cloud database. Sync is managed by [`SyncManager`](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Data/Access/sync_manager.py) — no manual scripts or user prompts required.

### Architecture
```
Leo.py (orchestrator)
  → SyncManager.sync_on_startup()     # Pull remote → merge → push deltas
  → [... cycle work ...]
  → SyncManager.run_full_sync()       # Push all local changes to cloud
  → Supabase (cloud DB)
  → Flutter App (reads Supabase)
```

### Data Flow
```
Local CSVs (source of truth during cycle)
     ↕ bi-directional UPSERT
Supabase (cloud DB, consumed by Flutter app)
```

---

## SyncManager Specification

### Module: `Data/Access/sync_manager.py`

#### `sync_on_startup()`
- **When**: Prologue Page 1 (start of every cycle)
- **Direction**: Bi-directional
- **Logic**:
  1. Pull all Supabase records with `updated_at > last_sync_timestamp`
  2. Merge with local CSVs (newer record wins)
  3. Push local records with `updated_at > last_sync_timestamp` to Supabase
  4. Update sync checkpoint

#### `run_full_sync(label: str)`
- **When**: Prologue P3, Chapter 1 P3, and ad-hoc
- **Direction**: CSV → Supabase
- **Logic**:
  1. Read all local CSVs
  2. Batch UPSERT to Supabase (500 rows/batch)
  3. Log sync event to audit trail

---

## Tables & Conflict Resolution

| Table | Unique Key | Conflict Strategy | Sync Frequency |
|-------|-----------|-------------------|:-:|
| `predictions` | `fixture_id` | UPSERT (newer `updated_at` wins) | 3×/cycle |
| `schedules` | `fixture_id` | UPSERT (newer `updated_at` wins) | 3×/cycle |
| `standings` | `league_id + team_id` | UPSERT (latest snapshot wins) | 1×/cycle |
| `teams` | `team_id` | UPSERT (latest data wins) | 1×/cycle |
| `region_league` | `league_id` | UPSERT | 1×/cycle |
| `accuracy_reports` | `report_id` | UPSERT | 1×/cycle |
| `audit_events` | `event_id` | INSERT only (append-only log) | On every event |

---

## Batch Processing

- **Batch Size**: 500 rows per UPSERT call
- **Concurrency**: Sequential batches (no parallel writes)
- **Error Handling**: Failed batches are logged and retried once; partial failure doesn't abort sync
- **Memory**: Streaming reads from CSVs to avoid loading entire files into memory

---

## Resilience Design

### Offline-First
- All CSV files are the **local source of truth** during a Leo.py cycle
- If Supabase is unreachable, the cycle continues normally — sync is retried next cycle
- This is critical for Aba, Nigeria connectivity constraints

### Conflict Resolution
- **Last-write-wins** based on `updated_at` timestamp
- Leo.py writes always have the latest `updated_at`, so they naturally win over stale cloud data
- Flutter app is **read-only** — it never writes to Supabase, so no write conflicts

### Data Integrity
- [`data_validator.py`](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Data/Access/data_validator.py): Validates CSV column schemas before sync
- [`health_monitor.py`](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Data/Access/health_monitor.py): Detects stale data and sync gaps via Chapter 3 oversight

---

## Performance

| Dataset | Rows | Sync Time | Bandwidth |
|---------|------|-----------|-----------|
| predictions.csv | ~10,000 | ~25s | ~4.7 MB |
| schedules.csv | ~22,000 | ~45s | ~8.7 MB |
| standings.csv | ~15,000 | ~30s | ~7.3 MB |
| Full sync (all tables) | ~50,000 | ~120s | ~22 MB |

---

## Environment Variables

| Variable | Used By | Purpose |
|----------|---------|---------|
| `SUPABASE_URL` | Python + Flutter | Project URL (`https://xxx.supabase.co`) |
| `SUPABASE_SERVICE_KEY` | Python only | Full write access (Service Role Key) |
| `SUPABASE_ANON_KEY` | Flutter only | Read-only access via RLS (Anon Key) |

---

## Monitoring & Debugging

### Check Sync Status
```sql
-- Last sync event
SELECT * FROM audit_events
WHERE event_type = 'SYNC'
ORDER BY created_at DESC LIMIT 5;

-- Row counts
SELECT 'predictions' as tbl, COUNT(*) as rows FROM predictions
UNION ALL SELECT 'schedules', COUNT(*) FROM schedules
UNION ALL SELECT 'standings', COUNT(*) FROM standings
UNION ALL SELECT 'teams', COUNT(*) FROM teams;
```

### Verify Freshness
```sql
SELECT MAX(updated_at) as latest_update FROM predictions;
-- Should be within the last 6 hours during active operation
```

### Rollback
```sql
-- Delete recent bad data
DELETE FROM predictions WHERE updated_at > '2026-02-17 12:00:00';
-- Re-run Leo.py cycle to re-sync
```

---

## Security

1. ✅ Service Role Key: only in Python backend `.env` (never in client apps)
2. ✅ Anon Key: used by Flutter app with Row Level Security (read-only)
3. ✅ `.env` files in `.gitignore`
4. ✅ RLS policies enforce read-only access for anonymous users
