# -*- coding: utf-8 -*-
"""v3.9.1025 Status-Schutz (Fix B): unbekannter OFFA-Statuscode erfindet keinen Status.

Befund: `_juprowaMapWorksheet` setzt `stat=JUPROWA_STATUS_MAP[code]||"aufgenommen"`. Im Pull wurde
das fuer BESTEHENDE Scheine ungeprueft uebernommen (`upd.scheinstatus=mapped.scheinstatus`) - ein
unbekannter Code (z.B. ein neuer OFFA-Status) setzte einen laufenden Schein still auf "aufgenommen",
und der naechste Push haette AK_AUFSTATUS 0 nach OFFA geschickt.

Fix: bei unbekanntem Code bleibt der alte scheinstatus (kein upd.scheinstatus) + einmal je Sitzung
activity_log `juprowa_status_unbekannt`. NEUE Scheine bleiben "aufgenommen" (unveraendert).

Geprueft wird die ECHTE `_juprowaSync` + `_juprowaMapWorksheet` + Helfer in Node; die Attrappen sind
an die echten Signaturen gebunden (Test 1). Umkehrprobe: derselbe Lauf gegen die auf den Altstand
zurueckgedrehte Zeile muss den Fehler zeigen. Normalfall-Probe: bei bekannten Codes erzeugen Alt- und
Neustand byte-gleiche PATCH/POST-Koerper.
"""
import json
import re
import subprocess

from conftest import _extract_fn

_STUB_SIGS = {
    "_authRetry": "(fn)",
    "_sbGet": "(table,filter)",
    "_sbPost": "(table,data,minimal)",
    "_sbPatch": "(table,id,data)",
    "_mapArbeitsschein": "(a)",
    "_mapBody": "(obj)",
    "_juprowaResolveWorker": "(code,text,workers)",
    "_dispoMonteurUebertragbar": "(monteurId)",
    "_asPullFresh": "(setArbeitsscheine)",
    "_juprowaDrainPending": "(maxBatch)",
    "_getDefaultSB": "()",
}

_NEU_GUARD = "if(!isPending&&_stBekannt1025&&mapped.scheinstatus!==existing.scheinstatus)upd.scheinstatus=mapped.scheinstatus;"
_ALT_GUARD = "if(!isPending&&mapped.scheinstatus!==existing.scheinstatus)upd.scheinstatus=mapped.scheinstatus;"
_NEU_MELDUNG = "if(!_stBekannt1025)_juprowaStatusUnbekannt(mapped.nummer,jws.AK_AUFSTATUS);"


def _const_line(html, name):
    m = re.search(r"^const " + re.escape(name) + r"=.*$", html, re.M)
    assert m, name + " nicht gefunden"
    return m.group(0)


def _helper_block(html):
    start = html.index("var _jpStatusUnbekanntGemeldet={};")
    fn = _extract_fn(html, "_juprowaStatusUnbekannt")
    assert fn
    return html[start:html.index(fn) + len(fn)]


def _bausteine(html):
    sync = _extract_fn(html, "_juprowaSync")
    assert sync and sync.startswith("function _juprowaSync(arbeitsscheine,setArbeitsscheine,silent)")
    parts = [
        _const_line(html, "JUPROWA_ART_MAP"),
        _const_line(html, "JUPROWA_STATUS_MAP"),
        _const_line(html, "JUPROWA_PRIO_MAP"),
        _const_line(html, "AS_GRP_OFFEN"),
        _extract_fn(html, "_prioHeilBedarf"),
        _extract_fn(html, "_juprowaMapWorksheet"),
        _helper_block(html),
        "async " + sync,
    ]
    for p in parts:
        assert p
    return parts


