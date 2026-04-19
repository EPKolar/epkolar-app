# HANDOFF NACHT 2026-04-19 (späte Session) · v3.6.2 → v3.7.0 (15h autonomous Run)

(Überschreibt 8h-HANDOFF vom Vormittag. Git-History hat beide v3.5.179→v3.6.0 und den jetzigen Run.)

## Start
- Zeit: 2026-04-19T12:45+02:00 Wien
- HEAD: `1c50cce`
- Version: 3.6.2
- Baseline: `() -2 {} 0 [] 0`, `node --check` OK

## Context — Überlappungen mit 8h-Run erkennen
Im 8h-Run v3.5.180→v3.6.0 wurden bereits implementiert:
- `window._s8_107c` (Thundering-Herd-Test, v3.5.181) — Block 2 überlappend
- `window._b017check` (v3.5.189) — Block 4 überlappend
- `window._s8Suite` (v3.5.190) — Block 5 überlappend (muss um T-B020 ergänzt werden)
- Memory-Leak PWA-Install-Fix (v3.5.191) — Block 6 überlappend
- SyncQueue Audit + _syncSkipCount (v3.5.192) — Block 7 überlappend
- `_ViewBoundary` für 15 Views (v3.5.193) — Block 8 überlappend
- `_log` Helper (v3.5.194) — Block 9 überlappend
- `sql/PERF_v3.6.md` (v3.5.195) — Teil Block 11
- `sql/INDEX_AUDIT_v3.6.sql` (v3.5.196) — Block 12 überlappend
- `sql/DEPLOY_sync_supplier_v3.md` (v3.5.197) — Block 13 überlappend

Ehrlichkeitsregel: Diese Blocks werden re-verifiziert + dokumentiert statt dupliziert. Neu gebaut werden die wirklich offenen Items: **Block 1 (B-020 Code-Fix + DB-SQL), Block 10 (Permission-Matrix), Block 11 Delta (React.memo), Block 14 (Mobile-UX), Block 15 (Bug-Hunt), Block 16 (RLS-Audit), Block 17 (_perfBench)**.

## Login-Hook-Karte (re-grep aus 8h-HANDOFF)
- `API.login` @ Line 1215-1262 · 5 Branches B20-A..E via console.error gelabelt (v3.5.180)
- LoginScreen UI @ Line 2898
- App onLogin-Callback @ Line 3717

## Blocks

### Block 1 · v3.6.3 · ✅ B-020 Code-Fix + DB-SQL
- **Code (index.html)**:
  - Neue Guard B20-F: empty-email in public.users → hartes throw vor Auth-Attempt (statt silent-Degraded-Mode)
  - Email-Fallback `u+"@epkolar.local"` ENTFERNT (war Security-Smell, fake-domain)
  - altEmail-Retry im bcrypt-Block ENTFERNT (gleicher Grund)
  - B20-E (silent "Eingeschränkter Modus" Toast) → B20-G throw
  - Neue belt-and-braces B20-H: nach allen Auth-Pfaden MUSS _authToken gesetzt sein, sonst throw
- **DB-SQL (sql/B020_FIX.sql)**:
  - u7 Schober: email='info@ep-kolar.at', auth_user_id=4f4a25c5-... (orphan-Cleanup optional)
  - u1/u2/u3: brauchen neue GoTrue-Accounts via Supabase Dashboard, SQL ist Template
  - Final-Verify-Query zeigt bad_empty/no_auth_link/auth_missing-Flags
- **Sebastians Action**: sql/B020_FIX.sql Schritt 1 direkt ausführen, Schritt 3 nach Dashboard-User-Anlage mit UUIDs füllen.

### Block 2 · v3.6.4 · ✅ Thundering-Herd verify (bereits v3.5.181)
- `_authRefreshInflight` Singleton-Promise-Guard existiert seit v3.5.112 (Line 736)
- `window._s8_107c` Self-Test existiert seit v3.5.181 (Line 817)
- 5 parallele 401 → 1 Refresh-Request (via inflight-promise dedup)
- Keine neuen Code-Änderungen. Re-verify nach Block 1 B-020 Flow (B20-H throw statt degraded mode ändert nichts am Refresh-Path).

