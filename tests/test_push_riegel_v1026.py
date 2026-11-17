# -*- coding: utf-8 -*-
"""v3.9.1026 Push-Riegel vor jedem Senden an die Warenwirtschaft (Sebastian 16.11.: "GUARDS, kein Umbau des Push-Kerns").

Regeln von `_juprowaPushSperre(schein, ctx)` (Grund-Text oder null):
  1. Roh-Statuscode aus dem letzten Abruf unbekannt -> gesperrt (nie einen geratenen Status zurueckschicken).
  2. Ein Endstatus (storniert 20, abgerechnet 10, bar bezahlt 11/15) sperrt JEDEN Push, bei dem der App-Status
     davon ABWEICHT, gleich welcher Endstatus. Gleicher Status -> frei, der Rohwert geht unveraendert zurueck.
  3. Vom letzten erfolgreichen Abruf nicht mehr geliefert -> gesperrt; ohne Abrufzeitpunkt Regel aus.

Geprueft mit der ECHTEN Riegel-Funktion, der ECHTEN `_juprowaReversMap` (Push-Body) und den ECHTEN Aufrufstellen
`_juprowaDrainPending`, `_juprowaPushAll`, `_juprowaSchedulePush` in Node. Attrappen sind an die echten Signaturen
gebunden. Umkehrproben: ohne Riegel bzw. ohne Regel 1/2 muss die Probe den Fehler zeigen.
Datenbeispiele aus dem Bestand (16.11.): S075338 (in OFFA storniert), S075406 (abgerechnet).
"""
import json
import re
import subprocess

from conftest import _extract_fn


def _const_line(html, name):
    m = re.search(r"^const " + re.escape(name) + r"=.*$", html, re.M)
    assert m, name
    return m.group(0)


def _riegel_block(html):
    a = html.index("var _JP_ENDSTATUS=")
    e_tok = "window._jpLetzterAbrufMs=_jpLetzterAbrufMs;}"
    e = html.index(e_tok, a) + len(e_tok)
    return html[a:e]


_SIGS = {
    "_sbGet": "(table,filter)",
    "_sbPost": "(table,data,minimal)",
    "_sbPatch": "(table,id,data)",
    "_mapArbeitsschein": "(a)",
    "_juprowaWorkerToCode": "(workerId)",
    "_juprowaPush": "(scheinId)",
}

_STUBS = u"""
var COLORS={};var window={};var navigator={onLine:true};
var _LS={};var localStorage={getItem:function(k){return _LS[k]==null?null:_LS[k];},setItem:function(k,v){_LS[k]=String(v);}};
var CALLS=[],PUSHED=[],GETS=[];var DB={};
function _sbGet(table,filter){GETS.push(table+'?'+filter);
  if(table!=='arbeitsscheine')return Promise.resolve([]);
  var m=/^id=eq\\.(.+)$/.exec(filter||'');if(m)return Promise.resolve(DB[m[1]]?[JSON.parse(JSON.stringify(DB[m[1]]))]:[]);
  var ex=/id=not\\.in\\.\\(([^)]*)\\)/.exec(filter||'');var aus=ex?ex[1].split(','):[];
  return Promise.resolve(Object.keys(DB).filter(function(k){return DB[k].push_pending&&DB[k].juprowa_id&&aus.indexOf(k)<0;}).map(function(k){return {id:k};}));}
function _sbPost(table,data,minimal){CALLS.push(['POST',table,data]);return Promise.resolve([]);}
function _sbPatch(table,id,data){CALLS.push(['PATCH',table,id,data]);return Promise.resolve([{}]);}
function _mapArbeitsschein(a){return Object.assign({},a);}
function _juprowaWorkerToCode(workerId){return '';}
function _juprowaPush(scheinId){PUSHED.push(scheinId);return Promise.resolve({ok:true,nummer:scheinId});}
var _w=console.warn;console.warn=function(){};
var STUNDE=3600000, ABRUF=Date.parse('2026-11-16T10:00:00Z');
function schein(nr,st,raw,syncIso,pend){return {id:'id'+nr,nummer:nr,juprowa_id:5000000+parseInt(nr.slice(1),10),scheinstatus:st,prioritaet:'normal',
  push_pending:pend!==false,juprowa_sync_at:syncIso||'2026-11-16T10:00:00Z',kundName:'Muster GmbH',kundStr:'Hauptstrasse 1',kundPlz:'1010',kundOrt:'Wien',
  durchgefuehrte:'Leuchte getauscht',juprowa_raw:(raw===undefined?null:{AK_AUFSTATUS:raw,AK_PRIOR:4,RE_ADR_NAM1:'Muster GmbH',AK_BAUADR_NUMMER:'K-4711'})};}
"""


