# -*- coding: utf-8 -*-
"""v3.9.730 — Register #16a (Kern): Termin per Drag&Drop fixieren = Pin.

Sebastian: Chip auf einen Tag der DERSELBEN Monteur-Zeile ziehen -> der Schein wird dort FIXIERT (📌),
der Rest des Plans rechnet sich drumherum; "Neu berechnen" respektiert Pins. Pins pro Woche in
localStorage (kein DDL). Drop ueber die Norm hinaus ist UNMOEGLICH (harte Wand gilt auch fuer Menschenhand).

Dieser Test pinnt den PUREN Kern: _dispoPlan(cfg) mit cfg.pins {scheinId: tagKey} legt den Schein auf
den gepinnten Tag SEINES Monteurs, unabhaengig vom Greedy-Score; harte Kapazitaetswand bleibt.
Die Pointer-Drag-Interaktion (Ghost, Schwelle 8px, Drop-Ziel-Feedback) ist Struktur-gepinnt (nicht node-eval).
"""
import subprocess


def _block(index_html):
    start = index_html.index("var DISPO_RESERVE_MIN=60;")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    return index_html[start:end]


_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"


def _run(node_exe, tmp_path, js):
    f = tmp_path / "pin730.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_pin_zwingt_tag(index_html, node_exe, tmp_path):
    """Ohne Pin landet S1 (Greedy) auf dem ersten Tag; MIT Pin auf 'di' landet er auf 'di'."""
    js = _block(index_html) + _OK + u"""
var base={monteure:[{id:'M1',name:'A'}],tage:[{key:'mo',woche:0,normMin:510},{key:'di',woche:0,normMin:510}],
  firma:{},dist:function(){return 0;},kapAbzug:{},hatFz:function(){return true;},horizont:1,
  scheine:[{id:'S1',adrKey:'a',dauerMin:120,monteurId:'M1',alterMs:1}]};
var r0=_dispoPlan(base);
ok(r0.plan['M1']['mo'].length===1,'ohne Pin: Greedy -> erster Tag (mo)');
base.pins={S1:'di'};
var r=_dispoPlan(base);
ok(r.plan['M1']['di'].length===1 && r.plan['M1']['di'][0].scheinId==='S1','Pin zwingt S1 auf di');
ok(r.plan['M1']['mo'].length===0,'S1 nicht mehr auf mo');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_pin_haelt_harte_wand(index_html, node_exe, tmp_path):
    """Ein gepinnter Schein belegt Kapazitaet; ein weiterer (ungepinnter) auf demselben Tag weicht aus/Warteliste."""
    js = _block(index_html) + _OK + u"""
var cfg={monteure:[{id:'M1',name:'A'}],tage:[{key:'mo',woche:0,normMin:510}],
  firma:{},dist:function(){return 0;},kapAbzug:{},hatFz:function(){return true;},horizont:1,
  pins:{P:'mo'},
  scheine:[{id:'P',adrKey:'a',dauerMin:400,monteurId:'M1',alterMs:1},
           {id:'Q',adrKey:'b',dauerMin:400,monteurId:'M1',alterMs:2}]};
var r=_dispoPlan(cfg);
ok(r.plan['M1']['mo'].length===1 && r.plan['M1']['mo'][0].scheinId==='P','gepinnter P auf mo');
ok(r.warteliste.filter(function(w){return w.scheinId==='Q';}).length===1,'Q passt nicht mehr -> Warteliste (harte Wand)');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_pin_falscher_monteur_ignoriert(index_html, node_exe, tmp_path):
    """Ein Pin auf einen Tag, aber der Schein gehoert einem anderen Monteur -> Pin greift nicht (Monteur aus AS)."""
    js = _block(index_html) + _OK + u"""
var cfg={monteure:[{id:'M1',name:'A'},{id:'M2',name:'B'}],tage:[{key:'mo',woche:0,normMin:510}],
  firma:{},dist:function(){return 0;},hatFz:function(){return true;},kapAbzug:{},horizont:1,
  pins:{S:'mo'},
  scheine:[{id:'S',adrKey:'a',dauerMin:120,monteurId:'M2',alterMs:1}]};
var r=_dispoPlan(cfg);
ok(r.plan['M2']['mo'].length===1,'Pin gilt in der Zeile des zugewiesenen Monteurs (M2)');
ok(r.plan['M1']['mo'].length===0,'nie in einer fremden Zeile (M1)');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_panel_drag_struktur(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    body = index_html[start:end]
    # Pointer-Events (kein HTML5-DnD), Bewegungs-Schwelle, Pin-Store
    assert "onPointerDown" in body, "kein Pointer-Drag am Chip"
    assert "epk_dispo_pins" in index_html, "Pin-Store (localStorage) fehlt"
    assert "DISPO_DRAG_SCHWELLE" in index_html, "Bewegungs-Schwelle (Klick vs Drag) fehlt"
