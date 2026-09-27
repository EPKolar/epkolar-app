# -*- coding: utf-8 -*-
"""v3.9.959 - das Werkzeug kennt ALLE Schreibweisen, in denen hier Elemente
erzeugt werden. Und es belegt das, statt es zu behaupten.

WARUM ES DIESE DATEI GIBT
─────────────────────────
Am 27.09.2026 hat das Alphabet dreimal an einem Tag zu einem falschen Ergebnis
gefuehrt:

  1. `createElement("h2"` fand **0** Stellen - die Datei schreibt `'h2'` mit
     EINFACHEN Anfuehrungszeichen. Es sind 30.
  2. Ein Riegel suchte `createElement('h2'` und meldete eine gerade gebaute
     Ueberschrift als fehlend: dort steht der lokale Kuerzel `h('h2'`.
  3. Eine Waisensuche meldete DREI nie gerenderte Komponenten, eine davon mit
     35 kB. ZWEI waren falsch - sie werden ueber `h(Name,{...})` erzeugt. Fast
     waere daraus der Schluss geworden, ein ganzes Overlay erscheine nie.

Jedes Mal lautete die Meldung "kommt nicht vor", und das ist von einem echten
Befund nicht zu unterscheiden. Seit v3.9.959 liegt die Suche an EINER Stelle:
`scripts/code_scan.py` mit `element_stellen` und `alle_elementnamen`.

Diese Datei prueft nicht, dass die Funktionen EXISTIEREN - das waere
Anwesenheit. Sie prueft, dass sie jede Form FINDEN und die Nicht-Formen NICHT
mitzaehlen, und sie macht das Muster absichtlich kaputt, um zu zeigen, dass die
Eichung das merkt.
"""
import io
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import code_scan  # noqa: E402

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")


def _roh():
    s = io.open(PFAD, encoding="utf-8", newline="").read()
    if len(s) < 3_000_000:
        raise AssertionError("index.html hat nur %d Bytes - Datenverlust."
                             % len(s))
    return s


def test_die_formen_eichung_besteht():
    """Vier Formen erkannt, drei Nicht-Formen nicht mitgezaehlt."""
    ok, gef, erw = code_scan.eichen_elemente()
    assert ok, (
        "Formen-Eichung gescheitert: %d von %d. Das Muster kennt nicht alle "
        "Schreibweisen oder zaehlt zu viel. Zu VIEL ist bei einer Waisensuche "
        "genauso falsch wie zu wenig: eine Komponente gilt dann als gerendert, "
        "obwohl sie es nicht ist." % (gef, erw))


def test_beide_erzeuger_werden_gefunden():
    """`React.createElement(` UND der Kuerzel `h(` - je an einem echten Fall.

    Nicht an einem gebauten Text: hier wird gemessen, dass die Formen in DIESER
    Datei wirklich beide gefunden werden. `EZKalender` und `FahrtenbuchView`
    werden ueber den Kuerzel erzeugt (Z12271 bzw. Z27781), `PlanViewerCanvas`
    ueber die lange Form (Z18417).
    """
    roh = _roh()
    for name in ("EZKalender", "FahrtenbuchView"):
        st = code_scan.element_stellen(roh, name)
        assert st, (
            "%s wird ueber den Kuerzel h(%s,{...}) erzeugt, die Suche findet "
            "es aber nicht. Dann meldet sie kuenftig wieder 'kommt nicht vor' "
            "fuer eine lebende Komponente." % (name, name))
    st = code_scan.element_stellen(roh, "PlanViewerCanvas")
    assert st, ("PlanViewerCanvas wird ueber React.createElement erzeugt "
                "(Z18417) und wird nicht gefunden.")


def test_beide_anfuehrungszeichen_bei_tags():
    """Ein Tag steht hier in EINFACHEN Anfuehrungszeichen - und das Muster
    darf sich darauf nicht verlassen.

    Gemessen: `h2` kommt 30 mal als Tag vor. Sucht man mit doppelten
    Anfuehrungszeichen, findet man 0 - das war Fehler 1 vom 27.09.
    """
    roh = _roh()
    st = code_scan.element_stellen(roh, "h2", als_tag=True)
    assert len(st) >= 25, (
        "Nur %d h2-Tags gefunden, erwartet um 30. Sinkt die Zahl stark, ist "
        "entweder das Muster kaputt oder es sind Ueberschriften "
        "verlorengegangen - beides gehoert angesehen." % len(st))


