# OVERNIGHT #2 · STATUS · Block 2 · Preview-Files

**Baseline:** `f0f97bf`
**End-State:** (nach Block 2 Commit)

## Ergebnis

| Sub-Task | Anweisung | Status | File |
|---|---|---|---|
| 2-1 | preview/whatsapp_ui_v0.html | ✅ existiert aus Overnight #1 | `preview/whatsapp_ui_v0.html` (9371756) |
| 2-2 | preview/WHATSAPP_UI_README.md | ✅ existiert aus Overnight #1 | `preview/WHATSAPP_UI_README.md` (d083e25) |
| 2-3 | preview/README.md (Ordner-Übersicht) | ✅ neu | `preview/README.md` |
| 2-4 | OVERNIGHT2_STATUS_2.md | ✅ dieses File | — |

## Was ist neu in 2-3

`preview/README.md` erklärt:
- Zweck des Ordners (Design-Iteration, Stakeholder-Review, Dokumentation)
- 7 Regeln für Preview-Files (standalone, CDN-React, pure state, Mock-Fixtures, Role-Switch, ...)
- Öffnen-Anleitung (file:// oder localhost:8000)
- Pattern für neue Previews (step-by-step template)
- Integration-Workflow bei Grün-Licht

## Keine index.html-Berührung

Gemäß H1 wurde index.html nicht angefasst. Alle Commits in diesem Block sind pure Docs.

## Check

Keine Version-Bumps (H4 — nur in Block 4 erlaubt).
Kein pytest-Impact (Tests prüfen nur index.html/sw.js-Invariants).
