"""v3.9.1092 - Tank-Eingabe: Dezimalfelder type=text + inputmode=decimal statt type=number.

App-Regel: Dezimal-Eingabefelder sind nie type=number (Komma wird verworfen/geleert,
Mausrad/Pfeile aendern Werte, iOS zeigt kein Komma). A55 Runde 4 fand alle Tank-Felder noch
auf type=number: QR-Schnelltanken, Batch-Tanken, Fahrzeug-Tankformular, _tankConfirmModal,
Tankfoto "Werte korrigieren". km-Felder: type=text + inputmode=numeric + pattern=[0-9]*.

Gelesen wird ueber _fzZahl ("72,77"/"72.77" -> 72.77, "1.234,5" -> 1234.5, "1.234" -> 1.234
wie vorher bei type=number - ein Punkt ohne Komma bleibt Dezimalpunkt). Angezeigt wird ueber
_tankEinDE (deutsches Komma, keine Tausenderpunkte).

Beweis "gleiche Zahl in der DB": der ECHTE _tankConfirmModal (alt aus 642a035 und neu) laeuft
in Node gegen eine Mini-DOM-Attrappe; fuer alt wird der Wert so eingespeist, wie ihn ein
type=number-Feld liefert (gueltige Zahl -> kanonisch, deutsches Komma -> Punkt, sonst "").
Umkehrproben: die Strukturpruefung muss auf dem alten Stand (642a035) anschlagen.
"""
import json
import os
import re
import subprocess

import pytest

from conftest import run_node_snippet, _extract_fn

ALT_REF = "642a035"


def _n(s):
    return s.replace("\r\n", "\n")


@pytest.fixture(scope="module")
def neu(index_html):
    return _n(index_html)


@pytest.fixture(scope="module")
def alt(repo_root):
    try:
        r = subprocess.run(["git", "-C", repo_root, "show", ALT_REF + ":index.html"],
                           capture_output=True, timeout=60)
    except Exception as e:  # pragma: no cover
        pytest.skip("git nicht verfuegbar: %s" % e)
    if r.returncode != 0:
        pytest.skip("Altstand %s nicht im Repo" % ALT_REF)
    return _n(r.stdout.decode("utf-8"))


# ── 1. Struktur: kein Tank-Feld mehr type=number ───────────────────────────
TANK_FELDER = [
    # (Name, Wiedererkennung im Quelltext, erwartete Art)
    ("Modal Liter", "mkField('🛢 Liter *','liter',", "decimal"),
    ("Modal Preis", "mkField('💶 Gesamtpreis (€)','preis',", "decimal"),
    ("Modal km", "mkField('🛣 km-Stand','km',", "numeric"),
    ("QR Liter", "value: qTankL,", "decimal"),
    ("QR Preis", "value: qTankP,", "decimal"),
    ("QR km", "value: qTankKm,", "numeric"),
    ("Batch Liter", "value: bLit,", "decimal"),
    ("Batch Preis", "value: bPreis,", "decimal"),
    ("Batch km", "value: bKm,", "numeric"),
    ("Formular Liter", "value: tankLiter,", "decimal"),
    ("Formular Preis", "value: tankPreis,", "decimal"),
    ("Formular km", "value: tankKm,", "numeric"),
    ("Tankfoto Liter", "value:_tankEdit.liter,", "decimal"),
    ("Tankfoto Preis", "value:_tankEdit.preis,", "decimal"),
    ("Tankfoto km", "value:(_tankEdit.km==null?\"\":_tankEdit.km),", "numeric"),
]


def _feld_text(src, marke):
    i = src.find(marke)
    if i < 0:
        return None
    a = max(src.rfind("React.createElement('input'", 0, i), src.rfind("mkField(", 0, i + 8))
    return src[a:i + len(marke) + 200]


