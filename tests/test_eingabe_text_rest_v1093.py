"""v3.9.1093 - die restlichen Zahlenfelder: type=text statt type=number (Fortsetzung von v3.9.1092 Tank).

App-Regel: Dezimalfelder type="text" inputMode="decimal", Ganzzahlfelder type="text" inputMode="numeric"
pattern="[0-9]*" - nie type="number" (Komma wird verworfen/geleert, Mausrad aendert Werte, iOS ohne Komma).

Neu:
  _ganzZahl(v)       Ganzzahl-Leser (Tausenderpunkte "12.345" -> 12345, "7,5" -> 7 wie parseInt bisher)
  ZahlEingabe        Bauteil fuer Felder, die schon im onChange rechnen (parseFloat(..)||38.5) und die
                     ZAHL zurueck in value schreiben: mit Fokus steht der getippte Text ("7," bleibt "7,"),
                     ohne Fokus der Wert deutsch (_tankEinDE). Ohne das Bauteil liesse sich kein Komma tippen.
Gelesen wird ueber _fzZahl (behaelt das Minus: Ausheizprotokoll Aussen, Ueberstunden, Temperatur).

Lohnnahe Felder (Zeiterfassung Stunden, Kontingent, Export-Pruefliste): Node-Beweis an den ECHTEN
Ausdruecken aus index.html - fuer jede frueher gueltige Eingabe dieselbe Zahl wie vorher
(alt: type=number lieferte "7,5" im de-Browser als "7.5"), und "7,5" wird nie 7.
"""
import json
import re
import subprocess

import pytest

from conftest import run_node_snippet, _extract_fn

ALT_REF = "6cba51b"  # v3.9.1092, letzter Stand mit den type=number-Feldern


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


# ── 1. Inventar: kein type=number-Eingabefeld mehr ─────────────────────────
_NUM = re.compile(r"""type\s*:\s*["']number["']|type\s*=\s*["']number["']|\.type\s*=(?!=)[^;]{0,40}\?\s*["']number["']"""
                  r"""|setAttribute\(\s*["']type["']\s*,\s*["']number["']|mkField\([^)]{0,80},\s*["']number["']""")


def _treffer(src):
    """Alle Stellen, an denen ein Eingabefeld type=number bekommen koennte - minus die zwei bekannten
    Nicht-Felder: der CSS-Selektor :not([type="number"]) und Spaltenbeschreibungen der Export-Pruefliste
    ({key:..,type:"number"}), die der Pruefliste-Renderer als text+decimal zeichnet (Test 2)."""
    out = []
    for m in _NUM.finditer(src):
        vor = src[max(0, m.start() - 12):m.start()]
        if vor.endswith(':not(['):
            continue
        obj = src[src.rfind("{", 0, m.start()):m.start()]
        if re.match(r"\{\s*key\s*:", obj):
            continue
        out.append(src.count("\n", 0, m.start()) + 1)
    return out


def test_kein_type_number_eingabefeld(neu):
    assert _treffer(neu) == [], "type=number-Felder uebrig in Zeilen %s" % _treffer(neu)


def test_umkehr_altstand_hatte_viele(alt):
    t = _treffer(alt)
    # v3.9.1092: 11 Felder (Tank) waren schon weg; uebrig waren rund 50 Stellen.
    assert len(t) >= 40, t


def test_umkehr_koeder_wird_erkannt(neu):
    for koeder in ("React.createElement('input', { type: \"number\", value: x})",
                   "h('input',{type:'number',step:'0.01'})",
                   "el.type='number';",
                   "mkField('Liter','liter','number',{})"):
        assert len(_treffer(neu + "\n" + koeder)) == 1, koeder


def test_spaltenbeschreibungen_gezaehlt(neu):
    """Die erlaubten {key:..,type:"number"}-Spalten sind genau die bekannten - eine neue faellt auf."""
    n = len(re.findall(r"""\{\s*key\s*:[^{}]{0,120}?type\s*:\s*["']number["']""", neu))
    assert n == 9, n  # 7241 hours, 14887+15053 stunden, 25549-25552 (4), 28876 Wochen-Spalten, 28986 stunden


# ── 2. Export-Pruefliste: Renderer zeichnet Zahlenspalten als text ────────
def _pruefliste_block(src):
    a = src.index("const inp=document.createElement('input');")
    b = src.index("td.appendChild(inp);", a)
    return src[a:b]


def test_pruefliste_renderer_text(neu):
    blk = _pruefliste_block(neu)
    assert "'number'?'number'" not in blk
    assert "inp.inputMode='decimal'" in blk
    assert "_fzZahl(raw)" in blk and "parseFloat(raw)" not in blk
    assert "_tankEinDE(v)" in blk


