#!/usr/bin/env python3
"""EPKolar pre-push-Tor (versioniert im Repo, aktiv ueber `git config core.hooksPath .githooks`).

Warum: Die Bau-Sperre (~/.claude/hooks/bau-sperre.js) prueft nur den Text eines Bash-Befehls. Ein Push ueber ein
Skript, eine IDE oder einen anderen Weg ging am 19.11.2026 an ihr vorbei (1046, 1047, fix/portal-fotos-speicher).
Dieser Hook laeuft in git selbst - bei JEDEM Push-Weg.

Regeln:
  * Push nach refs/heads/main nur, wenn die Tor-Marke <git-dir>/epk-tore-ok GENAU den gepushten Commit nennt
    (geschrieben von epk_tore.py nach 8/8 gruenen Toren).
  * Kein Force-Push auf main: der bisherige Stand von main muss Vorfahre des neuen sein.
  * Loeschen von main ist verboten.
  * Andere Zweige (Feature-/Release-Zweige) passieren - sie aendern die Auslieferung nicht.

GRENZE (ehrlich): `git push --no-verify` ueberspringt jeden pre-push-Hook. Client-seitig ist das nicht vollstaendig
verhinderbar. Der eigentliche Riegel muss server-seitig sitzen (GitHub Branch-Schutz / Ruleset auf main:
nur Fast-Forward, kein Force-Push, Pflicht-Status-Check). Dieser Hook ist Verteidigung in der Tiefe.
"""
import os
import subprocess
import sys

NULL = "0" * 40


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout.strip()


def marke():
    gd = git("rev-parse", "--git-dir")
    if gd and not os.path.isabs(gd):
        gd = os.path.join(os.getcwd(), gd)
    p = os.path.join(gd, "epk-tore-ok")
    try:
        with open(p, encoding="utf-8") as f:
            return (f.read().split() or [""])[0]
    except OSError:
        return ""


def pruefe(zeilen, marke_sha, ist_vorfahre):
    """Rueckgabe: Liste von Fehlermeldungen (leer = Push erlaubt)."""
    fehler = []
    for z in zeilen:
        teile = z.split()
        if len(teile) != 4:
            continue
        lokal_ref, lokal_sha, fern_ref, fern_sha = teile
        if fern_ref != "refs/heads/main":
            continue
        if lokal_sha == NULL:
            fehler.append("main loeschen ist verboten")
            continue
        if marke_sha != lokal_sha:
            fehler.append("Tore fuer %s nicht gruen (Marke: %s). Erst: python ~/.claude/hooks/epk_tore.py <worktree>"
                          % (lokal_sha[:7], marke_sha[:7] if marke_sha else "keine"))
        if fern_sha != NULL and not ist_vorfahre(fern_sha, lokal_sha):
            fehler.append("kein Fast-Forward auf main (Force-Push verboten)")
    return fehler


def main():
    zeilen = sys.stdin.read().splitlines()

    def ist_vorfahre(a, b):
        return subprocess.run(["git", "merge-base", "--is-ancestor", a, b]).returncode == 0

    fehler = pruefe(zeilen, marke(), ist_vorfahre)
    if fehler:
        sys.stderr.write("EPK-PRE-PUSH: Push abgelehnt:\n  - " + "\n  - ".join(fehler) + "\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
