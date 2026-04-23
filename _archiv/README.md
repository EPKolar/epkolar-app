# _archiv/

Historische Artefakte. **Nicht mehr aktiv**, bleiben im Repo nur für
Nachvollziehbarkeit (vorherige Sessions, abgeschlossene Bugs, superseded Docs).

Move-Stand: 2026-04-23 via `aufräumen`-Commit `7034ecf`.
Git-History bleibt via `git log --follow <pfad>` nachverfolgbar.

## Root-Level (13 Files)

| File | Grund |
|---|---|
| BUG_HUNT.md | Walkthrough-Befunde v3.6, abgeschlossene Findings-Liste |
| BUG_HUNT_v3.8.md | Round-2 Diff-Review, abgeschlossen |
| CC_COMMAND_10h_v3.8.19_COMPLETE.md | Konsumiertes 10h-Session-Kommando (v3.8.19) |
| HANDOFF_NACHT.md | 8h-Session Handoff |
| HANDOFF_NACHT_v3.8.md | 14h-Bug-Hunt-Loop Handoff |
| HANDOFF_NACHT_v3.8.19.md | Letzter Nacht-Handoff vor v3.8.19 |
| NEXT_CHAT_v3.5.23.md | Historischer Chat-Übergabe-Zettel |
| SMOKE_LOG_v3.8.18.md | Einzelner Smoke-Log-Dump |
| baseline_*.txt (5x) | Bracket-Baselines zum Start div. Sessions |

## sql/ (25 Files)

**Abgeschlossene Bug-Bs** (B-006 → B-007 → B-017 → B-020 → B-021 → B-022):
B006b_*, B007_EXECUTE.sql, B017_INVENTORY.md, B020_*, B021_VERIFY.md,
B022_PATCHED.md, RLS_B007_PLAN.md, ALL_SQL_ONEPASTE.sql

**Historische Handoffs** (sql/):
HANDOFF_2H_SHOT_19042026, _3H_FINAL, _BLOCK8, _BLOCK13_MVP,
_CONSOLIDATION_19042026, _OVERNIGHT_FINAL, _OVERNIGHT_v3.5.174, _v3591

**Superseded** (durch v3.7/v5.0 abgelöst):
INDEX_AUDIT_v3.6.sql, Testkonzept_v4_0.md, Testkonzept_v4_4_DELTA.md

**Completed Audits/Logs**:
OVERNIGHT_LOG.md (Session-Log 18./19.04), SILENT_CATCH_AUDIT.md,
SESSION_12H_START.md

## Wiederherstellung

Falls ein Artefakt wieder aktiv werden soll:
```bash
git mv _archiv/<pfad>/<datei> <zielort>/
```
Git erkennt Rename (100% Similarity), `git log --follow` findet die gesamte History.
