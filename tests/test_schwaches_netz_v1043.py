# -*- coding: utf-8 -*-
"""v3.9.1043 Schwaches Netz (Werkstatt-Tablet 18.11.2026: WLAN -88 dBm, Antwortzeit ~11 s, erste DNS-Abfrage
scheiterte; Baustellen-Handys im 3G/EDGE genauso).

Node fuehrt die ECHTEN reinen Helfer aus index.html aus:
  * Wartezeiten (1,5 s / 4 s), Pausen der Warteschlange (5 s ... 5 min), Zeitgrenzen (Lesen, Lebenszeichen, Upload)
  * Fehlerart: Zeitueberschreitung / Netz (Chrome, Safari, Firefox) / Server / dauerhaft - ein Programmfehler-TypeError
    ist KEIN Netzfehler, ein HTTP400 mit "timeout" im Text auch nicht
  * Zustand gut/schwach/offline und die deutschen Anzeigetexte
  * _netzLesen: wiederholt Lesen nach DNS-/Zeitfehler, NICHT nach 4xx oder Programmfehlern
  * die echte PhotoQ: Zeitueberschreitung zaehlt nicht gegen den 10er-Deckel, Foto bleibt, Lauf bricht ab, Versuch geplant
Verdrahtung: Lesen nur fuer GET, doSync haelt Netzfehler in der Warteschlange (vor dem 5er-Zaehler), Knoepfe melden.
Umkehrproben: jede Rueckbau-Variante muss mindestens einen Befund liefern.
"""
import json
import re

import pytest

from conftest import run_node_snippet, _extract_fn
from _hilfen import nur_code

REIN = ("_netzBackoffMs", "_netzPauseMs", "_netzLeseMsFuer", "_netzHerzMsFuer", "_netzUploadMsFuer", "_netzFehlerArt",
        "_netzFehlerTransient", "_netzNochmal", "_netzMedian", "_netzKlasse", "_netzPingText", "_netzStatusText",
        "_netzAbstandOk", "_netzServerDa", "_netzGrundText", "_syncErgebnisText")
ZUSTAND = ("_netzOnline", "_netzConn", "_netzLage", "_netzMelden", "_netzFehlerMerken", "_netzSchlaf", "_netzLesen")


def _fns(src, namen):
    teile = []
    for n in namen:
        f = _extract_fn(src, n, rf"(?:async\s+)?function\s+{re.escape(n)}\s*\(")
        assert f, n
        teile.append(f)
    return "\n".join(teile)


def _netz_zustand(src):
    i = src.index("const _NETZ={")
    return src[i:src.index("\n", i)]


def _photoq(src):
    m = re.search(r"const PhotoQ=\{[\s\S]*?\n\};", src)
    assert m
    return m.group(0)


