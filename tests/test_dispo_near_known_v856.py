"""
v3.9.856 — Dispo-Nachbarschafts-Bonus feuerte auf UNBEKANNTEN Distanzen.

`cfg.dist` (:5235) gab `_dispoStrecke.min` zurück und liess das `known`-Flag fallen.
Bei fehlender Geo liefert `_dispoStrecke` `{min:5 (INNERORTS-Attrappe), known:false}`
→ die nah-Schleife (:5087) sah `5 < DISPO_NAH_MIN(15)` als echte Nähe und vergab den
−30000-Bonus auf JEDES Paar (ferne Aufträge wurden geclustert). Fix: `cfg.near(x,y)`
= `st.known && st.min < DISPO_NAH_MIN`; die nah-Schleife nutzt `near()` statt `dist()<NAH`.
"""
import re
import json
from conftest import run_node_snippet


def test_cfg_near_known_gated(index_html):
    assert "near:function(x,y){" in index_html
    assert "return !!(st.known&&st.min!=null&&st.min<DISPO_NAH_MIN);}" in index_html


def test_nah_schleife_nutzt_near(index_html):
    # alte, distanz-basierte (known-blinde) nah-Erkennung ist weg
    assert "if(dist(stops[qn],s)<DISPO_NAH_MIN){nah=true;break;}" not in index_html
    assert "if(near(stops[qn],s)){nah=true;break;}" in index_html
    # near ist im Score-Scope verfuegbar
    assert "near=cfg.near||function(){return false;}" in index_html


def test_near_verhalten_via_node(index_html, node_exe):
    strecke = re.search(r"function _dispoStrecke\(plzA,plzB,geoMap,matrix\)\{.*?\n\}", index_html, re.S)
    haversine = re.search(r"function _dispoHaversine\([^)]*\)\{.*?\n\}", index_html, re.S)
    assert strecke and haversine, "Dispo-Strecke/Haversine nicht gefunden"
    harness = (
        "var DISPO_INNERORTS_KM=2, DISPO_INNERORTS_MIN=5, DISPO_KMH=50, DISPO_NAH_MIN=15;\n"
        + haversine.group(0) + "\n" + strecke.group(0) + "\n"
        # exakt das Praedikat aus cfg.near
        "function near(a,b,geo,mx){var st=_dispoStrecke(a,b,geo,mx);return !!(st.known&&st.min!=null&&st.min<DISPO_NAH_MIN);}\n"
        "const out={"
        "unbekannt:near('3100','3040',{},{}),"          # kein Matrix/Geo, verschiedene PLZ -> known:false
        "gleichePlz:near('3100','3100',{},{}),"          # gleiche PLZ -> known:true, min 5
        "matrixNah:near('3100','3040',{},{'3040|3100':{km:8,min:10}}),"   # known:true, 10<15
        "matrixFern:near('3100','3040',{},{'3040|3100':{km:40,min:50}})"  # known:true, 50>=15
        "};console.log(JSON.stringify(out));"
    )
    out = json.loads(run_node_snippet(node_exe, harness))
    assert out["unbekannt"] is False, "unbekannte Distanz darf NICHT als nah gelten (war der Bug)"
    assert out["gleichePlz"] is True, "gleiche PLZ ist echte Naehe"
    assert out["matrixNah"] is True
    assert out["matrixFern"] is False
