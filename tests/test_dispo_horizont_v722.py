# -*- coding: utf-8 -*-
"""v3.9.722 — Dispo P1-e Teil 1: 3-Wochen-Horizont + Wochen-Malus + km ab Firma.

Sebastian: der Planer rechnet rollierend KW+1..KW+3. Ein Schein, der in W1 nicht mehr in die Norm
passt, wandert nach W2, dann W3 — erst danach Warteliste ("passt nicht in 3 Wochen"). Wochen-Malus
im Score haelt Dringendes vorne. Jahresgrenze via isoW-Familie (kein +7-Bastel).
km-Nachtrag: jede Tagesroute rechnet ab FIRMA (Firma->Stopp1->..->StoppN->Firma), feste Endpunkte.
"""
import subprocess


def _block(index_html):
    start = index_html.index("var DISPO_RESERVE_MIN=60;")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    return index_html[start:end]


_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"


def _run(node_exe, tmp_path, js):
    f = tmp_path / "dispo722.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_konstanten_da(index_html):
    assert "var DISPO_HORIZONT_WOCHEN=3;" in index_html
    assert "var DISPO_WOCHEN_MALUS=" in index_html


def test_ueberlauf_w1_nach_w2(index_html, node_exe, tmp_path):
    """Zwei 400er-Scheine bei M1 passen nicht auf denselben Tag -> W1 nimmt einen, W2 den anderen."""
    js = _block(index_html) + _OK + u"""
var cfg={monteure:[{id:'M1',name:'A'}],
  tage:[{key:'w0',woche:0,normMin:510},{key:'w1',woche:1,normMin:510}],
  firma:{},dist:function(){return 0;},kapAbzug:{},hatFz:function(){return true;},horizont:2,
  scheine:[{id:'S1',adrKey:'a',dauerMin:400,monteurId:'M1',alterMs:1},
           {id:'S2',adrKey:'b',dauerMin:400,monteurId:'M1',alterMs:2}]};
var r=_dispoPlan(cfg);
ok(r.warteliste.length===0,'beide passen in 2 Wochen -> keine Warteliste');
ok(r.plan['M1']['w0'].length===1,'ein Schein in Woche 1');
ok(r.plan['M1']['w1'].length===1,'Ueberlauf in Woche 2');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_wochen_malus_haelt_in_w1(index_html, node_exe, tmp_path):
    """Wochen-Malus: S2 bleibt in W1, obwohl W1 (nach FARSTOP) mehr km kostet als das leere W2."""
    js = _block(index_html) + _OK + u"""
var D={FF:0,FA:10,FB:10,AF:10,AB:100,BF:10,BA:100,AA:0,BB:0};
function dist(a,b){return D[(a.plz||'F')+(b.plz||'F')]||0;}
var cfg={monteure:[{id:'M1',name:'A'}],
  tage:[{key:'w0',woche:0,normMin:510},{key:'w1',woche:1,normMin:510}],
  firma:{plz:'F'},dist:dist,kapAbzug:{},hatFz:function(){return true;},horizont:2,
  scheine:[{id:'FARSTOP',adrKey:'x',plz:'A',dauerMin:60,monteurId:'M1',alterMs:1},
           {id:'S2',adrKey:'y',plz:'B',dauerMin:60,monteurId:'M1',alterMs:2}]};
var r=_dispoPlan(cfg);
ok(r.plan['M1']['w0'].length===2,'Wochen-Malus haelt S2 in Woche 1 (trotz hoeherer km)');
ok(r.plan['M1']['w1'].length===0,'S2 NICHT in Woche 2');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_drei_wochen_erschoepfung_warteliste(index_html, node_exe, tmp_path):
    """4 Scheine à 400 bei M1, 3 Wochen à 1 Tag -> 3 passen, der 4. auf die Warteliste (Grund nennt 3 Wochen)."""
    js = _block(index_html) + _OK + u"""
var cfg={monteure:[{id:'M1',name:'Anton'}],
  tage:[{key:'w0',woche:0,normMin:510},{key:'w1',woche:1,normMin:510},{key:'w2',woche:2,normMin:510}],
  firma:{},dist:function(){return 0;},kapAbzug:{},hatFz:function(){return true;},horizont:3,
  scheine:[{id:'A',adrKey:'a',dauerMin:400,monteurId:'M1',alterMs:1},
           {id:'B',adrKey:'b',dauerMin:400,monteurId:'M1',alterMs:2},
           {id:'C',adrKey:'c',dauerMin:400,monteurId:'M1',alterMs:3},
           {id:'D',adrKey:'d',dauerMin:400,monteurId:'M1',alterMs:4}]};
var r=_dispoPlan(cfg);
ok(r.warteliste.length===1,'der 4. Schein passt in keine der 3 Wochen -> Warteliste');
ok(/3 Wochen/.test(r.warteliste[0].grund),'Grund nennt 3 Wochen: '+r.warteliste[0].grund);
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_km_ab_firma_hin_und_rueck(index_html, node_exe, tmp_path):
    """Route [A] = 2x dist(Firma,A) — Tagesrundfahrt ab Firma (feste Endpunkte)."""
    js = _block(index_html) + _OK + u"""
