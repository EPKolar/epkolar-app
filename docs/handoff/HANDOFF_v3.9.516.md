# EPKolar — Übergabe v3.9.516 (23.06.2026)

**Live auf origin/main + GitHub Pages.** HEAD `1c9c6d7` (v3.9.516). Working-Copy `\\srvdc02\Projekte\…\epkolar-app` (per-PC-Mapping siehe `CLAUDE.md`; auf diesem PC **Z:**, auf Sebastian-Desktop T:).

> **Hinweis Push-Stand:** v3.9.509–515 sind gepusht (`11a5e96..c3652bc`). **v3.9.516 (Excel-Druck-Kontrast) ist committed, aber Push-Stand bei Übergabe prüfen** (`git rev-list --left-right --count origin/main...HEAD`).

---

## Diese Session (23.06.2026) — Mobile-Tap-Target-Welle + Excel-Druck-Fix

Fortsetzung der Mobile-Optimierung aus v3.9.503–508. **Leitprinzip durchgehend: jeder Fix `isMob?neu:original`** (bzw. `window.innerWidth<600` wo kein `ww`/`isMob`-Prop verfügbar) → **Desktop byte-identisch**. Pro Version: `node --check` des größten Script-Blocks ✓ + 3× Versions-Konsistenz (APP_VERSION / SW_VER / CACHE_NAME) ✓.

### Mobile Tap-Targets (v3.9.509–515)

| Version | View | Inhalt |
|---|---|---|
| v3.9.509 | Overlay-Panels | Benachrichtigungs-/Foto-Warteschlangen-/Sync-Panel: Close-✕ (40px), 🗑️Alle-löschen/✅Alle-gelesen/🔄Sync (36px), Sync-Mode-Select (38px), Kategorie-Filter-Pills (34px), Per-Eintrag-/Per-Foto-Löschen (32px), 📷Aufnehmen/🔄Jetzt-senden (38px) |
| v3.9.510 | Arbeitsscheine-Kalender | Zeitraum-Nav ◀▶ (40px), Heute (38px), Tag/Woche/Monat-View-Tabs (40px), Such-Clear-✕. AS-**Listen**-Karten waren schon mobil (v3.9.39) |
| v3.9.511 | Zeiterfassung | KW-Nav ◀▶/Heute (38px), Monteur-Filter-Pills (36px), Per-Eintrag ✏️/✕ (inline-flex + 30px). Week-Summary/Day-Columns bleiben bewusst horizontal-scrollbar |
| v3.9.512 | Datenblatt-Ordner & Signatur | Datenblatt-Archiv Ordner-Buttons ✏️/🗑️ (40px), SignaturePad ✕-Löschen (36px, via `window.innerWidth<600` — Component ohne `ww`-Prop) |
| v3.9.513 | Urlaub/Abwesenheit (AbsView) | Genehmigungs-Core-Actions ✅Alle-genehmigen/❌Alle-ablehnen (40px), Einzel-Approve/Reject ✅❌ (40px), Edit ✎/🗑️ (40px), Kontingent ▼Details/✏️Bearbeiten (38px) |
| v3.9.514 | Chef-Portal (ChefDashboard, `isMob=ww<700`) | Zentraler `_drill`-Helper → **alle** „Label →"-Nav-Buttons (40px); Handlungsbedarf-Grid-Boxen (AS-ohne-Monteur/-Termin, Push-Stau, Monatsabrechnung) auf 44px |
| v3.9.515 | Urlaubskontingent-Tabelle | `minWidth:760` ergänzt → sauberer Horizontal-Scroll statt Spalten-Crush im `overflowX:auto`-Wrapper |

### Excel-Export Druck-Kontrast (v3.9.516)

**Sebastian-Befund:** Graue Schrift im Excel-Export (MA-Übersicht + Wochenplanung) druckt schlecht. Fix im **gemeinsamen `genXls`-Helper (Z.~3863)** — betrifft damit **ALLE** Exporte (Wochenplanung, MA-Übersicht, OFFA, Zeiterfassung, Abwesenheit, Mängel, Tickets, Fuhrpark, Werkzeuge …), reine Druck-Verbesserung ohne Layout-/Logik-Regression:
1. **Datenzellen** bekommen explizit `color:#000000` (vorher kein `color` gesetzt → je nach Excel/Drucker-Theme ausgegraut/blass).
2. **Subtitle-Zeile** (KW-Range + Export-Datum) `#666` → `#1a1a1a`.
3. **Footer-Zusammenfassung** (X Einträge + Firmenzeile) `#999` → `#555`.

Header-Grün, Status-Badge-Farben (`statusMap`) und Bank-/AGB-Boilerplate (`#bbb`) bewusst **unverändert**.

---

## Bewusst NICHT umgesetzt (Explore-Funde als Fehlalarm / hands-off verifiziert)

