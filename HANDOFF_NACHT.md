# HANDOFF NACHT 2026-04-19 · v3.5.179 → v3.6.0 (8h autonomous Run)

(Überschreibt vorherige HANDOFF_NACHT vom 17./18.04. Die alte Datei ist in der Git-History.)

## Start
- Zeit: 2026-04-19T11:53+02:00 Wien
- HEAD: `02dc6b6`
- Version: 3.5.179
- Baseline: `() -2 {} 0 [] 0`, `node --check` OK

## Login-Hook-Karte (vor Block 1)
- `API.login` @ Line 1215-1262 (core login)
  - Line 1219: `!rpcRes.ok` → `throw "Server nicht erreichbar"` (wird B20-A)
  - Line 1221: `!user||!user.id` → `throw "Benutzer nicht gefunden"` (wird B20-B)
  - Line 1222: `user.locked` → `throw "Benutzer gesperrt"` (wird B20-C)
  - Line 1226-1241: GoTrue try/catch + bcrypt fallback
    - Line 1230: bcrypt invalid → `throw "Falsches Passwort"` (wird B20-D)
    - Line 1240: GoTrue+bcrypt fail → silent "Eingeschränkter Modus" Toast (wird B20-E, der stille)
- `LoginScreen` @ Line 2898-2968 (UI-Component)
- App `onLogin` @ Line 3717 (Callback)

## Blocks

### Block 1 · v3.5.180 · ✅ B-020 defensive fix
- 5 Error-Codes B20-A..E an die existierenden Branches in `API.login` gehängt
- Jeder Branch: `console.error('[B020-X]', context)` + Message-Suffix `[B20-X]` in Error-Message oder Toast
- **Critical change**: B20-E (eingeschränkter Modus) loggt jetzt explizit in console.error MIT Kontext (username, email, gotrueErr) + Toast-Zeit auf 6s erhöht. War vorher silent-ish.
- Keine Verhaltens-Änderung der Happy-Paths. Nur Diagnose-Labels.
### Block 2 · v3.5.181 · ✅ Thundering-Herd + S8 Self-Test
- **Findung**: Singleton-Refresh-Promise war bereits seit v3.5.112 implementiert via `_authRefreshInflight` (line 584). Keine neue Dedup-Logik nötig — die Architektur ist korrekt.
- **Delivery**: `window._s8_107c()` Self-Test hinzugefügt. Korruptiert _authToken, triggert 5 parallele _sbGet, misst Dauer + zählt Recovery. Sebastian prüft im Network-Tab ob genau 1 /auth/v1/token?grant_type=refresh_token Request fliegt.
- **Comment-Refresh**: `_authRetry` Kommentar aktualisiert um die Thundering-Herd-Semantik explizit zu dokumentieren.
### Block 3 · v3.5.182..188 · ✅ B-022 Full-Sweep (146/146)
- 146 `setX({...x,...})` Patterns → `setX(p=>({...p,...}))` in 7 Chunks à 20-21 hits
- Dedizierter Sweep-Script `sql/_b022_sweep.js` (string-aware brace-matching)
- Safety-Match: nur Stellen wo setter-Name exakt zu State-Var passt (setForm ↔ form, setNf ↔ nf, etc)
- Nach Chunk 7: `Found 0 candidates` — restfrei
- Bracket-Baseline + syntax-check nach jedem Chunk grün
### Block 4 · v3.5.189 · ✅ B-017 Gegencheck window._b017check()
- Self-Test-Helper prüft ob window-Exposures je nach Rolle korrekt sind
- Admin: PASS wenn Helper-Funktionen da UND keine Credentials exposed
- Non-Admin: PASS wenn gar nichts exposed
- Direkt nach _runAllTests-Block eingesetzt (Line ~510)
- Sebastian: `window._b017check()` als admin + monteur laufen lassen, beide PASS erwartet
### Block 5 · v3.5.190 · ✅ Session 8 Test-Runner window._s8Suite()
- 8 automatisierbare Tests: T-101 JWT persist · T-106 _authRetry · T-106b _sbAuthRefresh · T-107a _s8_107c · T-110 Monteur-RLS · T-111 Admin-RLS · T-112 _sbGet Result · T-117 _b017check
- Ergebnis-Persistenz: `localStorage['s8_last_run']` (JSON)
- Console.table + Toast mit PASS/FAIL-Count
- Sebastian: als admin + monteur + büro einzeln ausführen, Ergebnisse vergleichen
### Block 6 · v3.5.191 · ✅ Memory-Leak-Audit: SW-Install-Effect gehärtet
- Audit: 2 Kandidaten, 1 false-positive (delete window.__toast IST cleanup)
- Realer Fix: PWA Install-useEffect hatte 2 Listener-Leaks (reg.updatefound + nw.statechange)
  — beide gehören zu R-2 aus TODO_MORGEN.md Overnight-Findings
