# -*- coding: utf-8 -*-
"""Verhaltenstests fuer den Schein-Abgleich mit der Auftragsverwaltung (B #18, #21, #22 aus dem Mutationslauf B,
26.11.2026, Stand 3.9.1122). Neue Datei, weil die bestehenden Abgleich-Testdateien ohne eigene GF-Freigabe nicht
geaendert werden duerfen (Tor 7). Nur Tests, index.html bleibt unveraendert (GF-Freigabe 26.11. abends).

Jeder Test schneidet den ECHTEN Code aus index.html und fuehrt ihn in node aus. Mutationsprobe siehe
epk-tiefenpruefung-2026-11-26/B_mutation.md, Abschnitt "Lohn-/OFFA-Tests geschaerft 26.11.".
"""
import json
import os
import shutil
import subprocess
import tempfile

import pytest

NODE = shutil.which("node")
needs_node = pytest.mark.skipif(not NODE, reason="node fehlt")


def _block(src, kopf, ende):
    assert src.count(kopf) == 1, "Anker nicht eindeutig: " + kopf[:80]
    i = src.index(kopf)
    return src[i:src.index(ende, i + len(kopf)) + len(ende)]


def _zeile(src, anfang):
    assert src.count(anfang) == 1, "Anker nicht eindeutig: " + anfang[:80]
    i = src.index(anfang)
    return src[i:src.index("\n", i)]


