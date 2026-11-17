# -*- coding: utf-8 -*-
"""Ticket-Fotos im Speicher - Standard AN mit Sicherheitsnetz (Entscheid Sebastian, 17.11.2026).

Node fuehrt die ECHTE PhotoQ samt Ticket-Netz (_tkFotoStand/_tkFotoStandLaden/_tkFotoNachLauf/
_tkKachelQuelle und den Ereignis-Block) gegen einen nachgebauten, dauerhaften Speicher aus:

  * Upload abgelehnt (401 / 403 / 500 / Netz weg): Foto bleibt in der Warteschlange (volles Bild),
    Status "error", Hinweis-Toast, Marke im Ticket (Stand-Karte), naechster Versuch geplant;
    die Kachel zeigt ohne Vorschaubild das lokale Bild.
  * Neustart: Eintrag stand auf "uploading" (Absturz mitten im Upload) und hat schon > 10 Versuche -
    der Start-Anstoss nimmt ihn trotzdem auf, der Upload gelingt unter GENAU dem Pfad, auf den das
    Ticket verweist, keine photos-Zeile, Warteschlange leer, Marke weg.
  * Schalter: Standard AN, localStorage "0" schaltet je Geraet ab.
Umkehrproben: stilles Verwerfen, kein Hinweis, 10er-Deckel, haengendes "uploading", keine Marke,
kein lokales Bild.
"""
import json
import re

import pytest

from conftest import run_node_snippet, _extract_fn


def _photoq(src):
    m = re.search(r"const PhotoQ=\{[\s\S]*?\n\};", src)
    assert m
    return m.group(0)


def _netz(src):
    a = src.index("const _tkFotoStand={")
    teile = [src[a:src.index("\n", a)]]
    for n in ("_tkFotoStandLaden", "_tkFotoNachLauf", "_tkKachelQuelle", "_tkFotoSrc", "_tkFotoUrl", "_tkFlag"):
        f = _extract_fn(src, n)
        assert f, n
        teile.append(f)
    i = src.index('window.addEventListener("epk-photoq"')
    b = src.rindex("if(typeof window!==\"undefined\"&&window.addEventListener){", 0, i)
    e = src.index("\n}\n", i) + 3
    teile.append(src[b:e])
    return "\n".join(teile)


PRELUDE = r"""
var timers=[];var setTimeout=(f,ms)=>{timers.push({f:f,ms:ms});return timers.length;};var clearTimeout=()=>{};
var clock=1000000;Date.now=()=>clock;
var LS={};var localStorage={getItem:k=>(k in LS?LS[k]:null),setItem:(k,v)=>{LS[k]=String(v);},removeItem:k=>{delete LS[k];}};
var H={};var toasts=[];
var window={addEventListener:(t,f)=>{(H[t]=H[t]||[]).push(f);},dispatchEvent:ev=>{(H[ev.type]||[]).forEach(f=>f(ev));return true;},__toast:(m,t)=>toasts.push(m)};
class CustomEvent{constructor(t,o){this.type=t;this.detail=(o||{}).detail;}}
var navigator={onLine:true};
var mem={photoQueue:[]};var ODB={load:async k=>JSON.parse(JSON.stringify(mem[k]||[])),save:async(k,v)=>{mem[k]=JSON.parse(JSON.stringify(v));},set:async(k,_d,v)=>{mem[k]=JSON.parse(JSON.stringify(v));}};
var SB_STORAGE="https://x.supabase.co/storage/v1",SB_BUCKET="epkolar-files";
var modus=[],up=[],posts=[];
async function _sbUploadFile(path,d){const m=modus.shift()||"ok";up.push(path+"|"+m+"|"+d.length);
  if(m==="401")throw new Error("Auth:401 abgelaufen");if(m==="403")throw new Error("HTTP403 Storage upload failed: denied");
  if(m==="500")throw new Error("HTTP500 Storage upload failed");if(m==="netz")throw new TypeError("Failed to fetch");
  return "https://x.supabase.co/storage/v1/object/public/epkolar-files/"+path;}
function _storagePath(c,pid,n){return "photos/"+pid+"/1_"+n;}
async function _sbPost(t,b){posts.push(t);}function _mapBody(b){return b;}
async function warte(){for(let i=0;i<30;i++)await new Promise(r=>setImmediate(r));}
"""

