# -*- coding: utf-8 -*-
"""P4: der Helfer _ktgStd - wer ruft ihn, und was bleibt uebrig?

FRAGE
─────
v3.9.992 ersetzte VIERZEHN Abschriften von `x||192.5` durch EINEN Helfer:

    function _ktgStd(v){if(v===null||v===undefined||v==="")return 192.5;
      const _k=parseFloat(v);return isNaN(_k)?192.5:_k;}

Zweck: eine echte 0 soll NICHT mehr auf 192,5 zurueckfallen.

Betroffen ist jede Stelle, die den Rueckgabewert WEITERVERARBEITET, und
jede Stelle, die die alte Form BEHALTEN hat - denn zwei Stellen, die
dasselbe Feld verschieden lesen, sind schlimmer als zwei gleich falsche.

Die Kur-Kommentare ZITIEREN `x||192.5` woertlich; darum laeuft alles ueber
die Codemaske.

KOEDER
──────
--koeder dreht in einer KOPIE eine _ktgStd-Stelle auf die alte Form zurueck.
Steigt die Zahl der `||192.5`-Reste dabei nicht um genau eins und faellt die
Zahl der _ktgStd-Aufrufe nicht um eins, misst dieses Skript nichts.
"""
import re
import sys

from nebenwirkung_helfer import lies, codemaske, zeile_von

MUSTER_REST = r"\|\|\s*192\.5"
MUSTER_REST2 = r"\|\|\s*38\.5"


def treffer(text, maske, muster):
    out = []
    for x in re.finditer(muster, text):
        if maske[x.start()]:
            out.append((zeile_von(text, x.start()),
                        " ".join(text[max(0, x.start() - 60):x.start() + 60].split())))
    return out


def main():
    text = lies()
    if "--koeder" in sys.argv:
        alt = "_ktgStd(ks.stunden)+(ks.vorjahr||0)-ys.urlaubStdGen"
        neu = "(ks.stunden||192.5)+(ks.vorjahr||0)-ys.urlaubStdGen"
        if alt not in text:
            print("KOEDER GESCHEITERT: Anker nicht gefunden.")
            return 2
        text = text.replace(alt, neu, 1)
        print("KOEDER AKTIV: _resturlaubK auf die alte falsy-Form zurueckgedreht.\n")
    maske = codemaske(text)

    auf = [t for t in treffer(text, maske, r"_ktgStd\s*\(")]
    print("_ktgStd-Stellen im CODE (inkl. Definition): %d" % len(auf))
    for z, s in auf:
        print("   Z%-7d %s" % (z, s[:120]))
    print("")
    rest = treffer(text, maske, MUSTER_REST)
    print("REST der alten Form `||192.5` im CODE: %d" % len(rest))
    for z, s in rest:
        print("   Z%-7d %s" % (z, s[:130]))
    print("")
    # Die Geschwisterfelder derselben Datensaetze: gilt die 0 dort auch?
    w = treffer(text, maske, MUSTER_REST2)
    print("Geschwisterfeld `woche`: `||38.5` im CODE: %d "
          "(NICHT kuriert - dieselbe falsy-Falle)" % len(w))
    for z, s in w:
        print("   Z%-7d %s" % (z, s[:130]))
    print("")
    v = treffer(text, maske, r"vorjahr\s*\|\|\s*0")
    u = treffer(text, maske, r"ueberstunden\s*\|\|\s*0")
    print("`vorjahr||0`: %d  `ueberstunden||0`: %d  "
          "(harmlos: der Rueckfall IST 0)" % (len(v), len(u)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
