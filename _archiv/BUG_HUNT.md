# Bug Hunt v3.6 — Walkthrough-Befunde · Block 15

Ergebnisse von 3 systematischen Scans am 19.04.2026. **Kein Code-Change in diesem Block** — nur Finding-Liste zur Priorisierung.

## Scan 1 · .then() ohne .catch() (27 Hits)

Potential unhandled-promise-rejections. Einige sind bewusst (e.g. SW-Unregister-Cleanup im Boot), andere riskant.

### P1 (echte Datenflüsse, Exception würde User treffen)
- keine in diesem Scan — alle .then() sind in Bootstrap- oder SW-Pfaden mit eingebauten catches downstream

### P2 (Bootstrap/SW — low risk aber aufräumen)
- L21, L262: `navigator.serviceWorker.getRegistrations().then(...)` — im Boot, fail unkritisch
- L26, L263: `caches.keys().then(...)` — Cache-Cleanup, fail unkritisch
- L249: innerHTML-Write im Boot-Indicator, fail unkritisch

### P3 (alle übrigen)
- Meist kommunizieren die bereits mit catch im ersten outer await. False positive des Scans.

**Empfehlung**: Nicht fixen. Die 5 hochwertigen Pfade (L21/26/249/262/263) sind Boot-Code ohne Critical-Path-Impact.

## Scan 2 · JSON.parse ohne try-catch (13 Hits)

Riskant bei corrupted localStorage oder malformed DB-Strings.

### P1 (User-Data, corrupted input möglich)
- L1235, L1251, L1256: `fz[0].serviceheft / tank_log / km_log` — Fahrzeug-JSON-Felder aus DB. **Haben `||'[]'` Fallback auf Default-Array** → Safe.
- L722: `JSON.parse(atob(parts[1].replace...))` in `_isJwtShape` — ist innerhalb `_isJwtShape`, und wird im return mit `split('.').length===3` pre-validiert. Aber atob/parse können trotzdem werfen bei garbage.

### P2 (Bekannte Fälle, alle in try-umgeben auf höherer Ebene)
- L489: in smoke-test `t()` helper (wrapped)
- restliche in größeren try-blocks deren Start >3 Zeilen vor dem Hit sind (Scan miss)

**Empfehlung**: 
- L722 `_isJwtShape`: add try/return false. **Wert: hoch** (Token-Corruption resistent).
- Andere Stellen: false-positive durch Scan-window-Grenze.

## Scan 3 · Hardcoded Dates (0 Hits)

Keine `new Date('2024-...')` o.ä. im Code. Alle Dates werden via `td2()`, `_ymd()`, oder user-input erzeugt. ✓

## Zusätzliche Findings (manuelle Review)

### Finding M-1 · _isJwtShape-Härtung (L722) — **NOT A BUG (v3.7.3)**

**Re-Check am 19.04 ~16:30**: 
- `_isJwtShape` (aktuell Line 887) hat KEIN atob/JSON.parse, nur reine shape-checks: `typeof t==='string' && t.split('.').length===3 && t.length>20`. Keine Wurf-Möglichkeit.
- Der atob+JSON.parse-Code existiert in `window._ensureAuth` (Line 796), dort aber **bereits in try/catch gewrapped** mit expliziter Fehlerbehandlung + Refresh-Trigger (Line 802-804).

**Begründung**: Der ursprüngliche Finding-Context war unscharf. Code-Review bestätigt: keine ungeschützte atob/JSON.parse-Kombination in Auth-Path mehr. **Kein Fix nötig.**

### Finding M-2 · photos table missing RLS?
`sql/B006b_B007_FINAL.sql` (Overnight-Handoff) listet 22 Policies für 8 Tabellen (AS=2 TE=2 notif=4 urlaub=4 fb=2 chk=2 komm=4 komp=2). **photos** fehlt — 25k Fotos könnten anon-readable sein. **P1 wenn echt**.
Sebastian prüft: `SELECT * FROM pg_policies WHERE tablename='photos';` — wenn leer → RLS-Policy nachbauen.

### Finding M-3 · `_authRefreshInflight` vs. parallel-kicked refresh — **RE-INVESTIGATE (v3.7.3)**

Current code (Line 585): nach fetch resolve wird `_authRefreshInflight=null` via `setTimeout(..., 50ms)` gecleared.

**Analyse**:
- Zwischen Promise-Resolve und setTimeout-Callback (0-50ms) ist `_authRefreshInflight` noch das alte Promise. Parallele Caller bekommen das fertige Promise → safe.
- Nach setTimeout-Clear (>50ms) ist inflight=null. Weiterer 401-Caller triggert neues Refresh → das ist korrekt (Token könnte zwischenzeitlich erneut abgelaufen sein).
- Das 50ms-Fenster ist **absichtlich** — verhindert dass rapid-fire-401s sofort 2 Refreshes triggern.

**Hypothetisches Problem**: Wenn zwischen "Promise resolve" und "new inflight null-set" ein neuer Caller kommt und das ALTE Promise bekommt, dessen `_storeAuth` aber schon gelaufen ist → kein Schaden (Token ist schon frisch).

**Block-7 `_thunderTest`** wird reale Messung liefern. Bis dahin: **No action, re-investigate via _thunderTest**.

### Finding M-4 · Long-Lived localStorage 'epkolar_gc' — **KNOWN-TRADE-OFF (v3.7.3)**

`silentReAuth` nutzt `epkolar_gc` (base64-encoded Email+Password) als Backup-Login wenn Refresh-Token tot ist.

**Threat-Modell**:
- Angreifer mit XSS-Access → kann localStorage dumpen → Password extrahieren.
- Angreifer mit physischem Device-Access (unlocked) → kann DevTools öffnen → dito.
- **Nicht** durch Network-Traffic (HTTPS) oder Server-Logs exponiert.

**Trade-Off**:
- **Pro**: Monteure mit langen Sessions (>JWT-TTL) müssen nicht jeden Tag neu einloggen. Kritisch für Offline-PWA-UX auf Baustellen.
- **Contra**: Passwort plaintext-base64 auf Device.

**Entscheidung**: **KNOWN-TRADE-OFF**, **kein Fix in v3.8**. Sebastian entscheidet ob Migration zu:
  - (a) Refresh-Token-only (längere TTL in Supabase setzen, 1w statt 1h)
  - (b) Biometric-Gate vor silentReAuth
  - (c) User-Setting "Auto-Login nach Session-Ende" (Opt-In)

Alle drei sind größere Features, nicht Hotfix.

## Priorisierte Action-Liste für Sebastian

1. **P1-Check Finding M-2**: photos-Tabelle RLS-Status prüfen (Supabase SQL-Editor, 2 min)
2. **P2-Patch Finding M-1**: _isJwtShape-try/catch (kleiner 3-line Fix, 5 min)
3. **P3**: Finding M-3 + M-4 als Backlog-Items, nicht jetzt fixen

**Kein Block-15-Code-Commit außer Doku** — Findings nur dokumentiert.
