# -*- coding: utf-8 -*-
"""B2/B3: Zaehlt die LESEAUFRUFE und trennt sie nach eigener Grenze.

FRAGE
─────
B3 (v3.9.993) haengt `limit=5000` nur noch an, wenn der Aufrufer KEINE
eigene Grenze gesetzt hat. B2/B2' (v3.9.995/996) meldet eine vermutlich
gekappte Liste nur noch dann, wenn der Aufrufer KEINE eigene Grenze hat.

Beides haengt an derselben Unterscheidung. Betroffen ist also NICHT die
geaenderte Stelle, sondern jeder Aufrufer mit eigener Grenze:
 * vor B3 gewann der Helfer-Wert 5000 (er stand ZULETZT in der Adresse) -
   `limit=1` lieferte bis zu 5000 Zeilen, `limit=200` ebenso;
 * nach B3 gilt die Grenze des Aufrufers.

KOEDER (Selbstprobe)
────────────────────
Mit --stand v995 wird derselbe Zaehler gegen 61c5387 gefahren. Dort ist der
BEKANNTE Fehler drin (der Melder feuerte bei jedem `limit=1`). Findet der
Zaehler die zehn `limit=1`-Aufrufe dort NICHT, misst er nichts und ein
gruenes Ergebnis auf HEAD bedeutet nichts.

AUFRUF
──────
    python scripts/nw_b2_b3_leseaufrufe.py
    python scripts/nw_b2_b3_leseaufrufe.py --stand v995
"""
import re
import subprocess
import sys

from nebenwirkung_helfer import lies, codemaske, zeile_von, REPO

LESER = ["_sbGetOrder", "_sbGetUsersSafe", "_sbGetAnon", "_sbGet"]


def argumente(text, maske, start):
    """Text der Argumentliste ab der oeffnenden Klammer bei `start`.

    Klammern werden nur gezaehlt, wo die Codemaske Code sagt - eine Klammer
    in einer Zeichenkette oder einem Kommentar kann damit nicht schliessen.
    Das ist der Grund, warum hier NICHT code_scan._klammer_zu benutzt wird:
    das kennt keine Regex-Literale und liefert die Stelle NACH der Klammer.
    """
    tiefe = 0
    i = start
    n = len(text)
    while i < n:
        c = text[i]
        if maske[i]:
            if c == "(":
                tiefe += 1
            elif c == ")":
                tiefe -= 1
                if tiefe == 0:
                    return text[start + 1:i]
        i += 1
    return None


def census(text):
    maske = codemaske(text)
    treffer = []
    belegt = set()
    for name in LESER:
        for m in re.finditer(re.escape(name) + r"\s*\(", text):
            p = m.start()
            if not maske[p]:
                continue            # steht im Kommentar - die Kur zitiert sich selbst
            if p in belegt:
                continue
            # _sbGet ist Praefix von _sbGetOrder/_sbGetAnon/_sbGetUsersSafe
            if name == "_sbGet" and re.match(r"_sbGet[A-Za-z]", text[p:p + 12]):
                continue
            # Definition selbst ueberspringen (function _sbGet(table,filter))
            vor = text[max(0, p - 20):p]
            if "function " in vor:
                continue
            belegt.add(p)
            klammer = text.index("(", m.start() + len(name) - 1)
            arg = argumente(text, maske, klammer)
            if arg is None:
                arg = ""
            eigen = re.search(r"limit=(\d+|\$\{|\"\s*\+|'\s*\+)", arg)
            treffer.append({
                "name": name,
                "pos": p,
                "zeile": zeile_von(text, p),
                "grenze": eigen.group(0) if eigen else "",
                "arg": " ".join(arg.split())[:150],
            })
    return treffer


def main():
    stand = None
    if "--stand" in sys.argv:
        stand = sys.argv[sys.argv.index("--stand") + 1]
    if stand:
        rev = {"v995": "61c5387", "v996": "1d6a6e5", "v994": "3de12b2",
               "v993": "54f5d34", "v992": "530f6c8", "v991": "c92f4a9",
               "vor": "a9c04d9"}.get(stand, stand)
        text = subprocess.run(["git", "-C", REPO, "show", rev + ":index.html"],
                              capture_output=True).stdout.decode("utf-8", "replace")
        print("STAND: git " + rev)
    else:
        text = lies()
        print("STAND: Arbeitsbaum (HEAD)")

    t = census(text)
    print("Leseaufrufe gesamt: %d" % len(t))
    for name in LESER:
        n = [x for x in t if x["name"] == name]
        print("  %-16s %3d" % (name, len(n)))
    eigen = [x for x in t if x["grenze"]]
    print("MIT eigener Grenze: %d" % len(eigen))
    von = {}
    for x in eigen:
        von[x["grenze"]] = von.get(x["grenze"], 0) + 1
    for k in sorted(von):
        print("   %-14s %dx" % (k, von[k]))
    print("OHNE eigene Grenze: %d  (bekommen die stille 5000)" % (len(t) - len(eigen)))
    print("")
    print("DIE AUFRUFER MIT EIGENER GRENZE - sie sind von B3 UND B2 betroffen:")
    for x in sorted(eigen, key=lambda y: y["zeile"]):
        print("  Z%-6d %-16s %-10s %s" % (x["zeile"], x["name"], x["grenze"], x["arg"][:110]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
