# HANDOFF v3.9.108 — 2026-06-03 (Autonomer CC-Sprint + Bug-Hunt + SQL-Hardening live)

## LIVE-STATE
- **App-Version:** v3.9.108 (war v3.9.101 zu Sprint-Beginn) — https://epkolar.github.io/epkolar-app/
- **MCP-Live-Smoke:** App bootet sauber, 0 Console-Errors, Login rendert. ✅ Schulungs-bereit.
- **SQL-Hardening LIVE** (Chat-Claude, 2026-06-03): 5 Security-Trigger + C1 absences-Migration ausgeführt + verifiziert (8/8 Logins, 7 Tabs, Händler-Sync intakt).
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
| **v3.9.106** | **B-A Payroll-Fix** (Chat-Claude verifiziert): `stdVonTag` jetzt feiertag-aware (neuer `_isATFeiertag`, Easter-berechnet). Mo-Do 8,5 / Fr 4,5 / Sa-So+Feiertag 0. Behebt Urlaub 98,5→90,0h (Pfingstmontag 25.5 zählte fälschlich mit). absences-Writer schreibt `hours:stdVonTag(d)` statt flat 7,7. |
| **v3.9.107** | **Bug-Hunt Welle 1** (5 Finder-Agenten, adversarial verifiziert, 9 Bugs): JUPROWA scheintyp `String()` (Regie→Service), AbsView-Übersicht isAdmin-Gate (MA-Salden-Leak per Swipe), Fahrzeug-Labels→visibleFz, Kontingent-Save→isAdmin, Deadline-TZ (heute≠abgelaufen), _authRetry offline-Guard, reauth-counter-reset, tog-Delete Approval-Orphan. |
| **v3.9.108** | **Urlaub-Toggle-Relabel** (Schulungs-Klarheit): 'urlaub'="Tab sehen", 'urlaub_edit'="Urlaub/Abwesenheit verwalten (bearbeiten+genehmigen)". `'urlaub'` ist Tab-Default JEDER Rolle → NICHT als Verwaltungs-Key nutzbar. + Live-Trigger-Doku. |
| **v3.9.109-112** | **Bug-Hunt-Fixes** (siehe BUG-HUNT-FINDINGS-2026-06-04.md): Urlaub-TDZ-Hotfix, JUPROWA-Prio, exportXls-Summe, Bescheinigung-Escaping, OFFA-Re-Import-Datenverlust, Approval-Bridge, Logout-Token, Übernacht-von/bis. |
| **v3.9.113** | **Mobile-Fix**: Planung KW-Sprung-Buttons flexWrap (671→385px @ 390-Viewport, live validiert). MCP-Mobile-Audit portrait+landscape: alle Tabs ohne Page-Overflow. Verbleibend (UX-Entscheidung): WeekPlan-Wochengitter (1268px) scrollt horizontal — Mobile-Redesign wäre Produktentscheidung. |
| **v3.9.114** | **⏸️ FINKZEIT AUF STANDBY** (Sebastian 04.06.2026): EIN Flag `FINKZEIT_ENABLED=false` (bei APP_VERSION) parkt 9 Frontend-Flächen: Tab Monatsabrechnung, mobile Nav, Dashboard-Fetch/Card/2-Alerts, Chef-Hinweis, Audit-Filter, Rechte-Toggle 'stunden'. Code GEPARKT nicht gelöscht (StundenzettelView/pdf_data-Handler unverändert, "FINKZEIT STANDBY"-Kommentare). DB unberührt. hasPerm('stunden') intakt. **REAKTIVIERUNG: nur `FINKZEIT_ENABLED=true` setzen — alles kommt zurück.** MCP-live-verifiziert: 14 Tabs, 0× FinkZeit/Monatsabrechnung sichtbar, 0 Crashes. |
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

## ✅ GEKLÄRT (Payroll, Sebastian + Chat-Claude 2026-06-03)
- **absences hours = `stdVonTag` KANONISCH**: Mo-Do 8,5h · Fr 4,5h · Sa/So 0 · AT/NÖ-Feiertag 0. NICHT flat 7,7. Writer (v3.9.106) + Migration C1 nutzen beide diese Logik inkl. Feiertags-Ausschluss. SOLL-Werte verifiziert (w6 Urlaub 90,0/ZA 25,5; w5 ZA 25,5/Sonder 17; w4 Urlaub 34/Kranken 17; w1 Sonder 8,5).
- **Reihenfolge: C1 (Daten) VOR C2 (RLS)** — bestätigt.

## 📋 NOCH OFFEN (Code, nächste Session)
- **ZA-Korrektur-Eingabefeld** im Urlaub-Bearbeiten-Modus (A1 Teil 4) — bewusst zurückgestellt bis C1-Migration live (sonst Korrektur auf hours=0-Daten).
- **B-E Client-Patch** (Sprint 83): Z7321-ff auf Edge-Function `admin-create-user` umstellen (Edge-Code ist fertig + gefixt, nur Client-Aufruf + Deploy fehlen).
- **supplier-sync Sync-Body**: DATANORM/IDS-Download aus Dashboard-`sync_supplier` portieren (TODO im File).

## First-read nächste Session
`docs/handoff/HANDOFF-v3.9.105.md` (dieses File) → dann `git log --oneline` ab `ef9e4fb`.
