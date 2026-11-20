# -*- coding: utf-8 -*-
"""A55-Funde 1080 (Handy hochkant 384x752, _layoutStufe "schmal").

1 Chef > Personal > KV-Zuschlaege: Lese-Tabelle war 720 px breit im 302-px-Kasten
  (Spalte "Ue 100%" abgeschnitten). Jetzt schmal = gestapelte Zeilen mit Feldnamen
  (CSS epk-kv-karten, dieselben Zellen); mittel/breit bleibt Tabelle.
2 Admin > Benutzer: der leere Detail-Platzhalter stand am Handy unter der Liste.
  schmal: Detail nur mit gewaehltem Benutzer.
3 Admin > Benutzer: "@lager ·" mit haengendem Trenner - nur vorhandene Teile.
4 Chef > Arbeit: "die aeltesten 8" / Plakette 20 / "alle 8 anzeigen" - jetzt
  alle ueberfaelligen, aelteste zuerst, "alle 20 anzeigen" = Plakette.
5 Projekte: Suchfeld am Handy auf 160 px gedeckelt, Platzhalter abgeschnitten.

Jeder Riegel fuehrt echten Code aus index.html in Node aus (wo moeglich) und hat
eine Umkehrprobe gegen den alten Stand.
"""
import io
import json
import os
import re

import pytest

from conftest import run_node_snippet

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")


