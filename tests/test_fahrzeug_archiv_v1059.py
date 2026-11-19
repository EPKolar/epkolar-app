# -*- coding: utf-8 -*-
"""v3.9.1059 - Fahrzeuge archivieren statt hart loeschen (GF-Entscheidung 19.11.2026).

Anlass: am 19.11.2026 wurden fz6 (TU-516CP) und fz3 (TU-545BC) ueber den Loeschen-Knopf hart aus
fahrzeuge geloescht - Tankbuch/km-Log/Schaeden/Serviceheft stehen IN der Zeile und waren mit weg.

Gemessen wird mit Node am ECHTEN Code, der aus index.html GESCHNITTEN wird (Zaehl-Assert auf jeden
Anker), nicht an einer Abschrift:
  * reine Helfer (_fzArchiviert/_fzNurAktiv/_fzNurArchiv/_fzArchivBody/_fzOhneArchiv/_fzArchivFehlerText)
  * FzArchivPanel (Admin-Archiv) mit Attrappen-React
  * die Schreibwege _fzArchivSetzen/del/wiederherstellen aus FahrzeugView: PATCH statt DELETE, ehrliche
    Meldung wenn die Spalte fehlt, NIE Rueckfall auf DELETE, nur Admin, Bestaetigung (danger/Abbrechen).
Dazu statische Pruefungen (Wurzel reicht fahrzeugeAktiv weiter) und die SQL-Entwuerfe (IDEMPOTENT,
kein CASCADE, Rollback vorhanden, Platzhalter statt erfundener Werte).
Jede Zusicherung hat eine Gegenprobe, die zeigt, dass der Melder anschlaegt.
"""
import io
import json
import re
import subprocess
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
INDEX = WURZEL / "index.html"
SQL = WURZEL / "sql"


def _q():
    return io.open(INDEX, encoding="utf-8", newline="").read()


def _schnitt(q, a, e):
    assert q.count(a) == 1, "Anker %d-mal: %r" % (q.count(a), a)
    i = q.index(a)
    j = q.index(e, i)
    return q[i:j + len(e)]


def _helfer(q):
    return _schnitt(q, "function _fzArchiviert(f){", "/* @FZ-ARCHIV-END */")


def _schreibwege(q):
    return _schnitt(q, "  const _fzArchivSetzen=async(id,archivieren)=>{", "    await _fzArchivSetzen(id,false);};")


STUBS = r"""
"use strict";
var window={};
var V={tx:"#111",dm:"#555",bd:"#ddd",cd:"#fff"};
var UI={fMeta:12};
function bsS(){return {padding:"9px 18px",fontSize:13,minHeight:44};}
function CC(){return {background:"#fff",padding:18};}
var React={createElement:function(t,p){var k=[].slice.call(arguments,2);return {t:t,p:p||{},k:k};}};
"""


