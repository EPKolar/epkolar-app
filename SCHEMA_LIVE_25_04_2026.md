# Live-DB-Schema EPKolar (Stand 25.04.2026 abends)

Verifiziert via REST-HEAD-Calls auf Supabase Production am 25.04.2026 ~18:00 (Sebastian).

## Existierende Tabellen

| Tabelle | Rows | Wichtige Spalten | Notiz |
|---|---|---|---|
| arbeitsscheine | 63 | scheinstatus, monteur, aufgenommen | scheinstatus="in_bearbeitung" (snake!) |
| workers | 9 | id (text!), name (eins!), role | nicht uuid, nicht vorname/nachname |
| users | 9 | username, role, email, auth_user_id | alle 9 verlinkt |
| fahrzeuge | 17 | kennzeichen, pickerl, naechst_service | snake_case |
| werkzeuge | 298 | letzte_kalib, naechste_kalib, status, zugewiesen, standort | |
| tickets | 2 | id, plan_id, x, y, status, type | KEIN xPct/yPct/page (B034 add für page) |
| plans | 1 | file_url, data_url (leer), is_pdf, width/height/version | file_url ist Storage-URL |
| absences | 3 | worker_id, von, bis, art | 3 Zombies worker_id='Günther' (B026) |
| weekplans | 4 | data (JSONB-Blob, RMW) | |
| time_entries | 36 | | |
| bautagebuch | 4 | | |
| photos | 0 | | |
| supplier_articles | 25.121 | | Holter UID=200079 |
| supplier_configs | 9 | | |
| supplier_orders | 0 | | |
| system_config | 8 | | |
| activity_log | 1.160 | | |
| notifications | 1.166 | | |
| finkzeit | 1 | jahr, monat, worker_id, status, data | worker_id = users-PK (u1-u9) |
| as_checklist | 0 | | |
| projects | 3 | | (NICHT projekte!) |

## Phantom-Tabellen (Memory-Bereinigung)

- **"projekte"**: 27× im Code, 0 _sbGet-Calls — ist deutsche UI-Variable für i18n, KEIN DB-Bug
- **"login_audit"**: 0 Code-Treffer — Phantom, war im alten Memory falsch dokumentiert
- **"rabatt_gruppe"**: 0 Code-Treffer — Phantom, war im alten Memory falsch dokumentiert

## Code-vs-DB-Mismatches (heute behoben)

- **v3.8.55 → v3.8.56**: PlanViewer expected `dataUrl`, DB has `file_url` → `_planSrc`-Resolver (`dataUrl || data_url || file_url`) + `_planLoadPdf` https-Support
- **v3.8.57 → v3.8.59**: tickets B-033 Auto-Migration in `xPct`/`yPct` (existieren nicht!) → korrigiert auf x/y-only. Component konvertiert beim Render via `pageDims.baseWidth/Height`. `_sbPatch` Auto-Migration entfernt. B033-SQL als `.DEPRECATED.sql` umbenannt mit Header-Warnung. Pin-Place konvertiert xPct → Pixel x/y vor Server-Push.

## camelCase → snake_case Mapping

`_mapBody` (L1366-1410) konvertiert camelCase-Frontend-Keys zu snake_case-DB-Spalten:
- Explizite RENAME-Liste: 30+ Keys (z.B. `projectId → project_id`, `dataUrl → data_url`, `naechstService → naechst_service`)
- Auto-Conversion via `_toSnake` für unbekannte camelCase-Keys
- `_translateAndExec` (L1598) ruft `_mapBody` IMMER für Generic-CRUD (L1845) — auto-applied bei jedem SQ.push.

Direkte `_sbPatch`/`_sbPost`-Calls umgehen `_mapBody`, schicken Keys 1:1. Diese Calls verwenden:
- snake_case-Keys direkt (korrekt: L1696/L1721/L1736/L1754/L1937/L1938/L1968/L2526/L2675/L2687/L2688/L2691/L2737)
- ODER absichtlich vorgemapped via `mapped=_mapBody(body)` (z.B. L1684/L1834/L1845)

## Pending nach Urlaub (manuell auf Supabase ausführen)

1. **B026_zombies_cleanup.sql** — 3 Zombies in `absences` mit worker_id='Günther' (Bug 4dd8a67 pre-fix)
2. **B034_tickets_page_column.sql** — `ALTER TABLE tickets ADD COLUMN IF NOT EXISTS page integer DEFAULT 1` für Multi-Page-Support
3. **B-027 sync_supplier Edge Function** — CLI-Deploy via `npx supabase login` + `supabase functions deploy sync_supplier`
4. **BASELINE_FIX_v3.8.sql** (falls noch offen) — UNIQUE-Constraints auf `users.email` + `arbeitsscheine.juprowa_id`

## NICHT mehr ausführen (deprecated)

- **B033_pixel_to_pct_migration.DEPRECATED.sql** — würde xPct/yPct/page-Spalten anlegen die der Code NICHT mehr nutzt (Auto-Migration in v3.8.59 entfernt). Datei behalten für Audit-Trail.

## Memory-Update für Sebastian

- "projekte" ist KEINE DB-Tabelle — nur UI-Variable. Vergessen.
- Schema-Drift-Patterns suchen via `_sbGet`/`_sbPost`/`_sbPatch`-Body-Inhalt vs Tabellen-Schema (siehe v3.8.57 `test_schema_assumptions.py`).
- Vor neuen Auto-Migrations: erst ALTER TABLE ausführen + Spalten verifizieren via `SELECT column_name FROM information_schema.columns WHERE table_name='X';`
