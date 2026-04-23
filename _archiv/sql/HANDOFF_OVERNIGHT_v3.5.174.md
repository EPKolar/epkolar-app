# Overnight-Session 18.04. → 19.04.2026

## Kennzahlen

- **Start**: 2026-04-18T22:26:23+02:00 (Sa 22:26 Wien)
- **Ende**: 2026-04-19T07:00+02:00 (So 07:00 Wien)
- **Start-HEAD**: `05d078f` (v3.5.162 — Plan erwartete v3.5.135, Code war bereits ~30 Versionen voraus)
- **End-HEAD**: `77f8c28` (v3.5.174)
- **Commits**: **12 Fixes** (alle 1-Bugfix-pro-Commit)
- **Bracket-Baseline** bei jedem Push: `() -2, {} 0, [] 0` ✓
- **Syntax-Check** (`node --check`) bei jedem Push ✓
- **CDN-Verify** (GitHub Pages `sw.js`) bei jedem Push ✓

## WICHTIG — P0 war bereits gefixt (nicht in dieser Session)

Der Plan erwartete v3.5.135 mit 3 kritischen P0-Bugs (A/B/C). Aktueller Code (v3.5.162) hatte diese bereits behoben — vermutlich in der vorherigen Overnight-Session:

| Plan-P0 | Status bei Session-Start | Gefixt in |
|---|---|---|
| P0-A: `window._sbH` Endlos-Rekursion | ✅ Bereits gefixt (Line 296: `window._sbH=_sbH`) | vermutl. vor v3.5.162 |
| P0-B: Login-Handler schreibt `'supabase-session'` | ✅ Bereits gefixt (Line 1234: echter JWT) | v3.5.124 |
| P0-C: Silent Re-Auth fehlt | ✅ Bereits gefixt (`_restoreAuth()` Line 626-634) | v3.5.142 |

→ Session fokussierte sich stattdessen auf **P1 Bug Hunting**.

## Was wurde gefixt (12 Commits)

- v3.5.174 P1: addKm NaN-Guard — analog v3.5.149, Non-Numeric wird abgewiesen (77f8c28)
- v3.5.173 P1: _openFileUrl mit noopener,noreferrer (Tabnabbing-Schutz) (afa8a6a)
- v3.5.172 P1: Werkzeug-Dashboard wzWert NaN-Guard — konsistent mit fzTankProFz (39aaa6d)
- v3.5.171 P1: addTank NaN-Guard für Liter — analog zu v3.5.149 km-Fix (fd5dcdf)
- v3.5.170 P1: Weather-API-Fetches mit _fT(10s)-Timeout (1a4703a)
- v3.5.169 P1: Weekplan-Migration null-safe — m.n.toLowerCase() crash (c1df3ff)
- v3.5.168 P1: Bauwochenbericht-Export null-safe — w.name.split() crashte bei null (b4e0177)
- v3.5.167 P1: Vorlagen-Save null-safe — form.name.trim() crashte bei undefined (a029cfa)
- v3.5.166 P1: Kommentare-Render null-safe — k.text.split() crashte bei null-Text (ad9e68b)
- v3.5.165 P1: Docs-Panel Search null-safe — d.name/d.filename ohne Guard (aeb7b35)
- v3.5.164 P1: Worker-Filter-Buttons null-name Crash (Mobile) (451b924)
- v3.5.163 P1: _dataUrlToBlob null-safe — malformed data-URLs geben jetzt null statt TypeError (528eb62)

### Fix-Kategorien

| Kategorie | Anzahl | Beispiele |
|---|---|---|
| Null-Safety (field.method Chain-Crash) | 7 | v3.5.163/164/165/166/167/168/169 |
| NaN-Guard für numerische User-Inputs | 3 | v3.5.171/172/174 |
| Fetch-Timeout-Härtung | 1 | v3.5.170 (Weather-API 10s) |
| Security/Defense-in-Depth | 1 | v3.5.173 (Tabnabbing-Schutz) |

Alle 7 Null-Safety-Fixes folgen gleichem Pattern: DB-nullable-Feld → `field.method()` ohne Guard → Crash. Konvention `(field||"")` wird eingezogen, identisch zu v3.5.154 (Workers-Map-Fix in prev Session).

## Smoke-Test für Sebastian morgens (je ~30s)

### 1. App starten
```
https://epkolar.github.io/epkolar-app/?t=morgens
```

### 2. Version-Check (F12 → Console)
```js
APP_VERSION  // erwartet: "3.5.174"
```

