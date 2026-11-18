# -*- coding: utf-8 -*-
"""18.11.2026 Warteschlange idempotent (Folge von v3.9.1043: Zeitueberschreitung wird WIEDERHOLT statt verworfen).

Fall "Antwort verloren": der Server hat die Zeile schon angelegt, der Client sieht nur eine Zeitueberschreitung
und schickt dieselbe Sendung noch einmal.

Node fuehrt die ECHTEN Funktionen aus index.html aus (_translateAndExec, _sbPost, _sbInsertIfAbsent, PhotoQ) gegen
einen falschen Server, der Zeilen nach PK speichert und PostgREST nachbildet:
  * resolution=ignore-duplicates + vorhandener PK -> 201 ohne Zeile (ON CONFLICT DO NOTHING)
  * Plain-POST + vorhandener PK -> 409
  * POST ohne id -> Server vergibt eine id (wie gen_random_uuid-Default) -> jede Wiederholung ist eine NEUE Zeile

Gepruefte Wege (Inventar C:/repos/epk-queue-idempotenz-inventar-2026-11-18.md, Abschnitt A):
  A1 POST /api/fz-termine/:fz, A2 POST /api/wz-service/:wz, A3 POST /api/photos/:typ/:entity, A4 PhotoQ.flush.
Erwartung: genau EINE Zeile, die Wiederholung gilt als Erfolg (kein 409 -> 5x -> Verwerfen + Falschwarnung).
Umkehrproben: (1) Rueckbau auf Plain-_sbPost -> Wiederholung endet in 409; (2) ohne stabile id -> Duplikat.
"""
import json
import os
import re
import subprocess
import tempfile

import pytest

from conftest import _extract_fn


def _node(node_exe, code):
    """_translateAndExec ist zu lang fuer `node -e` (Windows-Befehlszeile) -> ueber eine Datei."""
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


def _photoq(src):
    m = re.search(r"const PhotoQ=\{[\s\S]*?\n\};", src)
    assert m
    return m.group(0)


PRELUDE = r"""
var navigator={onLine:true};var window={dispatchEvent:()=>true};class CustomEvent{constructor(t,o){this.type=t;this.detail=(o||{}).detail;}}
var setTimeout=()=>0,clearTimeout=()=>{};
var SB_REST="https://x/rest/v1";
var rows={};var verlieren=0;var anfragen=[];var autoId=0;
function _sbWH(p){return {"Content-Type":"application/json","Prefer":p||"return=representation"};}
function _sbH(h){return h||{};}
function _fT(init){return init;}
async function _authRetry(fn){return await fn();}
function _onAuthFail(){}
async function _dbOhneDateien(t,id,d){return d;}
function _mapBody(b){return b;}
function _antwort(status,body){return {ok:status>=200&&status<300,status:status,text:async()=>body||"",json:async()=>{if(!body)throw new Error("leer");return JSON.parse(body);}};}
async function fetch(url,init){
  const tab=url.slice(SB_REST.length+1).split("?")[0];
  const pref=(init.headers&&init.headers.Prefer)||"";
  anfragen.push(tab+"|"+pref);
  const d=JSON.parse(init.body);
  rows[tab]=rows[tab]||{};
  const id=d.id?String(d.id):("srv"+(++autoId));
  let res;
  if(rows[tab][id]){res=pref.indexOf("ignore-duplicates")>=0?_antwort(201,""):_antwort(409,'{"code":"23505","message":"duplicate key value violates unique constraint"}');}
  else{rows[tab][id]=d;res=_antwort(201,pref.indexOf("return=minimal")>=0?"":JSON.stringify([d]));}
  if(verlieren>0){verlieren--;const e=new Error("signal timed out");e.name="TimeoutError";throw e;}/* Server HAT angelegt, Antwort geht verloren */
  return res;
}
function zahl(t){return Object.keys(rows[t]||{}).length;}
"""

