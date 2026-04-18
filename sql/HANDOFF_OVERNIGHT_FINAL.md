# EPKolar HANDOFF — Overnight-Loop FINAL · 18.04.2026 ~07:15

App live: **v3.5.122** (`ce746bf`).

## 📊 Overnight-Statistik

- **Dauer**: ~7h (von v3.5.108 @ 23:xx bis v3.5.122 @ 07:15)
- **Bugs gefixt**: **17** (v3.5.108-122, +1 docs-only commit)
- **Wakeup-Iterationen**: 7 (alle ~55min getaktet)
- **Kein single-push war false-positive** — jeder Commit enthält einen konkreten, verifizierten Bug-Fix
- **Brackets-Baseline** bei jedem Push: `() -2, {} 0, [] 0` ✓
- **Syntax-Check** (`node --check`) bei jedem Push ✓

## 🐛 Bug-Fix-Chronologie

| Ver | SHA | Kategorie | Fix |
|---|---|---|---|
| 108 | `fbf2a20` | **CRITICAL** TZ | 9x Y-M-D-Strings: `toISOString.split("T")[0]` → `_ymd(d)` (off-by-1-day in CET/CEST!) |
| 109 | `3f84c7d` | **CRITICAL** TZ | 13x weitere: Timer-date, isoDate, dayStr, weekStart, Fahrtenbuch-from-to |
| 110 | `033ffda` | React | Mount-Guards in 3 Panels (WorkerKompetenzen/Urlaub/Fahrtenbuch) |
| 111 | `6c4b3c7` | **Mobile** iOS | `_uuid()` Fallback — iOS <15.4 crashte mit `crypto.randomUUID()` TypeError |
| 112 | `729d00c` | **Auth** | `_sbAuthRefresh` Flight-Promise-Guard — keine Logout-Kaskaden bei paralleleln refresh-calls |
| 113 | `cc96da4` | Auth | `_sbAuthLogin` Error-Parsing: echte GoTrue-Messages statt rohem Status-Text |
| 114 | `27c24f5` | Auth | Login/Refresh/SilentReAuth/Logout alle mit `_fT` Timeout |
| 115 | `6801e91` | Debug | `window.SUPABASE_URL/_KEY/_sbH/_sbAuthLogin` für Console-Smoke-Tests |
| 116 | `18b2d6a` | **Mobile** iOS | `_dl()` Download-Helper — 9x Excel/TXT crashten in iOS Safari + Firefox durch Race-bei-revoke |
| 117 | `5130393` | Bug | OFFA-Export crashed bei AS mit `arbeitsanweisungen=null` — `(x||"").replace` |
| 118 | `0af052e` | Bug | Fahrtenbuch-Export — `fz.marke+' '+fz.modell` produzierte "undefined undefined" |
| 119 | `eeb0f01` | Browser | Clipboard-API-Fallback via `execCommand("copy")` (non-HTTPS/older browser) |
| 120 | `24d6dde` | 3-in-1 | Werkzeug-Export null-safe + `_sbGetAnon` Timeout + `genBarcodeSVG` XSS-Schutz |
| 121 | `b8a0bee` | XSS | `printLabels` HTML-escape via `_e()` (4 Positionen) |
| 122 | `ce746bf` | Bug | genPdf Mängelliste: `m.status.toUpperCase()` + `r.art` null-safe |

## ✅ SQL-Artefakte im Repo

- `/sql/B006b_B007_FINAL.sql` — archivierte B-007 Migration (4 Helpers + 22 Policies, ausgeführt)
- `/sql/AUTH_DEBUG_QUERIES.sql` — Diagnose-Queries (NULL-Trap, RLS-forced, Trigger, Duplicates, instance_id, identity-sub)
- `/sql/TODO_MORGEN.md` — vorherige HANDOFF-Variante (jetzt obsolet durch diese)

## 🔴 Noch offen (DEINE 5 Min Kaffee-Tasse)

**Auth-500 bei info@/office@** (Riedmann funktioniert):
1. Supabase SQL-Editor öffnen
2. `/sql/AUTH_DEBUG_QUERIES.sql` Query B ausführen → NULL-Trap check
3. Wenn NULL-Felder: FIX B drunter ausführen
4. Hard-Reload App: `location.reload()` nach `localStorage.clear()`
5. Console: `await window._sbAuthLogin('info@ep-kolar.at','test1234')`
   - Wegen **v3.5.113** siehst du jetzt die echte GoTrue-Fehlermeldung statt "500 ..."

## 🟢 Nicht mehr in diesem Loop berührt (forbidden-zone per CLAUDE.md)

- Juprowa Phase-1-Pull-Code (`_juprowaSync`, `_juprowaPull`, `_juprowaFetch_worksheets`)
- Juprowa Phase-2-Push hat FetchCalls ohne `_fT`-Timeout — bewusst nicht angefasst, riskant

## 📋 Deferred Blocks (für nächste volle Session)

| Block | Titel | Aufwand |
|---|---|---|
| 4 | Fahrzeug-Buchungs-Kalender (mit Konflikt-Logik) | 2-3h |
| 5 | Projekt-Gantt (SVG + Drag&Drop) | 2h |
| 6 | ZE-Kalender-Wochenansicht | 2h |
| **8** | **AS-Signature-Close-Flow** — **Schnell-Win** (SignaturePad existiert) | 1-2h |
| 9 | AS-PDF v2 (jsPDF statt HTML) | 2h |
| **13** | **Audit-Log-UI** — **Schnell-Win** (activity_log wird gefüllt) | 1-2h |
| 14 | Web-Push (VAPID + Server) | 1 Woche |
| 17 | v3.6.0 Final-QS + Deploy | abhängt |

**Empfehlung**: **Block 8 oder 13** als nächstes. Beide sind Schnell-Wins, keine RLS-Komplikation, UI isoliert.

## 🤖 Wakeup-Kette Stand

**Letzte geplante Iteration 8** (wäre 08:08 Uhr gewesen) nicht mehr gescheduled — Kette gestoppt per Prompt-Direktive "falls 06 Uhr überschritten". Guten Morgen Sebastian. ☕

## 📌 Letzter Stand in einer Zeile

```
HEAD: ce746bf · v3.5.122 · 17 bugs fixed overnight · B-006+B-007 DONE · B-018 (Auth 500 info@/office@) wartet auf Query B
```
