# -*- coding: utf-8 -*-
"""Maengel/Plaene Stufe 2.

1  Plan beim Oeffnen EINPASSEN (ganz sichtbar) statt 100 % - Pin-Prozente bleiben
   gleich. Rundweg: setzen -> speichern -> in anderem Viewer neu oeffnen -> gleiche %.
2  Kein Base64 in der Warteschlange: BEIDE Erfassungsformulare schicken images:[],
   die Fotos gehen nur ueber captureAndQueue.
3  Nach dem Speichern im Foto-Weg "Noch einen Mangel per Foto?" (ein Tipp = Kamera).
4  Mangel-Karte im CI: Status-Farben nur semantisch, 44-px-Tippziele, keine Eigenfarben.

Jeder verhaltensnahe Riegel hat eine Umkehrprobe (Mutation muss ihn rot machen).
"""
import io
import json
import re
import sys
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL / "tests"))
from conftest import _extract_fn, run_node_snippet  # noqa: E402


@pytest.fixture(scope="module")
def src():
    return io.open(str(WURZEL / "index.html"), encoding="utf-8", newline="").read()


def _fn(src, name):
    b = _extract_fn(src, name)
    assert b, "%s nicht gefunden - das ist rot, nicht gruen." % name
    return b


def _zwischen(text, anfang, ende):
    i = text.find(anfang)
    assert i >= 0, "Anker fehlt: %s" % anfang
    j = text.find(ende, i + len(anfang))
    assert j > i, "Ende fehlt: %s" % ende
    return text[i:j]


# ── 1 Einpassen + Rundweg ────────────────────────────────────────────────

RUNDWEG_JS = r"""
__EINPASSEN__
__PCT__
// Viewer wie im Browser: world-Div flex-zentriert -> Layout-Ursprung o=(v-w)/2 (auch negativ),
// transform translate(pan) scale(zoom) mit Ursprung 0 0 -> Rechteck = o+pan, Groesse w*zoom.
function oeffne(vw, vh, w, h){
  var ox=(vw-w)/2, oy=(vh-h)/2;
  var f=_planEinpassen(vw, vh, w, h, ox, oy, "seite");
  return {f:f, rect:{left:ox+f.panX, top:oy+f.panY, width:w*f.zoom, height:h*f.zoom}};
}
var out={};
var W=2384, H=1684;                      // A1 quer in pt (PDF bei scale 1)
var dlg=oeffne(412, 640, W, H);          // Dialog "Auf Plan setzen" am Handy
out.dlg=dlg;
// Tipp auf eine Planstelle P (in % der Planflaeche)
var P={x:37.25, y:62.5};
var sx=dlg.rect.left+P.x/100*dlg.rect.width, sy=dlg.rect.top+P.y/100*dlg.rect.height;
var gesetzt=_planPctAusKlick(sx, sy, dlg.rect);
out.gesetzt=gesetzt;
// "speichern" (defects.x/y sind Prozent) -> JSON-Rundweg wie SyncQueue/DB
var gespeichert=JSON.parse(JSON.stringify({x:gesetzt.x, y:gesetzt.y}));
// neu oeffnen im Plan-Viewer (andere Groesse) + Zoom des Nutzers dazwischen egal
var vp=oeffne(412, 720, W, H);
out.vp=vp;
var px=vp.rect.left+gespeichert.x/100*vp.rect.width, py=vp.rect.top+gespeichert.y/100*vp.rect.height;
out.wieder=_planPctAusKlick(px, py, vp.rect);
// Bild-Plan hochkant (Handyfoto 3000x4000 px)
out.bild=oeffne(412, 720, 3000, 4000);
// kleiner Plan: nicht ueber 6 aufblasen, Untergrenze bleibt 0.4
out.klein=oeffne(1200, 800, 300, 200);
out.leer=_planEinpassen(0, 0, 100, 100, 0, 0, "seite");
console.log(JSON.stringify(out));
"""


