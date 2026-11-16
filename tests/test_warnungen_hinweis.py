# -*- coding: utf-8 -*-
"""WARNUNGEN 16.11. - GF: "Dashboard - die Warnungen sind nicht schoen, das Rot und die Liste".

EIN Muster (Hinweis) fuer Home, Chef-Portal und die Kaesten ueber der Arbeitsschein-Liste.
Geprueft wird das VERHALTEN der Komponente (in Node mit einer React-Attrappe gezeichnet):
Liste zugeklappt, aufgeklappt hoechstens 5 Zeilen plus "alle N anzeigen", Zeilen mit
Oeffnen-Weg sind Knoepfe mit 44 px, Sortierung nach Ton. Dazu die Verwendung an allen Stellen
und die Abwesenheit von Farbliteralen/Vollrot. Jede Pruefung hat eine Umkehrprobe.
NUR ANZEIGE: welche Scheine/Fahrzeuge gelistet und gezaehlt werden, bleibt beim Aufrufer.
"""
import json
import re

from conftest import run_node_snippet
from _hilfen import nur_code


def _komponente(html):
    a = html.index("var HINWEIS_RANG=")
    b = html.index("function Kpi(", a)
    return html[a:b]


_ATTRAPPE = r"""
const React={createElement:function(t,p){var c=[].slice.call(arguments,2);return {t:t,p:p||{},c:c};}};
const _react={useState:{call:function(_,v){return [v,function(){}];}}};
const V={cd:'CD',bd:'BD',bg:'BG',tx:'TX',dm:'DM',acTx:'AC',bdK:'BK'};
const UI={fehler:'F',fehlerBg:'FB',achtung:'A',achtungTxt:'AT',achtungBg:'AB',neutralTxt:'NT',neutralBg:'NB',fMeta:12,fKlein:13,fText:14,rRund:18,zahlen:{fontVariantNumeric:'tabular-nums'}};
function _ik(n){return {t:'svg',p:{n:n},c:[]};}
function alle(k,f,acc){acc=acc||[];if(!k||typeof k!=='object')return acc;if(f(k))acc.push(k);(k.c||[]).forEach(function(x){alle(x,f,acc);});return acc;}
function text(k){if(k==null||k===false)return '';if(typeof k!=='object')return String(k);return (k.c||[]).map(text).join('');}
"""


def _zeichnen(node_exe, html, js):
    return json.loads(run_node_snippet(node_exe, _ATTRAPPE + _komponente(html) + js))


_LAUF = r"""
var e7=[1,2,3,4,5,6,7].map(function(i){return {k:i,haupt:'S07533'+i,neben:'Grund '+i,onOpen:function(){}};});
var zu=Hinweis({ton:'achtung',titel:'7 Scheine',eintraege:e7});
var auf=Hinweis({ton:'achtung',titel:'7 Scheine',eintraege:e7,offen:true});
var knoepfe=function(t){return alle(t,function(k){return k.p&&k.p.role==='button';});};
var zeilenAuf=knoepfe(auf).filter(function(k){return /S07533/.test(k.p['aria-label']||'');});
var ohneListe=Hinweis({ton:'gefahr',titel:'x',onGo:function(){}});
console.log(JSON.stringify({
  zu_zeilen: knoepfe(zu).filter(function(k){return /S07533/.test(k.p['aria-label']||'');}).length,
  zu_text: text(zu),
  auf_zeilen: zeilenAuf.length,
  auf_min44: zeilenAuf.every(function(k){return k.p.style.minHeight>=44;}),
  auf_alle: alle(auf,function(k){return k.t==='button'&&/alle 7 anzeigen/.test(text(k));}).length,
  kopf_expanded: knoepfe(auf)[0].p['aria-expanded'],
  kopf_label: knoepfe(zu)[0].p['aria-label'],
  kante: [Hinweis({ton:'gefahr',titel:'a'}).p.style.borderLeft, Hinweis({ton:'achtung',titel:'a'}).p.style.borderLeft, Hinweis({titel:'a'}).p.style.borderLeft],
  ohne_liste_knopf: knoepfe(ohneListe).length,
  data: Hinweis({titel:'a','data-offa-x':3}).p['data-offa-x'],
  sort: _hinweisSort([{ton:'neutral',i:1},{ton:'achtung',i:2},{ton:'gefahr',i:3},{ton:'achtung',i:4},{i:5}]).map(function(h){return h.i;}),
  detail: [_hinweisAusDetail({label:'KR-1',model:'VW',sub:'1.3.2026',status:'overdue'},0,null), _hinweisAusDetail('Okt 2026 — Meier, Huber',1,null)]
}));
"""


