# -*- coding: utf-8 -*-
"""v3.9.1007 - Einzahl/Mehrzahl statt Klammerform.

"⚠ 11 offene(r) Schein(e) evtl. in OFFA abgeschlossen" - die App kennt die
Zahl im Moment der Anzeige, die Klammer ist eine Verlegenheit des Schreibers.
Seit v1007 laeuft jede solche Stelle ueber EINE Quelle: _nWort(n, ein, mehr).

Die Riegel halten die EIGENSCHAFT fest ("kein UI-Text traegt eine
Klammerform", "die Form haengt an ===1"), nicht den Wortlaut einzelner
Stellen - eine neue Klammerform irgendwo in der Datei macht sie rot.
"""
import re
import subprocess

import pytest

_KLAMMER = re.compile(r"([A-Za-zäöüÄÖÜß]{2,})\((?:r|e|n|s|en|er)\)(?=[ \"'])")


def _ohne_kommentare(s):
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", "", s)


def _klammerformen(s):
    return [m.group(0) for m in _KLAMMER.finditer(_ohne_kommentare(s))
            if m.group(1) not in ("function", "catch")]


def test_kein_ui_text_traegt_eine_klammerform(index_html):
    treffer = _klammerformen(index_html)
    assert not treffer, (
        "Klammerform(en) im Code (nicht Kommentar): %r - bitte ueber "
        "_nWort(n,ein,mehr) schreiben." % treffer[:10]
    )


def test_der_melder_kann_anschlagen():
    """Positivprobe: ohne sie waere die Null oben keine Aussage."""
    probe = 'x("⚠ "+n+" offene(r) Schein(e) evtl.");/* Tag(e) im Kommentar */'
    assert _klammerformen(probe) == ["offene(r)", "Schein(e)"], _klammerformen(probe)


def test_es_gibt_genau_eine_quelle(index_html):
    assert index_html.count("function _nWort(") == 1
    i = index_html.find("function _nWort(")
    rumpf = index_html[i:index_html.find("}", i) + 1]
    assert "===1" in rumpf, rumpf


def test_der_offa_hinweis_benutzt_die_quelle(index_html):
    assert '_nWort(_verwaisteN,"offener Schein","offene Scheine")' in index_html


@pytest.mark.parametrize("n,erwartet", [
    (0, "0 offene Scheine"),
    (1, "1 offener Schein"),
    (11, "11 offene Scheine"),
])
def test_die_form_stimmt_ausgefuehrt(index_html, n, erwartet):
    """Nicht nur lesen - ausfuehren: dieselbe Funktion aus der Datei in node."""
    i = index_html.find("function _nWort(")
    fn = index_html[i:index_html.find("}", i) + 1]
    js = fn + ';process.stdout.write(_nWort(%d,"offener Schein","offene Scheine"));' % n
    try:
        aus = subprocess.run(["node", "-e", js], capture_output=True, timeout=30)
    except FileNotFoundError:
        pytest.skip("node fehlt")
    assert aus.stdout.decode("utf-8") == erwartet, aus.stderr
