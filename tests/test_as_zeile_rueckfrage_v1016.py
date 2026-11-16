# -*- coding: utf-8 -*-
"""v3.9.1016 - Arbeitsschein-Liste: Rueckfrage vor Termin/Status in der Zeile.

Befund: In der Tabellenzeile sind "Bestaetigt" (Datum) und "Status" direkt
aenderbar. Ein Fehltipp setzte sofort einen OFFA-Termin bzw. -Status.

Gebaut wurde NUR eine Bestaetigungsstufe davor. Die Riegel hier pruefen die
EIGENSCHAFT am ausgefuehrten Code (Node), nicht am Wortlaut:

  * Nach "Uebernehmen" ruft der neue Weg die Schreibfunktion mit GENAU den
    Argumenten auf, die der alte Weg (Stand d3c4cc6, unten woertlich
    hinterlegt) sofort geschrieben haette - nur zeitlich NACH der Frage.
  * "Abbrechen" ruft sie gar nicht auf.
  * Die Attrappe `updAs(id, updates)` hat die Signatur der echten
    (`const updAs=(id,updates)=>`) - das wird mitgeprueft.
  * Umkehrprobe: wird die Frage entfernt, schlagen die Riegel an.
"""
import json
import re
import subprocess

import pytest

# Der Status-Handler der Listenzeile im Stand d3c4cc6 (vor der Rueckfrage),
# woertlich aus `git show d3c4cc6:index.html`.
ALT_STATUS = (
    'e=>{e.stopPropagation();const _oldS=a.scheinstatus||"aufgenommen";const _newS=e.target.value;'
    'if(!_isLegalAsTransition(_oldS,_newS)){_optionalChain([window, \'access\', _stg1 => _stg1.__toast, '
    '\'optionalCall\', _stg2 => _stg2("⚠️ Ungültiger Status-Wechsel von "+_oldS+" → "+_newS,"warn")]);return;}'
    'updAs(a.id,{scheinstatus:_newS});}'
)
# Der Datums-Handler im Stand d3c4cc6.
ALT_DATUM = 'e=>updAs(a.id,{terminBestaetigt:e.target.value})'


def _helfer(src):
    i = src.index("function _asZeileRueckfrageText(")
    j = src.index("if(typeof window!=='undefined'){window._asZeileRueckfrageText", i)
    return src[i:j]


def _status_handler(src):
    i = src.index("onChange: e=>{e.stopPropagation();const _oldS=")
    j = src.index("}, style:", i)
    return src[i + len("onChange: "):j + 1]


