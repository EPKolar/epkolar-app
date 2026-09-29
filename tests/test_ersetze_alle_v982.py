# -*- coding: utf-8 -*-
"""`safe_edit.ersetze_alle` ersetzt mehrere Stellen - aber nur die GENANNTE Zahl.

🔴 WARUM ES DIESE FORM GIBT, OBWOHL `ersetze` auf Eindeutigkeit besteht.
Der Kopf von `scripts/safe_edit.py` sagt selbst: *„eine Reparatur an einer
von vier Stellen ist keine"*. Am 29.09.2026 stand genau dieser Fall an: die
Maengel-Filterpille steht viermal im Code, mit derselben Form und derselben
Kur. `ersetze` hat zu Recht verweigert - und vier kuenstlich verlaengerte
Anker waeren vier Gelegenheiten gewesen, einen davon falsch abzuschreiben.

🔴 UND WARUM ES TROTZDEM KEIN BLINDES `replace()` IST.
`erwartet` muss stimmen. Wer „vier" sagt und fuenf trifft, hat eine Stelle
uebersehen, die er nicht kennt - genau dann bricht es ab, BEVOR etwas
geschrieben wird. Die Zahl kommt aus einer Messung, nicht aus dem Gefuehl.

Das ist derselbe Gedanke wie ueberall in diesem Prueftstand: nicht „mach es
ueberall", sondern „ich behaupte N, und wenn es nicht N sind, will ich es
wissen".

Die ganze Maschinerie von `ersetze` bleibt dahinter: Groessenpruefung,
Surrogat-Riegel, Nebendatei, Ruecklesen. Faellt etwas auf, bleibt das
Original unberuehrt.
"""
import io
import os
import sys
import tempfile

import pytest

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "scripts"))

import safe_edit  # noqa: E402


def _datei(inhalt):
    ordner = tempfile.mkdtemp()
    pfad = os.path.join(ordner, "probe.txt")
    io.open(pfad, "w", encoding="utf-8", newline="").write(inhalt)
    return pfad


def test_die_richtige_zahl_ersetzt_alle():
    p = _datei("aXa aXa aXa\naXa aXa aXa\n")
    getan = safe_edit.ersetze_alle(p, "aXa", "aYa", "Probe", erwartet=6,
                                   min_bytes=10)
    t = io.open(p, encoding="utf-8", newline="").read()
    assert t.count("aYa") == 6 and t.count("aXa") == 0
    assert getan == ["Probe (6x)"], getan


def test_eine_zu_kleine_zahl_schreibt_NICHTS():
    """🔴 Der eigentliche Schutz: eine Stelle, die ich nicht kenne."""
    p = _datei("aXa aXa aXa\n")
    vorher = io.open(p, encoding="utf-8", newline="").read()
    with pytest.raises(SystemExit) as e:
        safe_edit.ersetze_alle(p, "aXa", "aYa", "Probe", erwartet=2,
                               min_bytes=10)
    assert "trifft 3 mal, erwartet waren 2" in str(e.value)
    assert io.open(p, encoding="utf-8", newline="").read() == vorher, \
        "Die Datei wurde angefasst, obwohl die Zahl nicht stimmte."


def test_eine_zu_grosse_zahl_schreibt_NICHTS():
    p = _datei("aXa\n")
    vorher = io.open(p, encoding="utf-8", newline="").read()
    with pytest.raises(SystemExit):
        safe_edit.ersetze_alle(p, "aXa", "aYa", "Probe", erwartet=4,
                               min_bytes=10)
    assert io.open(p, encoding="utf-8", newline="").read() == vorher


def test_kein_treffer_ist_ein_fehler_kein_erfolg():
    """Ein Anker, der gar nicht trifft, ist kein 'nichts zu tun' - er ist
    fast immer ein Tippfehler im Anker."""
    p = _datei("bbb\n")
    with pytest.raises(SystemExit):
        safe_edit.ersetze_alle(p, "aXa", "aYa", "Probe", erwartet=0,
                               min_bytes=10)


def test_ersetze_bleibt_unveraendert_auf_genau_einem_treffer():
    """🔴 Gegenprobe: die neue Form darf die alte nicht aufweichen.

    `ersetze` muss weiter GENAU einen Treffer verlangen - sonst waere der
    Umweg ueber `ersetze_alle` sinnlos und jeder mehrdeutige Anker ginge
    stillschweigend durch.
    """
    p = _datei("aXa aXa\n")
    vorher = io.open(p, encoding="utf-8", newline="").read()
    with pytest.raises(SystemExit):
        safe_edit.ersetze(p, [("aXa", "aYa", "Probe")], min_bytes=10)
    assert io.open(p, encoding="utf-8", newline="").read() == vorher
