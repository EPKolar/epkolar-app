# -*- coding: utf-8 -*-
"""Plaene Stufe 3 - Ticket-Fotos raus aus dem Ticket-Body.

Vorher: Fotos als Base64 (bis 2400 px) im Ticket, JEDER PUT aus updateTicket schickte
das ganze photos-Array mit - auch ein reiner Status- oder Zuweisungswechsel
(Lehre "Riesen-Body wedged die SyncQueue").

Riegel, jeweils mit den ECHTEN Funktionen aus index.html per node ausgefuehrt:
1. Status- und Zuweisungs-PUT tragen keine Fotodaten (kein "photos", kein "data:").
2. Neues Foto bei eingeschaltetem Storage-Schalter: PhotoQ bekommt das volle Bild mit
   festem Pfad tickets/<projekt>/<ticket>/..., im Ticket-PUT und -POST steht nur
   {name,path,thumb,w,h,takenAt}. Ein veralteter Zustand laedt dasselbe Foto nicht zweimal.
3. Alte Tickets mit Base64 werden weiter angezeigt (_tkFotoSrc).
4. Beide Schalter aus: PUT-Body Byte fuer Byte wie bis v3.9.1030, Foto-Eintrag wie bisher.
5. PhotoQ.flush nutzt den mitgebrachten Pfad und legt fuer Ticket-Fotos keine photos-Zeile an;
   alle anderen Fotos laufen unveraendert.
Umkehrproben: zurueckgebaut muss jeder Riegel anschlagen.
"""
import io
import json
import re
import sys
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL / "tests"))
from conftest import _extract_fn, run_node_snippet  # noqa: E402

# Der PUT-Body von updateTicket, wie er bis v3.9.1030 inline stand (Vergleich "Schalter aus").
ALT_BODY_JS = ('({title:_u.title,description:_u.description||"",status:_u.status,priority:_u.priority||"mittel",'
               'assignee:_u.assignee||"",gewerk:_u.gewerk||_u.layer||"",layer:_u.layer||"",x:_u.x,y:_u.y,'
               'photos:_u.photos||[],comments:_u.comments||[],status_history:_u.status_history||[],'
               'type:_u.type||"",due_date:_u.dueDate||null,progress:_u.progress||0,updated_at:_u.updatedAt||td2()})')


@pytest.fixture(scope="module")
def src():
    return io.open(str(WURZEL / "index.html"), encoding="utf-8", newline="").read()


def _stueck(src, a, b):
    i = src.index("const " + a + "=")
    return src[i:src.index("const " + b + "=", i)]


def _helfer(src):
    teile = [_extract_fn(src, n) for n in ("_optionalChain", "_tkFlag", "_tkNurGeaendert", "_tkFotoUrl",
                                            "_tkFotoSrc", "_tkFotoEintrag", "_tkFotosAuslagern")]
    assert all(teile), "Helfer fehlt"
    m = re.search(r"const _tkAusgelagert=[^\n]*", src)
    assert m, "_tkAusgelagert fehlt"
    return "\n".join(teile) + "\n" + m.group(0) + "\n"


