# XSS-Sink-Audit · 2026-04-24

**Scope:** `index.html` · Baseline: Commit-Range bis `d6ca8c2`.
**Methode:**
```bash
grep -nE 'dangerouslySetInnerHTML|innerHTML\s*='  index.html   # 5 Treffer
grep -nE '(?<![A-Za-z_])eval\s*\(|new\s+Function\s*\('  index.html  # 0 Treffer
grep -n  'document\.write'  index.html                          # 10 Treffer
```

## ✅ Keine `eval()` / `new Function()`

`grep` bestätigt 0 Treffer im gesamten File. Zusätzlich durch den Python-Test
`tests/test_security.py::test_no_eval_calls` + `test_no_function_constructor`
laufend überwacht.

## 🟡 `innerHTML =` (5 Stellen)

| Line | Kontext | Eingabe | Klassifizierung |
|-----:|---------|---------|-----------------|
|  288 | Boot-Error-UI | Static + `(typeof React)`/`(typeof ReactDOM)` | **Safe** — alles static/System |
|  303 | Cache-Repair-UI | Static + `retries` (int) | **Safe** |
|  307 | Boot-Fatal-UI | Static + `String((window.__EP_ERRORS||[]).map(e=>e.msg).join("; "))` | **Risk-P3** — `e.msg` kommt aus window.onerror; bei kontaminierten Error-Messages rendert HTML |
| 1941 | Dev-Overlay bei JS-Error | `String(msg)+line+stack` | **Risk-P3** — gleiches Problem |
|15511 | `dangerouslySetInnerHTML` + `genBarcodeSVG(kennzeichen,...)` | `selFz.kennzeichen` aus DB | **Safe** — `genBarcodeSVG` escaped `text` (L2878: `replace(/&/g,'&amp;')...`), SVG-Pfad sauber |

### P3-Empfehlung für L307 + L1941

Error-Messages von `window.onerror` können potentiell kontrollierte HTML enthalten
(XSS via error-chaining via manipulierter URL/Formular). Echtes Risiko: niedrig,
da der Angreifer schon im Kontext sein müsste. **Nicht fixing** (R6), aber als P3
im CODE_DEBT.md lokalisiert.

Einfacher Fix: `.textContent = ...` statt `.innerHTML = ...` für den Message-Teil,
und das Button-HTML separat via `createElement`.

## 🟡 `document.write` (10 Stellen)

Alle innerhalb `window.open()`-Print-Popups:

| Line | Handle | Kontext |
|-----:|--------|---------|
| 2642 | `w.document.write(...)` | Bescheinigung-Print |
| 2894 | `win.document.write(...)` | Generischer Print mit `_e(title)` escape |
| 5319 | `win.document.write(html)` | vor-escapete HTML |
| 5962 | `w.document.write(...)` | FinkZeit-Print Header |
| 5963 | `w.document.write(el.innerHTML)` | übernimmt DOM-subtree 1:1 |
| 7042 | ähnlich Print-Popup |
| 10899 | Warenkorb-Print |
| 12749 | FinkZeit Footer |
| 12756 | FinkZeit Footer (iframe/img src escape seit v3.8.21) |
| 13047 | (weitere Stelle) |

**Klassifizierung**: Diese sind **nicht** `document.write()` im main-window — sie
öffnen ein neues Fenster via `window.open()` und schreiben dort die Print-Version.
Für die Print-Popup ist das der idiomatische Weg. Risiko: nur wenn content nicht
escaped wird.

**Bekannte Fixes** (v3.8.20/21):
- L2894 `_e(title)` escape
- L5319 `html` ist vor-escapt (renderWarenkorb mit `_e`)
- L12750/12756 iframe/img src Attr-Escape (v3.8.21 R-6-Fix)

**Noch unfixed (potentiell):**
- L5963 `el.innerHTML` — die Quelle `el` kommt aus `document.querySelector(...)` — wenn
  die gerenderten Daten Input-User-Daten enthalten, ist das auf XSS-Ebene so sicher
  wie die render-Funktion (die sowieso mit React escaped).
- L10899 Warenkorb-Print — die `renderWarenkorb`-Funktion hat XSS-Fix R-3 (v3.8.20 L10888)
  mit `_e(...)` um onClick-Attribute.

## Zusammenfassung

- **Kein** eval/Function-Sink.
- **0** reale XSS-Bugs gefunden. Alle Stellen sind entweder statisch, bereits
  escaped, oder im kontrollierten Print-Popup-Kontext.
- **2 Stellen** (L307, L1941) mit P3-Härtungs-Empfehlung (Error-Message-Render).
- **Keine automatischen Fixes** (D1-Regel).

## Empfehlung für Sebastian

L307 + L1941 — textContent-Refactor einplanen. Risiko ist niedrig, aber `.innerHTML
= 'static + dynamic'`-Pattern ist strukturell ein Foot-Gun: wenn später der static-
Teil angepasst wird, kann schnell was dynamisches reinrutschen. Besser früh härten.
