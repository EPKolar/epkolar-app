# -*- coding: utf-8 -*-
"""v3.9.1056 Auth-Haertung (Pruefbericht C:/repos/epk-auth-pruefung-2026-11-19.md, Funde 2-16).

Node fuehrt die ECHTEN Funktionen aus index.html gegen einen falschen Server aus:
  * API.login (+ das echte _sbAuthLogin): eine neutrale Meldung fuer unbekannt / gesperrt / falsches Passwort,
    429 und unbestaetigte E-Mail mit eigenem Text, Netzfehler gehen als TypeError nach oben (Offline-Weg),
    Profil ueber auth_user_id, gesperrtes/fehlendes Profil beendet die Sitzung, kein Benutzername/keine E-Mail im Protokoll.
  * API.changePassword: altes Passwort gegen GoTrue, nur GoTrue wird gesetzt, users wird nie angefasst.
  * _passwortHilfeAnfragen: Erfolg nur bei ok:true, 404 ehrlich, immer anon-Schluessel.
  * _sqKennwortPurge: Kennwort-Felder raus aus syncQueue/syncQueueFailed, Benutzer-Anlage bleibt, kein Wert im Protokoll.
  * _profGesperrt, _sbSelFuer.
Dazu statische Riegel fuer Abmelden (scope=local), PwInput, Anmeldemaske, Warteschlangen-Besitzer, Mindestlaenge,
und fuer die SQL-Entwuerfe sql/AUTH_HAERTUNG_1..5. Jeder Riegel hat eine Umkehrprobe: Mangel zurueck -> Riegel schlaegt an.
"""
import json
import os
import re
import subprocess

import pytest

from _hilfen import funktion, nur_code
from conftest import EPK_TEST_TIMEOUT

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
SQL_DIR = os.path.join(WURZEL, "sql")
SQL_NAMEN = ["AUTH_HAERTUNG_1_users_v1056", "AUTH_HAERTUNG_2_gesperrt_v1056", "AUTH_HAERTUNG_3_waisen_v1056",
             "AUTH_HAERTUNG_4_policies_v1056", "AUTH_HAERTUNG_5_passwort_hilfe_v1056"]
NEUTRAL = "Anmeldung fehlgeschlagen – Benutzername oder Passwort prüfen"
GEHEIM = "Geheim-4711-xyz"


def _fn(src, name):
    """Funktion woertlich - mit "async", falls sie so deklariert ist (sonst waere await ein Syntaxfehler)."""
    f = funktion(src, name)
    i = src.find(f)
    return ("async " + f) if src[max(0, i - 6):i] == "async " else f


def _teil(src, start, ende):
    i = src.index(start)
    j = src.index(ende, i)
    return src[i:j]


def _node(node_exe, tmp_path, code, name="t.js"):
    p = tmp_path / name
    p.write_text(code, encoding="utf-8")
    r = subprocess.run([node_exe, str(p)], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout)


# ───────────────────────────────────────────────────────────── Node: API.login
LOGIN_PRELUDE = r"""
var logs=[];var console={log:function(){logs.push([].slice.call(arguments).map(function(x){return typeof x==="string"?x:JSON.stringify(x);}).join(" "));}};
console.warn=console.log;console.error=console.log;
var SB_REST="https://x/rest/v1";var SUPABASE_KEY="ANONKEY";var _SB_AUTH="https://x/auth/v1";
var _authToken=null;var _user=null;var localStorage={setItem:function(){},getItem:function(){return null;}};
function _fT(i){return i;}
function _safeJsonParse(t,d){try{return JSON.parse(t);}catch(e){return d;}}
function _storeAuth(d){_authToken=d.access_token;}
var logoutCalls=0;async function _sbAuthLogout(){logoutCalls++;_authToken=null;}
var patches=[];function _sbPatch(t,id,d){patches.push([t,id,d]);return Promise.resolve([]);}
function _sbPost(){return Promise.resolve({});}
var M={};var filters=[];var calls=[];
function antwort(status,body){return {ok:status>=200&&status<300,status:status,json:async function(){return body;},text:async function(){return JSON.stringify(body);}};}
async function fetch(url,init){
  calls.push(url);
  if(url.indexOf("/rpc/login_lookup")>=0)return antwort(200,M.lookup);
  if(url.indexOf("/token?grant_type=password")>=0){
    if(M.netz){throw new TypeError("Failed to fetch");}
    if(M.gt===200)return antwort(200,{access_token:"aaaa.bbbb.cccccccccccccccccccc",refresh_token:"r",expires_in:3600,user:{id:"AUID-1"}});
    return antwort(M.gt,{error_code:M.code||"invalid_credentials",msg:"x"});
  }
  return antwort(404,{});
}
async function _sbGetUsersSafe(f){filters.push(f);
  if(f.indexOf("auth_user_id=eq.")===0)return M.profAuth?[M.profAuth]:[];
  if(f.indexOf("id=eq.")===0)return M.profId?[M.profId]:[];
  return [];}
function neu(m){M=m;filters=[];calls=[];logoutCalls=0;patches=[];_authToken=null;}
"""

LOGIN_KOERPER = r"""
(async()=>{
 const R={};
 async function lauf(name,m){neu(m);try{const d=await API_T.login(" barger ".trim(),"__PW__");R[name]={ok:true,user:d.user,filters:filters,logout:logoutCalls,patches:patches};}
   catch(e){R[name]={ok:false,msg:String(e&&e.message),name:e&&e.name,filters:filters,logout:logoutCalls,calls:calls};}}
 const AKTIV={id:"U1",username:"barger",name:"Barger",email:"barger@ep-kolar.at",role:"monteur",active:1,locked:0,deactivate_at:null,permissions:"[]",login_count:3};
 await lauf("unbekannt",{lookup:null,gt:200});
 await lauf("falschesPw",{lookup:{email:"barger@ep-kolar.at"},gt:400});
 await lauf("gesperrtAlt",{lookup:{id:"U1",email:"barger@ep-kolar.at",locked:true},gt:200});
 await lauf("ohneMail",{lookup:{email:""},gt:200});
 await lauf("rate",{lookup:{email:"barger@ep-kolar.at"},gt:429,code:"over_request_rate_limit"});
 await lauf("unbestaetigt",{lookup:{email:"barger@ep-kolar.at"},gt:400,code:"email_not_confirmed"});
 await lauf("server",{lookup:{email:"barger@ep-kolar.at"},gt:503});
 await lauf("netz",{lookup:{email:"barger@ep-kolar.at"},netz:true});
 await lauf("gut",{lookup:{email:"barger@ep-kolar.at"},gt:200,profAuth:AKTIV});
 await lauf("profilGesperrt",{lookup:{email:"barger@ep-kolar.at"},gt:200,profAuth:Object.assign({},AKTIV,{locked:1})});
 await lauf("profilAusgeschieden",{lookup:{email:"barger@ep-kolar.at"},gt:200,profAuth:Object.assign({},AKTIV,{deactivate_at:"2000-01-01"})});
 await lauf("keinProfil",{lookup:{email:"barger@ep-kolar.at"},gt:200});
 await lauf("alterServer",{lookup:{id:"U1",email:"barger@ep-kolar.at"},gt:200,profId:AKTIV});
 R.logs=logs;
 process.stdout.write(JSON.stringify(R));
})().catch(e=>{process.stderr.write(String(e&&e.stack||e));process.exit(1);});
"""


