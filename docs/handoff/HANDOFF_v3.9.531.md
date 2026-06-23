# EPKolar — Übergabe v3.9.531 (23.06.2026)

**Live auf origin/main + GitHub Pages.** HEAD `d317e05` (v3.9.531). Working-Copy `\\srvdc02\Projekte\…\epkolar-app` (per-PC-Mapping siehe `CLAUDE.md`; auf diesem PC **Z:**, Sebastian-Desktop T:). Working-Tree clean, 0 ahead/behind.

**Supabase-MCP-Plugin ist in der Session verbunden** (OAuth, Projekt `jiggujpruejkaomgxarp` = „Baumanagement & Zeiterfassung", eu-west-2). DDL/DML lief autorisiert über `execute_sql`/Policies. Triade-Befehle: siehe `CLAUDE.md` (node_check, _bracket_check `() -1`, _check_version, pytest **997 grün**).

---

## Diese Session (23.06.2026) — v3.9.518 → v3.9.531 + DB/Storage

> v3.9.517 wurde übersprungen (die Test-Fixes gehörten zu v3.9.516).

### Frontend-Versionen
| Version | Inhalt |
|---|---|
| v3.9.518 | Alert-Detail-Panel Redesign (Home) — Status-aware Zeilen (overdue=rot/⚠, warn=orange), Kennzeichen fett + Modell-Sublabel, Datum als Status-Pill, Detail-Link als Button. Details abwärtskompatibel String\|Objekt. |
| v3.9.519 | Planungs-Excel: **Krankenstand- + Urlaub-Zeile** unter den Baustellen (read-only aus `abs`; `abs` neu als WeekPlan-Prop). |
| v3.9.520 | Excel höhere Datenzeilen (Wochenplanung + MA-Übersicht) via neuem `genXls`-Opt `rowHeight:34` (default 20). |
| v3.9.521 | **Abwesenheiten-Übersicht** (Krankenstand/Urlaub) direkt in der Wochenplanung — Desktop 7-Spalten-Tabelle + Mobile selDay-Card, blendet aus wenn KW leer. |
| v3.9.522 | Bug-Fix: Material-Notif blieb nach erledigter Bestellung — `_checkAutoNotifs` entfernt jetzt erledigte `material_order`/-`eskalation`-Notifs (Name-Match, Open-Order-Guard). |
| v3.9.523 | Planungs-Streifen (Abwesenheiten + SpezFz) **fluchten** mit Tabelle/Wetter — Desktop-Branches auf Wetter-Flex-Grid (28px+16%+6×12%+8%+44px, minWidth:800). `test_subpage_mobile_tables` an neue Flex-Implementierung angepasst. |
| v3.9.524 | Team-Kachel **flex statt grid** — Karten wachsen/füllen Reihen, größere Karten. |
| v3.9.525 | Team-Kachel Icon-Logik — Fallback rollen-/personenabhängig: Geschäftsführer 👔, Mitarbeiterinnen (id w7/w8) 👩, sonst 👷. |
| v3.9.526 | Team-Kachel Chef-Icon 👔 → **👨‍💼**. |
| v3.9.527 | Auswertungen: **Auftragsvolumen nur Büro/Admin/PL** (`_canSeeVolume=role∈{admin,projektleiter,buero}`) — KPI gesamt + Sektion „nach Geschäftsjahr" + Excel-Zeilen gegated; Monteure/Obermonteur sehen es nicht. |
| v3.9.528 | **Tankbeleg-km robust** aus OCR-`rawText` (KILOMETERSTAND-Zeile) via Helper `_kmFromBeleg(raw,curKm)` statt kaputtem `_j.km` + Plausi (>= Tacho, kein Rückwärts/Sprung). Edge-Function unverändert. |
| v3.9.529 | **tank_log Einträge: `id` + `kontrolliert`/`kontrolliert_von`/`kontrolliert_am`** (Fundament Beleg-Kontrolle). Frontend: addTank/qDoTank/batchSave + DB-Backfill (6 Einträge). |
| v3.9.530 | CSS: horizontale Scrollbars ausblenden (`::-webkit-scrollbar height:0`), vertikale bleibt 5px. |
| v3.9.531 | Arbeitsschein-Nr.: **dauerhaftes ⟳ (Juprowa-Marker) entfernt** (Mobile-Karte + Desktop-Tabelle, war 2×); Push-Pfeil ↑ bleibt. |

### DB / Storage (autorisiert, Supabase-Plugin)
- **Fahrzeug TU-707DR (Renault Clio) angelegt** als Kopie von fz9/TU-751DR (id `mqclio0707dr`, Fahrer w5, km 175.965, Rot, status aktiv). `zulassungsschein` auf `''` normalisiert (war `'[]'`). Live in App verifiziert (Playwright).
- **tank_log Backfill**: alle bestehenden Einträge haben jetzt `id` + `kontrolliert`-Felder (eintraege_ohne_id/-kontrolliert = 0).
- **Storage-Policies** (idempotent, snake_case): `auth_fahrzeuge_files_ins` (INSERT) + `auth_fahrzeuge_files_upd` (UPDATE) auf `storage.objects` → `authenticated` darf unter `epkolar-files/fahrzeuge/` schreiben/aktualisieren. **Kein Service-Key nötig** für Tankfoto-Uploads/Migration.
- Backups (im Repo, OHNE Service-Keys): `docs/db/tank-log-backup-2026-06-23.json`, `docs/db/tank-kontroll-backup-2026-06-23.json` (enthalten Base64 — über Tages-Backup gesichert).

---

## OFFEN / wartet auf Kommando

1. **Planungs-Excel in festen Ordner** (File System Access API) — **STOPP-Befund**: Die Wochenplanungs-Excel (Z.16079) läuft über das **geteilte `genXls`/`_dl`** (keine eigene Blob-Stelle). Vorschlag: opt-in-Flag `opts.planDir` in `genXls`, nur der Wochenplanungs-Aufruf setzt es → andere Exporte unverändert. Helfer-Set (`_plPick/_plSave/_plLoad/_plPerm/_plWriteToDir` via IndexedDB-Handle) + „📁 Ordner"-Button. **Wartet auf „go opt-flag".**
2. **Tankfoto-Migration Base64 → Storage** (`epkolar-files/fahrzeuge/<fzId>/tank/<eid>.jpg`, public). Policy ist live → **kein Service-Key**. Läuft über die authentifizierte Browser-Session: Test-Upload (Precondition) → Dry-Run (STOPP) → `--go` (Upload + URL-Verify + `tank_log`-Rewrite, idempotent: `http`-foto übersprungen) → Verify (Base64-foto = 0). Foto-Anzeige (`<img src>`) unverändert. `C:\temp\epkmig` (Service-Key-Variante) ist **obsolet**.
3. **Tank Teil 2 — Kennzeichen aus rawText** (Recon erledigt): Schnell-Pfad ist Fahrzeug-zuerst ohne Foto/OCR; Dialog-Pfad hat OCR aber fixes Fahrzeug (`sel`, addTank(sel) Z.20875). Optionen: (a) Mismatch-Warnung bei abweichendem Kennzeichen, (b) neuer Foto-zuerst-Einstieg mit Picker. **Wartet auf Richtungsentscheid.**

## Backlog (älter, unverändert)
- **B034**: `tickets.page`-Spalte (`ALTER TABLE tickets ADD COLUMN page integer DEFAULT 1;`).
- `sync_supplier v3` deploy aus `C:\temp\epkfn`; supplier-sync Stub-Cleanup.
- WEEKPLAN_ROWS_v1 / MIGRATE_v1 / RLS_WELLE_1_v6 (siehe HANDOFF_v3.9.516.md) falls noch offen.

## Test-Stand
- pytest **997 passed, 0 FAILED** (die 2 früheren Pre-Existing-Failures sind seit v3.9.516 gefixt; `test_subpage_mobile_tables` in v3.9.523 an Flex-Grid angepasst).
- Bracket-Baseline (Whole-File-Count) stabil **`() -5, {} 0, [] 0`** über alle Versionen; offizielles `_bracket_check.py` zeigt `() -1`.

## HART NICHT ANFASSEN (unverändert)
- `_juprowaPush`/`_juprowaPull`/Juprowa Phase-1+2; `parseTankBeleg`-OCR-Edge-Function nur Frontend-seitig angebunden (Function selbst unverändert).
- DB-Direktzugriff nur autorisiert über Supabase-Plugin mit explizitem Sebastian-OK; sonst SQL-Editor/Human-Run-Gate.

## Resume-Befehl
```
claude -p "EPKolar — neue Session. Pfad: Z:\05_Claude\02_Baumanagment & Zeiterfassungs - APP\03_Repos\epkolar-app
Live: v3.9.531-supabase. HEAD d317e05. Working-Tree clean.
Lies ZUERST docs/handoff/HANDOFF_v3.9.531.md — komplette Übergabe (v3.9.518–531 + DB/Storage + offene Punkte)."
```