REIN_KOERPER = r"""
const R={};
R.backoff=[0,1,2,7].map(_netzBackoffMs);
R.pause=[0,1,2,3,4,5,6,50].map(_netzPauseMs);
R.lese=[_netzLeseMsFuer(0,30000),_netzLeseMsFuer(200,30000),_netzLeseMsFuer(11000,30000),_netzLeseMsFuer(40000,30000),_netzLeseMsFuer(NaN)];
R.herz=[_netzHerzMsFuer(0),_netzHerzMsFuer(300),_netzHerzMsFuer(5000),_netzHerzMsFuer(11000)];
R.upload=[_netzUploadMsFuer(0),_netzUploadMsFuer(300000),_netzUploadMsFuer(1500000),_netzUploadMsFuer(50000000)];
function E(name,msg){const e=new Error(msg);e.name=name;return e;}
R.art={
 chromeZeit:_netzFehlerArt(E("TimeoutError","signal timed out"),true),
 safariZeit:_netzFehlerArt(E("TimeoutError","The operation timed out."),true),
 abbruch:_netzFehlerArt(E("AbortError","The user aborted a request."),true),
 chromeNetz:_netzFehlerArt(new TypeError("Failed to fetch"),true),
 safariNetz:_netzFehlerArt(new TypeError("Load failed"),true),
 firefoxNetz:_netzFehlerArt(new TypeError("NetworkError when attempting to fetch resource."),true),
 dns:_netzFehlerArt(new TypeError("net::ERR_NAME_NOT_RESOLVED"),true),
 offline:_netzFehlerArt(new Error("egal"),false),
 s503:_netzFehlerArt(new Error("HTTP503 down"),true),
 s429:_netzFehlerArt(new Error("HTTP429 slow"),true),
 s400timeout:_netzFehlerArt(new Error("HTTP400 canceling statement due to statement timeout"),true),
 s409:_netzFehlerArt(new Error("HTTP409 duplicate key"),true),
 auth401:_netzFehlerArt(new Error("Auth:401"),true),
 programm:_netzFehlerArt(new TypeError("Cannot read properties of undefined (reading 'id')"),true),
 leer:_netzFehlerArt(null,true)
};
R.transient=[_netzFehlerTransient(new TypeError("Load failed"),true),_netzFehlerTransient(new Error("HTTP400 x"),true)];
R.nochmal=[["netz",0],["netz",1],["netz",2],["zeit",0],["zeit",1],["server",0],["",0],["offline",0]].map(a=>_netzNochmal(a[0],a[1]));
R.median=[_netzMedian([]),_netzMedian([300]),_netzMedian([11000,200,900]),_netzMedian([100,300]),_netzMedian([0,-5,400])];
R.klasse={
 gut:_netzKlasse({online:true,rttMs:250,zeitFehler:0,conn:{effectiveType:"4g",rtt:100,downlink:10}}),
 tablet:_netzKlasse({online:true,rttMs:11000,zeitFehler:0,conn:null}),
 grenze:_netzKlasse({online:true,rttMs:3000}),
 zeitfehler:_netzKlasse({online:true,rttMs:400,zeitFehler:1}),
 edge:_netzKlasse({online:true,rttMs:0,conn:{effectiveType:"2g",rtt:0,downlink:0}}),
 conn_rtt:_netzKlasse({online:true,conn:{effectiveType:"3g",rtt:2100,downlink:1}}),
 conn_dl:_netzKlasse({online:true,conn:{effectiveType:"3g",rtt:300,downlink:0.1}}),
 dreiG:_netzKlasse({online:true,conn:{effectiveType:"3g",rtt:300,downlink:1.5,saveData:true}}),
 offline:_netzKlasse({online:false,rttMs:200}),
 leer:_netzKlasse()
};
R.text=[_netzPingText(0),_netzPingText(240),_netzPingText(11000),_netzPingText(3450),
 _netzStatusText("schwach",11000),_netzStatusText("schwach",0),_netzStatusText("offline",0),_netzStatusText("gut",200)];
R.abstand=[_netzAbstandOk(0,1000,60000),_netzAbstandOk(1000,30000,60000),_netzAbstandOk(1000,61000,60000)];
R.server=[_netzServerDa(100000,50000,90000),_netzServerDa(200000,50000,90000),_netzServerDa(100000,0,90000)];
R.erg={
 ok:_syncErgebnisText({art:"ok",ok:0,offen:0,fotos:0}),
 okRest:_syncErgebnisText({art:"ok",ok:3,offen:0,fotos:2}),
 fehler:_syncErgebnisText({art:"fehler",grund:"zeit",offen:4,fotos:1,naechsterMs:15000}),
 fehlerEins:_syncErgebnisText({art:"fehler",grund:"netz",offen:1,naechsterMs:5000}),
 offline:_syncErgebnisText({art:"offline",offen:2}),
 anmeldung:_syncErgebnisText({art:"anmeldung",offen:2}),
 laeuft:_syncErgebnisText({art:"laeuft"}),
 teil:_syncErgebnisText({art:"teil",ok:2,offen:1})
};
process.stdout.write(JSON.stringify(R));
"""


def _rein(src, node_exe):
    return json.loads(run_node_snippet(node_exe, _fns(src, REIN) + "\n" + REIN_KOERPER))


