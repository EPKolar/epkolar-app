# -*- coding: utf-8 -*-
"""D3-Gegenprobe: war die UNBEHANDELTE Ablehnung vor der Kur schon da?

Die Frage des Auftrags war: "die Funktion gibt jetzt ein abgelehntes Promise
zurueck - fangen alle vier Aufrufstellen das ab?" Die Antwort allein genuegt
nicht. Wenn `compressPhoto` VORHER an derselben Stelle ebenso abgelehnt hat,
ist die unbehandelte Ablehnung KEINE Nebenwirkung der Kur, sondern ein
Altbestand - und ein Befund, der das nicht trennt, schiebt der Kur etwas
unter.

Gemessen wird darum BEIDES: der Stand vor der Kur (530f6c8) und HEAD.
"""
import re
import subprocess
import sys

from nebenwirkung_helfer import codemaske, zeile_von, REPO
from nw_d3_fotoaufbereiten import kette


def stellen(text, name):
    maske = codemaske(text)
    out = []
    for m in re.finditer(re.escape(name) + r"\s*\(", text):
        p = m.start()
        if not maske[p]:
            continue
        if "function " in text[max(0, p - 30):p]:
            continue
        k = kette(text, maske, p)
        kcode = "".join(c if maske[p + i] else " " for i, c in enumerate(k))
        out.append((zeile_von(text, p), ".catch(" in kcode,
                    " ".join(k.split())[:70]))
    return out


def main():
    alt = subprocess.run(["git", "-C", REPO, "show", "530f6c8:index.html"],
                         capture_output=True).stdout.decode("utf-8", "replace")
    print("VOR DER KUR (530f6c8) - alle compressPhoto-Aufrufe:")
    a = stellen(alt, "compressPhoto")
    print("  %d Aufrufstellen, davon OHNE .catch: %d"
          % (len(a), sum(1 for x in a if not x[1])))
    for z, c, s in a:
        print("    Z%-7d %-8s %s" % (z, "CATCH" if c else "OFFEN", s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