def _rundweg(node_exe, src, einpassen=None):
    ep = einpassen if einpassen is not None else _fn(src, "_planEinpassen")
    js = RUNDWEG_JS.replace("__EINPASSEN__", ep).replace("__PCT__", _fn(src, "_planPctAusKlick"))
    return json.loads(run_node_snippet(node_exe, js))


def _ganz_sichtbar(o, vw, vh):
    r = o["rect"]
    return (r["left"] >= -0.01 and r["top"] >= -0.01
            and r["left"] + r["width"] <= vw + 0.01 and r["top"] + r["height"] <= vh + 0.01)


def test_1_rundweg_prozent_bleibt_gleich(node_exe, src):
    r = _rundweg(node_exe, src)
    assert abs(r["gesetzt"]["x"] - 37.25) < 1e-9 and abs(r["gesetzt"]["y"] - 62.5) < 1e-9
    assert abs(r["wieder"]["x"] - r["gesetzt"]["x"]) < 1e-9
    assert abs(r["wieder"]["y"] - r["gesetzt"]["y"]) < 1e-9
    # und die beiden Viewer haben WIRKLICH verschieden gezoomt/verschoben (sonst beweist der Rundweg nichts)
    assert abs(r["dlg"]["rect"]["top"] - r["vp"]["rect"]["top"]) > 10


def test_1_eingepasst_ist_ganz_sichtbar_und_nicht_100_prozent(node_exe, src):
    r = _rundweg(node_exe, src)
    assert r["dlg"]["f"]["zoom"] < 0.2, "A1-Plan am Handy muss deutlich unter 100 % stehen."
    assert _ganz_sichtbar(r["dlg"], 412, 640) and _ganz_sichtbar(r["vp"], 412, 720)
    assert _ganz_sichtbar(r["bild"], 412, 720)
    # Rand 12 px und Mitte: links = rechts
    d = r["dlg"]["rect"]
    assert abs(d["left"] - (412 - d["left"] - d["width"])) < 1e-6
    assert d["width"] <= 412 - 24 + 1e-6
    # herauszoomen bleibt moeglich (Untergrenze unter der Einpassung), nie unter 0.02
    assert 0.02 <= r["dlg"]["f"]["zMin"] < r["dlg"]["f"]["zoom"]
    assert r["klein"]["f"]["zoom"] <= 6 and r["klein"]["f"]["zMin"] == 0.4
    assert r["leer"] is None


def test_1_umkehrprobe_ohne_flexversatz_waere_rot(node_exe, src):
    """Die alte _fitWidth-Rechnung ignorierte den Flex-Versatz: pan=(vw-w*z)/2. Dieselbe
    Rechnung hier eingesetzt muss den Plan neben das Bild schieben."""
    ep = _fn(src, "_planEinpassen")
    mut = ep.replace("panX:links-(ox||0), panY:oben-(oy||0)", "panX:links, panY:oben")
    assert mut != ep, "Mutation hat nicht gegriffen."
    r = _rundweg(node_exe, src, mut)
    assert not _ganz_sichtbar(r["dlg"], 412, 640), "Die Sichtbarkeitsprobe kann nicht anschlagen."


