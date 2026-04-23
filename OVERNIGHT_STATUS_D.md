# OVERNIGHT STATUS · Block D · Statische Analyse + Security

**Baseline:** `d6ca8c2` (Ende Block C)
**End-State:** `1510037`

## Commits (4)

| SHA | Subject |
|---|---|
| 43bf4f5 | docs: XSS sink audit |
| 5502942 | docs: localStorage audit |
| 9dacfe7 | docs: code debt inventory |
| 1510037 | docs: dead code candidates |

## D1 · XSS-Sink-Audit · `sql/XSS_AUDIT.md`

- 5 `innerHTML`-Hits, 0 eval/Function, 10 `document.write`.
- Alle document.write sind in `window.open()`-Print-Popups — bekannte Fixes v3.8.20/21.
- 2 P3-Hardening-Empfehlungen: L307 + L1941 Error-Overlay sollten `.textContent`
  statt `innerHTML` fürs Message-Teil verwenden.
- Barcode-SVG (L15511) geprüft: text-escape in `genBarcodeSVG` L2878 vorhanden → safe.

## D2 · localStorage-Audit · `sql/LOCALSTORAGE_AUDIT.md`

- 19 Keys klassifiziert.
- **Kritischer Fund P2:** `epkolar_gc` (base64-encoded credentials) bleibt beim Logout
  im localStorage. v3.8.7 Iter-4 räumt nur IDB-Meta auf, nicht localStorage.
- **Zweiter Fund P3:** `epkolar_juprowa_wmap` nicht in Iter-17 Cleanup-Liste.
- Langfrist-Empfehlung: `epkolar_gc` auf PBKDF2 analog `_OFFPW` (v3.8.33).

## D3 · Code-Debt-Sweep · `sql/CODE_DEBT.md`

- **0 TODO/FIXME/HACK** im Code (Inline-Marker-frei, erstaunlich sauber).
- Debt durch Block-A-D-Audits identifiziert:
  - 5 Quick Wins (< 30 min) — P2 Logout-Cleanup, P3 textContent, P4 Token-Konsolidierung
  - 5 Larger (1-2 h) — PBKDF2-Migration epkolar_gc, 4 Auth-Retry-Gaps, Dokumentation, Dead-Code, canDo-Granularität
  - 5 Architecture-Level — Inactivity-Logout, Offline-Conflict-Resolution, Bundle-Schritt, Live-Integration-Tests, Enum-Konsolidierung
- Priorisierungs-Empfehlung: Diese Woche / Nächste Session / Mittel / v4.0.

## D4 · Dead-Code-Heuristik · `sql/DEAD_CODE_CANDIDATES.md`

- 287 Top-Level-Namen gescannt, **7 Kandidaten** mit count==1 gefunden.
- Liste: ESKALATION_RULES, INIT_AS, INIT_WZ, LazyImg, MATERIAL_UNITS,
  SCHEINART_C, SCHEINSTATUS_C.
- Alle manuell gegen-greped (bestätigt: nur Deklaration, kein Use).
- Nicht automatisch gelöscht (R6/D4): Heuristik-False-Positives möglich,
  Entscheidungen mit Sebastian klären.

## Ausserhalb der Rubrik entdeckt

Während Block D's Lesedurchgang wurden diese Items in CODE_DEBT.md / ROADMAP.md
mit aufgenommen:

- `_mapBody TEXT_JSON_FIELDS` L1312 — Whitelist ohne erklärte Herkunft.
- Token-Key-Duplikate (`epkolar_auth` + separate `_token`/`_refresh`).
- `epkolar_auth_backup_preforce` wird nur in `_restoreToken`-Pfad gecleart — wenn
  User `_forceExpireToken()` aufruft und dann ohne `_restoreToken()` den Tab
  schließt, bleibt der Backup-Token liegen (dev-only, niedrig).

## Fehlschläge
- Keine. Alle 4 Sub-Tasks durchgelaufen, alle Artefakte erzeugt.

## Skipped per R6 (bewusst)
- Keine automatischen Code-Fixes in index.html (außer A1 `_n`-Sweep, das war in Block A).
- Reine Dokumentation + Analyse = konform mit Overnight-Regeln.