def _basis(html):
    return "\n".join([
        _const_line(html, "AS_GRP_OFFEN"),
        _const_line(html, "AS_STATUS"),
        _const_line(html, "JUPROWA_STATUS_MAP"),
        _const_line(html, "JUPROWA_STATUS_REV"),
        _const_line(html, "JUPROWA_PRIO_MAP"),
        _const_line(html, "JUPROWA_PRIO_REV"),
        _extract_fn(html, "_offaNichtImFeed"),
        _extract_fn(html, "_juprowaSanitize"),
        _extract_fn(html, "_juprowaReversMap"),
        _riegel_block(html),
    ])


def _run(node_exe, tmp_path, js, name):
    f = tmp_path / name
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    return json.loads(r.stdout.strip().splitlines()[-1])


_FAELLE = u"""
var ctx={letzterAbrufMs:ABRUF};
var F={
 f1_S075406_abgerechnet_raw10: schein('S075406','abgerechnet',10),
 f2_S075406_inbearb_raw10:     schein('S075406','in_bearbeitung',10),
 f3_S075338_inbearb_raw20:     schein('S075338','in_bearbeitung',20),
 f4_S075338_storniert_raw20:   schein('S075338','storniert',20),
 f5_erledigt_raw11:            schein('S075400','erledigt',11),
 f6_bar_raw15:                 schein('S075401','bar_bezahlt',15),
 f7_unbekannt_raw99:           schein('S075402','in_bearbeitung',99),
 f8_normal_raw3:               schein('S075403','in_bearbeitung',3),
 f9_normal_raw4_freigegeben:   schein('S075404','freigegeben',4),
 f10_nicht_gelistet:           schein('S075405','in_bearbeitung',3,'2026-11-16T07:00:00Z'),
 f11_ohne_raw:                 schein('S075407','in_bearbeitung',undefined)
};
var out={};
Object.keys(F).forEach(function(k){var b=_juprowaReversMap(F[k]);out[k]={sperre:_juprowaPushSperre(F[k],ctx),AK_AUFSTATUS:b?(b.AK_AUFSTATUS===undefined?null:b.AK_AUFSTATUS):null,body:b};});
out.f10_ohne_abruf=_juprowaPushSperre(F.f10_nicht_gelistet,{});
out.f10_abruf_0=_juprowaPushSperre(F.f10_nicht_gelistet,{letzterAbrufMs:0});
out.f10_frisch_gestempelt=_juprowaPushSperre(schein('S075405','in_bearbeitung',3,'2026-11-16T09:59:30Z'),ctx);
out.f10_erst_nach_abruf_gepusht=_juprowaPushSperre(schein('S075405','in_bearbeitung',3,'2026-11-16T10:20:00Z'),ctx);
console.log(JSON.stringify(out));
"""


def test_attrappen_an_echte_signatur(index_html):
    for name, sig in _SIGS.items():
        m = re.search(r"function\s+" + re.escape(name) + r"(\([^)]*\))", index_html)
        assert m and m.group(1) == sig, (name, m and m.group(1))
        assert ("function " + name + sig) in _STUBS, name


