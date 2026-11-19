# -*- coding: utf-8 -*-
"""v3.9.1047 GF 19.11. "AS-Zeilen: Rueckfrage vor OFFA-Schreiben" - Vervollstaendigung.

Bestand (grep-first 19.11.): Die Rueckfrage `_asZeileRueckfrage` steht seit v3.9.1016 (Status,
Bestaetigt) und v3.9.1022 (Prioritaet, Monteur, Wischen) vor JEDEM Zeilen-Schreibweg, dessen Feld
in JUPROWA_PUSH_FIELDS steht. Ungefragt bleiben nur terminVorschlag (kein Push-Feld) und
sachbearbeiter (Push-Wert null = nur lokal). v1016 prueft Status/Datum am ausgefuehrten Code;
v1022 prueft Prioritaet/Monteur nur am Wortlaut. Diese Datei ergaenzt fuer Prioritaet und Monteur
den VERHALTENS-Riegel (Node): Abbrechen -> kein Schreibzugriff; Uebernehmen -> exakt dieselbe
Nutzlast wie der alte Sofort-Weg. Umkehrprobe: ohne Frage schlaegt der Riegel an.
Dazu ein Vollstaendigkeits-Riegel: jeder updAs-Aufruf in der Listenzeile mit einem Push-Feld
steht hinter der Rueckfrage.
"""
import json
import re
import subprocess

import pytest

ENDE = "/* v3.9.1022: erst nach Uebernehmen, gleiche Nutzlast */}"


def _handler(src, anfang):
    i = src.index("onChange: " + anfang)
    j = src.index(ENDE, i)
    return src[i + len("onChange: "):j + len(ENDE)]


def _prio(src):
    return _handler(src, "e=>{e.stopPropagation();const _np=e.target.value;")


def _monteur(src):
    return _handler(src, "e=>{e.stopPropagation();const _nm=e.target.value;")


def _helfer(src):
    i = src.index("function _asZeileRueckfrageText(")
    j = src.index("if(typeof window!=='undefined'){window._asZeileRueckfrageText", i)
    return src[i:j]


HARNISCH = r"""
var calls=[],log=[],antwort=true,fragen=[];
function updAs(id,updates){calls.push([id,updates]);log.push('schreib');return true;}
function _confirmModal(msg,opts){log.push('frage');fragen.push(msg);return Promise.resolve(antwort);}
var window={};
var JUPROWA_PUSH_FIELDS={monteur:'AK_MONTEUR',terminBestaetigt:'AK_TERMIN',prioritaet:'AK_PRIOR',scheinstatus:'AK_AUFSTATUS',sachbearbeiter:null};
var AS_STATUS={aufgenommen:{l:"aufgenommen"}};
var AS_PRIO={keine:{l:"keine"},hoch:{l:"hoch"},normal:{l:"normal"}};
function fdt(d){return d;}
var _hasTermin=function(t){return !!t;};
var monteure=[{id:'w1',name:'Anna Alt'},{id:'w2',name:'Bert Neu'}];
var MONT=monteure;
%(HELFER)s
var a={id:'as1',nummer:'S075483',scheinstatus:'aufgenommen',juprowa_id:'J1',prioritaet:'normal',monteur:'w1'};
var PRIO=(%(PRIO)s);
var MON=(%(MON)s);
function ev(v){return {stopPropagation:function(){},target:{value:v}};}
var ruhe=function(){return new Promise(function(r){setTimeout(r,5);});};
(async function(){
  var R={};
  calls=[];log=[];antwort=false;PRIO(ev('hoch'));await ruhe();R.prio_abbr=calls;R.prio_abbr_log=log.slice();
  calls=[];log=[];antwort=true;PRIO(ev('hoch'));R.prio_sofort=calls.length;await ruhe();R.prio_ok=calls;R.prio_ok_log=log.slice();
  calls=[];log=[];antwort=false;MON(ev('w2'));await ruhe();R.mon_abbr=calls;
  calls=[];log=[];antwort=true;MON(ev('w2'));R.mon_sofort=calls.length;await ruhe();R.mon_ok=calls;R.mon_ok_log=log.slice();
  R.fragen=fragen;
  console.log(JSON.stringify(R));
})().catch(function(e){console.error(e&&e.stack||e);process.exit(1);});
"""


