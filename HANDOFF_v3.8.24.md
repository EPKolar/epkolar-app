# HANDOFF · v3.8.24 Archivier-Pass · 2026-04-23 spät

**Start-HEAD**: `01b7332` (v3.8.23 Handoff-Doku)
**End-HEAD**: `ca75bcc` (archive-pass README-Updates)
**Tag**: `v3.8.24` (gepusht)
**Modus**: vollautonom via `CC_COMMAND_v3.8.24_ARCHIVE.md`.
**Typ**: Reines Repo-Housekeeping. Kein APP_VERSION-Bump, kein Code-Change.

---

## Block-Status-Tabelle

| Block | Thema | Status | Commit |
|---|---|---|---|
| 0 | Pre-Flight | ✅ DONE | — |
| 1 | 16 Files nach `_archiv/sql/` verschoben | ✅ DONE | `982eba7` |
| 2 | READMEs aktualisiert (sql/ + _archiv/sql/) | ✅ DONE | `ca75bcc` |
| 3 | Tag `v3.8.24` + Push | ✅ DONE | — |
| 4 | Handoff (dieser File) | 🔵 IN PROGRESS | — |

---

## Was verschoben wurde (16 Files)

**Post-Mortem**:
- `BASELINE_FIX_v3.8.sql` → `_archiv/sql/BASELINE_FIX_v3.8_BUGGY_constraints_dropped_23042026.sql`
  (umbenannt zur klaren Doku — file hatte falsche CHECK-Werte)
- `BASELINE_FIX_VERIFY_v3.8.sql`

**Erledigte Probleme**:
- `B_12_ORPHANS_ANALYSIS.md` (11 Rows migriert)
- `AUTH_DEBUG_QUERIES.sql` (B-020 geschlossen)

**Überholte Versionen**:
- `INDEX_AUDIT_v3.7.sql` + `INDEX_EFFECT_v3.8.sql` + `INDEX_EFFECT_v3.8_RESULTS.md`
- `PERF_HINTS.md` + `PERF_v3.6.md`
- `PERMISSION_MATRIX_v3.7.md` (ersetzt durch RLS_RECONCILE_v3.8)

**B-021 Status Quo**:
- `PHOTOS_RLS_AUDIT.sql` + `PHOTOS_RLS_FIX.sql`

**Einmal-Scripts**:
- `_b022_sweep.js`, `_deep_scan_nullable.js`, `_wrap_viewboundaries.js`

**TODO**:
- `TODO_MORGEN.md` (in HANDOFFs fortgeführt)

## In `sql/` geblieben (15 Files)

- `README.md` (aktualisiert)
- `ARCHITECTURE.md`, `SELFTEST_USAGE.md`, `DEPLOY_sync_supplier_v3.md`
- `RLS_RECONCILE_v3.8.md`, `RLS_SNAPSHOT_v3.8.sql`
- `Testkonzept_EPKolar_v5_0.md`
- `WHATSAPP_INTEGRATION_PLAN.md` + `WHATSAPP_SCHEMA_v3.8.sql` + `WHATSAPP_SEEDS_v3.8.sql`
- `_check_brackets.js`, `_check_syntax.js`, `_check_version.js`, `sql-runner.mjs`
- `DEPLOY_SQL_REVIEW_2026-04-23.md` (Session-Review, behalten als Kontext für Post-Mortem)

---

## Abweichung vom Command-File

Command-File Commit-Message sprach von "15 historische/erledigte Files"
— die tatsächliche Liste waren **16 Moves** (BASELINE_FIX ist eine
Datei, nicht zwei — aber BASELINE_FIX + VERIFY = 2; dazu 1+3+2+1+2+1+3+1 = 14;
Summe 16). Kleiner Zahlfehler im Command-File, inhaltlich kein Problem.

---

## Offen — Sebastian (unverändert aus v3.8.23)

- [ ] PAT rotieren
- [ ] B-020 Login-Smoke 5 User (paschinger, barger, cracana, pinger, schmid)
- [ ] Smoke-Test v3.8.23 Instant-Push-Flow

## Offen — CC v3.8.25+

- **`_juprowaSyncing` try/finally-Wrap** (Leak-Schutz bei hängendem Sync)
- **Feature 12 WhatsApp UI** (braucht Schema+Seeds-Deploy vorher)
- **Block 3 Last-Sync-Indikator** — wurde in v3.8.23 geskipped, in v3.8.24 nicht
  geplant. Falls gewollt: eigener Task, ~1h.
- **Falls CHECK-Constraints wieder gewollt sind**: saubere Neu-Version mit
  echten Werte-Listen erstellen (nicht das alte File wieder hochziehen).
  Korrekte Werte siehe `sql/DEPLOY_SQL_REVIEW_2026-04-23.md`.

---

## Metrics

- Commits: **3** (2 Archive-Commits + dieser Handoff = noch zu committen)
- 0 Code-Änderungen, 0 Version-Bumps
- 16 Files verschoben, 2 READMEs neu/aktualisiert
- `sql/` reduziert von 30 Files auf 15
- `_archiv/sql/` gewachsen auf ~42 Files total

---

## Repo-Layout nach v3.8.24

```
epkolar-app/
├── README.md
├── .gitignore
├── HANDOFF_v3.8.20.md
├── HANDOFF_v3.8.23.md
├── HANDOFF_v3.8.24.md    ← dieser File
├── index.html
├── sw.js
├── sql/                  ← 15 aktive Files
│   ├── README.md
│   ├── _check_*.js, sql-runner.mjs
│   ├── RLS_RECONCILE_v3.8.md + RLS_SNAPSHOT_v3.8.sql
│   ├── WHATSAPP_* (3 Files)
│   └── ARCHITECTURE/SELFTEST/Testkonzept/DEPLOY_sync/DEPLOY_REVIEW
└── _archiv/              ← historische Artefakte
    ├── README.md
    ├── sql/              ← 42 archivierte SQL-Files
    │   └── README.md
    └── (13 Root-Level-Artefakte aus v3.8.20 Aufräumen)
```