@pytest.fixture(scope="module")
def roh():
    return io.open(PFAD, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def _fn(src, name):
    i = src.index("\nfunction " + name + "(") + 1
    j = src.index("\nfunction ", i + 5)
    k = src.find("\n/*", i)
    if 0 < k < j:
        j = k
    return src[i:j]


def _stufe_code(src):
    i = src.index("const BP_MOB=600;")
    j = src.index("const BP_BREIT=")
    k = src.index("function _grobZeiger(", j)
    return "const BP_MOB=600;\n" + src[j:k]


# ---------------------------------------------------------------- 1 KV-Zuschlaege

KV_STUBS = r"""
var window={innerHeight:752};
var React={Fragment:'F',createElement:function(t,p){var c=[].slice.call(arguments,2);return {t:t,p:p||{},c:c};}};
var _react={useState:function(){return [true,function(){}];}};
var V={},UI={},COLORS={},mono='m',KV_RULES_FALLBACK={};
function CC(){return {};}
function _isATFeiertag(){return false;}
function _kvTagesnorm(){return 8;}
function _kvHundert100(){return false;}
function _kvTagZuschlag(){return {normal:8,mehrarbeit:1,ue50:2,ue100:0.5,zuschlagStd:3};}
function _fzDE(v,d){return v.toFixed(d);}
function _ikVw(i,t){return t;}
function _klappIk(){return null;}
function finde(n,f,out){if(!n||typeof n!=='object')return out;if(f(n))out.push(n);(n.c||[]).forEach(function(k){if(Array.isArray(k))k.forEach(function(x){finde(x,f,out);});else finde(k,f,out);});return out;}
function lauf(ww){
  var y=new Date().getFullYear();
  var t=KVZuschlagReport({ww:ww,entries:[{date:y+'-03-02',hours:10,w:'a'}],monteure:[{id:'a',n:'Test A'}]});
  var tab=finde(t,function(n){return n.t==='table';},[])[0];
  var ths=finde(tab,function(n){return n.t==='th';},[]).map(function(n){return n.c.join('');});
  var tds=finde(tab,function(n){return n.t==='td';},[]).map(function(n){return n.p['data-l']===undefined?null:n.p['data-l'];});
  return {klasse:tab.p.className||null,breite:tab.p.style.width,ths:ths,tds:tds};
}
"""


def _kv_lauf(node_exe, src):
    js = (KV_STUBS + _stufe_code(src) + "\n" + _fn(src, "KVZuschlagReport")
          + "\nconsole.log(JSON.stringify([lauf(384),lauf(412),lauf(800),lauf(1280)]));")
    return json.loads(run_node_snippet(node_exe, js))


def _kv_pruefe(r):
    schmal, schmal2, mittel, breit = r
    for s in (schmal, schmal2):
        assert s["klasse"] == "epk-kv-karten", "Handy: KV-Tabelle nicht als Karten"
        assert s["breite"] == "100%", "Handy: KV-Tabelle breiter als der Kasten"
        # jede Wertzelle traegt ihren Feldnamen = Spaltenkopf
        assert s["tds"][1:6] == s["ths"][1:6], (s["tds"], s["ths"])
        assert s["tds"][0] is None  # Name ohne Feldname, ueber die ganze Zeile (CSS)
    for t in (mittel, breit):
        assert t["klasse"] is None, "mittel/breit muss Tabelle bleiben"
        assert t["breite"] == "100%"


def test_1_kv_karten_am_handy(node_exe, roh):
    _kv_pruefe(_kv_lauf(node_exe, roh))


def test_1_kv_umkehrprobe(node_exe, roh):
    alt = roh.replace("className:isMob?'epk-kv-karten':undefined,", "", 1).replace(
        "style:{width:'100%',borderCollapse:'collapse',fontSize:12}}\n          ,h('thead'",
        "style:{width:isMob?720:'100%',borderCollapse:'collapse',fontSize:12}}\n          ,h('thead'", 1)
    assert alt != roh
    with pytest.raises(AssertionError):
        _kv_pruefe(_kv_lauf(node_exe, alt))


def test_1_kv_css(roh):
    css = roh[:roh.index("</style>")]
    for regel in ("table.epk-kv-karten thead { display: none; }",
                  "table.epk-kv-karten tr { display: grid; grid-template-columns: repeat(3,minmax(0,1fr));",
                  "table.epk-kv-karten td:first-child { grid-column: 1 / -1; }",
                  "table.epk-kv-karten td[data-l]::before { content: attr(data-l);"):
        assert regel in css, regel
    assert "width:isMob?720" not in roh


# ---------------------------------------------------------------- 2 Admin Detail-Platzhalter

PLATZ = "\"Benutzer auswählen für Details & Berechtigungen\""


def _admin(src):
    i = src.index("\nfunction AdminPanel(")
    return src[i:src.index("\nfunction OfflineBanner(", i)]


def _admin_platzhalter_nur_breit(src):
    a = _admin(src)
    p = a.index(PLATZ)
    vor = a[max(0, p - 900):p]
    return re.search(r"\) : isMob \? null/\*[^*]*\*/ : \(\s*React\.createElement\('div', \{ style: \{\.\.\.CC\(\),textAlign:\"center\",padding:40", vor) is not None


def test_2_admin_platzhalter_nicht_am_handy(roh):
    assert _admin(roh).count(PLATZ) == 1
    assert _admin_platzhalter_nur_breit(roh)
    # isMob im AdminPanel kommt aus _layoutStufe (schmal)
    assert 'const _adStufe=_layoutStufe(ww,' in _admin(roh) and 'const isMob=_adStufe==="schmal";' in _admin(roh)


def test_2_admin_umkehrprobe(roh):
    alt = re.sub(r"\) : isMob \? null/\*[^*]*\*/ : \(", ") : (", roh, count=1)
    assert alt != roh
    assert not _admin_platzhalter_nur_breit(alt)


# ---------------------------------------------------------------- 3 Benutzer-Unterzeile

def test_3_unterzeile_ohne_haengenden_trenner(node_exe, roh):
    js = _fn(roh, "_adUserZeile") + r"""
console.log(JSON.stringify([_adUserZeile('lager',undefined),_adUserZeile('lager',''),_adUserZeile('lager','Monteur'),
 _adUserZeile('',  'Monteur'),_adUserZeile(null,null),_adUserZeile(' x ',' Büro ')]));"""
    r = json.loads(run_node_snippet(node_exe, js))
    assert r == ["@lager", "@lager", "@lager · Monteur", "Monteur", "", "@x · Büro"]
    a = _admin(roh)
    assert "_adUserZeile(u.username,(rl2&&rl2.l)||u.role)" in a
    # Umkehrprobe: der alte Ausdruck haengte den Trenner immer an
    assert "\"@\", u.username, \" · \"  , _optionalChain([rl2" not in a
    alt = "".join(["@", "lager", " · ", ""])
    assert alt.endswith(" · ") and r[0] != alt


# ---------------------------------------------------------------- 4 Kritisch ueberfaellig

def _ueberfaellig_js(src):
    i = src.index("const _ueberfaelligeArr=")
    ue = src[i:src.index("\n", i)]
    j = src.index("const topOver=")
    to = src[j:src.index("\n", j)]
    return ue, to


def _hinweis_lauf(node_exe, src):
    ue, to = _ueberfaellig_js(src)
    js = r"""
var AS_GRP_OFFEN=['offen'];var _td='2026-11-20';
function _hasTermin(t){return !!t&&/^\d{4}-\d\d-\d\d/.test(t);}
var _react={useMemo:function(f){return f();},useState:function(v){return [v,function(){}];}};
var arbeitsscheine=[];for(var k=0;k<20;k++){var d=new Date(Date.UTC(2026,7,1+k*3));arbeitsscheine.push({id:'a'+k,scheinstatus:'offen',terminVorschlag:d.toISOString().slice(0,10)});}
arbeitsscheine.push({id:'z',scheinstatus:'offen',terminVorschlag:'2026-12-01'});arbeitsscheine.push({id:'e',scheinstatus:'erledigt',terminVorschlag:'2026-01-01'});
arbeitsscheine.reverse();
""" + ue + "\nconst ueberfaellige=_ueberfaelligeArr.length;\n" + to + r"""
var React={Fragment:'F',createElement:function(t,p){var c=[].slice.call(arguments,2);return {t:t,p:p||{},c:c};}};
var V={},UI={zahlen:{}};function _ik(){return null;}
""" + _fn(src, "_hinweisFarbe") + "\n" + _fn(src, "_hinweisTaste") + "\n" + _fn(src, "Hinweis") + r"""
function txt(n){if(n==null||n===false)return '';if(typeof n!=='object')return String(n);return (n.c||[]).map(function(k){return Array.isArray(k)?k.map(txt).join(''):txt(k);}).join('');}
var zeilen=topOver.map(function(a){return React.createElement('div',{key:a.id},a.id);});
var w=Hinweis({ton:'gefahr',titel:'x',zahl:ueberfaellige,zeilen:zeilen,offen:true});
var t=txt(w);var m=t.match(/alle (\d+) anzeigen/);
console.log(JSON.stringify({ue:ueberfaellige,top:topOver.length,erst:topOver[0].terminVorschlag,letzt:topOver[topOver.length-1].terminVorschlag,alle:m?Number(m[1]):null}));
"""
    return json.loads(run_node_snippet(node_exe, js))


def test_4_liste_und_plakette_gleich(node_exe, roh):
    r = _hinweis_lauf(node_exe, roh)
    assert r["ue"] == 20 and r["top"] == 20
    assert r["alle"] == 20, "'alle N anzeigen' muss die Plakette (Gesamtzahl) nennen"
    assert r["erst"] < r["letzt"], "aelteste zuerst"
    assert "titel:'Kritisch überfällig',zahl:ueberfaellige," in roh
    assert "die ältesten '+topOver.length" not in roh


def test_4_umkehrprobe(node_exe, roh):
    alt = roh.replace(
        "localeCompare(b.terminBestaetigt||b.terminVorschlag||'')),[arbeitsscheine,_td]);",
        "localeCompare(b.terminBestaetigt||b.terminVorschlag||'')).slice(0,8),[arbeitsscheine,_td]);", 1)
    assert alt != roh
    r = _hinweis_lauf(node_exe, alt)
    assert r["ue"] == 20 and r["alle"] == 8  # der alte Widerspruch


# ---------------------------------------------------------------- 5 Projekte-Suchfeld

def _such_stil(src):
    m = re.search(r'placeholder: "Projekt, Kunde\.\.\."  , style: (\{\.\.\.II\(\),[^}]*\})\} \)', src)
    assert m, "Suchfeld nicht gefunden"
    return m.group(1)


def _such_lauf(node_exe, stil):
    js = ("function II(){return {width:'100%',padding:'10px 11px',fontSize:14,minHeight:44};}"
          "function f(isMob){return " + stil + ";}"
          "console.log(JSON.stringify([f(true),f(false)]));")
    return json.loads(run_node_snippet(node_exe, js))


def _such_pruefe(r):
    mob, gross = r
    assert mob["fontSize"] == 16 and mob["minHeight"] >= 44
    # Platz fuer 38 px Lupe + 11 px rechts + ~140 px Text "Projekt, Kunde..." bei 16 px
    assert mob["minWidth"] >= 190 and mob["maxWidth"] == "none" and mob["flex"] == "1 1 200px"
    assert gross["maxWidth"] == 220 and gross["fontSize"] == 13 and "flex" not in gross or gross.get("flex") is None


def test_5_suchfeld_passt(node_exe, roh):
    _such_pruefe(_such_lauf(node_exe, _such_stil(roh)))


def test_5_umkehrprobe(node_exe):
    alt = '{...II(),width:"auto",maxWidth:isMob?160:220,minWidth:isMob?120:0,fontSize:isMob?16:13}'
    with pytest.raises(AssertionError):
        _such_pruefe(_such_lauf(node_exe, alt))


# ---------------------------------------------------------------- Grenzen

def test_kein_push_kern_in_den_aenderungen(roh):
    for teil in re.findall(r"A55 1080 \(\d\)[^\n]{0,600}", roh):
        assert "_juprowa" not in teil and "offa" not in teil.lower()
