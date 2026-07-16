# -*- coding: utf-8 -*-
"""v3.9.727 — Register #17: Dispo-Scope — ueberfaellige Termine gehoeren in die Planung.

Sebastian: "Ueberfaellig = war mal eine Idee, nicht erledigt -> neu planen. Zukunfts-Termin = passt,
von den Damen fixiert."
a) IN: AS_GRP_OFFEN ohne Termin ODER termin_bestaetigt < heute (Wiener Datum). Ueberfaellige: Chip-
   Badge "⚠ war DD.MM." + Alters-Bonus (aelter ueberfaellig -> weiter vorne).
b) DRAUSSEN: Zukunfts-Termin (>= heute) und scheinstatus 'aufgeschoben' (Parkplatz).
17d Zukunfts-Termine sind FIX: Dispo plant sie NIE um; ihre Dauer wird am Termin-Tag vom Kapazitaets-
   topf abgezogen (auf ALLE offenen mit Zukunfts-Termin, nicht nur Prio-1); fester Chip (📌) ohne
   Uebernehmen. 17e: alter Termin wird beim Uebernehmen ersetzt (E4b).
"""
import subprocess


def _block(index_html):
    start = index_html.index("var DISPO_RESERVE_MIN=60;")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    return index_html[start:end]


def _panel(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    return index_html[start:end]


_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"
_ISOW = u"""
var AS_GRP_OFFEN=["aufgenommen","freigegeben","in_bearbeitung","aufgeschoben"];
const isoWof=(dd)=>{const d=new Date(dd);d.setHours(0,0,0,0);d.setDate(d.getDate()+3-(d.getDay()+6)%7);const w=new Date(d.getFullYear(),0,4);return 1+Math.round(((d-w)/864e5-3+(w.getDay()+6)%7)/7);};
const isoWYof=(dd)=>{const d=new Date(dd);d.setHours(0,0,0,0);d.setDate(d.getDate()+3-(d.getDay()+6)%7);return d.getFullYear();};
"""


def _run(node_exe, tmp_path, js):
    f = tmp_path / "dispo727.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_scope_ueberfaellig_fix_aufgeschoben(index_html, node_exe, tmp_path):
    js = _ISOW + _block(index_html) + _OK + u"""
var mon=[{id:'m1',n:'Anton',r:'Monteur'}];
var now=new Date('2026-07-16T12:00:00');
var base=_dispoBuildInput([],mon,{},{},now,3);
var futIso=base.wochen[0].tage[0].iso;
var scheine=[
  {id:'A',scheinstatus:'in_bearbeitung',monteur:'m1',terminBestaetigt:'2026-07-10',arbeitsort:'Wien'},
  {id:'B',scheinstatus:'in_bearbeitung',monteur:'m1',terminBestaetigt:futIso,dauer:'03:00',arbeitsort:'Graz'},
  {id:'C',scheinstatus:'aufgeschoben',monteur:'m1',terminBestaetigt:'2026-07-08',arbeitsort:'Linz'},
  {id:'D',scheinstatus:'aufgenommen',monteur:'m1',arbeitsort:'Krems'}
];
var o=_dispoBuildInput(scheine,mon,{},{},now,3);
var ids=o.cfg.scheine.map(function(p){return p.id;});
ok(ids.indexOf('A')>=0,'ueberfaelliger A im Scope');
ok(ids.indexOf('D')>=0,'ohne Termin D im Scope');
ok(ids.indexOf('B')<0,'Zukunfts-Termin B NICHT im Scope');
ok(ids.indexOf('C')<0,'aufgeschoben C NICHT im Scope (Parkplatz)');
var pA=o.cfg.scheine.filter(function(p){return p.id==='A';})[0];
ok(pA.ueberfaelligVon==='2026-07-10','A traegt ueberfaelligVon');
ok(pA.ueberfaelligTage>0,'A ueberfaelligTage>0');
ok(o.ueberfaelligCount===1,'genau 1 ueberfaellig');
// 17d: B ist fix -> Kapazitaets-Abzug + fixMap
ok(o.fixMap['m1'] && o.fixMap['m1'][futIso] && o.fixMap['m1'][futIso][0].scheinId==='B','B als fester Chip (fixMap)');
ok(o.cfg.kapAbzug['m1'][futIso]>=180,'B (3h) zieht Kapazitaet ab');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_alters_bonus_ueberfaellig_vor_frisch(index_html, node_exe, tmp_path):
    js = _block(index_html) + _OK + u"""
var cfg={monteure:[{id:'M1',name:'A'}],tage:[{key:'d0',woche:0,normMin:510}],
  firma:{},dist:function(){return 0;},kapAbzug:{},hatFz:function(){return true;},horizont:1,
  scheine:[{id:'FRESH',adrKey:'a',dauerMin:400,monteurId:'M1',alterMs:0,ueberfaelligTage:0},
           {id:'OVERDUE',adrKey:'b',dauerMin:400,monteurId:'M1',alterMs:100,ueberfaelligTage:5}]};
var r=_dispoPlan(cfg);
ok(r.plan['M1']['d0'].length===1 && r.plan['M1']['d0'][0].scheinId==='OVERDUE','aelterer ueberfaelliger vor frischem ohne Termin');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_ueberfaellig_am_chip(index_html, node_exe, tmp_path):
    js = _block(index_html) + _OK + u"""
var cfg={monteure:[{id:'M1',name:'A'}],tage:[{key:'d0',woche:0,normMin:510}],
  firma:{},dist:function(){return 0;},kapAbzug:{},hatFz:function(){return true;},horizont:1,
  scheine:[{id:'X',adrKey:'a',dauerMin:120,monteurId:'M1',alterMs:1,ueberfaelligVon:'2026-07-10',ueberfaelligTage:6}]};
var r=_dispoPlan(cfg);
ok(r.plan['M1']['d0'][0].ueberfaelligVon==='2026-07-10','Chip traegt ueberfaelligVon (fuer das ⚠-Badge)');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_panel_pins(index_html):
    body = _panel(index_html)
    assert "überfällig" in body, "Kopfzeile ohne 'überfällig'-Zaehler"
    assert "⚠ war " in body, "Chip-Badge '⚠ war' fehlt"
    assert "_built.fixMap" in body or "fixMap" in body, "feste Chips (fixMap) nicht gerendert"
    assert "📌" in body, "📌-Badge fuer fixe Termine fehlt"
