# -*- coding: utf-8 -*-
"""`safe_edit.schneide` schneidet nicht mehr beliebig weit.

🔴 DER BEINAHE-UNFALL, 28.09.2026
Ich wollte im Ringdiagramm EINE Eigenschaft aendern und habe den Anker mit
`schneide` aus der Datei geholt - richtig so, getippte Anker sind die
haeufigste Fehlerquelle. Als Endmarker nahm ich einen Backtick. Der naechste
Backtick stand **zweitausend Zeichen weiter**, mitten in der uebernaechsten
Funktion. Der Schnitt nahm alles mit.

Und dann kommt der Teil, der wehtut: **`ersetze` hat nichts gemerkt.** Es
schuetzt vor MEHRDEUTIGEN Ankern - ein zu weit geschnittener Anker ist aber
gerade eindeutig. Es fand ihn genau einmal und schrieb ihn pflichtgemaess weg.
`SvgLine` war geloescht.

Gefangen hat es `node_check`, nicht das Sicherheitswerkzeug. Nichts war
committet, `git checkout -- index.html` hat es zurueckgeholt.

Die Lehre steht jetzt IM WERKZEUG: ein Schnitt ueber 1200 Zeichen ist fast
immer ein zu weiter Endmarker und wird abgelehnt. Wer wirklich mehr braucht,
sagt es mit `hoechstens=`.
"""
import io
import os
import sys
import tempfile

import pytest

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WURZEL, "scripts"))
import safe_edit  # noqa: E402


def _datei(inhalt):
    d = tempfile.mkdtemp()
    p = os.path.join(d, "probe.js")
    io.open(p, "w", encoding="utf-8", newline="").write(inhalt)
    return p


def test_ein_kurzer_schnitt_geht_durch():
    p = _datei("const a=1;\nfunction f(){return `x`;}\nconst b=2;\n")
    stueck = safe_edit.schneide(p, "function f(){", "}")
    assert stueck == "function f(){return `x`;}", stueck


def test_ein_zu_gieriger_schnitt_wird_ABGELEHNT():
    """\U0001F534 Genau der Fall, der `SvgLine` beinahe geloescht haette."""
    # Der Anfang traegt KEINEN Backtick - der naechste steht erst rund 2400
    # Zeichen weiter. Genau die Lage, die den Unfall erzeugt hat.
    inhalt = ("const a=start;\n"
              + "// Fuellung\n" * 200
              + "const b=`zweiter`;\n")
    p = _datei(inhalt)
    with pytest.raises(SystemExit) as e:
        safe_edit.schneide(p, "const a=start", "`")
    text = str(e.value)
    assert "Grenze" in text and "Endmarker" in text, text
    assert "SvgLine" in text, (
        "\U0001F534 Die Meldung nennt den Anlassfall nicht mehr. Eine Grenze "
        "ohne ihre\n  Geschichte wird beim naechsten Mal einfach hochgesetzt.")


def test_die_grenze_laesst_sich_bewusst_heben():
    """Wer wirklich viel braucht, soll es sagen koennen - aber sagen muessen."""
    inhalt = ("const a=start;\n" + "// Fuellung\n" * 200
              + "const b=`zweiter`;\n")
    p = _datei(inhalt)
    stueck = safe_edit.schneide(p, "const a=start", "`", hoechstens=99999)
    assert len(stueck) > 1200


def test_die_grenze_ist_nicht_wegdefiniert():
    """\U0001F534 Die Gegenprobe gegen die billigste Reparatur.

    Eine Grenze, die auf eine Million gesetzt wird, ist keine. Dieser Riegel
    haelt den Vorgabewert fest - wer ihn aendert, muss hier vorbei.
    """
    assert safe_edit.HOECHSTENS == 1200, (
        "\U0001F534 Die Vorgabegrenze steht auf %d statt 1200. Wenn das "
        "Absicht ist, gehoert\n  die Begruendung in den Kopf von `schneide` - "
        "und die Zahl hierher."
        % safe_edit.HOECHSTENS)


def test_ersetze_schuetzt_weiterhin_vor_mehrdeutigen_ankern():
    """Die alte Zusicherung bleibt - die neue tritt DANEBEN, nicht an ihre
    Stelle."""
    p = _datei("x=1;\nx=1;\n")
    with pytest.raises(SystemExit):
        safe_edit.ersetze(p, [("x=1;", "x=2;", "mehrdeutig")], min_bytes=0)
