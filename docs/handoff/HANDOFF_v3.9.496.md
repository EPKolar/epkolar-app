# EPKolar — Übergabe v3.9.496 (22.06.2026)

**Live auf origin/main + GitHub Pages.** HEAD `6e8ed9d` (v3.9.496 Fix-A-Erweiterung forms+defects). Working-Tree clean. Working-Copy: `\\srvdc02\Projekte\…\epkolar-app` (siehe `CLAUDE.md` für Pfad-Mapping pro PC).

## Diese Session — gepusht auf main (alle live, Triade grün)

| Version | Commit | Inhalt |
|---|---|---|
| v3.9.485 | `9450942` | Wochenplanung Tag-Kopieren — 📋 Spalten-Header + STRG+C/V + Multi-Paste |
| v3.9.486 | `470cade` | WP-Auswahl-Popup Smart-Positioning (klappt nach oben wenn unten kein Platz) |
| v3.9.487 | `2d2bd8f` | WP-Picker Opazität — V.bg → V.cd, stärkerer Shadow |
| v3.9.488 | `a1617e7` | WP Zellen-Kopieren via Tages-Chips im Picker |
| v3.9.489 | `4c960e4` | Chef-Portal Überfällig-Kachel Deep-Link bei 1 Treffer / Filter bei >1 (`window.__asOpenId`) |
| v3.9.490 | `d3f8b0e` | WP Bug-Hunt-Fixes — Drag-vs-Header-Hover-Conflict + Picker-Resize/Scroll-Tracking |
| v3.9.491 | `593727e` | Fix-A-Erweiterung — Server-Pull-Merge für entries + arbeitsscheine (analog v3.9.349) |
| v3.9.492 | `dda8105` | Dashboard Phantom-Urlaubsantrag — `pendingAbs` filtert Datum + stale Approvals |
| v3.9.493 | `2a3f1e1` | Urlaubs-Notif Massenversand-Fix — approve/reject nur an Antragsteller |
| v3.9.494 | `2cbbf91` | WP-Kopier-Bugfixes — (A) Tag-Kopieren leere Quelle skippen; (B) Zellen-Chip Source aus prev |
| v3.9.495 | `77aef06` | Wochenplanung „📋 Vorwoche"-Button (komplette Übernahme inkl. MA+FZ) |
| v3.9.496 | `6e8ed9d` | Fix-A-Erweiterung forms+defects (Merge statt Voll-Overwrite, analog v3.9.491) + `CLAUDE.md` |

## Live-Test-Befunde dieser Session (Playwright als admin)

| # | Test | Ergebnis |
|---|---|---|
| 1 | weekplans Multi-Device-Sync | ✅ implizit verifiziert — `wpHistory` hat 10 cross-KW-Keys aus Supabase |
| 2 | „📋 Vorwoche"-Button | ✅ Confirm-Modal greift bei nicht-leerem Ziel + Empty-Source-Toast bei leerer Quelle |
| 3 | Zellen-Kopier-Chips | ✅ Mo→Sa kopiert exakt, Picker bleibt offen, Cleanup OK |
| 4 | Forms/Defects Merge (v3.9.496) | ⏭ nicht testbar ohne Offline-Setup (SQ leer); Code-Inspektion OK |

## Offene Punkte — pro Kategorie

### A) Autonom abgearbeitet, kein Fix nötig (verifiziert)

| Task | Befund |
|---|---|
| Modal-Round-5 Logout/saveAs Refactor | 4 native `confirm()`-Stellen (`logout` Z.6124 ×2, `saveAs` Dup-Check Z.7043, `doJuprowaPushAll/doSinglePush` Z.6864/6865). Alle stilistisch — kein race, kein Datenverlust. Juprowa-Stellen HART nicht anfassen. |
| supplier-sync Stub-Cleanup | `index.html` grep returnt 0 Frontend-Referenzen. Edge-Function `supabase/functions/supplier-sync/index.ts` existiert eigenständig deployed. Kein toter Stub. |
| `weekplans` Server-Load Hardening | `_sbGet("weekplans")` macht `select=*` automatisch (Z.1892), `wp.data` ist im Response. `ODB.save("meta", wpH)` Key-konfliktfrei (parallel mit `lastUser`/`offlinePwHash`/`notifPrefs`). Kein Fix nötig. |
| Fix-B Pre-Wipe-Drain-Guard | Bereits seit v3.9.352 implementiert (Z.17546-17561): Drain-Loop bis 10s Deadline + explizite Warnung. |
| B034 (`tickets.page` Spalte) | Spalte existiert bereits laut STAND-2026-06-18-BACKLOG-DONE.md Block 3. Kein SQL-Staging nötig. |

### B) Wartet auf Sebastian — DB-Gate (manueller SQL-Run nötig)

