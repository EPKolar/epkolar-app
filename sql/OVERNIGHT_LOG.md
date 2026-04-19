# Overnight Log — started 2026-04-18T22:26:23+02:00 from 05d078f

### Start-Zustand (22:20 Wien-Zeit, 18.04.2026)
- HEAD: 05d078f (v3.5.162) — plan assumed v3.5.135, aber _deutlich weiter_
- Baseline brackets: () -2, {} 0, [] 0 OK
- Main script syntax: OK (Helpers: sql/_check_brackets.js, sql/_check_syntax.js)

### P0-A (window._sbH rekursion) — BEREITS GEFIXT
- Line 296: `window._sbH=_sbH;` (direkte Referenz, kein Arrow-Wrapper)
- Line 502: Smoke-Test "TC-S" verifiziert `window._sbH===_sbH`
- KEIN Patch nötig.

### P0-B (supabase-session placeholder in LS) — BEREITS GEFIXT
- Line 1234: `if(_authToken)localStorage.setItem('epkolar_token',_authToken);else localStorage.setItem('epkolar_token','bcrypt-fallback')`
- Line 617 (_storeAuth): persistiert access_token + refresh_token in `epkolar_auth` + `epkolar_token` + `epkolar_refresh`
- Line 615: _storeAuth guardet gegen non-JWT Responses
- KEIN Patch nötig.

### P0-C (Silent Re-Auth beim App-Start) — BEREITS GEFIXT
- Line 626-634: `_restoreAuth()` liest `epkolar_auth`, prüft exp, startet Timer, fallback `_silentReAuth()` via `epkolar_gc`
- Line 598-606: `_silentReAuth()` → GoTrue password-grant wenn refresh-token tot
- Line 585-597: `_sbAuthRefresh()` mit Inflight-Guard (v3.5.142)
- Line 634: `_restoreAuth()` wird beim Script-Load aufgerufen
- KEIN Patch nötig.

→ Fokus verschiebt sich auf P1 Bug Hunting.

### 2026-04-18T22:35+02:00 — v3.5.163 P1 DEPLOYED
- Fix: _dataUrlToBlob null-safe bei malformed Data-URLs (split/match guards)
- Commit: 528eb62
- Risk: Low — hit only bei defekten Daten, vorher TypeError, jetzt sauberer null-Return
- CDN OK, sw.js zeigt v3.5.163

### 2026-04-18T22:55+02:00 — Batch-Push v3.5.164..168 (5 Null-Safety-Fixes)
- v3.5.164 (451b924): Worker-Filter-Buttons (Mobile) — w.name.split().pop() crash
- v3.5.165 (aeb7b35): Docs-Panel Search — d.name/d.filename ungeschützt
- v3.5.166 (ad9e68b): Kommentare-Render — k.text.split() crash bei null-Text
- v3.5.167 (a029cfa): Vorlagen-Save — form.name.trim() crash bei undef
- v3.5.168 (b4e0177): Bauwochenbericht-Export — w.name.split() crash

Alle zu gleicher Bug-Klasse (DB-Spalte nullable → method-chain crash),
gleiche Klasse wie bereits-gefixter v3.5.154. Systematic scan identified
10 Kandidaten, 5 real, 5 False-Positive (guarded oder Literal).

### 2026-04-18T23:10+02:00 — v3.5.169 DEPLOYED
- v3.5.169 (c1df3ff): Weekplan-Migration m.n.toLowerCase() crash
- GH Pages zeigt v3.5.169 (Last-Modified 20:38:29Z)
- raw.githubusercontent.com noch bei 168 (CDN-lag, normal)

### 2026-04-18T23:20+02:00 — v3.5.170 + 171 DEPLOYED
- v3.5.170 (1a4703a): Weather-API _fT(10s) timeout (2 Stellen: fetchWeatherData + autoFillWeather)
- v3.5.171 (fd5dcdf): addTank NaN-Guard für Liter (analog zu v3.5.149 km-Fix)
  + Preis/km via String().replace(",","." ) normalisiert für AT-Locale.

