# HANDOFF v3.9.105 — 2026-06-03 (Autonomer CC-Sprint)

## LIVE-STATE
- **App-Version:** v3.9.105 (war v3.9.101 zu Sprint-Beginn) — https://epkolar.github.io/epkolar-app/
- **main HEAD:** gepusht (Commits 23f3fb2 → … auf `main`)
- **Tests:** 589+ pytest grün · Bracket-Baseline `() -1 / {} 0 / [] 0`
- **Backend:** Supabase `jiggujpruejkaomgxarp`

## ✓ GEPUSHT (Code, live nach GitHub-Pages-Build)
| Version | Inhalt |
|---|---|
| **v3.9.102** | **P0 3 Tab-Crashes** (Schulungs-Blocker): Monatsabrechnung/stunden (StundenzettelView `const isMob` fehlte), Auswertungen (ChartBox `const ww=useW();const isMob`), Werkzeuge (`scanning`-useState VOR den `[scanning]`-Effekt → TDZ). **+ Auth-Session-Robustheit**: `_sbAuthRefresh` Offline-Guard + 4xx-Rotation-Retry (Storage-Reread statt sofort Logout), `_storeAuth` RT-first + 80%-Refresh-Timer, `_restoreAuth` 10-Min-Headroom, Single-Flight erhalten. |
| **v3.9.103** | **A2 absences hours-Bug** (aktiver Quota-Defekt): Kalender-Writer schreibt jetzt `hours:7.7,tage:1` (war 0). from_date/to_date kanonisch (Sebastian Option 1). |
| **v3.9.104** | **A1 urlaub_edit** Permission: neuer Key in `PERMS_DESC` (auto-Checkbox), `AbsView.isAdmin` = admin/PL ODER `hasPerm('urlaub_edit')` → gated Bearbeiten/Genehmigen/Alle-MA-Sicht; ohne Recht read-only. Nicht an Rolle gekoppelt. |
| **v3.9.105** | **A3 defects** Doppelfelder: Kanonisch `prio/images/zugewiesen/frist` per Code-Kommentar markiert (Reader via `_mapDefect` schon vereinheitligt). |
| (edge) | **A4** `admin-create-user/index.ts`: call-breaking `created`-Spalte entfernt + `.or()`→`.eq()` + `vorname`. **B1** `supplier-sync/index.ts` (NEU): Creds server-seitig (service_role), Client liest username/password nie mehr. **Deploy = Sebastian.** |

## ✓ VERIFIZIERT (Agent-Audit, keine Regression)
- Auth-Robustheit, 3 Crash-Fixes, hours-Fix, urlaub_edit-Gating — alle clean (Regression-Agent: Hook-Order ChartBox/WerkzeugView OK, kein Over-Grant bei isAdmin-Redefine, kein Refresh-Loop).
- **A6**: Werkzeug-Kalib Null-Guard (`_isValidKalibDate`, 298→~4 = DB-Daten nicht Code) + Fuhrpark Rollen-Gate — beide present & correct (statisch).

## 🔴 OFFEN — SERVICE-ROLE / DEPLOY (Chat-Claude/Sebastian im SQL-Editor; CC kann das NICHT)
> Grund: Supabase Service-Role/SQL-Editor ist in CC nicht erreichbar (Classifier blockt). Ausführung + Smoke (barger-Token) durch Chat-Claude.

| # | Datei | Aktion / Befehl |
|---|---|---|
| C1 | `sql/migrate_absences_repair_v3998.sql` (+`_ROLLBACK`) | Daten-Migration der 30 Altlast-absences: worker_id NAME→wX, hours/tage (7,7h/Tag), worker_name. **SQL-Editor, Snapshot + VERIFY vor COMMIT.** Erwartungswerte-Query im ROLLBACK-File. |
| C2 | `sql/migrate_urlaub_edit_rls_v3111.sql` (+`_ROLLBACK`) | **urlaub_edit serverseitig** (Chat-Claude-Befund: barger umgeht UI-Gating per API!). `can_edit_urlaub()` prüft role + perms_override + permissions-Array. **FIX angewandt:** `active` int-safe (vorher `active AND` = Lockout-Bug). |
| C-def | `sql/migrate_defects_consolidate_v3112.sql` (+`_ROLLBACK`) | defects Doppelfeld-Daten konsolidieren. **Existenz-geguarded** — Spalten priority/fotos/worker/assignee/deadline evtl. nicht vorhanden; Header-Query zuerst laufen lassen. |
| C-rls | v3103–v3110 (8 RLS-Hardening) | **2 Fixes angewandt:** v3107 + v3110 hatten `CREATE POLICY IF NOT EXISTS` (KEIN gültiges PostgreSQL → Script-Abbruch) → auf `DROP IF EXISTS;CREATE` umgestellt. Apply-Reihenfolge wie HANDOFF v3.9.101. |
| C3 | Edge-Functions | `npx supabase functions deploy admin-create-user` + `... deploy supplier-sync` (Projekt jiggujpruejkaomgxarp). Danach Client-Patch B-E (Z7321-ff auf Edge-Fn) — Code-Teil offen. |

## ⚠️ FÜR SEBASTIAN ZU BESTÄTIGEN (payroll-sensibel)
- **absences hours = 7,7h/Tag (flat) vs `stdVonTag(d)` (8,5/4,5/0 nach Wochentag)**: der Writer nutzt jetzt flat 7,7 (deine Entscheidung), die optimistische Lokal-State-Zeile nutzt `stdVonTag`. Bei Vollzeit-5-Tage identisch in Summe (38,5h), aber Einzeltag weicht ab. Klären ob Urlaub am Ø-Tagessatz (7,7) ODER Ist-Tagesstunden gebucht wird; ggf. Writer + Migration angleichen.
- **C2 vor C1**: erst absences-Daten migrieren (C1), dann RLS (C2) — sonst rechnet/sichert ZA-Editing auf kaputten Daten.

## 📋 NOCH OFFEN (Code, nächste Session)
- **ZA-Korrektur-Eingabefeld** im Urlaub-Bearbeiten-Modus (A1 Teil 4) — bewusst zurückgestellt bis C1-Migration live (sonst Korrektur auf hours=0-Daten).
- **B-E Client-Patch** (Sprint 83): Z7321-ff auf Edge-Function `admin-create-user` umstellen (Edge-Code ist fertig + gefixt, nur Client-Aufruf + Deploy fehlen).
- **supplier-sync Sync-Body**: DATANORM/IDS-Download aus Dashboard-`sync_supplier` portieren (TODO im File).

## First-read nächste Session
`docs/handoff/HANDOFF-v3.9.105.md` (dieses File) → dann `git log --oneline` ab `ef9e4fb`.