PRELUDE = r"""
var store={};var localStorage={getItem:k=>(k in store?store[k]:null),setItem:(k,v)=>{store[k]=String(v);}};
var window={};var navigator={onLine:false};
var SB_STORAGE="https://x.supabase.co/storage/v1",SB_BUCKET="epkolar-files";
var pq=[];var PhotoQ={add:a=>{pq.push(a);return Promise.resolve(true);},flush:()=>Promise.resolve({ok:0})};
var sq=[];var SQ={push:a=>{sq.push(JSON.parse(JSON.stringify(a)));}};
function _tkThumb(){return Promise.resolve("data:image/jpeg;base64,THUMB");}
function td2(){return "2026-11-17";}function uid(){return "NEU1";}
var _TICKET2MANGEL_ST={},forms={maengel:[]},layers=[],_vpMid="m1",_vpIsField=false,isAdmin=true,selPlan={id:"PL1"};
function setForms(){}function _mgVerlaufFeld(){return {};}function _mgVerlaufPut(){}
function setSelTicket(){}function setNewTicket(){}function setSideMode(){}function setPendingPin(){}
var BIG="data:image/jpeg;base64,"+"A".repeat(200000);
var T={id:"T1",pid:"P1",planId:"PL1",title:"Steckdose",description:"",status:"offen",priority:"mittel",assignee:"",
  layer:"l1",gewerk:"l1",x:10,y:20,type:"info",dueDate:"",progress:0,updatedAt:"2026-11-16",status_history:[],
  comments:[],photos:[{name:"a.jpg",dataUrl:BIG,takenAt:"2026-11-01"},{name:"b.jpg",dataUrl:BIG,takenAt:"2026-11-02"}]};
var planData={tickets:[T]};function setPlanData(f){planData=f(planData);}
var p={id:"P1",name:"Projekt"};var newTicket=null;
"""


def _probe(src, node_exe):
    upd = _stueck(src, "updateTicket", "deleteTicket")
    crt = _stueck(src, "createTicket", "updateTicket")
    js = PRELUDE + _helfer(src) + upd + "\n" + crt + "\n" + r"""
var R={};
function reset(){sq=[];pq=[];planData={tickets:[T]};}
// 1 Status
reset();updateTicket({...T,status:"erledigt"});R.status=sq[0].body;
// 1 Zuweisung
reset();updateTicket({...T,assignee:"m7"});R.assign=sq[0].body;
// 4 Schalter aus -> wie bisher
store={"epk_tk_diff_put":"0"};reset();var _u={...T,status:"erledigt"};updateTicket(_u);
R.ausGleich=JSON.stringify(sq[0].body)===JSON.stringify((function(_u){return __ALT__;})(planData.tickets[0]));
var e0;_tkFotoEintrag({name:"c.jpg",dataUrl:"data:image/jpeg;base64,CCC",takenAt:"t",width:9,height:9},e=>{e0=e;});
R.ausEintrag=e0;R.ausGleicheRef=(function(){var a=[{dataUrl:"x",thumb:""}];return _tkFotosAuslagern(a,"T1","P1")===a;})();
// 2 Storage an
store={"epk_tk_foto_storage":"1"};reset();
_tkFotoEintrag({name:"c.jpg",dataUrl:"data:image/jpeg;base64,NEU"+"B".repeat(50000),takenAt:"t",width:2400,height:1800},e=>{
  var _p={...T,photos:[...T.photos,e]};updateTicket(_p);
  R.fotoBody=sq[0].body;R.fotoPq=pq.map(x=>({storagePath:x.storagePath,nurStorage:x.nurStorage,lang:x.dataUrl.length}));
  R.lokal=planData.tickets[0].photos[2];
  // veralteter Zustand (Schnellblatt): dasselbe Eintrags-Objekt noch einmal, plus Statuswechsel
  sq=[];updateTicket({..._p,status:"in_bearbeitung"});R.stale={body:sq[0].body,pq:pq.length};
  // neues Ticket mit Foto
  sq=[];pq=[];newTicket={x:1,y:2,page:1,planId:"PL1",pid:"P1",type:"info",title:"Neu",description:"",status:"offen",priority:"mittel",assignee:"",layer:"l1",dueDate:"",photos:[e],comments:[]};
  createTicket();
  R.post=sq.filter(x=>x.method==="POST")[0].body;R.postPq=pq.map(x=>x.storagePath);
  // 3 Anzeige
  R.src={alt:_tkFotoSrc({dataUrl:"data:image/jpeg;base64,ALT"}),str:_tkFotoSrc("data:image/png;base64,S"),
    neu:_tkFotoSrc({path:"tickets/P1/T1/1_0.jpg",thumb:"data:image/jpeg;base64,TH"}),
    ohneThumb:_tkFotoSrc({path:"tickets/P1/T1/1_0.jpg",thumb:""})};
  process.stdout.write(JSON.stringify(R));
});
"""
    js = js.replace("__ALT__", ALT_BODY_JS)
    return json.loads(run_node_snippet(node_exe, js))