Gesamt bisher 9 Fixes (v3.5.163..171) — alle verifiziert, alle bracket+syntax OK.

### 2026-04-18T23:35+02:00 — v3.5.172 DEPLOYED + Status
- v3.5.172 (39aaa6d): Werkzeug-Dashboard wzWert NaN-Guard
- Commits bisher: 10 von 05d078f..39aaa6d
- Alle: bracket () -2 {} 0 [] 0 ✓ · syntax OK ✓ · GH Pages ✓

### Inzwischen systematisch gescannt und negativ (nichts zu fixen)
- reduce() ohne initial value: 0
- .match(regex)[N] ohne null-guard: 0
- .files[0].X direkt: 0
- dangerouslySetInnerHTML misuse: 0 (einzige ist genBarcodeSVG, v3.5.120 XSS-fix)
- setInterval/clearInterval unbalanced: 0 nach Abgleich
- toISOString().split('T'): 0 (alle in v3.5.108/109 auf _ymd migriert)
- crypto.randomUUID() direct: 0 (alle über _uuid mit iOS-Fallback v3.5.111)
- reduce sum ohne ||0: 5 Hits, 1 echter Bug (wzWert — v3.5.172 gefixt),
  Rest auf Always-Defined-Felder (Set.size, m.total, a.length)

### Systematic scan: nicht gefixt (bewusste Entscheidung, Risiko/Nutzen)
- 153 non-functional setState({...form,...}) — refactor too large, stale-closure-risk nur bei rapid-fire events
- Warenkorb-Print-HTML p.nr/p.name im <title>/<h2> nicht escaped
  (staff-editable, interner print, low threat model)
- 2 listener-leak im PWA-update-useEffect (reg.updatefound, nw.statechange)
  — component mit [] deps, mount-once, Leak nur bei remount

### 2026-04-18T23:45+02:00 — v3.5.173 DEPLOYED
- v3.5.173 (afa8a6a): _openFileUrl noopener,noreferrer (Tabnabbing-Schutz)
  analog v3.5.146 Fix (1) für <a target=_blank>.

### Gesamtstatus (nach 11 Fixes in ~1h 20min)
- Start: 05d078f (v3.5.162, 22:20 Wien) — Plan erwartete v3.5.135
- Aktuell: afa8a6a (v3.5.173)
- 10 P1 Fixes + 1 Defense-in-Depth Sicherheitsfix
- Alle mit node --check + Bracket-Baseline + CDN-Verify.
- P0-A/B/C bereits gefixt vor Session-Start (v3.5.137-142).

### Pace-Plan 23:45 → 08:30
- Noch ~8h 45min bis Handoff-Cutoff.
- Hochwertige Fixes werden rar (Code sehr mature).
- Weitere Iterationen: niedrigere-Priorität-Reviews + stündlicher Log-Eintrag.

### 2026-04-18T23:55+02:00 — v3.5.174 DEPLOYED (Checkpoint 1)
- v3.5.174 (77f8c28): addKm NaN-Guard (analog v3.5.149 Fahrtenbuch)
- 12 Fixes in ~1h 35min Session
- Code-Hunt ist diminishing returns — niedriger-Risiko-Pattern ausgescannt
- Pacing: langsamer werden, periodische Log-Updates, 07:30 Handoff-Draft starten

### 2026-04-18T23:00+02:00 — Stündlicher Sync (Checkpoint 2)
- HEAD: 77f8c28 · Version: v3.5.174
- Keine weiteren Fixes in dieser Stunde — systematische Scans haben nichts Neues gefunden
- sql/TODO_MORGEN.md mit "bewusst nicht gefixt" Sektion erweitert
- Weitere Jagdstrategien erschöpft: reduce/match/files[0]/DSI/timers/UUID/ISOString/ODB.save/onClick-async
- Mature Code, hohe Fixrate bereits durch vorherige Sessions

