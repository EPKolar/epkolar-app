"""Monatsfreigabe (GF 24.11.2026, Nachtrag 1): schreibt die Datenbank 0 Zeilen, ist das ein Fehlschlag.

Die RLS blendet z. B. eine schon freigegebene Zeile fuer den Monteur aus -> PATCH liefert HTTP 200/204 mit 0 Zeilen.
Die App darf dann nicht "gespeichert"/"freigegeben" melden. Je ein Test fuer Freigeben (Monteur),
Beanstanden (Monteur, RPC), Admin-Freigabe (Chef-Portal) und Zurueckgeben (Buero und Admin).
"""
import io
import json
import os
import re
import subprocess
import tempfile

import pytest

from conftest import EPK_TEST_TIMEOUT

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _lies(p):
    return io.open(p, encoding="utf-8").read()


@pytest.fixture(scope="module")
def src():
    return _lies(os.path.join(ROOT, "index.html"))


def _schreib_fns(s):
    a = s.index("async function _mfSchreiben(")
    e = s.index("\nfunction _mfPatch(", a)
    e2 = s.index("\n", e + 1)
    return s[a:e2]


TREIBER = r"""
var SB_REST="https://x/rest/v1";var ANTWORT=null;var LETZTE=null;
function _fT(o){return o;}
function _sbWH(p){return {"Prefer":p};}
async function _authRetry(f){return f();}
async function fetch(url,opt){LETZTE={url:url,opt:opt};return ANTWORT;}
function antw(status,body){return {ok:status<300,status:status,
  text:async function(){return typeof body==="string"?body:JSON.stringify(body);},
  json:async function(){if(body===null)throw new Error("leer");return body;}};}
async function fall(name,status,body,aufruf){
  ANTWORT=antw(status,body);
  try{await aufruf();return {name:name,ok:true,url:LETZTE.url,prefer:LETZTE.opt.headers.Prefer};}
  catch(e){return {name:name,ok:false,msg:String(e&&e.message||e),url:LETZTE&&LETZTE.url};}
}
(async function(){
  var R=[];
  // Freigeben (Monteur), Admin-Freigabe, Zurueckgeben: alle ueber _mfPatch
  var faelle=[["freigeben",{status:"freigegeben",signatur_pfad:"monatsfreigabe/w1/x_unterschrift_1.png"}],
              ["admin_freigabe",{status:"zur_freigabe"}],
              ["zurueckgeben",{status:"in_arbeit",rueckgabe_grund:"Tag 12 pruefen"}]];
  for(var i=0;i<faelle.length;i++){
    var f=faelle[i];
    R.push(await fall(f[0]+"_null",200,[],function(){return _mfPatch("p1",f[1]);}));
    R.push(await fall(f[0]+"_eins",200,[{id:"p1"}],function(){return _mfPatch("p1",f[1]);}));
    R.push(await fall(f[0]+"_leerkoerper",204,null,function(){return _mfPatch("p1",f[1]);}));
    R.push(await fall(f[0]+"_fehler",403,{message:"permission denied"},function(){return _mfPatch("p1",f[1]);}));
  }
  // Beanstanden: RPC; die Datenbank-Funktion wirft bei 0 Zeilen (IF NOT FOUND) -> HTTP 400 -> Fehlschlag
  R.push(await fall("beanstanden_null",400,{message:"Monatsfreigabe: Abrechnung nicht zur Freigabe"},function(){return _mfSchreiben("POST","/rpc/monatsfreigabe_beanstanden",{p_id:"p1",p_grund:"Am 3. fehlt"});}));
  R.push(await fall("beanstanden_ok",204,null,function(){return _mfSchreiben("POST","/rpc/monatsfreigabe_beanstanden",{p_id:"p1",p_grund:"Am 3. fehlt"});}));
  console.log(JSON.stringify(R));
})();
"""