def _probleme(src):
    p = []
    for name, marke, art in TANK_FELDER:
        t = _feld_text(src, marke)
        if t is None:
            p.append(name + ": nicht gefunden")
            continue
        if re.search(r"type: ?\"number\"|'number'", t):
            p.append(name + ": type=number")
        if not re.search(r"type: ?\"text\"|'text'", t):
            p.append(name + ": nicht type=text")
        if art == "decimal" and not re.search(r"inputMode: ?\"decimal\"|inputmode:'decimal'", t):
            p.append(name + ": kein inputmode=decimal")
        if art == "numeric" and not (re.search(r"inputMode: ?\"numeric\"|inputmode:'numeric'", t)
                                     and "[0-9]*" in t):
            p.append(name + ": kein inputmode=numeric+pattern")
    # Lesestellen: ueber _fzZahl, nicht parseFloat (parseFloat("1.234,5") = 1.234)
    for marke in ("const _qL=_fzZahl(qTankL);const _qP=_fzZahl(qTankP);",
                  "const _bL=_fzZahl(bLit);const _bP=_fzZahl(bPreis);",
                  "liter:_fzZahl(_tankEdit.liter)||0,preis:_fzZahl(_tankEdit.preis)||0,",
                  "const L=_fzZahl(rawL);",
                  "_fzDE((_fzZahl(qTankP)/_fzZahl(qTankL)),3)",
                  "_fzDE((_fzZahl(bPreis)/_fzZahl(bLit)),3)",
                  "_fzDE((_fzZahl(tankPreis)/_fzZahl(tankLiter)),3)"):
        if marke not in src:
            p.append("Lesestelle fehlt: " + marke)
    return p


def test_tank_felder_text_statt_number(neu):
    assert _probleme(neu) == []


def test_umkehrprobe_altstand_schlaegt_an(alt):
    p = _probleme(alt)
    assert any("type=number" in x for x in p), p
    assert sum(1 for x in p if x.endswith(": type=number")) == len(TANK_FELDER), p


def test_umkehrprobe_einzelfeld_zurueck_auf_number(neu):
    kaputt = neu.replace('type: "text", inputMode:"decimal", autoComplete:"off", value: qTankL,',
                         'type: "number", inputMode:"decimal", autoComplete:"off", value: qTankL,', 1)
    assert kaputt != neu
    assert _probleme(kaputt) == ["QR Liter: type=number", "QR Liter: nicht type=text"]


def test_keine_number_felder_im_tankbereich_mehr(neu):
    """Gegenprobe ueber den ganzen Fahrzeug-Bereich: kein type=number mit Tank-Wert mehr."""
    for m in re.finditer(r"type: ?[\"']number[\"']", neu):
        umg = neu[m.start():m.start() + 260]
        assert not re.search(r"qTank|tankLiter|tankPreis|tankKm|bLit|bPreis|bKm|_tankEdit", umg), umg[:200]
    assert "'liter','number'" not in neu and "'preis','number'" not in neu and "'km','number'" not in neu


# ── 2. Parser: echte Funktionen aus index.html ─────────────────────────────
def _parser_harness(src):
    fz = _extract_fn(src, "_fzZahl")
    ein = _extract_fn(src, "_tankEinDE")
    assert fz and ein
    return fz + "\n" + ein + "\n"


def test_parser_und_anzeige_rundlauf(node_exe, neu):
    snip = _parser_harness(neu) + r"""
var ein=["72,77","72.77"," 72,77 ","0,5","1234","1.234,56","1.234","abc","",null,52.3,0.5];
var out=ein.map(function(v){var n=_fzZahl(v);return [v,isFinite(n)?n:null,_tankEinDE(v)];});
var rund=[52.3,"52,3","52.3",1234.5,0.5,"1.234,5",72.77].map(function(v){return _fzZahl(_tankEinDE(v))===_fzZahl(v);});
process.stdout.write(JSON.stringify({out:out,rund:rund}));
"""
    r = json.loads(run_node_snippet(node_exe, snip))
    assert r["out"] == [
        ["72,77", 72.77, "72,77"], ["72.77", 72.77, "72,77"], [" 72,77 ", 72.77, "72,77"],
        ["0,5", 0.5, "0,5"], ["1234", 1234, "1234"], ["1.234,56", 1234.56, "1234,56"],
        ["1.234", 1.234, "1,234"], ["abc", None, "abc"], ["", None, ""], [None, None, ""],
        [52.3, 52.3, "52,3"], [0.5, 0.5, "0,5"],
    ]
    assert all(r["rund"]), r["rund"]


