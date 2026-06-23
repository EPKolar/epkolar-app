# EPKolar — Übergabe v3.9.508 (22.06.2026, Context-Wechsel)

**Live auf origin/main + GitHub Pages.** HEAD `11a5e96` (v3.9.508). Working-Tree clean. Working-Copy `\\srvdc02\Projekte\…\epkolar-app` (siehe `CLAUDE.md` für Pfad-Mapping pro PC).

## Diese Session — gepusht (v3.9.485 → v3.9.508, 23 Versionen + 4 Doc/SQL/Test-Commits)

### Wochenplanung-Features
| Version | Inhalt |
|---|---|
| v3.9.485 | WP Tag-Kopieren (📋-Icon im Spalten-Header, STRG+C/V, Multi-Paste) |
| v3.9.486 | WP-Picker Smart-Positioning (öffnet nach oben wenn unten kein Platz) |
| v3.9.487 | WP-Picker Opazität (V.cd statt V.bg, stärkerer Shadow) |
| v3.9.488 | WP Zellen-Kopieren via Tages-Chips im Picker |
| v3.9.494 | WP-Kopier-Bugfixes (P1): leere Quelle skippen, Chip Source aus prev |
| v3.9.495 | WP „📋 Vorwoche"-Button — komplette KW-Übernahme inkl. MA+FZ |

### Chef-Portal / Notif
| Version | Inhalt |
|---|---|
| v3.9.489 | Chef-Portal Überfällig-Kachel Deep-Link (1 AS → Edit direkt, >1 → gefilterte Liste) |
| v3.9.490 | WP Bug-Hunt-Fixes (Drag-vs-Header-Hover-Conflict + Picker-Resize/Scroll-Tracking) |
| v3.9.492 | Dashboard Phantom-Urlaubsantrag — pendingAbs filtert Datum + stale Approvals |
| v3.9.493 | Urlaubs-Notif Massenversand-Fix — approve/reject nur an Antragsteller |
| v3.9.497 | Alert-Detail-Panel Sichtbarkeit (Background, Shadow, Akzent-Border) |

### Cross-Device-Sync (KRITISCH)
| Version | Inhalt |
|---|---|
| v3.9.491 | Fix-A-Erweiterung entries + arbeitsscheine (Merge statt Voll-Overwrite, analog v3.9.349 für tickets/plans) |
| v3.9.496 | Fix-A-Erweiterung forms + defects (analog v3.9.491) + CLAUDE.md |
| **v3.9.500** | **Wochenplanung Zeilen-Level-Storage (`weekplan_rows`)** — neue Tabelle, Diff-Save, Polling 30s, Conflict-Schutz |
| v3.9.501 | WP Offline-Race-Schutz — `__wpPendingRowIds`, Offline-Skip, doSync-Drain-Hook |
| **v3.9.502** | **KRITISCH-FIX `weekplan_rows.z` JSONB-Doppel-Serialisierung** (`JSON.stringify(r.z)` → `_safeJsonParse(r.z,{})`) |

### Mobile-Optimierung (v3.9.503-508)
| Version | Inhalt |
|---|---|
| v3.9.503 | WP-Planung Mobile (<600px) — Tages-Karten-Ansicht + selDay-State |
| v3.9.504 | MA-Übersicht Mobile — selDay-Tabs + MA-Cards (Rolle-Badge, BVH-Chips, ⚠️) |
| v3.9.505 | Spezialfahrzeuge-Übersicht Mobile — Card-Liste pro selDay |
| v3.9.506 | WP-Footer Mobile (Excel/PDF 50/50 Grid + Counter eigene Zeile) |
| v3.9.507 | WP-Header KW-Nav Mobile (◀/▶/savedKws Tap-Targets ≥36px) |
| v3.9.508 | VBautag Mobile (Form-Actions column, Card-Header column, Edit/Delete-Labels) |

### Tests + Docs
| Commit | Inhalt |
|---|---|
| `7582e5e` | v3.9.502 Regression-Tests T-WP-502-A/B/C (statische pytest gegen index.html) |
| `a3fadeb` | `sql/WEEKPLAN_MIGRATE_v1.sql` sort_order × 10 nachgereicht |
| `4d99898` + `73e83bc` | `docs/handoff/HANDOFF_v3.9.496.md` |
| RLS-Iterations | v3 → v4 → v5 → **v6** (`sql/RLS_WELLE_1_READY_v6.sql`) — Pattern-Drop, idempotent, anmeldungen-Conditional, Snapshot-Dedup |

## DB-Migrationen offen (Human-Run-Gate, NICHT von CC ausgeführt)

| File | Status | Aktion |
|---|---|---|
| `sql/WEEKPLAN_ROWS_v1.sql` | **PFLICHT vor v3.9.500-Live-Nutzung** | Tabelle `weekplan_rows` + RLS + Trigger anlegen |
| `sql/WEEKPLAN_MIGRATE_v1.sql` | nach `WEEKPLAN_ROWS_v1` | jsonb_array_elements → row-Tabelle, `sort_order=(ord-1)*10`, Padding-Skip |
| `sql/RLS_WELLE_1_READY_v6.sql` | optional, Phase 2 RLS-Härtung | Blöcke 1.1/1.2 idempotent re-apply + 1.3/1.4/1.6/1.7-conditional/1.8 |

**Kein Cleanup der alten `weekplans`-Tabelle** bis Live-Konkurrenz-Test grün. Alte JSON-Blobs bleiben Backup.

