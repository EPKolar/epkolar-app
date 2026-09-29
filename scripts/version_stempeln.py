# -*- coding: utf-8 -*-
"""Die Version setzen - und NUR die drei Marken, nicht jeden Treffer.

🔴 WARUM ES DIESES WERKZEUG GIBT. Bis zum 29.09.2026 habe ich die Version mit
einem blinden Ersetzen gestempelt:

    T.replace("3.9.979", "3.9.980")

Das trifft AUCH die Aenderungsvermerke im Quelltext. Beim Sprung auf v3.9.980
wurde aus

    /* v3.9.979: ZWEIWEGSCHALTER statt Ringtausch ... */

still ein `v3.9.980` - der Vermerk behauptete danach, die Kur sei eine Version
spaeter gekommen als in Wirklichkeit. Aufgefallen ist es nur, weil der Stempel
FUENF statt der erwarteten vier Stellen meldete.

Ein Vermerk sagt, WANN etwas passiert ist. Wer ihn mitstempelt, macht die
Aenderungsgeschichte der Datei unbrauchbar - und zwar lautlos: node_check,
Klammerbilanz und der Versionsabgleich bleiben alle gruen.

WAS GESTEMPELT WIRD - genau die drei Marken, die `sql/_check_version.js` auch
prueft:

    index.html   const APP_VERSION='...'
    sw.js        Kopfzeilen-Kommentar
    sw.js        const CACHE_NAME='...'

Alles andere bleibt unberuehrt. Der Lauf nennt je Marke den alten und den
neuen Wert und bricht ab, wenn eine Marke nicht GENAU EINMAL vorkommt.
"""
import io
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)

# (Datei, Muster mit genau EINER Gruppe fuer die Zahl, Name)
# 🔴 Das Muster fuer APP_VERSION war im ersten Entwurf zu streng: es verlangte
#    das Anfuehrungszeichen direkt hinter der Zahl, die Datei fuehrt aber
#    `APP_VERSION="3.9.980-supabase"` MIT Zusatz. Ergebnis: 0 Treffer - und
#    ein Stempel, der nichts findet, haette still nichts geaendert. Genau
#    deshalb bricht dieses Werkzeug bei einer Trefferzahl ungleich eins ab,
#    statt einfach weiterzumachen.
#    `APP_VERSION=` steht ausserdem DREIMAL in der Datei; zwei davon im
#    Aenderungsprotokoll. Die Zuweisung erkennt man am Anfuehrungszeichen
#    unmittelbar davor - in der Prosa steht dort ein Leerzeichen oder nichts.
MARKEN = [
    ("index.html",
     re.compile(r"(const APP_VERSION\s*=\s*[\"'])(\d+\.\d+\.\d+)([-\w]*[\"'])"),
     "index.html APP_VERSION"),
    ("sw.js", re.compile(r"(//\s*EP Kolar Service Worker[^\r\n]*?v)(\d+\.\d+\.\d+)()"),
     "sw.js Kopfzeile"),
    ("sw.js", re.compile(r"(CACHE_NAME\s*=\s*['\"][^'\"]*?)(\d+\.\d+\.\d+)(['\"])"),
     "sw.js CACHE_NAME"),
]


def lesen(pfad):
    return io.open(os.path.join(WURZEL, pfad), encoding="utf-8",
                   newline="").read()


def stand():
    """Der aktuelle Wert je Marke - oder None, wenn sie nicht eindeutig ist."""
    aus = []
    for datei, muster, name in MARKEN:
        t = lesen(datei)
        treffer = list(muster.finditer(t))
        aus.append((name, datei, muster,
                    treffer[0].group(2) if len(treffer) == 1 else None,
                    len(treffer)))
    return aus


def main(argv):
    if not argv:
        print("Aufruf: python scripts/version_stempeln.py <neue-version>")
        print("\nAktueller Stand:")
        for name, _d, _m, wert, n in stand():
            print("   %-24s %s%s" % (name, wert or "?",
                                     "" if n == 1 else "   (%d Treffer!)" % n))
        return 0

    neu = argv[0].lstrip("v")
    if not re.fullmatch(r"\d+\.\d+\.\d+", neu):
        print("\U0001F534 %r ist keine Version der Form X.Y.Z" % neu)
        return 2

    # 🔴 ZUERST PRUEFEN, DANN SCHREIBEN. Eine Marke, die zweimal vorkommt,
    #    macht jedes Stempeln zum Ratespiel - dann lieber gar nichts.
    vorher = stand()
    for name, _d, _m, wert, n in vorher:
        if n != 1:
            print("\U0001F534 %s kommt %d mal vor statt genau einmal. "
                  "NICHTS geschrieben." % (name, n))
            return 2
        if wert == neu:
            print("\U0001F534 %s steht schon auf %s. NICHTS geschrieben."
                  % (name, neu))
            return 2

    for (name, datei, muster, wert, _n) in vorher:
        t = lesen(datei)
        t2 = muster.sub(lambda m: m.group(1) + neu + m.group(3), t, count=1)
        assert t2 != t, name
        io.open(os.path.join(WURZEL, datei), "w", encoding="utf-8",
                newline="").write(t2)
        print("   %-24s %s -> %s" % (name, wert, neu))

    # Gegenprobe: hat es genau die drei Marken getroffen und sonst nichts?
    for name, _d, _m, wert, n in stand():
        if wert != neu:
            print("\U0001F534 %s steht danach auf %r statt %r." % (name, wert, neu))
            return 2
    print("\nAlle drei Marken auf %s. Aenderungsvermerke unberuehrt." % neu)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
