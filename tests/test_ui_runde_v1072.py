# -*- coding: utf-8 -*-
"""UI-Runde 1072 (Tablet-Pruefung 19.11.2026): sechs Funde, jeder mit echtem Code in node
und einer Umkehrprobe (alter Wortlaut -> Pruefung rot).

1 Formular-Tabellen schnitten am Tablet hochkant das Loeschkreuz und die Bemerkung ab.
2 Formular-Reiter: "Abnahme" lag rechts ausserhalb, ein Wisch auf der Reiterzeile blaetterte
  den Akten-Abschnitt weiter.
3 Projekt-Zeiterfassung: "5,00 / h" brach um, "Lagerleitung" lief aus der Spalte,
  "Beleucht-ung" brach mitten im Wort.
4 Kalender: "07:15 · 02:00" - die zweite Zahl ist eine Dauer.
5 Arbeitsscheine hochkant: "erledigt+abgerec…" und "Suche Nr, Kunde, A…".
6 Kopf "vor 40 Min" (Juprowa-Abruf) gegen Fenster "Letzter Sync 16:57" (App-Sync).
"""
import json
import re

import pytest

from conftest import _extract_fn, run_node_snippet


def _fns(src, *names):
    out = []
    for n in names:
        f = _extract_fn(src, n)
        assert f, "function %s fehlt" % n
        out.append(f)
    return "\n".join(out)


def _bp(src):
    return "\n".join("const %s=%s;" % (k, re.search(r"const %s=(\d+);" % k, src).group(1))
                     for k in ("BP_MOB", "BP_BREIT", "BP_QUER"))


def _stufen_js(src):
    return _bp(src) + "\n" + _fns(src, "_layoutStufe", "_formStapel", "_formTabKlasse",
                                   "_formTabelleKlasse", "_zeWochenSpalten")


# ---------------------------------------------------------------- 1 + 2 Stufen
def test_stufen_helfer_echt(node_exe, index_html):
    js = _stufen_js(index_html) + r"""
var r={};
[[800,1280],[390,844],[1280,800],[1440,900]].forEach(function(p){var st=_layoutStufe(p[0],p[1]);
  r[p[0]+"x"+p[1]]=[st,_formTabKlasse(st),_formTabelleKlasse(st,"sf"),_zeWochenSpalten(st)];});
console.log(JSON.stringify(r));"""
    r = json.loads(run_node_snippet(node_exe, js))
    assert r["800x1280"] == ["mittel", "form-tabs epk-fz-umbruch", "epk-fz-stapel fz-sf", "repeat(3,minmax(150px,1fr))"]
    assert r["390x844"] == ["schmal", "form-tabs epk-fz-umbruch", "epk-fz-stapel fz-sf", "repeat(3,minmax(0,1fr))"]
    assert r["1280x800"] == ["breit", "form-tabs", "", "repeat(6,minmax(120px,1fr))"]
    assert r["1440x900"][0] == "breit" and r["1440x900"][2] == ""


def test_stufen_css_vorhanden(index_html):
    for teil in (".form-tabs.epk-fz-umbruch{flex-wrap:wrap;overflow-x:visible}",
                 ".epk-fz-stapel thead{display:none}",
                 ".epk-fz-stapel td[data-l]::before{content:attr(data-l)",
                 ".epk-fz-stapel td.fz-weg{grid-column:1/-1;justify-self:end}",
                 ".epk-fz-stapel.fz-ah tr{grid-template-columns:repeat(3,minmax(0,1fr))}"):
        assert teil in index_html, teil


_FAKE_REACT = r"""
function _ce(type,props){var ch=[].slice.call(arguments,2);return {type:type,props:props||{},children:ch};}
var React={createElement:_ce};
function _walk(n,f){if(!n||typeof n!=="object")return;if(Array.isArray(n)){n.forEach(function(x){_walk(x,f);});return;}f(n);(n.children||[]).forEach(function(x){_walk(x,f);});}
function _find(root,pred){var out=[];_walk(root,function(n){if(n.props&&pred(n))out.push(n);});return out;}
var V={dm:"#666",ac:"#009640",acTx:"#007a33",bd:"#ddd",tx:"#111",mt:"#888"};var UI={fMeta:12,fSeite:22,fSeiteMob:18,zahlen:{fontVariantNumeric:"tabular-nums"}};
var window={innerWidth:800,innerHeight:1280};var mono="inherit";function CC(){return {};}function thS(){return {};}function tdSt(){return {};}function II(){return {};}function LL(){return {};}
var bdS={};var bsS=function(){return {};};var bgS={};
function _ik(){return null;}function _ikVw(a,b){return b;}function _ikT(a,b){return b;}function EditBadge(){return null;}function HeadFields(){return null;}
function FormActions(){return null;}function SavedList(){return null;}function SignaturePad(){return null;}function printForm(){}function td2(){return "2026-11-19";}function fdt(x){return x;}
"""


