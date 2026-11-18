# -*- coding: utf-8 -*-
"""Dateien nur im Speicher (Entscheid Sebastian 18.11.2026, Dauerregel: die Datenbank speichert nie Dateien).

Node fuehrt die ECHTEN Funktionen aus index.html aus:
  * Reine Helfer: Erkennung (data: ueber 2 kB, auch in JSON-Text wie tank_log), Ersetzen ohne Seiteneffekt,
    Ziel (Zulassungsschein -> privater Fahrzeug-Bucket, sonst epkolar-files), Bildquelle fuer den Berichtsdruck,
    Upload-Typ (docx -> octet-stream).
  * Waechter _dbOhneDateien: laedt jede Datei vor dem Schreiben hoch und ersetzt sie; ohne Datei dasselbe Objekt;
    OFFA-Ausnahme arbeitsscheine; scheitert der Upload, geht die Zeile NICHT raus.
  * Migration _dateienMigration: Probelauf schreibt nichts; Verschieben nur als Admin, nur nach bestandener
    Nachpruefung, patcht nur das eine Feld; zweiter Lauf findet nichts mehr.
Umkehrproben: jede Schutzzeile entfernt -> der Befund muss rot werden.
"""
import json
import re

import pytest

from conftest import run_node_snippet, _extract_fn

HELFER = ("_istDateiWert", "_dateiEndung", "_dateiBytes", "_dateiHash", "_dateiSicher", "_dateiJsonText",
          "_dateiSammeln", "_dateiErsetzen", "_sbPublicUrl", "_istSpeicherUrl", "_istBildQuelle", "_dateiIstPdf",
          "_dateiUploadTyp", "_dateiZiel", "_dateiQuelleSicher")
KONST = ("_DATEI_OEFFENTLICH", "_DATEI_GRENZE", "_DATEI_TAB_AUSNAHME", "_SB_FILES_MIME", "_dateiHochCache", "_DATEI_MIG_TABELLEN")

PRELUDE = r"""
var SUPABASE_URL="https://x.supabase.co",SB_BUCKET="epkolar-files",SB_FZ_BUCKET="epkolar-fahrzeuge",SB_DOCS_BUCKET="epkolar-docs",SB_GEF_BUCKET="epkolar-gefahrstoff";
var window={};var console_l=[];var console={warn:(...a)=>console_l.push(a.join(" ")),log:()=>{}};
var localStorage={getItem:()=>null,setItem:()=>{}};
const GROSS="data:image/jpeg;base64,"+"A".repeat(4000);
const GROSS2="data:application/pdf;base64,"+"B".repeat(6000);
const KLEIN="data:image/png;base64,"+"C".repeat(500);
"""


def _bundle(src, extra=()):
    teile = []
    for k in KONST:
        m = re.search(r"^const " + re.escape(k) + r"=.*$", src, re.M)
        assert m, k
        teile.append(m.group(0))
    for n in HELFER + tuple(extra):
        f = _extract_fn(src, n)
        assert f, n
        if ("async " + f[:60]) in src:  # _extract_fn beginnt bei "function" und laesst "async" weg
            f = "async " + f
        teile.append(f)
    return "\n".join(teile)