def _node(js):
    fd, pfad = tempfile.mkstemp(suffix=".js", prefix="abgl_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(js)
        r = subprocess.run([NODE, pfad], capture_output=True, text=True, encoding="utf-8", timeout=120)
    finally:
        os.remove(pfad)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def _sanitize(src):
    return _block(src, "function _juprowaSanitize(s){", "\n}")


# ── B #18  Text fuer die Cloud: JEDES Sonderzeichen ersetzt, nicht nur das erste ──
# Regel: Kommentar "Sanitize text for Juprowa Cloud (Latin-1 only - no em-dash, euro, etc.)" - nach dem Ersetzen darf
# kein Zeichen ausserhalb Latin-1 der Liste uebrig bleiben, egal wie oft es vorkommt.
# Mutation (B #18): Gedankenstrich nur einmal ersetzt (/—/g -> /—/).
@needs_node
def test_b18_sanitize_ersetzt_jedes_vorkommen(index_html):
    ein = ("Kabel — Dose — Schalter – Lampe – Ende ‘a’ ‘b’ “q” “r” "
           "€5 €7 x…y… 1 2 3")
    js = _sanitize(index_html) + "\nconsole.log(JSON.stringify([_juprowaSanitize(%s),_juprowaSanitize(%s),_juprowaSanitize(%s),_juprowaSanitize(%s)]));" % (
        json.dumps(ein), json.dumps("———"), json.dumps(""), json.dumps(None))
    r = _node(js)
    assert r[0] == "Kabel -- Dose -- Schalter - Lampe - Ende 'a' 'b' \"q\" \"r\" EUR5 EUR7 x...y... 1 2 3", r[0]
    assert all(ord(c) < 256 for c in r[0]), r[0]
    assert r[1] == "------", r
    assert r[2] == "" and r[3] is None, r


# ── B #21  Status-Rueckgabe: Rohwert der Auftragsverwaltung bleibt, solange er dasselbe bedeutet ──
# Regel: Kommentar in _juprowaReversMap (v3.9.570 A-2): "4 bleibt 4, 15 bleibt 15. Nur bei echter Status-Aenderung
# den Reverse senden"; analog v3.9.615 #1 fuer AK_PRIOR ("0 bleibt 0").
# Mutation (B #21): Status-Dirty-Check entfernt (immer JUPROWA_STATUS_REV).
@needs_node
def test_b21_status_rohwert_bleibt_bei_gleicher_bedeutung(index_html):
    js = "\n".join([
        "var localStorage={getItem:function(){return null;}};",
        _zeile(index_html, "const JUPROWA_WORKER_MAP="),
        _zeile(index_html, "const JUPROWA_STATUS_MAP="), _zeile(index_html, "const JUPROWA_PRIO_MAP="),
        _zeile(index_html, "const JUPROWA_PRIO_REV="), _zeile(index_html, "const JUPROWA_STATUS_REV="),
        "var _juprowaDynMap={};",
        _block(index_html, "function _juprowaWorkerToCode(workerId){", "\n}"),
        _sanitize(index_html),
        _block(index_html, "function _juprowaReversMap(schein){", "\n  return json;\n}"),
    ]) + r"""
function st(s,raw){var o={juprowa_id:5000001,nummer:"S1",scheinstatus:s};if(raw!==undefined)o.juprowa_raw={AK_AUFSTATUS:raw};
  var j=_juprowaReversMap(o);return j.AK_AUFSTATUS===undefined?null:j.AK_AUFSTATUS;}
function pr(p,raw){var o={juprowa_id:5000001,prioritaet:p};if(raw!==undefined)o.juprowa_raw={AK_PRIOR:raw};return _juprowaReversMap(o).AK_PRIOR;}
console.log(JSON.stringify({
  s:[st("bar_bezahlt",15),st("bar_bezahlt","15"),st("freigegeben",4),st("freigegeben",1),st("bar_bezahlt",11),
     st("erledigt",4),st("abgerechnet",15),st("bar_bezahlt"),st("freigegeben"),st("freigegeben",null),st("gibtsnicht",4)],
  p:[pr("keine",0),pr("keine",1),pr("hoch",0),pr("keine")]
}));"""
    r = _node(js)
    assert r["s"] == ["15", "15", "4", "1", "11", "5", "10", "11", "1", "1", None], r
    assert r["p"] == ["0", "1", "5", "1"], r


# ── B #22  Monteur-Zuweisung nur auf einen echten Mitarbeiter ───────────────
# Regel: Kommentar in updAs (v3.9.757 #31a): "eine monteur-Zuweisung muss ein realer Worker sein - gegen den
# public.workers-Mirror monteure geprueft ... Leer-Guard: nur pruefen, wenn der Mirror geladen ist".
# Mutation (B #22): Pruefung invertiert (!monteure.some( -> monteure.some().
@needs_node
def test_b22_updas_monteur_nur_echter_mitarbeiter(index_html):
    upd = _block(index_html, "const updAs=(id,updates)=>{", "\n  };")
    js = "\n".join([
        "var window={__toast:function(m){TOASTS.push(m);}};var TOASTS=[];var navigator={onLine:false};",
        _block(index_html, "const JUPROWA_PUSH_FIELDS={", "\n};"),
        _zeile(index_html, "const AS_GRP_OFFEN="),
    ]) + r"""
function lauf(monteure,updates,isAdmin,isMonteurRole){
  TOASTS=[];var SQ_LOG=[];var SQ={push:function(x){SQ_LOG.push(x);}};
  var arbeitsscheine=[{id:"s1",scheinstatus:"freigegeben",juprowa_id:5000001}];
  var setArbeitsscheine=function(){};var _juprowaSchedulePush=function(){};
  %s
  var ret=updAs("s1",updates);
  var body=SQ_LOG.length?SQ_LOG[0].body:null;
  return {ret:ret,monteur:body&&("monteur" in body)?body.monteur:"-fehlt-",notizen:body?body.notizen||null:null,toast:TOASTS.length};
}
var M=[{id:"w1",n:"Monteur A"},{id:"w2",n:"Monteur B"}];
console.log(JSON.stringify([
  lauf(M,{monteur:"w2"},true,false), lauf(M,{monteur:"x99"},true,false), lauf(M,{monteur:"x99",notizen:"n"},true,false),
  lauf([],{monteur:"x99"},true,false), lauf(M,{monteur:""},true,false), lauf(M,{monteur:"w1"},false,true)
]));""" % upd
    r = _node(js)
    ok, unbekannt, mitText, kalt, leer, alsMonteur = r
    assert ok == {"ret": True, "monteur": "w2", "notizen": None, "toast": 0}, ok
    assert unbekannt["ret"] is False and unbekannt["monteur"] == "-fehlt-" and unbekannt["toast"] == 1, unbekannt
    assert mitText["ret"] is True and mitText["monteur"] == "-fehlt-" and mitText["notizen"] == "n", mitText
    assert mitText["toast"] == 1, mitText
    assert kalt["ret"] is True and kalt["monteur"] == "x99", kalt      # Mirror leer: kein Kaltstart-Fehlalarm
    assert leer["ret"] is True and leer["monteur"] == "", leer         # Zuweisung loesen bleibt moeglich
    assert alsMonteur["ret"] is False and alsMonteur["monteur"] == "-fehlt-", alsMonteur  # Feldrolle weist nie zu
