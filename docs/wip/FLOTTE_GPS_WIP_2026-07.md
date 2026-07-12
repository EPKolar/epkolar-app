# Flotte-GPS-WIP — gesichert aus stash@{0}

WIP Flotte-Fixes (Null-Island/NaN-Guard + fz_latest-Banner), Vorbereitung GPS-Erfassung,
eingefroren 06.07.2026, gesichert 12.07.2026.

**Der Stash bleibt liegen** (`stash@{0}`) — dieser Patch ist nur eine zusätzliche Sicherung,
kein Ersatz. Weder `pop` noch `drop` ohne Sebastians Freigabe.

## Basis-Commit

Der Stash wurde erstellt auf:

    f182b40983ab97638371551810b16002d50e61f2   (v3.9.672)

## Umfang

    index.html | 10 ++++++----
    sw.js      |  4 ++--
    2 files changed, 8 insertions(+), 6 deletions(-)

## Wiederaufnahme

    git apply docs/wip/FLOTTE_GPS_WIP_2026-07.patch

Gegen den Basis-Commit oben prüfen (`git stash show stash@{0}` zeigt die Basis).
Weicht der aktuelle HEAD davon ab, muss der Patch rebasiert werden.

**Achtung Versionskollision:** Der Patch setzt `SW_VER`/`APP_VERSION`/`CACHE_NAME` auf
**v3.9.673**. Diese Nummer wurde am 12.07.2026 anderweitig vergeben (Sebastians
Entscheidung: .673 gilt als nicht reserviert). Beim Wiederaufnehmen müssen die
Versionszeilen des Patches auf die dann nächste freie Nummer angehoben werden — der
Rest des Patches (Null-Island/NaN-Guard, fz_latest-Banner) ist davon unberührt.