def _login_quelle(src):
    login = _teil(src, "    login: async function(u, p) {", "\n    me: async function()")
    return (_fn(src, "_sbAuthLogin") + "\n" + _fn(src, "_profGesperrt") + "\nvar API_T={\n" + login + "\n};\n")


def _login_lauf(node_exe, tmp_path, src):
    return _node(node_exe, tmp_path, LOGIN_PRELUDE + _login_quelle(src) + LOGIN_KOERPER.replace("__PW__", GEHEIM), "login.js")


def _login_mangel(R):
    m = []
    for fall in ("unbekannt", "falschesPw", "gesperrtAlt", "ohneMail", "profilGesperrt", "profilAusgeschieden", "keinProfil"):
        if R[fall]["ok"] or not R[fall]["msg"].startswith(NEUTRAL):
            m.append("%s: keine neutrale Meldung (%r)" % (fall, R[fall].get("msg")))
    if "Zu viele Versuche" not in R["rate"].get("msg", ""):
        m.append("429 ohne eigenen Text: %r" % R["rate"].get("msg"))
    if "nicht freigeschaltet" not in R["unbestaetigt"].get("msg", ""):
        m.append("email_not_confirmed ohne eigenen Text")
    if "nicht erreichbar" not in R["server"].get("msg", ""):
        m.append("5xx ohne eigenen Text")
    if R["netz"].get("name") != "TypeError":
        m.append("Netzfehler kommt nicht als TypeError an (Offline-Weg tot): %r" % R["netz"])
    g = R["gut"]
    if not g["ok"] or g["user"]["id"] != "U1" or g["filters"][:1] != ["auth_user_id=eq.AUID-1"]:
        m.append("Erfolg/Profil ueber auth_user_id kaputt: %r" % g)
    if g.get("patches") and g["patches"][0][1] != "U1":
        m.append("login_count auf falsche id")
    for fall in ("profilGesperrt", "profilAusgeschieden", "keinProfil"):
        if R[fall].get("logout") != 1:
            m.append("%s: Sitzung nicht beendet" % fall)
    a = R["alterServer"]
    if not a["ok"] or "id=eq.U1" not in a["filters"]:
        m.append("alte login_lookup-Fassung (mit id) geht nicht mehr: %r" % a)
    alles = "\n".join(R["logs"])
    for verboten in ("barger@", "barger", GEHEIM):
        if verboten in alles:
            m.append("Protokoll enthaelt %r" % verboten)
    return m


def test_login_neutral_ehrlich_und_ohne_pii_im_protokoll(node_exe, tmp_path, index_html):
    R = _login_lauf(node_exe, tmp_path, index_html)
    assert _login_mangel(R) == []


def test_umkehrprobe_login_aufzaehlung(node_exe, tmp_path, index_html):
    kaputt = index_html.replace('throw new Error(_neutral+" [B20-D]");', 'throw new Error("Falsches Passwort [B20-D]");', 1)
    assert kaputt != index_html
    R = _login_lauf(node_exe, tmp_path, kaputt)
    assert any(x.startswith("falschesPw") for x in _login_mangel(R))


def test_umkehrprobe_login_protokoll(node_exe, tmp_path, index_html):
    kaputt = index_html.replace("console.error('[B020-D] GoTrue-Anmeldung abgelehnt',{status:_st,code:_code});",
                                "console.error('[B020-D] GoTrue-Anmeldung abgelehnt',{status:_st,code:_code,username:u,email});", 1)
    assert kaputt != index_html
    R = _login_lauf(node_exe, tmp_path, kaputt)
    assert any("Protokoll enthaelt" in x for x in _login_mangel(R))


# ───────────────────────────────────────────────────────────── Node: changePassword
PW_PRELUDE = r"""
var logs=[];var console={log:function(){logs.push([].slice.call(arguments).join(" "));}};console.warn=console.log;console.error=console.log;
var SB_REST="https://x/rest/v1";var SUPABASE_KEY="ANONKEY";var _SB_AUTH="https://x/auth/v1";
var navigator={onLine:true};var PW_MIN_LEN=8;
var _authToken="alt1.alt2.altaltaltaltaltaltalt";var _user={id:"U1",username:"barger",email:"barger@ep-kolar.at"};
function _fT(i){return i;}function _isJwtShape(t){return typeof t==='string'&&t.split('.').length===3&&t.length>20;}
function _safeJsonParse(t,d){try{return JSON.parse(t);}catch(e){return d;}}
function _storeAuth(d){_authToken=d.access_token;}
var patched=0;function _sbPatch(){patched++;return Promise.resolve([]);}function _sbGet(){patched++;return Promise.resolve([]);}
var offline=null;var ODB={set:async function(s,k,v){if(k==="offlinePwHash")offline=v;}};
var _OFFPW={create:async function(u,p){return {u:u,h:"H"};}};
var M={};var calls=[];
function antwort(status,body){return {ok:status>=200&&status<300,status:status,json:async function(){return body;},text:async function(){return JSON.stringify(body);}};}
async function fetch(url,init){
  calls.push({url:url,method:init&&init.method,auth:init&&init.headers&&init.headers.Authorization});
  if(url.indexOf("/token?grant_type=password")>=0){const b=JSON.parse(init.body);
    if(b.password!==M.altPw)return antwort(400,{error_code:"invalid_credentials"});
    return antwort(200,{access_token:"neu1.neu2.neuneuneuneuneuneuneu",refresh_token:"r",expires_in:3600,user:{id:"AUID-1"}});}
  if(url.indexOf("/logout")>=0)return antwort(204,{});
  if(url.indexOf("/user")>=0)return M.put===200?antwort(200,{}):antwort(M.put,{error_code:M.code||"weak_password"});
  return antwort(404,{});
}
function neu(m){M=m;calls=[];patched=0;offline=null;_authToken="alt1.alt2.altaltaltaltaltaltalt";}
"""

PW_KOERPER = r"""
(async()=>{
 const R={};
 async function lauf(name,m,alt,neuPw){neu(m);try{const r=await API_T.changePassword(alt,neuPw);R[name]={ok:true,r:r,calls:calls,patched:patched,offline:offline,token:_authToken};}
   catch(e){R[name]={ok:false,msg:String(e&&e.message),calls:calls,patched:patched,offline:offline};}}
 await lauf("kurz",{altPw:"altesPasswort",put:200},"altesPasswort","kurz12");
 await lauf("altFalsch",{altPw:"altesPasswort",put:200},"falsch","__NEU__");
 await lauf("gut",{altPw:"altesPasswort",put:200},"altesPasswort","__NEU__");
 await lauf("schwach",{altPw:"altesPasswort",put:422,code:"weak_password"},"altesPasswort","__NEU__");
 R.logs=logs;
 process.stdout.write(JSON.stringify(R));
})().catch(e=>{process.stderr.write(String(e&&e.stack||e));process.exit(1);});
"""


def _pw_lauf(node_exe, tmp_path, src):
    teil = _teil(src, "    changePassword: async function(oldPw, newPw) {", "\n    // Data access (read-only")
    code = PW_PRELUDE + _fn(src, "_sbAuthLogin") + "\nvar API_T={\n" + teil + "\n};\n" + PW_KOERPER.replace("__NEU__", GEHEIM)
    return _node(node_exe, tmp_path, code, "pw.js")