_STUBS = u"""
var LOG=[];
var window={};var localStorage={getItem:function(){return null;},setItem:function(){}};
var SB_REST='x';function _sbWH(){return {};}
function _optionalChain(){return undefined;}function _log(){}
var _uidN=0;function uid(){return 'new'+(++_uidN);}
var FEED=[];var DB=[];var _juprowaSyncing=false;
function fetch(){return Promise.resolve({ok:true,json:function(){return Promise.resolve(FEED);}});}
function _authRetry(fn){return fn();}
function _sbGet(table,filter){return Promise.resolve(table==='arbeitsscheine'?JSON.parse(JSON.stringify(DB)):[]);}
function _sbPost(table,data,minimal){LOG.push(['POST',table,data]);return Promise.resolve([]);}
function _sbPatch(table,id,data){LOG.push(['PATCH',table,id,data]);return Promise.resolve([{}]);}
function _mapArbeitsschein(a){return a;}
function _mapBody(obj){return JSON.parse(JSON.stringify(obj));}
function _juprowaResolveWorker(code,text,workers){return '';}
function _dispoMonteurUebertragbar(monteurId){return true;}
function _asPullFresh(setArbeitsscheine){return Promise.resolve({ok:true});}
function _juprowaDrainPending(maxBatch){return Promise.resolve({drained:0,batch:0});}
function _getDefaultSB(){return '';}
async function SYNC(){var r=await _juprowaSync([],function(){},true);if(!r||r.error){console.log('SYNC-FEHLER '+JSON.stringify(r));process.exit(3);}return r;}
var _warn=console.warn;console.warn=function(){};
function fw(nr,st){return {ID:nr+'-id',AK_SCHEINNR:nr,AK_AUFSTATUS:st,AK_PRIOR:4,AK_AUFART:1,AK_SCHEINTYP:1};}
function db(nr,st,pend){return {id:'id-'+nr,nummer:nr,scheinstatus:st,prioritaet:'normal',push_pending:!!pend};}
function stripZeit(x){return JSON.parse(JSON.stringify(x,function(k,v){return (k==='juprowa_sync_at')?'T':v;}));}
"""


def _run(node_exe, tmp_path, js, name):
    f = tmp_path / name
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


_SZENARIO = u"""
(async function(){
  DB=[db('S1','in_bearbeitung'),db('S2','in_bearbeitung'),db('S4','in_bearbeitung'),db('S5','erledigt',true)];
  FEED=[fw('S1',99),fw('S2',20),fw('S3',99),fw('S4',3),fw('S5',77)];
  await SYNC();
  await SYNC();   // zweiter Pull: Meldung darf nicht doppelt kommen
  var out={patches:{},posts:[],logs:[]};
  LOG.forEach(function(e){
    if(e[0]==='PATCH'&&e[1]==='arbeitsscheine'){out.patches[e[2]]=out.patches[e[2]]||[];out.patches[e[2]].push(stripZeit(e[3]));}
    else if(e[0]==='POST'&&e[1]==='arbeitsscheine')out.posts.push(stripZeit(e[2]));
    else if(e[0]==='POST'&&e[1]==='activity_log'&&e[2].action!=='juprowa_pull')out.logs.push(e[2]);
  });
  console.log(JSON.stringify(out));
})().catch(function(e){console.log('EXC '+(e&&e.stack||e));process.exit(2);});
"""

_NORMALFALL = u"""
(async function(){
  DB=[db('S1','in_bearbeitung'),db('S2','in_bearbeitung'),db('S4','freigegeben'),db('S5','erledigt',true),db('S6','aufgenommen')];
  FEED=[fw('S1',5),fw('S2',20),fw('S3',1),fw('S4',4),fw('S5',10),fw('S6',0),fw('S7','15')];
  await SYNC();
  console.log(JSON.stringify(LOG.map(stripZeit)));
})().catch(function(e){console.log('EXC '+(e&&e.stack||e));process.exit(2);});
"""


def _js(html, szenario):
    return _STUBS + "\n".join(_bausteine(html)) + "\n" + szenario


def _altstand(html):
    assert html.count(_NEU_GUARD) == 1 and html.count(_NEU_MELDUNG) == 1
    return html.replace(_NEU_MELDUNG, "").replace(_NEU_GUARD, _ALT_GUARD)