### Block 3 · v3.6.5 · ✅ B-022 Sweep verify (bereits v3.5.182-188)
- 146/146 setState-Spread → functional update abgeschlossen im 8h-Run
- `node sql/_b022_sweep.js` → 0 candidates · keine setX({...x,...}) mit matching setter-var mehr
- Keine neuen Änderungen.

### Block 4 · v3.6.6 · ✅ B-017 Verify-Helper (bereits v3.5.189)
- `window._b017check()` in Line 632 — PASS/FAIL verdict je nach Rolle
- Admin: PASS wenn Helpers exposed UND credentials nicht exposed
- Non-Admin: PASS wenn nichts exposed
- Keine neuen Änderungen.

### Block 5 · v3.6.7 · ✅ S8 Runner + T-B020 ergänzt
- `window._s8Suite()` existiert seit v3.5.190
- Neu: T-B020 Test — prüft Auth-Token ↔ _user Konsistenz (Soft-Render-Leak-Detection aus Block 1)
- Jetzt 9 automatisierbare Tests: T-101/106/106b/107a/110/111/112/117/B020

### Block 6 · v3.6.8 · ✅ Memory-Leak Re-Audit
- Scan: useEffect mit setInterval/addEventListener/subscribe ohne cleanup → 0 echte Leaks
  - 3 Kandidaten alle false-positive (cleanup vorhanden, nur außerhalb 30-Zeilen-Scan-Fenster)
  - L3298: bereits v3.5.191 gehärtet (PWA Install)
  - L3898: popstate-Listener mit removeEventListener in return
  - L4591: _vorlagenBus.subscribe() → return direkt die unsubscribe-Fn
- Balance: setInterval/clearInterval 8/9 · setTimeout/clearTimeout 53/15 (one-shots ok) · addEventListener/removeEventListener 16/15 (1 intentional module-level visibilitychange)
- Keine neuen Änderungen.

### Block 7 · v3.6.9 · ✅ SyncQueue Race verify (bereits hardened)
- `window._epkSyncInflight` Reentrancy-Guard (v3.5.138)
- Peek-based iteration (Snapshot aus SQ.getAll() + removeMany am Ende)
- Max 5 Retries → syncQueueFailed (v3.5.70)
- Retry-Count-Updates via SQ._serial (v3.5.141)
- Shared Mutex für push/remove (v3.5.139/140)
- _syncSkipCount Diagnose (v3.5.192)
- Keine neuen Änderungen.

### Block 8 · v3.6.10 · ✅ ErrorBoundary verify (bereits v3.5.193)
- `_ViewBoundary` class + 15 Hauptviews wrapped
- Top-level `EpkErrorBoundary` als Last-Resort
- Keine neuen Änderungen.

### Block 9 · v3.6.11 · ✅ Logging verify (bereits v3.5.194)
- `window._log(level,component,...args)` Helper
- `window._setLogLevel('debug')` Runtime-Switch
- Migration der 69 existierenden console-Calls bleibt schrittweise.

### Block 10 · v3.6.12 · ✅ Permission-Matrix (sql/PERMISSION_MATRIX_v3.7.md)
- Tab-Visibility-Matrix für alle 8 Rollen × 15 Tabs
- Action-Matrix gruppiert (Projekte / AS / FZ+WZ / Material / Zeit+Formulare / Mängel+BT / User-Mgmt / Export+Audit)
- RLS-Scope aus B-007 Policies (Monteur-Isolation via current_monteur_id())
- Keine Abweichungen zum SOLL-Stand
- Audit-Queries für Sebastian (Browser Console + Supabase SQL-Editor)

### Block 11 · v3.6.13 · ✅ Perf: useMemo für AS-Liste filter+sort
- `filtered` und `sorted` in AS-Liste waren O(n) + O(n log n) pro Render (auch bei unrelated setState)
- Jetzt `_react.useMemo.call(void 0, ..., [deps])` → nur recompute bei echten Änderungen
- Deps: arbeitsscheine, filters, sortCol/Dir, monteure, curUser
- Weitere React.memo auf Row-Components nicht applied (EntryRow ist inner-function, benötigt Props-Stabilisierung zuerst — nicht sicher genug für 1h-Block)