def test_komponente_verhalten(node_exe, index_html):
    r = _zeichnen(node_exe, index_html, _LAUF)
    assert r["zu_zeilen"] == 0, "Liste muss standardmaessig zugeklappt sein"
    assert "7 anzeigen" in r["zu_text"]
    assert r["auf_zeilen"] == 5, "aufgeklappt hoechstens 5 Zeilen"
    assert r["auf_min44"], "Zeilen-Knoepfe unter 44 px"
    assert r["auf_alle"] == 1, "'alle 7 anzeigen' fehlt"
    assert r["kopf_expanded"] is True
    assert r["kopf_label"].startswith("7 Scheine")
    assert r["kante"] == ["3px solid F", "3px solid A", "3px solid BK"]
    assert r["ohne_liste_knopf"] == 1, "ohne Liste fuehrt die Kopfzeile zum Ziel (onGo)"
    assert r["data"] == 3, "data-*-Merkmale muessen an der Wurzel ankommen (Tests/Messung finden die Kaesten daran)"
    assert r["sort"] == [3, 2, 4, 1, 5], "Sortierung gefahr > achtung > neutral, sonst stabil"
    assert r["detail"][0] == {"k": 0, "haupt": "KR-1", "neben": "VW", "rechts": "1.3.2026", "rechtsTon": "gefahr", "onOpen": None}
    assert r["detail"][1]["haupt"] == "Okt 2026" and r["detail"][1]["neben"] == "Meier, Huber"


def test_umkehrprobe_verhalten(node_exe, index_html):
    kaputt = index_html.replace("max=p.max||5", "max=p.max||50", 1)
    assert kaputt != index_html
    r = _zeichnen(node_exe, kaputt, _LAUF)
    assert r["auf_zeilen"] == 7 and r["auf_alle"] == 0, "Umkehrprobe: ohne Deckel muesste alles offen stehen"
    kaputt = index_html.replace("var gesteuert=typeof p.offen===\"boolean\";var offen=gesteuert?p.offen:offenEig;",
                                "var gesteuert=typeof p.offen===\"boolean\";var offen=true;", 1)
    assert kaputt != index_html
    assert _zeichnen(node_exe, kaputt, _LAUF)["zu_zeilen"] == 5, "Umkehrprobe: offen-Vorgabe wird nicht erkannt"


def test_komponente_ohne_farbliterale_und_mindestschrift(index_html):
    k = nur_code(_komponente(index_html))
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", k), "Farbliteral in Hinweis - nur V.*/UI.* (Hell/Dunkel)"
    assert "rgba(" not in k
    zahlen = [int(x) for x in re.findall(r"fontSize:(\d+)", k)]
    assert not zahlen, "Schrift nur ueber UI.f*-Groessen: %r" % zahlen
    assert "minHeight:44" in k


def _block(code, anfang, ende):
    i = code.index(anfang)
    return code[i:code.index(ende, i)]


def test_verwendung_an_allen_stellen(index_html):
    code = nur_code(index_html)
    home = _block(code, "alerts.length>0&&(React.createElement('div', { 'data-hinweise': \"home\"", "dv('schnell')")
    assert "React.createElement(Hinweis" in home and "_hinweisSort(alerts)" in home
    assert "linear-gradient" not in home and "COLORS.ERROR" not in home and "▼" not in home
    asl = _block(code, "(_pushGesperrtL.length>0&&canSync)&&", "Schnell-Filter-Chips" if "Schnell-Filter-Chips" in code else "{key:\"\",label:\"Alle\"}")
    assert asl.count("React.createElement(Hinweis") == 4
    for rot in ("#ef4444", "239,68,68", "#991b1b", "#fca5a5", "⚠"):
        assert rot not in asl, "Rot/Emoji im Arbeitsschein-Kasten: %s" % rot
    assert "onOpen:()=>openEdit(x.a)" in asl and "onOpen:()=>openEdit(a)" in asl
    chef = _block(code, "_card('sorgen'", "_card('mt'")
    assert chef.count("React.createElement(Hinweis") == 6
    assert "#eab308" not in chef and "fontFamily:mono" not in chef
    krit = _block(code, "'Kritisch überfällig ('", "_drill('Arbeitsscheine','arbeitsscheine')")
    assert "window.__asOpenId=a.id" in krit and "COLORS.ERROR" not in krit
    assert code.count("function Hinweis(") == 1


def test_umkehrprobe_rot_im_kasten_faellt_auf(index_html):
    kaputt = index_html.replace("ton: \"achtung\", ik: \"senden\"", "ton: \"achtung\", farbe:\"#ef4444\", ik: \"senden\"", 1)
    assert kaputt != index_html
    code = nur_code(kaputt)
    asl = _block(code, "(_pushGesperrtL.length>0&&canSync)&&", "{key:\"\",label:\"Alle\"}")
    assert "#ef4444" in asl


def test_wortlaute_der_kaesten_bleiben(index_html):
    for w in ('+" NICHT an OFFA gesendet"', '+" in OFFA nicht mehr gelistet"', '"OFFA-Feed steht seit über "+OFFA_VERWAIST_TAGE+" Tagen"',
              '_nWort(_verwaisteN,"offener Schein","offene Scheine")', "Zustand unbekannt, keine Warnung.",
              "'Kritisch überfällig'", "'Scheine ohne Monteur'", "'Erledigt, noch nicht fakturiert'"):
        assert w in index_html, w
