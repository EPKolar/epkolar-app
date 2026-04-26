# Live-DB-Schema EPKolar (Stand 26.04.2026)

Sebastian-verifiziert via Supabase REST + Postgres-Console. Snapshot So 27.04 früh nach v3.8.64-Mega-Run.

## Existierende Tabellen (45 total, 23 wichtigste hier)

| Tabelle | Rows | Wichtige Spalten | Notiz |
|---|---|---|---|
| arbeitsscheine | 63 | scheinstatus, monteur, aufgenommen, juprowa_id, push_pending | scheinstatus="in_bearbeitung" snake |
| workers | 9 | id (text!), name (eins!), role, aktiv | id-Format w1-w9 |
| users | 9 | username, role, email, auth_user_id | id-Format u1-u9 + admin |
| fahrzeuge | 17 | kennzeichen, pickerl, naechst_service, km_stand, km_log, tank_log, serviceheft | snake_case durchgehend |
| werkzeuge | 298 | inventarnr, name, kategorie, status, zugewiesen, standort, wert, zustand_bewertung, letzte_kalib, naechste_kalib, serviceheft | |
| tickets | 2 | id, plan_id, x, y, status, type, gewerk | KEIN xPct/yPct (B033 deprecated). KEIN page (B034 pending). |
| plans | 1 | id, file_url, data_url (leer), is_pdf, width/height, version | file_url ist Storage-URL |
| absences | 3 | id, worker_id, von, bis, art | 3 Zombies worker_id='Günther' (B026 pending) |
| weekplans | 4 | data (JSONB) | RMW-Pattern |
| time_entries | 36 | worker, date, hours, projekt | |
| bautagebuch | 4 | datum, projekt | |
| photos | 0 | entity_type, entity_id | |
| supplier_articles | 25.121 | | Holter-UID 200079 |
| supplier_configs | 9 | | |
| supplier_orders | 0 | bestellt_von | |
| system_config | 8 | | |
| activity_log | 1.160+ | user_id (snake), action, details | |
| **notifications** | 1.166+ | id, user_id, type, title, body, link, read, created_at | **KEIN updated_at** (Bug-4 verifiziert via PGRST204) |
| finkzeit | 1+ | jahr, monat, **worker_id (= users-PK u1-u9!)**, status, data | NICHT workers-PK |
| as_checklist | 0 | | |
| projects | 3 | nr, name, kunden_nr, portal_code | NICHT 'projekte' (Phantom) |
| urlaubskontingent | varies | worker_id, jahr, vorjahr, woche, stunden, ueberstunden, urlaub | v3.8.64 zu STORES hinzugefügt (B-Bug-3) |

## Phantom-Tabellen (existieren NICHT, Memory-Bereinigung)
- "projekte" — UI-Variable, KEINE DB
- "login_audit" — alter Memory-Eintrag
- "rabatt_gruppe" — alter Memory-Eintrag

## Bestätigte Schema-Mismatches (in v3.8.64 behoben)
- **notifications.updated_at**: existiert NICHT in DB. _translateAndExec L1870 schickte unconditional → PGRST204 → SyncQueue 5x → drop. Fix: Blacklist `if(table!=='notifications')`. Commit `838c93d`.
- **finkzeit.worker_id**: ist users-PK (u1-u9), NICHT workers-PK (w1-w9). Code-Lookup in v3.8.63 fd7b42e auf dual-lookup users+monteure umgestellt.
- **urlaubsanträge.status**: 'genehmigt'/'ausstehend'/'abgelehnt'. v3.8.62 zog NUR genehmigte vom Rest ab. v3.8.64 e954f13 zieht jetzt genehmigt+ausstehend ab (Sebastian-Erwartung).

## Code-State der bekannten Sebastian-Bugs

| Bug | Status | Code-Pfad | Pending-DB |
|---|---|---|---|
| B-026 (3 Zombies absences worker_id='Günther') | code-side ok | — | sql/B026 manual cleanup |
| B-033 (xPct/yPct migration) | DEPRECATED | tickets bleibt x/y | NICHT ausführen |
| B-034 (tickets.page Spalte) | sql vorbereitet v3.8.64 | code rendert page-Filter | sql/B034 manual ALTER |

## V-Theme-Quirks (für künftige Audits)
- V-Object L3255 hat KEINEN `fg`-getter → `V.fg` ist undefined
- Defined: bg, sb, cd, bd, ac, tx, dm, mt, shadow, inputBg, optBg, calInv, grid, weBg, subBg, hov, rowAlt, empty
- 7 Stellen `color: V.fg` in v3.8.63 commit `92e833e` zu V.tx korrigiert

## ODB (IndexedDB) Schema
- DB_NAME: `epkolar_offline`
- DB_VER: `8` (v3.8.64, war 7 davor)
- 19 Stores: entries, forms, abs, absApprovals, files, planData, werkzeuge, arbeitsscheine, monteure, syncQueue, meta, projects, monteurProjekte, photoQueue, fahrzeuge, stundenzettel, notifications, syncQueueFailed, **urlaubskontingent** (NEU v3.8.64)
- ODB.get/set/del/getAll/clear haben graceful-degradation (v3.8.63 commit `e6dc384`): bei missing store → console.warn + no-op statt DOMException

## Pending nach Urlaub (manuell auf Supabase ausführen)
1. **B026_zombies_cleanup.sql** — 3 Zombies absences worker_id='Günther'
2. **sql/B034_tickets_page_column.sql** — `ALTER TABLE tickets ADD COLUMN page integer DEFAULT 1` (Multi-Page Tickets)
3. **NICHT** B033_pixel_to_pct_migration.DEPRECATED.sql ausführen
4. **B-027** sync_supplier Edge Function via CLI deployen

## Auth-Pfad
- GoTrue + Supabase RLS
- 9 users (alle 9 verlinkt zu auth_user_id)
- 9 workers (manche identisch zu users via u-zu-w-Mapping)
- Token-Refresh via _sbAuthRefresh + _silentReAuth (v3.8.52 force-logout-Fix)
- _authRefreshTimer auto-renewal vor exp

## silent-X-Logging (Stand 26.04, 163 total)
Top-Kategorien: silent-await (29), silent-dom (28), silent-ls (27), silent-async (11), silent-log (10), silent-toast (8), silent-haptic (7), silent-json (6), silent-notif (6), silent-auth (4). v3.8.64 SKIP wegen Bracket-Drift-Risiko bei Massenedits. Künftig: helper-Funktion mit Dedup für Console-Spam-Reduktion ohne catch-Edit.