| „Fund" | Warum übersprungen |
|---|---|
| Zeiterfassung Week-Summary `minWidth:700` | Gewollte horizontal-scrollbare Wochenleiste + `overflowX:auto`, kein Bug |
| WP-Desktop-Planungstabelle ▲▼🗑✕ (war als „Material" mislabeled) | Desktop-only Pfad (`!isMob`); Mobile-WP nutzt Tages-Karten (v3.9.503) → Session-Tabu „Desktop 100% unverändert" |
| Material-Bestellansicht | War bereits mobil (Such-Input/Clear-✕/Filter-Pills haben `minHeight:isMob?…`) |
| AS-Listen-Karten | Bereits mobil (v3.9.39, Buttons schon `minHeight:36`) |
| AbsView Typ-Filter-Pills flexWrap | `flexWrap:"wrap"` + `minHeight:36` schon vorhanden |
| ChefDashboard „Bulk-Approve Z.18937" | Phantom — Zeile ist ein useMemo-Kommentar, keine solche Aktion existiert dort |
| Fahrzeug-Schaden-Dialog-Buttons Z.20223 | Phantom — Zeile ist `reader.readAsDataURL`, kein Button |
| VBüro-Dashboard-Tabelle `minWidth:640` | Bereits `overflowX:auto` + 640; Explore-Vorschlag (700) hätte sie nur breiter gemacht |

---

## Backlog (übernommen aus HANDOFF_v3.9.508, unverändert offen)

### DB-Migrationen offen (Human-Run-Gate — CC führt DB NIE direkt aus)
| File | Status |
|---|---|
| `sql/WEEKPLAN_ROWS_v1.sql` | **PFLICHT vor v3.9.500-Live-Multi-User** — Tabelle `weekplan_rows` + RLS + Trigger |
| `sql/WEEKPLAN_MIGRATE_v1.sql` | nach ROWS_v1 — Blobs→Zeilen, `sort_order=(ord-1)*10`, Padding-Skip |
| `sql/RLS_WELLE_1_READY_v6.sql` | optional Phase-2 RLS-Härtung |
| **B034** `tickets.page` | `ALTER TABLE tickets ADD COLUMN page integer DEFAULT 1;` (Sebastian SQL-Editor) |

Kein Cleanup der alten `weekplans`-Tabelle bis Live-Konkurrenz-Test grün.

### Offene größere Mobile-Refactors (gezielte Session empfohlen)
| Kandidat | Größe |
|---|---|
| VMaterial Mobile (Detail-Tabs) | groß |
| AS-Detail-Edit-Form Mobile | sehr groß (hunderte Felder) |
| VBueroExport BWB-Inline-Vorschau Mobile | mittel-groß (Matrix-Refactor) |

### Sonstiges
- `sync_supplier v3` deploy: CLI aus `C:\temp\epkfn` (npm-UNC-Bug), `npx supabase functions deploy sync_supplier --no-verify-jwt --project-ref jiggujpruejkaomgxarp`
- supplier-sync Stub-Cleanup im Repo offen
- 2 Pre-Existing pytest-Failures (Test-Erwartung falsch, kein Code-Bug): `test_invariants::test_bracket_baseline` (erwartet 0, Baseline `()` -1), `test_wp_keying_0h_v3482` (Pattern durch v3.9.500-Refactor verschoben)
- Konflikt-Dialog Teil 2 (Multi-User-Race-Vergleich) — nicht umgesetzt, Analyse in HANDOFF_v3.9.496.md

---

## HART NICHT ANFASSEN
- `_juprowaPush`/`_juprowaPull`/Juprowa Phase-1+2
- `parseTankBeleg`/`addTank`/Tank-Kontroll-Dialog/km-Sperre
- `_RLS_SILENT_DENIAL_LABELS`
- DB `jiggujpruejkaomgxarp` — CC fasst Prod-DB NIE direkt an (SQL-Editor durch Sebastian)
- Desktop-Layouts (≥600px bzw. ≥700px im Chef-Portal) — alle Mobile-Arbeit ist breakpoint-gegated

---

## Triade-Stand (v3.9.516)
- `node --check` größter Script-Block: exit 0 ✓
- APP_VERSION + SW_VER + CACHE_NAME = `3.9.516` ✓
- Working-Tree clean (außer ggf. dieser Doku-Commit)

## Resume-Befehl nächste Session
```
claude -p "EPKolar — neue Session. Pfad: Z:\05_Claude\02_Baumanagment & Zeiterfassungs - APP\03_Repos\epkolar-app
(per-PC-Mapping siehe CLAUDE.md; auf Sebastian-Desktop T:; auf diesem PC Z:).

=== STAND ===
Live: v3.9.516-supabase. HEAD 1c9c6d7. Working-Tree clean.
Lies ZUERST docs/handoff/HANDOFF_v3.9.516.md — komplette Übergabe der letzten Session
(Mobile-Tap-Target-Welle v3.9.509–515 + Excel-Druck-Kontrast v3.9.516)."
```
