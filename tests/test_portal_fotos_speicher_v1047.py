# -*- coding: utf-8 -*-
"""v3.9.1047 Kundenportal-Fotos in den Speicher (Dauerregel 18.11.2026: die Datenbank speichert nie Dateien).

Vorher (bis v1045): submitMangel schickte die Base64-Vorschauen als p_images an portal_submit_defect (-> defects.images
in der DB) und legte die grossen Fotos in die PhotoQ, die der anonyme Kunde nie hochladen konnte.
Jetzt: Foto -> Edge Function portal-foto (privater Bucket epkolar-docs) -> nur "sbpriv:epkolar-docs/portal/..." an die RPC.

Node fuehrt die ECHTEN Funktionen aus index.html aus (Attrappen an die echten Signaturen gebunden):
  * Upload-Kette _portalFotoCall/_portalFotoHoch/_portalMangelFotosHoch: richtiger Endpunkt, anon-Schluessel,
    Wiederholung bei Netzfehler mit GLEICHEM Schluessel, keine Wiederholung bei Ablehnung, schon Hochgeladenes nicht nochmal.
  * submitMangel (aus KundenPortal herausgeschnitten): RPC bekommt nur Speicher-Pfade, nie data:, nie PhotoQ;
    gescheitertes Foto -> Kunde entscheidet; RPC-Fehler -> Eingaben bleiben.
  * Buero-Anzeige: sbpriv:epkolar-docs/portal/... wird ueber _dateiSigniert -> _sbSignedDocUrl("portal/...") aufgeloest.
  * Edge Function (TypeScript, von Node 24 ohne Typen ausgefuehrt) gegen eine Speicher-Attrappe.
Umkehrproben: die alte Zeile zurueck -> der Befund muss rot werden.
"""
import io
import json
import re
import subprocess
from pathlib import Path

import pytest

from conftest import _extract_fn, run_node_snippet

WURZEL = Path(__file__).resolve().parents[1]
FN_TS = WURZEL / "supabase" / "functions" / "portal-foto" / "index.ts"
SQL = WURZEL / "sql" / "portal_submit_defect_keine_dateien_v1047.sql"
AUSSEN = Path("C:/repos/epk-portal-foto")


@pytest.fixture(scope="module")
def src():
    return io.open(str(WURZEL / "index.html"), encoding="utf-8", newline="").read()


def _fn(src, name):
    f = _extract_fn(src, name)
    assert f, "%s nicht gefunden - das ist rot, nicht gruen." % name
    if ("async " + f[:60]) in src:
        f = "async " + f
    return f


def _zwischen(text, anfang, ende):
    i = text.find(anfang)
    assert i >= 0, "Anker fehlt: %s" % anfang[:80]
    j = text.find(ende, i + len(anfang))
    assert j >= 0, "Ende fehlt: %s" % ende[:80]
    return text[i:j + len(ende)]


ECHT = ("_fT", "_netzUploadMsFuer", "_dateiBytes", "_netzBackoffMs", "_netzFehlerArt", "_netzNochmal",
        "_dateiQuelleSicher", "_dateiSigniert", "_optionalChain",
        "_portalFotoCall", "_portalFotoHoch", "_portalFotoGrund", "_portalMangelFotosHoch", "_portalFotoSignieren",
        "_mgPrivPfade", "_mgFotoAufloesen")

