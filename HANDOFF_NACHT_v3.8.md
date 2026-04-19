# HANDOFF NACHT v3.7.0 → v3.8.0 · 14h-Run · 2026-04-19 16:22

## Start
- HEAD: `879c535` (v3.7.0)
- Baseline-Brackets: `() -2 {} 0 [] 0` (siehe `baseline_v3.8_start.txt`)
- `node --check`: OK

## Vorherige Findings (aus BUG_HUNT.md v3.7.0)

- **M-1 P2** `_isJwtShape`-Härtung: atob/JSON.parse im `_isJwtShape` kann bei garbage werfen. Fix: try/catch wrap.
- **M-2 P1** photos-Tabelle RLS: möglicherweise keine RLS-Policy → 25k Fotos anon-readable.
- **M-3 P3** `_authRefreshInflight` 50ms-race hypothetisch.
- **M-4 P2** localStorage `epkolar_gc` speichert base64-encoded Password.

## DB-State vor Run-Start (bereits geschlossen)
- **B-020 DB-Teil**: 9×OK verified am 19.04 ~14:00 (Sebastians Check). `sql/B020_FIX.sql` alle Schritte ausgeführt. In Block 0.3 NICHT re-executed.

## Blocks

### Block 1 · v3.7.2 · ✅ M-2 photos RLS Diagnose+Fix-SQL
- `sql/PHOTOS_RLS_AUDIT.sql`: 5 Diagnose-Queries (Policies, RLS-Flag, Schema, Counts) + Entscheidungsmatrix A-E
- `sql/PHOTOS_RLS_FIX.sql`: 3 Varianten (A=Policy fehlt, B=Policy zu offen, C=nur Matrix-Doku) mit vollen CREATE POLICY Blöcken für SELECT-Staff / SELECT-Field-Self / INSERT / UPDATE / DELETE
- Sebastian führt Audit → entscheidet → Fix → Verify via `_rlsAudit()`

### Block 2 · v3.7.3 · ✅ BUG_HUNT M-1/M-3/M-4 closed
- **M-1 NOT A BUG**: _isJwtShape hat keine atob/JSON.parse. Die einzige atob+parse-Stelle (window._ensureAuth Line 796) ist bereits try/catch-gewrappt.
- **M-3 RE-INVESTIGATE**: _authRefreshInflight 50ms-race — analysiert als harmlos (rapid-fire 401 wollen KEIN sofortiges 2. Refresh). Messung kommt via Block 7 _thunderTest.
- **M-4 KNOWN-TRADE-OFF**: epkolar_gc Password base64 — UX-Entscheidung (Monteure-Offline-PWA), Sebastian entscheidet Migration.
- Nur BUG_HUNT.md Doku-Update, **keine Code-Änderungen** (ehrliche Entscheidung).

### Block 3 · v3.7.4 · ✅ _selfTest() Orchestrator
- `window._selfTest({mode:'full'|'quick'|'security'})` fährt alle 5 Helper sequentiell
- Full-mode ruft perfBench → mobileCheck → b017check → rlsAudit → s8Suite
- Console.group + Console.table + Toast + localStorage['selftest_last_run']
- `sql/SELFTEST_USAGE.md` mit Usage, Regression-Workflow, Rollen-Matrix, Troubleshooting

### Block 4 · v3.7.5 · ✅ Index-Effekt-Verify SQL-Suite
- `sql/INDEX_EFFECT_v3.8.sql`: 12 EXPLAIN ANALYZE Queries für alle v3.6+v3.7 Indizes (AS/TE/Notif/Activity/SA-FTS/FB/Komm/Photos) + pg_stat_user_indexes Monitor
- `sql/INDEX_EFFECT_v3.8_RESULTS.md`: Template zum Ausfüllen, Vor-/Nach-Vergleich, Verdict-Matrix (EFFECTIVE/MARGINAL/INEFFECTIVE)
- Sebastian: vorher + nachher durchlaufen, Zahlen in Results-MD kopieren

### Block 5 · v3.7.6 · ✅ RLS-Matrix-Reconcile Template
- `sql/RLS_SNAPSHOT_v3.8.sql`: 5 Diagnose-Queries (Policies, rls_enabled, missing policy, rls disabled, helper-Functions)
- `sql/RLS_RECONCILE_v3.8.md`: 5 Status-Kategorien, Reconcile-Tabelle pro Table × Rolle × Command, Fix-Strategie je Gap-Typ
- Kein RLS_FIX_v3.8.sql erstellt — wird von Sebastian nach Snapshot-Review befüllt (ehrliche Entscheidung, keine Fix-SQL ohne echte Gap-Analyse)