def _render_form(node_exe, src, comp, stufe, rows):
    js = _stufen_js(src) + _FAKE_REACT + _fns(src, comp) + r"""
var _state={rows:%s};var _setCalls=0;
function useEditable(){return {saved:[],editIdx:null,data:_state,setData:function(fn){_setCalls++;_state=typeof fn==="function"?fn(_state):fn;},load:function(){},clear:function(){},save:function(){},del:function(){}};}
var tree=%s({p:{id:"p1",name:"BVH",plz:"3720",ort:"R"},forms:{},setForms:function(){},stufe:%s});
var tab=_find(tree,function(n){return n.type==="table";})[0];
var tds=_find(tab,function(n){return n.type==="td";});
var del=_find(tab,function(n){return n.type==="button"&&n.props["aria-label"]==="Zeile löschen";});
var before=_state.rows.length;if(del[0])del[0].props.onClick();
console.log(JSON.stringify({cls:tab.props.className||"",minW:tab.props.style.minWidth,
  labels:tds.map(function(t){return t.props["data-l"]||null;}),
  klassen:tds.map(function(t){return t.props.className||null;}),
  delMin:del.map(function(b){return [b.props.style.minWidth,b.props.style.minHeight];}),
  rowsVorher:before,rowsNachher:_state.rows.length,setCalls:_setCalls}));""" % (json.dumps(rows), comp, json.dumps(stufe))
    return json.loads(run_node_snippet(node_exe, js))


@pytest.mark.parametrize("comp,zeile,labels", [
    ("FSF", {"bauteil": "", "gk": False, "steig": False, "allg": False, "bemerkung": ""},
     ["Bauteil/Ebene", "GK-Wände", "Steigsch.", "Allg.", "Bemerkung", None]),
    ("FDH", {"art": "Heizung", "geschoss": "EG", "druck": "", "dauer": "", "bemerkung": ""},
     ["Art", "Geschoß", "Druck (bar)", "Dauer (min)", "Bemerkung", None]),
    ("FAbn", {"raum": "", "leistung": "", "ergebnis": "i.O.", "bemerkung": ""},
     ["Raum", "Leistung", "Ergebnis", "Bemerkung", None]),
])
def test_formular_zeilen_gestapelt_mit_erreichbarem_kreuz(node_exe, index_html, comp, zeile, labels):
    r = _render_form(node_exe, index_html, comp, "mittel", [zeile, dict(zeile)])
    assert r["cls"].startswith("epk-fz-stapel"), r
    assert r["minW"] == 0
    assert r["labels"][:len(labels)] == labels
    assert r["klassen"][len(labels) - 2] == "fz-breit" and r["klassen"][len(labels) - 1] == "fz-weg"
    assert all(m == [44, 44] for m in r["delMin"]) and len(r["delMin"]) == 2
    # derselbe Handler: Zeile weg ueber setData
    assert r["rowsVorher"] == 2 and r["rowsNachher"] == 1 and r["setCalls"] == 1
    # breit: Tabelle wie bisher, Kreuz trotzdem 44
    b = _render_form(node_exe, index_html, comp, "breit", [zeile])
    assert b["cls"] == "" and b["minW"] == 500 and b["delMin"] == [[44, 44]]


def test_ausheiz_gestapelt(node_exe, index_html):
    zeile = {"tag": "1", "datum": "", "vl": "", "rl": "", "aussen": "", "bemerkung": "Aufheizphase"}
    r = _render_form(node_exe, index_html, "FAH", "schmal", [zeile])
    assert r["cls"] == "epk-fz-stapel fz-ah" and r["minW"] == 0
    assert r["labels"] == ["Tag", "Datum", "VL °C", "RL °C", "Außen", "Bemerkung"]
    assert r["klassen"][1] == "fz-zwei" and r["klassen"][5] == "fz-breit"