# ---------------------------------------------------------------- reine Helfer
KOERPER_HELFER = r"""
const R={};
R.gross=_istDateiWert(GROSS);R.klein=_istDateiWert(KLEIN);R.http=_istDateiWert("https://x/"+"a".repeat(3000));
const row={a:[{foto:GROSS}],tank:JSON.stringify([{id:"t1",foto:GROSS2},{id:"t2",foto:"https://x"}]),n:5,leer:null};
const f=_dateiSammeln(row);R.funde=f.length;
const map=new Map(f.map((v,i)=>[v,"URL"+i]));const neu=_dateiErsetzen(row,map);
R.neuOhneData=JSON.stringify(neu).indexOf("data:")<0;R.tankText=typeof neu.tank==="string";
R.tankUrl=JSON.parse(neu.tank)[0].foto;R.altUnveraendert=row.a[0].foto===GROSS;
const ohne={x:{y:[1,2]}};R.gleicheRef=_dateiErsetzen(ohne,map)===ohne;
R.hashGleich=_dateiHash(GROSS)===_dateiHash(GROSS);R.hashVerschieden=_dateiHash(GROSS)!==_dateiHash(GROSS+"A");
R.zul=_dateiZiel("fahrzeuge","zulassungsschein","fz1",GROSS2);R.tankZiel=_dateiZiel("fahrzeuge","tank_log","fz1",GROSS);
R.bild=[_istBildQuelle("data:image/png;base64,xx"),_istBildQuelle(SUPABASE_URL+"/storage/v1/object/public/epkolar-files/a.png"),
  _istBildQuelle(SUPABASE_URL+"/storage/v1/object/public/epkolar-files/a\".png"),_istBildQuelle("https://boese.example/a.png"),_istBildQuelle("javascript:x")];
R.typ=[_dateiUploadTyp("epkolar-files","application/vnd.openxmlformats-officedocument.wordprocessingml.document"),_dateiUploadTyp("epkolar-files","application/pdf"),_dateiUploadTyp("epkolar-fahrzeuge","image/heic")];
R.pdf=[_dateiIstPdf(R.zul.ref),_dateiIstPdf(GROSS)];
R.pdfBoese=[_dateiIstPdf("javascript:alert(1).pdf"),_dateiIstPdf("https://evil.example/x.pdf"),_dateiIstPdf(SUPABASE_URL+"/storage/v1/object/public/epkolar-files/a.pdf")];
R.src=["javascript:alert(1).pdf","https://evil.example/x.pdf","data:text/html;base64,PHNjcmlwdD4=",SUPABASE_URL+"/storage/v1/object/public/epkolar-files/a\".pdf",SUPABASE_URL+"/storage/v1/object/public/epkolar-files/a.pdf",SUPABASE_URL+"/storage/v1/object/sign/epkolar-fahrzeuge/x.pdf?token=abc","data:application/pdf;base64,JVBE","data:image/png;base64,iV"].map(_dateiQuelleSicher).map(x=>x?"ok":"");R.bytes=_dateiBytes("data:x/y;base64,QUJD");R.endung=_dateiEndung(GROSS2);
process.stdout.write(JSON.stringify(R));
"""


def _probe_helfer(src, node_exe):
    return json.loads(run_node_snippet(node_exe, PRELUDE + _bundle(src) + "\n" + KOERPER_HELFER))


def _befunde_helfer(r):
    b = []
    if not r["gross"] or r["klein"] or r["http"]:
        b.append("Erkennung falsch: gross=%s klein=%s http=%s" % (r["gross"], r["klein"], r["http"]))
    if r["funde"] != 2:
        b.append("Sammeln fand %s statt 2 (JSON-Text tank_log muss mitzaehlen)" % r["funde"])
    if not r["neuOhneData"] or not r["tankText"] or r["tankUrl"] != "URL1":
        b.append("Ersetzen unvollstaendig: %r" % {k: r[k] for k in ("neuOhneData", "tankText", "tankUrl")})
    if not r["altUnveraendert"] or not r["gleicheRef"]:
        b.append("Ersetzen veraendert das Original oder kopiert ohne Grund")
    if not (r["hashGleich"] and r["hashVerschieden"]):
        b.append("Pruefsumme nicht deterministisch/unterscheidend")
    z = r["zul"]
    if z["bucket"] != "epkolar-fahrzeuge" or not z["ref"].startswith("sbpriv:epkolar-fahrzeuge/fahrzeuge/fz1/zulassung_") or not z["ref"].endswith(".pdf"):
        b.append("Zulassungsschein-Ziel falsch: %r" % z)
    t = r["tankZiel"]
    if t["bucket"] != "epkolar-files" or not t["ref"].startswith("https://x.supabase.co/storage/v1/object/public/epkolar-files/auto/fahrzeuge/fz1/"):
        b.append("Standard-Ziel falsch: %r" % t)
    if r["bild"] != [True, True, False, False, False]:
        b.append("Bildquelle fuer den Druck falsch: %r" % r["bild"])
    if r["typ"] != ["application/octet-stream", "application/pdf", "image/heic"]:
        b.append("Upload-Typ falsch: %r" % r["typ"])
    if r["pdf"] != [True, False] or r["bytes"] != 3 or r["endung"] != "pdf":
        b.append("PDF/Bytes/Endung falsch: %r %r %r" % (r["pdf"], r["bytes"], r["endung"]))
    if r["pdfBoese"] != [False, False, True]:
        b.append("PDF-Erkennung nimmt fremde Quellen an: %r" % r["pdfBoese"])
    if r["src"] != ["", "", "", "", "ok", "ok", "ok", "ok"]:
        b.append("Unsichere Quelle erreicht src (XSS): %r" % r["src"])
    return b