def test_1_viewer_passt_beim_oeffnen_ein(src):
    pv = _fn(src, "PlanViewerCanvas")
    eff = _zwischen(pv, "beim Oeffnen (und je neuer Seite) EINMAL ganz sichtbar einpassen", "}, [plan && plan.id, pageNum, pageDims, _imgReady, loading, loadError]);")
    assert 'if(_fitKeyRef.current === _key) return;' in eff, "Ohne Merker passt der Viewer bei jedem Render neu ein - Zoom/Pan gingen verloren."
    assert '_einpassen("seite")' in eff
    assert "pageDims._plan === plan.id && pageDims._pg === pageNum" in eff, "PDF wuerde mit den Massen der vorigen Seite eingepasst."
    assert "_imgReady !== _planSrc" in eff
    assert "onLoad: () => _setImgReady(_planSrc)" in pv
    assert "setPageDims({...dims, _plan: plan.id, _pg: pageNum});" in pv
    # Klick -> Prozent ueber den gepruefte Helfer, nicht ueber eine zweite Rechnung
    klick = _zwischen(pv, "const handleCanvasClick = (e) => {", "const _zoomCenter")
    assert "_planPctAusKlick(e.clientX, e.clientY, target.getBoundingClientRect())" in klick
    # alter 100-%-Stand (ohne Zeitstempel) wird NICHT mehr wiederhergestellt
    assert "typeof _s.t===\"number\" && (Date.now()-_s.t) < 15*60*1000" in pv
    assert "if(!_fitKeyRef.current) return;" in pv
    # Zuruecksetzen heisst eingepasst - an keiner Stelle mehr hart auf 100 %
    assert "setZoom(1); setPan({x: 0, y: 0}); }, title" not in pv
    assert 'e.key==="0"){ _einpassen("seite"); }' in pv
    # alle Zoom-Untergrenzen folgen zMinRef (sonst klemmt der erste Pinch die Einpassung auf 0.4)
    code = re.sub(r"/\*.*?\*/", "", pv, flags=re.S)
    assert "Math.max(0.4" not in code and ",0.4,6)" not in code


def test_1_mangel_dialog_nutzt_denselben_viewer(src):
    mps = _fn(src, "MangelPlanSetzen")
    assert "React.createElement(PlanViewerCanvas, { plan: plan, pinNr: null, tickets: _bisher" in mps
    # gespeichert wird pos.x/pos.y unveraendert (Prozent), keine Umrechnung mit Zoom
    assert "onSetzen({x:pend.x,y:pend.y,planId:plan.id,page:pend.page||1},plan)" in mps


# ── 2 images:[] in beiden Formularen (verhaltensnah) ──────────────────────

ADD_JS = r"""
var queue=[], cq=[], noch=[];
var window={__toast:function(){}};
var SQ={push:function(x){queue.push(x);}};
function captureAndQueue(file,et,id,pid,ctx){cq.push([file&&file.name,et,id,pid,ctx]);return Promise.resolve({});}
function _optionalChain(a){var v=a[0];for(var i=1;i<a.length;i+=2){if(v==null)return undefined;var op=a[i],fn=a[i+1];if(op==='access'||op==='optionalAccess')v=fn(v);else{var lhs=v;v=fn(function(){return lhs.apply(null,arguments);});}}return v;}
function uid(){return "m1";} function td2(){return "2026-11-14";} function _mgFristVorschlag(){return "2026-11-21";}
function _mgZuweisungMelden(){return 0;}
function setForms(){} function setName(){} function setNewPhotos(){} function setWorker(){} function setFrist(){} function setNeuPos(){} function setMgFotoAuf(){} function setMgFormAuf(){}
function setMgNochEins(v){noch.push(v);}
var B64="data:image/jpeg;base64,/9j/AAAA";
function lauf(mgFotoAuf){
  queue=[];cq=[];noch=[];
  var name="Steckdose locker", _vmIsField=false, isAdmin=true, _vmMid="", worker="w1", neuPos=null,
      p={id:"p1",name:"Haus"}, ebene="EG", frist="2026-11-21", prio="mittel", curUser={name:"Test"},
      newPhotos=[{thumb:B64+"thumb",full:B64+"full",file:{name:"a.jpg"}},{thumb:B64+"t2",full:B64+"f2",file:{name:"b.jpg"}}];
  %s
  add();
  return {queue:queue, cq:cq, noch:noch};
}
console.log(JSON.stringify({alt:lauf(false), foto:lauf(true)}));
"""


def _add_src(src):
    vm = _fn(src, "VMang")
    return _zwischen(vm, "const add=()=>", "/* v3.9.231 #2: Inverse")


def _add_lauf(node_exe, add_src):
    return json.loads(run_node_snippet(node_exe, ADD_JS % add_src))