def _node(prog, tmp_path, name):
    f = tmp_path / name
    f.write_text(prog, encoding="utf-8")
    r = subprocess.run(["node", str(f)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


HELFER_PROBE = r"""
var out={};
var iso="2026-11-19T13:20:00.000Z";
out.arch=[_fzArchiviert(null),_fzArchiviert({}),_fzArchiviert({archiviert_am:null}),_fzArchiviert({archiviert_am:""}),
          _fzArchiviert({archiviert_am:"  "}),_fzArchiviert({archiviert_am:iso}),_fzArchiviert({archiviert_am:undefined})];
var l=[{id:"a"},{id:"b",archiviert_am:iso},{id:"c",archiviert_am:null},{id:"d",archiviert_am:iso}];
out.aktiv=_fzNurAktiv(l).map(function(f){return f.id;});
out.archiv=_fzNurArchiv(l).map(function(f){return f.id;});
out.leer=[_fzNurAktiv(null).length,_fzNurArchiv(undefined).length];
out.body1=_fzArchivBody(true,"Sebastian",iso);
out.body2=_fzArchivBody(true,null,iso);
out.body3=_fzArchivBody(true,"  ",iso);
out.body4=_fzArchivBody(false,"Sebastian",iso);
var b={kmStand:5,archiviert_am:null,archiviert_von:null};
var o=_fzOhneArchiv(b);
out.ohne=o;out.ohneUnveraendert=("archiviert_am" in b);
var t={tankLog:[]};out.gleich=(_fzOhneArchiv(t)===t);
out.fSpalte=_fzArchivFehlerText(new Error("HTTP400 {code:PGRST204, message:Could not find the archiviert_am column of fahrzeuge in the schema cache}"),true);
out.fSpalte2=_fzArchivFehlerText(new Error('HTTP400 {"code":"42703","message":"column fahrzeuge.archiviert_von does not exist"}'),false);
out.fLeer=_fzArchivFehlerText(null,true,true);
out.fAdmin=_fzArchivFehlerText(new Error('HTTP400 Fahrzeug fz1: Archivieren/Wiederherstellen ist nur fuer Admin erlaubt.'),true);
out.fNetz=_fzArchivFehlerText(new Error("Failed to fetch"),true);
out.zeile=_fzArchivZeile({marke:"VW",modell:"Crafter",archiviert_am:"2026-11-19T10:00:00Z",archiviert_von:"Sebastian"});
console.log(JSON.stringify(out));
"""


def _helfer_lauf(tmp_path, quelle):
    return _node(STUBS + quelle + "\n" + HELFER_PROBE, tmp_path, "helfer.js")


def test_helfer_echt(tmp_path):
    r = _helfer_lauf(tmp_path, _helfer(_q()))
    assert r["arch"] == [False, False, False, False, False, True, False]
    assert r["aktiv"] == ["a", "c"] and r["archiv"] == ["b", "d"]
    assert r["leer"] == [0, 0]
    assert r["body1"] == {"archiviert_am": "2026-11-19T13:20:00.000Z", "archiviert_von": "Sebastian"}
    # wer unbekannt -> NULL, nichts erfunden
    assert r["body2"]["archiviert_von"] is None and r["body3"]["archiviert_von"] is None
    assert r["body4"] == {"archiviert_am": None, "archiviert_von": None}
    assert r["ohne"] == {"kmStand": 5} and r["ohneUnveraendert"] is True and r["gleich"] is True
    assert r["fSpalte"] == "Archivieren ist erst nach dem DB-Update möglich – Fahrzeug bleibt bestehen"
    assert r["fSpalte2"].startswith("Wiederherstellen ist erst nach dem DB-Update")
    assert "keine Berechtigung" in r["fLeer"]
    assert "nur für Admin" in r["fAdmin"]
    assert r["fNetz"].startswith("Archivieren fehlgeschlagen – Fahrzeug bleibt bestehen")
    assert r["zeile"] == "VW Crafter · archiviert am 19.11.2026 von Sebastian"


def test_helfer_umkehrprobe(tmp_path):
    q = _helfer(_q())
    alt = 'function _fzArchiviert(f){return !!(f&&f.archiviert_am!=null&&String(f.archiviert_am).trim()!=="");}'
    assert q.count(alt) == 1
    kaputt = q.replace(alt, "function _fzArchiviert(f){return false;}")
    r = _helfer_lauf(tmp_path, kaputt)
    assert r["archiv"] != ["b", "d"]  # der Melder schlaegt an


PANEL_PROBE = r"""
function texte(n,acc){if(n==null||n===false)return acc;if(typeof n==="string"||typeof n==="number"){acc.push(String(n));return acc;}
  if(Array.isArray(n)){n.forEach(function(x){texte(x,acc);});return acc;}(n.k||[]).forEach(function(x){texte(x,acc);});return acc;}
function knoepfe(n,acc){if(!n||typeof n!=="object")return acc;if(Array.isArray(n)){n.forEach(function(x){knoepfe(x,acc);});return acc;}
  if(n.t==="button")acc.push(n);(n.k||[]).forEach(function(x){knoepfe(x,acc);});return acc;}
function schriften(n,acc){if(!n||typeof n!=="object")return acc;if(Array.isArray(n)){n.forEach(function(x){schriften(x,acc);});return acc;}
  var st=n.p&&n.p.style;if(st&&st.fontSize!=null)acc.push(st.fontSize);(n.k||[]).forEach(function(x){schriften(x,acc);});return acc;}
var out={};var gerufen=[];var offen=null;
var liste=[{id:"fz3",kennzeichen:"TU-545BC",marke:"VW",modell:"Crafter",archiviert_am:"2026-11-19T10:00:00Z",archiviert_von:"Sebastian"}];
var zu=FzArchivPanel({liste:liste,offen:false,setOffen:function(v){offen=v;},onWiederherstellen:function(id){gerufen.push(id);}});
out.zuText=texte(zu,[]).join("|");
knoepfe(zu,[])[0].p.onClick();out.offen=offen;
var auf=FzArchivPanel({liste:liste,offen:true,setOffen:function(v){offen=v;},onWiederherstellen:function(id){gerufen.push(id);}});
out.aufText=texte(auf,[]).join("|");
var k=knoepfe(auf,[]);out.knopfMin=k.map(function(b){return b.p.style.minHeight;});
k.filter(function(b){return texte(b,[]).join("")==="Wiederherstellen";})[0].p.onClick();out.gerufen=gerufen;
out.schriften=schriften(auf,[]);
var leer=FzArchivPanel({liste:[],offen:true,setOffen:function(){},onWiederherstellen:function(){}});
out.leerText=texte(leer,[]).join("|");
console.log(JSON.stringify(out));
"""


def test_archiv_panel(tmp_path):
    r = _node(STUBS + _helfer(_q()) + "\n" + PANEL_PROBE, tmp_path, "panel.js")
    assert r["zuText"] == "Archiv (1)"
    assert r["offen"] is True
    assert "TU-545BC" in r["aufText"] and "Wiederherstellen" in r["aufText"]
    assert "archiviert am 19.11.2026 von Sebastian" in r["aufText"]
    assert r["gerufen"] == ["fz3"]
    assert all(m >= 44 for m in r["knopfMin"]) and len(r["knopfMin"]) == 2
    assert r["schriften"] and all(f >= 12 for f in r["schriften"])
    assert "Keine archivierten Fahrzeuge." in r["leerText"]


SCHREIB_HARNESS = r"""
var aufrufe={patch:[],sq:[],fetch:[],confirm:[],toast:[],sel:[]};
var MODUS=%(modus)s, BESTAETIGT=%(bestaetigt)s, ADMIN=%(admin)s;
var SQ={push:function(x){aufrufe.sq.push(x);}};
function fetch(u,o){aufrufe.fetch.push([u,o&&o.method]);return Promise.resolve({ok:true,json:function(){return [];}});}
async function _sbDelete(t,id){aufrufe.sq.push({url:"/api/"+t+"/"+id,method:"DELETE"});return {ok:1};}
async function _sbPatch(t,id,b){aufrufe.patch.push([t,id,b]);
  if(MODUS==="spalte")throw new Error("HTTP400 {code:PGRST204, message:Could not find the archiviert_am column of fahrzeuge in the schema cache}");
  if(MODUS==="leer")return [];
  return [Object.assign({id:id},b)];}
async function _confirmModal(m,o){aufrufe.confirm.push([m,o]);return BESTAETIGT;}
window.__toast=function(m,t){aufrufe.toast.push([m,t||""]);};
var zustand=[{id:"fz3",kennzeichen:"TU-545BC"},{id:"fz4",kennzeichen:"TU-1"}];
function setFahrzeuge(fn){zustand=typeof fn==="function"?fn(zustand):fn;}
var fahrzeugeAlle=zustand;var sel="fz3";function setSel(v){aufrufe.sel.push(v);}
var curUser={role:ADMIN?"admin":"projektleiter",name:"Sebastian",id:"u1"};
var isFzArchivAdmin=!!(curUser&&curUser.role==="admin");
%(code)s
(async function(){
  await %(aktion)s;
  console.log(JSON.stringify({a:aufrufe,z:zustand}));
})().catch(function(e){console.log(JSON.stringify({fehler:String(e)}));});
"""


def _schreib(tmp_path, modus="ok", bestaetigt=True, admin=True, aktion='del("fz3")', code=None):
    q = _q()
    prog = STUBS + _helfer(q) + "\n" + SCHREIB_HARNESS % {
        "modus": json.dumps(modus), "bestaetigt": "true" if bestaetigt else "false",
        "admin": "true" if admin else "false", "code": code if code is not None else _schreibwege(q), "aktion": aktion}
    r = _node(prog, tmp_path, "schreib_%s.js" % modus)
    assert "fehler" not in r, r
    return r


def _deletes(r):
    return [x for x in r["a"]["sq"] if x.get("method") == "DELETE"] + [x for x in r["a"]["fetch"] if x[1] == "DELETE"]


def test_archivieren_erfolg(tmp_path):
    r = _schreib(tmp_path)
    assert len(r["a"]["patch"]) == 1
    t, i, b = r["a"]["patch"][0]
    assert (t, i) == ("fahrzeuge", "fz3")
    assert b["archiviert_von"] == "Sebastian" and re.match(r"^\d{4}-\d\d-\d\dT", b["archiviert_am"])
    assert _deletes(r) == []
    fz3 = [f for f in r["z"] if f["id"] == "fz3"][0]
    assert fz3["archiviert_am"] == b["archiviert_am"]
    assert r["a"]["sel"] == [None]
    m, o = r["a"]["confirm"][0]
    assert "TU-545BC" in m and "archivieren" in m
    assert o["variant"] == "danger" and o["cancelLabel"] == "Abbrechen" and o["confirmLabel"] == "Archivieren"


def test_spalte_fehlt_ehrlich_kein_delete(tmp_path):
    r = _schreib(tmp_path, modus="spalte")
    assert _deletes(r) == []
    assert r["a"]["toast"] == [["Archivieren ist erst nach dem DB-Update möglich – Fahrzeug bleibt bestehen", "error"]]
    assert all("archiviert_am" not in f for f in r["z"]) and len(r["z"]) == 2
    assert r["a"]["sel"] == []


def test_null_zeilen_ist_kein_erfolg(tmp_path):
    r = _schreib(tmp_path, modus="leer")
    assert _deletes(r) == []
    assert len(r["a"]["toast"]) == 1 and "keine Berechtigung" in r["a"]["toast"][0][0]
    assert all("archiviert_am" not in f for f in r["z"])


def test_nur_admin_und_nur_nach_bestaetigung(tmp_path):
    r = _schreib(tmp_path, admin=False)
    assert r["a"]["patch"] == [] and r["a"]["confirm"] == []
    r = _schreib(tmp_path, bestaetigt=False)
    assert r["a"]["patch"] == [] and len(r["a"]["confirm"]) == 1


def test_wiederherstellen(tmp_path):
    r = _schreib(tmp_path, aktion='wiederherstellen("fz3")')
    assert r["a"]["patch"][0][2] == {"archiviert_am": None, "archiviert_von": None}
    m, o = r["a"]["confirm"][0]
    assert "wiederherstellen" in m and o["cancelLabel"] == "Abbrechen"
    assert r["a"]["toast"][-1][0] == "Fahrzeug wiederhergestellt"


def test_umkehrprobe_delete_rueckfall_wird_erkannt(tmp_path):
    code = _schreibwege(_q())
    alt = 'let res;try{res=await _sbPatch("fahrzeuge",id,body);}catch(e){'
    assert code.count(alt) == 1
    kaputt = code.replace(alt, alt + 'SQ.push({url:"/api/fahrzeuge/"+id,method:"DELETE",body:{}});')
    r = _schreib(tmp_path, modus="spalte", code=kaputt)
    assert _deletes(r) != []  # der Melder schlaegt an


def test_umkehrprobe_ohne_admin_riegel(tmp_path):
    code = _schreibwege(_q())
    alt = 'const del=async(id)=>{if(!isFzArchivAdmin)return;'
    assert code.count(alt) == 1
    r = _schreib(tmp_path, admin=False, code=code.replace(alt, "const del=async(id)=>{"))
    assert r["a"]["patch"] != []


# ── statisch: Verdrahtung ──────────────────────────────────────────────────────────

def test_wurzel_reicht_nur_aktive_weiter():
    q = _q()
    assert q.count("const fahrzeugeAktiv=_react.useMemo.call(void 0, ()=>_fzNurAktiv(fahrzeuge),[fahrzeuge]);") == 1
    # v3.9.1062: Arbeitsansichten bleiben aktiv; Auswertung, Bueroexport und Mitarbeiter (nur Fahrtenbuch-Panel)
    # bekommen die volle Liste, damit vergangene Kosten/Fahrten archivierter Fahrzeuge nicht verschwinden
    # (Verhalten gemessen in test_archiv_historie_v1062.py).
    for comp in ["HomeView", "ChefDashboard", "WeekPlan", "FlotteView"]:
        i = q.index("React.createElement(%s, {" % comp)
        teil = q[i:q.index("\n", i)]
        assert "fahrzeuge: fahrzeugeAktiv," in teil and "fahrzeuge: fahrzeuge," not in teil, comp
    for comp in ["MitarbeiterView", "AuswertungView", "VBueroExport"]:
        i = q.index("React.createElement(%s, {" % comp)
        teil = q[i:q.index("\n", i)]
        assert "fahrzeuge: fahrzeuge," in teil and "fahrzeugeAktiv" not in teil, comp
    i = q.index("React.createElement(FahrzeugView, {")
    assert "fahrzeuge: fahrzeuge, setFahrzeuge: setFahrzeuge" in q[i:i + 120]  # nur hier die volle Liste (Admin-Archiv)
    assert "WochenplanTafel,{wpHistory:wpHistory,monteure:monteure,fahrzeuge:fahrzeugeAktiv," in q
    assert "_fzRef.current=fahrzeugeAktiv;" in q


def test_fahrzeugview_kein_loeschweg_mehr():
    q = _q()
    a = q.index("function FahrzeugView({fahrzeuge:fahrzeugeAlle,")
    e = q.index("\nfunction ", a + 10)
    v = q[a:e]
    assert 'method:"DELETE"' not in v.replace('/api/fz-termine/"+tid,method:"DELETE"', "")
    assert '_sbDelete("fahrzeuge"' not in q
    assert "React.createElement('button', { onClick: ()=>del(sel), style: {...bsS(),minHeight:44}}, \"Archivieren\" )" in v
    assert "isFzArchivAdmin&&React.createElement('button', { onClick: ()=>del(sel)" in v
    assert '"Löschen" )' not in v[v.index("onClick: ()=>del(sel)") - 200:v.index("onClick: ()=>del(sel)") + 200]
    assert 'SQ.push({url:"/api/fahrzeuge/"+id,method:"PUT",body:_fzOhneArchiv(_body)});' in v
    assert "React.createElement(FzArchivPanel, {liste: archivFz," in v
    # die Ansicht arbeitet auf der gefilterten Liste; die Signatur benennt die volle um
    assert "const fahrzeuge=_react.useMemo.call(void 0, ()=>_fzNurAktiv(fahrzeugeAlle),[fahrzeugeAlle]);" in v


def test_keine_tageskonstante_im_neuen_code():
    q = _q()
    assert "86400000" not in _helfer(q) and "86400000" not in _schreibwege(q)


# ── SQL-Entwuerfe ──────────────────────────────────────────────────────────────────

ENTWUERFE = ["FAHRZEUG_ARCHIV_v1059_ENTWURF.sql", "FAHRZEUG_RESTORE_fz3_fz6_v1059_ENTWURF.sql"]


def _ohne_kommentare(t):
    return "\n".join(z.split("--", 1)[0] for z in t.splitlines())


def _sql_maengel(text):
    m = []
    if not text.startswith("-- IDEMPOTENT"):
        m.append("kein IDEMPOTENT-Kopf")
    if re.search(r"\bcascade\b", _ohne_kommentare(text), re.I):
        m.append("CASCADE")
    return m


@pytest.mark.parametrize("name", ENTWUERFE)
def test_sql_entwurf_und_rollback(name):
    t = io.open(SQL / name, encoding="utf-8").read()
    assert _sql_maengel(t) == []
    rb = SQL / name.replace("_ENTWURF.sql", "_ROLLBACK.sql")
    assert rb.exists()
    assert _sql_maengel(io.open(rb, encoding="utf-8").read()) == []


def test_sql_melder_umkehrprobe():
    assert "CASCADE" in _sql_maengel("-- IDEMPOTENT\nDROP TABLE x CASCADE;")
    assert "kein IDEMPOTENT-Kopf" in _sql_maengel("BEGIN;")
    assert _sql_maengel("-- IDEMPOTENT\n-- kein CASCADE im Kommentar\nSELECT 1;") == []


def test_sql_archiv_inhalt():
    t = _ohne_kommentare(io.open(SQL / "FAHRZEUG_ARCHIV_v1059_ENTWURF.sql", encoding="utf-8").read())
    assert re.search(r"ADD COLUMN IF NOT EXISTS archiviert_am\s+timestamptz NULL;", t)
    assert re.search(r"ADD COLUMN IF NOT EXISTS archiviert_von\s+text\s+NULL;", t)
    assert "DEFAULT" not in t.upper().split("ADD COLUMN IF NOT EXISTS ARCHIVIERT_AM")[1].split(";")[0]
    assert "BEFORE DELETE ON public.fahrzeuge" in t and "ERRCODE = '23001'" in t
    assert "coalesce(public.auth_role(), '') <> 'admin'" in t
    assert "WHERE f.archiviert_am IS NULL" in t
    assert not re.search(r"\b(delete\s+from|update\s+public\.fahrzeuge\s+set|drop\s+policy)\b", t, re.I)


def test_sql_restore_erfindet_nichts():
    roh = io.open(SQL / "FAHRZEUG_RESTORE_fz3_fz6_v1059_ENTWURF.sql", encoding="utf-8").read()
    t = _ohne_kommentare(roh)
    assert t.count("<AUS_BACKUP") >= 4 and "Platzhalter <AUS_BACKUP...> noch nicht ersetzt" in t
    assert "schon vorhanden" in t  # Vorpruefung bricht ab, wenn fz3/fz6 existieren
    ins = t[t.index("INSERT INTO public.fahrzeuge"):]
    ins = ins[:ins.index(";")]
    assert "coalesce" not in ins.lower() and "'" not in ins  # keine Ersatzwerte, keine Literale
    assert "kein Auffuellen mit Defaults" in roh
    rb = _ohne_kommentare(io.open(SQL / "FAHRZEUG_RESTORE_fz3_fz6_v1059_ROLLBACK.sql", encoding="utf-8").read())
    loesch = re.findall(r"DELETE FROM[^;]*;", rb)
    assert loesch == ["DELETE FROM public.fahrzeuge WHERE id IN ('fz3', 'fz6');"]
