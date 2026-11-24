# -*- coding: utf-8 -*-
"""Tablet-Runde 1077 (Tablet-Vollpruefung 19.11.2026, v1071-1074): Funde 1-12.

Jeder Fund mit echtem Code (aus index.html gezogen und in node ausgefuehrt, wo es
eine Rechnung gibt) und einer Umkehrprobe (alter Wortlaut -> Pruefung rot).
"""
import json
import re

from conftest import _extract_fn, run_node_snippet


def _fn(src, name):
    f = _extract_fn(src, name)
    assert f, "function %s fehlt" % name
    return f


_ENDE = {"_asKopfDeck": "};/*", "_asRollHoehe": "\n", "_absH": "\n"}


def _const_arrow(src, name):
    """Die Konstante `const NAME=...` woertlich aus index.html (Ende je Name festgelegt)."""
    a = src.index("const %s=" % name)
    ende = _ENDE[name]
    b = src.index(ende, a) + (2 if ende == "};/*" else 0)
    return src[a:b].rstrip("\r")


# ---------------------------------------------------------------- 1 AS hochkant
def _as_kasten_ok(src):
    return ('className: "epk-as-roll", style: {overflowX:"auto",scrollbarWidth:"thin",WebkitOverflowScrolling:"touch",..._asRollHoehe()}' in src
            and "table.epk-as-mittel thead th { z-index: 2 !important; }" in src
            and "table.epk-as-mittel thead th:first-child { z-index: 3 !important; }" in src)


def test_1_as_kasten_rollt_in_mittel_senkrecht(node_exe, index_html):
    assert _as_kasten_ok(index_html)
    js = "var V={cd:'#fff',bd:'#ddd'};var _dark=false;var _asBoxH=900;\n" + \
        _const_arrow(index_html, "_asKopfDeck") + "\n" + _const_arrow(index_html, "_asRollHoehe") + r"""
var r={};var _asMittel=true;r.m=[_asRollHoehe(),_asKopfDeck()];
_asMittel=false;r.b=[_asRollHoehe(),_asKopfDeck()];
_asMittel=true;_asBoxH=0;r.ohne=_asRollHoehe();
console.log(JSON.stringify(r));"""
    r = json.loads(run_node_snippet(node_exe, js))
    assert r["m"][0] == {"maxHeight": 900, "overflowY": "auto"}
    assert r["m"][1]["background"].endswith(",#fff") and "inset 0 -2px 0" in r["m"][1]["boxShadow"]
    assert r["b"] == [{}, {}], "breit unveraendert"
    assert r["ohne"]["maxHeight"] == "calc(100dvh - 160px)"
    # alle 13 Koepfe deckend, Nummer klebt weiter links
    a = index_html.index("React.createElement('table', { className: _asMittel?\"epk-as-mittel\"")
    b = index_html.index("React.createElement('tbody', {}, sorted.map", a)
    assert index_html[a:b].count("{...thS(),..._asKopfDeck(),") == 13
    # Owner-Messung 1089: der klebende Nummer-Kopf deckend getoent statt weiss - Pin nachgezogen
    assert "..._asKopfKlebt(_asNrKlebt())}, role: \"button\"" in index_html[a:b]
    assert "minWidth:112" in index_html[a:b] and "minWidth:104" in index_html[a:b]


def test_1_umkehrprobe(index_html):
    alt = index_html.replace(",..._asRollHoehe()}, ref: _asRollRef}", "}, ref: _asRollRef}", 1)
    assert alt != index_html and not _as_kasten_ok(alt)


# ---------------------------------------------------------------- 2 AS-Zeile
def test_2_push_knopf_hat_namen_und_abstand_klickweg_gleich(index_html):
    assert ("onClick: e=>{e.stopPropagation();doSinglePush(a.id);}, disabled: jupPushing, style: {background:a.push_error?\"#ef4444\":\"#f59e0b\""
            in index_html), "Klickweg/Stil-Anfang unveraendert"
    assert "'aria-label': a.push_error?\"Push erneut senden\":\"An OFFA senden\"" in index_html
    assert "opacity:jupPushing?.5:1,marginRight:6" in index_html
    assert "table.epk-as-mittel td .epk-ruhig { border-color: rgba(127,127,127,.55) !important; }" in index_html


def test_2_aufgeschoben_ist_eine_offa_prioritaet(index_html):
    """Befund 'aufgeschoben im Prioritaeten-Feld' geprueft und NICHT geaendert: OFFA-Code 2 ist
    die Prioritaet 'aufgeschoben' (Pull- und Push-Abbildung). Wer sie aus AS_PRIO nimmt, zeigt
    solche Scheine mit falschem Wert."""
    assert "'2':'aufgeschoben'" in index_html.split("const JUPROWA_PRIO_MAP=")[1][:200]
    assert "aufgeschoben:'2'" in index_html.split("const JUPROWA_PRIO_REV=")[1][:200]
    assert 'aufgeschoben:{l:"aufgeschoben"' in index_html.split("const AS_PRIO=")[1][:200]