def test_helfer(index_html, node_exe):
    assert _befunde_helfer(_probe_helfer(index_html, node_exe)) == []


@pytest.mark.parametrize("alt,neu", [
    ("const j=_dateiJsonText(v);if(j!==undefined)geh(j,t+1);return;}if(Array.isArray(v)){for(", "return;}if(Array.isArray(v)){for("),
    ("v.length>_DATEI_GRENZE&&", "v.length>_DATEI_GRENZE*100&&"),
    ('if(table==="fahrzeuge"&&spalte==="zulassungsschein")', "if(false)"),
    ("return _istSpeicherUrl(v)&&!/[\\x22\\x27<>\\s]/.test(v);}", "return v.indexOf(\"http\")===0;}"),
    ("if(bucket===SB_BUCKET&&!_SB_FILES_MIME[typ])return \"application/octet-stream\";", ""),
    (r'return (_istSpeicherUrl(v)||v.indexOf("sbpriv:")===0)&&/\.pdf(\?|$)/i.test(v);}', r'return /\.pdf(\?|$)/i.test(v);}'),
    (')return v;return "";}', ')return v;return v;}'),
    (r"if(/^data:(image\/[a-z0-9.+-]+|application\/pdf)[;,]/i.test(v))return v;", r"if(/^data:/i.test(v))return v;"),
])
def test_helfer_umkehrprobe(index_html, node_exe, alt, neu):
    assert index_html.count(alt) == 1, "Anker: " + alt
    try:
        b = _befunde_helfer(_probe_helfer(index_html.replace(alt, neu, 1), node_exe))
    except Exception as ex:
        b = [str(ex)[:200]]
    assert b, "Riegel blind fuer: " + alt


# ---------------------------------------------------------------- Waechter
KOERPER_WAECHTER = r"""
let hoch=[],fehler=false;
async function _sbDateiHoch(bucket,pfad,d){if(fehler)throw new TypeError("Failed to fetch");hoch.push(bucket+"|"+pfad);return d.length;}
(async()=>{
 const R={};
 const body={tank_log:JSON.stringify([{id:"t1",foto:GROSS}]),km_stand:5};
 const out=await _dbOhneDateien("fahrzeuge","fz1",body);
 R.ohneData=JSON.stringify(out).indexOf("data:")<0;R.km=out.km_stand;R.hoch=hoch.slice();
 R.original=body.tank_log.indexOf("data:")>0;
 const nichts={a:1,b:[KLEIN]};R.gleich=(await _dbOhneDateien("fahrzeuge","fz1",nichts))===nichts;
 const n0=hoch.length;await _dbOhneDateien("fahrzeuge","fz1",{tank_log:JSON.stringify([{id:"t9",foto:GROSS}])});R.cache=hoch.length===n0;
 const as={id:"as1",unterschrift_kunde:GROSS2};R.offa=(await _dbOhneDateien("arbeitsscheine","as1",as))===as&&hoch.length===n0;
 const arr=await _dbOhneDateien("checklists",null,[{id:"c1",items:[{photo:GROSS2}]},{id:"c2"}]);R.array=JSON.stringify(arr).indexOf("data:")<0&&arr.length===2;
 fehler=true;let durch=false,meld="";try{await _dbOhneDateien("werkzeuge","w1",{serviceheft:[{befund:"data:image/png;base64,"+"Z".repeat(3000)}]});durch=true;}catch(e){meld=String(e.message);}
 R.wirft=!durch;R.voruebergehend=/^HTTP503 /.test(meld);
 process.stdout.write(JSON.stringify(R));
})();
"""


def _probe_waechter(src, node_exe):
    return json.loads(run_node_snippet(node_exe, PRELUDE + _bundle(src, ("_dbOhneDateien",)) + "\n" + KOERPER_WAECHTER))