def _pw_mangel(R):
    m = []
    if R["kurz"]["ok"] or R["kurz"]["calls"]:
        m.append("zu kurzes Passwort nicht vor jedem Aufruf abgewiesen")
    a = R["altFalsch"]
    if a["ok"] or "Altes Passwort stimmt nicht" not in a["msg"] or any(c["url"].endswith("/user") for c in a["calls"]):
        m.append("falsches altes Passwort wird nicht gegen GoTrue abgewiesen: %r" % a)
    g = R["gut"]
    puts = [c for c in g.get("calls", []) if c["url"].endswith("/user") and c["method"] == "PUT"]
    if not g["ok"] or g["r"].get("gotrue") is not True or len(puts) != 1 or puts[0]["auth"] != "Bearer neu1.neu2.neuneuneuneuneuneuneu":
        m.append("Aendern ueber GoTrue mit frischer Sitzung kaputt: %r" % g)
    if not any(c["url"].endswith("/logout?scope=local") and c["auth"] == "Bearer alt1.alt2.altaltaltaltaltaltalt" for c in g.get("calls", [])):
        m.append("vorige Sitzung dieses Geraets nicht beendet")
    if g.get("offline") is None:
        m.append("Offline-Ablage nicht auf das neue Passwort umgestellt")
    for fall in ("kurz", "altFalsch", "gut", "schwach"):
        if R[fall]["patched"]:
            m.append("%s: users wurde gelesen/geschrieben (password_hash)" % fall)
    s = R["schwach"]
    if s["ok"] or "HTTP422" not in s["msg"]:
        m.append("abgelehntes neues Passwort nicht ehrlich gemeldet: %r" % s)
    if GEHEIM in "\n".join(R["logs"]):
        m.append("Passwort im Protokoll")
    return m


def test_passwort_aendern_ueber_gotrue(node_exe, tmp_path, index_html):
    assert _pw_mangel(_pw_lauf(node_exe, tmp_path, index_html)) == []


def test_umkehrprobe_passwort_aendern_ohne_altpruefung(node_exe, tmp_path, index_html):
    kaputt = index_html.replace("try{_neu=await _sbAuthLogin(_mail,oldPw);}catch(e){",
                                'try{_neu={access_token:"neu1.neu2.neuneuneuneuneuneuneu"};}catch(e){', 1)
    assert kaputt != index_html
    assert any("falsches altes Passwort" in x for x in _pw_mangel(_pw_lauf(node_exe, tmp_path, kaputt)))


# ───────────────────────────────────────────────────────────── Node: Passwort-Hilfe
HILFE_KOERPER = r"""
var SB_REST="https://x/rest/v1";var SUPABASE_KEY="ANONKEY";var _authToken="USERTOKEN";
function _fT(i){return i;}
var M={};var heads=[];
async function fetch(url,init){heads.push(init.headers);if(M.netz)throw new TypeError("Failed to fetch");
  return {ok:M.st>=200&&M.st<300,status:M.st,json:async function(){if(M.kaputt)throw new Error("x");return M.body;}};}
(async()=>{const R={};
 for(const [n,m] of [["ok",{st:200,body:{ok:true}}],["leerBody",{st:200,body:{}}],["falsch",{st:200,body:{ok:false}}],
                     ["fehlt",{st:404,body:{}}],["server",{st:500,body:{}}],["netz",{netz:true}],["kaputt",{st:200,kaputt:true}]]){
   M=m;R[n]=await _passwortHilfeAnfragen("barger");}
 M={st:200,body:{ok:true}};R.leer=await _passwortHilfeAnfragen("   ");
 R.heads=heads;process.stdout.write(JSON.stringify(R));})().catch(e=>{process.stderr.write(String(e&&e.stack||e));process.exit(1);});
"""


def _hilfe_mangel(R):
    m = []
    if R["ok"].get("ok") != 1:
        m.append("ok:true wird nicht als Erfolg erkannt")
    for n in ("leerBody", "falsch", "server", "netz", "kaputt", "leer", "fehlt"):
        if R[n].get("ok"):
            m.append("%s gilt als gesendet" % n)
    if R["fehlt"].get("grund") != "fehlt" or R["netz"].get("grund") != "netz":
        m.append("404/Netz nicht unterschieden")
    for h in R["heads"]:
        if "USERTOKEN" in json.dumps(h) or h.get("apikey") != "ANONKEY":
            m.append("nicht mit dem anon-Schluessel gerufen")
            break
    return m


def _hilfe_lauf(node_exe, tmp_path, src):
    return _node(node_exe, tmp_path, _fn(src, "_passwortHilfeAnfragen") + "\n" + HILFE_KOERPER, "hilfe.js")


def test_passwort_hilfe_nur_bei_ok_true(node_exe, tmp_path, index_html):
    assert _hilfe_mangel(_hilfe_lauf(node_exe, tmp_path, index_html)) == []


def test_umkehrprobe_passwort_hilfe_falschgruen(node_exe, tmp_path, index_html):
    kaputt = index_html.replace('return (j&&j.ok===true)?{ok:1}:{ok:0,grund:"antwort"};', "return {ok:1};", 1)
    assert kaputt != index_html
    assert _hilfe_mangel(_hilfe_lauf(node_exe, tmp_path, kaputt))


# ───────────────────────────────────────────────────────────── Node: Warteschlangen-Bereinigung
PURGE_KOERPER = r"""
var logs=[];var console={log:function(){logs.push([].slice.call(arguments).join(" "));}};console.warn=console.log;console.error=console.log;
var STORE={
 syncQueue:[
  {id:"a",url:"/api/users",method:"POST",body:{id:"N1",username:"neu",password:"__G__",name:"Neu",email:"n@x.at"}},
  {id:"b",url:"/api/users/N2",method:"PUT",body:{password:"__G__"}},
  {id:"c",url:"/api/projects/P1",method:"PUT",body:{name:"Bau"}},
  {id:"d",url:"/api/x",method:"POST",body:JSON.stringify({new_password:"__G__",note:"n"})}],
 syncQueueFailed:[{id:"e",url:"/api/users/N3",method:"PUT",body:{id:"N3",p_password:"__G__"},failedAt:"t"}]};
var ODB={load:async function(s){return STORE[s];},set:async function(s,k,v){STORE[s]=v;}};
var SQ={_serial:function(fn){return fn();}};
(async()=>{const n=await _sqKennwortPurge();
 process.stdout.write(JSON.stringify({n:n,store:STORE,logs:logs}));})().catch(e=>{process.stderr.write(String(e&&e.stack||e));process.exit(1);});
"""


def _purge_lauf(node_exe, tmp_path, src):
    felder = re.search(r"const _PW_FELDER=\[[^\]]*\];", src).group(0)
    return _node(node_exe, tmp_path, felder + "\n" + _fn(src, "_sqKennwortPurge") + "\n" + PURGE_KOERPER.replace("__G__", GEHEIM), "purge.js")