# ---------------------------------------------------------------- 2 Reiter + Wisch
_SWIPE_DOM = r"""
function _el(tag,attrs,parent){return {tag:tag,attrs:attrs||{},parentElement:parent||null,nodeType:1,style:{},scrollWidth:0,clientWidth:0,scrollLeft:0,
  closest:function(sel){var parts=sel.split(",");var n=this;while(n){for(var i=0;i<parts.length;i++){var p=parts[i].trim();
    var m=/^\[([a-z-]+)\]$/.exec(p);if(m&&Object.prototype.hasOwnProperty.call(n.attrs,m[1]))return n;
    if(/^[a-z]+$/.test(p)&&n.tag===p)return n;}n=n.parentElement;}return null;}};}
var document={body:{},querySelector:function(){return null;}};
var _react={useRef:function(v){return {current:v};}};
"""


def _wisch(node_exe, src, attrs_js):
    js = _stufen_js(src) + _FAKE_REACT + _SWIPE_DOM + _fns(src, "_swSperre", "_swScrollableX", "useSwipe", "VForm") + r"""
_react.useState=function(v){return [v,function(){}];};_react.useMemo=function(f){return f();};
function Row(){return null;}function _kurz(x){return x;}var FRegie=function(){},FSF=function(){},FDH=function(){},FAH=function(){},FAbn=function(){};
var tree=VForm({p:{id:"p1",name:"BVH"},forms:{},setForms:function(){},fTab:"sf",setFTab:function(){},ww:800});
var leiste=_find(tree,function(n){return typeof n.props.className==="string"&&n.props.className.indexOf("form-tabs")===0;})[0];
var attrs=__ATTRS__;
var shell=_el("div",{});var row=_el("div",attrs,shell);var btn=_el("button",{},row);
var gefeuert=0;var sw=useSwipe(function(){gefeuert++;return true;},function(){gefeuert++;return true;});
sw.onTouchStart({touches:[{clientX:300,clientY:100}],target:btn,currentTarget:shell});
sw.onTouchEnd({changedTouches:[{clientX:150,clientY:102}],stopPropagation:function(){}});
console.log(JSON.stringify({cls:leiste.props.className,noSwipe:leiste.props["data-no-swipe"]||null,gefeuert:gefeuert}));"""
    return json.loads(run_node_snippet(node_exe, js.replace("__ATTRS__", attrs_js)))


def test_reiterzeile_bricht_um_und_wisch_blaettert_nicht(node_exe, index_html):
    # die Attribute der echten Reiterzeile (aus VForm gerendert) in den echten useSwipe
    r = _wisch(node_exe, index_html, "leiste.props")
    assert r["cls"] == "form-tabs epk-fz-umbruch"
    assert r["noSwipe"] == "1"
    assert r["gefeuert"] == 0, "Wisch auf der Reiterzeile darf den Abschnitt nicht wechseln"
    # Umkehrprobe: dieselbe Geste ohne das Merkmal feuert den Abschnittswechsel
    u = _wisch(node_exe, index_html, "{}")
    assert u["gefeuert"] == 1


def test_reiterzeile_ohne_stopPropagation(index_html):
    i = index_html.index("function VForm(")
    teil = index_html[i:index_html.index("function SavedList(", i)]
    assert "stopPropagation" not in teil


# ---------------------------------------------------------------- 3 Wochenraster
def test_zeiterfassung_raster(index_html):
    i = index_html.index("function VZeit(")
    teil = index_html[i:index_html.index("function BerCell(", i)]
    # Tablet-Runde 1077 (7): zweites Argument DAYS.length (Sonntag erscheint mit Sonntagseintrag)
    assert 'gridTemplateColumns:_zeWochenSpalten(_layoutStufe(ww,(typeof window!=="undefined"?window.innerHeight:0)),DAYS.length),gap:6}}' in teil
    assert 'color:V.acTx,whiteSpace:"nowrap",...UI.zahlen}},fmtStd((entry.stunden||entry.hours||0))," h")' in teil  # Paket 13 (GF 24.11.2026): Stunden-Anzeige zentral ueber fmtStd (genau zwei Nachkommastellen, Komma, leer bleibt leer) - Pin bewusst nachgezogen
    assert "React.createElement('span',{style:{whiteSpace:\"nowrap\",...UI.zahlen}},(entry.von||\"\"),\"–\",(entry.bis||\"\"))" in teil
    assert 'title:(wk||{}).r||undefined' in teil and 'maxWidth:"100%",overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"' in teil
    assert "React.createElement('span',{style:{overflowWrap:\"break-word\",hyphens:\"manual\"}},entry.taetigkeit||entry.task)" in teil
    # keine eigene Breitenabfrage dazugekommen
    assert 'isMob?"repeat(3,minmax(0,1fr))":"repeat(6,1fr)"' not in teil