def _befunde_waechter(r):
    b = []
    if not r["ohneData"] or r["km"] != 5:
        b.append("Datei ging mit in den DB-Rumpf")
    if len(r["hoch"]) != 1 or not r["hoch"][0].startswith("epkolar-files|auto/fahrzeuge/fz1/"):
        b.append("Upload falsch: %r" % r["hoch"])
    if not r["original"]:
        b.append("Waechter veraendert das Objekt des Aufrufers")
    if not r["gleich"]:
        b.append("ohne Datei nicht dasselbe Objekt")
    if not r["cache"]:
        b.append("gleicher Inhalt zweimal hochgeladen")
    if not r["offa"]:
        b.append("Arbeitsschein-Rumpf angefasst (OFFA-Ausnahme)")
    if not r["array"]:
        b.append("Mehrzeilen-POST nicht geschuetzt")
    if not r["wirft"]:
        b.append("Upload-Fehler verschluckt - Zeile wuerde mit Base64 gesendet")
    if not r["voruebergehend"]:
        b.append("Upload-Fehler nicht als voruebergehend (HTTP503) gemeldet - Sonderwege wuerden die Aenderung still verwerfen")
    return b


def test_waechter(index_html, node_exe):
    assert _befunde_waechter(_probe_waechter(index_html, node_exe)) == []


@pytest.mark.parametrize("alt,neu", [
    ("  if(!map.size)return data;\n", "  return data;\n"),
    ("if(!_dateiHochCache.has(ck)){try{await _sbDateiHoch(z.bucket,z.pfad,v);}catch(e){",
     "{try{await _sbDateiHoch(z.bucket,z.pfad,v);}catch(e){return data;"),
    ("if(_DATEI_TAB_AUSNAHME[table]){", "if(false){"),
    ("if(Array.isArray(data)){let ch=false;", "if(false){let ch=false;"),
    ('throw new Error("HTTP503 Datei-Upload vor dem Speichern gescheitert ("+m.slice(0,160)+")");', "throw e;"),
])
def test_waechter_umkehrprobe(index_html, node_exe, alt, neu):
    assert index_html.count(alt) == 1, "Anker: " + alt
    try:
        b = _befunde_waechter(_probe_waechter(index_html.replace(alt, neu, 1), node_exe))
    except Exception as ex:
        b = [str(ex)[:200]]
    assert b, "Riegel blind fuer: " + alt


def _verdrahtung(src):
    b = []
    for n in ("_sbPost", "_sbUpsert", "_sbInsertIfAbsent", "_sbPatch"):
        f = _extract_fn(src, n) or ""
        rumpf = f[:f.find("fetch(")] if "fetch(" in f else ""
        if "data=await _dbOhneDateien(table," not in rumpf:
            b.append(n + " schreibt ohne Waechter")
    return b


def test_waechter_verdrahtet(index_html):
    assert _verdrahtung(index_html) == []


@pytest.mark.parametrize("n", ["_sbPost", "_sbPatch"])
def test_waechter_verdrahtet_umkehrprobe(index_html, n):
    f = _extract_fn(index_html, n)
    kaputt = index_html.replace(f, f.replace("data=await _dbOhneDateien(", "data=await (x=>x)(", 1), 1)
    assert _verdrahtung(kaputt), "Verdrahtungsprobe blind fuer " + n


