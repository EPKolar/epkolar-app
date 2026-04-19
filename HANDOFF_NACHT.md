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