def test_lesestellen_gleich_wie_vorher(node_exe, neu):
    """qDoTank/batchSave/Tankfoto: alt parseFloat(String(x).replace(",",".")) bzw. parseFloat(x)||0
    auf dem Wert, den type=number lieferte; neu _fzZahl auf dem Rohtext. Wo alt definiert: gleich."""
    snip = _parser_harness(neu) + r"""
function numWert(raw){/* was ein type=number-Feld als .value liefert (Chrome, de-AT) */
  var t=String(raw);
  if(/^-?(\d+(\.\d+)?|\.\d+)([eE][+-]?\d+)?$/.test(t))return t;
  if(/^\d+,\d+$/.test(t))return t.replace(',','.');
  return "";}
var ein=["72,77","72.77"," 72,77 ","0,5","1234","1.234,56"];
var res=ein.map(function(raw){
  var a=numWert(raw);
  var altQ=a===""?null:parseFloat(String(a).replace(",","."));
  var altF=a===""?null:(parseFloat(a)||0);
  var neuQ=_fzZahl(raw);var neuF=_fzZahl(raw)||0;
  return {raw:raw,altQ:altQ,neuQ:isFinite(neuQ)?neuQ:null,altF:altF,neuF:neuF};});
process.stdout.write(JSON.stringify(res));
"""
    res = json.loads(run_node_snippet(node_exe, snip))
    for r in res:
        if r["altQ"] is not None:
            assert r["neuQ"] == r["altQ"], r
            assert r["neuF"] == r["altF"], r
    neu_by = {r["raw"]: r["neuQ"] for r in res}
    assert neu_by == {"72,77": 72.77, "72.77": 72.77, " 72,77 ": 72.77, "0,5": 0.5,
                      "1234": 1234, "1.234,56": 1234.56}
    # alt undefiniert (Feld leer -> kein Speichern): " 72,77 " und "1.234,56"
    assert [r["raw"] for r in res if r["altQ"] is None] == [" 72,77 ", "1.234,56"]


# ── 3. Der echte _tankConfirmModal (alt und neu) gegen eine Mini-DOM ────────
DOM = r"""
var _V={};var V={};var __ls=[];var __gesamt=[];
function El(tag){this.tagName=String(tag).toUpperCase();this.style={};this.kids=[];this.attrs={};this.value='';this.textContent='';this.type='';this.name='';}
El.prototype.appendChild=function(c){this.kids.push(c);return c;};
El.prototype.setAttribute=function(k,v){this.attrs[k]=v;};
El.prototype.addEventListener=function(){};El.prototype.focus=function(){};El.prototype.select=function(){};El.prototype.remove=function(){};
var document={createElement:function(t){var e=new El(t);__gesamt.push(e);return e;},body:new El('body'),activeElement:null,
  addEventListener:function(){},removeEventListener:function(){}};
var window={};
function lauf(init,cur,werte){
  __gesamt=[];
  var p=window._tankConfirmModal(init,cur,false);
  var inp={};__gesamt.forEach(function(e){if(e.tagName==='INPUT')inp[e.name]=e;});
  var vorbelegt={liter:inp.liter.value,preis:inp.preis.value,typL:inp.liter.type,typP:inp.preis.type,typK:inp.km.type};
  Object.keys(werte).forEach(function(k){inp[k].value=werte[k];});
  var btn=__gesamt.filter(function(e){return e.tagName==='BUTTON'&&/Speichern/.test(e.textContent);})[0];
  var fehler='';var erg='offen';
  p.then(function(r){erg=r;});
  btn.onclick();
  __gesamt.forEach(function(e){if(e.tagName==='DIV'&&/⚠️/.test(e.textContent))fehler=e.textContent;});
  return Promise.resolve().then(function(){return {vorbelegt:vorbelegt,erg:erg,fehler:fehler};});
}
"""


