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

### Block 6 · v3.7.7 · ✅ B-020 Final-Verify + _forceExpireToken Dev-Helper
- `window._forceExpireToken()` + `window._restoreToken()` mit Guard `localStorage.__dev==='1'`
- `sql/B020_VERIFY_v3.8.md`: Login-Regression-Checkliste (9+1 User), Error-Code-Assertions B20-A..H, Token-Refresh-Test-Prozedur (Option A warten / Option B force)
- B-020 DB-Teil bleibt CLOSED (9×OK vor Run, nicht neu validiert per User-Bitte)

### Block 7 · v3.7.8 · ✅ _thunderTest() Last-Test Helper
- Temporärer fetch-Interceptor zählt /auth/v1/token?grant_type=refresh_token Calls
- Simuliert n=20 parallele _sbGet-Requests nach Force-Expire
- Verdict: SINGLETON OK (1 refresh) / NO REFRESH / THUNDERING HERD (>1)
- Guard: localStorage.__dev=='1' nötig (prod-safe)
- Auto-Restore via window._restoreToken() im finally

### Block 8 · v3.7.9 · ✅ WhatsApp Schema+Seeds+Plan (**ohne UI-Code**)
- `sql/WHATSAPP_SCHEMA_v3.8.sql`: whatsapp_templates + whatsapp_log Tabellen + RLS-Policies (admin-full, büro-read)
- `sql/WHATSAPP_SEEDS_v3.8.sql`: 4 Default-Templates (Terminbestätigung, Abschluss, Erinnerung, frei)
- `sql/WHATSAPP_INTEGRATION_PLAN.md`: explizit OUT-OF-SCOPE-Begründung für UI-Code, User-Stories für separate Feature-Session, Meta-API-Roadmap
- **Ehrlich**: UI-Code-Implementation (2-3h solide Arbeit) wurde nicht in diese Session gepresst — bessere Ergebnisse wenn mit Sebastian-Input designed

### Block 9 · v3.7.10 · ⚠ Mobile P1 Touch-Targets (NICHT GEPATCHT — ehrlich)
- **Ehrlichkeits-Regel angewendet**: Plan verlangt Touch-Target <44px Patches, aber CC hat keinen Live-Run von `_mobileCheck()` mit aktuellen Findings.
- **Risiko**: Blinde Patches an Buttons/Icons ohne konkrete Hit-List → potenzielle Regressions (falsche Elemente bekommen Padding, Layout bricht).
- **Delivery**: Version-Bump + HANDOFF-Eintrag, **keine Code-Änderungen**. Scanner `_mobileCheck()` ist seit v3.6.16 live — Sebastian liefert nach Live-Run im iPhone-Simulator/echtem Gerät die Hit-List, dann fokussierter Patch.
- Plan-Konformität: P1 Touch-Target <32px blockierend — wenn Liste da, in nächster Session Block-Fix.

### Block 10 · v3.7.11 · ⚠ sync_supplier Doku bleibt (Source noch nicht im Repo)
- Function-Source `supabase/functions/sync_supplier/` existiert weiterhin NICHT im Repo
- Existierendes `sql/DEPLOY_sync_supplier_v3.md` ist aktuell (v3.5.197 geschrieben, Content gültig)
- **Ehrlich**: keine neue Doku wenn nichts Neues bekannt ist. Plan wollte Code-Review der 223-Zeilen-Function, aber ohne Source-Access unmöglich.
- Sebastians offener Task bleibt: Source aus Supabase-Dashboard exportieren + ins Repo committen unter `supabase/functions/sync_supplier/`
