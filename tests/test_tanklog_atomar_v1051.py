# -*- coding: utf-8 -*-
"""v3.9.1051 Tankbuch atomar: tank_log-Schreibwege ueber Server-Funktionen (fz_tanklog_add/_del/_set) statt ganzem Array.

Node fuehrt die ECHTEN Funktionen aus index.html aus (_translateAndExec, _fzTankAtomar, _fzTankRpc, _fzTankHatDatei)
gegen einen falschen Server:
  * /rpc/fz_tanklog_*: Modus "404" (Funktion nicht eingespielt) oder "ok" (bildet die SQL-Semantik nach: per id
    idempotent anhaengen/entfernen, km_stand nur erhoehen, km-Zeile 'km_'||id idempotent).
  * _sbGet/_sbPatch: In-Memory-Zeile, jede Sendung wird mitgeschrieben.
Die Attrappe ist an die echte Signatur gebunden: die Argumentnamen, die der Client sendet, muessen genau die
Parameter der Funktion im SQL-Entwurf sein (sonst antwortet PostgREST in echt mit 404 und alles liefe still im Rueckfall).

Geprueft: (a) Anlegen schickt nur den einen Eintrag; (b) 404 -> bisheriger Weg mit byte-gleichem PATCH, 404 wird gemerkt;
(c) Wiederholung derselben id ist idempotent; (d) Entfernen schickt nur die id; (e) Umkehrproben (ohne Route -> ganzes
Array; ohne Datei-Riegel -> data: ginge an den Server). Dazu statische Pruefung des SQL-Entwurfs.
"""
import json
import os
import re
import subprocess
import tempfile

import pytest

from conftest import _extract_fn
from test_flotte_schreibwege_v1049 import _batch_lauf

HIER = os.path.dirname(os.path.abspath(__file__))
SQL = os.path.join(os.path.dirname(HIER), "sql", "TANKLOG_ATOMAR_v1051_ENTWURF.sql")

ROUTE_ZEILE = ('    if((d._tankAtomar||d.tankLog_add||d.tank_log_add)&&typeof _fzTankAtomar==="function"){if(await _fzTankAtomar(idOrSub,d)'
               '&&Object.keys(d).length===0)return{ok:1};}')
DATEI_RIEGEL = "  if(args.p_eintrag&&_fzTankHatDatei(args.p_eintrag))return false;"