# ---------------------------------------------------------------- Migration
KOERPER_MIG = r"""
const DB={fahrzeuge:[{id:"fz1",zulassungsschein:GROSS2,tank_log:JSON.stringify([{id:"t1",foto:GROSS},{id:"t2",foto:"https://x"}]),km:3},{id:"fz2",zulassungsschein:"",tank_log:"[]"}],werkzeuge:[{id:"w1",serviceheft:[]}]};
let hoch=[],patches=[],pruefOk=true,rolle="admin";
window._curUser=()=>({role:rolle});
async function _sbGet(t,f){const rows=DB[t]||[];if(f){const id=decodeURIComponent((/id=eq\.([^&]+)/.exec(f)||[])[1]||"");return JSON.parse(JSON.stringify(rows.filter(r=>r.id===id)));}return JSON.parse(JSON.stringify(rows));}
async function _sbPatch(t,id,body){patches.push({t:t,id:id,keys:Object.keys(body).sort(),data:JSON.stringify(body).indexOf("data:")>=0});const r=DB[t].find(x=>x.id===id);Object.assign(r,body);return [r];}
async function _sbDateiHoch(b,p,d){hoch.push(p);return d.length;}
async function _dateiDa(b,p,g){return pruefOk;}
const TAB=[{t:"fahrzeuge",u:1},{t:"werkzeuge",u:1}];
(async()=>{
 const R={};
 const dry=await _dateienMigration({tabellen:TAB});R.dry={dateien:dry.dateien,bytes:dry.bytes===7500,hoch:hoch.length,patches:patches.length};
 rolle="monteur";const nein=await _dateienMigration({go:true,tabellen:TAB});R.nichtAdmin={hoch:hoch.length,patches:patches.length,fehler:(nein.fehler||[]).length};
 rolle="admin";pruefOk=false;await _dateienMigration({go:true,tabellen:TAB});R.pruefFehler={patches:patches.length};
 pruefOk=true;hoch=[];const go=await _dateienMigration({go:true,tabellen:TAB});
 R.go={verschoben:go.verschoben,gepatcht:go.gepatcht,patches:patches.map(p=>p.keys.join(",")+(p.data?"+DATA":""))};
 R.zul=DB.fahrzeuge[0].zulassungsschein.slice(0,32);R.km=DB.fahrzeuge[0].km;
 const zwei=await _dateienMigration({go:true,tabellen:TAB});R.zweiter=zwei.dateien;
 process.stdout.write(JSON.stringify(R));
})();
"""


def _probe_mig(src, node_exe):
    return json.loads(run_node_snippet(node_exe, PRELUDE + _bundle(src, ("_nWort", "_dateienMigration")) + "\n" + KOERPER_MIG))


def _befunde_mig(r):
    b = []
    if r["dry"] != {"dateien": 2, "bytes": True, "hoch": 0, "patches": 0}:
        b.append("Probelauf: %r" % r["dry"])
    if r["nichtAdmin"]["hoch"] or r["nichtAdmin"]["patches"] or not r["nichtAdmin"]["fehler"]:
        b.append("Nicht-Admin konnte schreiben: %r" % r["nichtAdmin"])
    if r["pruefFehler"]["patches"]:
        b.append("Zeile umgestellt, obwohl die Nachpruefung scheiterte")
    g = r["go"]
    if g["verschoben"] != 2 or g["gepatcht"] != 2 or sorted(g["patches"]) != ["tank_log,updated_at", "updated_at,zulassungsschein"]:
        b.append("Verschieben: %r" % g)
    if r["zul"] != "sbpriv:epkolar-fahrzeuge/fahrzeu" or r["km"] != 3:
        b.append("Ergebnis in der Zeile falsch: %r km=%r" % (r["zul"], r["km"]))
    if r["zweiter"] != 0:
        b.append("zweiter Lauf fand noch %r Dateien (nicht idempotent)" % r["zweiter"])
    return b


def test_migration(index_html, node_exe):
    assert _befunde_mig(_probe_mig(index_html, node_exe)) == []


@pytest.mark.parametrize("alt,neu", [
    ('if(GO&&(!_u||_u.role!=="admin")){', "if(false){"),
    ('if(!await _dateiDa(z.bucket,z.pfad,gr))throw new Error("Nachpruefung: Datei fehlt oder Groesse falsch");', ""),
    ('if(!GO){log(tb.t+" "+row.id+" ."+sp+": "+_nWort(funde.length,"Datei","Dateien")+", "+Math.round(b/1024)+" kB");continue;}',
     'if(!GO){log("x");}'),
    ("const body={};body[sp]=neu;", "const body={...fr[0]};body[sp]=neu;"),
])
def test_migration_umkehrprobe(index_html, node_exe, alt, neu):
    assert index_html.count(alt) == 1, "Anker: " + alt
    try:
        b = _befunde_mig(_probe_mig(index_html.replace(alt, neu, 1), node_exe))
    except Exception as ex:
        b = [str(ex)[:200]]
    assert b, "Riegel blind fuer: " + alt