PRELUDE = r"""
var SUPABASE_URL="https://x.supabase.co",SUPABASE_KEY="ANONKEY",SB_DOCS_BUCKET="epkolar-docs",SB_BUCKET="epkolar-files",SB_FZ_BUCKET="epkolar-fahrzeuge",SB_GEF_BUCKET="epkolar-gefahrstoff";
var navigator={onLine:true};var window={};
var console={warn:()=>{},log:()=>{},error:()=>{}};
const CALLS=[];let PLAN=[];const SIGNIERT=[];
function _mkRes(status,body){return {ok:status>=200&&status<300,status:status,json:async()=>body};}
async function fetch(url,init){const b=init&&init.body?JSON.parse(init.body):null;CALLS.push({url:url,headers:(init&&init.headers)||{},body:b});const f=PLAN.shift();if(!f)throw new Error("kein Plan fuer "+url);return f(url,b);}
function _netzSchlaf(){return Promise.resolve();}
function _netzFehlerMerken(){}
function _netzOnline(){return true;}
const _NETZ={letzterOk:0};
async function _sbSignedDocUrl(path,sek){SIGNIERT.push(path);return SUPABASE_URL+"/storage/v1/object/sign/epkolar-docs/"+path+"?token=t";}
async function _sbSignedFzUrl(){return "";}async function _sbSignedGefUrl(){return "";}
const OK=(u,b)=>_mkRes(200,{path:"sbpriv:epkolar-docs/portal/P1/"+b.defect_id+"/"+b.name+".jpg",url:SUPABASE_URL+"/storage/v1/object/sign/epkolar-docs/portal/P1/"+b.defect_id+"/"+b.name+".jpg?token=t"});
const NETZ=()=>{throw new TypeError("Failed to fetch");};
const ZUGROSS=()=>_mkRes(413,{error:"too_large"});
const LIMIT=()=>_mkRes(429,{error:"limit_project"});
const F1={thumb:"data:image/jpeg;base64,/9j/T1",full:"data:image/jpeg;base64,/9j/FULL1"};
const F2={thumb:"data:image/jpeg;base64,/9j/T2",full:"data:image/jpeg;base64,/9j/FULL2"};
"""


def _bundle(src):
    k = re.search(r"^const _PORTAL_FOTO_FN=.*$", src, re.M)
    assert k, "_PORTAL_FOTO_FN fehlt"
    return k.group(0) + "\n" + "\n".join(_fn(src, n) for n in ECHT)


def _node(node_exe, body):
    return json.loads(run_node_snippet(node_exe, PRELUDE + body))


# ---------------------------------------------------------------- statisch: alter Weg ist weg, neuer da
def test_portal_submit_schickt_keine_vorschauen_mehr(src):
    sub = _zwischen(src, "  const submitMangel=async()=>{", "    }};")
    assert "p_images:JSON.stringify(thumbPhotos" not in src, "Base64-Vorschauen gehen wieder an die RPC."
    assert "thumbPhotos" not in sub and "PhotoQ." not in sub, "Portal-Submit benutzt wieder Vorschauen/PhotoQ."
    assert "p_images:JSON.stringify(fu.pfade)" in sub
    assert "_portalMangelFotosHoch(p.portalCode,mid,fotos)" in sub
    assert 'context:"Kunde-Mangelmeldung"' not in src
    assert 'const _PORTAL_FOTO_FN="/functions/v1/portal-foto";' in src


def test_buero_anzeige_loest_sbpriv_portal_auf(src):
    vm = _fn(src, "VMang")
    gp = _zwischen(vm, "const getPhotos=(m)=>{", "/* v3.9.274")
    assert "const all=_mgFotoAufloesen(local,mgSigniert);" in gp, "Buero zeigt sbpriv:-Pfade roh (kaputtes Bild)."
    eff = _zwischen(vm, "const _mgPrivOffen=_mgPrivPfade(ms)", "[_mgPrivOffen.join(\"|\")]);")
    assert "_dateiSigniert(v,3600)" in eff and "_dateiQuelleSicher(" in eff
    kp = _fn(src, "KundenPortal")
    assert "const all=_mgFotoAufloesen(local,portalFotoUrls);" in kp
    assert "_portalFotoSignieren(p.portalCode,_pfOffen)" in kp