def _lauf(node_exe, s, mutation=None):
    code = _schreib_fns(s)
    if mutation:
        assert mutation[0] in code, mutation[0]
        code = code.replace(mutation[0], mutation[1])
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.js")
        io.open(p, "w", encoding="utf-8").write(code + "\n" + TREIBER)
        r = subprocess.run([node_exe, p], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 0, r.stderr
    return {x["name"]: x for x in json.loads(r.stdout.strip().splitlines()[-1])}


@pytest.mark.parametrize("aktion", ["freigeben", "admin_freigabe", "zurueckgeben"])
def test_null_zeilen_ist_fehlschlag(node_exe, src, aktion):
    R = _lauf(node_exe, src)
    assert R[aktion + "_null"]["ok"] is False
    assert "Nicht gespeichert" in R[aktion + "_null"]["msg"]
    assert R[aktion + "_leerkoerper"]["ok"] is False
    assert R[aktion + "_fehler"]["ok"] is False
    assert R[aktion + "_eins"]["ok"] is True
    assert R[aktion + "_eins"]["prefer"] == "return=representation"
    assert "select=id" in R[aktion + "_eins"]["url"]


def test_beanstanden_null_zeilen_ist_fehlschlag(node_exe, src):
    R = _lauf(node_exe, src)
    assert R["beanstanden_null"]["ok"] is False
    assert "nicht zur Freigabe" in R["beanstanden_null"]["msg"]
    assert R["beanstanden_ok"]["ok"] is True
    # Datenbankseite: die RPC wirft bei 0 Zeilen, sonst kaeme 204 ohne Fehler zurueck
    sql = _lies(os.path.join(ROOT, "sql", "MONATSFREIGABE_v1_ENTWURF.sql"))
    rpc = sql[sql.index("FUNCTION public.monatsfreigabe_beanstanden"):]
    rpc = rpc[:rpc.index("END $f$")]
    assert re.search(r"IF NOT FOUND THEN RAISE EXCEPTION", rpc)


def test_umkehrprobe_ohne_zeilenpruefung_waere_rot(node_exe, src):
    # Altverhalten (return=minimal, keine Pruefung): 0 Zeilen gelten als Erfolg -> genau das darf nicht sein
    R = _lauf(node_exe, src, mutation=("_mfSchreiben(\"PATCH\",\"/finkzeit?id=eq.\"+encodeURIComponent(id),body,true)",
                                      "_mfSchreiben(\"PATCH\",\"/finkzeit?id=eq.\"+encodeURIComponent(id),body)"))
    assert R["freigeben_null"]["ok"] is True  # Mutation zeigt den Fehler: 0 Zeilen = "gespeichert"


def _block_um(s, anker, laenge=1400):
    i = s.index(anker)
    return s[i:i + laenge]


def test_aktionen_melden_erfolg_erst_nach_dem_schreiben(src):
    # Monteur: Freigeben - Patch, dann Nachlesen, dann Erfolgsmeldung; Fehler -> "Freigabe fehlgeschlagen"
    b = _block_um(src, "var freigeben=async function(){")
    assert b.index("await _mfPatch(row.id,{status:\"freigegeben\"") < b.index("Monatsabrechnung freigegeben")
    assert "Freigabe fehlgeschlagen" in b
    # Monteur: Beanstanden - RPC, Erfolg erst danach
    b = _block_um(src, "var beanstanden=async function(){")
    assert b.index("/rpc/monatsfreigabe_beanstanden") < b.index("An das Büro gesendet")
    # Chef-Portal: Admin-Freigabe - Patch vor Meldung/Toast, Fehler -> Toast "Freigabe fehlgeschlagen"
    b = _block_um(src, "var freigebenEine=async function(r){", 900)
    assert b.index("await _mfPatch(r.id,{status:\"zur_freigabe\"})") < b.index("_mfMelden(")
    assert "Freigabe fehlgeschlagen" in b
    # Zurueckgeben: Chef (an Buero) und Buero (zurueck in Arbeit) ueber _mfPatch mit Fehlerzweig
    b = _block_um(src, "try{await _mfPatch(r.id,{status:\"in_arbeit\",rueckgabe_grund:g});", 500)
    assert b.index("_mfPatch") < b.index("Zurück ans Büro") and "Fehlgeschlagen" in b
    b = _block_um(src, "return tun(\"zh\"+m.id,function(){return _mfPatch(row.id,{status:\"in_arbeit\"", 300)
    assert "Zurück in Arbeit" in b
    t = _block_um(src, "var tun=async function(key,fn,ok){", 400)
    assert t.index("await fn();") < t.index("window.__toast(ok)") and "catch(e)" in t
