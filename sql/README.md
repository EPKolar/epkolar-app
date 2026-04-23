# sql/

Aktive SQL-Scripts, Node-Helper und Referenz-Docs für die EPKolar-App.

> Historische SQL-Files (abgeschlossene Bugs, alte Handoffs, superseded
> Testkonzepte) sind ab 2026-04-23 nach `../_archiv/sql/` verschoben — siehe
> `../_archiv/README.md`.

## Node-Helper (im Repo-Root via `node sql/<file>` aufrufen)

| Script | Zweck |
|---|---|
| `_check_syntax.js` | Extrahiert inline `<script>`-Body aus `index.html` in tmp-Datei und ruft `node --check`. Exit 0 = OK (Node 24 akzeptiert `node --check *.html` nicht mehr direkt). |
| `_check_brackets.js` | Bracket-Balance. Erwartete Baseline: `() -2 {} 0 [] 0`. Die `-2` ist ein False-Positive aus Template-Literals — nicht versuchen zu "fixen". |
| `_deep_scan_nullable.js` | Null-Safety-Scan (`x.y` ohne optional chaining auf potentiell-nullable values). |
| `_b022_sweep.js` | Stale-Closure-Pattern-Detection (useEffect-Deps-Audit aus B-022). |
| `_wrap_viewboundaries.js` | Automatisches `<ViewBoundary>`-Wrapping für Top-Level-Render-Calls. |
| `sql-runner.mjs` | Node-`pg`-Runner für SQL-Files. `.env` mit `SUPABASE_DB_URL=postgres://...` erforderlich. |

## Offene Deploy-SQLs (Sebastian führt manuell aus)

| File | Status |
|---|---|
| `BASELINE_FIX_v3.8.sql` + `BASELINE_FIX_VERIFY_v3.8.sql` | ⏳ pending seit 2026-04-20 |
| `PHOTOS_RLS_AUDIT.sql` + `PHOTOS_RLS_FIX.sql` | ⏳ pending |
| `INDEX_AUDIT_v3.7.sql` + `INDEX_EFFECT_v3.8.sql` | ⏳ pending |
| `RLS_SNAPSHOT_v3.8.sql` + `RLS_RECONCILE_v3.8.md` | ⏳ pending |
| `WHATSAPP_SCHEMA_v3.8.sql` + `WHATSAPP_SEEDS_v3.8.sql` + `WHATSAPP_INTEGRATION_PLAN.md` | ⏳ Schema-Deploy gebraucht bevor UI-Code sinnvoll |
| `DEPLOY_sync_supplier_v3.md` | ⏳ pending |
| Orphan-UPDATE aus `B_12_ORPHANS_ANALYSIS.md` | ⏳ 11 Rows, siehe Doc |

## Referenz-Docs

- `ARCHITECTURE.md` — Gesamt-Überblick
- `README.md` (dieser) — Index
- `TODO_MORGEN.md` — Deferred-Blocks + Status
- `PERMISSION_MATRIX_v3.7.md` — Rollen/Permissions
- `PERF_v3.6.md` + `PERF_HINTS.md` — Performance-Analyse
- `SELFTEST_USAGE.md` — `window._selfTest()` Doku
- `Testkonzept_EPKolar_v5_0.md` — aktuelles Testkonzept
- `B_12_ORPHANS_ANALYSIS.md` — monteur-Orphan-Analyse (2026-04-23 live-updated)
- `INDEX_EFFECT_v3.8_RESULTS.md` — Erwartete Effekt-Metriken für Index-Deploy
- `AUTH_DEBUG_QUERIES.sql` — Auth-Debug-Query-Sammlung

## Ausführungs-Konvention

Für Dashboard-Pastes: SQL-File öffnen → im Supabase SQL Editor paste → Run.
Alle `.sql`-Files sind **idempotent** (mehrfache Ausführung ohne Schaden).

Für `sql-runner.mjs`: `.env` mit `SUPABASE_DB_URL=postgres://...` lokal anlegen
(wird via `.gitignore` nie committed).
