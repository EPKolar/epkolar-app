# sql/ — Aktive SQL + Doku

Dieser Ordner enthält **nur noch aktiv genutzte Dateien**. Alles historisch/erledigte
wurde in `../_archiv/sql/` verschoben (v3.8.24, 23.04.2026).

## Doku

- `ARCHITECTURE.md` *(parent root)* — EPKolar-Architektur-Übersicht
- `SELFTEST_USAGE.md` — wie `window._selfTest()` genutzt wird
- `RLS_RECONCILE_v3.8.md` — RLS-Policy-Matrix pro Tabelle
- `Testkonzept_EPKolar_v5_0.md` — aktives Testkonzept
- `DEPLOY_sync_supplier_v3.md` — Edge Function CLI-Deploy-Anleitung
- `WHATSAPP_INTEGRATION_PLAN.md` — Feature 12 Planung
- `DEPLOY_SQL_REVIEW_2026-04-23.md` — Session-Review der damals offenen Deploy-SQLs

### Audit-Docs (24.04.2026 Overnight)

- `CANDO_MATRIX.md` — 44-Actions × 7-Rollen Permission-Matrix
- `_authretry_gaps.md` — 27 fetch-Sites klassifiziert (13 wrapped, 4 gaps)
- `SMOKE_TESTS_v3.8.33.md` — 17 Prüfungen für v3.8.33 Iter-19-Fixes

## SQL-Snapshots

- `RLS_SNAPSHOT_v3.8.sql` — Query für Soll/Ist-Vergleich der RLS-Policies

## Human-Run-Gate — offen/manuell (14.07.2026)

- `STEMPEL_TERMINAL_v1.sql` — **offen.** Eigene Kiosk-Rolle `stempel_terminal`
  für die Stempeluhr (analog `lager_display`): RPC `stempel_terminal_workers()`
  (minimale Felder id/name/role/nfc_uid), SELECT+INSERT (kein UPDATE/DELETE)
  auf `stempel_log`, SELECT auf `system_config` Key `stempel_pause_rules`.
  Kein `auth.users`-Write (Auth-User legt Sebastian im Dashboard an, siehe
  Kommentarblock in der Datei). Zusätzlich nötig, aber NICHT Teil dieser
  SQL-Datei: App-Gate `?screen=stempel` (index.html ~Z.7376) um die neue
  Rolle erweitern + StempelTafel auf die RPC umstellen.
- `GPS_RETENTION_v1.sql` — **offen/manuell, nicht scharf geschaltet.** 12-Monats-
  Retention für `fz_positions` (GPS-Rohpunkte). `fz_fahrten` bleibt unberührt
  (Fahrtenbuch/Auswertung hängen an den aggregierten Fahrten, nicht an den
  Rohpunkten). Enthält nur auskommentierten DELETE-Einzeiler + auskommentierten
  pg_cron-Vorschlag (Extension muss vor Aktivierung erst eingeschaltet werden).
  `fz_positions` ist Stand 14.07.2026 leer (Tracker NICHT bestellt, keine Daten)
  — reine Vorsorge, kein akuter Handlungsbedarf.

## Feature-12 WhatsApp (nicht deployed)

- `WHATSAPP_SCHEMA_v3.8.sql` — 2 Tabellen + RLS + Indizes
- `WHATSAPP_SEEDS_v3.8.sql` — 4 Default-Templates
- `WHATSAPP_P3_TYPECHECK.sql` — FK-Typ-Verifikation (text vs uuid für arbeitsschein_id/projekt_id)

## Deploy-Reihenfolge (Full-Rebuild)

Bei einer hypothetischen Neuinstallation auf leerer Supabase-Instanz:

1. **Baseline-Schema** (out of scope hier — käme aus externen Migrations)
2. **RLS-Helpers** (`current_monteur_id()`, `current_user_role()`, `is_staff()`) — aus `../_archiv/sql/B006b_HEILUNGS_SQL.sql`
3. **B-007 Monteur-RLS Policies** — `../_archiv/sql/B007_EXECUTE.sql`
4. **Feature-12 Schema** — `WHATSAPP_SCHEMA_v3.8.sql` (vor Seeds!)
5. **Feature-12 Seeds** — `WHATSAPP_SEEDS_v3.8.sql` (setzt Templates voraus)

## Abhängigkeiten

- `WHATSAPP_SEEDS_v3.8.sql` hängt von `WHATSAPP_SCHEMA_v3.8.sql` ab (Fremdschlüssel
  auf `whatsapp_templates`).
- RLS-Policies hängen von Helper-Funktionen ab.
- `RLS_SNAPSHOT_v3.8.sql` ist read-only und kann jederzeit laufen.

## Idempotenz

- `WHATSAPP_SCHEMA_v3.8.sql` ist `CREATE TABLE IF NOT EXISTS` + `DROP POLICY IF EXISTS
  ... CREATE POLICY` — re-run sicher.
- `WHATSAPP_SEEDS_v3.8.sql` soll idempotent sein (UPSERT per `ON CONFLICT (name)` seit
  v3.8.9 Audit-Fix `e09438b`).

## Tools (Node-Scripts)

- `_check_brackets.js` — Bracket-Balance auf index.html (erwartete Baseline: `() -2 {} 0 [] 0`)
- `_check_syntax.js` — Extrahiert `<script>`-Body aus index.html, ruft `node --check` auf tmp
- `_check_version.js` — Versions-String-Check (APP_VERSION ↔ CACHE_NAME ↔ sw.js-Header)
- `sql-runner.mjs` — Direkter pg-Runner für migration files (`.env` mit `SUPABASE_DB_URL`)

## Archiv

Alle älteren SQL-Files, Post-Mortems, Einmal-Scripts: `../_archiv/sql/`
(mit eigenem README.md zum Kontext).