# ---------------------------------------------------------------- Node: Upload-Kette
def test_upload_kette_endpunkt_schluessel_wiederholung(node_exe, src):
    r = _node(node_exe, _bundle(src) + r"""
(async()=>{const R={};
 PLAN=[OK,NETZ,OK];
 const a=await _portalMangelFotosHoch("ABC","m1",[{...F1,key:"m1_0_aaaaaa"},{...F2,key:"m1_1_bbbbbb"}]);
 R.a=a;R.calls=CALLS.map(c=>({url:c.url,auth:c.headers.Authorization,apikey:c.headers.apikey,name:c.body.name,did:c.body.defect_id,data:c.body.dataUrl,keys:Object.keys(c.body).sort()}));
 CALLS.length=0;PLAN=[ZUGROSS];
 R.gross=await _portalMangelFotosHoch("ABC","m1",[{...F1,key:"m1_0_cccccc"}]);R.grossCalls=CALLS.length;
 CALLS.length=0;PLAN=[LIMIT];
 R.lim=await _portalMangelFotosHoch("ABC","m1",[{...F1,key:"m1_0_dddddd"}]);R.limCalls=CALLS.length;
 CALLS.length=0;PLAN=[];
 R.schon=await _portalMangelFotosHoch("ABC","m1",[{...F1,key:"k",pfad:"sbpriv:epkolar-docs/portal/P1/m1/k.jpg"}]);R.schonCalls=CALLS.length;
 CALLS.length=0;PLAN=[NETZ,NETZ,NETZ];
 R.netz=await _portalMangelFotosHoch("ABC","m1",[{...F1,key:"m1_0_eeeeee"}]);R.netzCalls=CALLS.length;
 process.stdout.write(JSON.stringify(R));})();
""")
    a = r["a"]
    assert a["fehl"] == [] and len(a["pfade"]) == 2
    assert a["pfade"][0] == "sbpriv:epkolar-docs/portal/P1/m1/m1_0_aaaaaa.jpg"
    assert a["pfade"][1] == "sbpriv:epkolar-docs/portal/P1/m1/m1_1_bbbbbb.jpg"
    assert set(a["urls"]) == set(a["pfade"])
    assert len(r["calls"]) == 3, "Netzfehler beim 2. Foto wurde nicht wiederholt."
    for c in r["calls"]:
        assert c["url"] == "https://x.supabase.co/functions/v1/portal-foto"
        assert c["auth"] == "Bearer ANONKEY" and c["apikey"] == "ANONKEY"
        assert c["keys"] == ["code", "dataUrl", "defect_id", "name"]
        assert c["did"] == "m1"
    assert r["calls"][1]["name"] == r["calls"][2]["name"] == "m1_1_bbbbbb", "Wiederholung mit neuem Schluessel = Doppel-Objekt."
    assert r["calls"][0]["data"] == "data:image/jpeg;base64,/9j/FULL1", "Nicht das volle Foto hochgeladen."
    assert r["grossCalls"] == 1 and r["gross"]["fehl"] == [{"i": 0, "grund": "zu groß"}]
    assert r["limCalls"] == 1 and r["lim"]["fehl"][0]["grund"] == "Obergrenze erreicht"
    assert r["schonCalls"] == 0 and r["schon"]["pfade"] == ["sbpriv:epkolar-docs/portal/P1/m1/k.jpg"]
    assert r["netzCalls"] == 3 and r["netz"]["fehl"][0]["grund"] == "keine Verbindung"


