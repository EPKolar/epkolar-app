# -*- coding: utf-8 -*-
"""Den Bericht der Inline-Messung lesen - und Navigation von Bereichen trennen.

🔴 WARUM DIESER ZWEITE SCHRITT NOETIG IST.
`inline_bereiche_messen.py` klickt nur INNERHALB des Inhaltsbereichs, und die
Annahme dahinter ist: dort steht keine Navigation. Fuer die Fachansichten
traegt sie. Fuer `home` nicht - dessen Kacheln SIND die Navigation. Ein Lauf
ueber `home` meldet 27 "Bereiche", von denen die meisten Wechsel in andere
Ansichten sind.

Das macht die Messungen nicht falsch: was nach dem Klick gemessen wurde, ist
wirklich da. Falsch waere die BESCHRIFTUNG. Und eine Zahl mit falscher
Beschriftung ist gefaehrlicher als keine.

WORAN MAN ES ERKENNT, OHNE NEU ZU MESSEN
Ein aufgeklappter Bereich laesst den Ruhezustand stehen (hoher Erhalt) oder
ersetzt ihn durch etwas, das noch Reste davon traegt. Eine Navigation tauscht
ALLES: Erhalt praktisch null. Einzelne Fensterwechsel gibt es auch in
Fachansichten - aber wenn FAST ALLE Eintraege einer Ansicht auf Erhalt ~0
stehen, ist die Ansicht selbst eine Kachelwand.

🔴 DIE SCHWELLEN STEHEN HIER, NICHT IM TEXT DES BERICHTS.
Ein Eintrag gilt als "getauscht" bei Erhalt < 0.10; eine Ansicht gilt als
Kachelwand, wenn mindestens 70 % ihrer Eintraege getauscht sind UND es
mindestens fuenf sind. Beide Zahlen sind gewaehlt, nicht gemessen - deshalb
nennt der Bericht je Ansicht den tatsaechlichen Anteil, damit man sie
nachrechnen kann.
"""
import io
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)

GETAUSCHT = 0.10
ANTEIL = 0.70
MINDESTENS = 5


def einordnen(bericht):
    aus = {}
    for name, v in bericht.get("ansichten", {}).items():
        b = v.get("bereiche") or []
        if not b:
            aus[name] = {"art": "keine Bereiche", "n": 0, "anteil": None}
            continue
        getauscht = sum(1 for x in b if (x.get("erhalt") or 0) < GETAUSCHT)
        anteil = getauscht / len(b)
        kachel = len(b) >= MINDESTENS and anteil >= ANTEIL
        aus[name] = {"art": "Kachelwand" if kachel else "Bereiche",
                     "n": len(b), "anteil": round(anteil, 2),
                     "unter24": sum(x.get("abs_unter24") or 0 for x in b),
                     "namenlos": sum(x.get("abs_namenlos") or 0 for x in b),
                     "unter12": sum(x.get("abs_unter12") or 0 for x in b)}
    return aus


def main(argv):
    pfad = (argv[0] if argv else
            os.path.join(WURZEL, "docs", "befunde", "INLINE_BEREICHE.json"))
    bericht = json.load(io.open(pfad, encoding="utf-8"))
    ein = einordnen(bericht)
    print("Schwellen: getauscht < %.2f Erhalt | Kachelwand ab %d%% von "
          "mindestens %d Eintraegen\n" % (GETAUSCHT, ANTEIL * 100, MINDESTENS))
    print("%-14s %-12s %5s %8s %8s %9s %9s"
          % ("Ansicht", "Art", "n", "getauscht", "<12px", "<24px",
             "namenlos"))
    ges_b = ges_24 = ges_nl = ges_12 = 0
    for name, d in sorted(ein.items()):
        print("%-14s %-12s %5d %8s %8s %9s %9s"
              % (name, d["art"], d["n"],
                 "-" if d["anteil"] is None else "%.0f%%" % (d["anteil"] * 100),
                 d.get("unter12", "-"), d.get("unter24", "-"),
                 d.get("namenlos", "-")))
        if d["art"] == "Bereiche":
            ges_b += d["n"]
            ges_24 += d.get("unter24", 0)
            ges_nl += d.get("namenlos", 0)
            ges_12 += d.get("unter12", 0)
    print("\nEchte Bereiche (ohne Kachelwaende): %d" % ges_b)
    print("   darin unter 12 px: %d | unter 24 px: %d | namenlos: %d"
          % (ges_12, ges_24, ges_nl))
    kw = [n for n, d in ein.items() if d["art"] == "Kachelwand"]
    if kw:
        print("\n\U0001F534 Als KACHELWAND gefuehrt und NICHT mitgezaehlt: %s"
              % ", ".join(sorted(kw)))
        print("   Ihre Klicks wechseln die Ansicht. Die Messungen dort sind "
              "richtig,\n   aber sie messen eine ANDERE Ansicht - als "
              "'Bereich' waeren sie falsch beschriftet.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
