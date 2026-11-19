# -*- coding: utf-8 -*-
"""v3.9.1049 Werkzeuge - Bedienung und Optik fuer Monteur (Telefon) und Buero.

Verhalten wird AUSGEFUEHRT, nicht gesucht: die reinen Helfer (_wzSuchTreffer,
_wzIstMeins, _wzChipPasst, _wzStartChip, _wzKlebTop) laufen in Node, zusammen
mit den ECHTEN Abhaengigkeiten aus index.html (_matFold, WZ_KAT, COLORS,
_wzKalibFaellig, _isValidKalibDate, td2, _ymd) - keine Nachbauten.

Jeder Verhaltensriegel hat eine Umkehrprobe (Koeder): eine verstuemmelte Kopie
des Helfers muss ROT werden, sonst misst der Riegel nichts.

Dazu Strukturriegel: die Schreibwege (PUT-Koerper) stehen Byte fuer Byte wie
vorher, das Ein/Aus/Scan-Rechtegate ist unveraendert, die Touch-Groessen.
"""
import json
import os
import re
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from conftest import _extract_fn, EPK_TEST_TIMEOUT  # noqa: E402


def _zeile(html, anfang):
    """Die EINE Quellzeile, die mit `anfang` beginnt."""
    treffer = [z for z in html.split("\n") if z.startswith(anfang)]
    assert len(treffer) == 1, "%d Zeilen beginnen mit %r" % (len(treffer), anfang)
    return treffer[0].rstrip("\r")


HELFER = ("function _wzSuchText(", "function _wzSuchTreffer(",
          "function _wzIstMeins(", "function _wzChipPasst(",
          "function _wzStartChip(", "function _wzKlebTop(")
GRUND = ("const COLORS=", "const WZ_KAT=", "const _ymd=d=>", "const td2=()=>",
         "function _isValidKalibDate(", "function _wzKalibFaellig(",
         "function _matFold(")


def _quelle(html, ersetze=None):
    teile = [_zeile(html, a) for a in GRUND + HELFER]
    code = "\n".join(teile)
    if ersetze:
        alt, neu = ersetze
        assert alt in code, "Koeder-Anker fehlt: %r" % alt
        code = code.replace(alt, neu, 1)
    return code