def _purge_mangel(R):
    m = []
    roh = json.dumps(R["store"])
    if GEHEIM in roh:
        m.append("Kennwort steht noch in der Warteschlange")
    ids = [x["id"] for x in R["store"]["syncQueue"]]
    if ids != ["a", "c", "d"]:
        m.append("falsche Eintraege entfernt/behalten: %r" % ids)
    a = R["store"]["syncQueue"][0] if R["store"]["syncQueue"] else {}
    if a.get("body", {}).get("username") != "neu":
        m.append("Benutzer-Anlage ging verloren")
    if R["store"]["syncQueueFailed"] and "p_password" in json.dumps(R["store"]["syncQueueFailed"]):
        m.append("syncQueueFailed nicht bereinigt")
    if GEHEIM in "\n".join(R["logs"]):
        m.append("Kennwort im Protokoll")
    return m


def test_warteschlange_ohne_klartext_kennwort(node_exe, tmp_path, index_html):
    assert _purge_mangel(_purge_lauf(node_exe, tmp_path, index_html)) == []


def test_umkehrprobe_warteschlange(node_exe, tmp_path, index_html):
    kaputt = index_html.replace("const nb={...b};_PW_FELDER.forEach(k=>{delete nb[k];});n++;", "const nb={...b};n++;", 1)
    assert kaputt != index_html
    assert _purge_mangel(_purge_lauf(node_exe, tmp_path, kaputt))


# ───────────────────────────────────────────────────────────── Node: _profGesperrt / _sbSelFuer
def test_profil_gesperrt_regel_und_spaltenliste(node_exe, tmp_path, index_html):
    cols = re.search(r'const _USER_SAFE_COLS="[^"]*";', index_html).group(0)
    code = (cols + "\n" + _fn(index_html, "_sbSelFuer") + "\n" + _fn(index_html, "_profGesperrt") + r"""
const d=new Date();const iso=x=>{const t=new Date(d.getTime()+x*24*3600*1000);return t.getFullYear()+"-"+String(t.getMonth()+1).padStart(2,"0")+"-"+String(t.getDate()).padStart(2,"0");};
const F={aktiv:{active:1,locked:0},ohneLocked:{active:1},gesperrt:{active:1,locked:1},gesperrtBool:{active:true,locked:true},
 inaktiv:{active:0,locked:0},inaktivBool:{active:false},gestern:{active:1,deactivate_at:iso(-1)},heute:{active:1,deactivate_at:iso(0)},
 morgen:{active:1,deactivate_at:iso(1)},leer:null};
const R={};for(const k in F)R[k]=_profGesperrt(F[k]);
R.selUsers=_sbSelFuer("users");R.selAndere=_sbSelFuer("projects");
process.stdout.write(JSON.stringify(R));""")
    R = _node(node_exe, tmp_path, code, "prof.js")
    assert R["aktiv"] is False and R["ohneLocked"] is False and R["morgen"] is False
    for k in ("gesperrt", "gesperrtBool", "inaktiv", "inaktivBool", "gestern", "heute", "leer"):
        assert R[k] is True, k
    assert R["selUsers"].startswith("select=id,") and "password_hash" not in R["selUsers"]
    assert R["selAndere"] == "select=*"


# ───────────────────────────────────────────────────────────── statische Riegel (Client)
def _mangel_client(html):
    c = nur_code(html)
    m = []
    # Fund 11
    if 'fetch(_SB_AUTH+"/logout?scope=local"' not in funktion(c, "_sbAuthLogout"):
        m.append("Abmelden ohne scope=local")
    # Fund 15/16 PwInput
    pw = funktion(c, "PwInput")
    if "tabIndex:-1" in pw or "minWidth:44" not in pw or "height:44" not in pw:
        m.append("Augen-Knopf nicht 44 px / nicht per Tastatur erreichbar")
    # Anmeldemaske
    ls = _teil(c, "function LoginScreen(", "'data-login-version'")  # bis zur Versionszeile; funktion() endete an der Parameter-Klammer
    if 'id:"lbl_login_user", autoComplete: "username", autoCapitalize: "none", autoCorrect: "off", spellCheck: false,' not in ls:
        m.append("Benutzername ohne autoCapitalize/autoCorrect/spellCheck/autoComplete")
    if 'id:"lbl_login_pw", type: "password", autoComplete: "current-password"' not in ls:
        m.append("Passwort ohne autoComplete current-password")
    if re.search(r'placeholder: "Benutzername", style: \{\.\.\.II\(\),flex:1,fontSize:16,minHeight:44', ls) is None:
        m.append("Passwort-Hilfe-Feld nicht 16 px / 44 px")
    if re.search("[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B06\u2B07\u2B05\u27A1\uFE0F]", ls):
        m.append("Emoji auf der Anmeldemaske")
    if "_passwortHilfeAnfragen(_u)" not in ls or "_translateAndExec(\"/api/password-reset\"" in ls:
        m.append("Passwort-Hilfe nicht ueber die RPC")
    if not all(x in ls for x in ('e.name==="TypeError"', 'e.name==="TimeoutError"', 'e.name==="AbortError"', "_OFFPW.verify(user,pw,cached)")):
        m.append("schwaches Netz: kein Offline-Weg")
    # users nie mit select=*
    for fn in ("_sbGet", "_sbGetOrder"):
        if '_sbSelFuer(table)' not in funktion(c, fn):
            m.append(fn + " liest users mit select=*")
    for fn in ("_sbPost", "_sbUpsert", "_sbPatch", "_sbDelete"):
        if '_sbSelFuer(table)' not in funktion(c, fn):
            m.append(fn + ": Antwort fuer users ohne Spaltenliste")
    if "password_hash" in re.search(r'const _USER_SAFE_COLS="[^"]*";', c).group(0):
        m.append("_USER_SAFE_COLS enthaelt password_hash")
    if "dcodeIO.bcrypt" in c:
        m.append("bcrypt/password_hash wird noch benutzt")
    # Fund 10: kein Kennwort in die Warteschlange
    if re.search(r"SQ\.push\(\{[^;]*?\bpassword\s*:", c):
        m.append("Kennwort in SQ.push")
    if "d.password_hash=d.password" in c:
        m.append("Klartext-Rueckfall nach password_hash")
    # Fund 12
    if "filter(it=>!it.owner||(!!_cuId&&it.owner===_cuId))" not in c or "!_cuId||!it.owner" in c:
        m.append("Warteschlange sendet fremde Eintraege")
    if "owner:photo.owner||" not in c or ".filter(x=>!x.owner||x.owner===_pqUid)" not in c:
        m.append("Foto-Warteschlange ohne Besitzer")
    # Fund 3d: Start mit gesperrtem Profil
    if "(fresh.length===0||_profGesperrt(fresh[0]))){await _zugangEntzogen(setCurUser);return;}" not in c:
        m.append("Start prueft gesperrtes Profil nicht")
    # Fund 9: eine Mindestlaenge
    if "const PW_MIN_LEN=8;" not in c:
        m.append("PW_MIN_LEN fehlt")
    for anker in ("if(newPw.length<PW_MIN_LEN){setPwMsg(", "if(!newPw||newPw.length<PW_MIN_LEN){setPwMsg(",
                  "if(nf.password.length<PW_MIN_LEN)", "nf.loginPw.length<PW_MIN_LEN", "if(np.length<PW_MIN_LEN)"):
        if anker not in c:
            m.append("Mindestlaenge nicht einheitlich: " + anker)
    for alt in ("newPw.length<4", "newPw.length<6", "nf.password.length<4", "nf.loginPw.length<4", "np.length>=6"):
        if alt in c:
            m.append("alte Mindestlaenge: " + alt)
    # Admin-Reset/Anlage nur online
    if 'alert("Passwort zurücksetzen geht nur mit Verbindung zum Server' not in c or "Benutzer anlegen geht nur mit Verbindung zum Server" not in c:
        m.append("Admin-Reset/Anlage nicht online-only")
    return m


