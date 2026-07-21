# -*- coding: utf-8 -*-
"""v3.9.800 c-1A (Sebastian-Freigabe) — die 7 Prio-Stufen wirken echt in der Dispo-Reihung.

_dispoTopf (0/1/2) bleibt byte-identisch (Begruendungs-Rang). NEU: pure _dispoPrioRang liefert die
Feinstufe fuer den Greedy-Sort: Topf 0 (Stoerung/SAT)=0; Topf 1 fein FIXTERMIN 1.0 < sehr hoch 1.3 <
hoch 1.6; Topf 2 fein normal 2.0 < niedrig 2.3 (keine/aufgeschoben/leer = 2.0 wie normal).

REIHENFOLGE-SEMANTIK (Sebastian): Feinstufe ZUERST, dann ueberfaelligTage desc, dann Alter -> ein
frischer "normal" geht vor einem lange ueberfaelligen "niedrig". Der v727-Ueberfaellig-Bonus wirkt
nur noch INNERHALB derselben Feinstufe. Score/Kapazitaetswand/Topf-0 byte-identisch.
"""
from conftest import run_node_snippet


def _rang(node_exe, index_html, schein_js):
    a = index_html.index("function _dispoTopf(s){")
    topf = index_html[a:index_html.index("\n}", a) + 2]
    b = index_html.index("function _dispoPrioRang(s){")
    rang = index_html[b:index_html.index("\n}", b) + 2]
    snip = topf + "\n" + rang + f";process.stdout.write(String(_dispoPrioRang({schein_js})))"
    return float(run_node_snippet(node_exe, snip).strip())


def test_feinstufen_werte(node_exe, index_html):
    def r(js): return _rang(node_exe, index_html, js)
    assert r("{scheinart:'stoerung'}") == 0.0
    assert r("{scheinart:'sat'}") == 0.0
    assert r("{prioritaet:'fixtermin'}") == 1.0
    assert r("{prioritaet:'sehr hoch'}") == 1.3
    assert r("{prioritaet:'hoch'}") == 1.6
    assert r("{prioritaet:'normal'}") == 2.0
    assert r("{prioritaet:'niedrig'}") == 2.3
    assert r("{prioritaet:'keine'}") == 2.0
    assert r("{prioritaet:'aufgeschoben'}") == 2.0
    assert r("{}") == 2.0  # leere Prio wie normal


def test_stoerung_schlaegt_prio(node_exe, index_html):
    # Stoerung/SAT bleibt Topf 0 = ganz vorne, egal welche Prio.
    assert _rang(node_exe, index_html, "{scheinart:'stoerung',prioritaet:'niedrig'}") == 0.0


def test_ordnung_streng_monoton(node_exe, index_html):
    seq = [_rang(node_exe, index_html, "{scheinart:'stoerung'}"),
           _rang(node_exe, index_html, "{prioritaet:'fixtermin'}"),
           _rang(node_exe, index_html, "{prioritaet:'sehr hoch'}"),
           _rang(node_exe, index_html, "{prioritaet:'hoch'}"),
           _rang(node_exe, index_html, "{prioritaet:'normal'}"),
           _rang(node_exe, index_html, "{prioritaet:'niedrig'}")]
    assert seq == sorted(seq) and len(set(seq)) == len(seq), "Feinstufen nicht streng aufsteigend/eindeutig"


def test_normal_vor_niedrig_semantik(node_exe, index_html):
    # Semantik-Entscheid: normal (2.0) < niedrig (2.3) -> ein frischer normal sortiert vor niedrig,
    # bevor der Ueberfaellig-Bonus ueberhaupt greift (Rang ist erstes Sortkriterium).
    assert _rang(node_exe, index_html, "{prioritaet:'normal'}") < _rang(node_exe, index_html, "{prioritaet:'niedrig'}")


def test_sort_zeile_reihenfolge(index_html):
    # Feinstufe ZUERST, dann ueberfaellig desc, dann Alter (Ueberfaellig nur INNERHALB gleicher Stufe).
    assert ("var ta=_dispoPrioRang(a),tb=_dispoPrioRang(b);if(ta!==tb)return ta-tb;" in index_html)
    assert ("var ua=a.ueberfaelligTage||0,ub=b.ueberfaelligTage||0;if(ua!==ub)return ub-ua;"
            "return (a.alterMs||0)-(b.alterMs||0);" in index_html)


def test_dispoTopf_byte_identisch(index_html):
    # _dispoTopf bleibt die alte Ganzzahl-Logik (Begruendungs-Rang rang===0/1/2 haengt daran).
    assert 'if(p==="fixtermin"||p==="sehr hoch"||p==="hoch")return 1;' in index_html
    assert "var rang=_dispoTopf(s)" in index_html
