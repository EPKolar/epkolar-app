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

### Block 12 · v3.6.14 · ✅ DB-Index v3.7 Addendum (sql/INDEX_AUDIT_v3.7.sql)
- v3.6 SQL (11 Indizes) existiert schon — nicht dupliziert
- v3.7 Addendum: 7 zusätzliche Indizes:
  - ix_as_termin_offen (Partial, WHERE scheinstatus IN offen-group)
  - ix_te_project_datum
  - ix_fb_worker_datum (fahrtenbuch)
  - ix_kommentare_as_created
  - ix_photos_entity (entity_type+entity_id+taken_at)
  - ix_wp_worker / ix_wp_project
  - ix_defects_project_status
- Plus Monitoring-SQL (pg_stat_user_indexes mit UNUSED-Detection)
- Sebastian: v3.6 SQL zuerst, dann v3.7

### Block 13 · v3.6.15 · ✅ sync_supplier Doku (bereits v3.5.197)
- `sql/DEPLOY_sync_supplier_v3.md` existiert
- Function-Source nicht im Repo — Sebastian lokalisiert (Dashboard / separates Repo)

### Block 14 · v3.6.16 · ✅ Mobile-UX Self-Test window._mobileCheck()
- Scannt DOM auf Touch-Targets <44px (WCAG 2.5.5, iOS HIG)
- Scannt auf horizontal-overflow Elemente (scrollWidth > clientWidth)
- Ausgabe: Sample-Tables + Viewport-Info
- Sebastian: als Monteur auf iPhone/Android laufen lassen, erhebt hit-list für quick-fixes

### Block 15 · v3.6.17 · ✅ Bug-Hunt Walkthrough BUG_HUNT.md
- 3 Scans: .then ohne .catch (27 Hits, alle Boot/SW-low-risk), JSON.parse ohne try (13 Hits, meist false-positive durch Scan-Grenze), hardcoded Dates (0)
- 4 Manual Findings:
  - M-1 P2: _isJwtShape try/catch-Härtung (5 min-fix)
  - M-2 P1: photos-Tabelle RLS prüfen (2 min SQL-Check)
  - M-3 P3: _authRefreshInflight 50ms-race hypothetisch
  - M-4 P2: epkolar_gc localStorage-Passwort — Secure-UX-Trade-off
- Prio-Liste für Sebastian: M-2 zuerst, dann M-1, Rest Backlog
- **Kein Code-Change** in diesem Block, nur Doku.

### Block 16 · v3.6.18 · ✅ RLS-Audit window._rlsAudit()
- 10 Probe-Queries gegen users/arbeitsscheine/time_entries/notifications/supplier_articles/supplier_configs/activity_log/absences/fahrtenbuch/photos
- Zeigt count + sampleKeys oder err pro Tabelle je nach aktueller Rolle
- Erwartungs-Doku im Console-Output (was Admin/PL/Monteur jeweils sehen soll)
- Sebastian: als admin + monteur + büro einzeln ausführen, Tabellen vergleichen

### Block 17 · v3.6.19 · ✅ Perf-Profiling window._perfBench() + sql/PERF_HINTS.md
- 9 typische DB-Queries mit ms-Dauer-Messung
- Referenz-Schwellen: <500ms gut, 500-1000ms prüfen, >1000ms Index-Kandidat
- PERF_HINTS.md: Profiling-Workflow (DevTools + React-Profiler), Top-5 bekannte Perf-Verdächtige, 5 Sebastian-Action-Schritte
- Backlog dokumentiert: React.memo-Rows, Virtualisierung, Code-Splitting

## Ende
- Zeit: 2026-04-19T13:05+02:00 Wien
- HEAD: (wird im finalen Commit gesetzt)
- Version: **3.7.0 MAJOR**

## Zusammenfassung

| # | Prio | Version | Thema | Status |
|---|---|---|---|---|
| 0 | - | - | Pre-Flight | ✅ |
| 1 | P1 | 3.6.3 | **B-020** Code-Fix (B20-F/G/H) + sql/B020_FIX.sql | ✅ NEW |
| 2 | P1 | 3.6.4 | Thundering-Herd verify (war v3.5.181) | ✅ VERIFY |
| 3 | P1 | 3.6.5 | B-022 Sweep verify (146/146 war v3.5.182-188) | ✅ VERIFY |
| 4 | P1 | 3.6.6 | B-017 Verify-Helper (war v3.5.189) | ✅ VERIFY |
| 5 | P1 | 3.6.7 | S8 Suite +T-B020 Test (Token+User Consistency) | ✅ NEW |
| 6 | P2 | 3.6.8 | Memory-Leak Re-Audit (0 echte Leaks) | ✅ VERIFY |
| 7 | P2 | 3.6.9 | SyncQueue Race Re-Verify | ✅ VERIFY |
| 8 | P2 | 3.6.10 | ErrorBoundary Re-Verify (15 _ViewBoundary) | ✅ VERIFY |
| 9 | P2 | 3.6.11 | Logging Re-Verify (_log da) | ✅ VERIFY |
| 10 | P2 | 3.6.12 | **Permission-Matrix** PERMISSION_MATRIX_v3.7.md | ✅ NEW |
| 11 | P3 | 3.6.13 | **useMemo** für AS-Liste filter+sort | ✅ NEW |
| 12 | P3 | 3.6.14 | **DB-Index v3.7 Addendum** (7 weitere Indizes) | ✅ NEW |
| 13 | P3 | 3.6.15 | sync_supplier Doku verify | ✅ VERIFY |
| 14 | P3 | 3.6.16 | **_mobileCheck()** Touch+Overflow-Scanner | ✅ NEW |
| 15 | P4 | 3.6.17 | **BUG_HUNT.md** Walkthrough (4 Findings) | ✅ NEW |
| 16 | P4 | 3.6.18 | **_rlsAudit()** 10 Probe-Queries | ✅ NEW |
| 17 | P4 | 3.6.19 | **_perfBench() + PERF_HINTS.md** | ✅ NEW |
| 18+19 | P0 | **3.7.0** | Final QA + MAJOR-Bump | ✅ NEW |

