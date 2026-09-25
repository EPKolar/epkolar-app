# -*- coding: utf-8 -*-
"""PreToolUse-Hook: `git add -A`, `git add -u` und `git add .` verweigern.

WOZU
────
Der git-Index gehoert dem REPOSITORY, nicht dem gerade laufenden Agenten.
Belegt am 25.09.2026: zwischen `git add` und `git commit` hat ein zweiter Lauf
den Index bestueckt - der Commit nahm **24 Dateien statt 2** mit. Wer `-A`,
`-u` oder `.` schreibt, uebergibt die Auswahl an einen Zustand, den er nicht
kontrolliert. Dateien werden deshalb einzeln benannt, und `add` und `commit`
gehoeren in EINEN Befehl.

WAS ER MISST
────────────
Nicht das Vorkommen der Zeichenfolge, sondern die ARGUMENTE eines echten
`git add`. Zwei Fehlalarme waeren sonst sicher:

  * `git commit -m "nie git add -A verwenden"` - die Regel steht in
    Commit-Meldungen und in der Doku dieses Repos. Zeichenketten werden
    deshalb VOR der Pruefung ausgeblendet.
  * `git add scripts/hook_git_add_riegel.py` - benannte Dateien sind genau
    das, was erlaubt sein soll, auch wenn der Pfad einen Punkt enthaelt.

Verkettete Befehle (`&&`, `||`, `;`, `|`, Zeilenumbruch) werden einzeln
angesehen; `git add -A && git commit` versteckt sich sonst hinter dem ersten
Glied.
"""
import json
import re
import sys

VERBOTEN = {"-A", "--all", "--no-ignore-removal", "-u", "--update", "."}
TRENNER = re.compile(r"&&|\|\||[;|\n]")


def ohne_zeichenketten(befehl):
    """Blendet den INHALT von '...' und "..." aus, die Laenge bleibt.

    Damit kann in einer Commit-Meldung ueber `git add -A` geschrieben werden,
    ohne dass der Riegel anschlaegt - der haeufigste denkbare Fehlalarm, denn
    genau diese Regel steht in der Doku dieses Repos.
    """
    return re.sub(r"'[^']*'|\"[^\"]*\"",
                  lambda m: m.group(0)[0] + " " * (len(m.group(0)) - 2) + m.group(0)[0],
                  befehl)


def verstoesse(befehl):
    """Gibt die beanstandeten Argumente zurueck - leer heisst sauber."""
    gefunden = []
    for glied in TRENNER.split(ohne_zeichenketten(befehl)):
        stuecke = glied.split()
        if len(stuecke) < 2:
            continue
        # `git` kann Schalter vor dem Unterbefehl tragen (git -C pfad add ...).
        try:
            i = stuecke.index("git")
        except ValueError:
            continue
        rest = stuecke[i + 1:]
        j = 0
        while j < len(rest) and rest[j].startswith("-"):
            j += 2 if rest[j] in ("-C", "-c", "--git-dir", "--work-tree") else 1
        if j >= len(rest) or rest[j] != "add":
            continue
        for arg in rest[j + 1:]:
            if arg in VERBOTEN or arg in ("./", ".\\"):
                gefunden.append(arg)
            elif (re.match(r"^-[A-Za-z]+$", arg) and not arg.startswith("--")
                    and ("A" in arg[1:] or "u" in arg[1:])):
                gefunden.append(arg)          # gebuendelt, etwa `-Av`
    return gefunden


def main():
    roh = sys.stdin.read()
    try:
        eingabe = json.loads(roh) if roh.strip() else {}
    except ValueError:
        return 0                               # kein Befehl, nichts zu pruefen
    befehl = (eingabe.get("tool_input") or {}).get("command") or ""
    schlimm = verstoesse(befehl)
    if not schlimm:
        return 0

    json.dump({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason":
            "Verweigert: `git add %s`. Der git-Index gehoert dem REPOSITORY, "
            "nicht diesem Lauf - zwischen `add` und `commit` kann ein anderer "
            "Lauf ihn bestuecken. Am 25.09.2026 committete ein Lauf dadurch 24 "
            "Dateien statt 2. Benenne die Dateien einzeln und fasse `add` und "
            "`commit` in EINEN Befehl:\n"
            "    git add pfad/a pfad/b && git commit -m \"...\"\n"
            "Danach die Dateizahl im Ergebnis gegenlesen."
            % " ".join(schlimm),
    }}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
