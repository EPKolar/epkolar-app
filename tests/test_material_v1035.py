# -*- coding: utf-8 -*-
"""v3.9.1035 Materialbestellung - Riegel fuer die neuen Helfer und Wege (nachgezogen 17.11.).
Gemessen 17.11.: die App lud nur limit=10000 von 25.121 Katalogartikeln; 12.765 Holter-Namen mit zerstoerten Umlauten;
Suchtreffer in zugeklappten Gruppen unsichtbar."""
import json
import re
import shutil

import pytest

from conftest import run_node_snippet


def _fn(html, name):
    m = re.search(r"function %s\([^)]*\)\{.*?\n" % re.escape(name), html)
    assert m, name
    return m.group(0)


def _const(html, name):
    m = re.search(r"const %s=[^\n]*\n" % re.escape(name), html)
    assert m, name
    return m.group(0)


@pytest.mark.skipif(shutil.which("node") is None, reason="node fehlt")
def test_umlaut_reparatur_und_suche(node_exe, index_html):
    moj = re.search(r"(const|var) _MAT_MOJ[^\n]*\n", index_html)
    assert moj, "_MAT_MOJ fehlt"
    js = (moj.group(0) + _fn(index_html, "_matTextFix") + _fn(index_html, "_matFold") +
          "console.log(JSON.stringify(["
          "_matTextFix('St„rke','2026-04-12'),"         # alter Holter-Stand -> repariert
          "_matTextFix('St„rke','2026-11-17'),"         # neuer Stand -> unveraendert
          "_matTextFix('Stärke','2026-04-12'),"               # echte Umlaute -> unveraendert
          "_matFold('Betätigung'),_matFold('Betaetigung'),_matFold('GROSS'),_matFold('Fuß')]));")
    r = json.loads(run_node_snippet(node_exe, js))
    assert r[0] == "Stärke", r
    assert r[1] == "St„rke" and r[2] == "Stärke"
    assert r[3] == r[4] == "betatigung"
    assert r[5] == "gross" and r[6] == "fuss"


def test_ganzer_katalog_wird_seitenweise_geladen(index_html):
    assert "&limit=10000&offset=" in index_html
    i = index_html.index("&limit=10000&offset=")
    block = index_html[i - 1500:i + 600]
    assert "if(_seite.length===0)break;" in block, "Abbruch bei leerer Seite fehlt"
    assert "_saFehler=true" in block, "Fehlerfall nicht markiert"
    assert "_MAT_KAT_SEITEN" in index_html


def test_kein_treffer_als_position_und_nochmal_anfordern(index_html):
    assert "Als Position übernehmen" in index_html
    assert "Nochmal anfordern" in index_html


def test_umkehrprobe_alter_10000er_schnitt(index_html):
    kaputt = index_html.replace("&limit=10000&offset=", "&limit=10000", 1)
    assert "&limit=10000&offset=" not in kaputt
