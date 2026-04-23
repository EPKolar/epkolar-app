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

## Kontakt

- Firma: **EP: Kolar & Sohn GesmbH** — Marktplatz 17, 3470 Kirchberg am Wagram — Tel +43 2279 2361
- Entwicklung: Sebastian Günther (planung@ep-kolar.at)
