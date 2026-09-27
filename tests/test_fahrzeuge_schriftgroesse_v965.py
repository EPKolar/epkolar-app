# -*- coding: utf-8 -*-
"""Keine festen Schriftgroessen unter 12 px in der Fahrzeugansicht.

Punkt 2 des Auftrags: bei 21 Fahrzeugen statt drei sind die kleinen Schriften
der Fahrzeugansicht der groesste Einzelbefund - 39 Stellen bei 390 px, 44 bei
1440 px. Gehoben wurden 113 feste Werte (29 mal 9 px, 40 mal 10 px, 44 mal
11 px) auf UI.fMeta, den untersten Sprossen der Tokenleiter, plus die zwei im
gemeinsamen Bauteil `Kpi`.

🔴 DIE FALLE AUS v3.9.943 IST HIER FESTGEHALTEN: ein Muster `fontSize:[0-9]+`
zerschneidet `fontSize:9.5` zu `UI.fMeta.5`, und node_check meldet dann
'Unexpected number'. Deshalb steht hinter der Zahl ein `(?![\\d.])` - und
deshalb gibt es unten einen Koeder, der genau diese Kommazahl enthaelt.

🔴 WAS DIESER RIEGEL NICHT MISST: die App-Huelle. Nach der Kur bleiben bei
390 px zwei und bei 1440 px sieben Stellen unter 12 px, und alle sitzen in
`header`, `div.bottom-nav` oder dem Sync-Banner - nicht im Inhalt der
Ansicht. Die Huelle traegt jede der 22 Ansichten; sie zu heben ist ein eigener
Schritt mit eigener Messung, so wie es v3.9.943 fuer die 9er und 11er
festgehalten hat. Das hier ist NICHT die Aussage "die Ansicht hat keine
kleinen Schriften mehr" - es ist die Aussage "die Ansicht selbst hat keine".
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import code_scan  # noqa: E402

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")
KLEIN = re.compile(r"fontSize\s*:\s*(\d+(?:\.\d+)?)(?![\d.])")


def _lies():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _spanne(text, name):
    feld = code_scan.ist_code(text)
    a = text.index("function %s(" % name)
    b = min(m.start() for m in re.finditer(r"function\s+[A-Z]\w+\s*\(", text)
            if feld[m.start()] and m.start() > a)
    return a, b


def kleine_schriften(abschnitt):
    return [m.group(1) for m in KLEIN.finditer(abschnitt)
            if float(m.group(1)) < 12]


def test_fahrzeugansicht_ohne_schrift_unter_12px():
    text = _lies()
    a, b = _spanne(text, "FahrzeugView")
    # Gegenprobe zur Grundgesamtheit: der Abschnitt muss ueberhaupt
    # Schriftgroessen fuehren, sonst ist die Null unten geschenkt.
    alle = KLEIN.findall(text[a:b])
    assert len(alle) > 60, (
        "\U0001F534 Nur %d feste Schriftgroessen in FahrzeugView - die Spanne "
        "stimmt nicht,\n  und eine leere Grundgesamtheit meldet immer gruen."
        % len(alle))
    fund = kleine_schriften(text[a:b])
    assert not fund, (
        "\U0001F534 %d feste Schriftgroessen unter 12 px in der "
        "Fahrzeugansicht: %s\n"
        "  Bei 21 Fahrzeugen war das der groesste Einzelbefund der Ansicht "
        "(39 Stellen bei 390 px).\n"
        "  Der unterste Sprossen der Leiter ist UI.fMeta (12)."
        % (len(fund), sorted(set(fund))))


def test_kpi_kachel_ohne_schrift_unter_12px():
    """Die vier Kennzahl-Kacheln kamen aus einem GEMEINSAMEN Bauteil.

    Sie waren nicht unter den 113 Stellen der Ansicht und blieben nach dem
    ersten Griff als einzige vier uebrig - `Kpi` wird an 50 Stellen benutzt.
    """
    text = _lies()
    feld = code_scan.ist_code(text)
    a = text.index("function Kpi(")
    b = min(m.start() for m in re.finditer(r"function\s+[A-Za-z_]\w*\s*\(", text)
            if feld[m.start()] and m.start() > a)
    fund = kleine_schriften(text[a:b])
    assert not fund, (
        "\U0001F534 Die Kennzahl-Kachel fuehrt wieder Schrift unter 12 px: %s\n"
        "  Sie wird an rund 50 Stellen benutzt - das schlaegt auf mehrere "
        "Ansichten durch." % fund)


def test_das_raster_laesst_keine_waisenkachel():
    """Bei 390 px ergaben 100 px drei Spalten und eine Kachel allein in Zeile 2.

    Gemessen am 27.09.2026: drei Kacheln bei y=379, "Service faellig" allein
    bei y=515. 160 px ergibt 2x2 - dieselbe Zeilenzahl, aber 183 statt 119 px
    breite Kacheln.
    """
    text = _lies()
    a, b = _spanne(text, "FahrzeugView")
    seg = text[a:b]
    assert 'minmax(100px,1fr)' not in seg, (
        "\U0001F534 Das Kennzahlraster steht wieder auf 100 px - bei 390 px "
        "gibt das drei\n  Spalten und eine Waisenkachel."
    )
    assert 'minmax(160px,1fr)' in seg, (
        "\U0001F534 Das Kennzahlraster der Fahrzeugansicht ist nicht mehr "
        "auffindbar."
    )


def test_koeder_neun_px():
    """Ein 9-px-Wert MUSS gemeldet werden."""
    assert kleine_schriften('h("div",{style:{fontSize:9}},"x")') == ["9"]
    assert kleine_schriften('h("div",{style:{fontSize: 11}},"x")') == ["11"]


def test_koeder_kommazahl_wird_nicht_zerschnitten():
    """\U0001F534 Der Fehler aus v3.9.943, als Probe festgehalten.

    `fontSize:9.5` ist kleiner als 12 und gehoert gemeldet - aber als "9.5",
    nicht als "9". Ein Muster ohne `(?![\\d.])` liest hier eine 9 und laesst
    das ".5" stehen; beim Ersetzen wurde daraus `UI.fMeta.5` und node_check
    meldete 'Unexpected number'.
    """
    assert kleine_schriften('h("div",{style:{fontSize:9.5}},"x")') == ["9.5"]
    assert kleine_schriften('h("div",{style:{fontSize:12.5}},"x")') == []


def test_gegenprobe_zwoelf_und_token_schweigen():
    """12 px und die Token duerfen NICHT gemeldet werden."""
    for fall in ('h("div",{style:{fontSize:12}},"x")',
                 'h("div",{style:{fontSize:14}},"x")',
                 'h("div",{style:{fontSize:UI.fMeta}},"x")',
                 'h("div",{style:{fontSize:UI.fKlein}},"x")'):
        assert not kleine_schriften(fall), (
            "\U0001F534 %s wurde gemeldet - der Riegel meldet dann alles." % fall)
