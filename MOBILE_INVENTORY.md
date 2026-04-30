# Mobile Inventory v3.8.67

Branch: `cc-mobile-refactor/2026-04-30`  Base: `27a0040` (v3.8.66)
File: `index.html` (17193 lines, 1.75 MB)
Pytest-Baseline: **359 Tests** (9 min collect)
Bracket-Baseline: `() -2 / {} 0 / [] 0` ✅

---

## A) Bottom-Nav-Audit (Tabs & g-Properties)

### Vollständige Tab-Liste (Zeilen 4812–4829)

| # | Label | Icon | perm | g | Bucket |
|---|-------|------|------|---|--------|
| 1 | Home | 🏠 | `_home` | 0 | Home |
| 2 | Chef | 👑 | `_chef` | 0 | Home |
| 3 | Projekte | 🏗️ | `projekte` | 1 | Baustelle |
| 4 | Arbeitsscheine | 📋 | `arbeitsscheine` | 1 | Baustelle |
| 5 | Planung | 📅 | `wochenplanung` | **2** | Zeit ⚠️ |
| 6 | Zeiterfassung | ⏱️ | `zeiterfassung` | 2 | Zeit |
| 7 | Urlaub | 🏖️ | `urlaub` | 2 | Zeit |
| 8 | Monatsabrechnung | 📄 | `stunden` | **2** | Zeit ⚠️ |
| 9 | Fahrzeuge | 🚐 | `fahrzeuge` | 3 | Fuhrpark |
| 10 | Werkzeuge | 🔧 | `werkzeuge` | 3 | Fuhrpark |
| 11 | Mitarbeiter | 👷 | `mitarbeiter` | 4 | Mehr |
| 12 | Auswertungen | 📊 | `auswertungen` | 4 | Mehr |
| 13 | Einstellungen | 🔌 | `_settings` | 4 | Mehr |
| 14 | Büro-Export | 📋 | `bueroexport` | 4 | Mehr |
| 15 | Admin | ⚙️ | `admin` | 4 | Mehr |

### Tabs ohne g-Property
**KEINE.** Alle 15 Tabs haben definiertes `g`. → Phase 2 hat keine Lücken zu füllen.

### Vorschlag (NICHT umsetzen, nur Notiz für Sebastian)
- "Planung" (g:2 → könnte g:1) — Wochenplanung ist eher Baustelle als Zeit
- "Monatsabrechnung" (g:2 → könnte g:4) — Reporting/Verwaltung, eher Mehr

→ **Kein Code-Change in Phase 2 nötig** (Sebastian-Entscheid). Nur dokumentiert.

---

## B) Tabellen mit min-width (KRITISCH = >600px)

### TOP-12 KRITISCH (sortiert nach Wert desc)

| Line | Wert | Selektor / Komponente | Mitigated? |
|------|------|----------------------|------------|
| 5936 | 1300px | `<table>` Arbeitsscheine-Overview | ❌ |
| 6109 | 1050px | `<table>` Kunden | ❌ |
| 3398 | 860px | CSS `.ber-table` | partial @900px |
| 12788 | 800px | `<div flex>` Bauvorhaben editor | ❌ |
| 12815 | 800px | `<table>` Edit mode | ❌ |
| 16984 | 800px | `<table>` Werkzeugverwaltung | ❌ |
| 6033 | 700px | Calendar 7-day grid | ❌ |
| 9988 | 700px | `<table>` Aufgaben/Tasks | ✅ overflowX wrap |
| 12712 | 700px | `<table>` Timesheet week | ❌ |
| 15456 | 700px | `<table>` KW Übersicht | ❌ |
| 7388 | 600px | `<table>` Benachrichtigungen | ❌ |
| 12764 | 600px | `<table>` Statistik | ❌ |
| 14583 | 600px | `<table>` Fahrzeugverwaltung | ❌ |

### CSS-Anker (Zeile 163, 3398, 3399)
- `.mob-table-wrap table { min-width: 600px }` (line 163) — Wrapper-Default
- `.ber-table { min-width: 860px }` (line 3398) — Reports
- `@media(max-width:900px) .ber-table { min-width:600px }` (line 3399) — partial mitigation

**Strategy Phase 3:** CSS-Override im bestehenden `@media(max-width:600px)` Block — alle `.ber-table` und `<table>` mit `minWidth>600` wrappen oder responsive machen. Lieber CSS-only als Inline-Edits (weniger Diff-Risk).

---

## C) Inline-Style Top-30 fixe Breiten

### Modal-Container (OK — width:100% + maxWidth)
| Line | maxWidth | Komponente |
|------|----------|-----------|
| 6466 | 1200 | VBueroExport |
| 10628 | 1200 | VFotos |
| 11845 | 1100 | VMaterial modal |
| 3687 | 960 | KundenPortal wrapper |
| 12342 | 900 | VMaterial list |
| 13653 | 900 | StundenzettelView |
| 13932 | 700 | VerbindungView |
| 17167 | 520 | WerkzeugView modal |
| 15333 | 480 | ZeiterfassungView modal |
| 8809 | 440 | VZeit modal |
| 3898 | 420 | LoginScreen modal |
| 13830 | 420 | StundenzettelView signature modal |

