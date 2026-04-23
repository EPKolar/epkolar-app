# OVERNIGHT #2 · STATUS · Block 1 · Docs nachziehen

**Zeitraum:** 2026-04-25 früh (Overnight #2 Start).
**Baseline:** `282c3de` (v3.8.38).
**End-State:** `4b30204` (nach VORAB-Check).

## Ergebnis: Alle Block-1-Docs existieren bereits aus Overnight #1.

Sebastian's Overnight #2-Command listet Doku-Items, die während Overnight #1 (Block A+C) und im Iter-19-Sweep bereits erstellt wurden. Nichts neu zu machen außer Gegen-Check:

| Sub-Task | Anweisung | Status | Vorhandener File |
|---|---|---|---|
| 1-1 | ARCHITECTURE.md im Repo-Root | ✅ existiert | `ARCHITECTURE.md` (f773883, 24.04) |
| 1-2 | RUNBOOK.md im Repo-Root | ✅ existiert | `RUNBOOK.md` (7327d2b, 24.04) |
| 1-3 | sql/CANDO_MATRIX.md | ✅ existiert | `sql/CANDO_MATRIX.md` (81c84f5, 24.04) |
| 1-4a | sql/README.md | ✅ existiert | `sql/README.md` (6c6cba3, 24.04) |
| 1-4b | sql/_archiv/README.md | ✅ existiert | `_archiv/sql/README.md` (6c6cba3, 24.04) |
| VORAB | SILENT_REAUTH_STATUS.md | ✅ neu erstellt | `SILENT_REAUTH_STATUS.md` (4b30204, 25.04) |

## Commits diesem Block (1)

| SHA | Subject |
|---|---|
| 4b30204 | docs: silent re-auth status after L1 gc-removal |

## Keine Duplikate erzeugt

H8-Prinzip "Ehrlich bleiben": Bestehende Docs werden nicht neu geschrieben, nur die fehlende VORAB-Datei ergänzt. Jeder bestehende Doc-Text wurde auf Aktualität geprüft — alle sind post-v3.8.37 und noch gültig.

## Nächster Block

Block 2: Preview-Files. Gleiche Situation erwartet — `preview/whatsapp_ui_v0.html` + `WHATSAPP_UI_README.md` existieren bereits; nur neue Datei `preview/README.md` ist zu ergänzen.
