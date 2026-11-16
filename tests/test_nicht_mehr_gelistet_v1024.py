# -*- coding: utf-8 -*-
"""v3.9.1024 GF: Storno aus OFFA kommt teilweise nicht an. Gemessen 16.11.: 15 offene/erledigte Scheine fehlen im
laufenden WorksheetList-Feed (62 geliefert). Nur ANZEIGE: Hinweis + Formular-Kennzeichen. Feed/Push/Nummern unberuehrt."""
import json
import re
import shutil

import pytest

from conftest import run_node_snippet


def _fn(html):
    m = re.search(r"function _offaNichtImFeed\(s,maxMs\)\{.*?\n", html)
    assert m
    return m.group(0)


@pytest.mark.skipif(shutil.which("node") is None, reason="node fehlt")
def test_rechnung(node_exe, index_html):
    js = ("const AS_GRP_OFFEN=['aufgenommen','freigegeben','aufgeschoben','in_bearbeitung'];" + _fn(index_html) +
          "const mx=Date.parse('2026-11-16T15:31:00Z');const f=(st,t,j)=>_offaNichtImFeed({juprowa_id:j===undefined?1:j,scheinstatus:st,juprowa_sync_at:t},mx);"
          "console.log(JSON.stringify([f('in_bearbeitung','2026-09-02T10:00:00Z'),f('erledigt','2026-07-21T10:00:00Z'),"
          "f('in_bearbeitung','2026-11-16T15:30:00Z'),f('storniert','2026-04-01T00:00:00Z'),f('abgerechnet','2026-04-01T00:00:00Z'),"
          "f('in_bearbeitung','2026-09-02T10:00:00Z',null),f('in_bearbeitung',null)]));")
    assert json.loads(run_node_snippet(node_exe, js)) == [True, True, False, False, False, False, False]


def test_nur_anzeige_und_bestehendes_unberuehrt(index_html):
    assert "window._offaNichtImFeed=_offaNichtImFeed;" in index_html
    assert "'data-offa-nicht-im-feed': _nichtImFeedL.length" in index_html
    assert "_nichtImFeed(form)&&React.createElement('span'" in index_html
    # nicht zwischen OFFA_VERWAIST_TAGE und _isOffaVerwaist eingefuegt
    a = index_html.index("var OFFA_VERWAIST_TAGE")
    b = index_html.index("function _isOffaVerwaist")
    assert "_offaNichtImFeed" not in index_html[a:b]
    # nur bei frischem Feed (bei stillem Feed greift der bestehende Banner)
    assert '_offaFeed.zustand==="frisch"&&!!(window._offaNichtImFeed' in index_html


def test_umkehrprobe(index_html):
    kaputt = index_html.replace("return t<maxMs-60*60*1000;", "return false;", 1)
    assert "return t<maxMs-60*60*1000;" not in kaputt