def test_regeln_mit_echten_datenbeispielen(index_html, node_exe, tmp_path):
    r = _run(node_exe, tmp_path, _STUBS + _basis(index_html) + _FAELLE, "riegel_faelle.js")
    # (1) S075406 App abgerechnet + OFFA 10 -> frei, Rohwert 10 geht unveraendert zurueck
    assert r["f1_S075406_abgerechnet_raw10"]["sperre"] is None
    assert r["f1_S075406_abgerechnet_raw10"]["AK_AUFSTATUS"] == "10"
    # (2) gleicher Schein, App in_bearbeitung + OFFA 10 -> GESPERRT (sonst ginge "3" raus = Abrechnung zurueckgedreht)
    assert r["f2_S075406_inbearb_raw10"]["sperre"] == "OFFA-Endstatus abgerechnet weicht ab"
    assert r["f2_S075406_inbearb_raw10"]["AK_AUFSTATUS"] == "3"
    # (3) S075338 App in_bearbeitung + OFFA 20 -> GESPERRT (sonst ginge "3" raus = Storno zurueckgedreht)
    assert r["f3_S075338_inbearb_raw20"]["sperre"] == "OFFA-Endstatus storniert weicht ab"
    assert r["f3_S075338_inbearb_raw20"]["AK_AUFSTATUS"] == "3"
    # (4) App storniert + OFFA 20 -> frei, Body "20"
    assert r["f4_S075338_storniert_raw20"]["sperre"] is None
    assert r["f4_S075338_storniert_raw20"]["AK_AUFSTATUS"] == "20"
    # (5) App erledigt + OFFA 11 -> GESPERRT
    assert r["f5_erledigt_raw11"]["sperre"] == "OFFA-Endstatus bar bezahlt weicht ab"
    # bar bezahlt 15 = App bar_bezahlt -> frei, 15 bleibt 15
    assert r["f6_bar_raw15"]["sperre"] is None and r["f6_bar_raw15"]["AK_AUFSTATUS"] == "15"
    # unbekannter Code 99 -> gesperrt (sonst ginge "3" statt 99 raus)
    assert r["f7_unbekannt_raw99"]["sperre"] == "OFFA-Statuscode 99 unbekannt"
    assert r["f7_unbekannt_raw99"]["AK_AUFSTATUS"] == "3"
    # Normalfall frei
    assert r["f8_normal_raw3"]["sperre"] is None and r["f8_normal_raw3"]["AK_AUFSTATUS"] == "3"
    assert r["f9_normal_raw4_freigegeben"]["sperre"] is None and r["f9_normal_raw4_freigegeben"]["AK_AUFSTATUS"] == "4"
    assert r["f11_ohne_raw"]["sperre"] is None
    # Regel 3
    # v3.9.1037 GF 17.11.: Regel 3 entfernt - ein nicht im Feed gelieferter Schein wird NICHT mehr gesperrt
    assert r["f10_nicht_gelistet"]["sperre"] is None
    assert r["f10_ohne_abruf"] is None and r["f10_abruf_0"] is None
    assert r["f10_frisch_gestempelt"] is None
    assert r["f10_erst_nach_abruf_gepusht"] is None


def test_normalfall_push_body_festgeschrieben(index_html, node_exe, tmp_path):
    """Push-Body im Normalfall: der Riegel aendert ihn nicht (er laeuft nur davor). Byte-genau festgeschrieben."""
    r = _run(node_exe, tmp_path, _STUBS + _basis(index_html) + _FAELLE, "riegel_body.js")
    assert json.dumps(r["f8_normal_raw3"]["body"], separators=(",", ":"), ensure_ascii=False) == (
        '{"ID":5075403,"AK_SCHEINNR":"S075403","AK_ARBEITEN":"Leuchte getauscht","AK_PRIOR":"4","AK_AUFSTATUS":"3",'
        '"AK_BAUADR_STR":"Hauptstrasse 1","AK_BAUADR_PLZ":"1010","AK_BAUADR_ORT":"Wien","AK_BAUADR_LKZ":"A",'
        '"AK_BAUADR_NAM1":"Muster GmbH","RE_ADR_NAM1":"Muster GmbH","AK_BAUADR_NUMMER":"K-4711"}')


def test_umkehrprobe_regeln(index_html, node_exe, tmp_path):
    alt = _basis(index_html)
    r2 = "if(_JP_ENDSTATUS.indexOf(m)>=0&&m!==schein.scheinstatus)return"
    r1 = "if(m==null)return \"OFFA-Statuscode \""
    assert alt.count(r2) == 1 and alt.count(r1) == 1
    ohne = alt.replace(r2, "if(false)return").replace(r1, "if(false)return \"OFFA-Statuscode \"")
    r = _run(node_exe, tmp_path, _STUBS + ohne + _FAELLE, "riegel_umkehr.js")
    assert r["f3_S075338_inbearb_raw20"]["sperre"] is None, "Umkehrprobe: ohne Regel 2 muss der Storno frei sein"
    assert r["f7_unbekannt_raw99"]["sperre"] is None


def _aufrufstellen(html):
    pa = _extract_fn(html, "_juprowaPushAll")
    dr = _extract_fn(html, "_juprowaDrainPending")
    a = html.index("var _jpPushSet=")
    e = html.index("if(typeof window!=='undefined')window._juprowaSchedulePush", a)
    return "async " + pa + "\nasync " + dr + "\n" + html[a:e]


