# Code Debt Inventory v2 · 2026-04-25 (Overnight #2 Block 5-3)

**Baseline:** `5e190ef` (v3.8.39)
**Vorgänger:** `sql/CODE_DEBT.md` (Overnight #1 Block D-3, mit CLOSED-Status-Updates aus v3.8.34-37).

## Delta seit v1

### Closed (seit Overnight #1)

| ID | Beschreibung | Version |
|---|---|---|
| QW1 | `epkolar_gc` Logout-Cleanup | v3.8.34 |
| QW2 | `epkolar_juprowa_wmap` Logout-Cleanup | v3.8.34 |
| QW3 | Error-Overlay textContent | v3.8.37 |
| L1 | `epkolar_gc` PBKDF2 (wurde eliminiert statt migriert) | v3.8.35 |
| L2 | 4 `_authRetry`-Gaps | v3.8.36 |
| L3 | `_mapBody` TEXT_JSON_FIELDS Doku | v3.8.37 |
| L4 (teilweise) | Dead-Code INIT_AS/INIT_WZ/LazyImg | v3.8.37 |
| Iter-20 | Juprowa-Push Response-Parse Observability | v3.8.38 |
| Block 4-4 | alt-Attribute Sweep | v3.8.39 |

### Neu entdeckt (Block 5)

### QW6 (neu) · COLORS-Konstanten-Einführung
- **Wo:** Duplicate-String-Audit (`sql/DUPLICATE_STRINGS.md`) zeigt 8+ Farb-Hex-Werte mit je 30-200 Vorkommen.
- **Problem:** Markenfarben (`#009640` = EP_GREEN existiert, 62 Raw-Hex-Vorkommen) würden bei Feinjustierung an 62 Stellen geändert werden müssen.
- **Fix:** `COLORS`-Namespace einführen, Callsites migrieren.
- **Aufwand:** 1-2 h mit sorgfältigem Batch-Approach.
- **Prio:** P3.

### L6 (neu) · TABLES-Namespace
- **Problem:** Table-Names (`'arbeitsscheine'` 54×, `'fahrzeuge'` 43×) als Raw-Strings in allen `_sbGet`/`_sbPost`-Calls.
- **Risiko:** Typo würde RLS-"table not found" erst zur Runtime zeigen.
- **Fix:** `const TABLES={ARBEITSSCHEINE:'arbeitsscheine',...}` + Callsite-Migration.
- **Aufwand:** 2 h.
- **Prio:** P3.

### Architecture-Level (unchanged von v1)

- **A1** Inactivity-Logout — Sebastian-Entscheidung offen
- **A2** Offline-Conflict-Resolution — Sebastian-Entscheidung offen
- **A3** Bundle-Schritt für v4.0
- **A4** Test-Suite auf Live-Integration (Playwright?)
- **A5** SCHEINART_C/SCHEINSTATUS_C durchsetzen oder löschen

### Geerbt (von v1, offen)

- **QW4** Token-Key-Duplikate (`epkolar_auth` + `_token` + `_refresh`) — P4
- **QW5** `_n()`-Sweep Nachziehen — P4 (die 4 intentional-Items aus Block A sind bewusst nicht angefasst)
- **L5** `canDo` `isField` Granularität — wartet auf Business-Case

## Gesamtbild

| Kategorie | v1 | v2 | Trend |
|---|---:|---:|---|
| Quick-Wins | 5 | 3 | 🟢 -2 |
| Larger Fixes | 5 | 3 | 🟢 -2 |
| Arch-Level | 5 | 5 | stabil |
| Neu in v2 | — | 2 | Monitoring |

**Gesamt-Debt reduziert**: 9 CLOSED in 5 Tagen bei 13 offenen ursprünglich. Qualitativ: Hochrisiko-Items (Security P2: L1, L2) sind durch. Verbleibende Items sind Refactor-Arbeit, keine Bugs.

## Empfehlung für Sebastian

Top-3-Priorität wenn er Zeit hat:

1. **COLORS-Namespace** (QW6) — wenn EP-Grün je feinjustiert wird, ist Refactor einmalig günstig.
2. **TABLES-Namespace** (L6) — Typo-Prävention, Developer-Experience.
3. **Inactivity-Logout** (A1) — Security-nächster-logischer-Schritt nach L1.