def _befunde(r):
    b = []
    for k in ("status", "assign"):
        t = json.dumps(r[k])
        if "photos" in r[k] or "data:" in t:
            b.append(k + "-PUT traegt Fotodaten")
    if set(r["status"]) != {"status", "status_history", "updated_at"}:
        b.append("Status-PUT: %s" % sorted(r["status"]))
    if set(r["assign"]) != {"assignee", "updated_at"}:
        b.append("Zuweisungs-PUT: %s" % sorted(r["assign"]))
    if not r["ausGleich"]:
        b.append("Schalter aus: Body nicht wie bisher")
    if r["ausEintrag"] != {"name": "c.jpg", "dataUrl": "data:image/jpeg;base64,CCC", "takenAt": "t"}:
        b.append("Schalter aus: Foto-Eintrag veraendert")
    if not r["ausGleicheRef"]:
        b.append("Schalter aus: Fotos werden trotzdem ausgelagert")
    neu = r["fotoBody"].get("photos", [None] * 3)[2] if r["fotoBody"].get("photos") else None
    if not neu or "dataUrl" in neu or not neu.get("path", "").startswith("tickets/P1/T1/") or not neu.get("thumb", "").startswith("data:image/jpeg"):
        b.append("neues Foto steht nicht als Verweis im PUT: %r" % (neu and {k: str(v)[:40] for k, v in neu.items()}))
    if neu and (neu.get("w"), neu.get("h")) != (2400, 1800):
        b.append("w/h fehlen")
    if len(r["fotoPq"]) != 1 or not r["fotoPq"][0]["nurStorage"] or r["fotoPq"][0]["lang"] < 50000 \
            or (neu and r["fotoPq"][0]["storagePath"] != neu.get("path")):
        b.append("PhotoQ bekommt das volle Bild nicht unter dem Ticket-Pfad: %r" % r["fotoPq"])
    if not r["lokal"] or "dataUrl" in r["lokal"]:
        b.append("lokaler Zustand haelt weiter Base64")
    if r["stale"]["pq"] != 1 or "photos" in r["stale"]["body"]:
        b.append("veralteter Zustand laedt erneut hoch / schickt Fotos: %r" % r["stale"])
    pf = r["post"].get("photos") or []
    if len(pf) != 1 or "dataUrl" in pf[0] or "data:image/jpeg;base64,NEU" in json.dumps(r["post"]) \
            or not pf[0].get("path", "").startswith("tickets/P1/NEU1/") or r["postPq"] != [pf[0].get("path")]:
        b.append("POST eines neuen Tickets traegt das Foto nicht als Verweis: %r" % r["postPq"])
    s = r["src"]
    if s["alt"] != "data:image/jpeg;base64,ALT" or s["str"] != "data:image/png;base64,S" \
            or s["neu"] != "data:image/jpeg;base64,TH" \
            or s["ohneThumb"] != "https://x.supabase.co/storage/v1/object/public/epkolar-files/tickets/P1/T1/1_0.jpg":
        b.append("Anzeige: %r" % s)
    return b


def test_fotos_raus_aus_dem_ticket_body(src, node_exe):
    assert _befunde(_probe(src, node_exe)) == []


