# -*- coding: utf-8 -*-
"""v3.9.743 — Dispo-Horizont auf 4 Wochen (Sebastian: "dispo soll ueber 4 wochen gehen").

Default-Planungshorizont DISPO_HORIZONT_WOCHEN 3 -> 4. Mit dem KW+0-Anker (v739) zeigt die Dispo damit die
laufende Woche + 3 Folgewochen. _dispoBuildInput ohne explizites horizontWochen liefert 4 Wochen.
"""
import subprocess


def _block(index_html):
    start = index_html.index("var DISPO_RESERVE_MIN=60;")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    return index_html[start:end]


def test_konstante_ist_4(index_html):
    assert "var DISPO_HORIZONT_WOCHEN=4;" in index_html, "Default-Horizont nicht auf 4 Wochen"


def test_buildinput_default_4_wochen(index_html, node_exe, tmp_path):
    js = (u"""
var AS_GRP_OFFEN=["aufgenommen","freigegeben","in_bearbeitung","aufgeschoben"];
const isoWof=(dd)=>{const d=new Date(dd);d.setHours(0,0,0,0);d.setDate(d.getDate()+3-(d.getDay()+6)%7);const w=new Date(d.getFullYear(),0,4);return 1+Math.round(((d-w)/864e5-3+(w.getDay()+6)%7)/7);};
const isoWYof=(dd)=>{const d=new Date(dd);d.setHours(0,0,0,0);d.setDate(d.getDate()+3-(d.getDay()+6)%7);return d.getFullYear();};
""" + _block(index_html) + u"""
function ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }
var out=_dispoBuildInput([],[{id:'M1',n:'A',r:'Monteur'}],{},{},new Date('2026-07-16T00:00:00'));
ok(out.wochen.length===4,'ohne horizontWochen-Arg -> 4 Wochen (Default), war '+out.wochen.length);
ok(out.horizont===4,'horizont-Feld = 4');
console.log('OK');
""")
    f = tmp_path / "hor743.js"; f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout
