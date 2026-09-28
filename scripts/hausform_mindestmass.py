# -*- coding: utf-8 -*-
"""Verzeichnis der Hausform „am Telefon ein Mass, am Schreibtisch keines".

    minHeight: isMob ? 40 : 0
    minWidth:  isMob ? 120 : 0

🔴 DIESES VERZEICHNIS IST KEINE MANGELLISTE - und der Weg hierher ist der
eigentliche Befund. Am 28.09.2026 hielt ich diese Form fuer den Mangel und
baute einen Riegel, der sie NIRGENDS mehr dulden wollte. Ich hatte ZWEI
Knoepfe gemessen und ueber alle geurteilt.

Der Riegel wurde rot und nannte 23 Stellen. Ich hielt das fuer die
Grundgesamtheit - bis beim Suchen nach einem anderen Knopf `isMob?44:0`
auftauchte, eine Schreibweise, die mein Muster nicht kannte. Gezaehlt ueber
ALLE Formen: 110 Vorkommen in 17 Schreibweisen. Mein Riegel hatte 87 davon
nicht gesehen und dabei ausgesehen, als haette er die Datei vermessen.

Und die Messung sagt: die Form ist NICHT der Mangel. Ueber 44 Aufnahmen lagen
50 Bedienelemente unter 24 px - die allermeisten dieser 110 Stellen sind
gross genug, weil Inhalt und Polsterung sie tragen. Der Mangel ist die
GERENDERTE Groesse, und die sieht nur der Browser:

    python scripts/echtmengen_messen.py      (44 Aufnahmen, 390 und 1440 px)
    python scripts/dialog_messen.py          (die vier Ueberlagerungen)

Dieses Werkzeug zaehlt also nur, WIE VERBREITET die Hausform ist, und schreibt
die Stellen mit Zeile und Beschriftung auf - damit die naechste Messung weiss,
wo sie nachsehen kann. Es faellt kein Urteil.
"""
import io
import json
import os
import re
import sys
from collections import Counter

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
WURZEL = os.path.dirname(HIER)

import code_scan  # noqa: E402

# 🔴 KEIN festes Zahlenpaar. Genau daran ist der erste Zaehler gescheitert:
#    er kannte `40:0` und meldete 23, obwohl 110 dastanden. Gesucht wird die
#    FORM - irgendeine Bedingung, irgendeine Zahl, Null am Schreibtisch.
MUSTER = re.compile(
    r"min(?:Height|Width)\s*:\s*[A-Za-z_$][\w.$]*\s*\?\s*\d+\s*:\s*0\b")

# Koeder je Schreibweise. Ein Koeder, der die Luecke des Musters TEILT,
# bestaetigt nur die Blindheit - deshalb stehen hier bewusst verschiedene
# Zahlen, beide Eigenschaften und ein anderer Bedingungsname.
KOEDER = [
    ("minHeight:isMob?40:0", True),
    ("minHeight:isMob?44:0", True),
    ("minWidth:isMob?120:0", True),
    ("minHeight:_bxMob?44:0", True),
    ("minHeight: isMob ? 36 : 0", True),
    # Gegenproben: was NICHT gemeldet werden darf.
    ("minHeight:isMob?40:24", False),
    ("minHeight:0", False),
    ("maxHeight:isMob?40:0", False),
]


def eichen():
    """Selbstprobe. Ohne sie ist jede Zahl dieses Werkzeugs wertlos."""
    schief = []
    for text, soll in KOEDER:
        traf = bool(MUSTER.search(text))
        if traf != soll:
            schief.append((text, soll, traf))
    return schief


def stellen(text=None):
    if text is None:
        text = io.open(os.path.join(WURZEL, "index.html"),
                       encoding="utf-8", newline="").read()
    ist = code_scan.ist_code(text)
    aus = []
    for m in MUSTER.finditer(text):
        if not ist[m.start()]:
            continue          # Kommentar - nicht mitzaehlen.
        vor = text[max(0, m.start() - 700):m.start()]
        aria = re.findall(r"'aria-label':\s*\"([^\"]{0,60})\"", vor)
        titel = re.findall(r"title:\s*\"([^\"]{0,40})\"", vor)
        klick = re.findall(r"onClick:\s*([^,]{0,60})", vor)
        aus.append({"zeile": text.count("\n", 0, m.start()) + 1,
                    "form": m.group(0),
                    "name": (aria[-1] if aria else
                             (titel[-1] if titel else "")),
                    "onClick": (klick[-1].strip() if klick else "")[:50]})
    return aus


def main():
    schief = eichen()
    if schief:
        for text, soll, traf in schief:
            print("\U0001F534 Koeder %r: soll %s, ist %s" % (text, soll, traf))
        print("Das Muster ist nicht geeicht. Die Zahlen unten sind wertlos.")
        return 2
    print("Koeder: %d von %d richtig (davon %d Gegenproben)"
          % (len(KOEDER), len(KOEDER), sum(1 for _, s in KOEDER if not s)))

    aus = stellen()
    formen = Counter(x["form"] for x in aus)
    print("\n%d Vorkommen in %d Schreibweisen:" % (len(aus), len(formen)))
    for f, n in formen.most_common():
        print("   %-34s %3d" % (f, n))

    ziel = os.path.join(WURZEL, "docs", "befunde", "HAUSFORM_MINDESTMASS.json")
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps({"vorkommen": len(aus), "schreibweisen": len(formen),
                    "je_form": dict(formen), "stellen": aus},
                   ensure_ascii=False, indent=1))
    print("\ngeschrieben:", ziel)
    print("🔴 Das ist KEINE Mangelliste. Welche dieser Knoepfe zu klein sind,")
    print("   sagt nur: python scripts/echtmengen_messen.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