ROUTE_KOERPER = r"""
(async()=>{
 const R={};
 async function lauf(url,body){/* wie doSync seit 1043: Zeitueberschreitung -> Eintrag bleibt -> naechster Lauf sendet DIESELBE Sendung */
   const out=[];
   for(let i=0;i<3;i++){try{await _translateAndExec(url,"POST",body);out.push("ok");break;}catch(e){out.push(String(e&&e.message||e).slice(0,40));}}
   return out;}
 verlieren=1;R.fz=await lauf("/api/fz-termine/FZ1",{id:"t1",typ:"Service",datum:"2026-11-18"});R.fzRows=zahl("fz_termine");
 verlieren=1;R.wz=await lauf("/api/wz-service/WZ1",{id:"s1",art:"Service"});R.wzRows=zahl("wz_service");
 verlieren=1;R.ph=await lauf("/api/photos/ticket/T1",{id:"p1",name:"a.jpg"});R.phRows=zahl("photos");
 /* ohne id (bewusst id-loser Altbestand): bleibt Plain-POST, Server vergibt id -> Wiederholung = Duplikat (dokumentiert) */
 verlieren=1;R.ohneId=await lauf("/api/fz-termine/FZ2",{typ:"Service",datum:"2026-11-19"});R.ohneIdRows=Object.values(rows.fz_termine).filter(r=>r.fahrzeug_id==="FZ2").length;
 R.anfragen=anfragen;
 process.stdout.write(JSON.stringify(R));
})().catch(e=>{process.stdout.write(JSON.stringify({crash:String(e&&e.stack||e)}));});
"""


def _route(src, node_exe):
    code = PRELUDE + "\n".join(_fn(src, n) for n in ("_translateAndExec", "_sbPost", "_sbInsertIfAbsent")) + "\n" + ROUTE_KOERPER
    return _node(node_exe, code)


def _route_befunde(r):
    if "crash" in r:
        return ["Probe abgestuerzt: " + r["crash"][:300]]
    b = []
    for k, tab in (("fz", "fzRows"), ("wz", "wzRows"), ("ph", "phRows")):
        if r[k][-1] != "ok" or len(r[k]) != 2:
            b.append("%s: Wiederholung nach verlorener Antwort scheitert: %r" % (k, r[k]))
        if r[tab] != 1:
            b.append("%s: %r Zeilen statt 1" % (k, r[tab]))
    return b


def test_routen_wiederholung_ohne_duplikat_und_ohne_409(index_html, node_exe):
    r = _route(index_html, node_exe)
    assert _route_befunde(r) == []
    # die stabile id geht ueber ignore-duplicates, der id-lose Altbestand bleibt Plain-POST
    assert "fz_termine|return=minimal,resolution=ignore-duplicates" in r["anfragen"]
    assert "fz_termine|return=representation" in r["anfragen"]


def test_ohne_stabile_id_waere_es_ein_duplikat(index_html, node_exe):
    """Umkehrprobe zum Grund der Umstellung: OHNE Client-id erzeugt dieselbe Wiederholung eine zweite Zeile.
    Genau deshalb wird die id bei der ERZEUGUNG vergeben und nie zur Sendezeit."""
    r = _route(index_html, node_exe)
    assert r["ohneId"] == ["signal timed out", "ok"], r["ohneId"]
    assert r["ohneIdRows"] == 2, r["ohneIdRows"]


ROUTE_RUECKBAU = [
    ('if(_fztM&&_fztM.id){await _sbInsertIfAbsent("fz_termine",_fztM);}else{await _sbPost("fz_termine",_fztM);}',
     'await _sbPost("fz_termine",_fztM);'),
    ('if(_wzsM&&_wzsM.id){await _sbInsertIfAbsent("wz_service",_wzsM);}else{await _sbPost("wz_service",_wzsM);}',
     'await _sbPost("wz_service",_wzsM);'),
    ('if(mapped&&mapped.id){await _sbInsertIfAbsent("photos",mapped);}else{await _sbPost("photos",mapped);}',
     'await _sbPost("photos",mapped);'),
]