def test_signieren_nur_eigene_speicheradressen(node_exe, src):
    r = _node(node_exe, _bundle(src) + r"""
(async()=>{const R={};
 const P="sbpriv:epkolar-docs/portal/P1/m1/k.jpg",Q="sbpriv:epkolar-docs/portal/P1/m1/b.jpg";
 PLAN=[NETZ,(u,b)=>{R.body=b;return _mkRes(200,{urls:{[P]:SUPABASE_URL+"/storage/v1/object/sign/epkolar-docs/portal/P1/m1/k.jpg?token=t",[Q]:"javascript:alert(1)"}});}];
 R.u=await _portalFotoSignieren("ABC",[P,Q,"data:image/png;base64,xx","sbpriv:epkolar-docs/docs/x.pdf"]);
 R.leer=await _portalFotoSignieren("ABC",[]);R.calls=CALLS.length;
 R.auf=_mgFotoAufloesen(["data:image/jpeg;base64,A",P,Q,"https://x.supabase.co/storage/v1/object/public/epkolar-files/a.jpg"],R.u);
 R.priv=_mgPrivPfade([{photos:[P,"data:x"]},{photos:JSON.stringify([Q,P])},{photos:null}]);
 process.stdout.write(JSON.stringify(R));})();
""")
    assert r["body"] == {"code": "ABC", "action": "sign", "paths": [
        "sbpriv:epkolar-docs/portal/P1/m1/k.jpg", "sbpriv:epkolar-docs/portal/P1/m1/b.jpg"]}
    assert list(r["u"]) == ["sbpriv:epkolar-docs/portal/P1/m1/k.jpg"], "Fremde/unsichere Adresse durchgelassen."
    assert r["leer"] == {} and r["calls"] == 2, "Signieren nach Netzfehler nicht wiederholt (oder leere Liste fragt an)."
    assert r["auf"] == ["data:image/jpeg;base64,A", "https://x.supabase.co/storage/v1/object/sign/epkolar-docs/portal/P1/m1/k.jpg?token=t",
                        "https://x.supabase.co/storage/v1/object/public/epkolar-files/a.jpg"]
    assert r["priv"] == ["sbpriv:epkolar-docs/portal/P1/m1/k.jpg", "sbpriv:epkolar-docs/portal/P1/m1/b.jpg"]


def test_buero_signiert_portal_pfad_im_docs_bucket(node_exe, src):
    r = _node(node_exe, _bundle(src) + r"""
(async()=>{const R={};R.u=await _dateiSigniert("sbpriv:epkolar-docs/portal/P1/m1/k.jpg",3600);R.s=SIGNIERT;R.q=_dateiQuelleSicher(R.u);
 process.stdout.write(JSON.stringify(R));})();
""")
    assert r["s"] == ["portal/P1/m1/k.jpg"]
    assert r["q"] == r["u"] and r["u"].startswith("https://x.supabase.co/storage/v1/object/sign/")


# ---------------------------------------------------------------- Node: submitMangel selbst
def _submit_src(src):
    kp = _fn(src, "KundenPortal")
    return _zwischen(kp, "  const submitMangel=async()=>{", "    }};")


SUBMIT_HARNESS = r"""
async function lauf(opts,SUBMIT){
  let submittingMangel=false;let newMangel=opts.nm;const st={rpc:[],toasts:[],confirm:[],urls:{},nmNull:false};
  const setSubmittingMangel=()=>{};
  const setNewMangel=(x)=>{newMangel=typeof x==="function"?x(newMangel):x;if(newMangel===null)st.nmNull=true;};
  const setPortalFotoUrls=(f)=>{st.urls=f(st.urls);};
  let forms={maengel:[]};const setForms=(f)=>{forms=f(forms);};
  const p={id:"P1",portalCode:"ABC123"};
  const uid=()=>"m1abcdefgh";const td2=()=>"2026-11-19";
  window.__toast=(t)=>st.toasts.push(t);
  const _confirmModal=async(msg,o)=>{st.confirm.push(msg);return opts.confirm;};
  const _portalRpcCall=async(name,body)=>{st.rpc.push({name:name,body:body});if(opts.rpcFail)throw new Error("HTTP400");return body.p_id;};
  const PhotoQ={add:()=>{throw new Error("PhotoQ im Portal")},flush:()=>{throw new Error("PhotoQ im Portal")}};
  eval(SUBMIT+";globalThis.__sm=submitMangel;");
  await globalThis.__sm();
  st.nm=newMangel;st.forms=forms;st.uploads=CALLS.filter(c=>c.url.indexOf("/functions/v1/portal-foto")>0).map(c=>c.body.name);CALLS.length=0;
  return st;
}
"""


