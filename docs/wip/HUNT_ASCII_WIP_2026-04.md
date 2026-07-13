# Hunt-ASCII-WIP — gesichert aus stash@{1}

Sebastian-WIP: ASCII-Konvertierung der Bug-Hunt-Skripte (Umlaute/Sonderzeichen aus den
Bat-/Queue-Dateien raus). Angelegt April 2026, gesichert 13.07.2026.

**Der Stash bleibt liegen** (`stash@{1}` auf dem srvdc02-Spiegel) — dieser Patch ist eine
zusätzliche Sicherung, kein Ersatz. Weder `pop` noch `drop` ohne Sebastians Freigabe.
Mit dieser Datei ist der Spiegel vollständig aus GitHub reproduzierbar: er enthält keine
Unikate mehr (der zweite Stash liegt als `FLOTTE_GPS_WIP_2026-07.patch` daneben).

## Basis

    Branch:  cc-bug-hunt-eternal/2026-04-26
    Commit:  02881d0a866fecbbc35d805e50bf1025baeda1dd
             "sprint 1: Home/Dashboard - 25 findings (13 HIGH, 9 MEDIUM, 2 NOISE)
              [manual recovery from CC permission-block]"

`git apply --check` gegen diesen Commit: **sauber** (verifiziert 13.07.2026 in einem
temporären Worktree, nichts angewendet).

## Umfang

    scripts/bughunt-eternal-baumgmt.bat  | 382 ++++++++++++++++-------------------
    scripts/bughunt-queue-baumgmt.txt    |  65 +++---
    scripts/bughunt-state-baumgmt.txt    |   4 +-
    scripts/powerplan-backup-baumgmt.txt |   2 +-
    4 files changed, 212 insertions(+), 241 deletions(-)

## Wiederaufnahme

    git checkout cc-bug-hunt-eternal/2026-04-26
    git apply docs/wip/HUNT_ASCII_WIP_2026-04.patch

Der Patch ist gegen den Basis-Commit oben gebaut. Weicht der Branch-Kopf inzwischen ab,
muss er rebasiert werden — die Skripte liegen unter `scripts/`, nicht in `index.html`,
Konflikte sind also unwahrscheinlich.

Siehe auch `FLOTTE_GPS_WIP_2026-07.md` (Sicherung von `stash@{0}`).