def test_client_riegel(index_html):
    assert _mangel_client(index_html) == []


@pytest.mark.parametrize("alt,neu,erwartet", [
    ('fetch(_SB_AUTH+"/logout?scope=local"', 'fetch(_SB_AUTH+"/logout"', "scope=local"),
    ('React.createElement(\'button\', { type:"button", onClick:()=>_setShow(s=>!s)', 'React.createElement(\'button\', { type:"button", tabIndex:-1, onClick:()=>_setShow(s=>!s)', "Augen-Knopf"),
    ('autoCapitalize: "none", autoCorrect: "off", spellCheck: false, value: user,', "value: user,", "autoCapitalize"),
    ('placeholder: "Benutzername", style: {...II(),flex:1,fontSize:16,minHeight:44', 'placeholder: "Benutzername", style: {...II(),flex:1,fontSize:13,minHeight:44', "16 px"),
    ('_ik("schloss",14), "Passwort vergessen?")', '"\U0001F511 Passwort vergessen?")', "Emoji"),
    ('const parts=[hasSelect?"":_sbSelFuer(table),filter||"",hatGrenze?', 'const parts=[hasSelect?"":"select=*",filter||"",hatGrenze?', "_sbGet liest"),
    ('SQ.push({url:"/api/users",method:"POST",body:{id:nid,username:nf.username,name:nf.name,', 'SQ.push({url:"/api/users",method:"POST",body:{id:nid,username:nf.username,password:nf.password,name:nf.name,', "Kennwort in SQ.push"),
    ("filter(it=>!it.owner||(!!_cuId&&it.owner===_cuId))", "filter(it=>!_cuId||!it.owner||it.owner===_cuId)", "fremde Eintraege"),
    (".filter(x=>!x.owner||x.owner===_pqUid)", "", "Foto-Warteschlange"),
    ("(fresh.length===0||_profGesperrt(fresh[0]))){await _zugangEntzogen(setCurUser);return;}", "(false)){return;}", "gesperrtes Profil"),
    ('if(newPw.length<PW_MIN_LEN){setPwMsg("Mindestens "', 'if(newPw.length<4){setPwMsg("Mindestens "', "Mindestlaenge"),
    ("_sbPatch(\"users\",_prof.id,_stamp)", "dcodeIO.bcrypt.compareSync(1,2);_sbPatch(\"users\",_prof.id,_stamp)", "bcrypt"),
])
def test_umkehrprobe_client(index_html, alt, neu, erwartet):
    assert alt in index_html, alt
    kaputt = index_html.replace(alt, neu, 1)
    assert any(erwartet in x for x in _mangel_client(kaputt)), _mangel_client(kaputt)


# ───────────────────────────────────────────────────────────── SQL-Entwuerfe
def _sql(name, art="ENTWURF"):
    with open(os.path.join(SQL_DIR, "%s_%s.sql" % (name, art)), encoding="utf-8") as f:
        return f.read()


def _ohne_kommentar(t):
    return "\n".join(l.split("--", 1)[0] for l in t.splitlines())


def _funktionsrumpf(t, kopf):
    i = t.index(kopf)
    a = t.index("AS $$", i)
    e = t.index("$$;", a + 5)
    return t[a:e]


