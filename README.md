# EPKolar App

Single-File React-PWA für EP: Kolar & Sohn GesmbH (Haustechnik-Firma, Kirchberg am Wagram).
Arbeitsscheinverwaltung, Zeiterfassung, Material-Warenkorb, FinkZeit-Monatsabrechnung,
Fahrzeug- und Werkzeug-Management, Chef-Dashboard, Juprowa-Sync.

Aktuelle Version siehe `const APP_VERSION` in `index.html` bzw. `CACHE_NAME` in `sw.js`.

## Stack

- **Frontend**: React 18 via CDN (unpkg), alles inline in einer einzigen `index.html` (~16 k Zeilen)
- **Backend**: Supabase (PostgREST + GoTrue Auth + Storage), hosted
- **Deploy**: GitHub Pages (branch `main`, Root-Verzeichnis), SW-Cache für Offline
- **Node-Tooling**: nur für lokale Helper-Scripts (Syntax-/Bracket-Check), kein Build-Step

## Repo-Layout

```
index.html                 # Die gesamte App (inline JS+CSS+React)
sw.js                      # Service Worker (Cache-Strategie)
HANDOFF_v3.8.20.md         # Aktueller Handoff-Stand (neuer Versions-Handoff überschreibt diesen)

sql/                       # Aktive SQL-Scripts + Helpers + Referenz-Docs
├── _check_syntax.js       # Extrahiert <script>-Body aus index.html -> node --check
├── _check_brackets.js     # Bracket-Balance-Check (() -2 {} 0 [] 0 ist erwartete Baseline)
├── _deep_scan_nullable.js # Null-Safety-Scan
├── _b022_sweep.js         # Stale-Closure-Pattern-Scan (B-022)
├── _wrap_viewboundaries.js# Automatisches ViewBoundary-Wrapping
├── sql-runner.mjs         # pg-Client-Runner für offline SQL-Deploys
├── README.md              # Index aktiver SQL-Files
├── TODO_MORGEN.md         # Deferred/offene Blocks
├── ARCHITECTURE.md        # Architektur-Überblick
├── PERMISSION_MATRIX_v3.7.md # Rollen/Permission-Referenz
├── SELFTEST_USAGE.md      # window._selfTest() Doku
├── Testkonzept_EPKolar_v5_0.md # Aktuelles Testkonzept
└── ...                    # Offene Deploy-SQLs: BASELINE_FIX, PHOTOS_RLS, INDEX_AUDIT,
                           # RLS_SNAPSHOT+RECONCILE, WHATSAPP (Schema+Seeds+Plan)

_archiv/                   # Historische Artefakte (abgeschlossene Bug-Bs, alte Handoffs,
                           # superseded Testkonzepte). Nur für Nachvollziehbarkeit.
```

## Lokale Helper

```bash
node sql/_check_syntax.js    # -> "syntax OK" wenn index.html parsed
node sql/_check_brackets.js  # -> "brackets () -2 {} 0 [] 0" (die -2 ist False-Positive
                             #    aus Template-Literals, ist die gewünschte Baseline)
```

## Deploy

Push auf `main` → GitHub Pages baut automatisch (siehe `pages build and deployment` Action).
Kein separater Build-Step. SW cached `./index.html` + `./` (Shell), externe CDN-Assets
werden stale-while-revalidate gecached.

## Versioning

- Jeder Release = Commit mit Message `vX.Y.Z <titel>` + annotated tag `vX.Y.Z`.
- `APP_VERSION` (index.html) und `CACHE_NAME`/Header-Kommentar (sw.js) müssen synchron sein —
  der Cache-Name ist der Trigger für SW-Update-Flow.
- Work-in-Progress Commits verwenden `vX.Y.Z-wip <titel>` ohne Tag.

## Security

- Supabase RLS auf allen user-facing Tabellen (siehe `sql/PERMISSION_MATRIX_v3.7.md`).
- CSP im `<head>`-Meta restriktiv auf Supabase + open-meteo + cdnjs + unpkg.
- `_e(s)` HTML-Entity-Escape-Helper für Print-Popup-Templates.
- `_fT(init, ms)` Fetch-Timeout-Wrapper (AbortSignal-basiert).

## Aktuelle Version

**v3.9.86** (2026-06-03) — Sprint-65 Final-Sweep: Theme-Final-Push (~40 inline
`#ef4444` → `COLORS.ERROR` Top-Visibility-Sites: Sync-Banner, Notif-Badge,
Auswertung Push-Stau + Kritisch-AS, Maengel-Status-Map, Wetter T-max,
Dashboard FinkStats/Pickerl/dringende-AS, Voice-Recognition-Button),
Doc-Update README v3.9.86. 502/502 Tests grün, Brackets `() -1 / {} 0 / [] 0`.

Sprints recent (v3.9.79-86):
- v3.9.86 Sprint-65 Final-Sweep + Cleanup + Theme-Final-Push (40 Theme-Migrations)
- v3.9.85 Sprint-64 Mobile-Polish-Final + Touch-Optimization (10 fixes)
- v3.9.84 Sprint-63 Code-Quality-R + Hardening-R (13 fixes)
- v3.9.83 Sprint-62 NotifCenter-Polish + Date/Time-Refinement (6 fixes)
- v3.9.82 Sprint-61 Search+Filter-Round + UX-Refinement (9 fixes)
- v3.9.81 Sprint-60 Form-Validation-R3 + Tooltips-R2 + Confirm-Migrations (10 fixes)
- v3.9.79-80 vorherige Sprint-Wellen

## Dev-Quickstart

```bash
# Lokaler Test-Server:
python -m http.server 8765 --bind 127.0.0.1

# Tests laufen:
python -m pytest tests/ -q
# Erwartet: 502 passed (Stand v3.9.86)

# Brackets-Sanity (stripper-Variante, ignoriert Strings/Kommentare):
python scripts/_bracket_check.py index.html
# Erwartet: () -1 / {} 0 / [] 0 (stable Baseline seit v3.9.12)
```

## Hard-Constraints (DO NOT TOUCH)

- Auth-Funktionen: `_silentReAuth`, `_sbAuthRefresh`, `_sbRH`, `_sbWH`, `_sbH`, `_storeAuth`
- OFFA push/sync code
- Juprowa-code
- `_optionalChain` (Build-output)

## Docs

- `docs/SESSION-WRAP-2026-05-17.md` — letzter Session-Outcome
- `docs/RESUME-2026-05-17.md` — Resume-Procedure
- `MOBILE_INVENTORY.md` — Mobile-Issue-Inventar
- `MOBILE_SMOKE_v3.8.67.md` — Mobile-Test-Checkliste

## Tests

502 Tests in `tests/` (source-code-pattern-assertion-Style, kein React-Render).
Stil: `tests/test_dringend_filter.py`.

## Kontakt

- Firma: **EP: Kolar & Sohn GesmbH** — Marktplatz 17, 3470 Kirchberg am Wagram — Tel +43 2279 2361
- Entwicklung: Sebastian Günther (planung@ep-kolar.at)