def test_attrappen_an_echte_signatur_gebunden(index_html):
    for name, sig in _STUB_SIGS.items():
        m = re.search(r"function\s+" + re.escape(name) + r"(\([^)]*\))", index_html)
        assert m, name + " nicht in index.html"
        assert m.group(1) == sig, "%s: echte Signatur %s, Attrappe %s" % (name, m.group(1), sig)
    # Die Attrappen im Probe-Skript tragen genau diese Signaturen.
    for name, sig in _STUB_SIGS.items():
        assert ("function " + name + sig) in _STUBS, name


def test_unbekannter_code_behaelt_status_und_meldet_einmal(index_html, node_exe, tmp_path):
    rc, out = _run(node_exe, tmp_path, _js(index_html, _SZENARIO), "status_schutz_neu.js")
    assert rc == 0, out
    res = json.loads(out.strip().splitlines()[-1])
    # S1 bestehend, unbekannter Code 99 -> kein scheinstatus im PATCH (alter Status bleibt)
    assert res["patches"]["id-S1"], res
    for p in res["patches"]["id-S1"]:
        assert "scheinstatus" not in p, p
        assert p["juprowa_raw"]["AK_AUFSTATUS"] == 99  # Rohdaten weiter byte-treu gespeichert
    # S2 bekannter Code 20 -> storniert wie bisher
    assert res["patches"]["id-S2"][0].get("scheinstatus") == "storniert"
    # S4 bekannt + gleich -> kein scheinstatus
    assert "scheinstatus" not in res["patches"]["id-S4"][0]
    # S3 NEU mit unbekanntem Code -> weiterhin "aufgenommen"
    s3 = [p for p in res["posts"] if p["nummer"] == "S3"]
    assert s3 and s3[0]["scheinstatus"] == "aufgenommen", res["posts"]
    # Meldung: je (Nummer, Code) genau einmal ueber zwei Pulls; S1 und S5 (pending) gemeldet
    keys = sorted((json.loads(l["details"])["nummer"], json.loads(l["details"])["code"]) for l in res["logs"])
    assert all(l["action"] == "juprowa_status_unbekannt" for l in res["logs"]), res["logs"]
    assert keys == [("S1", "99"), ("S5", "77")], keys  # nur BESTEHENDE Scheine; neuer S3 bleibt still "aufgenommen"


def test_umkehrprobe_altstand_erfindet_aufgenommen(index_html, node_exe, tmp_path):
    rc, out = _run(node_exe, tmp_path, _js(_altstand(index_html), _SZENARIO), "status_schutz_alt.js")
    assert rc == 0, out
    res = json.loads(out.strip().splitlines()[-1])
    assert res["patches"]["id-S1"][0].get("scheinstatus") == "aufgenommen", \
        "Umkehrprobe: der Altstand muss den Fehler zeigen, sonst prueft der Test nichts"
    assert res["logs"] == []


def test_normalfall_alt_und_neu_byte_gleich(index_html, node_exe, tmp_path):
    rc1, neu = _run(node_exe, tmp_path, _js(index_html, _NORMALFALL), "status_normal_neu.js")
    rc2, alt = _run(node_exe, tmp_path, _js(_altstand(index_html), _NORMALFALL), "status_normal_alt.js")
    assert rc1 == 0 and rc2 == 0, neu + alt
    assert neu == alt
    assert '"scheinstatus":"erledigt"' in neu  # Probe trifft wirklich Statuswechsel


def test_tabellen_unveraendert(index_html):
    assert _const_line(index_html, "JUPROWA_STATUS_MAP") == (
        "const JUPROWA_STATUS_MAP={'0':'aufgenommen','1':'freigegeben','2':'aufgeschoben','3':'in_bearbeitung',"
        "'4':'freigegeben','5':'erledigt','10':'abgerechnet','11':'bar_bezahlt','15':'bar_bezahlt','20':'storniert'};")
    assert "stat=JUPROWA_STATUS_MAP[String(jws.AK_AUFSTATUS)]||\"aufgenommen\";" in index_html