# ---------------------------------------------------------------- 3 Abwesenheiten
def test_3_stunden_mit_komma_und_einer_stelle(node_exe, index_html):
    # Paket 13 (GF 24.11.2026): Stunden-Anzeige zentral ueber fmtStd (genau zwei Nachkommastellen, Komma, leer bleibt leer) - Pin bewusst nachgezogen: _absH ruft fmtStd - zwei Stellen statt einer
    js = _fn(index_html, "_n") + "\n" + _fn(index_html, "_fzZahl") + "\n" + _fn(index_html, "fmtStd") + "\n" + _const_arrow(index_html, "_absH") + r"""
console.log(JSON.stringify([_absH(192.5,1),_absH(68.5,1),_absH(38.5,1),_absH(0,1),_n(192.5,0)]));"""
    r = json.loads(run_node_snippet(node_exe, js))
    assert r[:4] == ["192,50", "68,50", "38,50", "0,00"]
    assert r[4] == "193", "Umkehrprobe: der alte Formatierer rundete 192,5 auf 193"
    # Paket 13 (GF 24.11.2026): Stunden-Anzeige zentral ueber fmtStd (genau zwei Nachkommastellen, Komma, leer bleibt leer) - Pin bewusst nachgezogen: _absH ruft fmtStd (zwei Stellen) - die Aufrufe bleiben
    assert '"Rest ",(kontUnlesbar?"–":(resturlaub(m).toFixed?_absH(resturlaub(m),1):resturlaub(m))+" h")' in index_html
    assert "_absH((ys.krankenstandStd||0),1)" in index_html
    assert ":_absH(ks.woche||38.5,1))" in index_html
    assert ':(kontUnlesbar?"–":_absH(_ktgStd(ks.stunden),1)))' in index_html
    assert ':(kontUnlesbar?"–":_absH(ks.vorjahr||0,1)))' in index_html
    assert "_n(resturlaub(m),0)" not in index_html
    assert 'color:UI.markeTxt/* Tablet-Runde 1077 (3)' in index_html


# ---------------------------------------------------------------- 4 Statistik
def _stat_js(src):
    return "const _ymd=d=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,\"0\")}-${String(d.getDate()).padStart(2,\"0\")}`;\n" + \
        _fn(src, "_stTagSchluessel") + "\n" + _fn(src, "_stTagesreihe")


def test_4_tagesreihe_30_tage_gueltige_daten(node_exe, index_html):
    js = _stat_js(index_html) + r"""
var heute=new Date(2026,10,19,15,0,0).getTime();
var byD={};byD[_stTagSchluessel(new Date(2026,10,19,10,0,0).toISOString())]={cnt:22,u:new Set(["a","b"])};
byD["2026-11-01"]={cnt:3,u:new Set(["a"])};
var r=_stTagesreihe(byD,heute,30);
var neu=r.map(function(d){return isNaN(new Date(d.day+"T00:00:00").getTime());});
var alt={d:"2026-11-19",cnt:1,users:1};
console.log(JSON.stringify({n:r.length,erst:r[0].day,letzt:r[29],leer:r[5],ungueltig:neu.filter(Boolean).length,
  altUngueltig:isNaN(new Date(alt.day+"T00:00:00").getTime())}));"""
    r = json.loads(run_node_snippet(node_exe, js))
    assert r["n"] == 30
    assert r["erst"] == "2026-10-21"
    assert r["letzt"] == {"day": "2026-11-19", "d": "2026-11-19", "cnt": 22, "users": 2}
    assert r["leer"]["cnt"] == 0
    assert r["ungueltig"] == 0
    assert r["altUngueltig"] is True, "Umkehrprobe: die alte Reihe (nur d) ergab Invalid Date"


def test_4_statistik_anzeige(index_html):
    assert "const daily=_stTagesreihe(_byD,Date.now(),30);" in index_html
    assert ".slice(-14).map(d=>({d,cnt" not in index_html
    assert 'juprowa_pull:"OFFA-Abruf",juprowa_push:"OFFA-Senden"' in index_html
    assert ",actions_7d:_alUnlesbar?null:(_a7[String(u.id)]||0)}));" in index_html
    assert 'u.actions_7d==null?"—":u.actions_7d' in index_html
    assert 'u.logins>0&&React.createElement' in index_html and 'u.logins||0, "x"' not in index_html
    assert '.replace(".",","), " Benutzer/Tag"' in index_html


