# -*- coding: utf-8 -*-
"""v3.9.729 — Register #19: km/Fahrzeit-Kaskade — "+0 km" ist Schwachsinn.

Sebastian (Live-Befund v727, PRIO HOCH): jeder Chip zeigt "+0 km". Fix = Kaskade, killt "+0 km" SOFORT
ohne Geo-Daten via Innerorts-Konstante.
Kaskade `_dispoStrecke(plzA,plzB,geoMap,matrix)`:
  1. plz_distanz-Matrix (normalisiert plz_a<plz_b): echte km+min -> EXAKT "N km".
  2. gleiche PLZ: Konstante DISPO_INNERORTS_KM=2 / DISPO_INNERORTS_MIN=5 -> "~2 km".
  3. plz_geo-Zentroid beide bekannt: Haversine*Strassenfaktor -> "~N km".
  4. sonst (andere PLZ, keine Daten): km unbekannt -> "? km"; FAHRZEIT nie 0, min = DISPO_INNERORTS_MIN.
plz_geo/plz_distanz sind live LEER -> Code muss jetzt "~2 km"/"? km" liefern und mit gefuellten Tabellen
automatisch echte km (kein neuer Push). Testfall S075327 Karin Pfeiler (PLZ != 3470, keine Daten) -> "? km".
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
    f = tmp_path / "km729.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_strecke_kaskade(index_html, node_exe, tmp_path):
    js = _block(index_html) + _OK + u"""
var geo={'3470':{lat:48.43,lon:15.74},'3430':{lat:48.33,lon:15.61}};
var mx={'3470|3800':{km:40,min:35}};
var m=_dispoStrecke('3470','3800',{},mx); ok(m.km===40&&m.min===35&&m.exact===true,'Matrix -> exakt');
var m2=_dispoStrecke('3800','3470',{},mx); ok(m2.km===40,'Matrix symmetrisch (normalisiert plz_a<plz_b)');
var sp=_dispoStrecke('3470','3470',geo,mx); ok(sp.km===DISPO_INNERORTS_KM&&sp.min===DISPO_INNERORTS_MIN&&sp.known===true&&sp.exact===false,'gleiche PLZ -> ~2km/5min');
var g=_dispoStrecke('3470','3430',geo,{}); ok(g.known===true&&g.exact===false&&g.km>0&&g.min>0,'geo-Zentroid -> Haversine, min>0');
var u=_dispoStrecke('3470','9999',{},{}); ok(u.known===false&&u.km===null&&u.min===DISPO_INNERORTS_MIN&&u.min>0,'unbekannt -> ? km, Fahrzeit NIE 0');
var u2=_dispoStrecke('','3430',{},{}); ok(u2.known===false&&u2.min>0,'fehlende PLZ -> unbekannt, min>0');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_buildinput_kmlabel(index_html, node_exe, tmp_path):
    js = _ISOW + _block(index_html) + _OK + u"""
var mon=[{id:'m1',n:'A',r:'Monteur'}];
var sch=[{id:'S1',scheinstatus:'aufgenommen',monteur:'m1',kundPlz:'3470',arbeitsort:'Kirchberg'},
         {id:'S2',scheinstatus:'aufgenommen',monteur:'m1',kundPlz:'3430',arbeitsort:'Tulln'}];
var o=_dispoBuildInput(sch,mon,{},{},new Date('2026-07-16T00:00:00'),3,{},{});
var p1=o.cfg.scheine.filter(function(p){return p.id==='S1';})[0];
ok(/~2 km/.test(p1.kmLabel),'S1 (PLZ=Firma 3470) -> ~2 km: '+p1.kmLabel);
var p2=o.cfg.scheine.filter(function(p){return p.id==='S2';})[0];
ok(/\\? km/.test(p2.kmLabel),'S2 (andere PLZ, keine Daten) -> ? km: '+p2.kmLabel);
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_kein_plus0km_im_rechenkern(index_html):
    block = _block(index_html)
    assert '+"+Math.max(0,Math.round(best.mehr))+" km"' not in block, "'+N km'-Format (inkl. +0 km) muss aus der Begruendung raus"
    assert "? km" in block, "Unbekannt-Label '? km' fehlt"


def test_signatur_erweitert(index_html):
    assert "function _dispoBuildInput(scheine,monteure,wpHistory,absMap,now,horizontWochen,geoMap,distMatrix,blocksMap)" in index_html
    assert "window._dispoStrecke=_dispoStrecke" in index_html
