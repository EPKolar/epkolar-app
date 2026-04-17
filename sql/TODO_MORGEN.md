# TODO MORGEN — Stand 18.04.2026 ~01:30

App live: **v3.5.116** (`18b2d6a`). Overnight-Bug-Hunt-Iteration 1 (Wakeup um 01:27) hat keine zusätzlichen low-risk-Bugs gefunden, die einen weiteren Push rechtfertigen. Kein false-positive Push gemacht.

## 🔴 Kritisch — DEINE Aufgabe (5 Min Kaffee-Tasse)

1. **Auth-500-Fix bei info@/office@**:
   - SQL-Editor öffnen → `/sql/AUTH_DEBUG_QUERIES.sql` (im Repo) → **Query B** ausführen
   - Wenn `_null=TRUE` Spalten → "FIX B" SQL drunter ausführen
   - Hard-Reload App → Console: `await window._sbAuthLogin('info@ep-kolar.at','test1234')`
   - **Wegen v3.5.113 zeigt der Fehler jetzt die echte GoTrue-Message**
   - Erwartung: Token-Object zurückgegeben statt 500-Error

2. **Falls FIX B nicht reicht**:
   - Query A (RLS forced auf auth.*)
   - Query C (Custom-Trigger auf auth.users)
   - Postgres-Logs im Dashboard → Filter `level=error` während Login-Versuch

## 🟡 Code-Verbesserungen, die ich gesehen aber nicht gefixt hab

### Vorhanden, aber nicht refactored (regression-risk zu hoch ohne Tests)
- **52× `setForm({...form,...})`** vs. nur 9× `setForm(prev=>{...prev,...})`. Stale-Closure-Risiko in async callbacks (z.B. SystemConfigPanel save). Erst migrieren wenn ein konkreter Bug auftaucht.
- **0× `aria-label`** auf 500 `<button>`s. Accessibility-Tooling fehlt. Wenn EU-Barrierefreiheit später wichtig: bulk-add via Code-Mod.
- **38× `setX` Calls in DOM ohne Mount-Guard** (außer den 3 die ich in v3.5.110 gefixt hab). Niedrig-priorität — nur 3 Panels haben tatsächlich das setState-after-unmount-Problem in Praxis.

### Bewusst ungefixt (Forbidden Zone per CLAUDE.md)
- Juprowa Phase-1-Pull-Code (`_juprowaSync`, `_juprowaPull`) — auch wenn dort fetch ohne Timeout ist
- `_juprowaPushAll` — könnte concurrency-guard kriegen, aber riskant

### Geringe ROI (skip außer auf User-Wunsch)
- Mehr `try/catch` um swallowed errors (21 leere `.catch()`, 26 leere `try{...}catch(_){}`)  → könnten zu activity_log loggen, aber meist sind das defensive Guards
- `setTimeout(fetchSuppliers, 500)` Pattern in 3 Stellen (Supplier-Liste) → könnte mit Promise.all + sofortigem refresh ersetzt werden
- Mobile a11y: `data-no-swipe` ist nur an 1 Stelle — andere Tabellen mit horizontal-scroll könnten auch davon profitieren

## ✅ Diese Nacht (3 Sessions, v3.5.108→116, alle gepusht)

| Ver | Stichwort |
|---|---|
| 108 | **CRITICAL TZ-Fix** — `kwD()` und 8 weitere Y-M-D-Builders waren in CET/CEST off-by-1-day (UTC ISO-Cut) |
| 109 | TZ-Fix Runde 2 — 13 weitere Stellen (Timer-date, isoDate, dayStr, weekStart, Fahrtenbuch-from-to, lastSync) |
| 110 | Mount-Guards in 3 Panels gegen setState-after-unmount |
| 111 | iOS <15.4 Crash-Fix — `_uuid()` Fallback statt `crypto.randomUUID()` |
| 112 | Auth-Refresh Flight-Promise-Guard — keine Logout-Kaskaden mehr |
| 113 | `_sbAuthLogin` Error-Parsing — echte GoTrue-Messages statt rohem Status-Text |
| 114 | Auth-Endpoints alle mit `_fT`-Timeout |
| 115 | `window.SUPABASE_URL/_KEY/_sbH/_sbAuthLogin` exposed für Console-Smoke-Tests |
| 116 | iOS Safari Download-Fix — `_dl()` Helper (anker zu DOM, +2s revoke) |

## 📋 Deferred Blocks (aus CC_OVERNIGHT_v3575.md)

| Block | Titel | Wann |
|---|---|---|
| 4 | Fahrzeug-Buchungs-Kalender | Sobald 1-2h Zeit |
| 5 | Projekt-Gantt | optional |
| 6 | ZE-Kalender-Wochenansicht | optional |
| 8 | AS-Signature-Close-Flow | **Schnell-Win** (SignaturePad existiert bereits) |
| 9 | AS-PDF v2 (jsPDF statt HTML) | wenn Print-PDFs gebraucht |
| 12 | SW Cache-Bust Auto | riskant — derzeit manuell ok |
| 13 | Audit-Log UI | Schnell-Win (activity_log wird bereits gefüllt) |
| 14 | Web-Push | braucht VAPID + Server — 1 Woche Aufwand |
| 15 | Mobile iOS-Quirks Final Pass | echte Geräte nötig |
| 16 | Perf-Benchmark + Indizes | 1h |
| 17 | v3.6.0 Final-QS + Deploy | nach 8/13 |

**Empfehlung**: Block 8 (AS-Signature) oder Block 13 (Audit-UI) als nächstes — beides 1-2h, beides isolierte Komponenten ohne RLS-Komplikation.

## 🤖 Wakeup-Status

Nächster geplanter Wakeup: nicht gesetzt (war in dieser Iteration: bei keiner Findung dokumentieren statt forced-pushen). Wenn du willst dass die Loop weiterläuft, einfach `weiter` schreiben oder `/loop 30min "fix bugs and push"`.