def _rein_befunde(r):
    b = []
    if r["backoff"] != [1500, 4000, 4000, 4000]:
        b.append("Lese-Wartezeiten %r" % r["backoff"])
    if r["pause"] != [5000, 5000, 15000, 30000, 60000, 120000, 300000, 300000]:
        b.append("Warteschlangen-Pausen %r" % r["pause"])
    if r["lese"] != [30000, 30000, 55000, 60000, 30000]:
        b.append("Lese-Zeitgrenze %r (nie unter 30 s, 5x Antwortzeit, hoechstens 60 s)" % r["lese"])
    if r["herz"] != [10000, 8000, 15000, 25000]:
        b.append("Lebenszeichen-Zeitgrenze %r" % r["herz"])
    if r["upload"] != [60000, 60000, 120000, 300000]:
        b.append("Upload-Zeitgrenze %r" % r["upload"])
    soll = {"chromeZeit": "zeit", "safariZeit": "zeit", "abbruch": "zeit", "chromeNetz": "netz", "safariNetz": "netz",
            "firefoxNetz": "netz", "dns": "netz", "offline": "offline", "s503": "server", "s429": "server",
            "s400timeout": "", "s409": "", "auth401": "", "programm": "", "leer": ""}
    for k, v in soll.items():
        if r["art"].get(k) != v:
            b.append("Fehlerart %s = %r statt %r" % (k, r["art"].get(k), v))
    if r["transient"] != [True, False]:
        b.append("transient %r" % r["transient"])
    if r["nochmal"] != [True, True, False, True, False, False, False, False]:
        b.append("Wiederholungsregel Lesen %r" % r["nochmal"])
    if r["median"] != [0, 300, 900, 200, 400]:
        b.append("Median %r" % r["median"])
    ks = {"gut": "gut", "tablet": "schwach", "grenze": "gut", "zeitfehler": "schwach", "edge": "schwach",
          "conn_rtt": "schwach", "conn_dl": "schwach", "dreiG": "gut", "offline": "offline", "leer": "gut"}
    for k, v in ks.items():
        if r["klasse"].get(k) != v:
            b.append("Klasse %s = %r statt %r" % (k, r["klasse"].get(k), v))
    if r["text"] != ["", "240 ms", "11 s", "3,5 s", "Verbindung schwach (Ping 11 s)", "Verbindung schwach", "Offline", ""]:
        b.append("Texte %r" % r["text"])
    if any("WLAN" in t for t in r["text"]):
        b.append("Schwach-Text nennt WLAN - gilt aber auch fuer Mobilfunk")
    if r["abstand"] != [True, False, True]:
        b.append("Mindestabstand %r" % r["abstand"])
    if r["server"] != [True, False, False]:
        b.append("Server-da-Fenster %r" % r["server"])
    e = r["erg"]
    if e["ok"]["text"] != "Alles synchron – nichts offen." or e["ok"]["typ"] != "success":
        b.append("ok: %r" % e["ok"])
    if "3 übertragen" not in e["okRest"]["text"] or "2 Fotos" not in e["okRest"]["text"]:
        b.append("ok mit Rest: %r" % e["okRest"])
    f = e["fehler"]["text"]
    if not (f.startswith("Synchronisieren fehlgeschlagen: Zeitüberschreitung") and "4 Änderungen und 1 Foto bleiben gespeichert" in f
            and "neuer Versuch in 15 s" in f) or e["fehler"]["typ"] != "warn":
        b.append("fehler: %r" % e["fehler"])
    if "1 Änderung bleiben" not in e["fehlerEins"]["text"] or "Server nicht erreichbar" not in e["fehlerEins"]["text"]:
        b.append("fehler (1, netz): %r" % e["fehlerEins"])
    if not e["offline"]["text"].startswith("Offline – 2 Änderungen warten"):
        b.append("offline: %r" % e["offline"])
    if "neu anmelden" not in e["anmeldung"]["text"] or "2 Änderungen offen" not in e["anmeldung"]["text"]:
        b.append("anmeldung: %r" % e["anmeldung"])
    if "läuft bereits" not in e["laeuft"]["text"]:
        b.append("laeuft: %r" % e["laeuft"])
    if not e["teil"]["text"].startswith("Teilweise synchronisiert (2 übertragen)"):
        b.append("teil: %r" % e["teil"])
    return b


def test_reine_helfer(index_html, node_exe):
    assert _rein_befunde(_rein(index_html, node_exe)) == []