function dist(a,b){var P={F:0,A:10};return Math.abs((P[a.plz]||0)-(P[b.plz]||0));}
var cfg={monteure:[{id:'M1',name:'A'}],tage:[{key:'w0',woche:0,normMin:510}],
  firma:{plz:'F'},dist:dist,kapAbzug:{},hatFz:function(){return true;},horizont:1,
  scheine:[{id:'S1',adrKey:'a',plz:'A',dauerMin:60,monteurId:'M1',alterMs:1}]};
var r=_dispoPlan(cfg);
ok(r.wocheKm===20,'Route [A] = Firma->A->Firma = 10+10 = 20 km');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_km_firma_endpunkte_und_einfuege_formel(index_html):
    """Feste Firma-Endpunkte je Tag (kein Uebertrag) + Einfuege-Score-Formel woertlich."""
    block = _block(index_html)
    assert "var pts=[firma].concat(st3,[firma]);" in block, "Tagesroute nicht mit festen Firma-Endpunkten gebaut"
    assert "dist(last,s)+dist(s,firma)-dist(last,firma)" in block, "Einfuege-Mehr-km-Formel geaendert"


def _panel(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    return index_html[start:end]


def test_dispopanel_rendert_pro_woche(index_html):
    body = _panel(index_html)
    assert "_built.wochen" in body, "DispoPanel gruppiert nicht pro Woche (3-Wochen-Ansicht fehlt)"


def test_dispopanel_km_ab_firma_hinweis(index_html):
    body = _panel(index_html)
    assert "ab Firma" in body, "km-ab-Firma-Hinweis (Tagesrundfahrt) fehlt im Panel"


def test_dispopanel_wochen_klappbar(index_html):
    body = _panel(index_html)
    # Wochen-Sektionen auf-/zuklappbar (W1 offen, 2+3 klappbar)
    assert "_setOpenW" in body or "_openW" in body, "Wochen-Sektionen nicht klappbar"


def test_buildinput_drei_wochen_und_jahresgrenze(index_html, node_exe, tmp_path):
    """_dispoBuildInput baut HOR Wochen; Horizont ueber die Jahresgrenze (Dez 2026 -> 2027) korrekt."""
    js = u"""
var AS_GRP_OFFEN=["aufgenommen","freigegeben","in_bearbeitung","aufgeschoben"];
const isoWof=(dd)=>{const d=new Date(dd);d.setHours(0,0,0,0);d.setDate(d.getDate()+3-(d.getDay()+6)%7);const w=new Date(d.getFullYear(),0,4);return 1+Math.round(((d-w)/864e5-3+(w.getDay()+6)%7)/7);};
const isoWYof=(dd)=>{const d=new Date(dd);d.setHours(0,0,0,0);d.setDate(d.getDate()+3-(d.getDay()+6)%7);return d.getFullYear();};
""" + _block(index_html) + _OK + u"""
var out=_dispoBuildInput([],[{id:'M1',n:'A',r:'Monteur'}],{},{},new Date('2026-12-22T00:00:00'),3);
ok(out.wochen.length===3,'3 Wochen im Horizont');
var yrs=out.wochen.map(function(w){return w.yr;});
ok(yrs.indexOf(2027)>=0,'Horizont ueberschreitet die Jahresgrenze (2027 dabei)');
ok(out.wochen[0].kw>=50 && out.wochen[2].kw<=3,'KW-Wrap 52/53 -> 01 korrekt ('+out.wochen[0].kw+'->'+out.wochen[2].kw+')');
ok(out.cfg.tage.length===15,'3 Wochen x 5 Tage = 15 Kandidatentage');
ok(out.cfg.tage[0].woche===0 && out.cfg.tage[14].woche===2,'woche-Index 0..2 gesetzt');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)
