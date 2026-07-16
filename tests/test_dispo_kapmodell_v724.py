# -*- coding: utf-8 -*-
"""v3.9.724 — Register #0: Kapazitaetsmodell — drei Tagesarten statt Vollblock.

Sebastian:
0a Planungszeilen bvh WOERTLICH "Störungen"/"SAT-Störungen" (umlaut-fold) = NICHT belegt ->
   Stoerungsdienst-Tag = VOLLE Kapazitaet + Score-BONUS (bevorzugtes Ziel). SAT-Scheine
   (_dispoTopf-SAT-Kriterium woertlich) bevorzugt SAT-Tage, Kreuz mit kleinem Malus.
0b normale BVH-Belegung = KEIN Vollblock -> Vorab-Fenster DISPO_VORAB_MIN=120: eine Stoerung VOR
   der Baustelle; Chip "vor 🏗 <BVH>"; Score-Malus zwischen Wochen-Malus und Buendelung -> genutzt
   erst wenn nichts Besseres in 3 Wochen frei ist (statt Warteliste).
0c Frei-Tag = volle Kapazitaet.
Harte Grenzen: Norm-Wand, Reserve, Urlaub/Krank blocken GANZ, manueller Block ganz.
"""
import subprocess


def _block(index_html):
    start = index_html.index("var DISPO_RESERVE_MIN=60;")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    return index_html[start:end]


_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"
_ISOW = u"""
var AS_GRP_OFFEN=["aufgenommen","freigegeben","in_bearbeitung","aufgeschoben"];
const isoWof=(dd)=>{const d=new Date(dd);d.setHours(0,0,0,0);d.setDate(d.getDate()+3-(d.getDay()+6)%7);const w=new Date(d.getFullYear(),0,4);return 1+Math.round(((d-w)/864e5-3+(w.getDay()+6)%7)/7);};
const isoWYof=(dd)=>{const d=new Date(dd);d.setHours(0,0,0,0);d.setDate(d.getDate()+3-(d.getDay()+6)%7);return d.getFullYear();};
"""


def _run(node_exe, tmp_path, js):
    f = tmp_path / "dispo724.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_konstanten(index_html):
    for c in ("var DISPO_VORAB_MIN=120;", "var DISPO_STOERTAG_BONUS=", "var DISPO_VORAB_MALUS=", "var DISPO_SAT_CROSS_MALUS="):
        assert c in index_html, "Konstante fehlt: " + c


def test_istsat(index_html, node_exe, tmp_path):
    js = _block(index_html) + _OK + u"""
ok(_dispoIstSat({scheinart:'sat'})===true,'scheinart sat');
ok(_dispoIstSat({arbeitsanweisungen:'SAT Anlage stoerung'})===true,'SAT im Text');
ok(_dispoIstSat({scheinart:'stoerung',arbeitsanweisungen:'Gastherme'})===false,'normale Stoerung ist nicht SAT');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_stoertag_bevorzugt(index_html, node_exe, tmp_path):
    """Score-Bonus: Schein landet auf dem Stoerungsdienst-Tag, nicht auf dem (zuerst gelisteten) freien Tag."""
    js = _block(index_html) + _OK + u"""
var cfg={monteure:[{id:'M1',name:'A'}],
  tage:[{key:'mi',woche:0,normMin:510},{key:'di',woche:0,normMin:510}],
  tagArt:{M1:{mi:{art:'frei'},di:{art:'stoerung'}}},
  firma:{},dist:function(){return 0;},kapAbzug:{},hatFz:function(){return true;},horizont:1,
  scheine:[{id:'S1',adrKey:'a',dauerMin:120,monteurId:'M1',alterMs:1}]};
var r=_dispoPlan(cfg);
ok(r.plan['M1']['di'].length===1,'Schein bevorzugt den Stoerungsdienst-Tag (Di)');
ok(r.plan['M1']['mi'].length===0,'nicht auf den freien Tag Mi');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_sat_bevorzugt_sat_tag(index_html, node_exe, tmp_path):
    js = _block(index_html) + _OK + u"""
var cfg={monteure:[{id:'M1',name:'A'}],
  tage:[{key:'st',woche:0,normMin:510},{key:'sat',woche:0,normMin:510}],
  tagArt:{M1:{st:{art:'stoerung'},sat:{art:'sat'}}},
  firma:{},dist:function(){return 0;},kapAbzug:{},hatFz:function(){return true;},horizont:1,
  scheine:[{id:'X',scheinart:'sat',adrKey:'a',dauerMin:120,monteurId:'M1',alterMs:1}]};
var r=_dispoPlan(cfg);
ok(r.plan['M1']['sat'].length===1,'SAT-Schein bevorzugt den SAT-Stoerungs-Tag');
ok(r.plan['M1']['st'].length===0,'nicht auf den normalen Stoerungs-Tag (Kreuz-Malus)');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_vorab_letzter_ausweg_und_fenster(index_html, node_exe, tmp_path):
    """Vorab-Slot: genutzt vor der Warteliste; Chip 'vor 🏗'; Schein > Vorab-Fenster passt NICHT."""
    js = _block(index_html) + _OK + u"""
