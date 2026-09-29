# -*- coding: utf-8 -*-
"""Ein neues Messwerkzeug bringt seine Selbstprobe mit.

🔴 DIE FEHLERKLASSE, DIE DAS FESTHAELT, hat mich am 29.09.2026 VIERMAL an
einem Tag erwischt - jedes Mal sah der Ausfall aus wie ein Ergebnis:

  * eine nach HOEHE sortierte, auf zwoelf gekappte Beispielliste, und daraus
    eine Aussage ueber die BREITE (sie stimmte zufaellig),
  * eine Hilfsfunktion, die die Stelle HINTER der Klammer zurueckgibt - der
    Sucher fand NULL Treffer, und null sieht aus wie „es gibt keine",
  * eine zu grobe Zuordnung, die SECHS Faelle meldete, wo es drei sind,
  * ein Haken, der auf einer cp1252-Konsole abstuerzte, statt zu schuetzen.

Drei davon hat eine Eichprobe gefangen, bevor die Zahl in einen Bericht kam.
Der vierte hatte an dieser Stelle keine.

🔴 DIESER RIEGEL VERLANGT NICHT, DASS ALLE 45 WERKZEUGE NACHGERUESTET WERDEN.
Das waere eine Behauptung ueber 18 Skripte, die ich nicht einzeln geprueft
habe - und manche brauchen keine: `md5_geschuetzt.py` VERGLEICHT Abdruecke,
der Vergleich ist die Probe. Stattdessen eine Sperrklinke: die Zahlen duerfen
nur FALLEN. Wer ein neues Messwerkzeug ohne Selbstprobe dazulegt, wird rot.

🔴 UND DIE SCHAERFSTE ZAHL IST NICHT DIE GROESSTE. Vier Werkzeuge VERSPRECHEN
im Kopftext eine Selbstprobe und haben im Code keine. Das ist schlimmer als
gar keine: wer den Kopf liest, haelt das Werkzeug fuer abgesichert und glaubt
seiner Null. Eines davon - `tastenkapern_messen.py` - habe ich selbst
geschrieben, samt dem Satz „🔴 SELBSTPROBE: derselbe Lauf muss an einem
Container OHNE inneren Knopf melden, dass der Container reagiert". Der Lauf
tut das nicht; Container ohne inneres Bedienelement werden vorher
aussortiert.
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "scripts"))

import werkzeug_eichung as W  # noqa: E402

# Stand 29.09.2026, im selben Lauf ZWEIMAL nachgezogen:
#  * `tastenkapern_messen.py` hat seine versprochene Selbstprobe bekommen;
#  * 🔴 und der SUCHER war zu streng. Er entfernt Kommentare - richtig -, und
#    dadurch wurde eine Probe unsichtbar, die als schlichtes `if ...: return 2`
#    gebaut ist und nur im Kommentar darueber so heisst. Er hat damit
#    `thema_cssvariablen_messen.py` und `thema_echter_tipp_messen.py`
#    beschuldigt, die es richtig machen. Ein Zaehler, dessen Befunde man
#    verwerfen muss, wird nicht mehr gelesen.
# Die Klinken duerfen nur FALLEN.
ERWARTET_OHNE = 16
ERWARTET_HALB = 2
ERWARTET_VERSPROCHEN = 2


def _zaehlung():
    import io
    voll = halb = 0
    ohne, versprochen = [], []
    for f in W.werkzeuge():
        q = io.open(os.path.join(W.SKRIPTE, f), encoding="utf-8",
                    newline="").read()
        p, a, _formen = W.beurteile(q)
        if p and a:
            voll += 1
        elif p:
            halb += 1
        else:
            ohne.append(f)
            if W.VERSPRECHEN.search(q):
                versprochen.append(f)
    return voll, halb, ohne, versprochen


def test_der_sucher_besteht_seine_eigene_eichung():
    """🔴 Ein Werkzeug, das Eichungen zaehlt und selbst keine hat, waere die
    Pointe des ganzen Befunds."""
    schief = W.eichen()
    assert not schief, (
        "Der Sucher besteht seine eigene Eichung nicht:\n%s"
        % "\n".join("   " + s for s in schief))


def test_die_grundgesamtheit_ist_nicht_leer():
    """🔴 Gegenprobe zur Null. Findet der Namensfilter ueberhaupt Werkzeuge?"""
    n = len(W.werkzeuge())
    assert n >= 40, (
        "Nur %d Messwerkzeuge gefunden, am 29.09. waren es 45.\n"
        "  Entweder ist aufgeraeumt worden - dann gehoeren die Klinken "
        "nachgezogen -,\n  oder der Namensfilter greift daneben und alle "
        "Zahlen unten sind wertlos." % n)


def test_kein_neues_werkzeug_ohne_selbstprobe():
    _v, _h, ohne, _p = _zaehlung()
    assert len(ohne) <= ERWARTET_OHNE, (
        "%d Messwerkzeuge ohne Selbstprobe, gebucht sind hoechstens %d.\n"
        "  Neu dazugekommen: %s\n"
        "  Ein Messwerkzeug ohne Koeder kann seinen eigenen Ausfall nicht "
        "bemerken -\n  es meldet dann eine Null, die von „es gibt "
        "keine“ nicht zu unterscheiden ist.\n"
        "  Muster: `def eichen()` mit Koedern UND Gegenproben, und `return 2` "
        "wenn eine\n  Probe scheitert. Beispiel: scripts/klammerbilanz.py"
        % (len(ohne), ERWARTET_OHNE, sorted(ohne)[-3:]))


def test_keine_neue_probe_die_nur_warnt():
    _v, halb, _o, _p = _zaehlung()
    assert halb <= ERWARTET_HALB, (
        "%d Werkzeuge haben eine Probe, die nur WARNT und weitermacht "
        "(gebucht: %d).\n  Eine Probe ohne Abbruch ist eine Meinung: der "
        "Lauf gibt seine Zahlen trotzdem\n  aus, und im Bericht steht "
        "nachher nicht, dass sie unbeurteilt sind."
        % (halb, ERWARTET_HALB))


def test_kein_neues_versprechen_ohne_deckung():
    """🔴 Die schaerfste der drei Klinken.

    Ein Kopftext, der eine Selbstprobe zusagt, die es nicht gibt, ist
    schlimmer als gar keine Zusage - er macht den Leser sicher.
    """
    _v, _h, _o, versprochen = _zaehlung()
    assert len(versprochen) <= ERWARTET_VERSPROCHEN, (
        "%d Werkzeuge versprechen eine SELBSTPROBE und haben keine "
        "(gebucht: %d):\n%s\n"
        "  Entweder die Probe bauen - oder die Zusage aus dem Kopftext "
        "nehmen. Beides ist\n  ehrlich; sie stehenzulassen ist es nicht."
        % (len(versprochen), ERWARTET_VERSPROCHEN,
           "\n".join("   " + f for f in sorted(versprochen))))


def test_koeder_ein_kommentar_erfuellt_die_pruefung_NICHT():
    """🔴 Die Gegenprobe, ohne die der ganze Riegel wertlos waere.

    Jede der fuenf Schreibweisen kommt in den Kopftexten dieses Hauses
    staendig vor. Wer den ROHEN Text durchsucht, misst seine eigene
    Begruendung mit und meldet jedes Werkzeug als geeicht.
    """
    p, _a, _f = W.beurteile(
        "def main():\n"
        "    # KOEDER: hier waere eine Selbstprobe sinnvoll, siehe eichen()\n"
        "    return 0\n")
    assert not p, (
        "Ein KOMMENTAR ueber die Selbstprobe erfuellt die Pruefung - dann "
        "meldet dieser\n  Riegel jedes Haus-Skript als in Ordnung.")
