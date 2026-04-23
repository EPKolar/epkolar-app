# Dead Code Candidates v2 · 2026-04-25 (Overnight #2 Block 5-1)

**Baseline:** `5e190ef` (v3.8.39).
**Methode:** Identisch zu v1 (Overnight #1 Block D-4), aber post-Cleanup.
**Ergebnis:** 4 Kandidaten (reduziert von 7 in v1).

## Kandidaten (count == 1, manuell verifiziert)

| Name | Line | Typ | Entscheidung v1 |
|---|---:|---|---|
| `ESKALATION_RULES` | ~2763 | const Object | KEEP (Dokumentations-Artefakt für Feature 12 Auto-Escalation) |
| `MATERIAL_UNITS` | ~9348 | const Array | KEEP (Units-Liste reserviert für Dropdown-Wiring) |
| `SCHEINART_C` | ~399 | Object.freeze | KEEP (Enum-Konstante, Code nutzt Raw-Strings) |
| `SCHEINSTATUS_C` | ~398 | Object.freeze | KEEP (selbe Logik wie SCHEINART_C) |

## Delta zu v1

| Name | v1-Status | v2-Status |
|---|---|---|
| `INIT_AS` | LISTED | ✅ DELETED v3.8.37 (DSGVO: echte Kundendaten in Seed) |
| `INIT_WZ` | LISTED | ✅ DELETED v3.8.37 (unused Seed-Werkzeuge) |
| `LazyImg` | LISTED | ✅ DELETED v3.8.37 (unused React-Component) |
| `ESKALATION_RULES` | LISTED | 🟡 KEEP mit Rationale |
| `MATERIAL_UNITS` | LISTED | 🟡 KEEP mit Rationale |
| `SCHEINART_C` | LISTED | 🟡 KEEP mit Rationale |
| `SCHEINSTATUS_C` | LISTED | 🟡 KEEP mit Rationale |

## Statistik

- Total Top-Level-Namen: **284** (v1: 287 — Reduktion durch Löschungen)
- Dead Candidates: **4** (v1: 7)
- Aktiv genutzte: **280** (98.6 %)

## Empfehlung

Sebastian-Entscheidung bleibt offen:

- **(A)** Enums `SCHEINART_C`/`SCHEINSTATUS_C` durchsetzen (alle Raw-String-Callsites migrieren) — groß, hunderte Stellen.
- **(B)** Enums löschen — ehrliche Anerkennung dass Code mit Strings arbeitet.
- **(C)** Status-Quo — Enums als Doku-Artefakte + `eslint-disable` Kommentar.

`ESKALATION_RULES` + `MATERIAL_UNITS` warten auf konkrete Feature-Nutzung. Wenn Feature nicht kommt → später löschen.