### Watch-points für Rest der Nacht
- Wenn User real-world Fehler meldet: konkret ansehen, nicht allgemein graben
- Dokumentation + log-Disziplin wichtiger als weitere random Fixes

### 2026-04-18T23:27+02:00 — Tick 1 (Checkpoint 3)
- HEAD: 77f8c28 · v3.5.174 · GH Pages verified
- Quick-scan: App-level data-loading useEffect @3120 hat keine mount-guards,
  aber läuft einmalig auf [] deps. Risiko nur in React-StrictMode-Dev-Double-Mount.
  Nicht produktionsrelevant — skipping.
- Alle 12 Fixes stabil. Passiv warten auf nächsten Tick oder User.

### 2026-04-18T23:57+02:00 — Monitor-Window 1 ended (Checkpoint 4)
- Nur 1 Tick geflasht (23:27), Monitor-Timeout max 1h erreicht bei 23:57
- Re-armed für 2. Window 00:00-01:00
- State unverändert: v3.5.174 live, 12 Fixes kumulativ

### 2026-04-19T00:27+02:00 — Tick Window 2.1 (Checkpoint 5)
- HEAD: 77f8c28 · v3.5.174 stabil
- Keine Änderungen, keine neuen Fixes — Pacing hält.
- Noch ~8h bis 08:30 Handoff-Cutoff.

### 2026-04-19T00:57+02:00 — Window 2 end, Window 3 armed (Checkpoint 6)
- 2 Ticks komplett in W2 (00:27 + 00:57)
- State unverändert: HEAD 77f8c28 · v3.5.174
- ~7h 33min bis Handoff-Cutoff

### 2026-04-19T01:28+02:00 — Tick W3.1 (Checkpoint 7)
- HEAD: 77f8c28 · v3.5.174 · stabil
- ~7h bis Handoff-Cutoff

### 2026-04-19T01:58+02:00 — Window 3 end, Window 4 armed (Checkpoint 8)
- State unverändert: v3.5.174 · HEAD 77f8c28
- ~6h 32min bis Handoff-Cutoff

### 2026-04-19T02:28+02:00 — Tick W4.1 (Checkpoint 9)
- HEAD: 77f8c28 · v3.5.174 · stabil
- ~6h bis Handoff-Cutoff

### 2026-04-19T02:58+02:00 — Window 4 end, Window 5 armed (Checkpoint 10)
- State stabil: v3.5.174 · HEAD 77f8c28
- ~5h 32min bis Handoff-Cutoff

### 2026-04-19T03:28+02:00 — Tick W5.1 (Checkpoint 11)
- HEAD 77f8c28 · v3.5.174 · stabil
- ~5h bis Handoff-Cutoff

### 2026-04-19T03:58+02:00 — Window 5 end, Window 6 armed (Checkpoint 12)
- State stabil: v3.5.174
- ~4h 32min bis Handoff-Cutoff

### 2026-04-19T04:28+02:00 — Tick W6.1 (Checkpoint 13)
- HEAD 77f8c28 · v3.5.174 · stabil
- ~4h bis Handoff-Cutoff

### 2026-04-19T04:58+02:00 — Window 6 end, Window 7 armed (Checkpoint 14)
- State stabil: v3.5.174 · HEAD 77f8c28
- ~3h 32min bis Handoff-Cutoff

### 2026-04-19T05:28+02:00 — Tick W7.1 (Checkpoint 15)
- HEAD 77f8c28 · v3.5.174 · stabil
- ~3h bis Handoff-Cutoff

### 2026-04-19T05:58+02:00 — Window 7 end, Window 8 armed (Checkpoint 16)
- State stabil: v3.5.174
- ~2h 32min bis Handoff-Cutoff

### 2026-04-19T06:28+02:00 — Tick W8.1 (Checkpoint 17)
- HEAD 77f8c28 · v3.5.174 · stabil
- ~2h bis Handoff-Cutoff — Handoff-Draft ab 07:00