def _mangel_sql(name, t, rb):
    m = []
    code = _ohne_kommentar(t)
    if t.splitlines()[0].strip() != "-- IDEMPOTENT" or rb.splitlines()[0].strip() != "-- IDEMPOTENT":
        m.append("Kopf -- IDEMPOTENT fehlt")
    if re.search(r"\bcascade\b", t + rb, re.I):
        m.append("CASCADE")
    if "\nBEGIN;" not in code or "\nCOMMIT;" not in code:
        m.append("keine Transaktion")
    if "VORPRUEFUNG" not in t or "RAISE EXCEPTION" not in code:
        m.append("keine abbrechende Vorpruefung")
    if "VORHER" not in t or "NACHHER" not in t:
        m.append("keine Vorher/Nachher-Zahlen")
    probe = t[t.find("-- PROBE"):] if "-- PROBE" in t else ""
    if "-- BEGIN;" not in probe or "-- ROLLBACK;" not in probe or "SET LOCAL ROLE" not in probe:
        m.append("kein auskommentierter Probenblock BEGIN ... ROLLBACK mit Rollen")
    if name.startswith("AUTH_HAERTUNG_1"):
        if "REVOKE SELECT ON public.users FROM anon, authenticated;" not in code or "column_name <> 'password_hash'" not in code:
            m.append("password_hash bleibt lesbar")
        rumpf = _funktionsrumpf(t, "CREATE OR REPLACE FUNCTION public.login_lookup(p_username text)")
        rc = _ohne_kommentar(rumpf)
        if re.findall(r"jsonb_build_object\('(\w+)'", rc) != ["email"] or "'id'" in rc or "'phone'" in rc:
            m.append("login_lookup gibt mehr als die E-Mail heraus")
        for bed in ("u.locked", "u.active", "u.deactivate_at"):
            if bed not in rc:
                m.append("login_lookup filtert nicht " + bed)
        pol = code[code.index("CREATE POLICY users_update"):code.index(";", code.index("CREATE POLICY users_update"))]
        if "WITH CHECK" not in pol or "auth.uid()" not in pol or "'admin'" not in pol:
            m.append("users_update nicht eng")
        if "v_frei constant text[] := ARRAY['last_login','login_count','updated_at','phone','avatar'];" not in code:
            m.append("harmlose Spalten nicht festgelegt")
        if "DELETE FROM auth.sessions WHERE user_id = target_user_id;" not in code or "UPDATE auth.refresh_tokens SET revoked = true" not in code:
            m.append("Reset beendet Sitzungen nicht")
        if "ERRCODE = '23505'" not in code or "lower(au.email) = lower(btrim(p_email))" not in code:
            m.append("admin_create_user ueberschreibt vorhandenes Konto")
        if "AUTH_HAERTUNG_v1056_HUELLE' in v_src" not in code:
            m.append("Huelle nicht idempotent (wuerde sich selbst kopieren)")
        # Review 19.11. Fund 2: Rollout-Tor ueber die Versionsmarke im Login-Protokoll
        kopf = t[:t.index("\nBEGIN;")]
        if "gotrue v3.9.1056-supabase" not in kopf or "details enthaelt den User-Agent" in kopf:
            m.append("Rollout-Tor im Kopf nicht konkret (Versionsmarke)")
        if (r"regexp_match(coalesce(a.details::text,''), 'gotrue v(\d{1,4})\.(\d{1,4})\.(\d{1,6})')" not in code
                or "AND (l.v IS NULL OR ARRAY[l.v[1]::int, l.v[2]::int, l.v[3]::int] < ARRAY[3,9,1056])$q$" not in code
                or "WHERE l.zeit > now() - interval '14 days'" not in code or "RAISE EXCEPTION 'Vorpruefung Tor:" not in code):
            m.append("Rollout-Tor bricht nicht ab bei alter/fehlender Version")
        # Review 19.11. Fund 3: Wiederverknuepfen statt 23505-Sackgasse
        if ("NOT EXISTS (SELECT 1 FROM public.users pu WHERE pu.auth_user_id = v_vorhanden)" not in code
                or "AND lower(btrim(coalesce(pu.email,''))) = lower(btrim(p_email))" not in code
                or "AND pu.auth_user_id IS NULL)) THEN" not in code
                or "IF public.auth_role() IS DISTINCT FROM 'admin' THEN" not in code
                or "IF length(coalesce(p_password,'')) < 8 THEN" not in code):
            m.append("admin_create_user: kein Wiederverknuepfen (oder Admin-/Laengenpruefung weg)")
        # Review 19.11. Fund 4: weitere Lesewege fuer den Hash
        if ("information_schema.view_column_usage" not in code or "p.prorettype = 'public.users'::regtype" not in code
                or "to_jsonb\\s*\\(|row_to_json\\s*\\(" not in code or "select\\s+\\*" not in code
                or "IF v_n > 0 THEN\n    RAISE EXCEPTION 'Vorpruefung: % weitere Lesewege" not in code
                or "v_geprueft constant text[] := ARRAY['login_lookup','_users_selbst_nur_harmlos'];" not in code):
            m.append("weitere Lesewege fuer password_hash nicht geprueft")
        # Review 19.11. Fund 10: Spaltenrecht nur an Rollen mit vorherigem Tabellen-SELECT
        if ("GRANT SELECT (%s) ON public.users TO anon, authenticated" in code
                or "EXECUTE format('GRANT SELECT (%s) ON public.users TO %s', v_spalten, v_rollen);" not in code
                or "(v_x->>'anon_tabelle')::boolean" not in code):
            m.append("Spaltenrecht nicht aus der Sicherung")
        rbc = _ohne_kommentar(rb)
        i_rev = rbc.find("REVOKE SELECT ON public.users FROM anon, authenticated;")
        i_gr = rbc.find("GRANT SELECT ON public.users TO anon;")
        if i_rev < 0 or i_gr < 0 or i_rev > i_gr:
            m.append("Rueckweg: erst REVOKE, dann exakt nach Sicherung vergeben - fehlt")
        # Review 19.11. Fund 12: verstaendlicher Abbruch bei SETOF/TABLE
        if "RETURN QUERY" not in code or "pg_get_functiondef(''public.%''::regproc)" not in code:
            m.append("SETOF-Abbruch ohne Handlungsanweisung")
    if name.startswith(("AUTH_HAERTUNG_1", "AUTH_HAERTUNG_2")):
        # Review 19.11. Fund 1: Aussperr-Schutz wie in AUTH_HAERTUNG_4 + active NULL
        if "WHERE u.auth_user_id IS NOT NULL AND u.active IS NULL;" not in code:
            m.append("Aussperr-Schutz: active NULL nicht abgefangen")
        if ("RAISE EXCEPTION 'Vorpruefung: % Logins ohne aktive users-Zeile waren in den letzten 30 Tagen aktiv" not in code
                or "RAISE EXCEPTION 'Vorpruefung: % verknuepfte users-Zeilen haben active = NULL" not in code
                or "au.last_sign_in_at > now() - interval '30 days'" not in code):
            m.append("Aussperr-Schutz: 30-Tage-Regel fehlt")
        # Review 19.11. Fund 11: nur der Kopf wird umbenannt
        if "EXECUTE replace(v_def" in code or "regexp_replace(v_def, '^CREATE OR REPLACE FUNCTION public\\.' || v_name || '\\(" not in code:
            m.append("Kopf-Umbenennung nicht auf das erste Vorkommen begrenzt")
        if re.search(r"regexp_replace\(v_def,[^;]*'g'\)", code):
            m.append("Kopf-Umbenennung nicht auf das erste Vorkommen begrenzt ('g')")
    if name.startswith("AUTH_HAERTUNG_2"):
        rumpf = _ohne_kommentar(_funktionsrumpf(t, "CREATE OR REPLACE FUNCTION public.ist_aktiver_benutzer()"))
        for bed in ("u.auth_user_id = auth.uid()", "u.active", "u.locked", "u.deactivate_at > current_date"):
            if bed not in rumpf:
                m.append("ist_aktiver_benutzer prueft nicht " + bed)
        if "kein aktiver, verknuepfter Admin" not in code:
            m.append("kein Aussperr-Schutz")
        if "WHEN v_name = 'auth_role' THEN '''anon'''" not in code:
            m.append("auth_role faellt nicht auf anon")
        if "freizuegige Policies negieren einen Helfer" not in code:
            m.append("negierte Helfer nicht abgefangen")
        # Review 19.11. Fund 5: breitere Negationsmuster + Hinweisliste Funktionen/Sichten
        for muster in (r"'\mnot\s*\(*\s*' || v_h", r"v_h || '\)?\s*is\s+distinct\s+from'",
                       r"'is\s+distinct\s+from\s*\(*\s*' || v_h", r"'coalesce\(\s*' || v_h || '\s*,[^()]*\)\s*(<>|!=",
                       r"v_h || '\)?\s*is\s+not\s+true'", r"v_h || '\)?\s*=\s*false'", r"v_rolle || '\)?\s*(<>|!=)'"):
            if muster not in code:
                m.append("Negationsmuster fehlt: " + muster)
        if "IF EXISTS (SELECT 1 FROM unnest(v_negiert) m WHERE r.ausdruck ~* m) THEN" not in code:
            m.append("Negationsmuster werden nicht alle angewendet")
        if "HINWEIS Funktion % ruft Helfer" not in code or "FROM pg_views v" not in code:
            m.append("Funktionen/Sichten mit Helfern nicht gelistet")
        # Review 19.11. Fund 6: EXPLAIN-ANALYZE-Block nur auskommentiert
        if ("-- EXPLAIN (ANALYZE, BUFFERS, VERBOSE) SELECT count(*) FROM public.supplier_articles;" not in t
                or "-- EXPLAIN (ANALYZE, BUFFERS, VERBOSE) SELECT count(*) FROM public.time_entries;" not in t):
            m.append("Leistungs-Messblock (EXPLAIN ANALYZE) fehlt")
        if re.search(r"\bexplain\b", code, re.I):
            m.append("EXPLAIN laeuft automatisch mit")
    if name.startswith("AUTH_HAERTUNG_3"):
        if "infinity" in code.lower():
            m.append("banned_until = infinity (GoTrue liest das nicht sicher)")
        if "interval '100 years'" not in code or "Keine IDs eingetragen" not in code or "ist KEINE Waise" not in code:
            m.append("Waisen nicht per expliziter, gepruefter ID-Liste gesperrt")
    if name.startswith("AUTH_HAERTUNG_4"):
        liste = code[code.index("v_tabellen constant text[] := ARRAY["):code.index("];", code.index("v_tabellen constant"))]
        for tabu in ("arbeitsscheine", "kunden", "finkzeit", "offa", "juprowa", "feed", "supplier_configs"):
            if tabu in liste:
                m.append("Freigabe-/Tabu-Tabelle in der aktiven Liste: " + tabu)
        if "ist_aktiver_benutzer() fehlt" not in code or "(SELECT public.ist_aktiver_benutzer())" not in code:
            m.append("Ersatzbedingung/Voraussetzung fehlt")
        if "AS RESTRICTIVE FOR SELECT TO authenticated" not in code or "NOT public.is_kiosk_role()" not in code:
            m.append("Kiosk-Sperre fehlt")
        if "Logins ohne aktive users-Zeile waren in den letzten 30 Tagen aktiv" not in code:
            m.append("kein Schutz vor dem Aussperren von Diensten")
    if name.startswith("AUTH_HAERTUNG_5"):
        rumpf = _ohne_kommentar(_funktionsrumpf(t, "CREATE OR REPLACE FUNCTION public.passwort_hilfe_anfragen(p_username text)"))
        rets = re.findall(r"RETURN\s+([^;]+);", rumpf)
        if not rets or any(r.strip() != "v_ok" for r in rets):
            m.append("RPC antwortet nicht immer gleich: %r" % rets)
        if "GRANT EXECUTE ON FUNCTION public.passwort_hilfe_anfragen(text) TO anon, authenticated;" not in code:
            m.append("anon darf die RPC nicht rufen")
        if "REVOKE ALL ON TABLE public.passwort_hilfe_log FROM PUBLIC, anon, authenticated;" not in code:
            m.append("Log lesbar")
        if "interval '1 hour'" not in rumpf or "v_n >= 30" not in rumpf:
            m.append("keine Drosselung")
        # Review 19.11. Fund 8: globale Grenze nur fuer Nicht-Treffer; echte Treffer melden immer (1/Name/Stunde)
        i_nicht = rumpf.find("IF NOT v_treffer THEN")
        i_grenze = rumpf.find("v_n >= 30")
        i_ende = rumpf.find("\n  END IF;", i_nicht) if i_nicht >= 0 else -1   # Ende des Nicht-Treffer-Zweigs
        if (i_nicht < 0 or not (i_nicht < i_grenze < i_ende)
                or "WHERE NOT treffer AND angefragt_am > v_jetzt - interval '10 minutes'" not in rumpf):
            m.append("globale Grenze bremst auch echte Treffer")
        if "WHERE username_norm = v_norm AND treffer AND angefragt_am > v_jetzt - interval '1 hour'" not in rumpf:
            m.append("keine Drosselung je Benutzername")
        # Review 19.11. Fund 9: Text-created_at als ISO-8601 UTC
        if ("to_char(v_jetzt AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS.MS\"Z\"')" not in rumpf
                or "IF v_zeit_text THEN" not in rumpf):
            m.append("created_at als Text nicht im ISO-Format")
    return m


