# TODO Morgen — nach Overnight-Session 18./19.04.2026

## ✅ Gefixt in dieser Session (v3.5.163 → v3.5.174)

12 Commits, alle mit Bracket-Baseline () -2 {} 0 [] 0 + node --check + GH-Pages-Verify.

Siehe `sql/OVERNIGHT_LOG.md` oder `git log 05d078f..HEAD --oneline`.

## 🟡 Bewusst nicht gefixt (Aufwand/Nutzen-Abwägung)

### R-1 · Non-functional setState (153 Stellen)
Pattern: `setForm({...form, field: v})` statt `setForm(prev=>({...prev, field: v}))`.
Stale-closure-Risiko nur bei rapid-fire Events (z.B. 2 Key-Presses <16ms).
Refactor wäre eigenes Projekt — nicht in 1-Fix-pro-Commit Regime machbar.
**Empfehlung**: gezielt nur bei beobachteten Stale-Updates, nicht flächendeckend.

### R-2 · PWA Install-useEffect Listener-Leaks (2 Stellen)
`reg.addEventListener("updatefound", ...)` und `nw.addEventListener("statechange", ...)`
ohne cleanup. In Produktion harmlos (App-Komponente mit `[]` deps → mount-once).
**Empfehlung**: Bei React StrictMode Double-Mount-Aktivierung ggf. explizit cleanup.

### R-3 · Warenkorb-Print-HTML: p.nr/p.name unescaped in <title>/<h2>
`renderWarenkorb` (Zeile 10152) interpoliert Projekt-Nr/-Name ohne HTML-Escape.
Internes Staff-Feature, Print-Popup — low threat model.
**Empfehlung**: Bei nächster Berührung `_e()` analog zu v3.5.144/157/158 einziehen.

### R-4 · Weather-API-Fetch @ 15316 (Error-Boundary activity_log POST)
Kein `_fT` Timeout. Aber bereits in äußerem try/catch, Fallback via Error-Boundary-UI.
Konsistent-Machen wäre nice-to-have.

### R-5 · Diagnose-fetches @ 332,335,471-479 (Smoke-Test + Startup-Log)
Kein `_fT` Timeout. Sind Test-/Log-Pfade, blocking UI ist unmöglich
weil async. Bewusst so belassen.

### R-6 · iframe/img src `z.datei` (FinkZeit Print) nicht _e()-escaped
Attribut-Injection theoretisch möglich wenn datei URL `"`-Zeichen enthält.
In der Praxis FileReader-Data-URLs → immer `data:mime;base64,...` Format.
**Empfehlung**: Bei nächstem FinkZeit-Touch als v3.5.144-Pendant nachziehen.

## 🟢 Audit-Ergebnis: Negative Scans (keine Funde)

| Scan | Treffer | Kommentar |
|---|---|---|
| reduce() ohne initial value | 0 | |
| .match()[N] ohne null-guard | 0 | |
| .files[0].X ohne optional-chain | 0 | |
| dangerouslySetInnerHTML misuse | 0 | einzige Nutzung genBarcodeSVG bereits XSS-hardened v3.5.120 |
| setInterval/clearInterval unbalance | 0 | |
| toISOString().split('T')[0] | 0 | alle v3.5.108/109 auf _ymd(d) migriert |
| crypto.randomUUID() direkt | 0 | alle via _uuid() mit iOS-Fallback v3.5.111 |
| Unprotected ODB.save | 0 | |
| onClick: async ohne try/catch | 0 | |
| javascript: href | 0 | |
| throw in .map/.filter/.reduce | 0 | |

## 🔵 Deferred Blocks (unverändert aus prev Handoff)

| Block | Titel | Aufwand |
|---|---|---|
| 4 | Fahrzeug-Buchungs-Kalender (mit Konflikt-Logik) | 2-3h |
| 5 | Projekt-Gantt (SVG + Drag&Drop) | 2h |
| 6 | ZE-Kalender-Wochenansicht | 2h |
| 8 | AS-Signature-Close-Flow | ✅ **DONE v3.8.7** (L5043 `_shouldAutoClose`) |
| 9 | AS-PDF v2 (jsPDF statt HTML) | 2h |
| 13 | Audit-Log-UI | ✅ **DONE v3.8.7 + v3.8.22** (Admin→Aktivität, Filter erweitert) |
| 14 | Web-Push (VAPID + Server) | 1 Woche |
| 17 | v3.6.0 Final-QS + Deploy | abhängt |

**Empfehlung**: Block 8 oder 13 als nächstes — beide Schnell-Wins.

---

## Update 2026-04-23 (v3.8.22)

Block 8 und Block 13 waren **bereits in v3.8.7 umgesetzt** (Bug-Hunt-Loop), aber nie hier als DONE markiert. Heute in v3.8.22 nur die echten Lücken geschlossen:

- **Audit-UI Filter-Dropdown** (L6583) war auf 5 Optionen beschränkt obwohl ACT_LABELS 20+ Action-Typen kennt. Erweitert auf 17 sinnvolle Gruppen inkl. `juprowa` (Pull+Push gemeinsam), `upload` (Foto+FinkZeit), `export` (3 Export-Typen).
- **Entity-Type-Filter** neu hinzugefügt — rendert `ENT_LABELS` als `<option>`-Liste, neuer Filter-Key `actFilter.entity`, server-seitig via `entity_type=eq.X`.

Block 8 hat keinen echten Gap (Auto-Close funktioniert, Edge-Cases abgedeckt).

Verbleibende Deferred: Block 4/5/6/9/14/17.