_AUFRUF = u"""
DB={
 idS075338:schein('S075338','in_bearbeitung',20),
 idS075406:schein('S075406','abgerechnet',10),
 idS075402:schein('S075402','in_bearbeitung',99),
 idS075403:schein('S075403','in_bearbeitung',3),
 idS075405:schein('S075405','in_bearbeitung',3,'2026-11-16T07:00:00Z')
};
window.__lastJuprowaPull=ABRUF;
(async function(){
  var d1=await _juprowaDrainPending(10);
  var p1=PUSHED.slice();PUSHED=[];
  var d2=await _juprowaDrainPending(10);
  var p2=PUSHED.slice();var q2=GETS.filter(function(g){return g.indexOf('push_pending=eq.true')>=0;}).pop();PUSHED=[];
  var a1=await _juprowaPushAll();var p3=PUSHED.slice();PUSHED=[];
  ['idS075338','idS075403','idS075402'].forEach(function(i){_juprowaSchedulePush(i);});
  setTimeout(function(){
    var p4=PUSHED.slice();
    var logs=CALLS.filter(function(c){return c[0]==='POST'&&c[1]==='activity_log';}).map(function(c){return [c[2].action,JSON.parse(c[2].details).nummer,JSON.parse(c[2].details).grund];});
    var asWrites=CALLS.filter(function(c){return c[1]==='arbeitsscheine';}).length;
    console.log(JSON.stringify({d1:d1,p1:p1.sort(),d2:d2,p2:p2.sort(),q2:q2,a1:a1,p3:p3.sort(),p4:p4.sort(),logs:logs,asWrites:asWrites,pending:Object.keys(DB).filter(function(k){return DB[k].push_pending;}).sort()}));
  },2300);
})();
"""


def test_aufrufstellen_senden_gesperrte_nicht(index_html, node_exe, tmp_path):
    r = _run(node_exe, tmp_path, _STUBS + _basis(index_html) + _aufrufstellen(index_html) + _AUFRUF, "riegel_aufruf.js")
    frei = ["idS075403", "idS075405", "idS075406"]  # v3.9.1037: S075405 (nicht im Feed) ist frei
    assert r["p1"] == frei, r          # Drain: nur die freien
    assert r["p3"] == frei, r          # PushAll: nur die freien
    assert r["p4"] == ["idS075403"], r  # Klammer: S075338 + 99 gesperrt
    assert r["p2"] == frei, r
    # zweiter Drain nimmt kuerzlich gesperrte Scheine aus der Abfrage (verstopfen den Stapel nicht)
    assert "id=not.in.(" in r["q2"] and "idS075338" in r["q2"] and "select=id" in r["q2"] and "limit=10" in r["q2"]
    # kein Schreibzugriff auf arbeitsscheine durch den Riegel; push_pending bleibt bei allen stehen
    assert r["asWrites"] == 0
    assert r["pending"] == sorted(["idS075338", "idS075402", "idS075403", "idS075405", "idS075406"])
    # Meldung genau einmal je Schein+Grund trotz Drain x2 + PushAll + Klammer
    assert sorted(r["logs"]) == sorted([
        ["juprowa_push_gesperrt", "S075338", "OFFA-Endstatus storniert weicht ab"],
        ["juprowa_push_gesperrt", "S075402", "OFFA-Statuscode 99 unbekannt"],
    ]), r["logs"]


def test_umkehrprobe_ohne_riegel_im_drain(index_html, node_exe, tmp_path):
    stellen = _aufrufstellen(index_html)
    riegel = "try{if(await _juprowaPushSperreFuerId(row.id)){fail++;continue;}"
    assert stellen.count(riegel) == 1
    ohne = stellen.replace(riegel, "try{")
    r = _run(node_exe, tmp_path, _STUBS + _basis(index_html) + ohne + _AUFRUF, "riegel_aufruf_umkehr.js")
    assert "idS075338" in r["p1"], "Umkehrprobe: ohne Riegel wuerde der Drain den Storno ueberschreiben"


def test_knopf_und_anzeige(index_html):
    i = index_html.index("const doSinglePush=async(id)=>{")
    seg = index_html[i:i + 700]
    assert seg.index("_juprowaPushSperreFuerId(id)") < seg.index("confirm(\"Diesen Schein zur Juprowa Cloud senden?\")")
    assert seg.index("return;}") < seg.index("_juprowaPush(id)")
    assert "'data-offa-push-gesperrt': _pushGesperrtL.length" in index_html
    assert "NICHT an OFFA gesendet" in index_html
    assert "\"OFFA-Status: Code \"" in index_html and "\" (unbekannt)\"" in index_html
    assert "\"Nicht an OFFA: \"+_g" in index_html


def test_lesefehler_sperrt(index_html, node_exe, tmp_path):
    js = _STUBS + _basis(index_html) + u"""
_sbGet=function(table,filter){return Promise.reject(new Error('netz'));};
_juprowaPushSperreFuerId('x').then(function(g){console.log(JSON.stringify({g:g}));});
"""
    r = _run(node_exe, tmp_path, js, "riegel_lesefehler.js")
    assert r["g"] == "OFFA-Pruefung nicht moeglich (Lesefehler)"