@pytest.mark.parametrize("name", SQL_NAMEN)
def test_sql_entwurf(name):
    assert _mangel_sql(name, _sql(name), _sql(name, "ROLLBACK")) == []


@pytest.mark.parametrize("name,alt,neu,erwartet", [
    ("AUTH_HAERTUNG_1_users_v1056", "REVOKE SELECT ON public.users FROM anon, authenticated;", "", "password_hash bleibt lesbar"),
    ("AUTH_HAERTUNG_1_users_v1056", "SELECT jsonb_build_object('email', btrim(u.email))", "SELECT jsonb_build_object('email', btrim(u.email), 'id', u.id)", "mehr als die E-Mail"),
    ("AUTH_HAERTUNG_1_users_v1056", "DELETE FROM auth.sessions WHERE user_id = target_user_id;", "", "Sitzungen"),
    ("AUTH_HAERTUNG_1_users_v1056", "     AND NOT coalesce(u.locked::text IN ('1','t','true'), false)\n     AND (u.deactivate_at IS NULL OR u.deactivate_at > current_date)\n     AND nullif", "     AND nullif", "filtert nicht"),
    ("AUTH_HAERTUNG_2_gesperrt_v1056", "       AND NOT coalesce(u.locked::text IN ('1','t','true'), false)\n       AND (u.deactivate_at IS NULL OR u.deactivate_at > current_date)\n  );", "  );", "ist_aktiver_benutzer prueft nicht"),
    ("AUTH_HAERTUNG_3_waisen_v1056", "now() + interval '100 years'\n   WHERE id = ANY (v_ziel)", "'infinity'\n   WHERE id = ANY (v_ziel)", "infinity"),
    ("AUTH_HAERTUNG_4_policies_v1056", "    'werkzeuge','wz_service','as_vorlagen',", "    'werkzeuge','wz_service','as_vorlagen','arbeitsscheine',", "arbeitsscheine"),
    ("AUTH_HAERTUNG_5_passwort_hilfe_v1056", "  IF v_norm = '' OR length(v_norm) > 80 THEN RETURN v_ok; END IF;", "  IF v_norm = '' OR length(v_norm) > 80 THEN RETURN jsonb_build_object('ok', false); END IF;", "immer gleich"),
    ("AUTH_HAERTUNG_5_passwort_hilfe_v1056", "DROP FUNCTION IF EXISTS public.passwort_hilfe_anfragen(text);", "DROP FUNCTION IF EXISTS public.passwort_hilfe_anfragen(text) CASCADE;", "CASCADE"),
    # ── Review 19.11.: je Fund der alte Text zurueck -> Riegel schlaegt an
    # Fund 1 (Skript 1 und 2): active NULL / 30-Tage-Regel
    ("AUTH_HAERTUNG_1_users_v1056", "    FROM public.users u WHERE u.auth_user_id IS NOT NULL AND u.active IS NULL;", "    FROM public.users u WHERE false;", "active NULL"),
    ("AUTH_HAERTUNG_1_users_v1056", "    RAISE EXCEPTION 'Vorpruefung: % Logins ohne aktive users-Zeile waren in den letzten 30 Tagen aktiv", "    RAISE NOTICE 'Vorpruefung: % Logins ohne aktive users-Zeile waren in den letzten 30 Tagen aktiv", "30-Tage-Regel"),
    ("AUTH_HAERTUNG_2_gesperrt_v1056", "    FROM public.users u WHERE u.auth_user_id IS NOT NULL AND u.active IS NULL;", "    FROM public.users u WHERE false;", "active NULL"),
    ("AUTH_HAERTUNG_2_gesperrt_v1056", "    RAISE EXCEPTION 'Vorpruefung: % Logins ohne aktive users-Zeile waren in den letzten 30 Tagen aktiv", "    RAISE NOTICE 'Vorpruefung: % Logins ohne aktive users-Zeile waren in den letzten 30 Tagen aktiv", "30-Tage-Regel"),
    # Fund 2: Rollout-Tor
    ("AUTH_HAERTUNG_1_users_v1056", "--      PRUEFSTELLE (Review 19.11. Fund 2):", "--      Pruefen: activity_log action='login' der letzten Tage, details enthaelt den User-Agent. (", "Rollout-Tor im Kopf"),
    ("AUTH_HAERTUNG_1_users_v1056", "       AND (l.v IS NULL OR ARRAY[l.v[1]::int, l.v[2]::int, l.v[3]::int] < ARRAY[3,9,1056])$q$", "$q$", "Rollout-Tor bricht nicht ab"),
    # Fund 4: weitere Lesewege
    ("AUTH_HAERTUNG_1_users_v1056", "  IF v_n > 0 THEN\n    RAISE EXCEPTION 'Vorpruefung: % weitere Lesewege", "  IF false THEN\n    RAISE EXCEPTION 'Vorpruefung: % weitere Lesewege", "weitere Lesewege"),
    ("AUTH_HAERTUNG_1_users_v1056", "        FROM information_schema.view_column_usage vcu", "        FROM information_schema.columns vcu", "weitere Lesewege"),
    # Fund 10: Spaltenrecht aus der Sicherung; Rueckweg erst REVOKE
    ("AUTH_HAERTUNG_1_users_v1056", "EXECUTE format('GRANT SELECT (%s) ON public.users TO %s', v_spalten, v_rollen);", "EXECUTE format('GRANT SELECT (%s) ON public.users TO anon, authenticated', v_spalten);", "nicht aus der Sicherung"),
    ("AUTH_HAERTUNG_1_users_v1056", "  REVOKE SELECT ON public.users FROM anon, authenticated;\n  IF (v_x->>'anon_tabelle')", "  IF (v_x->>'anon_tabelle')", "erst REVOKE"),
    # Fund 11: Kopf-Umbenennung nur erstes Vorkommen
    ("AUTH_HAERTUNG_1_users_v1056", "    EXECUTE v_kopie;", "    EXECUTE replace(v_def, 'FUNCTION public.'||v_name||'(', 'FUNCTION public.'||v_basis||'(');", "erste Vorkommen"),
    ("AUTH_HAERTUNG_1_users_v1056", "'CREATE OR REPLACE FUNCTION public.' || v_basis || '(');", "'CREATE OR REPLACE FUNCTION public.' || v_basis || '(', 'g');", "('g')"),
    ("AUTH_HAERTUNG_2_gesperrt_v1056", "    EXECUTE v_kopie;", "    EXECUTE replace(v_def, 'FUNCTION public.'||v_name||'()', 'FUNCTION public.'||v_basis||'()');", "erste Vorkommen"),
    ("AUTH_HAERTUNG_2_gesperrt_v1056", "'CREATE OR REPLACE FUNCTION public.' || v_basis || '()');", "'CREATE OR REPLACE FUNCTION public.' || v_basis || '()', 'g');", "('g')"),
    # Fund 12: SETOF-Abbruch mit Handlungsanweisung
    ("AUTH_HAERTUNG_1_users_v1056",
     "    IF v_set THEN\n      RAISE EXCEPTION '% liefert eine Menge (RETURNS %) - die Huelle reicht nur EINEN Rueckgabewert weiter, nichts geaendert. Pruefen: SELECT pg_get_functiondef(''public.%''::regproc); und was die App aus rpc/% liest (Array?). Dann die Huelle auf RETURN QUERY SELECT * FROM <Basis>(...) umbauen lassen - melden', v_name, v_res, v_name, v_name; END IF;",
     "    IF v_set THEN RAISE EXCEPTION '% liefert eine Menge (SETOF/TABLE) - Huelle nicht vorgesehen, melden', v_name; END IF;",
     "SETOF-Abbruch"),
    # Fund 5: Negationsmuster
    ("AUTH_HAERTUNG_2_gesperrt_v1056", "    v_h || '\\)?\\s*is\\s+distinct\\s+from',", "", "is\\s+distinct\\s+from"),
    ("AUTH_HAERTUNG_2_gesperrt_v1056", "    v_h || '\\)?\\s*=\\s*false',", "", "=\\s*false"),
    ("AUTH_HAERTUNG_2_gesperrt_v1056", "    IF EXISTS (SELECT 1 FROM unnest(v_negiert) m WHERE r.ausdruck ~* m) THEN", "    IF r.ausdruck ~* v_negiert[1] THEN", "nicht alle angewendet"),
    ("AUTH_HAERTUNG_2_gesperrt_v1056", "FROM pg_views v", "FROM pg_matviews v", "Sichten mit Helfern"),
    # Fund 6: EXPLAIN nur auskommentiert
    ("AUTH_HAERTUNG_2_gesperrt_v1056", "-- EXPLAIN (ANALYZE, BUFFERS, VERBOSE) SELECT count(*) FROM public.time_entries;", "", "Messblock"),
    ("AUTH_HAERTUNG_2_gesperrt_v1056", "-- EXPLAIN (ANALYZE, BUFFERS, VERBOSE) SELECT count(*) FROM public.supplier_articles;", "EXPLAIN (ANALYZE, BUFFERS, VERBOSE) SELECT count(*) FROM public.supplier_articles;", "automatisch"),
    # Fund 8: alte Reihenfolge (globale Grenze vor dem Nachschlagen, gilt fuer alle)
    ("AUTH_HAERTUNG_5_passwort_hilfe_v1056", "  SELECT u.id, u.name, u.username, u.active, u.locked, u.deactivate_at INTO v_user",
     "  SELECT count(*) INTO v_n FROM public.passwort_hilfe_log WHERE angefragt_am > v_jetzt - interval '10 minutes';\n  IF v_n >= 30 THEN RETURN v_ok; END IF;\n  SELECT u.id, u.name, u.username, u.active, u.locked, u.deactivate_at INTO v_user",
     "echte Treffer"),
    # Fund 9: created_at roh statt ISO
    ("AUTH_HAERTUNG_5_passwort_hilfe_v1056", "           to_char(v_jetzt AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS.MS\"Z\"')", "           v_jetzt", "ISO-Format"),
])
def test_umkehrprobe_sql(name, alt, neu, erwartet):
    t, rb = _sql(name), _sql(name, "ROLLBACK")
    if alt in t:
        t = t.replace(alt, neu, 1)
    else:
        assert alt in rb, alt
        rb = rb.replace(alt, neu, 1)
    assert any(erwartet in x for x in _mangel_sql(name, t, rb)), _mangel_sql(name, t, rb)