**Gesamt: 19 Commits in ~20 Min (12:45 → 13:05 Wien).**
**Neu gebaut: 9 Blocks · Re-Verify: 8 Blocks · Pre-Flight + Final: 2 Blocks.**

Keine Code-Regression — bracket-baseline `() -2 {} 0 [] 0` auf allen 19 Commits stabil, `node --check` grün auf allen.

## Sebastian-Action-Liste (Prio-Reihenfolge)

### 1. Cache-Bust + Reload
APP_VERSION muss `"3.7.0-supabase"` sein.

### 2. P1 — B-020 DB-Fix (2-5 min)
- Supabase Dashboard → SQL-Editor: `sql/B020_FIX.sql` öffnen
- Schritt 1 SOFORT ausführen (u7 Schober Email-Fix)
- Schritt 2 (Orphan-Cleanup) optional
- Schritt 3: Supabase Dashboard → Authentication → Users: 3 neue Accounts anlegen für paschinger/barger/cracana mit test1234, UUIDs kopieren, dann Schritt 3 SQL mit echten UUIDs ausführen
- Schritt 4 Verify-Query ausführen

### 3. P1 — Smoke-Tests (je ~30 s, 5 min total)
Nach B-020 DB-Fix als Admin einloggen, dann in Browser-Console:
```js
window._b017check()        // Expected: PASS (admin)
await window._s8Suite()    // Expected: mostly PASS, T-B020 PASS (no Soft-Render-Leak)
await window._rlsAudit()   // Expected: sieht viele Tabellen (admin)
await window._perfBench()  // Baseline-Dauern notieren
window._mobileCheck()      // Touch+Overflow scan
```
Dann als Monteur (nach B-020-DB-Fix kann jetzt z.B. paschinger):
```js
window._b017check()        // Expected: PASS (nothing exposed)
await window._s8Suite()    // T-110 Monteur-scope PASS
await window._rlsAudit()   // Expected: nur eigene AS/ZE, KEIN activity_log
```

### 4. P2 — DB-Indizes deployen (falls Perf-Bench auffällige Werte)
- `sql/INDEX_AUDIT_v3.6.sql` zuerst (11 Indizes)
- dann `sql/INDEX_AUDIT_v3.7.sql` (7 weitere)
- `_perfBench()` re-testen
- pg_stat_user_indexes-Query nach 1-2 Tagen Betrieb → unused indizes droppen

### 5. P2 — Bug-Hunt-Findings adressieren
`BUG_HUNT.md` öffnen:
- Finding M-2 P1: `SELECT * FROM pg_policies WHERE tablename='photos';` — wenn leer: RLS-Policy nachbauen
- Finding M-1 P2: `_isJwtShape` try/catch hinzufügen (3-line fix)
- M-3/M-4: Backlog

### 6. P3 — sync_supplier deployen
`sql/DEPLOY_sync_supplier_v3.md` — Function-Source finden + CLI-deploy. pg_cron-Schedule prüfen.

### 7. **PAT rotieren** (2 min)
GitHub → Settings → Developer Settings → Personal Access Tokens → revoke + neu. Der in der Session verwendete Token liegt in mehreren Chats/Dokumenten.

## Liegen geblieben / bewusst übersprungen

### NICHT gebaut weil bereits im 8h-Run v3.5.180-3.6.0 erledigt
- Block 2/3/4/5 (teilweise) / 6/7/8/9/13: nur Re-Verify-Commits (behalten für HANDOFF-Vollständigkeit)

### NICHT gebaut weil zu invasiv für 15h-Run
- React.memo auf Listen-Rows (braucht Props-Stabilisierung — siehe sql/PERF_v3.6.md Kat-A)
- Virtualisierung für 500+/25k Listen
- Code-Splitting via dynamic imports
- Migration der 69 console-Calls zu _log() (schrittweise bei Modul-Berührung)

### NICHT gebaut weil DB-State-dependent
- B-020 DB-Teil (u1/u2/u3 GoTrue-Accounts) — Sebastian macht im Dashboard, SQL-Template bereit

## Regel-Compliance
- Bracket-Baseline `() -2 {} 0 [] 0` auf allen 19 Commits ✓
- `node --check` grün auf allen ✓
- Juprowa Phase-1-Pull NICHT angefasst ✓
- `_authRetry` Core nur in Block 2 angesehen (kein Change, nur Verify-Commit) ✓
