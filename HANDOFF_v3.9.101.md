# HANDOFF v3.9.101 — 2026-06-03

## LIVE-STATE
- **App-Version:** v3.9.101 LIVE (https://epkolar.github.io/epkolar-app/)
- **main HEAD:** `abea06f` (12 SQL-Files + Sprint 82)
- **Letzter Code-Sprint:** Sprint 82 — Mein-Tag-Kachel komplett raus (Variante B)
- **Tests:** 575/575 grün
- **Backend:** Supabase `jiggujpruejkaomgxarp`

## ✓ FERTIG (live + verifiziert)
| Action | Status |
|---|---|
| Kiener User komplett (auth_user_id + monteur_id + Namen) | ✓ Chat-Claude live |
| notifications -1538 (Cleanup read=1 älter 30d) | ✓ live |
| `users_anon_select` DROPPED | ✓ live (anon-Hash-Leak ZU) |
| `users_anon_update` DROPPED | ✓ live |
| Sprint 82 v3.9.101 Mein-Tag-Kachel raus | ✓ pushed + live |
| Sprint 81 v3.9.100 (absences-Lookup Z14037 + Werkzeug-Kalib L18026 + checklists.items Cross-Device) | ✓ pushed |
| Sprint 79 v3.9.99 (Mein-Tag-Gate + Fuhrpark + Werkzeug-Kalib Helper) | ✓ pushed |

## 🔴 OFFEN — SQL BEREIT, NICHT AUSGEFÜHRT
Service-Role-Run via Sebastian/Chat-Claude im SQL Editor. **Tabelle für Tabelle mit Smoke!**

### Apply-Reihenfolge (Pro Schritt: SQL → Smoke barger-Token → grün=weiter / rot=ROLLBACK)

| # | Tabelle | SQL-File | Rollback-File | Smoke (barger) | Severity |
|---|---|---|---|---|---|
| 1 | **users** P0-1 | `sql/migrate_users_self_elevation_fix_v3104.sql` | `_ROLLBACK.sql` | PATCH role self/admin → 403 | 🔴 P0 |
| 2 | **supplier_configs** P0-2 | `sql/migrate_supplier_configs_creds_lockdown_v3105.sql` | `_ROLLBACK.sql` | View `supplier_configs_safe`: username/password=NULL | 🔴 P0 |
| 3 | **urlaubskontingent** P0-3 | `sql/migrate_urlaubskontingent_hardening_v3106.sql` | `_ROLLBACK.sql` | SELECT nur eigene, PATCH=403 | 🟠 |
| 4 | **projects** P0-4 | `sql/migrate_projects_hardening_v3107.sql` | `_ROLLBACK.sql` | PATCH=403, SELECT=200 | 🟠 |
| 5 | **system_config** P0-5 | `sql/migrate_system_config_hardening_v3108.sql` | `_ROLLBACK.sql` | SELECT=403 | 🟠 |
| 6 | **finkzeit+bescheinigungen** P0-6 | `sql/migrate_finkzeit_bescheinigungen_v3109.sql` | `_ROLLBACK.sql` | SELECT nur eigene | 🟡 |
| 7 | **activity_log_anon_insert** | `sql/migrate_activity_log_anon_drop_v3110.sql` | `_ROLLBACK.sql` | anon POST=403, authenticated POST=201 | 🟡 |
| 8 | **anon plans/projects/project_documents** | `sql/migrate_anon_portal_lockdown_v3103.sql` | `_ROLLBACK.sql` | anon nur Portal-Projekte sichtbar + Portal-Code-Login OK | 🟠 |

### Helper-Functions (neu, sprint-übergreifend)
- `is_admin()` (Sprint 53 v3.9.53)
- `is_admin_or_pl()` (v3.10.4) — admin OR projektleiter
- `is_hr()` (v3.10.5) — admin OR buero OR projektleiter
- `can_see_supplier_creds()` (v3.10.5) — admin OR PL OR rolle='Lagerleitung'

### Snapshots (Rollback-Reference)
Pro Migration `public._rls_snapshot_v310X` mit Original-Policies.

## 🟡 OFFEN — ANALYSE / ENTSCHEIDUNG

### absences B-A
- **AKTIVER Schreib-Bug Z14027** — schrieb worker_id=NAME statt wX
- **FIX:** ✓ Sprint 81 v3.9.100 (Z14037 Lookup `monteure.find(m=>m.n===sel).id`)
- **DB-Cleanup:** `sql/migrate_absences_fix_v3998.sql` NACH Code-Fix-Deploy ausführen (NAME→wX via Lookup)

### B-E +Neuer Benutzer (halb-Anlage)
- Aktuell: `/rpc/admin_reset_password` mit User-JWT scheitert → users-Row angelegt aber auth.users fehlt
- **Plan:** Edge-Function `supabase/functions/admin-create-user/index.ts` (Skeleton + Plan bereits in `f066304` pushed)
- **Sebastian-Action:** Deploy + Client-Code-Patch (Z7321-7326 auf Edge-Function umstellen)

### supplier_configs Stufe 2
- Stufe 1 (jetzt): View `supplier_configs_safe` + WRITE-Policies admin/PL/Lager
- Stufe 2 (nach App-Code-Sprint 83): SELECT-Policy supplier_configs restrict auf admin/PL
- App-Code-Sprint 83: Z7401 + Z12359 + alle Monteur-erreichbaren Pfade auf View migrieren

## 📋 SEBASTIAN-AKTIONEN

| # | Aktion | Reihenfolge |
|---|---|---|
| 1 | Apply 8 SQL-Files (Reihenfolge oben), Smoke dazwischen | NACH P0-1 zuerst |
| 2 | `scripts/audit_v3_9_95.ps1` — Self-Elevation-Probe als Verify | nach SQL #1 |
| 3 | Test-PWs rotieren (kiener Test1234! ist demo) | bevor Schulung |
| 4 | Händler-PWs rotieren (Heinze/Impex/SHT/ÖAG/Holter) | nach P0-2 |
| 5 | Edge-Function `admin-create-user` deployen | optional Sprint |
| 6 | App-Code-Patch B-E (Sprint 83) für Edge-Function | optional Sprint |
| 7 | `sql/migrate_absences_fix_v3998.sql` ausführen | nach Code-Fix LIVE-deployed |
| 8 | `sql/cleanup_notifications_v3998.sql` Option C | optional sofort |

## 🚫 NICHT-BUGS (dokumentiert)
- AS↔Projekte getrennt (92 AS.projektnr ohne projects-Match — Juprowa-Linkage, by design)
- 10 AS ohne Monteur-Zuweisung (Aufnahme-Status, by design)
- 4 Fahrzeuge ohne pickerl/service-Datum (N-719.920 / N-779.427 / TU-777DF / TU-481FK — manuell ergänzen)
- Werkzeug-Kalib-Code hat schon Null-Guards (Sebastian-Befund 298 evtl. truthy-stale-Werte in DB, NICHT Code)

## 📂 Code-Pfade (Reference)

### Login-Pfad (kritisch für RLS)
- `index.html` Z2163 `_sbAuthLogin`: nutzt RPC `login_lookup` (SECURITY DEFINER vermutlich)
- → anon-SELECT-Policy auf users NICHT vom Login-Pfad benötigt ✓

### Self-Elevation-Pfad
- `index.html` Z2198 `_sbPatch("users", id, {last_login, login_count})` — User-JWT, eigener User
- Policy `users_update_self_safe_columns` MUSS last_login/login_count erlauben (WITH CHECK)

### activity_log-Pfade
- Z2199 Login-Audit: `_sbPost("activity_log",...)` mit authenticated JWT
- Z2287/2852/3032/4432/18489 alle mit `_sbWH()` (authenticated JWT)
- → activity_log_anon_insert ungenutzt, kann gedroppt werden ✓

## 📦 ZIP-Reference
Alle SQL-Files in `sql/v3.10.x_handoff.zip` (siehe README im Repo)

## 🔗 Quick-Links
- Repo: https://github.com/EPKolar/epkolar-app
- Live: https://epkolar.github.io/epkolar-app/
- HEAD: `abea06f`
- Tag v3.9.101: `ee01561`

## 📅 Session-Stats (Marathon ~30+ Sprints)
- v3.9.16 → v3.9.101 (87 Versionen Code-Sprints)
- v3.10.0 → v3.10.5 (6 Security-SQL-Rollouts)
- ~140+ Findings analysiert
- ~80+ Tier-1 Fixes deployed
- 575 Tests grün (+57 in dieser Session, von 518 → 575)
- Brackets `() -1 / {} 0 / [] 0` stable durchgehend

— Ende Handoff —
