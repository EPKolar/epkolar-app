# -*- coding: utf-8 -*-
"""v3.9.714 — Dispo E3-Verdrahtung: _dispoPlan (Greedy + Buendelung + 2-opt) + _dispoTopf + _dispoAbwAbzug.

Testliste (Bauauftrag): Wand (Schein passt nicht -> Warteliste) · Buendelung gleiche Adresse -> ein
Monteur/Tag · Topf-Reihenfolge · Abwesenheit beantragt blockt / abgelehnt frei / Teiltag reduziert.
"""
import subprocess


def _block(index_html):
    start = index_html.index("var DISPO_RESERVE_MIN=60;")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    return index_html[start:end]


def test_dispoplan_executed(index_html, node_exe, tmp_path):
    js = _block(index_html) + u"""
function ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }
// _dispoTopf
ok(_dispoTopf({scheinart:'stoerung'})===0,'topf stoerung'); ok(_dispoTopf({prioritaet:'hoch'})===1,'topf hoch');
ok(_dispoTopf({prioritaet:'normal'})===2,'topf rest');
// _dispoAbwAbzug (normMin 510)
ok(_dispoAbwAbzug({status:'beantragt'},510)===510,'beantragt blockt');
ok(_dispoAbwAbzug({status:'abgelehnt'},510)===0,'abgelehnt frei');
ok(_dispoAbwAbzug({status:'genehmigt',std:4},510)===240,'ZA-teiltag 4h');
ok(_dispoAbwAbzug(null,510)===0,'keine abwesenheit');
// _dispoPlan: Buendelung + Wand
var firma={plz:'0',lat:0,lon:0};
function dist(a,b){ if(a.plz===b.plz)return 0; var A={A:1,B:5,'0':0}; return Math.abs((A[a.plz]||0)-(A[b.plz]||0)); }
var cfg={
  monteure:[{id:'M1',name:'A'},{id:'M2',name:'B'}],
  tage:[{key:'Mo',normMin:510},{key:'Di',normMin:510}],
  firma:firma, dist:dist, kapAbzug:{}, hatFz:function(){return true;},
  scheine:[
    {id:'S1',bvh:'BVH-A1',adrKey:'a',plz:'A',dauerMin:120,alterMs:3,monteurId:'M1'},
    {id:'S2',bvh:'BVH-A2',adrKey:'a',plz:'A',dauerMin:120,alterMs:2,monteurId:'M1'},
    {id:'S3',bvh:'BVH-B', adrKey:'b',plz:'B',dauerMin:120,alterMs:1,monteurId:'M1'}
  ]};
var r=_dispoPlan(cfg);
// S1 und S2 (gleicher adrKey 'a') muessen bei DEMSELBEN Monteur am SELBEN Tag landen (Buendelung)
function findScheinPos(id){for(var m in r.plan)for(var t in r.plan[m])for(var i=0;i<r.plan[m][t].length;i++)if(r.plan[m][t][i].scheinId===id)return m+'/'+t;return null;}
ok(findScheinPos('S1')===findScheinPos('S2'),'S1+S2 gebuendelt gleicher Monteur/Tag');
ok(r.warteliste.length===0,'alles verplant');
ok(typeof r.wocheKm==='number','wocheKm zahl');
// WAND: ein Schein mit 500min auf 510-Norm (kap 510-60=450) passt nicht -> Warteliste
var cfg2={monteure:[{id:'M1',name:'A'}],tage:[{key:'Mo',normMin:510}],firma:firma,dist:dist,kapAbzug:{},hatFz:function(){return true;},
  scheine:[{id:'X',bvh:'X',adrKey:'x',plz:'A',dauerMin:500,alterMs:1,monteurId:'M1'}]};
var r2=_dispoPlan(cfg2);
ok(r2.warteliste.length===1 && r2.warteliste[0].scheinId==='X','WAND: 500min passt nicht in 450 -> Warteliste');
// fz-Bedarf: hatFz=false -> Warteliste mit Grund
var cfg3={monteure:[{id:'M1',name:'A'}],tage:[{key:'Mo',normMin:510}],firma:firma,dist:dist,kapAbzug:{},hatFz:function(){return false;},
  scheine:[{id:'Y',bvh:'Y',adrKey:'y',plz:'A',dauerMin:60,fzTyp:'Steiger',alterMs:1,monteurId:'M1'}]};
var r3=_dispoPlan(cfg3);
ok(r3.warteliste.length===1,'fz-Bedarf ohne freies FZ -> Warteliste');
console.log('OK');
"""
    f = tmp_path / "dispoplan.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout
