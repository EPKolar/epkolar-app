# -*- coding: utf-8 -*-
"""v3.9.1007 - Werkzeugwert in Kacheln als "€ 16.490" (wie AuswertungView v1004).

Vorher: Home "€16 490", Werkzeuge "€16 490 Wert" (schmales Leerzeichen als
Tausendertrenner, kein Abstand zum Zeichen). Nur die Anzeige; _fmtEur, fmt$
und Exporte bleiben unberuehrt.
"""
import subprocess

import pytest


def _fn(html):
    i = html.find("function _eurKachel(")
    assert i != -1
    return html[i:html.find(chr(10), i)].rstrip()  # steht auf EINER Zeile


@pytest.mark.parametrize("n,erwartet", [(16490, "€ 16.490"), (0, "€ 0"), ("x", "—"), ("1234.6", "€ 1.235")])
def test_das_bild_stimmt_ausgefuehrt(index_html, node_exe, n, erwartet):
    js = _fn(index_html) + ";process.stdout.write(_eurKachel(%s).replace(/\u00a0|\u202f/g,' '));" % (
        repr(n) if isinstance(n, str) else n)
    # Ueber stdin statt -e: Nicht-ASCII in der Windows-Kommandozeile kommt verstuemmelt an.
    aus = subprocess.run([node_exe], input=js.encode("utf-8"), capture_output=True, timeout=60)
    assert aus.stdout.decode("utf-8") == erwartet, aus.stderr


def test_beide_kacheln_benutzen_es(index_html):
    assert '_eurKachel(totalWert))' in index_html, "Home-Kachel Werkzeugwert"
    assert 'sub: _eurKachel(totalWert)+" Wert"' in index_html, "Werkzeuge-Kachel Gesamt"
    assert '"€"+totalWert.toLocaleString("de-AT")' not in index_html
    assert '"€", totalWert.toLocaleString("de-AT")' not in index_html


def test_die_globalen_formatierer_bleiben(index_html):
    i = index_html.find("window._fmtEur=(n)=>")
    assert i != -1
    zeile = index_html[i:index_html.find(chr(10), i)]
    assert "_eurKachel" not in zeile and "minimumFractionDigits:2" in zeile