# ---------------------------------------------------------------- 4 Dauer
def test_dauer_kurz_echt(node_exe, index_html):
    js = _fns(index_html, "_dauerKurzDE") + r"""
console.log(JSON.stringify(["02:00:00","01:30:00","01:30","00:45:00","01:20:00","1.5","2,25","00:00:00","",null,"abc"].map(_dauerKurzDE)));"""
    r = json.loads(run_node_snippet(node_exe, js))
    assert r == ["2 h", "1,5 h", "1,5 h", "0,75 h", "1,33 h", "1,5 h", "2,25 h", "", "", "", ""]


def test_dauer_in_beiden_kalenderansichten(index_html):
    assert '[a.terminZeit||"", _dauerKurzDE(a.dauer), _kurz(a.arbeitsanweisungen,60)].filter(Boolean).join(" · ")' in index_html
    assert 'a.terminZeit||"", _dauerKurzDE(a.dauer)?(" · "+_dauerKurzDE(a.dauer)):"", calMonteur' in index_html
    # Umkehrprobe: die alte HH:MM-Anzeige neben der Startzeit ist weg
    assert "a.dauer?window._dauerToDisplay(a.dauer)" not in index_html
    assert 'a.dauer?(" · "+window._dauerToDisplay(a.dauer))' not in index_html


# ---------------------------------------------------------------- 5 Texte
def test_kachel_und_suchfeld_kurz(index_html):
    assert 'sub: "erledigt + abger." , title: "Fertig = erledigt + abgerechnet"' in index_html
    assert 'sub: "erledigt+abgerechnet"' not in index_html
    assert 'placeholder: "Nr., Kunde …"' in index_html
    assert "Suche Nr, Kunde, Arbeit..." not in index_html


# ---------------------------------------------------------------- 6 Sync-Alter
def test_sync_alter_echt(node_exe, index_html):
    js = _fns(index_html, "_syncStempelMs", "_alterSeitText") + r"""
var j=new Date(2026,10,19,17,6,0).getTime();
console.log(JSON.stringify([
 _alterSeitText(_syncStempelMs("2026-11-19 16:57"),j),
 _alterSeitText(_syncStempelMs("2026-11-19T17:06"),j),
 _alterSeitText(_syncStempelMs("2026-11-19 17:05"),j),
 _alterSeitText(_syncStempelMs("2026-11-19 15:00"),j),
 _alterSeitText(_syncStempelMs("2026-11-18 10:00"),j),
 _alterSeitText(_syncStempelMs(""),j),
 _alterSeitText(_syncStempelMs("kaputt"),j),
 _alterSeitText(j-40*60000,j)]));"""
    r = json.loads(run_node_snippet(node_exe, js))
    assert r == ["vor 9 Min", "gerade eben", "vor 1 Min", "vor 2 Std.", "vor 1 Tag", "", "", "vor 40 Min"]


def test_kopf_liest_den_app_sync(index_html):
    kopf = index_html[index_html.index("/* v3.9.1016 Juprowa-Sync-Hinweis"):index_html.index("/* Sync indicator */")]
    assert "_alterSeitText(_syncStempelMs(syncStatus.lastSync),Date.now())" in kopf
    assert "window._lastJuprowaSyncAt" not in kopf, "Kopf darf nicht wieder den Juprowa-Abruf zeigen"
    assert "setInterval" not in kopf
    # OFFA-Abruf bleibt sichtbar - im Sync-Fenster
    assert '"Letzter OFFA-Abruf: ", txt' in index_html
    # der vorhandene Herzschlag rendert den Kopf weiter (kein neuer Zeitgeber noetig)
    assert "const iv=setInterval(heartbeat,30000);" in index_html
    assert "setLastHeartbeat(Date.now());" in index_html