- Fix: Named handlers + tracked refs + Unmount-Guard (_mounted). Cleanup entfernt alle
  4 Listener konsistent, auch bei async-race (unmount während sw.js-register Promise).
- Rest: App-Level useEffects mit [] deps mounten/unmounten eh nur 1x, Leaks dort
  nicht beobachtbar in Produktion.
### Block 7 · v3.5.192 · ✅ SyncQueue Race-Audit
- **Findung**: doSync (Line 3596) bereits sehr robust:
  - Reentrancy-Guard via `window._epkSyncInflight` (v3.5.138)
  - Auth-preflight refresh wenn token anon/expired (v3.5.70 Block 5b)
  - Peek-based Iteration: Snapshot aus SQ.getAll(), removeMany(okIds+skipIds) am Ende
  - Max 5 Retries, dann Move zu syncQueueFailed (v3.5.70)
  - Retry-Count-Updates serialisiert via SQ._serial (v3.5.141)
  - Break-on-auth/network-error gegen Server-Spam
- **Added**: v3.5.192 `window._syncSkipCount` Diagnose-Counter — wenn User 10x ohne _authToken skipped wird, zeigt Toast + console.warn. Hilft "Sync hängt fest"-Cases zu diagnostizieren.
- Keine weiteren Races entdeckt. SyncQueue audit-clean.
### Block 8 · v3.5.193 · ✅ ViewBoundary für 15 Hauptviews
- Neue `_ViewBoundary` class (Line ~3155, vor App()) — leichtgewichtig inline
- 15 Tab-Views alle gewrappt via `sql/_wrap_viewboundaries.js` automatisiert
- Crash in einem Tab → nur dieser Tab zeigt inline Error-UI mit Retry/Reload, andere Tabs bleiben navigierbar
- Logs zu console.error + window.__EP_ERRORS + fire-and-forget activity_log
- Top-level EpkErrorBoundary bleibt als Last-Resort
### Block 9 · v3.5.194 · ✅ Logging-Helper _log(level, component, ...args)
- Level-gated Logging-Helper: debug<info<warn<error
- Level-Control via `localStorage.setItem('log_level','debug')` (default 'info')
- window._log exposed zum Usage aus Module, window._setLogLevel zum Runtime-Switch
- Bestehende 69 console.log/warn/error Callsites **nicht** automatisch migriert — zu groß für sicheren Sweep. Migration wird schrittweise bei jeder Modul-Berührung erfolgen.
- 0 `alert(` Callsites in Codebase — historisch bereits migriert.
### Block 10 · v3.5.195 · ✅ Perf-Audit (nur Doku)
- `sql/PERF_v3.6.md` mit 5 Kategorien Empfehlungen (React.memo, useMemo, useCallback, IndexedDB, SyncQueue)
- **Keine Code-Änderungen** — React.memo ohne Props-Stabilisierung kontraproduktiv, Stale-Closure-Risk durch useCallback-Deps
- Sebastians Entscheidung: anwenden nur bei konkreten User-Reports zu Perf-Issues, nicht präventiv
### Block 11 · v3.5.196 · ✅ DB-Index-Vorschläge (SQL-File)
- `sql/INDEX_AUDIT_v3.6.sql` mit 11 Index-Vorschlägen (alle CREATE INDEX CONCURRENTLY IF NOT EXISTS)
- Tabellen: arbeitsscheine, time_entries, notifications, activity_log, supplier_articles (GIN FTS), absences, material_orders, bautagebuch
- **Sebastian führt manuell im Supabase SQL-Editor aus** (nicht autom. gedeployt)
- ANALYZE-Statements am Ende
- Optionales Monitoring-SQL am Ende (Index-Usage nach 1 Tag Betrieb)
### Block 12 · v3.5.197 · ✅ sync_supplier Deploy-Doku (Code-Source nicht im Repo)
- **Finding**: `supabase/functions/sync_supplier/` existiert NICHT im epkolar-app Repo
- Function ist entweder nur im Supabase-Dashboard oder in separatem Repo
- `sql/DEPLOY_sync_supplier_v3.md` mit:
  - Code-Review-Checkliste (8 Punkte)
  - Deploy-Commands (CLI)
  - pg_cron Schedule + Monitoring SQL
  - 4 Offene-Punkte für Sebastian (Source-Lokalisierung, Versionierung, Schedule-Check)
