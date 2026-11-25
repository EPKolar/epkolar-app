"""Monatsfreigabe-Schalter: Lesefehler halten die Monatsfreigabe VERSTECKT (Stand 3.9.1118).

Schalter = system_config, Schluessel 'monatsfreigabe_aktiv_ab' (siehe test_mf_schalter_p16.py).
Regel: fehlt/leer/unlesbar = AUS. Dieser Test deckt die Fehlerfaelle beim LESEN des Schalters ab:
  - Netzfehler (fetch wirft, z. B. "Failed to fetch" / Zeitueberschreitung)
  - Zeile fehlt (leere Antwort [])
  - HTTP-Fehler (401, 403, 404, 500, 503)
  - Antwort nicht lesbar (json() wirft)
  - Netzfehler schon bei der Modellpruefung
In jedem Fall: Ergebnis aktiv:false, keine Meldungstypen aktiviert.
Zusaetzlich: war der Schalter vorher AN und das erneute Lesen scheitert, wird er AUS (kein stehengebliebener Altwert).

Jeder Fall prueft mit, dass der Fehlerweg wirklich durchlaufen wurde (system_config wurde abgefragt), sonst waere
"unsichtbar" auch durch einen frueheren Abbruch erklaerbar.

Umkehrprobe (24./25.11.2026): mit einer Kopie, in der _mfSchalterLaden im Fehlerfall ein Datum setzt
(_mfSchalterAb="2026-11-01" statt ""), sind die Faelle rot.
"""
import json
import shutil
import subprocess

import pytest

NODE = shutil.which("node")
needs_node = pytest.mark.skipif(not NODE, reason="node fehlt")


def _zeile(src, kopf):
    i = src.index(kopf)
    return src[i:src.index("\n", i)]


def _fn(src, kopf):
    i = src.index(kopf)
    return src[i:src.index("\n}", i) + 2]


def _kern(src):
    s = src.replace("\r\n", "\n")
    teile = [
        _zeile(s, "var _mfModellStand="),
        _zeile(s, "var MF_SCHALTER_KEY="),
        _fn(s, "function _mfSchalterWert(v){"),
        _zeile(s, "function _mfSchalterAn("),
        _zeile(s, "function _mfIstAktiv(){"),
        _fn(s, "async function _mfSchalterLaden(){"),
        _zeile(s, "function _mfFehltModell("),
        _fn(s, "function _mfModellPruefen(){"),
    ]
    return "\n".join(teile) + "\n"


# FALL steuert die Antwort auf die system_config-Abfrage; MODELL_WIRFT laesst schon die Modellpruefung scheitern.
SZENARIO = r"""
var SB_REST="https://x/rest/v1",AUFRUFE=[],AKTIVIERT=0;
function _sbH(){return {};}function _fT(o){return o;}async function _authRetry(f){return f();}
function _ezHeuteISO(){return "2026-11-24";}
function _mfNotifTypenAktivieren(){AKTIVIERT++;}
function antw(ok,status,body,jsonWirft){return {ok:ok,status:status,
  json:async function(){if(jsonWirft)throw new SyntaxError("Unexpected token < in JSON");return body;},
  text:async function(){return JSON.stringify(body);}};}
async function fetch(u){AUFRUFE.push(u);
  if(u.indexOf("/system_config")>=0){
    if(FALL==="netz")throw new TypeError("Failed to fetch");
    if(FALL==="zeit"){var z=new Error("The operation was aborted due to timeout");z.name="TimeoutError";throw z;}
    if(FALL==="leer")return antw(true,200,[]);
    if(FALL==="jsonkaputt")return antw(true,200,null,true);
    if(/^http\d+$/.test(FALL))return antw(false,parseInt(FALL.slice(4),10),{message:"Fehler"});
    return antw(true,200,[{value:"2026-11-01"}]);
  }
  if(MODELL_WIRFT)throw new TypeError("Failed to fetch");
  return antw(true,200,[]);}
(async function(){
  if(VORHER_AN){_mfSchalterAb="2026-11-01";}
  var r=await _mfModellPruefen();
  console.log(JSON.stringify({ergebnis:r,aktiv:_mfIstAktiv(),aktiviert:AKTIVIERT,
    schalterGelesen:AUFRUFE.some(function(u){return u.indexOf("/system_config?key=eq.monatsfreigabe_aktiv_ab")>=0;})}));
})();
"""


def _lauf(src, fall, modell_wirft=False, vorher_an=False):
    js = ("var FALL=" + json.dumps(fall) + ",MODELL_WIRFT=" + json.dumps(modell_wirft)
          + ",VORHER_AN=" + json.dumps(vorher_an) + ";\n" + _kern(src) + SZENARIO)
    r = subprocess.run([NODE, "-e", js], capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout)


FEHLERFAELLE = ["netz", "zeit", "leer", "jsonkaputt", "http401", "http403", "http404", "http500", "http503"]


@needs_node
@pytest.mark.parametrize("fall", FEHLERFAELLE)
def test_lesefehler_haelt_mf_versteckt(index_html, fall):
    r = _lauf(index_html, fall)
    assert r["schalterGelesen"] is True, ("Fehlerweg nicht durchlaufen", fall, r)
    assert {k: r[k] for k in ("ergebnis", "aktiv", "aktiviert")} == {"ergebnis": False, "aktiv": False, "aktiviert": 0}, (fall, r)


@needs_node
@pytest.mark.parametrize("fall", FEHLERFAELLE)
def test_lesefehler_schaltet_vorher_an_wieder_aus(index_html, fall):
    """Altwert 'an' darf einen gescheiterten Neu-Lesevorgang nicht ueberleben."""
    r = _lauf(index_html, fall, vorher_an=True)
    assert r["schalterGelesen"] is True, ("Fehlerweg nicht durchlaufen", fall, r)
    assert {k: r[k] for k in ("ergebnis", "aktiv", "aktiviert")} == {"ergebnis": False, "aktiv": False, "aktiviert": 0}, (fall, r)


@needs_node
def test_netzfehler_bei_modellpruefung_versteckt(index_html):
    r = _lauf(index_html, "an", modell_wirft=True)
    assert {k: r[k] for k in ("ergebnis", "aktiv", "aktiviert")} == {"ergebnis": False, "aktiv": False, "aktiviert": 0}, r


@needs_node
def test_gegenprobe_lesbarer_schalter_ist_an(index_html):
    """Gegenprobe: dieselbe Attrappe mit lesbarem Schalter (ab 2026-11-01, heute 2026-11-24) ergibt AN -
    die Fehlerfaelle oben sind also nicht durch eine kaputte Attrappe gruen."""
    r = _lauf(index_html, "an")
    assert r == {"ergebnis": True, "aktiv": True, "aktiviert": 1, "schalterGelesen": True}, r