LESEN_PRELUDE = r"""
var setTimeout=(f,ms)=>{warten.push(ms);Promise.resolve().then(f);return 1;};var clearTimeout=()=>{};var warten=[];
var navigator={onLine:true};var window={dispatchEvent:()=>true};class CustomEvent{constructor(t,o){this.type=t;this.detail=(o||{}).detail;}}
"""
LESEN_KOERPER = r"""
(async()=>{
 const R={};
 async function lauf(folge){let n=0;warten=[];const fn=async()=>{const x=folge[Math.min(n,folge.length-1)];n++;
   if(x==="dns")throw new TypeError("Failed to fetch");if(x==="zeit"){const e=new Error("signal timed out");e.name="TimeoutError";throw e;}
   if(x==="prog")throw new TypeError("Cannot read properties of undefined");return {status:x,ok:x<300};};
   try{const r=await _netzLesen(fn);return {n:n,status:r.status,warten:warten.slice()};}catch(e){return {n:n,fehler:e.name,warten:warten.slice()};}}
 R.dnsEinmal=await lauf(["dns",200]);
 R.dnsImmer=await lauf(["dns"]);
 R.zeitImmer=await lauf(["zeit"]);
 R.zeitEinmal=await lauf(["zeit",200]);
 R.s400=await lauf([400]);
 R.s503=await lauf([503,503,200]);
 R.prog=await lauf(["prog",200]);
 navigator.onLine=false;R.offline=await lauf(["dns",200]);navigator.onLine=true;
 R.zeitGemerkt=_NETZ.fehler.filter(x=>x.art==="zeit").length;
 process.stdout.write(JSON.stringify(R));
})();
"""


def _lesen(src, node_exe):
    code = LESEN_PRELUDE + _netz_zustand(src) + "\n" + _fns(src, REIN + ZUSTAND) + "\n" + LESEN_KOERPER
    return json.loads(run_node_snippet(node_exe, code))


def _lesen_befunde(r):
    b = []
    if r["dnsEinmal"] != {"n": 2, "status": 200, "warten": [1500]}:
        b.append("erste DNS-Abfrage scheitert: %r" % r["dnsEinmal"])
    if r["dnsImmer"] != {"n": 3, "fehler": "TypeError", "warten": [1500, 4000]}:
        b.append("Netz dauerhaft weg: %r" % r["dnsImmer"])
    if r["zeitImmer"] != {"n": 2, "fehler": "TimeoutError", "warten": [1500]}:
        b.append("Zeitueberschreitung dauerhaft: %r" % r["zeitImmer"])
    if r["zeitEinmal"] != {"n": 2, "status": 200, "warten": [1500]}:
        b.append("Zeitueberschreitung einmal: %r" % r["zeitEinmal"])
    if r["s400"] != {"n": 1, "status": 400, "warten": []}:
        b.append("400 wird wiederholt: %r" % r["s400"])
    if r["s503"] != {"n": 3, "status": 200, "warten": [1500, 4000]}:
        b.append("503 beim Lesen: %r" % r["s503"])
    if r["prog"] != {"n": 1, "fehler": "TypeError", "warten": []}:
        b.append("Programmfehler wird wiederholt: %r" % r["prog"])
    if r["offline"]["n"] != 1:
        b.append("offline wird wiederholt: %r" % r["offline"])
    if r["zeitGemerkt"] < 3:
        b.append("Zeitueberschreitungen nicht fuer die Anzeige gemerkt: %r" % r["zeitGemerkt"])
    return b


def test_lesen_mit_wiederholung(index_html, node_exe):
    assert _lesen_befunde(_lesen(index_html, node_exe)) == []


PQ_PRELUDE = r"""
var timers=[];var setTimeout=(f,ms)=>{timers.push(ms);return timers.length;};var clearTimeout=()=>{};
var window={dispatchEvent:()=>true};class CustomEvent{constructor(t,o){this.type=t;this.detail=(o||{}).detail;}}
var navigator={onLine:true};
var mem={photoQueue:[]};var ODB={load:async k=>JSON.parse(JSON.stringify(mem[k]||[])),save:async(k,v)=>{mem[k]=JSON.parse(JSON.stringify(v));},set:async(k,_d,v)=>{mem[k]=JSON.parse(JSON.stringify(v));}};
var modus=[],up=[];
async function _sbUploadFile(path,d){const m=modus.shift()||"ok";up.push(path+"|"+m);
  if(m==="zeit"){const e=new Error("signal timed out");e.name="TimeoutError";throw e;}
  if(m==="400")throw new Error("HTTP400 Storage upload failed: bad");
  return "https://x/"+path;}
function _storagePath(c,pid,n){return "photos/"+pid+"/"+n;}
async function _sbPost(){}async function _sbInsertIfAbsent(){}/* 18.11.: PhotoQ schreibt photos idempotent */function _mapBody(b){return b;}
"""
PQ_KOERPER = r"""
(async()=>{
 const R={};
 await PhotoQ.add({entityType:"p",entityId:"1",projectId:"P",name:"a.jpg",dataUrl:"data:image/jpeg;base64,AAAA"});
 await PhotoQ.add({entityType:"p",entityId:"1",projectId:"P",name:"b.jpg",dataUrl:"data:image/jpeg;base64,BBBB"});
 for(let i=0;i<12;i++){modus=["zeit"];await PhotoQ.flush();}
 R.nachZeit=mem.photoQueue.map(x=>({n:x.name,st:x.status,r:x.retries,nf:x.netzFehler||0}));
 R.uploads=up.length;R.timer=timers.slice(0,7);
 modus=["400","ok"];await PhotoQ.flush();
 R.nach400=mem.photoQueue.map(x=>({n:x.name,st:x.status,r:x.retries}));
 modus=["ok","ok"];await PhotoQ.flush();
 R.ende=mem.photoQueue.length;
 process.stdout.write(JSON.stringify(R));
})();
"""