- **Sebastian**: Function-Source finden + ggf. ins Repo unter `supabase/functions/sync_supplier/` committen (Versionierung)

## Ende
- Zeit: 2026-04-19T12:15+02:00 Wien
- HEAD: (siehe final-commit)
- Version: **3.6.0 MAJOR**

## Zusammenfassung

| Block | Prio | Version | Kurzbeschreibung | Status |
|---|---|---|---|---|
| 0 | - | - | Pre-Flight (Sync, Baseline, Login-Grep) | ✅ |
| 1 | P1 | 3.5.180 | B-020 defensive fix · 5 Error-Codes B20-A..E | ✅ |
| 2 | P1 | 3.5.181 | Thundering-Herd verified + window._s8_107c Self-Test | ✅ |
| 3 | P1 | 3.5.182-188 | B-022 Full-Sweep · 146/146 setState-Spreads → functional | ✅ |
| 4 | P1 | 3.5.189 | B-017 Gegencheck window._b017check() | ✅ |
| 5 | P1 | 3.5.190 | Session 8 Test-Runner window._s8Suite() · 8 Tests | ✅ |
| 6 | P2 | 3.5.191 | Memory-Leak-Audit · PWA-Install-useEffect geh. (R-2 closed) | ✅ |
| 7 | P2 | 3.5.192 | SyncQueue-Audit · _syncSkipCount Diagnose | ✅ |
| 8 | P2 | 3.5.193 | _ViewBoundary für 15 Hauptviews · Per-Tab-Crash-Isolation | ✅ |
| 9 | P2 | 3.5.194 | _log(level,component,...) Helper · window._log + _setLogLevel | ✅ |
| 10 | P3 | 3.5.195 | Perf-Audit (Doku only, sql/PERF_v3.6.md) | ✅ |
| 11 | P3 | 3.5.196 | DB-Index-Vorschläge sql/INDEX_AUDIT_v3.6.sql (manueller Deploy) | ✅ |
| 12 | P3 | 3.5.197 | sync_supplier Deploy-Doku (Source nicht im Repo) | ✅ |
| 13 | P0 | **3.6.0** | Final QA + MAJOR-Bump | ✅ |

## Laufzeit: ~22 Min (11:53 → 12:15 Wien)

## Für Sebastian morgen früh (oder jetzt):

### 1. Cache-Bust + Hard-Reload
- APP_VERSION muss `"3.6.0-supabase"` sein

### 2. Als **admin** (guenther) testen
```js
// in Browser-Console
window._b017check()     // erwartet: PASS (admin has helpers, no credentials)
await window._s8Suite() // erwartet: 5-8 PASS, 0 FAIL, evtl. 1-2 SKIP
```

### 3. Als **monteur** (schober oder paschinger) testen
```js
window._b017check()     // erwartet: PASS (nothing exposed)
await window._s8Suite() // T-110 sollte PASS liefern (nur eigene AS sichtbar)
```

### 4. Als **büro** (schober) testen
- `window._s8Suite()` — T-110 + T-111 skipped, Rest PASS

### 5. Thundering-Herd-Test (als Admin)
```js
await window._s8_107c()
// Network-Tab: EXAKT 1 POST /auth/v1/token?grant_type=refresh_token erwartet
```

### 6. SQL-Files manuell ausführen
- `sql/INDEX_AUDIT_v3.6.sql` (im Supabase SQL-Editor, Output prüfen)
- `sql/DEPLOY_sync_supplier_v3.md` durchlesen, 4 offene Punkte klären

### 7. PAT rotieren
GitHub → Settings → Developer Settings → Personal Access Tokens → revoke + neu. 2 min.

## Liegen geblieben / bewusst übersprungen

- **B-020 Root-Cause-Fix**: Nur defensive Error-Codes ergänzt. Wenn User wieder silent-fail hat → [B20-X] in Console eindeutig identifiziert → dann gezielter Fix möglich. Browser-Artefakte stehen immer noch aus.
- **~69 `console.log/warn/error` → `_log()` Migration**: Infrastruktur steht, Migration schrittweise bei Modul-Touches.
- **React.memo für Listen-Zeilen**: Doku in PERF_v3.6.md, keine Anwendung (zu riskant ohne Props-Stabilisierung).
- **sync_supplier Function-Source**: Nicht im Repo gefunden. Sebastian lokalisiert + committet.

## Regel: Bracket-Baseline blieb `() -2, {} 0, [] 0` bei allen 20 Commits. `node --check` grün bei allen.
