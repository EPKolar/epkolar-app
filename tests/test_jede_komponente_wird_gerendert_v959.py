# -*- coding: utf-8 -*-
"""v3.9.959 - genau EINE Komponente wird nie gerendert, und sie ist benannt.

WOZU
────
Eine deklarierte Ansicht, die niemand mehr erzeugt, ist eine Flaeche, die
niemand messen kann: keine Sonde faehrt sie an, kein Riegel sieht sie, und ein
Fehler darin faellt erst auf, wenn sie eines Tages wieder eingehaengt wird. In
der Sitzung vom 26./27.09.2026 ist zweimal ein Befund an genau dieser Frage
haengengeblieben.

Gemessen an v3.9.959: **95** Komponenten (`function` mit grossem
Anfangsbuchstaben), davon wird **eine** nie als Element erzeugt:

    PlanViewer   Z17077   9.651 Bytes   -> createElement(PlanViewer 0 mal

Das ist bekannt und richtig dokumentiert: der Kommentar in `PlanViewerCanvas`
sagt es selbst, und gezeichnet wird `PlanViewerCanvas`.

🔴 GELOESCHT WIRD NICHTS. Die Hausregel lautet "parken, nicht loeschen" -
`test_finkzeit_standby_v3991.py::test_code_parked_not_deleted` haelt das
ausdruecklich fest. Dieser Riegel schuetzt nicht davor, dass toter Code
LIEGENBLEIBT, sondern davor, dass unbemerkt NEUER dazukommt.

🔴 WARUM DIESE DATEI ZWEI SCHREIBWEISEN KENNT - ein eigener Messfehler
──────────────────────────────────────────────────────────────────────
Die erste Messung suchte nur `createElement(Name` und `<Name` und meldete
DREI nie gerenderte Komponenten: `EZKalender`, `PlanViewer`,
`FahrtenbuchView` - 35 kB davon. Bei `FahrtenbuchView` waere daraus fast der
Schluss geworden, das Fahrtenbuch-Overlay erscheine ueberhaupt nicht.

Gemessen war das Gegenteil: beide werden ueber den lokalen Kuerzel erzeugt -
`h(EZKalender,{...})` in Z12271 und `h(FahrtenbuchView,{...})` in Z27781, wobei
`const h=React.createElement` im Rumpf steht. **Zwei von drei Meldungen waren
falsch, weil der Zaehler eine Schreibweise nicht kannte.** Dieselbe Form wie
beim h2-Riegel eine Stufe vorher: ein Muster, das eine Schreibweise nicht
kennt, meldet "kommt nicht vor" - und das sieht aus wie ein Befund.

Deshalb zaehlt diese Datei BEIDE Formen, und der Koeder unten belegt fuer JEDE
einzeln, dass sie erkannt wird.

WAS DIESE DATEI NICHT MISST
───────────────────────────
Ob eine gerenderte Komponente auch tatsaechlich auf den Schirm kommt - das
haengt an Bedingungen, Rechten und Daten (siehe die Regel "Wegriegel": ein
Bauteil-Riegel findet nicht, dass das Bauteil nie erreicht wird). Gemessen
wird nur: es gibt eine Stelle, die dieses Element erzeugt.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import code_scan  # noqa: E402

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")

# Namentlich, mit Grund - keine Obergrenze. Eine Zahl allein unterscheidet
# nicht, ob eine bekannte Waise verschwindet und eine neue dazukommt.
BEKANNTE_WAISEN = {
    "PlanViewer":
        "9.651 B, Z17077. Gezeichnet wird PlanViewerCanvas; der Kommentar "
        "dort sagt es selbst und stimmt. Bleibt liegen - Hausregel "
        "\"parken, nicht loeschen\".",
}


def _lies():
    roh = io.open(PFAD, encoding="utf-8", newline="").read()
    if len(roh) < 3_000_000:
        raise AssertionError(
            "index.html hat nur %d Bytes - Datenverlust. Eine leere Datei hat "
            "keine Komponenten und damit auch keine Waisen." % len(roh))
    return roh


# `ist_code` laeuft ueber 3,6 MB und wurde von jeder Pruefung neu gerufen -
# die Datei brauchte dadurch 29 s. Gemerkt wird nach Textlaenge UND md5, damit
# ein geaenderter Text (die Koeder-Fassungen) NICHT den Eintrag des heilen
# Stands bekommt: ein Zwischenspeicher, der den falschen Wert liefert, waere
# schlimmer als der langsame Lauf.
_FELD_CACHE = {}


def _feld(text):
    import hashlib
    k = (len(text), hashlib.md5(text.encode("utf-8")).hexdigest())
    if k in _FELD_CACHE:
        return _FELD_CACHE[k]
    ok, gef, erw = code_scan.eichen(text)
    assert ok, (
        "code_scan-Eichung gescheitert (%d von %d). Der Abtaster irrt, also "
        "sind alle Zahlen dieser Datei ohne Wert - er findet dann zu WENIG, "
        "und das sieht wie eine Waise aus." % (gef, erw))
    feld = code_scan.ist_code(text)
    _FELD_CACHE[k] = feld
    return feld


def _komponenten(text, feld):
    aus = {}
    for m in re.finditer(r"function\s+([A-Z]\w+)\s*\(", text):
        if feld[m.start()]:
            aus.setdefault(m.group(1), m.start())
    return aus


def _renderstellen(text, feld, name):
    """BEIDE Schreibweisen: React.createElement(Name UND h(Name.

    Das `(?<![A-Za-z0-9_$.])` vor dem h verhindert, dass `search(`, `_ch(`
    oder `.h(` als Aufruf des Kuerzels gelesen werden.
    """
    n = re.escape(name)
    muster = (r"createElement\(\s*" + n + r"\b"
              r"|(?<![A-Za-z0-9_$.])h\(\s*" + n + r"\b"
              r"|<" + n + r"\b")
    return [m.start() for m in re.finditer(muster, text) if feld[m.start()]]


# EIN Durchgang fuer alle Namen. Die erste Fassung rief `_renderstellen` je
# Komponente - 95 Regex-Laeufe ueber 3,6 MB, 28 s fuer diese Datei. Ein Riegel,
# der die Kette messbar verlangsamt, wird irgendwann uebersprungen; dann misst
# er nichts mehr.
_GERENDERT = re.compile(
    r"(?:createElement|(?<![A-Za-z0-9_$.])h)\(\s*([A-Z]\w+)\b"
    r"|<([A-Z]\w+)\b")


def _gerenderte_namen(text, feld):
    aus = set()
    for m in _GERENDERT.finditer(text):
        if feld[m.start()]:
            aus.add(m.group(1) or m.group(2))
    return aus


def _waisen(text):
    feld = _feld(text)
    komp = _komponenten(text, feld)
    assert len(komp) > 30, (
        "Nur %d Komponenten gefunden. Das ist kein gruenes Ergebnis - die "
        "Datei fuehrt um 95. Entweder irrt der Zaehler, oder die Deklarationen "
        "sind anders geschrieben." % len(komp))
    erzeugt = _gerenderte_namen(text, feld)
    return {n: text.count("\n", 0, p) + 1
            for n, p in komp.items() if n not in erzeugt}, len(komp)


def test_keine_neue_waise():
    """Genau die benannten Komponenten werden nie gerendert."""
    roh = _lies()
    waisen, gesamt = _waisen(roh)
    neu = {n: z for n, z in waisen.items() if n not in BEKANNTE_WAISEN}
    weg = [n for n in BEKANNTE_WAISEN if n not in waisen]
    assert not neu, (
        "%d von %d Komponenten werden NEU nie mehr als Element erzeugt:\n%s\n\n"
        "Eine Ansicht, die niemand erzeugt, kann keine Sonde anfahren und kein "
        "Riegel sehen - ein Fehler darin faellt erst auf, wenn sie wieder "
        "eingehaengt wird.\n"
        "Ist das gewollt (Ansicht geparkt): hier mit Grund eintragen. Ist es "
        "ein Versehen: die Renderstelle ist verlorengegangen.\n"
        "Und zuerst pruefen, ob sie ueber den Kuerzel erzeugt wird - "
        "h(Name,{...}) statt React.createElement(Name,{...}). Genau daran hat "
        "sich die erste Fassung dieser Messung zweimal geirrt."
        % (len(neu), gesamt,
           "\n".join("  %-26s Z%d" % (n, z) for n, z in sorted(neu.items()))))
    assert not weg, (
        "Diese bekannten Waisen werden jetzt gerendert: %s.\n"
        "Das ist keine Verschlechterung - aber der Eintrag in BEKANNTE_WAISEN "
        "gehoert dann WEG, samt seiner Begruendung. Eine Ausnahme, deren "
        "Anlass verschwunden ist, erlaubt beim naechsten Mal einen echten "
        "Fehler." % ", ".join(weg))


def test_der_zaehler_kennt_BEIDE_schreibweisen():
    """KOEDER, je Schreibweise einzeln.

    Die erste Fassung kannte `h(Name` nicht und meldete zwei lebende
    Komponenten als Waisen - 35 kB davon. Ein Zaehler, der eine Schreibweise
    nicht kennt, meldet "kommt nicht vor", und das sieht aus wie ein Befund.
    """
    roh = _lies()
    feld = _feld(roh)
    # Zwei Komponenten, von denen bekannt ist, WIE sie erzeugt werden.
    faelle = [
        ("EZKalender", "h("),               # h(EZKalender,{...}) in Z12271
        ("FahrtenbuchView", "h("),          # h(FahrtenbuchView,{...}) Z27781
        ("PlanViewerCanvas", "createElement("),
    ]
    for name, form in faelle:
        st = _renderstellen(roh, feld, name)
        assert st, (
            "KOEDER AUSGEFALLEN: %s wird nachweislich ueber %s%s erzeugt, "
            "diese Messung findet es aber nicht. Dann waere jede gemeldete "
            "Waise wertlos." % (name, form, name))


def test_der_riegel_wird_bei_einer_neuen_waise_rot():
    """KOEDER auf die Aussage selbst.

    Der Riegel SUCHT Waisen und meldet gruen, wenn er keine findet. Also wird
    einer lebenden Komponente die Renderstelle genommen - sie MUSS dann als
    Waise erscheinen.
    """
    roh = _lies()
    anker = "h(EZKalender,{"
    assert anker in roh, (
        "Der Anker fuer den Koeder ist weg. Dann gehoert der Koeder an eine "
        "andere gerenderte Komponente - nicht weggelassen.")
    kaputt = roh.replace(anker, "h(XKalenderX,{", 1)
    waisen, _ = _waisen(kaputt)
    assert "EZKalender" in waisen, (
        "KOEDER NICHT GEFUNDEN: nach dem Entfernen der einzigen Renderstelle "
        "von EZKalender meldet der Riegel keine Waise. Er ist blind.")