# ---------------------------------------------------------------- 5 Wechselkennzeichen
def test_5_mein_fahrzeug_und_detailkopf(node_exe, index_html):
    js = "\n".join(_fn(index_html, n) for n in ("_fzKzKurz", "_fzKzAktiv", "_fzKzAnzeige")) + r"""
function _fzArchiviert(f){return !!f.archiviert;}
var a={id:1,kennzeichen:"TU-266BP (X5)",modell:"X5"},b={id:2,kennzeichen:"TU-266BP (Golf)",modell:"Golf"};
console.log(JSON.stringify([_fzKzAnzeige(a,[a,b]),a.kennzeichen]));"""
    r = json.loads(run_node_snippet(node_exe, js))
    assert r[0] == "TU-266BP · X5" and r[1] == "TU-266BP (X5)"
    assert '_fzKzAnzeige(_meinFz,fahrzeuge)||"—")' in index_html
    assert "_fzKzAnzeige(selFz,fahrzeuge)||selFz.kennzeichen)" in index_html
    assert '_meinFz.kennzeichen||"—")' not in index_html


# ---------------------------------------------------------------- 7 Projekt-Zeiterfassung
def test_7_sonntag_nur_mit_eintrag(node_exe, index_html):
    js = _fn(index_html, "_zeWochenSpalten") + "\n" + _fn(index_html, "_zeWochenTage") + r"""
console.log(JSON.stringify([_zeWochenTage([{datum:"2026-11-19"}],"2026-11-22"),_zeWochenTage([{date:"2026-11-22T08:00"}],"2026-11-22"),
 _zeWochenSpalten("breit"),_zeWochenSpalten("breit",7),_zeWochenSpalten("mittel",7)]));"""
    r = json.loads(run_node_snippet(node_exe, js))
    assert r[0] == ["Mo", "Di", "Mi", "Do", "Fr", "Sa"]
    assert r[1][-1] == "So" and len(r[1]) == 7
    assert r[2] == "repeat(6,minmax(120px,1fr))" and r[3] == "repeat(7,minmax(120px,1fr))"
    assert r[4] == "repeat(3,minmax(150px,1fr))"
    assert "const DAYS=_zeWochenTage(pe,isoDate(6));" in index_html
    assert 'gridTemplateColumns:"repeat("+DAYS.length+",1fr) auto"' in index_html


# ---------------------------------------------------------------- 9 Chef / Push-Anzeige
def test_9_push_fehler_kurz(node_exe, index_html):
    js = _fn(index_html, "_pushFehlerKurz") + r"""
console.log(JSON.stringify([_pushFehlerKurz('HTTP 500: {"code":"XX000","details":null,"hint":null,"message":"Failed"}'),
 _pushFehlerKurz("TypeError: Failed to fetch"),_pushFehlerKurz("HTTP 409: Konflikt"),_pushFehlerKurz(null),_pushFehlerKurz("")]));"""
    r = json.loads(run_node_snippet(node_exe, js))
    assert r[0] == "OFFA-Server nicht erreichbar – wird automatisch erneut versucht"
    assert r[1] == r[0]
    assert r[2].startswith("OFFA hat die Änderung nicht angenommen")
    assert r[3] == "" and r[4] == ""
    assert "title:String(form.push_error),'data-push-fehler':\"1\"" in index_html
    assert "_pushFehlerKurz(form.push_error))" in index_html
    assert "titel:'OFFA-Senden ausstehend'" in index_html
    assert "aeltester seit '+_asPushStauInfo.alter+' · '+_asPushStauInfo.grund" not in index_html


def test_9_chef_zahlen_und_typen(index_html):
    # A55 1080 (4): Pin bewusst nachgezogen - topOver ist nicht mehr auf 8 gekappt (Titel "die aeltesten 8",
    # Plakette 20 und "alle 8 anzeigen" widersprachen sich am Handy). Liste = alle ueberfaelligen, Plakette
    # bleibt ueberfaellige; Gleichheit Liste/Plakette laeuft in Node in tests/test_a55_funde_v1080.py.
    assert "titel:'Kritisch überfällig',zahl:ueberfaellige," in index_html
    assert "localeCompare(b.terminBestaetigt||b.terminVorschlag||'')).slice(0,8),[arbeitsscheine,_td]);" not in index_html
    assert "titel:'Kritisch überfällig',zahl:topOver.length" not in index_html
    assert "((AT_T[a.typ]&&AT_T[a.typ].l)||a.typ)" in index_html


def test_9_push_kern_unberuehrt(index_html):
    """Nur Anzeige: kein Aufruf von _juprowaPush/_juprowaSanitize in den geaenderten Stellen."""
    for teil in re.findall(r"Tablet-Runde 1077 \(9\)[^\n]{0,400}", index_html):
        assert "_juprowaPush(" not in teil and "_juprowaSanitize(" not in teil