KOERPER = r"""
(async()=>{
 const R={schritte:[]};
 const PFAD="tickets/P1/T1/1700000000000_0.jpg";
 const ticketFoto={name:"a.jpg",path:PFAD,thumb:"",w:2400,h:1800};/* so steht es im Ticket (Vorschaubild fehlte) */
 await PhotoQ.add({entityType:"ticket",entityId:"T1",projectId:"P1",context:"Ticket-Foto",name:"a.jpg",dataUrl:"data:image/jpeg;base64,VOLL"+"A".repeat(5000),storagePath:PFAD,nurStorage:true});
 await warte();
 for(const m of ["401","403","500","netz"]){clock+=61000;modus=[m];await PhotoQ.flush();await warte();
   const q=mem.photoQueue;const st=_tkFotoStand.map[PFAD];
   R.schritte.push({m:m,q:q.length,status:q[0]&&q[0].status,voll:!!(q[0]&&q[0].dataUrl&&q[0].dataUrl.length>5000),
     marke:!!st,toasts:toasts.length,quelle:_tkKachelQuelle(ticketFoto,st).slice(0,27)});}
 R.timer=timers.filter(t=>t.ms!==8000).map(t=>t.ms);
 /* Neustart: Absturz mitten im Upload, schon viele Versuche */
 if(mem.photoQueue[0]){mem.photoQueue[0].status="uploading";mem.photoQueue[0].retries=12;}
 _tkFotoStand.map={};_tkFotoStand.t=null;const t0=toasts.length;
 const start=timers.find(t=>t.ms===8000);R.startAnstoss=!!start;
 modus=["ok"];if(start)start.f();await warte();await warte();
 R.nach={q:mem.photoQueue.length,up:up[up.length-1],posts:posts.length,marke:!!_tkFotoStand.map[PFAD],neueToasts:toasts.length-t0,
   pfadGleich:(up[up.length-1]||"").split("|")[0]===ticketFoto.path};
 R.flag={leer:_tkFlag("epk_tk_foto_storage",true),null:(LS.epk_tk_foto_storage="0",_tkFlag("epk_tk_foto_storage",true)),eins:(LS.epk_tk_foto_storage="1",_tkFlag("epk_tk_foto_storage",true))};
 R.quelleMitThumb=_tkKachelQuelle({path:PFAD,thumb:"data:image/jpeg;base64,TH"},{lokal:"data:image/jpeg;base64,VOLL"});
 process.stdout.write(JSON.stringify(R));
})();
"""


def _probe(src, node_exe):
    return json.loads(run_node_snippet(node_exe, PRELUDE + _photoq(src) + "\n" + _netz(src) + "\n" + KOERPER))


def _befunde(r):
    b = []
    for s in r["schritte"]:
        if s["q"] != 1 or not s["voll"]:
            b.append("%s: Foto nicht mehr (voll) in der Warteschlange - stiller Verlust" % s["m"])
        if s["status"] != "error":
            b.append("%s: Status %r statt error" % (s["m"], s["status"]))
        if not s["marke"]:
            b.append("%s: keine Marke im Ticket" % s["m"])
        if s["quelle"] != "data:image/jpeg;base64,VOLL":
            b.append("%s: Kachel zeigt %r statt des lokalen Bildes" % (s["m"], s["quelle"]))
    if [s["toasts"] for s in r["schritte"]] != [1, 2, 3, 4]:
        b.append("Fehler nicht sichtbar (Toasts je Fehlschlag): %r" % [s["toasts"] for s in r["schritte"]])
    if not r["timer"] or r["timer"][0] != 15000:
        b.append("kein naechster Versuch geplant: %r" % r["timer"])
    if not r["startAnstoss"]:
        b.append("kein Anstoss nach dem Neustart")
    n = r["nach"]
    if n["q"] != 0 or not (n["up"] or "").endswith("|ok|" + str(len("data:image/jpeg;base64,VOLL") + 5000)) or not n["pfadGleich"]:
        b.append("Neustart: Foto nicht unter dem Ticket-Pfad nachgeladen: %r" % n)
    if n["posts"] != 0:
        b.append("Ticket-Foto schreibt eine photos-Zeile")
    if n["marke"]:
        b.append("Marke bleibt nach erfolgreichem Upload")
    if n["neueToasts"] != 0:
        b.append("Erfolg meldet einen Fehler")
    if r["flag"] != {"leer": True, "null": False, "eins": True}:
        b.append("Schalter: %r" % r["flag"])
    if r["quelleMitThumb"] != "data:image/jpeg;base64,TH":
        b.append("Vorschaubild hat nicht Vorrang")
    return b


def test_sicherheitsnetz(index_html, node_exe):
    assert _befunde(_probe(index_html, node_exe)) == []


@pytest.mark.parametrize("alt,neu", [
    ('await PhotoQ.update(ph.id,{status:"error",retries:(ph.retries||0)+1,lastError:e.message||"Netzwerkfehler"});fail++;',
     'await PhotoQ.remove(ph.id);fail++;'),
    ("if(ph.nurStorage)tkFail++;", ""),
    ("&&((x.retries||0)<10||x.nurStorage));", "&&(x.retries||0)<10);"),
    ('x.status==="error"||(x.nurStorage&&x.status==="uploading"))&&(', 'x.status==="error")&&('),
    ("if(x&&x.nurStorage&&x.storagePath)m[x.storagePath]=", "if(false)m[x.storagePath]="),
    ("if(ph&&typeof ph===\"object\"&&!ph.dataUrl&&!ph.thumb&&st&&st.lokal)return st.lokal;", ""),
    ('PhotoQ._meld({art:"flush",ok:ok,fail:fail,tkFail:tkFail});', ""),
    ('if(v==="0")return false;', ""),
])
def test_sicherheitsnetz_umkehrprobe(index_html, node_exe, alt, neu):
    assert index_html.count(alt) == 1, "Anker: " + alt
    try:
        befunde = _befunde(_probe(index_html.replace(alt, neu, 1), node_exe))
    except Exception as ex:
        befunde = [str(ex)[:200]]
    assert befunde, "Riegel blind fuer: " + alt


def test_sicherheitsnetz_verdrahtet(index_html):
    """Beide Foto-Raster (Ticket-Detail, Schnellblatt) zeichnen ueber TkFotoKachel und zeigen den Hinweis."""
    assert index_html.count("React.createElement(TkFotoKachel,{key:") == 2
    assert index_html.count("React.createElement(TkFotoHinweis,{photos:ticket.photos})") == 2
    assert index_html.count('_tkFlag("epk_tk_foto_storage",true)') == 2