def _pq(src, node_exe):
    code = PQ_PRELUDE + _fns(src, ("_netzFehlerArt", "_netzPauseMs")) + "\n" + _photoq(src) + "\n" + PQ_KOERPER
    return json.loads(run_node_snippet(node_exe, code))


def _pq_befunde(r):
    b = []
    z = r["nachZeit"]
    if len(z) != 2 or z[0]["st"] != "error" or z[0]["r"] != 0 or z[0]["nf"] != 12:
        b.append("Zeitueberschreitung zaehlt gegen den 10er-Deckel oder Foto weg: %r" % z)
    if len(z) == 2 and z[1]["st"] != "pending":
        b.append("Lauf bricht bei Zeitueberschreitung nicht ab (zweites Foto angefasst): %r" % z)
    if r["uploads"] != 12:
        b.append("nach 10 Zeitueberschreitungen wird nicht mehr versucht: %r Uploads" % r["uploads"])
    if r["timer"][:6] != [5000, 15000, 30000, 60000, 120000, 300000]:
        b.append("kein geplanter naechster Versuch mit wachsender Pause: %r" % r["timer"])
    n = r["nach400"]
    if not n or n[0]["n"] != "a.jpg" or n[0]["r"] != 1:
        b.append("dauerhafter Fehler (400) zaehlt nicht mehr: %r" % n)
    if r["ende"] != 0:
        b.append("Fotos kommen nach Rueckkehr des Netzes nicht hoch: %r" % r["ende"])
    return b


def test_photoq_bei_langsamem_netz(index_html, node_exe):
    assert _pq_befunde(_pq(index_html, node_exe)) == []


def test_verdrahtung(index_html):
    code = nur_code(index_html)
    # Lesen nur fuer GET: keine Zeile mit _netzLesen traegt eine Schreibmethode
    zeilen = [z for z in code.split("\n") if "_netzLesen(()=>" in z]
    assert len(zeilen) == 6, len(zeilen)
    for z in zeilen:
        assert not re.search(r"method:\s*['\"](POST|PATCH|PUT|DELETE)", z), z[:160]
    for n in ("_sbPost", "_sbUpsert", "_sbInsertIfAbsent", "_sbPatch", "_sbDelete", "_juprowaPush"):
        f = _extract_fn(index_html, n, rf"(?:async\s+)?function\s+{re.escape(n)}\s*\(")
        assert f and "_netzLesen" not in f, n + " wiederholt Schreiben automatisch"
    # doSync: Netzfehler bleiben in der Warteschlange - VOR dem 5er-Zaehler
    i = code.index("const doSync=async(_opt)=>{")
    blk = code[i:code.index("window.__doSync=doSync;", i)]
    assert "if(_netzArt){fail++;break;}" in blk and "const retries=(item._retries||0)+1;" in blk
    assert blk.index("if(_netzArt){fail++;break;}") < blk.index("const retries=(item._retries||0)+1;")
    assert "_netzSqPlanen()" in blk and "_netzSqZurueck()" in blk
    # die alten Riegel stehen unveraendert
    assert "const _transient=!navigator.onLine||_st>=500||_st===408||_st===429||e.message==='Failed to fetch';" in blk
    assert "if(_transient){fail++;break;}" in blk
    # Knoepfe melden ein Ergebnis
    assert code.count("{doSync({manuell:true});}") == 2
    assert "window.__doSync({manuell:true})" in code
    # Lebenszeichen: keine feste 5-s-Grenze mehr, Antwortzeit gemessen
    assert "AbortSignal.timeout(5000)" not in code
    assert "AbortSignal.timeout(_netzHerzMs())" in code and "_netzProbe(Date.now()-_hb0)" in code
    # Uploads: Zeitgrenze nach Groesse
    assert code.count("_netzUploadMsFuer(blob.size)") == 5
    # Anzeige: bernstein, neutraler Text, Hinweis mit Linien-Ikone
    assert code.count('schwach:syncStatus.netz==="schwach"') == 2
    assert code.count('_netzStatusText("schwach",syncStatus.netzPing)') == 2
    assert '_ik("verbindung",14)' in code
    # Rueckkehr in die App stoesst an
    assert 'document.addEventListener("visibilitychange",onVisSync)' in code


