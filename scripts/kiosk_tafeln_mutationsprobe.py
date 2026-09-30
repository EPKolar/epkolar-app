# -*- coding: utf-8 -*-
"""Mutationsprobe fuer `kiosk_tafeln_quelltext.py` - misst WIRKUNG.

WARUM DIESE DATEI EXISTIERT
---------------------------
`kiosk_tafeln_quelltext.py` traegt eine Selbstprobe. Dass eine Selbstprobe
DA IST, belegt nichts - ein Riegel, dessen Ausfall man nicht bemerkt, ist
Zierrat. Geprueft wird hier also nicht die Anwesenheit des Abbruchs,
sondern seine Wirkung:

    Nimmt man dem Werkzeug die Sicht, MUSS es rot werden
    UND es darf danach KEINE Zahl mehr nennen.

Die zweite Haelfte ist die wichtigere. Ein Werkzeug, das zwar 2
zurueckgibt, aber trotzdem seine Tabelle druckt, ist gefaehrlicher als
eines, das schweigt: die Tabelle wird gelesen, der Rueckgabewert nicht.

DIE GRUNDLINIE IST TEIL DER PROBE
---------------------------------
Zuerst laeuft das Werkzeug UNVERAENDERT. Ist es dort schon rot oder nennt
es schon keine Zahlen, misst die ganze Probe nichts - dann bricht sie ab,
statt zwei gruene Haken zu melden. Eine Mutationsprobe auf einer bereits
roten Grundlinie ist die Fehlerform, gegen die sie gebaut ist.

Zum Schluss wird zurueckgesetzt und noch einmal gefahren: bleibt das
Werkzeug danach rot, hat die Probe selbst etwas beschaedigt, und ihr
Ergebnis ist wertlos.

AUFRUF
------
    python scripts/kiosk_tafeln_mutationsprobe.py
    (Rueckgabe 0 = alle Mutationen wurden bemerkt)
"""
import contextlib
import io
import os
import sys

for _strom in (sys.stdout, sys.stderr):
    try:
        _strom.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import kiosk_tafeln_quelltext as K  # noqa: E402

# Die Zeile, an der man erkennt, dass das Werkzeug eine Zahl NENNT. Sie
# steht nur im Auswertungsteil, nie in der Selbstprobe.
ZAHLZEILE = "RLS-Marken      :"


def fahre():
    """Werkzeug laufen lassen; Rueckgabe und Ausgabe einfangen."""
    puffer = io.StringIO()
    with contextlib.redirect_stdout(puffer):
        try:
            rc = K.main(None)
        except SystemExit as e:
            rc = e.code
    text = puffer.getvalue()
    return rc, text, (ZAHLZEILE in text)


# Jede Mutation nimmt dem Werkzeug GENAU EINE Faehigkeit - und zwar eine,
# deren Verlust sonst wie ein Befund aussieht:
#   1. ein Melder, der nur noch EINE Schreibweise kennt, meldet fuer die
#      anderen "kommt nicht vor";
#   2. eine Erfolgspruefung, die ihr Muster nicht mehr kennt, erklaert
#      einen richtig gebauten Takt faelschlich zur blossen Uhr.
MUTATIONEN = [
    ("RLS-Melder kennt nur EINE Schreibweise",
     lambda: K.RLS_MARKEN.__setitem__(slice(None), ["_rlsLeer"])),
    ("Erfolgspruefung erkennt Array.isArray nicht mehr",
     lambda: K.ERFOLG_MUSTER.__setitem__(slice(None), ["gibtsnicht"])),
]


def main():
    print("GRUNDLINIE (unveraendert)")
    rc0, _, zahlen0 = fahre()
    print("  Rueckgabe %s, nennt Zahlen: %s" % (rc0, zahlen0))
    if rc0 != 0 or not zahlen0:
        print("  ABBRUCH: die Grundlinie ist schon rot oder nennt keine "
              "Zahlen - dann misst diese Probe nichts, und zwei gruene "
              "Haken darunter waeren eine Luege.")
        return 2

    print("\nMUTATIONEN")
    alle_ok = True
    for name, brich in MUTATIONEN:
        sicherung = (list(K.RLS_MARKEN), list(K.ERFOLG_MUSTER))
        brich()
        rc, _, zahlen = fahre()
        gut = (rc == 2 and not zahlen)
        alle_ok = alle_ok and gut
        print("  %-48s Rueckgabe %-3s Zahlen %-6s %s"
              % (name, rc, zahlen,
                 "ROT wie gewollt" if gut else "GESCHEITERT"))
        K.RLS_MARKEN[:] = sicherung[0]
        K.ERFOLG_MUSTER[:] = sicherung[1]

    print("\nGEGENPROBE: nach dem Zuruecksetzen wieder gruen?")
    rc9, _, zahlen9 = fahre()
    print("  Rueckgabe %s, nennt Zahlen: %s" % (rc9, zahlen9))
    if rc9 != 0 or not zahlen9:
        print("  GESCHEITERT: die Probe hat das Werkzeug beschaedigt.")
        alle_ok = False

    print("\n%s" % ("Alle Mutationen wurden bemerkt."
                    if alle_ok else "MINDESTENS EINE MUTATION BLIEB GRUEN."))
    return 0 if alle_ok else 2


if __name__ == "__main__":
    sys.exit(main())