def _node(node_exe, code):
    fd, p = tempfile.mkstemp(suffix=".js")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(code)
        r = subprocess.run([node_exe, p], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    finally:
        os.remove(p)
    assert r.returncode == 0, r.stderr[:2000]
    return json.loads(r.stdout)


def _fn(src, name):
    f = _extract_fn(src, name, rf"(?:async\s+)?function\s+{re.escape(name)}\s*\(")
    assert f, name
    return f


def _sql():
    with open(SQL, encoding="utf-8") as f:
        return f.read()


def _sql_params(name):
    m = re.search(r"create or replace function public\." + name + r"\(([^)]*)\)", _sql(), re.I)
    assert m, name
    return [re.match(r"\s*(\w+)", p).group(1) for p in m.group(1).split(",")]


PRELUDE = r"""
var navigator={onLine:true};var toasts=[];var window={__toast:function(m){toasts.push(String(m));}};
var _RD=Date;Date=class extends _RD{constructor(...a){if(a.length)super(...a);else super("2026-11-19T10:00:00.000Z");}static now(){return new _RD("2026-11-19T10:00:00.000Z").getTime();}};
var SB_REST="https://x/rest/v1";
var _RLS_SILENT_DENIAL_LABELS={fahrzeuge:"Fahrzeug-Änderung"};
var ROUTE_MAP={fahrzeuge:["fahrzeuge","fahrzeuge"]};
function _mapBody(b){const m={...b};if("tankLog" in m){m.tank_log=m.tankLog;delete m.tankLog;}if("kmStand" in m){m.km_stand=m.kmStand;delete m.kmStand;}return m;}
function _fzOhneFinanz(m){return m;}
function _ymd(d){return "2026-11-19";}
function _sbH(h){return h||{};}
function _fT(init){return init;}
async function _authRetry(fn){return await fn();}
function _onAuthFail(){}
var ANDERES={id:"tANDERS",datum:"2026-11-18",liter:30,preis:45,km:12000,foto:"",by:"Geraet B"};
var db;function reset(){db={F1:{id:"F1",fahrer:"m1",tank_log:JSON.stringify([ANDERES]),km_log:"[]",km_stand:12000}};}reset();
var rpcModus="ok";var rpcAntwort=null;var verlieren=0;var rpc=[];var gets=[];var patches=[];
function _ant(status,obj){return {ok:status>=200&&status<300,status:status,text:async()=>JSON.stringify(obj||{}),json:async()=>obj};}
async function fetch(url,init){
  const name=url.split("/rpc/")[1];const a=JSON.parse(init.body);rpc.push({name:name,body:init.body});
  if(rpcModus==="404")return _ant(404,{code:"PGRST202",message:"Could not find the function"});
  if(rpcAntwort)return _ant(200,rpcAntwort);
  const z=db[a.p_fahrzeug_id];if(!z)return _ant(200,{ok:false,grund:"fahrzeug_fehlt"});
  let tl=JSON.parse(z.tank_log||"[]"),kl=JSON.parse(z.km_log||"[]");let res;
  if(name==="fz_tanklog_add"){const e=a.p_eintrag;let neu=false;if(!tl.some(x=>x&&x.id===e.id)){tl=[e].concat(tl);neu=true;}
    if(a.p_km>0){const kid=a.p_km_log_id||("km_"+e.id);if(!kl.some(x=>x&&x.id===kid))kl.push({id:kid,km:a.p_km,date:"2026-11-19"});z.km_stand=Math.max(z.km_stand||0,a.p_km);}
    res={ok:true,neu:neu};}
  else if(name==="fz_tanklog_del"){const n0=tl.length;tl=tl.filter(x=>!(x&&x.id===a.p_eintrag_id));res={ok:true,entfernt:n0-tl.length};}
  else if(name==="fz_tanklog_set"){if(!tl.some(x=>x&&x.id===a.p_eintrag_id))return _ant(200,{ok:false,grund:"eintrag_fehlt"});tl=tl.map(x=>(x&&x.id===a.p_eintrag_id)?Object.assign({},x,a.p_patch):x);res={ok:true,km_stand:null};}
  else return _ant(404,{});
  z.tank_log=JSON.stringify(tl);z.km_log=JSON.stringify(kl);
  if(verlieren>0){verlieren--;throw new TypeError("Failed to fetch");}/* Server HAT geschrieben, Antwort verloren */
  return _ant(200,res);
}
async function _sbGet(tab,q){gets.push(q);const id=decodeURIComponent(q.split("eq.")[1].split("&")[0]);const r=db[id];return r?[JSON.parse(JSON.stringify(r))]:[];}
async function _sbPatch(tab,id,data){patches.push(JSON.stringify(data));Object.assign(db[id],data);return [db[id]];}
async function lauf(url,method,body){const out=[];
  for(let i=0;i<3;i++){try{await _translateAndExec(url,method,JSON.parse(JSON.stringify(body)));out.push("ok");break;}catch(e){out.push(String(e&&e.message||e).slice(0,30));}}
  return out;}
function _arr(v){return (typeof v==="string")?JSON.parse(v||"[]"):(v||[]);}/* Rueckfall-PATCH traegt das Array (der echte _mapBody stringifiziert erst dort) */
function TL(){return _arr(db.F1.tank_log);}
function KL(){return _arr(db.F1.km_log);}
function neuStart(){reset();rpc=[];gets=[];patches=[];toasts=[];verlieren=0;rpcAntwort=null;}
var E={id:"tk1",datum:"2026-11-19",liter:40,preis:60,km:12345,foto:"sbpriv:epkolar-files/fahrzeuge/F1/tank/tk1.jpg",by:"A",kontrolliert:false,kontrolliert_von:null,kontrolliert_am:null};
var STALE=[E];/* lokaler Stand von Geraet A: kennt die Tankung von Geraet B (tANDERS) noch nicht */
"""

KOERPER = r"""
(async()=>{
 const R={};
 /* (a) Tank-Dialog (addTank-Koerper) und QR/Sammel (tankLog_add) bei vorhandener Funktion */
 neuStart();_fzTankRpcDa=null;
 R.dlg=await lauf("/api/fahrzeuge/F1","PUT",{_tankAtomar:{op:"add",eintrag:E,kmForce:false},tankLog:STALE,kmStand:12345});
 R.dlgRpc=rpc;R.dlgPatches=patches;R.dlgGets=gets;R.dlgTl=TL().map(x=>x.id);R.dlgKm=db.F1.km_stand;R.dlgKl=KL();
 neuStart();
 R.qr=await lauf("/api/fahrzeuge/F1","PUT",{tankLog_add:E,kmStand:12345});
 R.qrRpc=rpc;R.qrPatches=patches;R.qrTl=TL().map(x=>x.id);R.qrKl=KL();
 /* (c) Antwort verloren -> Wiederholung derselben Sendung */
 neuStart();verlieren=1;
 R.wdh=await lauf("/api/fahrzeuge/F1","PUT",{tankLog_add:E,kmStand:12345});
 R.wdhIds=rpc.map(c=>JSON.parse(c.body).p_eintrag.id);R.wdhTl=TL().map(x=>x.id);R.wdhKl=KL().map(x=>x.id);
 /* (d) Entfernen */
 neuStart();db.F1.tank_log=JSON.stringify([E,ANDERES]);
 R.del=await lauf("/api/fahrzeuge/F1","PUT",{_tankAtomar:{op:"del",id:"tk1"},tankLog:[]});
 R.delRpc=rpc;R.delPatches=patches;R.delTl=TL().map(x=>x.id);
 /* Admin-Korrektur nach unten (kmForce): Server haengt an, km_stand dann wie bisher unbedingt ueber den km-Zweig */
 neuStart();db.F1.km_stand=20000;
 R.force=await lauf("/api/fahrzeuge/F1","PUT",{_tankAtomar:{op:"add",eintrag:E,kmForce:true},tankLog:STALE,kmStand:12345});
 R.forceKm=db.F1.km_stand;R.forceKl=KL().map(x=>x.id);R.forcePatches=patches;
 /* abgewiesen (Fremdfahrzeug) -> Toast, kein Rueckfall-Schreiben */
 neuStart();rpcAntwort={ok:false,grund:"nicht_berechtigt"};
 R.nb=await lauf("/api/fahrzeuge/F1","PUT",{_tankAtomar:{op:"add",eintrag:E,kmForce:false},tankLog:STALE,kmStand:12345});
 R.nbPatches=patches;R.nbToasts=toasts;
 /* data: im Eintrag -> NIE an die Funktion, alter Weg (dort verschiebt _dbOhneDateien die Datei) */
 neuStart();const ED=Object.assign({},E,{id:"tk9",foto:"data:image/jpeg;base64,AAAA"});
 R.datei=await lauf("/api/fahrzeuge/F1","PUT",{tankLog_add:ED,kmStand:12345});
 R.dateiRpc=rpc.map(c=>c.body);R.dateiPatches=patches.length;
 /* (b) Funktion fehlt (404) -> bisheriger Weg; 404 gemerkt */
 neuStart();_fzTankRpcDa=null;rpcModus="404";
 R.f404=await lauf("/api/fahrzeuge/F1","PUT",{_tankAtomar:{op:"add",eintrag:E,kmForce:false},tankLog:STALE,kmStand:12345});
 R.f404Patches=patches;R.f404Gets=gets;R.f404Rpc=rpc.length;
 neuStart();
 R.f404b=await lauf("/api/fahrzeuge/F1","PUT",{_tankAtomar:{op:"del",id:"tk1"},tankLog:[]});
 R.f404bPatches=patches;R.f404bRpc=rpc.length;R.merk=_fzTankRpcDa;
 neuStart();
 R.f404c=await lauf("/api/fahrzeuge/F1","PUT",{tankLog_add:E,kmStand:12345});
 R.f404cPatches=patches;R.f404cRpc=rpc.length;
 process.stdout.write(JSON.stringify(R));
})().catch(e=>{process.stdout.write(JSON.stringify({crash:String(e&&e.stack||e)}));});
"""

ALT_KOERPER = r"""
(async()=>{
 const R={};
 neuStart();R.a=await lauf("/api/fahrzeuge/F1","PUT",{tankLog:STALE,kmStand:12345});R.aPatches=patches;R.aGets=gets;
 neuStart();R.b=await lauf("/api/fahrzeuge/F1","PUT",{tankLog:[]});R.bPatches=patches;
 neuStart();R.c=await lauf("/api/fahrzeuge/F1","PUT",{tankLog_add:E,kmStand:12345});R.cPatches=patches;
 R.rpc=rpc.length;
 process.stdout.write(JSON.stringify(R));
})().catch(e=>{process.stdout.write(JSON.stringify({crash:String(e&&e.stack||e)}));});
"""

HELFER = ("_fzTankHatDatei", "_fzTankRpc", "_fzTankAtomar")


def _lauf(src, node_exe, koerper=KOERPER, helfer=HELFER):
    code = PRELUDE + "\n".join(_fn(src, n) for n in helfer + ("_translateAndExec",)) + "\nvar _fzTankRpcDa=null;\n" + koerper
    r = _node(node_exe, code)
    assert "crash" not in r, r.get("crash", "")[:800]
    return r


@pytest.fixture(scope="module")
def lauf(index_html, node_exe):
    return _lauf(index_html, node_exe)


def _args(c):
    return json.loads(c["body"])


# ── (a) Anlegen: nur der eine Eintrag geht an den Server ──────────────────────────────────────

def test_anlegen_dialog_schickt_nur_den_eintrag(lauf):
    r = lauf
    assert r["dlg"] == ["ok"]
    assert [c["name"] for c in r["dlgRpc"]] == ["fz_tanklog_add"]
    a = _args(r["dlgRpc"][0])
    assert a == {"p_fahrzeug_id": "F1", "p_eintrag": a["p_eintrag"], "p_km": 12345, "p_km_log_id": None}
    assert a["p_eintrag"]["id"] == "tk1" and "tankLog" not in r["dlgRpc"][0]["body"]
    assert r["dlgPatches"] == [] and r["dlgGets"] == [], "kein Rueckfall-Schreiben, kein Lese-Aendern-Schreiben"
    # die Tankung von Geraet B bleibt erhalten (vorher: ganzes Array aus dem alten Stand -> weg)
    assert r["dlgTl"] == ["tk1", "tANDERS"]
    assert r["dlgKm"] == 12345 and [k["id"] for k in r["dlgKl"]] == ["km_tk1"]


def test_anlegen_qr_und_sammel_ueber_die_funktion(lauf):
    r = lauf
    assert r["qr"] == ["ok"] and [c["name"] for c in r["qrRpc"]] == ["fz_tanklog_add"]
    assert r["qrPatches"] == [] and r["qrTl"] == ["tk1", "tANDERS"]
    assert [k["id"] for k in r["qrKl"]] == ["km_tk1"]


# ── (c) Wiederholung ─────────────────────────────────────────────────────────────────────────

def test_wiederholung_gleiche_id_idempotent(lauf):
    r = lauf
    assert r["wdh"] == ["Failed to fetch", "ok"], r["wdh"]
    assert r["wdhIds"] == ["tk1", "tk1"], "Wiederholung muss dieselbe id senden"
    assert r["wdhTl"] == ["tk1", "tANDERS"], "genau ein Eintrag trotz zweimal gesendet"
    assert r["wdhKl"] == ["km_tk1"]


# ── (d) Entfernen ────────────────────────────────────────────────────────────────────────────

def test_entfernen_schickt_nur_die_id(lauf):
    r = lauf
    assert r["del"] == ["ok"]
    assert [c["name"] for c in r["delRpc"]] == ["fz_tanklog_del"]
    assert _args(r["delRpc"][0]) == {"p_fahrzeug_id": "F1", "p_eintrag_id": "tk1"}
    assert r["delPatches"] == [] and r["delTl"] == ["tANDERS"], "die fremde Tankung bleibt, kein ganzes Array"


def test_km_korrektur_nach_unten_bleibt_unbedingt(lauf):
    r = lauf
    assert r["force"] == ["ok"]
    assert r["forceKm"] == 12345, "Admin-Korrektur nach unten muss weiter wirken"
    assert r["forceKl"] == ["km_tk1"], "km-Zeile nicht doppelt"
    assert all("tank_log" not in p for p in r["forcePatches"]), r["forcePatches"]


def test_abgewiesen_wie_bisher_toast_ohne_schreiben(lauf):
    r = lauf
    assert r["nb"] == ["ok"] and r["nbPatches"] == []
    assert any("NICHT gespeichert" in t for t in r["nbToasts"]), r["nbToasts"]


def test_datei_im_eintrag_geht_nie_an_die_funktion(lauf):
    r = lauf
    assert r["dateiRpc"] == [], "data:-Inhalt darf nicht an fz_tanklog_add"
    assert r["dateiPatches"] == 1, "alter Weg (mit _dbOhneDateien in _sbPatch) uebernimmt"


# ── (b) 404 -> bisheriger Weg byte-gleich ────────────────────────────────────────────────────

def _alt_src(src):
    assert src.count(ROUTE_ZEILE) == 1
    return src.replace(ROUTE_ZEILE + "/* v3.9.1051", "/* v3.9.1051", 1)


def test_404_rueckfall_byte_gleich_zum_alten_weg(index_html, node_exe, lauf):
    neu = lauf
    alt = _lauf(_alt_src(index_html), node_exe, ALT_KOERPER, ())
    assert alt["rpc"] == 0
    assert neu["f404"] == ["ok"] and neu["f404Rpc"] == 1
    assert neu["f404Patches"] == alt["aPatches"], (neu["f404Patches"], alt["aPatches"])
    assert neu["f404Gets"] == alt["aGets"]
    assert neu["f404b"] == ["ok"] and neu["f404bPatches"] == alt["bPatches"]
    assert neu["f404c"] == ["ok"] and neu["f404cPatches"] == alt["cPatches"]
    # 404 wird fuer die Sitzung gemerkt: danach kein weiterer Versuch
    assert neu["f404bRpc"] == 0 and neu["f404cRpc"] == 0 and neu["merk"] is False
    # der Hinweis _tankAtomar geht nie als Spalte in einen PATCH
    assert not any("_tankAtomar" in p for p in neu["f404Patches"] + neu["f404bPatches"])


# ── (e) Umkehrproben ─────────────────────────────────────────────────────────────────────────

def test_umkehrprobe_ohne_route_geht_das_ganze_array(index_html, node_exe):
    r = _lauf(_alt_src(index_html), node_exe)
    assert r["dlgRpc"] == []
    assert any('"tank_log":[' in p for p in r["dlgPatches"]), "ohne Route geht das ganze Array"
    assert r["dlgTl"] == ["tk1"], "Umkehrprobe: die Tankung von Geraet B ist weg (Lost Update)"
    assert r["delRpc"] == [] and r["delPatches"]


def test_umkehrprobe_ohne_datei_riegel_ginge_base64_raus(index_html, node_exe):
    assert index_html.count(DATEI_RIEGEL) == 1
    r = _lauf(index_html.replace(DATEI_RIEGEL, "", 1), node_exe)
    assert r["dateiRpc"] and "data:image/jpeg;base64," in r["dateiRpc"][0]


# ── Bindung an die echte Signatur (SQL-Entwurf) ──────────────────────────────────────────────

def test_argumente_passen_zur_sql_signatur(lauf, index_html):
    assert list(_args(lauf["dlgRpc"][0]).keys()) == _sql_params("fz_tanklog_add")
    assert list(_args(lauf["qrRpc"][0]).keys()) == _sql_params("fz_tanklog_add")
    assert list(_args(lauf["delRpc"][0]).keys()) == _sql_params("fz_tanklog_del")
    # Buero-Wege (_tankMark, _tankEditSave): gleiche drei Namen wie fz_tanklog_set
    assert _sql_params("fz_tanklog_set") == ["p_fahrzeug_id", "p_eintrag_id", "p_patch"]
    assert index_html.count('_fzTankRpc("fz_tanklog_set",{p_fahrzeug_id:fzId,p_eintrag_id:eid,p_patch:') == 2


# ── Erzeuger ─────────────────────────────────────────────────────────────────────────────────

def test_sammel_entfernen_reiht_id_hinweis_ein(index_html, node_exe):
    r = _batch_lauf(node_exe, index_html)
    assert len(r["q"]) == 1
    assert r["q"][0]["body"]["_tankAtomar"] == {"op": "del", "id": "tkB"}


def test_tank_dialog_reiht_genau_den_lokalen_eintrag_ein(index_html):
    a = index_html.index("const addTank=async")
    blk = index_html[a:index_html.index("const addSchaden=", a)]
    assert "f.tankLog=[_tkNeu,...(f.tankLog||[])];" in blk, "lokaler Stand und Server-Eintrag sind dasselbe Objekt"
    assert 'u=>({_tankAtomar:{op:"add",eintrag:_tkNeu,kmForce:!!_r.kmDowngraded},tankLog:u.tankLog,kmStand:u.kmStand})' in blk


def test_buero_wege_erst_funktion_dann_rueckfall(index_html):
    for name, nxt in (("const _tankMark=async", "const _tankMarkOk="), ("const _tankEditSave=async", "const loadAll=")):
        a = index_html.index(name)
        blk = index_html[a:index_html.index(nxt, a)]
        i_rpc = blk.index('_fzTankRpc("fz_tanklog_set"')
        i_get = blk.index('_sbGet("fahrzeuge"')
        assert i_rpc < i_get, name
        assert "const _rr=_ra.fehlt?null:(_ra.res||{});" in blk and "const rows=_rr?null:await _sbGet(" in blk, name


BUERO_PRELUDE = r"""
var curUser={name:"Buero B"};var fz=[{id:"F1",kmStand:12000,tankLog:[{id:"tANDERS",datum:"2026-11-18",liter:30,preis:45,km:12000}]}];
function setFahrzeuge(fn){fz=fn(fz);}var fotoView={e:{id:"tANDERS"}};function _setTankFotoView(fn){fotoView=fn(fotoView);}function _setTankEdit(){}
"""


def _buero(src, node_exe, modus, antwort="null"):
    def teil(a, b):
        i = src.index(a)
        return src[i:src.index(b, i)]
    code = (PRELUDE + BUERO_PRELUDE + _fn(src, "_fzTankRpc") + "\nvar _fzTankRpcDa=null;\n" +
            teil("const _tankMark=async", "\n  const _tankMarkOk=") + "\n" +
            teil("const _tankEditSave=async", "\n  const loadAll=") + "\n" +
            "rpcModus=" + json.dumps(modus) + ";rpcAntwort=" + antwort + ";" + r"""
(async()=>{const R={};
 R.mark=await _tankMark("F1","tANDERS",true);R.markRpc=rpc.map(c=>JSON.parse(c.body));R.markGets=gets.length;R.markPatches=patches.slice();
 R.tlLokal=fz[0].tankLog[0];R.toasts=toasts.slice();
 rpc=[];gets=[];patches=[];
 await _tankEditSave("F1","tANDERS",{datum:"2026-11-18",liter:31,preis:46,km:12100});
 R.editRpc=rpc.map(c=>JSON.parse(c.body));R.editGets=gets.length;R.editPatches=patches.slice();R.fz=fz[0];R.toasts2=toasts.slice();
 process.stdout.write(JSON.stringify(R));})().catch(e=>{process.stdout.write(JSON.stringify({crash:String(e&&e.stack||e)}));});
""")
    r = _node(node_exe, code)
    assert "crash" not in r, r.get("crash", "")[:800]
    return r


def test_buero_kontrolle_ueber_die_funktion(index_html, node_exe):
    r = _buero(index_html, node_exe, "ok")
    assert r["mark"] is True and r["markGets"] == 0 and r["markPatches"] == []
    assert [list(a.keys()) for a in r["markRpc"]] == [["p_fahrzeug_id", "p_eintrag_id", "p_patch"]]
    assert sorted(r["markRpc"][0]["p_patch"].keys()) == ["kontrolliert", "kontrolliert_am", "kontrolliert_von"]
    assert r["tlLokal"]["kontrolliert"] is True and r["tlLokal"]["kontrolliert_von"] == "Buero B"
    assert r["editGets"] == 0 and r["editPatches"] == []
    assert r["editRpc"][0]["p_patch"] == {"datum": "2026-11-18", "liter": 31, "preis": 46, "km": 12100}
    assert r["fz"]["tankLog"][0]["km"] == 12100


def test_buero_kontrolle_404_bisheriger_weg(index_html, node_exe):
    r = _buero(index_html, node_exe, "404")
    assert r["mark"] is True and r["markGets"] == 1 and len(r["markPatches"]) == 1
    assert len(r["markRpc"]) == 1 and r["editRpc"] == [], "404 gemerkt -> Korrektur fragt nicht nochmal"
    assert r["editGets"] == 1 and len(r["editPatches"]) == 1 and '"km_stand":12100' in r["editPatches"][0]


def test_buero_abgewiesen_dieselbe_meldung(index_html, node_exe):
    r = _buero(index_html, node_exe, "ok", '{ok:false,grund:"nicht_berechtigt"}')
    assert r.get("mark") is None and r["markPatches"] == []  # undefined -> kein Rueckgaengig-Angebot
    assert any("Tank-Kontrolle NICHT gespeichert" in t for t in r["toasts"]), r["toasts"]
    assert any("Tank-Korrektur NICHT gespeichert" in t for t in r["toasts2"]), r["toasts2"]


def test_buero_rpc_404_wird_gemerkt(index_html, node_exe):
    code = PRELUDE + _fn(index_html, "_fzTankRpc") + r"""
var _fzTankRpcDa=null;rpcModus="404";
(async()=>{const a=await _fzTankRpc("fz_tanklog_set",{p_fahrzeug_id:"F1",p_eintrag_id:"x",p_patch:{kontrolliert:true}});
 const b=await _fzTankRpc("fz_tanklog_set",{p_fahrzeug_id:"F1",p_eintrag_id:"x",p_patch:{kontrolliert:true}});
 rpcModus="ok";_fzTankRpcDa=null;db.F1.tank_log=JSON.stringify([ANDERES]);
 const c=await _fzTankRpc("fz_tanklog_set",{p_fahrzeug_id:"F1",p_eintrag_id:"tANDERS",p_patch:{kontrolliert:true}});
 process.stdout.write(JSON.stringify({a:a,b:b,n:rpc.length,c:c,tl:TL()}));})();
"""
    r = _node(node_exe, code)
    assert r["a"] == {"fehlt": True} and r["b"] == {"fehlt": True} and r["n"] == 2
    assert r["c"]["res"]["ok"] is True and r["tl"][0]["kontrolliert"] is True


# ── SQL-Entwurf statisch ─────────────────────────────────────────────────────────────────────

def _fn_rumpf(sql, name):
    a = sql.index("create or replace function public." + name + "(")
    e = sql.index("end $$;", a)
    return sql[a:e]


@pytest.mark.parametrize("name", ["fz_tanklog_add", "fz_tanklog_del", "fz_tanklog_set"])
def test_sql_funktion_gehaertet(name):
    s = _sql()
    b = _fn_rumpf(s, name)
    assert "security definer" in b
    assert "set search_path to 'public', 'pg_temp'" in b
    assert "for update" in b, "Zeile sperren"
    assert "public.is_hr() or (v_fahrer is not null and v_fahrer = public.current_monteur_id())" in b, "RLS gespiegelt"
    assert re.search(r"revoke all on function public\." + name + r"\([^)]*\)\s+from public, anon;", s)
    assert re.search(r"grant execute on function public\." + name + r"\([^)]*\)\s+to authenticated;", s)
    assert not re.search(r"grant execute on function public\." + name + r"\([^)]*\)\s+to [^;]*anon", s)


def test_sql_kopf_und_riegel():
    s = _sql()
    assert s.startswith("-- IDEMPOTENT")
    assert "NICHT APPLIZIERT" in s
    add = _fn_rumpf(s, "fz_tanklog_add")
    st = _fn_rumpf(s, "fz_tanklog_set")
    for b in (add, st):
        assert "position('data:' in" in b and "position(';base64,' in" in b and "files_not_allowed" in b
    # idempotent per id
    assert "if not exists (select 1 from jsonb_array_elements(v_tl) e where e->>'id' = v_id)" in add
    assert "'km_' || v_id" in add and "greatest(coalesce(f.km_stand, 0), p_km)" in add
    # text <-> jsonb: NULL/'' -> [] ueber die Hilfsfunktion, kein stiller Neuanfang bei Korruption
    hj = s[s.index("create or replace function public._fz_json_array("):]
    assert "return '[]'::jsonb" in hj and "_korrupt" in hj
    assert "revoke all on function public._fz_json_array(text, text) from public, anon, authenticated;" in s
    # Probe-Block nur als Kommentar, mit ROLLBACK
    assert "-- begin;" in s and "-- rollback;" in s
    for zeile in s.splitlines():
        z = zeile.strip().lower()
        assert not z.startswith("begin;") and not z.startswith("commit;"), zeile


def test_sql_keine_kaskade_kein_drop_table():
    s = _sql().lower()
    assert "cascade" not in s.replace("kaskade", "")
    assert "drop table" not in s and "delete from" not in s
