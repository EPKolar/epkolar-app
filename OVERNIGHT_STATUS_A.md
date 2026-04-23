# OVERNIGHT STATUS · Block A · Hygiene + Test-Suite

**Zeitraum:** 2026-04-23 spät → 2026-04-24 früh
**Baseline:** `1fcc24e` (v3.8.33)
**End-State:** `beb8b44`

## Drift-Hinweis (R9)

Die Anweisungsdatei `CC_OVERNIGHT_24042026.md` spezifiziert als Start-Zustand
**v3.8.31** (nach `e09438b` Audit-Fix). Tatsächlicher Start war **v3.8.33 / 1fcc24e**,
weil ein Iter-19-Bug-Hunt-Commit vorher user-initiiert durchgeführt wurde. Drift
erkannt, Memory korrigiert, Overnight-Lauf weiter ohne Version-Bump wie vorgesehen.

## Commits (4)

| SHA | Subject |
|---|---|
| 85b6ab0 | refactor: _n() sweep for NaN-safe numeric formatting |
| 9e8bdae | docs: _authRetry gap audit |
| 81c84f5 | docs: canDo permission matrix |
| beb8b44 | test: static invariant suite bootstrap (33 tests, 7 Themen) |

## A1 · _n() Sweep
- 5 `.toFixed()` Treffer total. 1 Fix (L13853 `w.hours` → NaN-safe), 4 intentional
  dokumentiert (_fmtH guarded, _n-Definition selbst, GeoAPI-Coords, guarded by `>0`).
- R4-Checks grün: syntax OK, brackets `() -2 {} 0 [] 0`.

## A2 · _authRetry Gap Audit
- 27 Sites (21 SB_REST + 6 _SB_AUTH) klassifiziert.
- 13 ✅ wrapped, 8 🟡 intentional, 4 🔴 Gaps.
- Gaps: L6366 juprowa_update_passport (P2), L6365 juprowa_get_config (P2),
  L3954 bautagebuch-schema-check (P3), L4031 workers-probe (P3).
- Nicht automatisch gefixt (A2-Regel, R6).

## A3 · canDo Permission Matrix
- 44 Actions + 2 Owner-Zweige extrahiert aus L3008-3014.
- 7-Rollen-Matrix (admin/pl/buero/om/tech/mont/lager) in `sql/CANDO_MATRIX.md`.
- 5 Inkonsistenzen dokumentiert (I1 admin_panel ohne isLager, I2 isLager-
  Redundanz, I3 isField ungranuliert, I4 buero-Field-Actions, I5 isOwn-Mehrdeutig).

## A4 · Python Test-Suite
- Bootstrap: tests/ mit requirements.txt, README, conftest, 6 Test-Files.
- **33 Tests, 33 passed, 0 failed** (Target war 25 — übertroffen).
- Themen: invariants(5), versioning(4), helpers(10), security(4), cando(3), docs(7).
- Laufzeit: ~0.9 s.
- Run: `python -m pytest tests/ -v`.

## Fehlschläge behandelt während A4

| Fail | Ursache | Fix |
|---|---|---|
| test_b007_final_sql_present | File wurde 23.04. archiviert | Pfad `_archiv/sql/` |
| test_offpw_login_write_uses_helper | Regex zu eng (nur 1-Zeilen-Snippet) | Regex auf ~200 Char Kontext erweitert |
| test_no_document_write | 5 legit `<win>.document.write` (Print-Popups) | Test umbenannt + filter auf top-level `document.write` |

Alle 3 sauber aufgelöst (nicht als fail dokumentiert, da behoben).

## Skipped / out of scope
- Keine. Alle 4 Sub-Tasks abgeschlossen.

## Brackets-Baseline am Ende
`() -2 {} 0 [] 0` — stabil.
