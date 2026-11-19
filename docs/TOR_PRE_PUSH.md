# Push-Tor als echter git pre-push-Hook (19.11.2026)

## Problem
Die Bau-Sperre (`~/.claude/hooks/bau-sperre.js`) prueft nur den TEXT eines Bash-Befehls auf `git push`. Ein Push,
der anders ausgeloest wird (Skriptdatei, IDE, anderes Programm), ging an ihr vorbei. Am 19.11.2026 so geschehen:
v3.9.1046, v3.9.1047 (main, Tore jeweils gruen) und der Zweig `fix/portal-fotos-speicher` wurden ueber ein
Skript gepusht.

## Loesung
`.githooks/pre-push` (Shell-Huelle) + `.githooks/pre_push.py` (Logik), versioniert im Repo. Aktivierung pro Klon:

    git config core.hooksPath .githooks

(gilt fuer den Klon und alle seine Worktrees). git ruft den Hook bei JEDEM Push-Weg auf.

Regeln: Push nach `main` nur, wenn `<git-dir>/epk-tore-ok` genau den gepushten Commit nennt (geschrieben von
`scripts/tore/epk_tore.py` = Kopie von `~/.claude/hooks/epk_tore.py` nach 8/8 gruenen Toren); kein Force-Push und
kein Loeschen von main; andere Zweige passieren. Fehlt Python → Ablehnung (fail closed).

## Gegenprobe (Rot → Gruen), 19.11.2026
Gleicher main-Push ohne Tor-Marke, an den echten Hook gefuettert (`hook_umkehr.py` im Sitzungs-Scratchpad):

| Stand | Ergebnis |
|---|---|
| Hook-Logik OHNE Marken-Pruefung (entspricht dem Zustand der Skript-Umgehung) | rc 0 → Push ginge durch |
| Hook wie committet | rc 1 → "Tore fuer 739f6a7 nicht gruen (Marke: keine)" → abgelehnt |

Dazu `tests/test_pre_push_tor.py` (10 Faelle, Exit 0): main ohne/falsche Marke abgelehnt, mit Marke erlaubt,
Force abgelehnt, Loeschen abgelehnt, Feature-Zweig erlaubt, gemischter Push wird als Ganzes abgelehnt.

Ende-zu-Ende ueber den Skriptweg (Sebastian, NICHT durch Claude - die Bau-Sperre verbietet Claude jeden Push-Befehl):
in einem Wegwerf-Klon mit lokalem Bare-Remote `git config core.hooksPath .githooks` setzen und per Skript
`git push <bare> HEAD:main` ausloesen → muss mit "EPK-PRE-PUSH: Push abgelehnt" enden.

## Grenze - ehrlich
`git push --no-verify` ueberspringt jeden pre-push-Hook; client-seitig ist das nicht vollstaendig verhinderbar.
Der eigentliche Riegel ist server-seitig: **GitHub Branch-Schutz / Ruleset auf `main`** (nur Fast-Forward, kein
Force-Push, kein Loeschen, Pflicht-Status-Check oder Pflicht-Review). Das muss Sebastian im GitHub-Repo
(Settings → Rules → Rulesets) einrichten. Der Hook ist Verteidigung in der Tiefe.
