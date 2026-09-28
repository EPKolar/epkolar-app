# -*- coding: utf-8 -*-
"""Das Ringdiagramm zeichnet ALLE Legendenzeilen, nicht nur acht.

WAS FALSCH WAR - nachgerechnet, nicht uebernommen.
`SvgPie` hatte eine viewBox der Hoehe `size` mit size=150 (beide Aufrufer
nutzen die Vorgabe). Legendenzeile i sitzt bei y=i*18+16, ihr Farbraehmchen
bei y=i*18+8 mit height 9, unterer Rand also i*18+17.

    sichtbar solange  i*18+17 <= 150  ->  i <= 7,39  ->  ACHT Zeilen

Ab der neunten lag die Zeile ausserhalb der viewBox und wurde nie gezeichnet.
Gemessen: absTyp verliert 7 von 15 Eintraegen, asArt 1 von 9.

Das ist FEHLENDE Information, nicht kleine. Keine Schriftgroesse behebt es, und
niemand sieht, dass etwas fehlt - es steht ja nichts da.
"""
import io
import os
import re

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PFAD = os.path.join(WURZEL, "index.html")


def _rumpf():
    t = io.open(PFAD, encoding="utf-8", newline="").read()
    i = t.index("function SvgPie(")
    j = t.index("function SvgLine(", i)
    return t[i:j]


def test_die_viewbox_waechst_mit_der_legende():
    r = _rumpf()
    assert "Math.max(size, data.length*18+12)" in r, (
        "Die viewBox-Hoehe haengt nicht mehr an der Zahl der Eintraege.\n"
        "  Bei einer festen Hoehe von 150 verschwindet alles ab der neunten "
        "Legendenzeile -\n"
        "  lautlos, weil dort dann einfach nichts steht.")


def test_die_rechnung_dahinter_stimmt_noch():
    """Der Riegel rechnet die Geometrie NACH, statt sie zu glauben.

    Aendert jemand den Zeilenabstand oder den Anfangsversatz, ohne die
    viewBox-Formel mitzuziehen, faellt es hier auf - und nicht erst, wenn eine
    Auswertung Eintraege verliert.
    """
    r = _rumpf()
    m_y = re.search(r"y:\s*i\*(\d+)\+(\d+),\s*fill:\s*V\.dm", r)
    assert m_y, ("Die Legendenzeile ist nicht mehr auffindbar - der Riegel "
                 "misst dann nichts.")
    abstand, versatz = int(m_y.group(1)), int(m_y.group(2))
    m_f = re.search(r"data\.length\*(\d+)\+(\d+)", r)
    assert m_f, "Die viewBox-Formel ist nicht auffindbar."
    f_abstand, f_zugabe = int(m_f.group(1)), int(m_f.group(2))
    assert f_abstand == abstand, (
        "Die viewBox rechnet mit Abstand %d, die Legende zeichnet mit %d.\n"
        "  Dann passt die Hoehe wieder nicht." % (f_abstand, abstand))
    assert f_zugabe >= versatz + 1 - abstand, (
        "Die Zugabe (%d) ist zu klein fuer den Versatz (%d) bei Abstand %d -\n"
        "  die letzte Zeile ragt wieder hinaus."
        % (f_zugabe, versatz, abstand))


def test_koeder_die_alte_geometrie_haette_acht_zeilen_gezeigt():
    """Die Rechnung, die den Befund belegt - als Probe festgehalten.

    Ohne sie waere die alte Hoehe eine Zahl ohne Bedeutung, und beim naechsten
    Umbau setzt sie jemand zurueck, weil niemand mehr weiss, warum sie weg ist.
    """
    size, abstand, versatz = 150, 18, 16
    sichtbar = sum(1 for i in range(30) if i * abstand + versatz + 1 <= size)
    assert sichtbar == 8, (
        "Die Rechnung ergibt %d sichtbare Zeilen statt acht - dann stimmt der "
        "aufgeschriebene Befund nicht mehr." % sichtbar)
    for n in (9, 15, 30):
        hoehe = max(size, n * abstand + 12)
        assert (n - 1) * abstand + versatz + 1 <= hoehe, (
            "Bei %d Eintraegen ragt die letzte Zeile heraus." % n)