def test_2_kein_base64_in_der_warteschlange_beide_formulare(node_exe, src):
    r = _add_lauf(node_exe, _add_src(src))
    for weg in ("alt", "foto"):
        q = r[weg]["queue"]
        posts = [x for x in q if x["url"] == "/api/defects" and x["method"] == "POST"]
        assert len(posts) == 1, weg
        assert posts[0]["body"]["images"] == [], "%s: images ist nicht leer" % weg
        assert "data:" not in json.dumps(q), "%s: Base64 in der Haupt-Warteschlange" % weg
        # die Fotos gehen trotzdem raus - je Foto ein captureAndQueue am Mangel
        assert [c[0] for c in r[weg]["cq"]] == ["a.jpg", "b.jpg"], weg
        assert all(c[1] == "defect" and c[2] == "m1" and c[3] == "p1" for c in r[weg]["cq"]), weg


def test_2_umkehrprobe_alte_vorschau_waere_rot(node_exe, src):
    a = _add_src(src)
    mut = a.replace("images:[],", "images:newPhotos.map(ph=>ph.thumb),")
    assert mut != a, "Mutation hat nicht gegriffen."
    r = _add_lauf(node_exe, mut)
    assert "data:" in json.dumps(r["alt"]["queue"]), "Die Base64-Probe kann nicht anschlagen."


def test_2_altes_formular_reicht_die_datei_an_captureandqueue(src):
    vm = _fn(src, "VMang")
    alt = _zwischen(vm, "ref: photoRef, type: \"file\"", "newPhotos.map((ph,i)=>")
    assert "setNewPhotos(prev=>[...prev,{thumb,full:ph.dataUrl,file}])" in alt, (
        "Ohne file im Eintrag laedt add() das Foto nie hoch.")


def test_2_alte_base64_bilder_bleiben_lesbar(src):
    vm = _fn(src, "VMang")
    gp = _zwischen(vm, "const getPhotos=(m)=>{", "/* v3.9.274")
    assert "const local=arr.map(ph=>typeof ph===\"string\"?ph:ph.full||ph.thumb||ph);" in gp


# ── 3 Folge-Angebot ──────────────────────────────────────────────────────

def test_3_folge_angebot_nur_nach_dem_foto_weg(node_exe, src):
    r = _add_lauf(node_exe, _add_src(src))
    assert r["foto"]["noch"] == [True], "Nach dem Foto-Weg kommt kein 'Noch einen?'."
    assert r["alt"]["noch"] == [False], "Das alte Formular bietet faelschlich die Kamera an."


def test_3_umkehrprobe_folge_angebot(node_exe, src):
    a = _add_src(src)
    mut = a.replace("setMgNochEins(_ausFoto);", "")
    assert mut != a
    r = _add_lauf(node_exe, mut)
    assert r["foto"]["noch"] != [True], "Die Folge-Probe kann nicht anschlagen."


def test_3_ein_tipp_oeffnet_die_kamera(src):
    vm = _fn(src, "VMang")
    b = _zwischen(vm, ", mgNochEins&&!mgFormAuf&&!mgFotoAuf&&React.createElement('div'", "/* ── Kundenmeldungen Review ── */")
    assert "Noch einen Mangel per Foto?" in b
    # Touch-UI-Rest (17.11.2026): Emoji -> _ik("kamera",18) davor; gepinnt bleibt das label um das Datei-Feld.
    i = b.find("_ik(\"kamera\",18), \"Noch einen\", React.createElement('input'")
    assert i > 0, "Der Knopf ist kein label um das Datei-Feld - dann ist es keine Nutzergeste."
    nah = b[i:i + 300]
    assert 'capture: "environment"' in nah and "onChange: _mgFotoZuerst" in nah
    assert b.count("minHeight:44") >= 2
    zuerst = _zwischen(vm, "const _mgFotoZuerst=", "// Load photos from server")
    assert "setMgNochEins(false)" in zuerst and "setMgFotoAuf(true)" in zuerst