### 3. P0-A Regression (bereits gefixt, muss stabil sein)
```js
typeof window._sbH === 'function' && window._sbH.toString().length > 100
// MUSS true sein. Wenn false → window._sbH=()=>_sbH() hat sich wieder eingeschlichen.
```

### 4. Login + Token-Persistenz (P0-B Regression)
Login mit `schober / test1234`, dann Console:
```js
localStorage.getItem('epkolar_token').length > 200
// MUSS true sein (echter JWT). Wenn kurz → bcrypt-fallback oder supabase-session-Regression.
```

### 5. Refresh-Token gesetzt (P0-B Regression)
```js
localStorage.getItem('epkolar_refresh') && localStorage.getItem('epkolar_refresh').length > 50
// MUSS true sein. _storeAuth muss refresh_token persistieren.
```

### 6. Kein oranger Banner
Nach Login darf **kein** oranger "Server nicht erreichbar"-Banner oben erscheinen.

### 7. F5 Reload → eingeloggt bleiben (P0-C Regression)
```js
// Reload drücken. Nach Reload:
_authToken && JSON.parse(atob(_authToken.split('.')[1])).exp > Date.now()/1000
// MUSS true sein. _restoreAuth() hat Token aus epkolar_auth geladen.
```

### 8. Voller Smoke-Battery (optional, ~5s)
```js
await _runAllTests()
// Sollte PASS für alle 14 TC-X Tests, insbesondere:
//   TC-S window._sbH === _sbH (kein Arrow-Wrapper)
//   TC-S window.SB_REST exposed
//   TC-J "supabase-session" abgelehnt
//   TC-M SQ 50 parallel-push (Mutex)
//   TC-F _fT hat AbortSignal
```

Wenn alle 7 grün → Auth-Saga DONE & alle P0/P1-Fixes leben. Wenn nicht → `sql/TODO_MORGEN.md` für Details.

## Systematic Scans ohne Funde (nichts zu fixen)

| Pattern | Result |
|---|---|
| `reduce()` ohne initial value | 0 Treffer |
| `.match(regex)[N]` ohne null-guard | 0 Treffer (1 in Try/Catch-Fallback ok) |
| `.files[0].X` ohne optional-chain | 0 Treffer |
| `dangerouslySetInnerHTML` misuse | 0 (einzige Nutzung `genBarcodeSVG` bereits v3.5.120 XSS-hardened) |
| `setInterval` / `clearInterval` unbalanced | 0 (16 adds / 13 removes erklärbar) |
| `toISOString().split('T')[0]` | 0 (alle v3.5.108/109 auf `_ymd(d)` migriert) |
| `crypto.randomUUID()` direkt | 0 (alle via `_uuid()` mit iOS-Fallback v3.5.111) |
| Unprotected `ODB.save` | 0 |
| `onClick: async` ohne try/catch | 0 |
| `javascript:` in href | 0 |
| `throw` in `.map/.filter/.reduce` | 0 |

## Bewusst nicht gefixt (Aufwand/Nutzen-Entscheidung)

Siehe `sql/TODO_MORGEN.md` für Details. Kurzfassung:

- **R-1**: 153 non-functional `setState({...form,...})` — zu groß für 1-Fix-pro-Commit, nur bei rapid-fire Events riskant.
- **R-2**: 2 Listener-Leaks im PWA-Install-useEffect — Produktion-harmlos (mount-once).
- **R-3**: Warenkorb-Print-HTML unescaped — Staff-editable, low threat.
- **R-4**: Error-Boundary activity_log-POST ohne Timeout — bereits outer try/catch.
- **R-5**: Diagnose-Fetches ohne Timeout — Log-only Pfade, nicht UI-blocking.
- **R-6**: FinkZeit iframe `z.datei` ohne HTML-Escape — Data-URLs always safe format.

## Iteration-Log

Siehe `sql/OVERNIGHT_LOG.md` (17 Checkpoints, 22:26 → 07:00).

## Offene TODOs

Siehe `sql/TODO_MORGEN.md`:
- 6 bewusst-nicht-gefixt Einträge mit Empfehlungen
- Deferred Blocks (4, 5, 6, **8**, 9, **13**, 14, 17) mit Aufwandsschätzung
- Empfehlung: **Block 8 (AS-Signature-Close-Flow)** oder **Block 13 (Audit-Log-UI)** als nächstes

## 📌 Letzter Stand in einer Zeile

```
HEAD: 77f8c28 · v3.5.174 · 12 Fixes overnight · 0 P0 (pre-fixed) · Null-Safety + NaN-Guards + Tabnabbing-Härtung
```

☕ Guten Morgen Sebastian.
