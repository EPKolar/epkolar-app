# _archiv/sql/ — Historische Dateien

Alles hier ist **nicht mehr aktiv**. Bleibt als Referenz/Audit-Trail.

## ⚠ Nicht löschen

Die Artefakte hier sind Audit-Beweis (B-006/7/17/20/21/22 Close-Outs, Post-Mortems,
Session-Handoffs). Löschen entfernt Context zur Nachvollziehbarkeit. Wiederherstellung
per `git mv _archiv/sql/<file> sql/` — Git-History bleibt via `git log --follow` erhalten.

## Post-Mortem 23.04.2026

- `BASELINE_FIX_v3.8_BUGGY_constraints_dropped_23042026.sql` — hatte
  falsche CHECK-Werte-Listen für scheinstatus/prioritaet/role. 3 Constraints
  wurden per `ALTER TABLE DROP CONSTRAINT IF EXISTS` auf Supabase entfernt.
  Das File hier ist **nicht wieder anwenden** ohne vorher CHECK-Block zu
  entfernen oder Werte-Listen zu korrigieren. Details siehe
  `../sql/DEPLOY_SQL_REVIEW_2026-04-23.md` mit den korrekten Werte-Listen.
- `BASELINE_FIX_VERIFY_v3.8.sql` — Verify-Query. `applied=true` war
  irreführend (sagte nur aus dass Constraint existiert, nicht ob sie
  korrekt ist).

## Erledigte Probleme

- `B_12_ORPHANS_ANALYSIS.md` — 11 Rows `monteur=''` wurden auf NULL
  migriert (23.04). Keine Ghost-Orphans mehr.
- `AUTH_DEBUG_QUERIES.sql` — B-020 geschlossen 19.04 (9 user-Links).

## Überholte Versionen

- `PERMISSION_MATRIX_v3.7.md` → ersetzt durch `../sql/RLS_RECONCILE_v3.8.md`
- `PERF_v3.6.md` + `PERF_HINTS.md` + `INDEX_AUDIT_v3.7.sql` +
  `INDEX_EFFECT_v3.8.sql` + `INDEX_EFFECT_v3.8_RESULTS.md` — Perf-Baseline
  war bei allen Queries <130ms, keine Optimierung aktuell nötig.

## B-021 Status Quo

- `PHOTOS_RLS_AUDIT.sql` + `PHOTOS_RLS_FIX.sql` — 19.04 Business-Entscheidung
  auf Status Quo (alle authenticated sehen alle Fotos, `uploaded_by` als
  Audit-Trail). Rückweg ohne Datenmigration jederzeit möglich.

## Einmal-Scripts

- `_b022_sweep.js`, `_deep_scan_nullable.js`, `_wrap_viewboundaries.js` —
  wurden einmalig für spezifische Refactorings genutzt. Nicht permanent
  im Tools-Satz gehalten.

## TODO

- `TODO_MORGEN.md` — Inhalt ist in HANDOFF-Docs fortgeführt (v3.8.22+).

## Ältere Welle (v3.8.20 Aufräumen, 23.04.2026 früher)

Die v3.8.20-Aufräumen-Welle hat bereits ältere Artefakte hierher verschoben:
- 8 historische Session-Handoffs (HANDOFF_2H_SHOT_*, _3H_FINAL, _BLOCK8,
  _BLOCK13_MVP, _CONSOLIDATION, _OVERNIGHT_FINAL, _OVERNIGHT_v3.5.174, _v3591)
- SESSION_12H_START.md
- Closed-Bug-Artefakte (B006b, B007, B017, B020, B021, B022, RLS_B007_PLAN)
- Superseded (Testkonzept v4.0 + v4.4_DELTA, INDEX_AUDIT_v3.6,
  ALL_SQL_ONEPASTE, SILENT_CATCH_AUDIT)
- Session-Logs (OVERNIGHT_LOG)

Für Wiederherstellung: `git mv _archiv/sql/<file> sql/` — Rename preserviert
History via `git log --follow`.
