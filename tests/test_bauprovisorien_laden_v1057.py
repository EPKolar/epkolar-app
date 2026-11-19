# -*- coding: utf-8 -*-
"""v1057 Bughunt: Bauprovisorien-Lader uebernimmt Provisorien nur MIT Mieten.

Scheiterte die Mieten-Abfrage, standen die Provisorien trotzdem im Zustand und
die Auto-Anlage in BauprovisorienView erzeugte fuer jedes Jahr eine neue,
unverrechnete Mietzeile - auch fuer laengst verrechnete Jahre.

Echte Funktionen aus index.html in node: _rlsLeer, _bpLadenOk und der
Auto-Anlage-Effekt der BauprovisorienView (Umkehrprobe mit dem alten Lader).
"""
import json
import re

from conftest import _extract_fn, run_node_snippet


def _helpers(index_html):
    return _extract_fn(index_html, "_rlsLeer") + "\n" + _extract_fn(index_html, "_bpLadenOk") + "\n"


def _effekt(index_html):
    st = index_html.index("function BauprovisorienView(")
    seg = index_html[st:st + 20000]
    yr = re.search(r"const _yr=s=>\{.*?\};", seg).group(0)
    jahre = re.search(r"const _jahre=p=>\{.*?return out;\};", seg).group(0)
    mieten = re.search(r"const _mietenOf=pid=>[^;]*;", seg).group(0)
    a = seg.index("// Auto-create fehlende Mieten-Zeilen")
    b = seg.index("},[bauprovisorien,bauproMieten]);", a)
    body = seg[a:b]
    body = body[body.index("()=>{") + len("()=>{"):]
    return yr, jahre, mieten, body


def _lauf(node_exe, index_html, alter_lader):
    yr, jahre, mieten, body = _effekt(index_html)
    lader_neu = "if(_bpLadenOk(_bp,_bm)){setBauprovisorien(_bp);setBauproMieten(_bm);}"
    lader_alt = "if(Array.isArray(_bp))setBauprovisorien(_bp);if(Array.isArray(_bm))setBauproMieten(_bm);"
    js = _helpers(index_html) + (
        "let bauprovisorien=[],bauproMieten=[];const posts=[];\n"
        "const setBauprovisorien=v=>{bauprovisorien=v;};\n"
        "const setBauproMieten=v=>{bauproMieten=typeof v==='function'?v(bauproMieten):v;};\n"
        "const SQ={push:i=>posts.push(i)};let _n=0;const uid=()=>'u'+(++_n);\n"
        "const _canDo=true;const _nowYr=2026;\n"
        + yr + "\n" + jahre + "\n" + mieten + "\n"
        "const _bp=[{id:'bp1',errichtung_datum:'2023-05-01',abbau_datum:''}];\n"
        "const _bm=null;/* Mieten-Abfrage gescheitert (catch -> null) */\n"
        + (lader_alt if alter_lader else lader_neu) + "\n"
        "(function(){" + body + "})();\n"
        "console.log(JSON.stringify({bp:bauprovisorien.length,neu:posts.length}));"
    )
    return json.loads(run_node_snippet(node_exe, js))


def test_bp_laden_ok_reale_funktion(node_exe, index_html):
    js = _helpers(index_html) + (
        "const rls=[];rls.__rlsFehler=403;"
        "console.log(JSON.stringify([_bpLadenOk([{id:1}],[]),_bpLadenOk([{id:1}],null),"
        "_bpLadenOk([{id:1}],rls),_bpLadenOk(null,[]),_bpLadenOk([],[])]));"
    )
    assert json.loads(run_node_snippet(node_exe, js)) == [True, False, False, False, True]


def test_gescheiterte_mieten_abfrage_erzeugt_keine_geisterzeilen(node_exe, index_html):
    out = _lauf(node_exe, index_html, alter_lader=False)
    assert out == {"bp": 0, "neu": 0}, out


def test_umkehrprobe_alter_lader_legt_jedes_jahr_neu_an(node_exe, index_html):
    out = _lauf(node_exe, index_html, alter_lader=True)
    # 2023..2026 = 4 Jahre, alle als "offen" neu angelegt
    assert out == {"bp": 1, "neu": 4}, out


def test_lader_nutzt_bp_laden_ok(index_html):
    assert "if(!_alv)return;if(_bpLadenOk(_bp,_bm)){setBauprovisorien(_bp);setBauproMieten(_bm);}" in index_html
    assert "if(Array.isArray(_bp))setBauprovisorien(_bp);" not in index_html