def test_umkehr_pruefliste_alt(alt):
    blk = _pruefliste_block(alt)
    assert "'number'?'number'" in blk and "parseFloat(raw)" in blk


# ── 3. Node: Leser und lohnnahe Ausdruecke ────────────────────────────────
def _helfer(src):
    return "\n".join(_extract_fn(src, n) for n in ("_fzZahl", "_tankEinDE", "_ganzZahl", "_ktgStd"))


def _node(node_exe, js):
    return json.loads(run_node_snippet(node_exe, js))


def test_leser(node_exe, neu):
    js = _helfer(neu) + r"""
var F=["7.5","7,5","8","0,25","-5,5","-2.5","1.234,5","","abc",null];
var G=["8","12.345","7,5","-3","","x",null,"1.234"];
console.log(JSON.stringify({f:F.map(_fzZahl),g:G.map(_ganzZahl),d:[7.5,"7.5","-5.5",0,null,"",192.5,"abc"].map(_tankEinDE)}));
"""
    r = _node(node_exe, js)
    assert r["f"][:8] == [7.5, 7.5, 8, 0.25, -5.5, -2.5, 1234.5, None]  # NaN -> JSON null
    assert r["f"][8] is None and r["f"][9] is None
    assert r["g"] == [8, 12345, 7, -3, None, None, None, 1234]
    assert r["d"] == ["7,5", "7,5", "-5,5", "0", "", "", "192,5", "abc"]


# Echte onChange-Ausdruecke der lohnnahen Felder (aus index.html geschnitten, nicht abgeschrieben)
_LOHN = re.compile(r"(?:setAddHours\((_fzZahl\(e\.target\.value\)\|\|0)\))"
                   r"|(?:\b(woche|vorjahr|ueberstunden|hours):(_fzZahl\(e\.target\.value\)\|\|[0-9.]+))"
                   r"|(?:\bstunden:(_ktgStd\(_fzZahl\(e\.target\.value\)\)))")


def _lohn_ausdruecke(src):
    out = []
    for m in _LOHN.finditer(src):
        out.append(m.group(1) or m.group(3) or m.group(4))
    return out


def test_lohnfelder_gleiche_zahl_wie_vorher(node_exe, neu):
    aus = _lohn_ausdruecke(neu)
    # 2x Stunden (Zeiterfassung, Wochen-Erfassung), 2x je woche/stunden/vorjahr/ueberstunden (Kontingent
    # Tabelle + Karte), 1x editEntry.hours = 11
    assert len(aus) == 11, aus
    js = _helfer(neu) + r"""
var A=%s;
/* alt: type=number im de-Browser lieferte "7,5" als "7.5"; der alte Ausdruck las mit parseFloat bzw. _ktgStd(roh) */
var ROH=["7.5","7,5","8","0,25"], ALT=["7.5","7.5","8","0.25"];
var res=A.map(function(x){
  var f=new Function("e","_fzZahl","_ktgStd","return "+x);
  var altx=x.replace("_ktgStd(_fzZahl(e.target.value))","_ktgStd(e.target.value)").replace("_fzZahl(e.target.value)","parseFloat(e.target.value)");
  var g=new Function("e","_fzZahl","_ktgStd","return "+altx);
  return {x:x,neu:ROH.map(function(v){return f({target:{value:v}},_fzZahl,_ktgStd);}),
          alt:ALT.map(function(v){return g({target:{value:v}},_fzZahl,_ktgStd);}),
          bug:g({target:{value:"7,5"}},_fzZahl,_ktgStd)};
});
console.log(JSON.stringify(res));
""" % json.dumps(aus)
    for r in _node(node_exe, js):
        assert r["neu"] == r["alt"], r
        assert r["neu"][1] == 7.5, r          # "7,5" wird nie 7
        assert r["bug"] == 7, r               # Umkehrprobe: der alte Leser auf Text machte 7


def test_ueberstunden_negativ(node_exe, neu):
    aus = [a for a in _lohn_ausdruecke(neu) if a.endswith("||0")]
    js = _helfer(neu) + "var f=new Function('e','_fzZahl','return '+%s);console.log(JSON.stringify([f({target:{value:'-2,5'}},_fzZahl),f({target:{value:'-'}},_fzZahl)]));" % json.dumps(aus[0])
    assert _node(node_exe, js) == [-2.5, 0]


def test_pruefliste_eingabe_node(node_exe, neu):
    blk = _pruefliste_block(neu)
    a = blk.index("inp.addEventListener('input',")
    lst = blk[a:blk.index("});", a) + 3]
    js = _helfer(neu) + r"""
function lauf(v){var r={};var col={type:'number',key:'h'};var cb;var inp={value:v,addEventListener:function(t,f){cb=f;}};
%s
cb();return r.h;}
console.log(JSON.stringify(["7.5","7,5","8","0,25","","abc"].map(lauf)));
""" % lst
    assert _node(node_exe, js) == [7.5, 7.5, 8, 0.25, "", ""]