def _submit_lauf(node_exe, src, submit):
    return _node(node_exe, _bundle(src) + SUBMIT_HARNESS + "const SUBMIT=" + json.dumps(submit) + r""";
(async()=>{const R={};
 const nm=()=>({name:"Steckdose Kueche",beschreibung:"lose",ort:"EG",photos:[{...F1},{...F2}]});
 PLAN=[OK,OK];R.ok=await lauf({nm:nm()},SUBMIT);
 PLAN=[OK,ZUGROSS];R.halb=await lauf({nm:nm(),confirm:false},SUBMIT);
 PLAN=[OK];R.nochmal=await lauf({nm:R.halb.nm,confirm:false},SUBMIT);
 PLAN=[OK,ZUGROSS];R.ohne=await lauf({nm:nm(),confirm:true},SUBMIT);
 PLAN=[OK,OK];R.rpcweg=await lauf({nm:nm(),rpcFail:true},SUBMIT);
 process.stdout.write(JSON.stringify(R));})();
""")


def test_submit_rpc_bekommt_nur_speicherpfade(node_exe, src):
    r = _submit_lauf(node_exe, src, _submit_src(src))
    ok = r["ok"]
    assert len(ok["rpc"]) == 1 and ok["rpc"][0]["name"] == "portal_submit_defect"
    b = ok["rpc"][0]["body"]
    imgs = json.loads(b["p_images"])
    assert "data:" not in b["p_images"], "Base64 an die RPC = Datei in der DB."
    assert len(imgs) == 2 and all(x.startswith("sbpriv:epkolar-docs/portal/P1/m1abcdefgh/") for x in imgs)
    assert b["p_id"] == "m1abcdefgh" and b["p_code"] == "ABC123"
    assert ok["nmNull"] is True and ok["forms"]["maengel"][0]["photos"] == imgs
    assert set(ok["urls"]) == set(imgs), "Frische Fotos ohne signierte Adresse = leere Kacheln im Portal."
    assert all(re.match(r"^[A-Za-z0-9_-]{8,64}$", k) for k in ok["uploads"]), ok["uploads"]


def test_submit_gescheitertes_foto_kunde_entscheidet(node_exe, src):
    r = _submit_lauf(node_exe, src, _submit_src(src))
    h = r["halb"]
    assert h["rpc"] == [], "Mangel trotz verlorenem Foto still gesendet."
    assert len(h["confirm"]) == 1 and "Foto 2 (zu groß)" in h["confirm"][0]
    assert h["nmNull"] is False and h["nm"]["_mid"] == "m1abcdefgh"
    assert h["nm"]["photos"][0]["pfad"].startswith("sbpriv:epkolar-docs/portal/P1/m1abcdefgh/")
    n = r["nochmal"]
    assert n["uploads"] == [h["nm"]["photos"][1]["key"]], "Erneuter Versuch laedt Foto 1 noch einmal hoch."
    assert len(json.loads(n["rpc"][0]["body"]["p_images"])) == 2
    o = r["ohne"]
    assert len(o["rpc"]) == 1 and len(json.loads(o["rpc"][0]["body"]["p_images"])) == 1
    w = r["rpcweg"]
    assert w["nmNull"] is False, "RPC gescheitert, Formular trotzdem geschlossen = Meldung verloren."
    assert any("Eingaben bleiben erhalten" in t for t in w["toasts"])


def test_umkehrprobe_alte_vorschauen_waeren_rot(node_exe, src):
    sub = _submit_src(src)
    mut = sub.replace("p_images:JSON.stringify(fu.pfade)", "p_images:JSON.stringify(fotos.map(ph=>ph.thumb))")
    assert mut != sub, "Mutation hat nicht gegriffen."
    r = _submit_lauf(node_exe, src, mut)
    assert "data:" in r["ok"]["rpc"][0]["body"]["p_images"], "Die Base64-Probe kann nicht anschlagen."


def test_umkehrprobe_photoq_waere_rot(node_exe, src):
    sub = _submit_src(src)
    mut = sub.replace("      const fu=await", "      PhotoQ.add({});const fu=await", 1)
    assert mut != sub
    r = _submit_lauf(node_exe, src, mut)
    assert r["ok"]["rpc"] == [] and r["ok"]["nmNull"] is False, "Die PhotoQ-Probe kann nicht anschlagen."