def test_umkehrprobe_sql_wiederverknuepfen():
    """Review 19.11. Fund 3: alte Huellen-Bedingung (nur 'schon mit diesem Benutzernamen verknuepft') -> Riegel schlaegt an."""
    name = "AUTH_HAERTUNG_1_users_v1056"
    t, rb = _sql(name), _sql(name, "ROLLBACK")
    kaputt, n = re.subn(r"\n     -- erlaubt 2 .*?AND pu\.auth_user_id IS NULL\)\) THEN", " THEN", t, count=1, flags=re.S)
    assert n == 1
    assert "lower(btrim(p_username))) THEN" in kaputt
    assert any("Wiederverknuepfen" in x for x in _mangel_sql(name, kaputt, rb)), _mangel_sql(name, kaputt, rb)


def test_sql_keine_werte_und_kein_live_apply_hinweis():
    """Die Entwuerfe nennen keine echten E-Mail-Adressen/IDs und sind als ENTWURF markiert."""
    for name in SQL_NAMEN:
        t = _sql(name)
        assert "STATUS: ENTWURF — NICHT APPLIZIERT" in t, name
        assert not re.search(r"[\w.+-]+@(ep-kolar\.at|epkolar\.local)", t), name
        assert not re.search(r"'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'", t.replace("00000000-0000-0000-0000-000000000000", "")), name
