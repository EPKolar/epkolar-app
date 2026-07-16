# -*- coding: utf-8 -*-
"""v3.9.713 — Dispo Etappe 3 Rechenkern (pure //@DISPO Functions), via Node ausgefuehrt.

_dispoAdrKey (Buendel-Normalisierung), _dispoDauer (Feld>Keyword>Default), _dispoHaversine,
_dispo2opt (km monoton nicht-schlechter), _dispoKapazitaet (harte Wand - Reserve - Abwesenheit).
"""
import subprocess


def _block(index_html):
    start = index_html.index("var DISPO_RESERVE_MIN=60;")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    return index_html[start:end]


def test_rechenkern_executed(index_html, node_exe, tmp_path):
    js = _block(index_html) + u"""
function eq(g,e,n){ if(JSON.stringify(g)!==JSON.stringify(e)){ console.error('FAIL '+n+': '+JSON.stringify(g)+' != '+JSON.stringify(e)); process.exit(1);} }
function ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }
// _dispoAdrKey: die drei echten Varianten sind identisch
var a1=_dispoAdrKey('Marktplatz Nr. 6'), a2=_dispoAdrKey('Marktplatz Nr.6'), a3=_dispoAdrKey('Marktplatz 6');
eq(a1,a2,'adrKey Nr. == Nr.'); eq(a2,a3,'adrKey Nr. == plain'); eq(a1,'marktplatz 6','adrKey wert');
eq(_dispoAdrKey('Kirchberg/Wagram, Hauptstraße'),'kirchberg/wagram hauptstrasse','adrKey umlaut');
// _dispoDauer: Feld schlaegt Keyword schlaegt Default
eq(_dispoDauer({dauer:'02:30'}).min,150,'dauer feld'); ok(_dispoDauer({dauer:'02:30'}).geschaetzt===false,'dauer feld exakt');
eq(_dispoDauer({arbeitsanweisungen:'Verteiler tauschen'}).min,120,'dauer keyword verteiler (v751 #29d: Klasse Zaehler, gemessen 120)');
ok(_dispoDauer({arbeitsanweisungen:'Verteiler tauschen'}).geschaetzt===true,'dauer keyword geschaetzt');
eq(_dispoDauer({arbeitsanweisungen:'irgendwas anderes'}).min,90,'dauer default');
// _dispoHaversine: gleicher Punkt = 0; 1 Grad lat ~ 111km * 1.3
ok(_dispoHaversine(48,16,48,16)===0,'haversine null');
ok(Math.abs(_dispoHaversine(48,16,49,16,1)-111.19)<1,'haversine 1grad');
ok(Math.abs(_dispoHaversine(48,16,49,16)-111.19*1.3)<2,'haversine strassenfaktor');
// _dispo2opt: gekreuzte Route wird nicht schlechter (Punkte auf einer Linie 0..3)
var P=[[0,0],[3,0],[1,0],[2,0]]; function D(i,j){return Math.abs(P[i][0]-P[j][0]);}
var order=[0,1,2,3]; var r=_dispo2opt(order,D);
function L(o){var s=0;for(var i=0;i<o.length-1;i++)s+=D(o[i],o[i+1]);return s;}
ok(L(r)<L(order),'2opt verbessert'); ok(L(r)===4,'2opt optimal bei fixen Firma-Endpunkten -> 0-2-1-3 = 4');
// _dispoKapazitaet: 510 - 60 Reserve - 0 = 450; -240(ZA 4h) -> 210; grosse Abw -> 0
eq(_dispoKapazitaet(510,0),450,'kap voll');
eq(_dispoKapazitaet(510,240),210,'kap za-teiltag');
eq(_dispoKapazitaet(270,0),210,'kap freitag');
eq(_dispoKapazitaet(510,510),0,'kap volltag-abw');
console.log('OK');
"""
    f = tmp_path / "dispo.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_constants_named(index_html):
    for c in ("DISPO_RESERVE_MIN=60", "PUFFER_JE_STOPP=10", "DISPO_DAUER_REGELN=["):
        assert c in index_html