# ---------------------------------------------------------------- neue Datei-Wege (statisch)
def test_neue_dateiwege(index_html):
    s = index_html
    # Tank: Fehler/Offline -> PhotoQ unter demselben festen Pfad (kein Foto-Verlust, kein Base64)
    assert s.count('_dateiInPhotoQ("fahrzeuge/"+fzId+"/tank/"+_eid+".jpg",tankFoto,') == 2
    # Zulassungsschein, Werkzeug-Befund/-Rechnung, Checklisten-Foto: kein roher data:-Wert mehr in den Zustand
    assert "zulassungsschein:ev.target.result" not in s
    assert s.count("reader.onload=ev=>_zulHoch(sel,ev.target.result);") == 3
    assert "befund:ev.target.result" not in s and "rechnung:ev.target.result" not in s
    assert "photo:ev.target.result" not in s
    # Anzeige privater Verweise + Druck mit Speicher-Bildern
    assert s.count("React.createElement(DateiQuelle, {v: selFz.zulassungsschein") == 2
    assert 'if(String(url).indexOf("sbpriv:")===0)' in (_extract_fn(s, "_openFileUrl") or "")
    assert "cl=await _pdfDateienEinbetten(cl);" in (_extract_fn(s, "_genChecklistPdf") or "")
    assert "rows=await _pdfDateienEinbetten(rows);" in (_extract_fn(s, "_genBautagPdf") or "")
    assert s.count("_istBildQuelle(d.sig") == 4
    # DateiQuelle gibt nur gepruefte Quellen an img/iframe weiter (Sicherheits-Pruefung 18.11.)
    dq = _extract_fn(s, "DateiQuelle") or ""
    assert dq.count("_dateiQuelleSicher(") == 3 and "setSrc(v" not in dq and "setSrc(u" not in dq
    # Admin-Werkzeug sichtbar nur fuer Admin
    assert 'curUser.role==="admin"&&React.createElement(DateienSpeicherPanel, {})' in s


def test_sicherheit_hr_daten_nie_oeffentlich(index_html):
    """Security review 18.11. (HIGH): nur eine feste Liste unkritischer Tabellen darf in den oeffentlichen Bucket."""
    i = index_html.index("const _DATEI_OEFFENTLICH={")
    liste = index_html[i:index_html.index("};", i)]
    for hr in ("absence_files", "bescheinigungen", "fahrbewilligungen", "anmeldungen", "workers", "finkzeit", "users", "gefahrstoff"):
        assert hr not in liste, hr
    z = index_html[index_html.index("function _dateiZiel("):]
    z = z[:z.index("\n")]
    assert "if(_DATEI_OEFFENTLICH[table])return{bucket:SB_BUCKET" in z
    assert z.rstrip().endswith('return{bucket:SB_DOCS_BUCKET,pfad:p,ref:"sbpriv:"+SB_DOCS_BUCKET+"/"+p};}')


def test_umkehrprobe_hr_oeffentlich_wird_rot(index_html):
    kaputt = index_html.replace("const _DATEI_OEFFENTLICH={", "const _DATEI_OEFFENTLICH={fahrbewilligungen:1,", 1)
    i = kaputt.index("const _DATEI_OEFFENTLICH={")
    assert "fahrbewilligungen" in kaputt[i:kaputt.index("};", i)]


def test_sicherheit_duplikat_byteweise(index_html):
    """Security review 18.11. (MEDIUM): vorhandenes Objekt wird Byte fuer Byte verglichen, nicht nur die Groesse."""
    d = index_html[index_html.index("async function _dateiDa(bucket,pfad,groesse,vergleich){"):]
    d = d[:d.index("\n")]
    assert "if(a[i]!==c[i])return false;" in d
    assert "&&await _dateiDa(bucket,pfad,blob.size,blob))return blob.size;" in index_html


def test_umkehrprobe_duplikat_nur_groesse(index_html):
    kaputt = index_html.replace("&&await _dateiDa(bucket,pfad,blob.size,blob))", "&&await _dateiDa(bucket,pfad,blob.size))", 1)
    assert "&&await _dateiDa(bucket,pfad,blob.size,blob))return blob.size;" not in kaputt