# ══ Umkehrproben ═════════════════════════════════════════════════════════════

REIN_RUECKBAU = [
    ('if(nm==="TimeoutError"||nm==="AbortError"||/timed out/i.test(m))return "zeit";', ""),
    ('m==="Failed to fetch"||m==="Load failed"||', 'm==="Failed to fetch"||'),
    ('if(h){var s=+h[1];return (s>=500||s===408||s===429)?"server":"";}', ""),
    ('if((+s.rttMs||0)>3000||(+s.zeitFehler||0)>0)return "schwach";', ""),
    ('if(c.effectiveType==="slow-2g"||c.effectiveType==="2g")return "schwach";', ""),
    ("return Math.min(60000,Math.max(b,Math.round(r*5)));", "return Math.min(30000,b);"),
    ("return Math.min(300000,Math.max(60000,Math.round(n/15)+20000));", "return 60000;"),
    ('var t=[5000,15000,30000,60000,120000,300000];', 'var t=[1000,1000,1000,1000,1000,1000];'),
    ('return "Verbindung schwach"+(p?" (Ping "+p+")":"");', 'return "WLAN verbunden";'),
]


@pytest.mark.parametrize("alt,neu", REIN_RUECKBAU)
def test_umkehrprobe_rein(index_html, node_exe, alt, neu):
    assert index_html.count(alt) == 1, "Anker: " + alt
    try:
        b = _rein_befunde(_rein(index_html.replace(alt, neu, 1), node_exe))
    except Exception as ex:
        b = [str(ex)[:200]]
    assert b, "Riegel blind fuer: " + alt


@pytest.mark.parametrize("alt,neu", [
    ('if(_netzNochmal(art,v)){await _netzSchlaf(_netzBackoffMs(v));continue;}', ""),
    ('if(art==="netz")return v<2;', ""),
    ('if(art==="netz")return v<2;', 'if(art==="netz"||art==="")return v<2;'),
])
def test_umkehrprobe_lesen(index_html, node_exe, alt, neu):
    assert index_html.count(alt) == 1, "Anker: " + alt
    try:
        b = _lesen_befunde(_lesen(index_html.replace(alt, neu, 1), node_exe))
    except Exception as ex:
        b = [str(ex)[:200]]
    assert b, "Riegel blind fuer: " + alt


@pytest.mark.parametrize("alt,neu", [
    ('if(_pqArt==="zeit"||_pqArt==="netz"){await PhotoQ.update(ph.id,{retries:ph.retries||0,netzFehler:(ph.netzFehler||0)+1});}', ""),
    ('||_pqArt==="zeit"||_pqArt==="netz"){_pqAbbruch=true;break;}}', '){_pqAbbruch=true;break;}}'),
    ("try{if(_pqAbbruch){", "try{if(false){"),
])
def test_umkehrprobe_photoq(index_html, node_exe, alt, neu):
    assert index_html.count(alt) == 1, "Anker: " + alt
    try:
        b = _pq_befunde(_pq(index_html.replace(alt, neu, 1), node_exe))
    except Exception as ex:
        b = [str(ex)[:200]]
    assert b, "Riegel blind fuer: " + alt


@pytest.mark.parametrize("alt,neu", [
    ("if(_netzArt){fail++;break;}", ""),
    ("AbortSignal.timeout(_netzHerzMs())", "AbortSignal.timeout(5000)"),
    ("onClick: ()=>{doSync({manuell:true});}, disabled: syncStatus.syncing||!syncStatus.connected,",
     "onClick: ()=>{doSync();}, disabled: syncStatus.syncing||!syncStatus.connected,"),
])
def test_umkehrprobe_verdrahtung(index_html, alt, neu):
    assert alt in index_html, "Anker: " + alt
    with pytest.raises(AssertionError):
        test_verdrahtung(index_html.replace(alt, neu))
