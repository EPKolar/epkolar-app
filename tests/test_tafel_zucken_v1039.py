# -*- coding: utf-8 -*-
"""v3.9.1039 Monteur-Tafel zuckt am Display (Sebastian 18.11.).
Ursache: Auto-Fit mass nach jedem Render neu; neue Skala -> neue Breite -> anderer Umbruch -> neue Skala (Pendel),
ausgeloest vor allem durch das 60-s-Nachladen, das die Scheine auch ohne Aenderung neu setzte."""
import json
import re
import shutil

import pytest

from conftest import run_node_snippet


def _fn(html, name):
    m = re.search(r"function %s\([^)]*\)\{.*?\n" % re.escape(name), html)
    assert m, name
    return m.group(0)


def _pendel(js_fn):
    # Inhalt: bei Skala 1.0 -> Hoehe 1100 (Skala 0.98); bei 0.98 bricht Text anders -> Hoehe 1060 (Skala 1.01); usw.
    return (js_fn +
            "var st={key:null},s=1,verlauf=[];"
            "function hoehe(sc){return sc<1?1060:1100;}"
            "for(var i=0;i<12;i++){var sc=Math.min(1.25,Math.max(0.6,1080/hoehe(s)));s=_kioskFitNext(s,sc,st,'1920x1080|woche');verlauf.push(s);}"
            "var wechsel=0;for(var j=1;j<verlauf.length;j++){if(verlauf[j]!==verlauf[j-1])wechsel++;}"
            "var st2={key:null};var a=_kioskFitNext(0.9,1.2,st2,'k1');var b=_kioskFitNext(a,1.0,st2,'k2');"
            "console.log(JSON.stringify({wechsel:wechsel,ende:s,neuerSchluessel:[a,b]}));")


@pytest.mark.skipif(shutil.which("node") is None, reason="node fehlt")
def test_fit_pendelt_nicht(node_exe, index_html):
    r = json.loads(run_node_snippet(node_exe, _pendel(_fn(index_html, "_kioskFitNext"))))
    assert r["wechsel"] <= 1, r
    assert r["ende"] <= 1.0, r
    # neuer Schluessel (Fenster/Ansicht/Daten) darf in beide Richtungen
    assert r["neuerSchluessel"] == [1.2, 1.0], r


@pytest.mark.skipif(shutil.which("node") is None, reason="node fehlt")
def test_umkehrprobe_altes_verhalten_pendelt(node_exe):
    alt = "function _kioskFitNext(prev,sc,st,key){return (Math.abs(prev-sc)>0.01)?sc:prev;}\n"
    r = json.loads(run_node_snippet(node_exe, _pendel(alt)))
    assert r["wechsel"] > 5, r


def test_beide_tafeln_nutzen_den_riegel(index_html):
    assert index_html.count("_setFitScale(function(prev){return _kioskFitNext(prev,sc,_fitSt,") == 2
    assert "_setFitScale(function(prev){return (Math.abs(prev-sc)>0.01)?sc:prev;});" not in index_html
    assert index_html.count("const _fitSt=_react.useRef.call(void 0, {key:null}).current;") == 2


def test_nachladen_setzt_nur_bei_aenderung(index_html):
    i = index_html.index("Auto-Refresh 60s (Fetch erneut + Stand updaten)")
    block = index_html[i:index_html.index(",[]);", index_html.index("},60000)", i))]
    assert "if(_sig!==_kioskTafelSig){_kioskTafelSig=_sig;props.setArbeitsscheine(" in block
    # Stand wird weiter bei JEDEM erfolgreichen Abruf gesetzt (v3.9.939)
    assert block.index("if(Array.isArray(raw))") < block.index("setStand(new Date());")
    assert block.index("_kioskTafelSig=_sig") < block.index("setStand(new Date());")


def test_umkehrprobe_nachladen(index_html):
    kaputt = index_html.replace("if(_sig!==_kioskTafelSig){", "if(true){", 1)
    assert "if(_sig!==_kioskTafelSig){_kioskTafelSig=_sig;" not in kaputt
