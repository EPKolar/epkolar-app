"""Monatsfreigabe-Schalter (GF-Entscheidung 24.11.2026 abends, Stand 3.9.1116).

Das Datenmodell ist live. Sichtbar wird die Monatsfreigabe erst, wenn der Admin sie im Chef-Portal einschaltet:
system_config, Schluessel 'monatsfreigabe_aktiv_ab' (Wert ISO-Datum; fehlt/leer/unlesbar = AUS; aktiv wenn heute >= Datum).
Beides muss stimmen: Datenmodell da (_mfModellPruefen) UND Schalter an. Aus = fuer Buero, Admin und Monteur nichts sichtbar
(kein Reiter, keine Monteur-Karte, keine Chef-Liste, kein Zaehler, keine Meldungstypen, keine Erinnerungen, kein Anlegen).
Nur App-seitig - die DB laesst Buero/Admin weiterhin ueber die API schreiben (Bericht).

Umkehrprobe: gegen 3.9.1116 ohne Schalter (89f5a63) ist "Schalter aus -> unsichtbar" rot.
"""
import json
import re
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
    teile = [_zeile(s, "var _mfModellStand="), _zeile(s, "function _mfIstAktiv(){"), _zeile(s, "function _mfFehltModell(")]
    for kopf in ("var MF_SCHALTER_KEY=",):
        if kopf in s:
            teile.append(_zeile(s, kopf))
    for kopf in ("function _mfSchalterWert(v){", "async function _mfSchalterLaden(){"):
        if kopf in s:
            teile.append(_fn(s, kopf))
    if "function _mfSchalterAn(" in s:
        teile.append(_zeile(s, "function _mfSchalterAn("))
    teile.append(_fn(s, "function _mfModellPruefen(){"))
    return "\n".join(teile) + "\n"


SZENARIO = r"""
var SB_REST="https://x/rest/v1",AUFRUFE=[],AKTIVIERT=0;
function _sbH(){return {};}function _fT(o){return o;}async function _authRetry(f){return f();}
function _ezHeuteISO(){return "2026-11-24";}
function _mfNotifTypenAktivieren(){AKTIVIERT++;}
function antw(ok,status,body){return {ok:ok,status:status,json:async function(){return body;},text:async function(){return JSON.stringify(body);}};}
async function fetch(u){AUFRUFE.push(u);
  if(u.indexOf("/system_config")>=0){if(SCHALTER==="403")return antw(false,403,{});return antw(true,200,SCHALTER===null?[]:[{value:SCHALTER}]);}
  return antw(true,200,[]);}
(async function(){var r=await _mfModellPruefen();console.log(JSON.stringify({ergebnis:r,aktiv:_mfIstAktiv(),aktiviert:AKTIVIERT}));})();
"""


def _lauf(src, schalter):
    js = "var SCHALTER=" + json.dumps(schalter) + ";\n" + _kern(src) + SZENARIO
    r = subprocess.run([NODE, "-e", js], capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout)


@needs_node
@pytest.mark.parametrize("schalter", [None, "", "2026-11-25", "2027-01-01", "403", "kaputt"])
def test_aus_oder_zukunft_unsichtbar(index_html, schalter):
    r = _lauf(index_html, schalter)
    assert r == {"ergebnis": False, "aktiv": False, "aktiviert": 0}, (schalter, r)


@needs_node
@pytest.mark.parametrize("schalter", ["2026-11-24", "2026-11-01", '"2026-11-24"'])
def test_ab_heute_sichtbar(index_html, schalter):
    r = _lauf(index_html, schalter)
    assert r == {"ergebnis": True, "aktiv": True, "aktiviert": 1}, (schalter, r)


def test_alle_sichtstellen_haengen_am_schalter(index_html):
    """Buero-Reiter, Monteur-Karte, Chef-Liste, Zaehler, Start-Meldungen, Buero-Inhalt: alle ueber _mfIstAktiv (= Modell UND Schalter)."""
    s = index_html
    assert 'filter(function(r){return r[0]!=="freigabe"||_mfIstAktiv();})' in s
    assert 'FINKZEIT_ENABLED&&_mfIstAktiv()&&MF_MONTEUR_ROLLEN.indexOf(curUser.role)>=0&&React.createElement(MonatsfreigabeMonteur' in s
    assert 'FINKZEIT_ENABLED&&_mfIstAktiv()&&curUser&&curUser.role==="admin"&&React.createElement(MonatsfreigabeChef' in s
    assert 'if(tab==="freigabe"&&_mfIstAktiv())inhalt=h(MonatsfreigabeBuero' in s
    assert 'var r={_chef:0,stunden:0,bueroexport:0};if(!curUser||!_mfIstAktiv())return r;' in s
    assert 'if(!curUser||typeof pushNotif!=="function"||!_mfIstAktiv())return 0;' in s
    assert "function _mfIstAktiv(){return _mfModellStand===\"da\"&&_mfSchalterAn();}" in s


def test_admin_schalter_im_chef_portal(index_html):
    s = index_html
    i = s.index("function MonatsfreigabeSchalter({curUser}){")
    k = s[i:s.index("\nfunction ", i + 10)]
    assert 'curUser.role!=="admin"||_mfModellStand!=="da")return null;' in k
    assert "_confirmModal(frage," in k and not re.search(r"(?<![\w.])confirm\(", k)
    assert '"Einschalten"' in k and '"Ausschalten"' in k and 'type:"date"' in k
    assert 'await _sbUpsert("system_config",{key:MF_SCHALTER_KEY,value:w,' in s
    assert 'var MF_SCHALTER_KEY="monatsfreigabe_aktiv_ab";' in s
    assert "monatsfreigabe_einstellungen?select=id&limit=1" in s  # Modellpruefung unveraendert, Schalter NICHT dort abgelegt
    assert "React.createElement(MonatsfreigabeSchalter,{curUser:curUser})" in s