@pytest.mark.parametrize("alt,neu", ROUTE_RUECKBAU)
def test_umkehrprobe_routen(index_html, node_exe, alt, neu):
    assert index_html.count(alt) == 1, alt
    b = _route_befunde(_route(index_html.replace(alt, neu, 1), node_exe))
    assert b, "Rueckbau auf Plain-POST muss auffallen: " + neu
    assert any("HTTP409" in x for x in b), b


PQ_KOERPER = r"""
var mem={photoQueue:[]};var ODB={load:async k=>JSON.parse(JSON.stringify(mem[k]||[])),save:async(k,v)=>{mem[k]=JSON.parse(JSON.stringify(v));},set:async(k,_d,v)=>{mem[k]=JSON.parse(JSON.stringify(v));}};
async function _sbUploadFile(path){return "https://x/"+path;}
function _storagePath(c,pid,n){return "photos/"+pid+"/"+n;}
function _netzFehlerArt(e){return (e&&e.name==="TimeoutError")?"zeit":"";}
function _netzPauseMs(){return 5000;}
(async()=>{
 const R={};
 await PhotoQ.add({entityType:"ticket",entityId:"T1",projectId:"P",name:"a.jpg",dataUrl:"data:image/jpeg;base64,AAAA"});
 const id=mem.photoQueue[0].id;
 verlieren=1;R.l1=await PhotoQ.flush();
 R.nach1=mem.photoQueue.map(x=>({st:x.status,r:x.retries}));
 R.l2=await PhotoQ.flush();
 R.nach2=mem.photoQueue.map(x=>({st:x.status,r:x.retries,e:(x.lastError||"").slice(0,12)}));
 R.rows=zahl("photos");R.idGleich=!!(rows.photos&&rows.photos[id]);
 process.stdout.write(JSON.stringify(R));
})().catch(e=>{process.stdout.write(JSON.stringify({crash:String(e&&e.stack||e)}));});
"""


def _pq(src, node_exe):
    code = PRELUDE + _fn(src, "_sbPost") + "\n" + _fn(src, "_sbInsertIfAbsent") + "\n" + _photoq(src) + "\n" + PQ_KOERPER
    return _node(node_exe, code)


def _pq_befunde(r):
    if "crash" in r:
        return ["Probe abgestuerzt: " + r["crash"][:300]]
    b = []
    if r["nach2"] != []:
        b.append("Foto bleibt nach verlorener Antwort in der Warteschlange haengen: %r" % r["nach2"])
    if r["rows"] != 1 or not r["idGleich"]:
        b.append("photos-Zeilen %r (soll 1 mit der id aus PhotoQ.add)" % r["rows"])
    return b


def test_photoq_wiederholung_ohne_duplikat(index_html, node_exe):
    r = _pq(index_html, node_exe)
    assert _pq_befunde(r) == []
    assert r["nach1"] and r["nach1"][0]["st"] == "error", r  # erster Lauf: Zeitueberschreitung, Foto bleibt


def test_umkehrprobe_photoq(index_html, node_exe):
    alt = 'await _sbInsertIfAbsent("photos",_mapBody({id:ph.id,'
    assert index_html.count(alt) == 1
    b = _pq_befunde(_pq(index_html.replace(alt, 'await _sbPost("photos",_mapBody({id:ph.id,', 1), node_exe))
    assert b and "haengen" in b[0], b


def test_photoq_id_bei_erzeugung(index_html):
    """Die id, ueber die dedupliziert wird, vergibt PhotoQ.add beim Einreihen - nicht flush beim Senden."""
    pq = _photoq(index_html)
    add = pq[pq.index("async add(photo)"):pq.index("async getAll()")]
    assert "id:photo.id||" in add and "randomUUID" in add
    fl = pq[pq.index("async flush()"):]
    assert "randomUUID" not in fl and "uid()" not in fl
