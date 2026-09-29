# -*- coding: utf-8 -*-
"""Die Klammern von index.html gehen auf - zustandsbasiert gemessen.

🔴 FRAGE 15, und sie ist nicht beantwortet worden, sondern GEMESSEN.

`scripts/_bracket_check.py` streicht mit einer Reihe regulaerer Ausdruecke,
und das Vorlagenliteral-Muster steht VOR dem Kommentarmuster. Diese Datei
zitiert in Kommentaren mit Backticks - jeder einzelne wird als ENDE eines
viel frueher geoeffneten Literals gelesen. Ergebnis am heilen Stand:

    beurteilt   27,9 % der Datei
    Grundlinie  () -1

`scripts/klammerbilanz.py` stellt dieselbe Frage mit `code_scan.ist_code` -
demselben zustandsbasierten Abtaster, der schon fuenf andere Riegel traegt
und eine Eichprobe bestehen muss:

    beurteilt   54,9 % der Datei
    Bilanz      () 0 / [] 0 / {} 0, und keine Kreuzung

🔴 DIE ALTE GRUNDLINIE WAR EIN ARTEFAKT, und das ist jetzt lueckenlos
nachgerechnet. Der Kopftext von `_bracket_check.py` behauptet seit dem
18.05.2026 das Gegenteil: *"investigated ... and confirmed it is NOT a
stripper artifact ... The drift is a real, stable code-level imbalance"*.
Gegengerechnet:

    alte Maske, Netto ()                     -1
    neue Maske, Netto ()                      0
    NUR vom alten Tor gezaehlt, Netto ()      0
    NUR vom neuen Tor gezaehlt, Netto ()     +1

Das `-1` ist also das Spiegelbild eines `+1`, das in der EIGENEN blinden Zone
des alten Tors liegt. Bei richtiger Zerlegung verschwinden beide.

🔴 UND DAS ENTSCHEIDENDE ARGUMENT IST NICHT DIE SCHOENERE ZAHL. Ein Tor
auszutauschen, weil die neue Zahl gefaelliger aussieht, ist dieselbe Bewegung
wie eine Pruefung anzupassen, damit sie gruen wird. Das Argument ist, dass
das neue Tor einen Fehler findet, den das alte nicht findet - belegt an
`index.html` selbst (`scripts/klammertor_vergleich.py`): eine einzelne
unpaarige `(` in echten Code bei Zeile 11380 gesetzt ->

    altes Tor  Rueckgabe 0   () -1 / {} 0 / [] 0     GRUEN
    neues Tor  Rueckgabe 1   nennt Zeile und Umgebung

Das alte Tor bleibt trotzdem in der Kette: `test_klammertor_blindheit_v956`
misst es und haelt seine Blindheit fest, damit sie nicht weiter waechst. Es
kommt ein Tor DAZU, es wird keines ersetzt.
"""
import io
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "scripts"))

import klammerbilanz as KB  # noqa: E402

PFAD = os.path.join(HIER, "..", "index.html")
# Der alte Streicher beurteilt 27,9 %. Weniger als die Haelfte waere keine
# Verbesserung mehr - dann misst der neue Abtaster nicht mehr, was er soll.
MINDESTANTEIL = 50.0


def _text():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def test_die_eichung_besteht():
    """🔴 Sechs Proben, darunter die zum Backtick im Kommentar.

    Ohne sie waere die Null unten von der Null eines kaputten Abtasters nicht
    zu unterscheiden - und genau so ist der alte gescheitert.
    """
    schief = KB.eichen()
    assert not schief, (
        "Der Abtaster besteht seine eigene Eichung nicht:\n%s"
        % "\n".join("   " + s for s in schief))


def test_es_wird_genug_beurteilt():
    """🔴 Gegenprobe zur Null: eine Maske, die fast nichts als Code fuehrt,
    meldet immer eine saubere Bilanz."""
    text = _text()
    aus, _v = KB.maske(text)
    anteil = 100.0 * sum(aus) / len(text)
    assert anteil >= MINDESTANTEIL, (
        "Nur %.1f %% von index.html werden als Code beurteilt, verlangt sind "
        "%.1f %%.\n  Eine Bilanz ueber zu wenig Text ist keine Bilanz - der "
        "alte Streicher hat\n  mit 27,9 %% jahrelang eine Zahl gemeldet, die "
        "nichts bedeutete." % (anteil, MINDESTANTEIL))


def test_jede_klammer_hat_ihren_partner():
    text = _text()
    zahl, fehler = KB.bilanz(text)
    assert not fehler, (
        "%d unpaarige Klammern:\n%s"
        % (len(fehler),
           "\n".join("   Zeile %d: %r %s"
                     % (text.count("\n", 0, i) + 1, c, g)
                     for i, c, g in fehler[:10])))
    assert all(v == 0 for v in zahl.values()), (
        "Die Bilanz geht nicht auf: %r.\n  Der Stapel hat trotzdem nichts "
        "gefunden - dann rechnen Zaehlung und Stapel\n  verschieden, und "
        "eine der beiden ist kaputt." % zahl)


def test_koeder_eine_einzelne_klammer_im_ECHTEN_text_wird_gefunden():
    """🔴 Mutationsprobe im Speicher, an der echten Datei.

    Nicht an einem Kunsttext: dass ein Abtaster `(1;` findet, sagt nichts
    darueber, ob er es in 3,7 MB mit 561 Vorlagen-Einbettungen und
    Regex-Literalen auch tut. Die Datei wird dabei NICHT angefasst.
    """
    text = _text()
    aus, _v = KB.maske(text)
    # Eine Stelle, die der Abtaster als Code fuehrt, moeglichst weit hinten -
    # dort steht der Grossteil der Bauteile.
    stelle = -1
    for i in range(len(text) - 3, len(text) // 2, -1):
        if text[i] == ";" and aus[i]:
            stelle = i + 1
            break
    assert stelle > 0, ("Keine Code-Stelle zum Setzen des Koeders gefunden - "
                        "dann misst diese Probe nichts.")
    kaputt = text[:stelle] + "(" + text[stelle:]
    zahl, fehler = KB.bilanz(kaputt)
    assert fehler, (
        "Eine zusaetzliche `(` in echtem Code bei Zeile %d wird NICHT "
        "gefunden.\n  Dann ist die Null der anderen Pruefung wertlos."
        % (text.count("\n", 0, stelle) + 1))
    assert zahl["("] == 1, (
        "Die Zaehlung meldet %d statt 1 nach einer einzelnen zusaetzlichen "
        "Klammer." % zahl["("])


def test_koeder_ein_backtick_im_kommentar_bewegt_nichts():
    """🔴 Genau der Fehler, an dem das alte Tor gescheitert ist.

    Ein Backtick in einem Blockkommentar hat dort `() -4` statt `() -1`
    gemeldet - ohne dass am Quelltext etwas falsch war.
    """
    text = _text()
    vorher, _f = KB.bilanz(text)
    marke = "\n/* zitiert `foo` und `bar` so */\n"
    mit = text[:200] + marke + text[200:]
    nachher, fehler = KB.bilanz(mit)
    assert vorher == nachher and not fehler, (
        "Ein Backtick im Kommentar bewegt die Bilanz: %r -> %r (%d "
        "unpaarige).\n  Dann macht der neue Abtaster denselben Fehler wie "
        "der alte, er sieht nur\n  anders aus." % (vorher, nachher,
                                                   len(fehler)))