## Offene Mobile-Refactors (nicht abgeschlossen)

| Kandidat | Größe | Status |
|---|---|---|
| **VMaterial Mobile** | groß (700+ Z., mehrere Tabs) | offen — gezielter Auftrag empfohlen |
| **VBueroExport BWB-Inline-Vorschau Mobile** | mittel-groß (Matrix-Refactor) | offen |
| **AS-Detail-Edit-Form Mobile** | sehr groß (hunderte Felder) | offen |
| **WP-View-Switcher Mobile** | klein (Z.16170) | als nächster kleiner Touch geeignet |

## Konflikt-Dialog (Teil 2 aus v3.9.501-Analyse)

Vergleichs-Dialog für Multi-User-Race (lokale Edit vs. fremde Server-Edit). **Nicht umgesetzt.** Analyse + Aufwand-Schätzung in `HANDOFF_v3.9.496.md` (300-370 Zeilen für Modal + Detect-Pfad). Wenn priorisiert: v3.9.502 (gezielt) als eigene Session.

## Backlog (unverändert / Pre-Existing)

- Modal-Round-5 native `confirm()` (logout Z.6124, saveAs Z.7043) — Status-quo Tradeoff, kein echter Bug
- `pytest tests/` zeigt **2 Pre-Existing-Failures** (nicht v3.9.502-verursacht):
  - `test_invariants.py::test_bracket_baseline` (erwartet 0, Baseline ist seit Sessions `()` -1)
  - `test_wp_keying_0h_v3482.py::test_wphistory_load_keys_with_year` (Pattern wurde von v3.9.500 Refactor verschoben)
- **995 passed** im Rest

## Triade-Stand

- `node_check.py` exit 0 ✓
- `_bracket_check.py`: `()` -1, `{}` 0, `[]` 0 (Baseline unverändert seit Session-Start)
- `_check_version.js`: APP_VERSION + SW_VER + CACHE_NAME alle 3.9.508 ✓

## HART NICHT ANFASSEN (unverändert)

- `_juprowaPush` / `_juprowaPull` / Juprowa Phase-1+2
- `parseTankBeleg` / `addTank` / Tank-Kontroll-Dialog / km-Sperre
- `_RLS_SILENT_DENIAL_LABELS`
- DB-Direktive `jiggujpruejkaomgxarp` HART — CC fasst DB NIE direkt an (SQL-Editor durch Sebastian)
- Diagnose-Aufträge bleiben strikt read-only

## Nächste konkrete Schritte für Sebastian

1. **PFLICHT vor Live-Multi-User-Nutzung der WP-v3.9.500-Architektur:**
   - `sql/WEEKPLAN_ROWS_v1.sql` apply (Tabelle anlegen)
   - `sql/WEEKPLAN_MIGRATE_v1.sql` apply (Blobs → Zeilen migrieren)
   - Verify: Row-Count vorher/nachher, Sample-Inspect, Konkurrenz-Test 2 Geräte

2. **Optional:** `sql/RLS_WELLE_1_READY_v6.sql` apply (Phase 2 Härtung).

3. **Nächste Mobile-Session:** wähle Kandidat aus „Offene Mobile-Refactors". Empfehlung: **WP-View-Switcher** als nächster kleiner Touch (5-Min-Task), dann eine gezielte Session für VMaterial / BWB / AS-Form.

4. **9 stale `absence_approval`-Notifs Cleanup** ist bereits erledigt (Sebastian SQL-Run in dieser Session bestätigt).

## Resume-Befehl für die nächste Session

```
claude -p "EPKolar — neue Session. Pfad: Z:\05_Claude\02_Baumanagment & Zeiterfassungs - APP\03_Repos\epkolar-app
(per-PC-Mapping siehe CLAUDE.md; auf Sebastian-Desktop T:).

=== STAND ===
Live: v3.9.508-supabase auf origin/main + GitHub Pages. HEAD 11a5e96. Working-Tree clean.

Lies ZUERST docs/handoff/HANDOFF_v3.9.508.md — komplette Übergabe-Doku der letzten Session.

=== HARTE REGELN ===
- KEINE selbst-initiierten Fixes ohne expliziten Auftrag. Diagnose-Aufträge sind READ-ONLY.
- CC fasst DB NIE direkt an (DB-Direktive jiggujpruejkaomgxarp).
- _juprowaPush / Tank-Flow / RLS_SILENT_DENIAL_LABELS / v3.9.306-324 nicht anfassen.
- Triade vor Push: node_check exit 0, pytest 995+ grün (2 Pre-Existing-Failures bekannt),
  _check_version.js synced. Bracket-Baseline () -1 unverändert.
- Working-Tree-Verify via git rev-parse --show-toplevel (= //srvdc02/Projekte/...).
- Edge-Deploys NUR aus C:\temp\epkfn.
- Push: git push origin main (KEIN gh). Remote-Verify per curl raw.githubusercontent.com.

=== AUFGABE ===
[Sebastian füllt hier den konkreten Auftrag ein — z.B. 'WP-View-Switcher Mobile',
'VMaterial Mobile-Refactor', 'BWB-Inline-Vorschau Mobile', 'Konflikt-Dialog v3.9.502',
oder 'SQL Human-Run-Gate für WEEKPLAN_ROWS_v1 + MIGRATE_v1 betreuen + Live-Verify'.]
" --allow-dangerously-skip-permissions --output-format stream-json --verbose
```
