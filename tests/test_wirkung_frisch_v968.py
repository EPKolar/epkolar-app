# -*- coding: utf-8 -*-
"""Die Wirkungsmessung ist nicht aelter als die Schriftquellen.

🔴 WORUM ES GEHT
`test_css_boden_12px_v966.py` liest den QUELLTEXT. Es hat sich zweimal
gezeigt, dass das in beide Richtungen zu wenig ist:

  * Zu WENIG: was inline auf 12 px steht, kann der Browser auf 10 px
    ausrechnen, wenn eine Regel mit `!important` daruebersteht. Genau so sah
    die Arbeitsscheinliste nach v3.9.965 aus - Quelltext sauber, Schirm nicht.
  * Zu VIEL: drei der neun in v3.9.966 gehobenen Regeln treffen ueberhaupt
    kein Bauteil. An denen ist der Quelltextriegel gruen - und war es auch,
    als sie noch 11 px trugen.

`scripts/schriftgroesse_wirkung.py` misst deshalb die BERECHNETE Groesse am
gerenderten Baum und legt ihr Ergebnis in `docs/befunde/WIRKUNG_SCHRIFT.json`
ab. Dieser Riegel haelt fest, dass dieses Ergebnis noch zum Code passt.

🔴 DIE KLINKE HAENGT AN EINEM ABDRUCK DER SCHRIFTQUELLEN, NICHT AN DER
VERSIONSNUMMER. Sonst muesste nach jeder unbeteiligten Aenderung ein
Browserlauf von Minuten gefahren werden - und ein Riegel, der die Kette
messbar bremst, wird irgendwann uebersprungen. Ein uebersprungener Riegel
meldet gruen, ohne zu messen.
Der Abdruck deckt genau das ab, was die berechnete Groesse veraendern kann:
alle CSS-Quellen (samt der Laufzeit-Quelle `GCSS()`) und jede
Inline-Schriftangabe.
"""
import importlib.util
import io
import json
import os

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BERICHT = os.path.join(WURZEL, "docs", "befunde", "WIRKUNG_SCHRIFT.json")
WERKZEUG = os.path.join(WURZEL, "scripts", "schriftgroesse_wirkung.py")


def _werkzeug():
    sp = importlib.util.spec_from_file_location("_wirkung", WERKZEUG)
    mod = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(mod)
    return mod


def _bericht():
    return json.loads(io.open(BERICHT, encoding="utf-8", newline="").read())


def test_es_gibt_ueberhaupt_eine_wirkungsmessung():
    assert os.path.exists(WERKZEUG), (
        "\U0001F534 `scripts/schriftgroesse_wirkung.py` fehlt. Ohne sie "
        "behauptet der\n  Quelltextriegel eine Wirkung, die er nicht misst.")
    assert os.path.exists(BERICHT), (
        "\U0001F534 `docs/befunde/WIRKUNG_SCHRIFT.json` fehlt - es ist nie "
        "gemessen worden.\n  Lauf: python scripts/schriftgroesse_wirkung.py")


def test_die_messung_passt_noch_zu_den_schriftquellen():
    """Die eigentliche Klinke."""
    b = _bericht()
    jetzt = _werkzeug().fingerabdruck()
    alt = b.get("abdruck") or {}
    assert alt.get("md5") == jetzt["md5"], (
        "\U0001F534 Die Wirkungsmessung ist aelter als die Schriftquellen.\n"
        "  gemessen an v%s (%s): %d Zeichen CSS, %d Inline-Angaben\n"
        "  jetzt im Code   : %d Zeichen CSS, %d Inline-Angaben\n"
        "  Es ist etwas an den Schriften geaendert worden, ohne die WIRKUNG "
        "nachzumessen.\n"
        "  Der Quelltextriegel kann das nicht sehen - genau deshalb gibt es "
        "diese Klinke.\n"
        "  Lauf: python scripts/schriftgroesse_wirkung.py"
        % (b.get("version"), b.get("gemessen_am"),
           alt.get("css_zeichen", -1), alt.get("inline_angaben", -1),
           jetzt["css_zeichen"], jetzt["inline_angaben"]))


def test_die_messung_hat_ueberhaupt_etwas_gesehen():
    """Gegenprobe auf die Grundgesamtheit.

    Eine Messung ueber null Aufnahmen meldet null Stellen - und das sieht aus
    wie ein makelloses Ergebnis.
    """
    b = _bericht()
    a = b.get("aufnahmen") or []
    assert len(a) >= 6, (
        "\U0001F534 Nur %d Aufnahmen im Bericht. Erwartet sind mindestens "
        "sechs (drei\n  Ansichten mal zwei Breiten) - sonst ist jede Zahl "
        "darin geschenkt." % len(a))
    assert any(x.get("anzahl", 0) > 0 for x in a), (
        "\U0001F534 KEINE einzige Aufnahme hat eine Stelle unter 12 px "
        "gefunden.\n"
        "  Das ist zu gut: die App-Huelle traegt in jeder Ansicht welche. "
        "Vermutlich hat\n"
        "  der Melder nichts gesehen statt nichts gefunden.")


def test_keine_inline_angabe_wird_mehr_uebersteuert():
    """\U0001F534 Die Krankheit selbst, als Zahl.

    „Uebersteuert" heisst: inline steht 12 px oder mehr, berechnet kommt
    weniger heraus. Das ist die Form, an der v3.9.965 gruen war und der
    Schirm nicht. Nach der CSS-Kur aus v3.9.966 ist die Zahl 0 - und sie soll
    0 bleiben.
    """
    b = _bericht()
    n = b.get("summe_uebersteuert")
    assert n == 0, (
        "\U0001F534 %d Stellen tragen inline 12 px oder mehr und werden "
        "kleiner ausgerechnet.\n"
        "  Eine Regel mit !important uebersteuert jede Inline-Angabe. "
        "Beispiele:\n    %s"
        % (n, [x.get("uebersteuert_beispiele")
               for x in (b.get("aufnahmen") or []) if x.get("uebersteuert")]))