→ **Alle OK**, weil `width:100%` daneben steht.

### KRITISCH — fixe Breiten ohne 100%-Fallback (Phase-4 Targets)
| Line | Width | Komponente | Aktion |
|------|-------|-----------|--------|
| 5881 | 220 | sharePdf QR-Input | conditional `isMob?"100%":220` |
| 5978 | 200 | sharePdf QR-image | OK (Bild) |
| 12327 | 180 | VMaterial DATANORM-System input | conditional |
| 12328 | 150 | VMaterial DATANORM-Category | conditional |
| 12329 | 120 | VMaterial DATANORM-Trade select | conditional |
| 12235 | 130 | VMaterial DATANORM-Version | conditional |
| 12766 | 160 | WeekPlan vehicle column TH | OK in Tabelle |
| 14733 | 140 | FahrtenbuchPanel month picker | conditional |
| 14072 | 130 | SystemConfigPanel value input | conditional |
| 10899 | 120 | VDoku folder name input | conditional |
| 14573 | 120 | ChefDashboard worker label | OK (Label) |
| 5941 | 120 | sharePdf TH Termin-Vorschlag | OK in Tabelle |
| 5942 | 120 | sharePdf TH Termin-Bestätigt | OK in Tabelle |

→ **Phase 4 Top-Targets:** 5881, 12327, 12328, 12329, 12235, 14733, 14072, 10899, 6588 (Project select 200px). Bei Tabellen-TH/TD kein Edit (Tabelle wird in Phase 3 responsive).

---

## D) Touch-Targets <40px (Tier 1 — am Häufigsten gebraucht)

### Tier-1: Hochfrequente Buttons

| Line | Padding | FontSize | Eff.H | Komponente |
|------|---------|----------|-------|-----------|
| 5963 | 4px 7px | 11 | 19px | `✏️` AS-Edit (Arbeitsscheine-Tabelle) |
| 5964 | 4px 7px | 11 | 19px | `📄` AS-PDF |
| 5965 | 4px 7px | 11 | 19px | `⬜` AS-QR |
| 5966 | 4px 7px | 11 | 19px | `☁️↑` AS-Push |
| 5967 | 4px 7px | 11 | 19px | `⊘` AS-Storno |
| 3812 | 6px 10px | 11 | 23px | `👁️ Ansehen` Doku |
| 3813 | 6px 10px | 11 | 23px | `💾` Doku-Download |
| 5021 | 2px ?px | 12 | ~16px | Notif-Delete `✕` |
| 5060 | 4px ?px | 12 | ~20px | Photo-Queue Remove `🗑️` |
| 4989 | 4px 10px | 10 | 18px | Notif-Sync `🔄` |

### Tier-2: Modal-Close (kann brechen wenn vergrößert)
| Line | Padding | FontSize | Eff.H | Komponente |
|------|---------|----------|-------|-----------|
| 4894 | implizit | 16 | ~18px | Search clear `X` |
| 4895 | 4px 10px | 11 | 18px | Search ESC |
| 4976 | 2px 6px | 18 | 22px | Notif close `✕` |
| 5041 | implizit | 18 | ~18px | Photo-Queue close `✕` |
| 5073 | implizit | 18 | ~18px | Sync close `✕` |
| 5135 | 2px 6px | 16 | 20px | iOS install dismiss |
| 5141 | 2px 6px | 16 | 20px | iOS install close |

### Helper-Klassen (bereits OK)
- `bpS`, `bsS`, `bdS` (Z. 3311+) — `padding:9px 18px` + `minHeight:44` → OK
- `II()` Input-Helper → `minHeight:44` OK
- `.form-tabs button` (Z.3401) → `min-height:44px` OK (CSS-Klasse)

→ **Phase 5 Targets:** 5963–5967 (AS-Tabellen-Aktionen), 3812–3813 (Doku), 4976/5135/5141 (Modal-Close-Buttons).

---

## Offene Fragen (für Sebastian zu klären)

1. **Misplaced Tabs (Planung/Monatsabrechnung):** Sollen die in andere Buckets verschoben werden? (siehe A) — vorerst NICHT geändert.
2. **Calendar-Grid 7-Tage (Z.6033):** Stapeln auf Mobile (1fr statt 7) wäre echter Refactor. Vorerst overflowX-Wrap als Workaround (siehe Phase 3).
3. **AS-Tabellen-Action-Buttons (Z.5963–5967):** 5 Icons pro Zeile bei größerer Padding wird Toolbar-Reflow auslösen. Vermutlich Hide-on-Mobile + Swipe-Action besser, aber außerhalb dieser Patch-Reihe.

---

## Skip-Liste

- Bottom-Nav g-Property-Lücken: KEINE → Phase 2 entfällt (kein Commit)
- Modal-maxWidth-Werte: alle OK (haben width:100%) → kein Edit
- bpS/bsS/II() Helper: bereits ≥44px → kein Edit
- TH/TD width-Attribute in Tabellen: indirekt durch Phase-3-Tabellen-Refactor erledigt