def test_3_textfeld_behaelt_diktat(src):
    vm = _fn(src, "VMang")
    form = _zwischen(vm, ", mgFotoAuf&&React.createElement('div', { style: {...CC()", "\"✓ Mangel speichern\"")
    assert "React.createElement(SpeechWrap, { value: name, onChange: v=>setName(v)}" in form
    # Touch-UI-Rest (17.11.2026): das Mikrofon-Emoji im Feldnamen ist weg - MicBtn in SpeechWrap bleibt (Zeile darueber).
    assert "Was ist der Mangel?" in form


# ── 4 Mangel-Karte im CI ─────────────────────────────────────────────────

def test_4_status_farben_semantisch(node_exe, src):
    js = (
        "var UI={fehler:'F',fehlerBg:'Fb',achtung:'A',achtungTxt:'At',achtungBg:'Ab',neutralTxt:'N',neutralBg:'Nb',"
        "marke:'M',markeTxt:'Mt',markeBg:'Mb',linie:'L'};var V={dm:'D'};"
        + _fn(src, "_mgStFarbe") + _fn(src, "_mgPrioFarbe")
        + "console.log(JSON.stringify({o:_mgStFarbe('offen'),i:_mgStFarbe('in Behebung'),b:_mgStFarbe('behoben'),"
        "a:_mgStFarbe('abgelehnt'),u:_mgStFarbe('offen',true),ph:_mgPrioFarbe('hoch'),pm:_mgPrioFarbe('mittel')}));"
    )
    r = json.loads(run_node_snippet(node_exe, js))
    assert r["o"]["c"] == "A" and r["b"]["c"] == "M" and r["u"]["c"] == "F" and r["i"]["c"] == "N"
    assert len({r[k]["c"] for k in "oibu"}) == 4, "offen/in Arbeit/erledigt/ueberfaellig nicht unterscheidbar."
    assert r["a"]["c"] == "D" and r["a"]["c"] != r["b"]["c"], "abgelehnt traegt die Erledigt-Farbe."
    assert r["pm"]["c"] != "F" and r["ph"]["c"] != "F", "Prio benutzt die Fehlerfarbe (Rot ist ueberfaellig vorbehalten)."


def _karte(src):
    vm = _fn(src, "VMang")
    return _zwischen(vm, ", MANGEL_ST_SICHT.map(st=>{", "/* v3.9.1004 A: Plan-Setzen-Dialog")


def test_4_karte_ohne_eigenfarben(src):
    k = re.sub(r"/\*.*?\*/", "", _karte(src), flags=re.S)
    for f in ("#0ea5e9", "#ef4444", "#eab308", "#22c55e", "#f97316", "#3b82f6", "#6366f1", "#009640", "COLORS."):
        assert f not in k, "Eigenfarbe %s in der Mangel-Karte" % f
    assert "_mgStFarbe(" in k and "_mgPrioFarbe(" in k


def test_4_tippziele_44(src):
    k = _karte(src)
    status = _zwischen(k, "MANGEL_ST.map(ns=>{", "})")
    assert "minHeight:44,minWidth:44" in status and "...bsS()" in status
    assert "onClick: ()=>_placeOnPlan(m), style: {...bsS(),minHeight:44" in k
    assert "onClick: ()=>delM(m.id), 'aria-label': \"Mangel löschen\", style: {...bdS,minWidth:44,minHeight:44" in k
    assert "width:44,height:44,boxSizing:\"border-box\"" in k, "Foto-hinzufuegen ist kleiner als 44 px."
    assert "minWidth:44,minHeight:44,margin:\"-10px 0 -10px -10px\"" in k, "Sammel-Haken ohne 44-px-Ziel."
    # Umkehrprobe: die alten Kleinst-Knoepfe sind weg
    assert "padding:\"3px 8px\",borderRadius:12" not in k
    assert "width:36,height:36" not in k