HARNISCH = r"""
var calls=[],log=[],antwort=true;
function updAs(id,updates){calls.push([id,updates]);log.push('schreib');return true;}
function _confirmModal(msg,opts){log.push('frage');fragen.push([msg,opts]);return Promise.resolve(antwort);}
var fragen=[];
function _isLegalAsTransition(a,b){return b!=='verboten';}
function _optionalChain(){log.push('toast');}
var window={};
var JUPROWA_PUSH_FIELDS={terminBestaetigt:'AK_TERMIN',scheinstatus:'AK_AUFSTATUS',sachbearbeiter:null};
var AS_STATUS={aufgenommen:{l:"aufgenommen"},erledigt:{l:"erledigt"},storniert:{l:"storniert"}};
function fdt(d){var p=d.split('-');return p[2]+'.'+p[1]+'.'+p[0];}
var _hasTermin=function(t){return !!(t&&t>'1900-01-01');};
%(HELFER)s
var a={id:'as1',nummer:'S075483',scheinstatus:'aufgenommen',juprowa_id:'J1',terminBestaetigt:''};
var NEU_STATUS=(%(NEU)s);
var ALT_STATUS=(%(ALT)s);
var ALT_DATUM=(%(ALTD)s);
function ev(v){return {stopPropagation:function(){},target:{value:v}};}
function st(){var s={ref:{current:null},timer:{current:null},laeuft:{current:false},gesetzt:[]};s.setzen=function(v){s.ref.current=v;s.gesetzt.push(v);};return s;}
var ruhe=function(){return new Promise(function(r){setTimeout(r,5);});};
(async function(){
  var R={};
  // --- Status: alter Weg
  calls=[];log=[];ALT_STATUS.call(null,ev('erledigt'));R.alt_status=calls;
  // --- Status: neuer Weg, Uebernehmen
  calls=[];log=[];antwort=true;NEU_STATUS(ev('erledigt'));R.status_sofort=calls.length;await ruhe();R.status_ok=calls;R.status_ok_log=log.slice();
  // --- Status: neuer Weg, Abbrechen
  calls=[];log=[];antwort=false;NEU_STATUS(ev('erledigt'));await ruhe();R.status_abbr=calls;R.status_abbr_log=log.slice();
  // --- Status: verbotener Wechsel fragt nicht und schreibt nicht (Reihenfolge Pruefung -> Schreiben)
  calls=[];log=[];antwort=true;NEU_STATUS(ev('verboten'));await ruhe();R.status_verboten_log=log.slice();
  // --- Datum: alter Weg
  calls=[];log=[];ALT_DATUM(ev('2026-11-18'));R.alt_datum=calls;
  // --- Datum: Entwurf schreibt nicht, Verlassen fragt, Uebernehmen schreibt
  calls=[];log=[];antwort=true;var s1=st();var e1=ev('2026-11-18');
  _asBestEntwurf(a,e1,s1,updAs);R.entwurf_schreib=calls.length;R.entwurf_timer=s1.timer.current!==null;
  await _asBestUebernehmen(a,e1,s1,updAs);R.datum_ok=calls;R.datum_ok_log=log.slice();R.datum_ok_rest=s1.ref.current;
  // --- Datum: Abbrechen
  calls=[];log=[];antwort=false;var s2=st();var e2=ev('2026-11-18');
  _asBestEntwurf(a,e2,s2,updAs);await _asBestUebernehmen(a,e2,s2,updAs);R.datum_abbr=calls;R.datum_abbr_rest=s2.ref.current;
  // --- Datum: halbes Jahr beim Tippen startet keine Frage per Zeitgeber
  var s3=st();_asBestEntwurf(a,ev('0002-11-18'),s3,updAs);R.halbjahr_timer=s3.timer.current!==null;
  // --- Datum: unveraendert -> keine Frage
  calls=[];log=[];var a2={id:'as2',nummer:'S1',terminBestaetigt:'2026-11-19'};var s4=st();var e4=ev('2026-11-19');
  _asBestEntwurf(a2,e4,s4,updAs);await _asBestUebernehmen(a2,e4,s4,updAs);R.gleich_log=log.slice();
  // --- Texte
  R.text_offa=_asZeileRueckfrageText(a,'terminBestaetigt','2026-11-18');
  R.text_ohne=_asZeileRueckfrageText({nummer:'S075485'},'terminBestaetigt','2026-11-18');
  R.text_leer=_asZeileRueckfrageText(a,'terminBestaetigt','');
  R.text_status=_asZeileRueckfrageText(a,'scheinstatus','erledigt');
  R.knopf=fragen.length?fragen[0][1]:null;
  console.log(JSON.stringify(R));
})().catch(function(e){console.error(e&&e.stack||e);process.exit(1);});
"""


def _lauf(helfer, neu):
    js = HARNISCH % {"HELFER": helfer, "NEU": neu, "ALT": ALT_STATUS, "ALTD": ALT_DATUM}
    out = subprocess.run(["node", "-e", js], capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout.strip().splitlines()[-1])


@pytest.fixture(scope="module")
def R(index_html):
    return _lauf(_helfer(index_html), _status_handler(index_html))


def test_attrappe_hat_die_echte_signatur(index_html):
    assert "const updAs=(id,updates)=>{" in index_html
    assert "window._confirmModal=function(message,opts){" in index_html


