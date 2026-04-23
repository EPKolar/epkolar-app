# sql/ — Aktive SQL + Doku

Dieser Ordner enthält **nur noch aktiv genutzte Dateien**. Alles historisch/erledigte
wurde in `../_archiv/sql/` verschoben (v3.8.24, 23.04.2026).

## Doku

- `ARCHITECTURE.md` — EPKolar-Architektur-Übersicht
- `SELFTEST_USAGE.md` — wie `window._selfTest()` genutzt wird
- `RLS_RECONCILE_v3.8.md` — RLS-Policy-Matrix pro Tabelle
- `Testkonzept_EPKolar_v5_0.md` — aktives Testkonzept
- `DEPLOY_sync_supplier_v3.md` — Edge Function CLI-Deploy-Anleitung
- `WHATSAPP_INTEGRATION_PLAN.md` — Feature 12 Planung
- `DEPLOY_SQL_REVIEW_2026-04-23.md` — Session-Review der damals offenen Deploy-SQLs
  (die meisten sind jetzt im Archiv, Doku bleibt als Kontext)

## SQL-Snapshots

- `RLS_SNAPSHOT_v3.8.sql` — Query für Soll/Ist-Vergleich der RLS-Policies

## Feature-12 WhatsApp (nicht deployed)

- `WHATSAPP_SCHEMA_v3.8.sql` — 2 Tabellen + RLS + Indizes
- `WHATSAPP_SEEDS_v3.8.sql` — 4 Default-Templates

## Tools (Node-Scripts)

- `_check_brackets.js` — Bracket-Balance auf index.html (erwartete Baseline: `() -2 {} 0 [] 0`)
- `_check_syntax.js` — Extrahiert `<script>`-Body aus index.html, ruft `node --check` auf tmp
- `_check_version.js` — Versions-String-Check (APP_VERSION ↔ CACHE_NAME ↔ sw.js-Header)
- `sql-runner.mjs` — Direkter pg-Runner für migration files (`.env` mit `SUPABASE_DB_URL`)

## Archiv

Alle älteren SQL-Files, Post-Mortems, Einmal-Scripts: `../_archiv/sql/`
(mit eigenem README.md zum Kontext).