# ---------------------------------------------------------------- 10 Dispo
def test_10_dispo_kachel_text_mindestens_90px(index_html):
    assert "h('div',{style:{flex:\"1 1 90px\",minWidth:0}}" in index_html
    assert 'display:"flex",flexWrap:"wrap"/* Tablet-Runde 1077 (10) */' in index_html
    assert 'marginLeft:"auto",paddingLeft:6,minWidth:44}}' in index_html
    assert 'letterSpacing:.2,whiteSpace:"nowrap"}},(isFix?_dpIkTxt' in index_html


# ---------------------------------------------------------------- 11 Wisch
def _swipe_js(src):
    return r"""
var _react={useRef:function(v){return {current:v};}};
var document={body:{nodeType:1},querySelector:function(){return null;}};
function getComputedStyle(n){return {overflowX:n._ov||"visible"};}
""" + _fn(src, "_swScrollableX") + "\n" + _fn(src, "_swQuerrollerSperrt") + "\n" + _fn(src, "_swSperre") + "\n" + _fn(src, "useSwipe") + r"""
function knoten(par,o){var n={nodeType:1,parentElement:par,scrollWidth:100,clientWidth:100,scrollLeft:0,_ov:"visible",closest:function(){return null;}};for(var k in o)n[k]=o[k];return n;}
function lauf(imKasten){
  var main=knoten(null,{});var kasten=knoten(main,{scrollWidth:1300,clientWidth:700,scrollLeft:600,_ov:"auto"});
  var ziel=imKasten?knoten(kasten,{}):knoten(main,{});
  var links=0;var sw=useSwipe(function(){links++;},function(){});
  sw.onTouchStart({touches:[{clientX:500,clientY:300}],target:ziel,currentTarget:main});
  sw.onTouchEnd({changedTouches:[{clientX:350,clientY:302}]});
  return links;}
console.log(JSON.stringify([lauf(true),lauf(false)]));"""


def test_11_wisch_im_querkasten_wechselt_nicht(node_exe, index_html):
    r = json.loads(run_node_snippet(node_exe, _swipe_js(index_html)))
    assert r == [0, 1], "im Kasten (am Anschlag) kein Bereichswechsel, ausserhalb weiter"


def test_11_umkehrprobe(node_exe, index_html):
    alt = index_html.replace("ok:!skip&&!noTouch&&!(sc&&_swQuerrollerSperrt(sc)),", "ok:!skip&&!noTouch,", 1)
    assert alt != index_html
    r = json.loads(run_node_snippet(node_exe, _swipe_js(alt)))
    assert r == [1, 1], "alter Stand: der Kasten am Anschlag liess den Wisch durch"


def test_11_kein_stoppropagation_im_start(index_html):
    f = _fn(index_html, "useSwipe")
    start = f[f.index("onTouchStart:e=>{"):f.index("onTouchEnd:e=>{")]
    assert "stopPropagation" not in start.split("/*")[0]
    assert "stopPropagation()" not in re.sub(r"/\*.*?\*/", "", start, flags=re.S)


# ---------------------------------------------------------------- 12 Kleinigkeiten
def test_12_kleinigkeiten(index_html):
    # 1084 P3 (3): 9em -> 10em - "Monatsabrechnung" stand gekappt (108/112 px mittel, 117/121 px breit); der Riegel bleibt: ueberlange Namen kuerzt der Knopf weiter (test_p3_funde_v1084.py)
    assert 'maxWidth:"10em",overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap",verticalAlign:"bottom"}}, akt.l):"Mehr"' in index_html
    assert 'gap:12,flexWrap:"wrap",rowGap:8}}/* v3.9.1050 A55' in index_html
    assert 'visibility:da?"visible":"hidden",userSelect:"none",WebkitUserSelect:"none"' in index_html
    assert 'curUser&&curUser.role==="admin"&&React.createElement(\'details\', { \'data-technik\': "verbindung"' in index_html
    assert 'curUser&&curUser.role==="admin"&&React.createElement(\'details\', { \'data-technik\': "app"' in index_html
    # Werkzeuge-Kennzahl ist seit 1074 einheitlich
    assert 'React.createElement(Kpi, { label: "Kalibrierung fällig" , value: kalibFaellig' in index_html


def test_12_umkehrprobe_technik(index_html):
    alt = index_html.replace('curUser&&curUser.role==="admin"&&React.createElement(\'details\', { \'data-technik\': "app"', "React.createElement('div', {", 1)
    assert alt != index_html
    assert 'curUser&&curUser.role==="admin"&&React.createElement(\'details\', { \'data-technik\': "app"' not in alt
