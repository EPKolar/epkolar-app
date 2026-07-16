# -*- coding: utf-8 -*-
"""v3.9.717 — Dispo P1-a: Monteur kommt aus dem AS, NIE von der Dispo.

Sebastian-Korrektur (v716 schlug live Guenther/GF + Lindhuber/Buero fuer Stoerungen vor):
- Vorschlaege NUR in der Zeile des im Schein zugewiesenen Monteurs (a.monteur).
- Schein OHNE Monteur -> NIE eingeplant -> Warteliste "Monteur fehlt — im Schein zuweisen" (ohneMonteur:true).
- Schein MIT Monteur aber kein freier Tag -> Warteliste "kein freier Tag bei <Name>" (ohneMonteur:false),
  NIE Spillover auf einen anderen Monteur (Least-Loaded-Tie-Break entfaellt ersatzlos).
- Rasterzeilen = NUR Feld-Monteure, WOERTLICH nach dem WeekPlan-Praedikat (Z.18449):
  !["Backoffice","Verkauf/Buchhaltung","Geschäftsführer"].includes(m.r)
- _dispoBuildInput traegt monteurId je planSchein.
"""
import subprocess


def _block(index_html):
    start = index_html.index("var DISPO_RESERVE_MIN=60;")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    return index_html[start:end]


_HARNESS = u"""
function ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }
"""


def _run(node_exe, tmp_path, js):
    f = tmp_path / "dispo717.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_dispoplan_nur_zugewiesener_monteur(index_html, node_exe, tmp_path):
    """Schein mit monteurId=M2 -> Vorschlag ausschliesslich in Zeile M2, nie M1."""
    js = _block(index_html) + _HARNESS + u"""
var cfg={monteure:[{id:'M1',name:'A'},{id:'M2',name:'B'}],tage:[{key:'Mo',normMin:510}],
  firma:{plz:'0',lat:0,lon:0},dist:function(){return 0;},kapAbzug:{},hatFz:function(){return true;},
  scheine:[{id:'S1',bvh:'X',adrKey:'x',dauerMin:60,monteurId:'M2',alterMs:1}]};
var r=_dispoPlan(cfg);
ok(r.plan['M2']['Mo'].length===1 && r.plan['M2']['Mo'][0].scheinId==='S1','S1 nur bei zugewiesenem M2');
ok(r.plan['M1']['Mo'].length===0,'S1 nie bei M1');
ok(r.warteliste.length===0,'S1 verplant');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_dispoplan_ohne_monteur_in_warteliste(index_html, node_exe, tmp_path):
    """Schein ohne monteurId -> kein Chip, Warteliste mit ohneMonteur:true + Grund 'Monteur fehlt'."""
    js = _block(index_html) + _HARNESS + u"""
var cfg={monteure:[{id:'M1',name:'A'}],tage:[{key:'Mo',normMin:510}],
  firma:{plz:'0'},dist:function(){return 0;},kapAbzug:{},hatFz:function(){return true;},
  scheine:[{id:'N',bvh:'N',adrKey:'n',dauerMin:60,monteurId:'',alterMs:1}]};