def _modal(src):
    a = src.index("window._tankConfirmModal=function(")
    b = src.index("\n};\n", a) + 4
    return src[a:b]


NUMWERT = r"""
function numWert(raw){var t=String(raw);
  if(/^-?(\d+(\.\d+)?|\.\d+)([eE][+-]?\d+)?$/.test(t))return t;
  if(/^\d+,\d+$/.test(t))return t.replace(',','.');
  return "";}
"""

EINGABEN = ["72,77", "72.77", " 72,77 ", "0,5", "1234", "1.234,56"]


def _modal_lauf(node_exe, src, als_number, mit_parser):
    pre = _parser_harness(src) if mit_parser else ""
    snip = DOM + pre + NUMWERT + _modal(src) + r"""
var EIN=%s;var NUM=%s;
var res=[];var kette=Promise.resolve();
EIN.forEach(function(raw){kette=kette.then(function(){
  var w=NUM?numWert(raw):raw;var pr=NUM?numWert(raw):raw;
  return lauf({datum:'2026-11-22',liter:'',preis:''},1000,{liter:w,preis:pr,km:'1200'}).then(function(r){res.push({raw:raw,erg:r.erg,fehler:r.fehler});});});});
kette.then(function(){return lauf({datum:'2026-11-22',liter:'52,3',preis:89.5,km:1200},1000,{});}).then(function(r){
  process.stdout.write(JSON.stringify({res:res,vor:r.vorbelegt,vorErg:r.erg}));});
""" % (json.dumps(EINGABEN), "true" if als_number else "false")
    return json.loads(run_node_snippet(node_exe, snip))


def test_modal_schreibt_gleiche_zahlen_wie_vorher(node_exe, neu, alt):
    a = _modal_lauf(node_exe, alt, als_number=True, mit_parser=False)
    n = _modal_lauf(node_exe, neu, als_number=False, mit_parser=True)
    alt_by = {r["raw"]: r for r in a["res"]}
    neu_by = {r["raw"]: r for r in n["res"]}
    for raw in EINGABEN:
        ar, nr = alt_by[raw], neu_by[raw]
        if isinstance(ar["erg"], dict):  # alt definiert -> neu exakt gleich (Liter, Preis, km, Datum)
            assert nr["erg"] == ar["erg"], (raw, ar, nr)
    # alt: " 72,77 " und "1.234,56" lieferte type=number als "" -> Liter-Fehler, nichts gespeichert
    assert alt_by[" 72,77 "]["erg"] == "offen" and "Liter" in alt_by[" 72,77 "]["fehler"]
    assert alt_by["1.234,56"]["erg"] == "offen"
    # neu: " 72,77 " wird jetzt gelesen; "1.234,56" scheitert weiter am Preis-Muster (kein Tausenderpunkt), nichts Falsches gespeichert
    assert neu_by[" 72,77 "]["erg"] == {"datum": "2026-11-22", "liter": 72.77, "preis": 72.77, "km": 1200}
    assert neu_by["1.234,56"]["erg"] == "offen" and "Gesamtpreis" in neu_by["1.234,56"]["fehler"]
    assert neu_by["72,77"]["erg"]["liter"] == 72.77 and neu_by["0,5"]["erg"]["preis"] == 0.5
    # Vorbelegung: alt Punkt im number-Feld, neu Komma im Textfeld; beide speichern dieselbe Zahl
    assert a["vor"] == {"liter": "52.3", "preis": "89.5", "typL": "number", "typP": "number", "typK": "number"}
    assert n["vor"] == {"liter": "52,3", "preis": "89,5", "typL": "text", "typP": "text", "typK": "text"}
    assert a["vorErg"] == n["vorErg"] == {"datum": "2026-11-22", "liter": 52.3, "preis": 89.5, "km": 1200}