# ---------------------------------------------------------------- Edge Function in Node (Typen werden entfernt)
STUB_SB = r"""
export const ST={objs:{},uploads:[],signed:[]};
export function createClient(){
  return {
    from(t){const q={_f:{},select(){return q;},eq(k,v){q._f[k]=v;return q;},neq(){return q;},
      async limit(){return q._f.portal_code==="ABC123"?{data:[{id:"P1"}],error:null}:{data:[],error:null};}};return q;},
    storage:{from(b){return {
      async list(prefix){const pre=prefix+"/";const seen={};const out=[];
        for(const k of Object.keys(ST.objs)){if(k.indexOf(b+"/"+pre)!==0)continue;const rest=k.slice((b+"/"+pre).length);const i=rest.indexOf("/");
          if(i<0)out.push({name:rest,id:"x",created_at:ST.objs[k]});else if(!seen[rest.slice(0,i)]){seen[rest.slice(0,i)]=1;out.push({name:rest.slice(0,i),id:null});}}
        return {data:out,error:null};},
      async upload(path,bytes,o){ST.uploads.push({b:b,path:path,o:o,n:bytes.length});if(ST.objs[b+"/"+path])return {error:{statusCode:"409",message:"The resource already exists"}};ST.objs[b+"/"+path]=new Date().toISOString();return {error:null};},
      async createSignedUrl(path,s){ST.signed.push(path);return {data:{signedUrl:"https://x.supabase.co/storage/v1/object/sign/"+b+"/"+path+"?token=t&s="+s},error:null};},
      async createSignedUrls(paths,s){return {data:paths.map(p=>({path:p,error:null,signedUrl:"https://x.supabase.co/storage/v1/object/sign/"+b+"/"+p+"?token=t"})),error:null};}
    };}}
  };
}
"""

RUNNER = r"""
import {ST} from "./sb.mjs";
globalThis.Deno={env:{get:k=>({SUPABASE_URL:"https://x.supabase.co",SUPABASE_SERVICE_ROLE_KEY:"SERVICE"})[k]},serve:h=>{globalThis.H=h;}};
await import("./fn.ts");
const H=globalThis.H;
const ORG="https://epkolar.github.io";
async function call(body,method){const r=await H(new Request("https://x/functions/v1/portal-foto",{method:method||"POST",headers:{origin:ORG,"content-type":"application/json"},body:method==="OPTIONS"?undefined:JSON.stringify(body)}));let j=null;try{j=await r.json();}catch(e){}return {s:r.status,j:j,o:r.headers.get("access-control-allow-origin")};}
const b64=a=>Buffer.from(Uint8Array.from(a)).toString("base64");
const JPG="data:image/jpeg;base64,"+b64([0xff,0xd8,0xff,0xe0,1,2,3,4,5,6]);
const PNGALS=JPG.replace("image/jpeg","image/png");
const R={};
R.opt=await call(null,"OPTIONS");
R.code=await call({code:"FALSCH",defect_id:"m1",name:"m1_0_aaaaaa",dataUrl:JPG});
R.ok=await call({code:" ABC123 ",defect_id:"m1",name:"m1_0_aaaaaa",dataUrl:JPG});
R.upl=ST.uploads.slice();
R.wieder=await call({code:"ABC123",defect_id:"m1",name:"m1_0_aaaaaa",dataUrl:JPG});R.uplNach=ST.uploads.length;
R.magic=await call({code:"ABC123",defect_id:"m1",name:"m1_0_bbbbbb",dataUrl:PNGALS});
R.gif=await call({code:"ABC123",defect_id:"m1",name:"m1_0_cccccc",dataUrl:"data:image/gif;base64,R0lGODlh"});
R.html=await call({code:"ABC123",defect_id:"m1",name:"m1_0_cccccc",dataUrl:"data:text/html;base64,PGI+"});
R.trav=await call({code:"ABC123",defect_id:"../x",name:"m1_0_dddddd",dataUrl:JPG});
R.gross=await call({code:"ABC123",defect_id:"m1",name:"m1_0_eeeeee",dataUrl:"data:image/jpeg;base64,"+Buffer.alloc(4*1024*1024+10,0xff).toString("base64")});
for(let i=0;i<9;i++)ST.objs["epkolar-docs/portal/P1/m2/f"+i+".jpg"]=new Date().toISOString();
ST.objs["epkolar-docs/portal/P1/m2/f9.jpg"]=new Date().toISOString();
R.limD=await call({code:"ABC123",defect_id:"m2",name:"m2_0_ffffff",dataUrl:JPG});
for(let d=0;d<6;d++)for(let i=0;i<10;i++)ST.objs["epkolar-docs/portal/P1/q"+d+"/f"+i+".jpg"]=new Date().toISOString();
R.limP=await call({code:"ABC123",defect_id:"m3",name:"m3_0_gggggg",dataUrl:JPG});
for(const k of Object.keys(ST.objs))if(k.indexOf("/q")>0)ST.objs[k]=new Date(Date.now()-25*3600*1000).toISOString();
R.altZaehltNicht=await call({code:"ABC123",defect_id:"m3",name:"m3_0_hhhhhh",dataUrl:JPG});
R.sign=await call({code:"ABC123",action:"sign",paths:["sbpriv:epkolar-docs/portal/P1/m1/m1_0_aaaaaa.jpg","sbpriv:epkolar-docs/portal/P2/m1/x.jpg","portal/P1/../P2/m1/x.jpg","sbpriv:epkolar-docs/docs/a/b.pdf"]});
R.sign51=await call({code:"ABC123",action:"sign",paths:Array(51).fill("portal/P1/m1/a.jpg")});
R.signCode=await call({code:"NEIN",action:"sign",paths:["portal/P1/m1/a.jpg"]});
process.stdout.write(JSON.stringify(R));
"""


