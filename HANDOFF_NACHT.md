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