| Task | Quelle | Aktion |
|---|---|---|
| **RLS Welle 1 Phase 2 (Blöcke 1.0a, 1.3, 1.4, 1.6, 1.7, 1.8)** | `sql/RLS_WELLE_1_READY_v5.sql` (v4 + v3 sind DEPRECATED) | v5 fixt zwei aufeinanderfolgende Bugs: (1) Spalten-Mismatches aus v3 (`wp.worker_id`, `forms.project_id`, `bautagebuch.project_id`); (2) DROP-Loop-Filter v3/v4 droppte nur `qual='true'`, NICHT die realen offenen Policies mit `qual=(auth.role()='authenticated'::text)` → Härtung war wirkungslos. v5 erweitert Filter um `auth.role()`-Pattern + neuer Block **1.0a Repair** für fahrzeuge/time_entries (die nominell seit 12.06. „applied" sind aber wegen Filter-Bug daneben offene Policies stehen haben). Block 1.5 fz_schaeden entfällt (Tabelle gedroppt). Blöcke 1.7/1.8 brauchen weiterhin information_schema-Pre-Check. Rollback-Snapshot `_rls_snapshot_v3923` ist idempotent angelegt. |
| Riedmann-Monteur-Tankung RLS-Beweis | wartet auf Live-Setup (Live-Gerät / Live-User) | — |

### C) Wartet auf Sebastian — CLI/Deploy

| Task | Befehl | Notiz |
|---|---|---|
| **sync_supplier v3 Deploy** | `npx supabase functions deploy sync_supplier --no-verify-jwt --project-ref jiggujpruejkaomgxarp` | AUS `C:\temp\epkfn` — NIE aus Z:/T:/UNC (CLI verträgt das nicht). Source-Lage laut alter Übergabe unklar; siehe `sql/DEPLOY_sync_supplier_v3.md`. Live-Function läuft, Frontend ruft sie nicht. Optional. |

### D) Wartet auf externen Input

| Task | Input | Quelle |
|---|---|---|
| **Rotes SERVER-Banner mobil** | Sebastians Beobachtung an einem Test-Handy | Visual-QA |

### E) Bewusst deferred / als P3 verworfen

- `addItem` NaN-Maskierung (Material) — `parseFloat()||1`-Fallback greift, kein echter Bug (Welle 2 verworfen).
- `delWzPhoto canDo`-Inkonsistenz — `isVAdmin`-Hard-Check vorhanden, nur stilistisch (Welle 2 verworfen).
- Bug-Hunt-Findings P3 aus Welle 1/3 (viewport-resize-tracking P2 ist via v3.9.490 schon gefixt; rest theoretische Edge-Cases).

## Diese Session — bereits erledigt (auch außerhalb des Code)

- **9 stale `absence_approval`-Notifs in Prod-DB gelöscht** — Sebastian hat die in `v3.9.493` aufgelistete `DELETE FROM notifications WHERE id IN (...)`-Anweisung im Supabase-SQL-Editor ausgeführt (DELETE 9 Success). Damit ist die Folge des Pre-v3.9.493-Massenversands aus dem System raus; v3.9.493-Code-Fix verhindert die Wieder-Entstehung.
- **ocr_tankbeleg Datum-Parser DONE** — Sebastian hat live mit echtem Beleg gescannt und verifiziert.

## Nächste konkrete Schritte für Sebastian

1. **Smoke-Test der WP-Kopier-Features (v3.9.485-488, v3.9.494, v3.9.495)** auf echtem Gerät — Tag-Kopieren-Header (📋/✂️), Zellen-Chips im Picker, „📋 Vorwoche"-Header-Button.
2. **Smoke-Test der Cross-Device-Sync-Hardening (v3.9.491, v3.9.496)** — entries/arbeitsscheine/forms/defects offline anlegen → online → andere Geräte sollten keine Phantom-Verluste mehr sehen.
3. **RLS Welle 1 Phase 2** ausführen via `sql/RLS_WELLE_1_READY_v5.sql` (v3 + v4 deprecated; v4 hatte zusätzlich zum Spalten-Mismatch noch einen DROP-Loop-Filter-Bug der die Härtung wirkungslos gemacht hätte). v5 enthält neuen **Block 1.0a Repair** der für fahrzeuge/time_entries die in v3 offen-gebliebenen `auth.role()`-Policies daneben entfernt — pflicht zuerst applien. Block 1.5 fz_schaeden entfällt. Blöcke 1.7/1.8 vor Apply nochmal kurz mit information_schema-Pre-Check verifizieren. Rollback-Snapshot `_rls_snapshot_v3923` ist idempotent angelegt.

## HART NICHT ANFASSEN (unverändert)

- `_juprowaPush` / `_juprowaPull` / Juprowa Phase-1+2 (inkl. `doJuprowaPushAll`/`doSinglePush` Z.6864/6865 mit native `confirm()`)
- `parseTankBeleg` / `addTank` / Tank-Kontroll-Dialog / km-Sperre
- `_RLS_SILENT_DENIAL_LABELS`
- DB-Direktive `jiggujpruejkaomgxarp` — CC fasst DB NIE direkt an (Plugin-Org-Mismatch). SQ.push-Operationen durch die App selbst sind OK (normale Offline-Queue).
- Diagnose-Aufträge bleiben strikt read-only.

## Validierungs-Triade vor jedem Push

```
cd /d "Z:\05_Claude\02_Baumanagment & Zeiterfassungs - APP\03_Repos\epkolar-app"
git rev-parse --show-toplevel   # //srvdc02/Projekte/.../epkolar-app
python scripts/node_check.py index.html
python scripts/_bracket_check.py index.html   # Baseline () -1, {} 0, [] 0
node sql/_check_version.js                     # ✓ versions synced
python -m pytest tests/ -q                     # 993 grün
```

Push-Weg: `git push origin main` (KEIN `gh`). Remote-Verify per `curl raw.githubusercontent.com/EPKolar/epkolar-app/main/sw.js` nach jedem Push.