def test_zahleingabe_bauteil(node_exe, neu):
    js = _helfer(neu) + _extract_fn(neu, "ZahlEingabe") + r"""
var ST=null;var React={useState:function(i){return [ST,function(){}];},createElement:function(t,p){return p;}};
var p1=ZahlEingabe({value:7.5,inputMode:'decimal',onChange:function(){}});
ST="7,";var p2=ZahlEingabe({value:7,inputMode:'decimal'});
ST=null;var p3=ZahlEingabe({value:"",inputMode:'numeric',pattern:'[0-9]*'});
console.log(JSON.stringify([p1.type,p1.value,p1.inputMode,p2.value,p3.type,p3.inputMode,p3.value]));
"""
    assert _node(node_exe, js) == ["text", "7,5", "decimal", "7,", "text", "numeric", ""]


# ── 4. Lesepfade beim Speichern (Quelltext-Anker) ─────────────────────────
NEU_LESER = [
    "if(typeof fv==='number'){var n=_fzZahl(vals[k]);",
    "var _num=function(x){var n=_fzZahl(x);",
    "skonto_prozent:_fzZahl(data.skonto_prozent)||0,jahresbonus_prozent:_fzZahl(data.jahresbonus_prozent)||0,datanorm_intervall_tage:_ganzZahl(data.datanorm_intervall_tage)||28",
    "betrag:Math.max(0,_fzZahl(e.target.value)||0)",
    "budgetStunden:e.target.value===\"\"?null:Math.max(0,_fzZahl(e.target.value)||0)",
    "budgetEuro:e.target.value===\"\"?null:Math.max(0,_fzZahl(e.target.value)||0)",
    "temperatur:entry.temperatur?_fzZahl(entry.temperatur)||0:null",
    "const setMenge=(key,val)=>{const n=Math.max(0,_fzZahl(val)||0);",
    "const mng=_fzZahl(r.menge)||1;",
    "const v=Math.max(0.01,_fzZahl(e.target.value)||1);",
    "finkStunden:_fzZahl(val)||0",
    "const kms=_ganzZahl(form.km_start),kme=_ganzZahl(form.km_ende);",
    "const _kfl=form.kraftstoff_liter?_fzZahl(form.kraftstoff_liter):null;const _kfp=form.kraftstoff_preis_liter?_fzZahl(form.kraftstoff_preis_liter):null;",
    "const km=_ganzZahl(qKm);",
    "kmStand:_ganzZahl(nf.kmStand)||0,km_stand:_ganzZahl(nf.kmStand)||0",
    "km:_ganzZahl(e.target.value)||0",
    "kosten:Math.max(0,_fzZahl(e.target.value)||0)",
    "miete_pro_jahr:form.miete_pro_jahr!==\"\"?(_fzZahl(form.miete_pro_jahr)||0):null",
    "betrag:verrBetrag!==\"\"?(_fzZahl(verrBetrag)||0):null",
    "kosten:_fzZahl(e.target.value)||0",
    "wert:Math.max(0,_fzZahl(e.target.value)||0)",
]
ALT_LESER = [
    "parseFloat(vals[k])", "parseFloat(data.skonto_prozent)", "temperatur:entry.temperatur?parseFloat(entry.temperatur)",
    "finkStunden:parseFloat(val)", "kontingent", "setAddHours(parseFloat(e.target.value)||0)",
    "woche:parseFloat(e.target.value)||38.5", "stunden:_ktgStd(e.target.value)",
]


@pytest.mark.parametrize("anker", NEU_LESER)
def test_leser_im_speicherpfad(neu, anker):
    assert anker in neu


@pytest.mark.parametrize("anker", [a for a in ALT_LESER if a != "kontingent"])
def test_alte_leser_weg(neu, alt, anker):
    assert anker not in neu
    assert anker in alt  # Umkehrprobe: der Anker traf den Altstand


def test_ganzzahlfelder_numeric_pattern(neu):
    for marke in ("value: qKm,", "value: nf.kmStand,", "value: kmVal,", "value: s.km||\"\",", "value:form.km_start,",
                  "value:form.km_ende,", "value:f.aufbewahrung_tage,", "value: form.fortschritt,",
                  "value: suppEdit.datanorm_intervall_tage||28,"):
        i = neu.index(marke)
        kopf = neu[max(neu.rfind("createElement('input'", 0, i), neu.rfind("h('input'", 0, i)):i]
        assert re.search(r"""type\s*:\s*["']text["']""", kopf), marke
        assert re.search(r"""inputMode\s*:\s*["']numeric["']""", kopf), marke
        assert "[0-9]*" in kopf, marke
