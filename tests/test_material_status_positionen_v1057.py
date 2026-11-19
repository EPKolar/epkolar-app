# -*- coding: utf-8 -*-
"""v1057 Bughunt: VMaterial.updateStatus uebernahm die im Preisvergleich
bearbeiteten Positionen nur am Server, nicht in der lokalen Liste. Der naechste
Statusknopf derselben Sitzung sendete dann die ORIGINAL-Positionen und
ueberschrieb die bestellten am Server.

Der Test fuehrt die echte updateStatus aus index.html in node aus (SQ, setOrders
usw. als Attrappen): erst 'bestellt' mit bearbeiteten Positionen, dann
'erledigt' mit der Bestellung aus der Liste. Umkehrprobe: alte Zeile -> der
zweite PUT traegt wieder die Original-Positionen.
"""
import json

from conftest import run_node_snippet

NEU = "setOrders(prev=>prev.map(x=>x.id===ord.id?{...x,status:newStatus,positionen:upd.positionen,kommentar_lager:upd.kommentar_lager}:x));"
ALT = "setOrders(prev=>prev.map(x=>x.id===ord.id?{...x,status:newStatus,kommentar_lager:upd.kommentar_lager}:x));"


def _update_status_src(index_html):
    st = index_html.index("const updateStatus=async(ord,newStatus,overridePos)=>{")
    i = index_html.index("{", index_html.index("=>", st))
    depth = 0
    while True:
        c = index_html[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return index_html[st:i + 1] + ";"
        i += 1


def _lauf(node_exe, src):
    js = (
        "const window={};const curUser={role:'admin'};const canDo=()=>true;\n"
        "const _react={};const _statusLocked={current:false};const lagerKommentar='';\n"
        "const setLagerKommentar=()=>{};const MAT_STATUS={};const puts=[];\n"
        "const SQ={push:async i=>{puts.push(JSON.parse(JSON.stringify(i.body)));}};\n"
        "let orders=[{id:'o1',status:'in_bearbeitung',kommentar_lager:'',positionen:[{name:'Kabel',menge:100},{name:'Dose',menge:20}]}];\n"
        "const setOrders=f=>{orders=typeof f==='function'?f(orders):f;};\n"
        + src + "\n"
        "(async()=>{await updateStatus(orders[0],'bestellt',[{name:'Kabel',menge:50}]);"
        "await updateStatus(orders[0],'erledigt');"
        "console.log(JSON.stringify({p1:puts[0].positionen,p2:puts[1].positionen,lokal:orders[0].positionen}));})();"
    )
    return json.loads(run_node_snippet(node_exe, js))


def test_folgestatus_behaelt_bestellte_positionen(node_exe, index_html):
    src = _update_status_src(index_html)
    assert NEU in src
    out = _lauf(node_exe, src)
    bestellt = [{"name": "Kabel", "menge": 50}]
    assert out["p1"] == bestellt
    assert out["lokal"] == bestellt
    assert out["p2"] == bestellt, "Folgestatus darf die bestellten Positionen nicht ueberschreiben: %r" % out


def test_umkehrprobe_alte_zeile_ueberschreibt(node_exe, index_html):
    src = _update_status_src(index_html).replace(NEU, ALT)
    out = _lauf(node_exe, src)
    assert len(out["p2"]) == 2, "Umkehrprobe: alte Logik muss die Original-Positionen erneut senden: %r" % out