def test_der_alte_schreibweg_steht_woertlich_im_neuen(index_html):
    neu = _status_handler(index_html)
    assert "updAs(a.id,{scheinstatus:_newS})" in neu
    assert "updAs(a.id,{terminBestaetigt:e.target.value})" in _helfer(index_html)
    # Die Pruefung des Uebergangs steht weiter VOR dem Schreiben.
    assert neu.index("_isLegalAsTransition(_oldS,_newS)") < neu.index("updAs(a.id,{scheinstatus:_newS})")


def test_status_schreibt_dieselben_argumente_erst_nach_der_frage(R):
    assert R["alt_status"] == [["as1", {"scheinstatus": "erledigt"}]]
    assert R["status_sofort"] == 0, "Status wurde VOR der Rueckfrage geschrieben"
    assert R["status_ok"] == R["alt_status"], "Nutzlast weicht vom alten Weg ab"
    assert R["status_ok_log"] == ["frage", "schreib"]


def test_status_abbrechen_schreibt_nichts(R):
    assert R["status_abbr"] == []
    assert R["status_abbr_log"] == ["frage"]


def test_verbotener_wechsel_bleibt_wie_bisher(R):
    assert R["status_verboten_log"] == ["toast"], "Statuspruefung veraendert"


def test_datum_schreibt_dieselben_argumente_erst_nach_der_frage(R):
    assert R["alt_datum"] == [["as1", {"terminBestaetigt": "2026-11-18"}]]
    assert R["entwurf_schreib"] == 0, "Der Entwurf hat schon geschrieben"
    assert R["datum_ok"] == R["alt_datum"], "Nutzlast weicht vom alten Weg ab"
    assert R["datum_ok_log"] == ["frage", "schreib"]
    assert R["datum_ok_rest"] is None


def test_datum_abbrechen_schreibt_nichts_und_stellt_zurueck(R):
    assert R["datum_abbr"] == []
    assert R["datum_abbr_rest"] is None, "Entwurf bleibt nach Abbrechen stehen"


def test_tippen_des_jahres_loest_keine_frage_aus(R):
    assert R["entwurf_timer"] is True
    assert R["halbjahr_timer"] is False


def test_unveraendertes_datum_fragt_nicht(R):
    assert R["gleich_log"] == []


def test_texte_sind_ehrlich(R):
    assert R["text_offa"] == "Termin bestätigen: S075483 · 18.11.2026 – wird an OFFA gemeldet. Übernehmen?"
    assert "OFFA" not in R["text_ohne"], "Ohne juprowa_id pusht updAs nicht - dann darf der Text es nicht behaupten"
    assert R["text_leer"].startswith("Bestätigten Termin entfernen: S075483")
    assert R["text_status"] == "Status ändern: S075483 · aufgenommen → erledigt – wird an OFFA gemeldet. Übernehmen?"
    assert R["knopf"]["confirmLabel"] == "Übernehmen"


def test_umkehrprobe_ohne_frage_schlaegt_an(index_html):
    neu = _status_handler(index_html)
    kaputt = neu.replace('_asZeileRueckfrage(a,"scheinstatus",_newS).then(_ok=>{if(_ok)updAs(a.id,{scheinstatus:_newS});});',
                         "updAs(a.id,{scheinstatus:_newS});", 1)
    assert kaputt != neu
    r = _lauf(_helfer(index_html), kaputt)
    assert r["status_sofort"] == 1 and r["status_abbr"] != []
    helfer = _helfer(index_html)
    h2 = helfer.replace('ok=await _asZeileRueckfrage(a,"terminBestaetigt",e.target.value);', "ok=true;", 1)
    assert h2 != helfer
    r2 = _lauf(h2, neu)
    assert r2["datum_abbr"] != [], "Umkehrprobe: Datum ohne Frage wuerde nicht auffallen"