def test_edge_function_verhalten(node_exe, tmp_path):
    ts = FN_TS.read_text(encoding="utf-8")
    imp = 'import { createClient } from "npm:@supabase/supabase-js@2";'
    assert ts.count(imp) == 1
    (tmp_path / "fn.ts").write_text(ts.replace(imp, 'import { createClient } from "./sb.mjs";'), encoding="utf-8")
    (tmp_path / "sb.mjs").write_text(STUB_SB, encoding="utf-8")
    (tmp_path / "run.mjs").write_text(RUNNER, encoding="utf-8")
    p = subprocess.run([node_exe, "run.mjs"], cwd=str(tmp_path), capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert p.returncode == 0, p.stderr
    r = json.loads(p.stdout)
    assert r["opt"]["s"] == 200 and r["opt"]["o"] == "https://epkolar.github.io"
    assert r["code"]["s"] == 403 and r["code"]["j"] == {"error": "invalid_code"}
    assert r["ok"]["s"] == 200 and r["ok"]["j"]["path"] == "sbpriv:epkolar-docs/portal/P1/m1/m1_0_aaaaaa.jpg"
    assert r["ok"]["j"]["url"].startswith("https://x.supabase.co/storage/v1/object/sign/epkolar-docs/portal/P1/m1/")
    assert r["ok"]["j"]["url"].endswith("&s=604800"), "Signierte Adresse nicht 7 Tage."
    u = r["upl"][0]
    assert u["b"] == "epkolar-docs" and u["path"] == "portal/P1/m1/m1_0_aaaaaa.jpg" and u["o"]["upsert"] is False
    assert u["o"]["contentType"] == "image/jpeg"
    assert r["wieder"]["s"] == 200 and r["uplNach"] == 1, "Wiederholung legte ein zweites Objekt an."
    assert r["magic"]["s"] == 400 and r["magic"]["j"]["error"] == "bad_image"
    assert r["gif"]["s"] == 415 and r["html"]["s"] == 415
    assert r["trav"]["s"] == 400 and r["trav"]["j"]["error"] == "invalid_defect"
    assert r["gross"]["s"] == 413
    assert r["limD"]["s"] == 429 and r["limD"]["j"]["error"] == "limit_defect"
    assert r["limP"]["s"] == 429 and r["limP"]["j"]["error"] == "limit_project"
    assert r["altZaehltNicht"]["s"] == 200, "Objekte aelter als 24 h zaehlen faelschlich."
    assert list(r["sign"]["j"]["urls"]) == ["sbpriv:epkolar-docs/portal/P1/m1/m1_0_aaaaaa.jpg"], "Fremdes Projekt signiert."
    assert r["sign51"]["s"] == 400 and r["signCode"]["s"] == 403
    assert "SERVICE" not in json.dumps(r), "Schluessel in einer Antwort."


def test_edge_function_quelle_konstanten():
    ts = FN_TS.read_text(encoding="utf-8")
    for s in ('const BUCKET = "epkolar-docs";', "const MAX_BYTES = 4 * 1024 * 1024;", "const MAX_PER_DEFECT = 10;",
              "const MAX_PER_PROJECT_24H = 60;", "const MAX_SIGN_PATHS = 50;", "const SIGN_SECONDS = 7 * 24 * 3600;",
              'const ALLOWED_ORIGINS = ["https://epkolar.github.io"];', "upsert: false",
              'Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")', "Deno.serve("):
        assert s in ts, s
    # der Service-Schluessel wird nur gelesen, an createClient gegeben und auf Vorhandensein geprueft - nie ausgegeben
    assert ts.count("SERVICE_KEY") == 3 and ts.count("console.error(") == 2


def test_aussen_kopien_gleich():
    """Die Abgabe liegt auch unter C:/repos/epk-portal-foto (fuer den Lead); beide muessen gleich sein."""
    if not AUSSEN.is_dir():
        pytest.skip("Aussen-Ordner nicht auf diesem Rechner")
    assert (AUSSEN / "portal-foto" / "index.ts").read_bytes() == FN_TS.read_bytes()
    assert (AUSSEN / "portal_submit_defect_keine_dateien.sql").read_bytes() == SQL.read_bytes()


# ---------------------------------------------------------------- SQL-Entwurf statisch
def test_sql_entwurf():
    q = SQL.read_text(encoding="utf-8")
    code = "\n".join(l for l in q.splitlines() if not l.lstrip().startswith("--"))
    assert "CREATE OR REPLACE FUNCTION public.portal_submit_defect(\n  p_code text, p_id text, p_title text, p_description text, p_ort text, p_images text\n) RETURNS text" in code
    assert "SECURITY DEFINER SET search_path TO 'public', 'pg_temp'" in code
    assert "RAISE EXCEPTION 'files_not_allowed'" in code
    assert "position('data:' in" in code and "position(';base64,' in" in code
    assert "'sbpriv:epkolar-docs/portal/' || v_pid || '/' || v_id || '/'" in code
    assert "starts_with(v_s, v_prefix)" in code and "length(v_s) > 300" in code and "jsonb_array_length(v_imgs) > 10" in code
    assert code.count("RAISE EXCEPTION 'invalid_images'") >= 3
    assert "GRANT EXECUTE ON FUNCTION public.portal_submit_defect(text,text,text,text,text,text) TO anon, authenticated;" in code
    for k in ("invalid_portal_code", "title_too_short", "text_too_long", "'Kunde', 'gemeldet', 'offen', 'normal', 'Kunde'"):
        assert k in code, k
    assert "-- BEGIN;" in q and "-- ROLLBACK;" in q and "files_not_allowed" in q.split("PROBE", 1)[1]
    # Client und Function liefern genau den Praefix, den die RPC verlangt
    ts = FN_TS.read_text(encoding="utf-8")
    assert 'const REF_PREFIX = "sbpriv:" + BUCKET + "/";' in ts and '"portal/" + pid + "/" + did' in ts