def _node(node_exe, tmp_path, code, name):
    p = tmp_path / name
    p.write_text(code, encoding="utf-8")
    r = subprocess.run([node_exe, str(p)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 0, "node: " + (r.stderr or "")[:1500]
    assert r.stdout.strip(), "node lieferte nichts - ein leerer Lauf ist kein gruener Lauf"
    return json.loads(r.stdout.strip().splitlines()[-1])


GERAETE = [
    {"id": "A", "name": "Kreissäge HKS 190", "inventarnr": "EK-E001", "kat": "elektro",
     "status": "verfuegbar", "zugewiesen": "", "standort": "Lager"},
    {"id": "B", "name": "Hilti TE 30-A36", "inventarnr": "10084101", "kat": "elektro",
     "status": "ausgegeben", "zugewiesen": "M1", "standort": "Baustelle"},
    {"id": "C", "name": "Fluke 1664 FC", "inventarnr": "EK-M002", "kat": "mess",
     "status": "verfuegbar", "zugewiesen": "", "naechsteKalib": "2020-01-15"},
    {"id": "D", "name": "Bosch GBH 2-28", "inventarnr": "EK-E003", "kat": "elektro",
     "status": "reparatur", "zugewiesen": "M2", "seriennr": "SN-777"},
    {"id": "E", "name": "Leiter 3x9", "inventarnr": "EK-L001", "kat": "leiter",
     "status": "verloren", "zugewiesen": ""},
]

MESSUNG = r"""
const G=%s;
const ids=f=>G.filter(f).map(w=>w.id);
const such=q=>ids(w=>_wzSuchTreffer(w,q,w.id==="B"?"Max Müller":""));
const chip=(c,mid)=>ids(w=>_wzChipPasst(w,c,mid));
console.log(JSON.stringify({
  leer:such(""), saege:such("saege"), saege2:such("säge"), sage:such("sage"),
  gross:such("KREIS"), hiltiTe:such("hilti te"), und:such("hilti bosch"),
  inv:such("10084101"), kat:such("messgerat"), kat2:such("Messgeräte"), person:such("mueller"),
  serie:such("sn-777"), standort:such("baustelle"),
  meinM1:ids(w=>_wzIstMeins(w,"M1")), meinLeer:ids(w=>_wzIstMeins(w,"")),
  cAlle:chip("alle","M1"), cMeine:chip("meine","M1"), cMeineOhne:chip("meine",""),
  cVerf:chip("verfuegbar"), cAus:chip("ausgegeben"), cRep:chip("reparatur"),
  cDef:chip("verloren"), cKal:chip("kalib_faellig"), cUnbekannt:chip("quatsch"),
  start:[_wzStartChip("verfuegbar",true,"M1"),_wzStartChip("verfuegbar",true,""),
         _wzStartChip("meine",false,""),_wzStartChip("meine",false,"M9"),
         _wzStartChip("",false,""),_wzStartChip(null,false,"M1")],
  kleb:[_wzKlebTop(390),_wzKlebTop(600),_wzKlebTop(601),_wzKlebTop(1199),_wzKlebTop(1200)]
}));
"""


def _messe(html, node_exe, tmp_path, name, ersetze=None):
    return _node(node_exe, tmp_path,
                 _quelle(html, ersetze) + "\n" + MESSUNG % json.dumps(GERAETE), name)


@pytest.fixture(scope="module")
def wz(index_html):
    fn = _extract_fn(index_html, "WerkzeugView")
    assert fn and len(fn) > 40000, "WerkzeugView nicht (ganz) gefunden"
    return fn


def _code(s):
    return re.sub(r"/\*[\s\S]*?\*/", "", s)


# ── 1. Suche ────────────────────────────────────────────────────────────────
def test_suche_ist_umlaut_tolerant_und_und_verknuepft(index_html, node_exe, tmp_path):
    m = _messe(index_html, node_exe, tmp_path, "such.js")
    assert m["leer"] == ["A", "B", "C", "D", "E"], "leere Suche muss alles zeigen"
    for k in ("saege", "saege2", "sage", "gross"):
        assert m[k] == ["A"], (k, m[k])
    assert m["hiltiTe"] == ["B"], m["hiltiTe"]
    assert m["und"] == [], "zwei Woerter muessen BEIDE passen (UND, nicht ODER): %r" % m["und"]
    assert m["inv"] == ["B"], m["inv"]
    assert m["kat"] == ["C"] and m["kat2"] == ["C"], "Kategorie-Name wird nicht gefunden"
    assert m["person"] == ["B"], "Person (ue = ü) wird nicht gefunden"
    assert m["serie"] == ["D"] and m["standort"] == ["B"], (m["serie"], m["standort"])


def test_koeder_oder_suche_wird_erkannt(index_html, node_exe, tmp_path):
    m = _messe(index_html, node_exe, tmp_path, "koeder_oder.js",
               ("return t.split(/\\s+/).every(", "return t.split(/\\s+/).some("))
    assert m["und"] != [], "KOEDER STUMM: eine ODER-Suche bliebe unbemerkt"


# ── 2. "Bei mir" ────────────────────────────────────────────────────────────
def test_bei_mir_haengt_an_der_eigenen_monteur_id(index_html, node_exe, tmp_path):
    m = _messe(index_html, node_exe, tmp_path, "mein.js")
    assert m["meinM1"] == ["B"], m["meinM1"]
    assert m["meinLeer"] == [], (
        "ohne Monteur-Id darf NICHTS 'meins' sein - sonst zaehlen alle "
        "nicht zugewiesenen Geraete (zugewiesen='') als eigene: %r" % m["meinLeer"])
    assert m["cMeine"] == ["B"] and m["cMeineOhne"] == [], (m["cMeine"], m["cMeineOhne"])


def test_koeder_mein_ohne_id_wird_erkannt(index_html, node_exe, tmp_path):
    m = _messe(index_html, node_exe, tmp_path, "koeder_mein.js",
               ("return !!(w&&mid&&w.zugewiesen===mid);", "return !!(w&&w.zugewiesen===mid);"))
    assert m["meinLeer"] != [], "KOEDER STUMM: 'meins' ohne Id bliebe unbemerkt"


# ── 3. Chips ────────────────────────────────────────────────────────────────
def test_chips_filtern_wie_beschriftet(index_html, node_exe, tmp_path):
    m = _messe(index_html, node_exe, tmp_path, "chips.js")
    assert m["cAlle"] == ["A", "B", "C", "D", "E"]
    assert m["cVerf"] == ["A", "C"] and m["cAus"] == ["B"], (m["cVerf"], m["cAus"])
    assert m["cRep"] == ["D"] and m["cDef"] == ["E"], (m["cRep"], m["cDef"])
    # C ist VERFUEGBAR und trotzdem faellig - der Chip haengt am Datum, nicht am Status
    assert m["cKal"] == ["C"], m["cKal"]
    assert m["cUnbekannt"] == ["A", "B", "C", "D", "E"], "unbekannter Chip muss wie 'alle' wirken"


def test_koeder_kalib_ueber_status_wird_erkannt(index_html, node_exe, tmp_path):
    m = _messe(index_html, node_exe, tmp_path, "koeder_kal.js",
               ('if(chip==="kalib_faellig")return _wzKalibFaellig(w);',
                'if(chip==="kalib_faellig")return w.status==="kalibrierung";'))
    assert m["cKal"] != ["C"], "KOEDER STUMM: Kalibrierung nach Status statt Datum bliebe unbemerkt"


def test_startchip_monteur_landet_auf_bei_mir(index_html, node_exe, tmp_path):
    m = _messe(index_html, node_exe, tmp_path, "start.js")
    assert m["start"] == ["meine", "verfuegbar", "alle", "meine", "alle", "alle"], m["start"]


def test_klebekante_je_breite(index_html, node_exe, tmp_path):
    m = _messe(index_html, node_exe, tmp_path, "kleb.js")
    assert m["kleb"] == [-10, -10, -20, -20, None], m["kleb"]


# ── 4. Verdrahtung in WerkzeugView ──────────────────────────────────────────
def test_helfer_sind_verdrahtet(wz):
    c = _code(wz)
    assert "return _wzChipPasst(w,werkStatusFilter,_wzMid);" in c
    assert "return _wzSuchTreffer(w,search," in c
    assert "_wzStartChip(_wkzFilterLoad(\"werkStatusFilter\",\"alle\"),_wzFeld,_wzMid)" in c
    assert "const _wzSuchFeld=(ph)=>" in c
    assert c.count("_wzSuchFeld(") == 3, "Suchfeld in Liste, Ein/Aus und Service"
    for k in ("{key:'meine',label:'Bei mir'}", "{key:'reparatur',label:'In Reparatur'}"):
        assert k in c, k
    assert "if(w.status==='reparatur')cnt.reparatur++;" in c
    assert "if(_wzMid&&w.zugewiesen===_wzMid)cnt.meine++;" in c


def test_wzmid_steht_vor_jedem_verbraucher(wz):
    """_matchesChip laeuft im useMemo waehrend des Renders - ein spaeter
    deklariertes const waere dort in der TDZ (Absturz des Reiters)."""
    c = _code(wz)
    i = c.find("const _wzMid=")
    assert i > 0
    for verbraucher in ("const [werkStatusFilter", "const _matchesChip", "const _chipCounts"):
        j = c.find(verbraucher)
        assert j > i, "%s steht vor const _wzMid" % verbraucher


def test_touchflaechen_am_telefon(wz):
    c = _code(wz)
    assert "minHeight:isMob?34" not in c and "minHeight:36}" not in c, "Restknopf unter 44 px"
    assert c.count("minHeight:isMob?48:44") >= 6, c.count("minHeight:isMob?48:44")
    assert "padding:\"8px 14px\",minHeight:44,borderRadius:22" in c, "Filter-Chips nicht 44 px"


def test_ci_farben_und_lesbarkeit(wz):
    c = _code(wz)
    assert "217,119,6" not in c, "Werkzeug-Orange als Flaechen-/Rahmenton uebrig"
    assert "color:\"#f97316\"" not in c, "Orange als Schriftfarbe (2,8:1) uebrig"
    assert "color:\"#eab308\"" not in c, "Gelb als Schriftfarbe uebrig"
    assert "color:\"#a1a1aa\"" not in c
    assert "WZ_STATUS[k].i" not in c, "Emoji im Status-Auswahlfeld"


def test_reparaturknopf_nur_mit_recht(wz):
    c = _code(wz)
    assert ", canDo(\"wz_edit\",curUser)&&React.createElement('button', { onClick: ()=>scanToRepair(scannedWz.id)" in c
    assert "const scanToRepair=(wzId)=>{if(!canDo(\"wz_edit\",curUser))return;" in c


def test_schreibwege_byte_gleich(wz):
    """Die PUT-Koerper aller Ein/Aus-Wege stehen unveraendert."""
    for s in (
        'SQ.push({url:"/api/werkzeuge/"+id,method:"PUT",body:{status:"ausgegeben",zugewiesen:monteurId,projekt:projektId||"",standort:"Baustelle"}});',
        'SQ.push({url:"/api/werkzeuge/"+id,method:"PUT",body:{status:"verfuegbar",zugewiesen:"",projekt:"",standort:"Lager"}});',
        'const _patch={status:"ausgegeben",zugewiesen:_myMid,standort:"Baustelle"};',
        'const _patch={status:"verfuegbar",zugewiesen:"",projekt:"",standort:"Lager"};',
        'const _patch={status:"ausgegeben",zugewiesen:monteurId,standort:"Baustelle"};',
        'const _patch={status:"reparatur",standort:"Werkstatt/Service"};',
        "const checkout=(id,monteurId,projektId)=>{if(!canDo(\"wz_edit\",curUser))return;",
        "const checkin=id=>{if(!canDo(\"wz_edit\",curUser))return;",
    ):
        assert s in wz, "Schreibweg veraendert: %r" % s
    # die Ausgabe-Rueckfrage bei faelliger Kalibrierung bleibt am Knopf
    assert 'if(_wzKalibFaellig(w)&&!confirm(' in wz


def test_ehrlicher_leerzustand_und_restzahl(wz):
    c = _code(wz)
    assert "\"Du hast gerade kein Werkzeug ausgeliehen\"" in c
    assert "\"Filter zurücksetzen\"" in c
    assert "weitere verfügbare Geräte - bitte oben suchen" in c, "abgeschnittene Ausgabeliste ohne Restzahl"


def test_monteur_telefon_ohne_bestandskacheln(wz):
    c = _code(wz)
    assert "!(isMob&&_wzFeld)&&React.createElement('div', { className: \"kpi-grid\"" in c
    assert "_wzFeld&&sub!==\"scan\"&&React.createElement('button', { onClick: switchToScan" in c