// cap(v0) = 510-60-330 = 120 (Vorab-Fenster)
var cfg={monteure:[{id:'M1',name:'A'}],tage:[{key:'v0',woche:0,normMin:510}],
  tagArt:{M1:{v0:{art:'vorab',bvh:'BVH Leth'}}},kapAbzug:{M1:{v0:330}},
  firma:{},dist:function(){return 0;},hatFz:function(){return true;},horizont:1,
  scheine:[{id:'S',adrKey:'a',dauerMin:100,monteurId:'M1',alterMs:1}]};
var r=_dispoPlan(cfg);
ok(r.plan['M1']['v0'].length===1,'kurzer Schein passt ins Vorab-Fenster');
ok(/vor 🏗/.test(r.plan['M1']['v0'][0].begruendung),'Chip-Kennzeichnung "vor 🏗": '+r.plan['M1']['v0'][0].begruendung);
// 200min passt nicht in 120er-Fenster -> Warteliste
var cfg2={monteure:[{id:'M1',name:'A'}],tage:[{key:'v0',woche:0,normMin:510}],
  tagArt:{M1:{v0:{art:'vorab',bvh:'BVH Leth'}}},kapAbzug:{M1:{v0:330}},
  firma:{},dist:function(){return 0;},hatFz:function(){return true;},horizont:1,
  scheine:[{id:'B',adrKey:'b',dauerMin:200,monteurId:'M1',alterMs:1}]};
var r2=_dispoPlan(cfg2);
ok(r2.plan['M1']['v0'].length===0 && r2.warteliste.length===1,'zu langer Schein passt NIE ins Vorab-Fenster -> Warteliste');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_buildinput_tagarten(index_html, node_exe, tmp_path):
    js = _ISOW + _block(index_html) + _OK + u"""
var mon=[{id:'m1',n:'Anton',r:'Monteur'}];
var now=new Date('2026-07-16T00:00:00');
var base=_dispoBuildInput([],mon,{},{},now,3);
// v3.9.739: Woche 0 ist jetzt die LAUFENDE Woche (kann vergangene Tage haben) -> tagArt auf der Folgewoche (immer Zukunft) pruefen.
var iso=base.wochen[1].tage[1].iso; var wtag=base.wochen[1].tage[1].wtag; // Di der Folgewoche
var kwk=base.wochen[1].yr+'-'+base.wochen[1].kw;
function mkWp(bvh){var wp={};var z={};z[wtag]={ma:['m1']};wp[kwk]=[{z:z,bvh:bvh}];return wp;}
// Stoerungen-Zeile -> voll + tagArt stoerung, NICHT geblockt
var oS=_dispoBuildInput([],mon,mkWp('Störungen'),{},now,3);
ok(oS.tagArt['m1'][iso].art==='stoerung','Störungen-Zeile -> Stoerungsdienst-Tag');
ok(oS.cfg.kapAbzug['m1'][iso]===0,'Stoerungsdienst-Tag NICHT geblockt (Abzug 0)');
// SAT-Störungen
var oSat=_dispoBuildInput([],mon,mkWp('SAT-Störungen'),{},now,3);
ok(oSat.tagArt['m1'][iso].art==='sat','SAT-Störungen-Zeile -> SAT-Tag');
// normale BVH -> vorab, Kapazitaet auf 120 begrenzt (Abzug = 510-60-120 = 330)
var oB=_dispoBuildInput([],mon,mkWp('BVH Leth'),{},now,3);
ok(oB.tagArt['m1'][iso].art==='vorab','normale Baustelle -> Vorab-Tag');
ok(oB.cfg.kapAbzug['m1'][iso]===330,'Vorab-Tag auf 120-Fenster begrenzt (Abzug 330): '+oB.cfg.kapAbzug['m1'][iso]);
ok(oB.blockGrund['m1'][iso] && /Vorab/.test(oB.blockGrund['m1'][iso][0].label),'Vorab-Grund-Chip');
// Urlaub blockt weiterhin GANZ (auch auf Belegungstag)
var am={}; am['Anton_'+iso]={type:'urlaub',status:'genehmigt',hours:0};
var oU=_dispoBuildInput([],mon,mkWp('BVH Leth'),am,now,3);
ok(oU.cfg.kapAbzug['m1'][iso]>=510-60,'Urlaub blockt ganz (auch auf Belegungstag)');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)