@pytest.mark.parametrize("alt,neu", [
    ("body:_tkNurGeaendert(_old&&_tkB(_old),_tkB(_u))", "body:_tkB(_u)"),
    ("if(_c&&_c.tid===tid)return _c.v;", ""),
    ("if(_c&&_c.tid===tid)return _c.v;", "if(_c)return _c.v;"),
    ("if(ticket.photos)ticket.photos=_tkFotosAuslagern(ticket.photos,ticket.id,p.id);", ""),
    ("if(_phA!==_u.photos)_u={..._u,photos:_phA};", ""),
    ("if(k===\"updated_at\"||JSON.stringify(neuB[k])!==JSON.stringify(altB[k]))out[k]=neuB[k];", "out[k]=neuB[k];"),
    ("return f.dataUrl||f.thumb||_tkFotoUrl(f)||\"\";", "return f.dataUrl||\"\";"),
    ("if(!_tkFlag(\"epk_tk_foto_storage\",false)){cb(e);return;}", ""),
])
def test_umkehrprobe(src, node_exe, alt, neu):
    assert src.count(alt) == 1, "Anker fehlt: " + alt
    kaputt = src.replace(alt, neu, 1)
    try:
        befunde = _befunde(_probe(kaputt, node_exe))
    except Exception as ex:  # zurueckgebaut kann die Probe auch abstuerzen - das ist ebenfalls ein Anschlag
        befunde = [str(ex)[:200]]
    assert befunde, "Riegel blind fuer: " + alt


def test_storage_schalter_standard_aus(src):
    """Solange der Upload nach tickets/ nicht am Geraet geprueft ist, bleibt der Storage-Weg aus."""
    f = _extract_fn(src, "_tkFotoEintrag") + _extract_fn(src, "_tkFotosAuslagern")
    assert f.count('_tkFlag("epk_tk_foto_storage",false)') == 2
    assert '_tkFlag("epk_tk_diff_put",true)' in _extract_fn(src, "_tkNurGeaendert")


# ── 5 PhotoQ.flush ──────────────────────────────────────────────────────────
def _photoq(src):
    m = re.search(r"const PhotoQ=\{[\s\S]*?\n\};", src)
    assert m
    return m.group(0)


def _flush_probe(src, node_exe):
    js = r"""
var mem={photoQueue:[]};var ODB={load:async k=>JSON.parse(JSON.stringify(mem[k]||[])),save:async(k,v)=>{mem[k]=v;},set:async(k,_d,v)=>{mem[k]=v;}};
var navigator={onLine:true};var up=[],posts=[];
async function _sbUploadFile(path,d){up.push(path);return "https://x/storage/v1/object/public/epkolar-files/"+path;}
function _storagePath(c,pid,n){return "photos/"+pid+"/123_"+n;}
async function _sbPost(t,b){posts.push(b.entity_type);}function _mapBody(b){return b;}
""" + _photoq(src) + r"""
(async()=>{
 await PhotoQ.add({entityType:"ticket",entityId:"T1",projectId:"P1",name:"a.jpg",dataUrl:"data:image/jpeg;base64,AA",storagePath:"tickets/P1/T1/1_0.jpg",nurStorage:true});
 await PhotoQ.add({entityType:"defect",entityId:"D1",projectId:"P1",name:"b.jpg",dataUrl:"data:image/jpeg;base64,BB"});
 var r=await PhotoQ.flush();
 process.stdout.write(JSON.stringify({r,up,posts,rest:mem.photoQueue.length}));
})();
"""
    return json.loads(run_node_snippet(node_exe, js))


def _flush_befunde(r):
    b = []
    if r["up"] != ["tickets/P1/T1/1_0.jpg", "photos/P1/123_b.jpg"]:
        b.append("Upload-Pfade: %r" % r["up"])
    if r["posts"] != ["defect"]:
        b.append("photos-Zeilen: %r" % r["posts"])
    if r["r"] != {"ok": 2, "fail": 0} or r["rest"] != 0:
        b.append("Ergebnis: %r" % r)
    return b


def test_photoq_ticketpfad(src, node_exe):
    assert _flush_befunde(_flush_probe(src, node_exe)) == []


@pytest.mark.parametrize("alt,neu", [
    ("const storagePath=ph.storagePath||_storagePath(", "const storagePath=_storagePath("),
    ("if(!ph.nurStorage)/*", "if(true)/*"),
])
def test_photoq_umkehrprobe(src, node_exe, alt, neu):
    assert src.count(alt) == 1, alt
    assert _flush_befunde(_flush_probe(src.replace(alt, neu, 1), node_exe)), "Riegel blind fuer: " + alt
