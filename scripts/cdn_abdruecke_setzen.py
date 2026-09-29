# -*- coding: utf-8 -*-
"""Traegt die geprueften SRI-Abdruecke in die acht cdnjs-Tags ein.

🔴 WARUM DAS EIN EIGENES WERKZEUG IST UND KEIN HANDGRIFF.
Ein Abdruck ist 88 Zeichen Base64 ohne Bedeutung. Ein einziges falsches
Zeichen fuehrt nicht zu einem Fehler, sondern dazu, dass der Browser die
Datei VERWEIGERT - bei `react.production.min.js` bleibt die App weiss, ohne
Meldung auf dem Schirm. Acht solche Zeichenketten von Hand abzuschreiben
sind acht Gelegenheiten, die App zu toeten.

Dieses Werkzeug holt die Abdruecke aus der Tafel des Riegels
(`tests/test_cdn_integrity_v986.py`), damit es nur EINE Fassung davon gibt.
Eine zweite Abschrift koennte auseinanderlaufen, und dann waere nicht mehr
zu sagen, welche stimmt.

🔴 ES PRUEFT VORHER GEGEN DIE DATEI SELBST. Mit `--nachrechnen` wird jede
Datei abgerufen und ihr sha512 gebildet; stimmt einer nicht, wird NICHTS
geschrieben. Die cdnjs-API ist selbst cdnjs - sie als Quelle fuer die
Pruefsumme von cdnjs-Dateien zu nehmen waere ein Zirkel.

Aufruf:
    python scripts/cdn_abdruecke_setzen.py --nachrechnen   # mit Netz, streng
    python scripts/cdn_abdruecke_setzen.py                 # nur eintragen
"""
import io
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, os.path.join(WURZEL, "tests"))

import safe_edit                                   # noqa: E402
from test_cdn_integrity_v986 import TAFEL          # noqa: E402

ZIEL = os.path.join(WURZEL, "index.html")
BASIS = "https://cdnjs.cloudflare.com/ajax/libs/"


def nachrechnen():
    """Jeden Abdruck gegen die Datei pruefen, die der Browser wirklich holt.

    Gibt die Liste der Abweichungen zurueck; leer heisst geprueft.
    """
    import base64
    import hashlib
    import urllib.request
    schief = []
    for pfad, soll in sorted(TAFEL.items()):
        try:
            with urllib.request.urlopen(BASIS + pfad, timeout=40) as a:
                roh = a.read()
        except Exception as e:                       # noqa: BLE001
            schief.append("%s: nicht erreichbar (%s)" % (pfad, e))
            continue
        if not roh:
            schief.append("%s: leere Antwort" % pfad)
            continue
        ist = "sha512-" + base64.b64encode(
            hashlib.sha512(roh).digest()).decode()
        if ist != soll:
            schief.append("%s\n     Tafel: %s\n     Datei: %s"
                          % (pfad, soll, ist))
        else:
            print("   gleich  %s" % pfad)
    return schief


def main(argv):
    if "--nachrechnen" in argv:
        print("Rechne die %d Abdruecke gegen die ausgelieferten Dateien nach:"
              % len(TAFEL))
        schief = nachrechnen()
        if schief:
            print("\n\U0001F534 %d Abdruecke stimmen NICHT:" % len(schief))
            for s in schief:
                print("   " + s)
            print("\nNICHTS GESCHRIEBEN. Ein falscher Abdruck macht die App "
                  "vollstaendig tot -\ndas ist schlimmer als gar keiner.")
            return 2
        print("   \U0001F7E2 %d von %d stimmen ueberein.\n" % (len(TAFEL),
                                                               len(TAFEL)))

    t = io.open(ZIEL, encoding="utf-8", newline="").read()
    paare, schon, fehlt = [], [], []
    for pfad, abdruck in sorted(TAFEL.items()):
        wort = "href" if pfad.endswith(".css") else "src"
        alt = 'crossorigin %s="%s%s"' % (wort, BASIS, pfad)
        neu = 'crossorigin integrity="%s" %s="%s%s"' % (abdruck, wort,
                                                        BASIS, pfad)
        n = t.count(alt)
        if neu in t:
            schon.append(pfad)
        elif n == 1:
            paare.append((alt, neu, pfad))
        else:
            fehlt.append("%s: Anker trifft %d mal statt einmal" % (pfad, n))

    if fehlt:
        print("\U0001F534 %d Anker passen nicht:" % len(fehlt))
        for f in fehlt:
            print("   " + f)
        print("NICHTS geschrieben. Die Tags sehen anders aus als erwartet -\n"
              "das gehoert angesehen, nicht ueberschrieben.")
        return 2
    if schon:
        print("%d Tags tragen den Abdruck schon: %s"
              % (len(schon), ", ".join(schon)))
    if not paare:
        print("\U0001F7E2 Nichts zu tun - alle %d Tags sind abgesichert."
              % len(TAFEL))
        return 0

    vorher = len(t)
    safe_edit.ersetze(ZIEL, paare)
    nachher = len(io.open(ZIEL, encoding="utf-8", newline="").read())
    print("\U0001F7E2 %d Abdruecke eingetragen, %+d Zeichen."
          % (len(paare), nachher - vorher))
    print("   Jetzt EINMAL laden und die Konsole ansehen: schlaegt ein "
          "Abdruck fehl,\n   bleibt die App weiss und sagt es nur dort.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