def _lauf(src):
    js = HARNISCH % {"HELFER": _helfer(src), "PRIO": _prio(src), "MON": _monteur(src)}
    out = subprocess.run(["node", "-e", js], capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout.strip().splitlines()[-1])


@pytest.fixture(scope="module")
def R(index_html):
    return _lauf(index_html)


def test_prio_abbrechen_schreibt_nichts(R):
    assert R["prio_abbr"] == []
    assert R["prio_abbr_log"] == ["frage"]


def test_prio_uebernehmen_schreibt_exakt_wie_bisher(R):
    assert R["prio_sofort"] == 0, "vor der Rueckfrage geschrieben"
    assert R["prio_ok"] == [["as1", {"prioritaet": "hoch"}]]
    assert R["prio_ok_log"] == ["frage", "schreib"]


def test_monteur_abbrechen_schreibt_nichts(R):
    assert R["mon_abbr"] == []


def test_monteur_uebernehmen_schreibt_exakt_wie_bisher(R):
    assert R["mon_sofort"] == 0
    assert R["mon_ok"] == [["as1", {"monteur": "w2"}]]
    assert R["mon_ok_log"] == ["frage", "schreib"]


def test_frage_nennt_offa(R):
    assert R["fragen"], "keine Rueckfrage gestellt"
    assert all("wird an OFFA gemeldet" in f for f in R["fragen"]), R["fragen"]


def test_feld_bleibt_auf_altem_wert_kontrolliert(index_html):
    """Abbrechen: kein State-Update -> das kontrollierte select zeigt weiter den gespeicherten Wert."""
    assert "value: a.prioritaet||\"keine\", onChange: e=>{e.stopPropagation();const _np=" in index_html


def test_umkehrprobe_ohne_frage_schlaegt_an(index_html):
    kaputt = index_html.replace('_asZeileRueckfrage(a,"prioritaet",_np).then(_ok=>{if(_ok)updAs(a.id,{prioritaet:_np});});',
                                'updAs(a.id,{prioritaet:_np});', 1)
    assert kaputt != index_html
    R2 = _lauf(kaputt)
    assert R2["prio_abbr"] != [], "Riegel haette den fehlenden Schutz NICHT bemerkt"


def _zeile(src):
    """Die AS-Listenzeile: vom Status-Handler bis zum Storno-Knopf der Rechner-Zeile."""
    i = src.index("onChange: e=>{e.stopPropagation();const _oldS=")
    i = src.rfind("\n", 0, src.rfind("\n", 0, i))
    j = src.index("title: \"Stornieren\", 'aria-label': \"Schein stornieren\"", i)
    return src[i:j]


def test_vollstaendig_jeder_push_feld_schreibweg_der_zeile_ist_gefragt(index_html):
    m = re.search(r"const JUPROWA_PUSH_FIELDS=\{(.*?)\n\};", index_html, re.S)
    push = {k for k, v in re.findall(r"^\s*(\w+):([^,\n]+)", m.group(1), re.M) if v.strip() != "null"}
    assert {"scheinstatus", "prioritaet", "monteur", "terminBestaetigt"} <= push
    zeile = _zeile(index_html)
    ungefragt = []
    for t in re.finditer(r"updAs\(a\.id,\{(\w+):", zeile):
        feld = t.group(1)
        if feld not in push:
            continue
        vor = zeile[max(0, t.start() - 120):t.start()]
        if "_asZeileRueckfrage(" not in vor:
            ungefragt.append(feld)
    assert not ungefragt, "Push-Feld ohne Rueckfrage in der AS-Zeile: %s" % ungefragt