var r=_dispoPlan(cfg);
ok(r.plan['M1']['Mo'].length===0,'ohne Monteur -> kein Chip');
ok(r.warteliste.length===1 && r.warteliste[0].scheinId==='N','ohne Monteur -> Warteliste');
ok(r.warteliste[0].ohneMonteur===true,'ohneMonteur-Flag true');
ok(/Monteur fehlt/.test(r.warteliste[0].grund),'Grund nennt Monteur fehlt');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_dispoplan_kein_spillover_least_loaded_entfaellt(index_html, node_exe, tmp_path):
    """M1 voll -> sein zweiter Schein geht in die Warteliste (kein freier Tag bei <Name>),
    NIE auf den leeren M2 (Least-Loaded-Tie-Break entfaellt)."""
    js = _block(index_html) + _HARNESS + u"""
var cfg={monteure:[{id:'M1',name:'Anton'},{id:'M2',name:'Berta'}],tage:[{key:'Mo',normMin:510}],
  firma:{plz:'0'},dist:function(){return 0;},kapAbzug:{},hatFz:function(){return true;},
  scheine:[{id:'A',bvh:'A',adrKey:'a',dauerMin:400,monteurId:'M1',alterMs:2},
           {id:'B',bvh:'B',adrKey:'b',dauerMin:400,monteurId:'M1',alterMs:1}]};
var r=_dispoPlan(cfg);
ok(r.plan['M2']['Mo'].length===0,'kein Spillover auf den leeren M2');
ok(r.plan['M1']['Mo'].length===1,'genau ein Schein passt bei M1');
ok(r.warteliste.length===1,'der zweite M1-Schein steht in der Warteliste');
var w0=r.warteliste[0];
ok(/Anton/.test(w0.grund),'Grund nennt den Monteur-Namen Anton');
ok(w0.ohneMonteur===false,'M1-voll ist NICHT ohneMonteur');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_dispobuildinput_feld_monteur_und_monteurid(index_html, node_exe, tmp_path):
    """_dispoBuildInput: nur Feld-Monteure als Zeilen (GF/Backoffice raus), monteurId je planSchein."""
    js = u"""
var AS_GRP_OFFEN=["aufgenommen","freigegeben","in_bearbeitung","aufgeschoben"];
function isoWof(){return 29;} function isoWYof(){return 2026;}
""" + _block(index_html) + _HARNESS + u"""
var monteure=[{id:'M1',n:'Anton',r:'Monteur'},{id:'GF',n:'Guenther',r:'Geschäftsführer'},
              {id:'BO',n:'Lindhuber',r:'Backoffice'},{id:'VK',n:'Vera',r:'Verkauf/Buchhaltung'}];
var scheine=[{id:'S1',scheinstatus:'aufgenommen',arbeitsort:'Wien',monteur:'M1'},
             {id:'S2',scheinstatus:'aufgenommen',arbeitsort:'Graz',monteur:''}];
var out=_dispoBuildInput(scheine,monteure,{},{},new Date('2026-07-16T00:00:00'));
ok(out.monteure.length===1 && out.monteure[0].id==='M1','nur Feld-Monteur als Zeile (GF/BO/VK raus)');
ok(out.cfg.monteure.length===1 && out.cfg.monteure[0].id==='M1','cfg.monteure nur Feld-Monteur');
var ps=out.cfg.scheine;
ok(ps.length===2,'beide offenen Scheine im plan-input');
var s1=ps.filter(function(p){return p.id==='S1';})[0];
ok(s1.monteurId==='M1','S1 traegt monteurId M1');
var s2=ps.filter(function(p){return p.id==='S2';})[0];
ok(s2.monteurId==='','S2 ohne monteurId');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_dispo_field_praedikat_woertlich(index_html):
    """Rasterzeilen-Praedikat WOERTLICH wie WeekPlan (Z.18449), nicht neu erfunden."""
    start = index_html.index("function _dispoBuildInput(")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    seg = index_html[start:end]
    assert '["Backoffice","Verkauf/Buchhaltung","Geschäftsführer"]' in seg, \
        "Feld-Monteur-Praedikat der Wochenplanung fehlt im Dispo-Pfad"


def test_dispopanel_header_ohne_monteur(index_html):
    """Kopfzeile zeigt 'ohne Monteur' + 'nicht unterbringbar' (Damen sehen fehlende Zuweisung)."""
    start = index_html.index("function DispoPanel({arbeitsscheine,monteure,wpHistory,abs,onUebernehmen,onOpenSchein})")
    end = index_html.index("function ArbeitsscheinView(", start)
    body = index_html[start:end]
    assert "ohne Monteur" in body, "Kopfzeile ohne 'ohne Monteur'-Zaehler"
    assert "nicht unterbringbar" in body