def test_ein_lauf_liefert_dasselbe_wie_viele():
    """`alle_elementnamen` (EIN Durchgang) muss zu `element_stellen`
    (je Name) passen.

    Die schnelle Form ist nur dann brauchbar, wenn sie dasselbe sagt. Ein
    Riegel, der von 4 s auf 28 s wuchs, wurde deshalb umgebaut - und ein
    Umbau auf Geschwindigkeit, der das Ergebnis aendert, ist kein Umbau,
    sondern ein neuer Fehler.
    """
    roh = _roh()
    alle = code_scan.alle_elementnamen(roh)
    for name in ("PlanViewerCanvas", "EZKalender", "FahrtenbuchView"):
        einzeln = code_scan.element_stellen(roh, name)
        assert name in alle, (
            "%s fehlt im Ein-Lauf-Ergebnis, wird aber einzeln gefunden "
            "(%d Stellen)." % (name, len(einzeln)))
        assert len(alle[name]) == len(einzeln), (
            "%s: Ein-Lauf sagt %d Stellen, Einzelsuche %d. Die schnelle Form "
            "sagt etwas anderes als die langsame."
            % (name, len(alle[name]), len(einzeln)))
    assert "PlanViewer" not in alle, (
        "PlanViewer erscheint im Ein-Lauf-Ergebnis als erzeugt. Einzeln "
        "gemessen ist es 0 - dann zaehlt der Ein-Lauf zu viel, vermutlich "
        "weil `PlanViewerCanvas` als `PlanViewer` gelesen wird (fehlende "
        "Wortgrenze).")


def test_ein_verkrueppeltes_muster_faellt_bei_der_eichung_auf():
    """KOEDER auf die Eichung selbst.

    Die Eichung ist der einzige Grund, den Zahlen zu trauen. Also wird das
    Muster absichtlich um den Kuerzel beschnitten - genau der Fehler vom
    27.09. - und die Eichung MUSS das melden.
    """
    echt = code_scan._ERZEUGER
    try:
        code_scan._ERZEUGER = r"createElement\(\s*"      # Kuerzel entfernt
        ok, gef, erw = code_scan.eichen_elemente()
        assert not ok, (
            "Die Eichung besteht, obwohl das Muster den Kuerzel `h(` nicht "
            "mehr kennt (%d von %d). Dann ist sie wertlos und haette den "
            "Fehler vom 27.09. durchgelassen." % (gef, erw))
        # Und die Auskunft muss verweigert werden, nicht eine Zahl geliefert.
        with pytest.raises(SystemExit):
            code_scan.element_stellen(_roh(), "EZKalender")
    finally:
        code_scan._ERZEUGER = echt
    # Und danach ist alles wieder in Ordnung - sonst hat diese Probe die
    # folgenden Pruefungen vergiftet.
    assert code_scan.eichen_elemente()[0], (
        "Nach dem Koeder ist das Muster nicht wiederhergestellt. Dann messen "
        "alle folgenden Pruefungen mit einem kaputten Werkzeug.")


def test_ein_zu_weites_muster_faellt_auch_auf():
    """KOEDER in der Gegenrichtung.

    Zu viel zu zaehlen ist bei einer Waisensuche genauso falsch: eine
    Komponente gilt dann als gerendert, obwohl sie es nicht ist. Ein Muster
    ohne die Sperre vor `h` liest `search(` und `.h(` mit - die Eichung muss
    auch das melden.
    """
    echt = code_scan._ERZEUGER
    try:
        code_scan._ERZEUGER = r"(?:createElement|h)\(\s*"   # Sperre entfernt
        ok, gef, erw = code_scan.eichen_elemente()
        assert not ok, (
            "Die Eichung besteht, obwohl das Muster `search('div')` und "
            "`obj.h('div')` mitzaehlt (%d statt %d). Eine Waisensuche wuerde "
            "damit tote Komponenten fuer lebend erklaeren." % (gef, erw))
    finally:
        code_scan._ERZEUGER = echt
    assert code_scan.eichen_elemente()[0]
