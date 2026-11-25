# -*- coding: utf-8 -*-
"""v1049 Fahrzeuge - Bedienung und Optik fuer Monteur (Telefon) und Buero.

Verhalten wird AUSGEFUEHRT, nicht gesucht: die reinen Helfer (_fzArt, _fzBetrieb,
_fzBusSvg, _fzBusFuer, _fzSuchTreffer, _fzIstMeins, _fzChipPasst, _fzDE) laufen
in Node zusammen mit den ECHTEN Abhaengigkeiten aus index.html (COLORS,
TIME_*, window._pickerlStatus, _fzPickerlFaellig, _fzServiceFaellig, _matFold).

Jeder Verhaltensriegel hat eine Umkehrprobe (Koeder): eine verstuemmelte Kopie
des Helfers muss ROT werden, sonst misst der Riegel nichts.

Dazu Strukturriegel: alle Schreibwege der Fahrzeugansicht stehen Byte fuer
Byte wie vor dem Umbau (Hash je Handler + Hash ueber die Menge aller upd(...)/
SQ.push(...)-Aufrufe), die Mein-Karte oeffnet nur die bestehenden Dialoge, die
Finanz-Sichtbarkeit haengt weiter nur an _maStaffRolle.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import date, timedelta

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from conftest import EPK_TEST_TIMEOUT  # noqa: E402
from test_flotte_schreibwege_v1049 import _comp_const, _scan_to  # noqa: E402


def _zeile(html, anfang):
    treffer = [z for z in html.split("\n") if z.startswith(anfang)]
    assert len(treffer) == 1, "%d Zeilen beginnen mit %r" % (len(treffer), anfang)
    return treffer[0].rstrip("\r")


GRUND = ("const TIME_SECOND=", "const TIME_MINUTE=", "const TIME_HOUR=", "const TIME_DAY=",
         "const COLORS=", "function _matFold(", "window._pickerlStatus=",
         "function _fzPickerlFaellig(", "function _fzServiceFaellig(")
HELFER = ("function _fzArt(", "function _fzBetrieb(", "const _FZ_BETRIEB=", "function _fzBusSvg(",
          "function _fzBusFarbe(", "const _FZ_ART_NAME=", "function _fzBusFuer(", "function _fzSuchText(",
          "function _fzSuchTreffer(", "function _fzIstMeins(", "function _fzIstFaellig(",
          "function _fzOffeneSchaeden(", "function _fzDE(", "function _fzChipPasst(")


def _quelle(html, ersetze=None):
    code = "var window={};\n" + "\n".join(_zeile(html, a) for a in GRUND + HELFER)
    if ersetze:
        alt, neu = ersetze
        assert alt in code, "Koeder-Anker fehlt: %r" % alt
        code = code.replace(alt, neu, 1)
    return code


def _node(node_exe, tmp_path, code, name):
    p = tmp_path / name
    p.write_text(code, encoding="utf-8")
    r = subprocess.run([node_exe, str(p)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 0, "node: " + (r.stderr or "")[:1500]
    assert r.stdout.strip(), "node lieferte nichts - ein leerer Lauf ist kein gruener Lauf"
    return json.loads(r.stdout.strip().splitlines()[-1])


def _d(tage):
    return (date.today() + timedelta(days=tage)).isoformat()


FLOTTE = [
    {"id": "A", "kennzeichen": "TU-545BC", "marke": "Renault", "modell": "Trafic", "typ": "Transporter",
     "fahrer": "M1", "status": "aktiv", "pickerl": _d(400), "naechstService": _d(200), "schaeden": []},
    {"id": "B", "kennzeichen": "TU-83JM", "marke": "Scania", "modell": "P 93 Ladekran", "typ": "LKW",
     "fahrer": "M2", "status": "aktiv", "pickerl": _d(-5), "naechstService": _d(100),
     "schaeden": [{"status": "in_reparatur"}]},
    {"id": "C", "kennzeichen": "N-719.920", "marke": "", "modell": "Kompressor", "typ": "Anhänger",
     "fahrer": "", "status": "aktiv", "pickerl": "", "naechstService": _d(-3),
     "schaeden": [{"status": "offen"}, {"status": "erledigt"}]},
    {"id": "D", "kennzeichen": "TU-266BP", "marke": "Mercedes", "modell": "CL 500", "typ": "PKW",
     "fahrer": "", "status": "stillgelegt", "pickerl": _d(-100), "schaeden": []},
    {"id": "E", "kennzeichen": "TU-656BR", "marke": "Ford", "modell": "Custom Kasten", "typ": "Transporter",
     "fahrer": "M1", "status": "aktiv", "pickerl": _d(10), "schaeden": None},
]
NAMEN = {"M1": "Paschinger", "M2": "Jürgen Müller"}

MESSUNG = r"""
const G=%s, N=%s;
const ids=f=>G.filter(f).map(x=>x.id);
const such=q=>ids(f=>_fzSuchTreffer(f,q,N[f.fahrer]||""));
const chip=(c,mid)=>ids(f=>_fzChipPasst(f,c,mid));
const svg=o=>_fzBusSvg(o);
console.log(JSON.stringify({
  art:G.map(_fzArt), artRoh:[_fzArt({typ:"lkw"}),_fzArt({typ:"Anhaenger"}),_fzArt({typ:"Stapler"}),_fzArt(null),_fzArt({})],
  betrieb:G.map(_fzBetrieb), betriebNull:_fzBetrieb(null),
  leer:such(""), kz:such("tu-545bc"), kzOhne:such("tu545"), kzTeil:such("tu 545"), gross:such("SCANIA"),
  fahrer:such("mueller"), fahrer2:such("müller"), modell:such("trafic"), und:such("trafic scania"),
  typ:such("anhanger"), nichts:such("xyz"),
  meinM1:ids(f=>_fzIstMeins(f,"M1")), meinLeer:ids(f=>_fzIstMeins(f,"")), meinUndef:ids(f=>_fzIstMeins(f,undefined)),
  cAlle:chip("alle","M1"), cMein:chip("mein","M1"), cMeinOhne:chip("mein",""), cFaellig:chip("faellig"),
  cWerkstatt:chip("werkstatt"), cSchaden:chip("schaden"), cQuatsch:chip("quatsch"),
  de:[_fzDE(5000,0),_fzDE(1234567.891,2),_fzDE(6,1),_fzDE(0.1234,3),_fzDE(2.0049,3),_fzDE("52,3",1),_fzDE(NaN,1),_fzDE(null,0),_fzDE("",0),_fzDE(-1234.5,1),_fzDE(-0.0001,2),_fzDE(129453,0)],
  svgBus:svg({art:"bus",farbe:"#009640",gr:48,titel:"Transporter, In Betrieb"}),
  svgLkw:svg({art:"lkw",gr:30}), svgAnh:svg({art:"anhaenger"}), svgQuatsch:svg({art:"<x>",farbe:"red;background:url(x)",gr:"abc",titel:'"><script>'}),
  fuer:G.map(f=>_fzBusFuer(f,40)),
  farben:["betrieb","werkstatt","ausser","quatsch"].map(_fzBusFarbe)
}));
"""


def _messe(html, node_exe, tmp_path, name, ersetze=None):
    return _node(node_exe, tmp_path, _quelle(html, ersetze) + "\n" + MESSUNG % (json.dumps(FLOTTE), json.dumps(NAMEN)), name)


@pytest.fixture(scope="module")
def fv(index_html):
    a = index_html.index("function FahrzeugView(")
    # Endmarke angepasst 25.11.2026 (v3.9.1120): DEMO_FZ (stand direkt hinter FahrzeugView) ist entfernt.
    b = index_html.index("\n/* ═══════════ GEFAHRSTOFFE / SICHERHEITSDATENBL", a)
    return index_html[a:b]


def _code(s):
    return re.sub(r"/\*[\s\S]*?\*/", "", s)


# ── 1. Fahrzeug-Bild ────────────────────────────────────────────────────────
def test_bildart_nach_typ(index_html, node_exe, tmp_path):
    m = _messe(index_html, node_exe, tmp_path, "art.js")
    # v1051: PKW und Stapler bekommen eigene Zeichnungen (vorher Transporter) - typ unterscheidet sie
    assert m["art"] == ["bus", "lkw", "anhaenger", "pkw", "bus"], m["art"]
    assert m["artRoh"] == ["lkw", "anhaenger", "stapler", "bus", "bus"], m["artRoh"]


def test_betriebszustand_aus_vorhandenen_werten(index_html, node_exe, tmp_path):
    """status kennt nur aktiv/stillgelegt; Werkstatt = Schaden in_reparatur."""
    m = _messe(index_html, node_exe, tmp_path, "betrieb.js")
    assert m["betrieb"] == ["betrieb", "werkstatt", "betrieb", "ausser", "betrieb"], m["betrieb"]
    assert m["betriebNull"] == "betrieb"


def test_svg_varianten_und_farbe(index_html, node_exe, tmp_path):
    m = _messe(index_html, node_exe, tmp_path, "svg.js")
    bus, lkw, anh = m["svgBus"], m["svgLkw"], m["svgAnh"]
    for t in (bus, lkw, anh):
        assert t.startswith("<svg ") and t.endswith("</svg>") and 'viewBox="0 0 48 32"' in t
        assert "<script" not in t and "<image" not in t and "href" not in t, "nur eigene Pfade, nichts Nachgeladenes"
    assert 'data-fz-art="bus"' in bus and 'data-fz-art="lkw"' in lkw and 'data-fz-art="anhaenger"' in anh
    assert len({bus.split("data-fz-art")[1], lkw.split("data-fz-art")[1], anh.split("data-fz-art")[1]}) == 3, "drei verschiedene Zeichnungen"
    assert 'width="48" height="32"' in bus and 'width="30" height="20"' in lkw and 'width="40" height="27"' in anh
    assert "color:#009640" in bus and 'role="img"' in bus and 'aria-label="Transporter, In Betrieb"' in bus
    assert 'aria-hidden="true"' in lkw and "<title>" not in lkw, "ohne Titel: Zierbild, nicht vorgelesen"


def test_svg_nimmt_keine_fremden_werte_auf(index_html, node_exe, tmp_path):
    q = _messe(index_html, node_exe, tmp_path, "svg_q.js")["svgQuatsch"]
    assert 'data-fz-art="bus"' in q, "unbekannte Art faellt auf den Transporter zurueck"
    assert "red;" not in q and "url(" not in q and "color:#009640" in q, "Farbe nur als #rrggbb"
    assert 'width="40"' in q
    assert "<script>" not in q and "&lt;script&gt;" in q and "&quot;&gt;" in q, "Titel wird maskiert"


def test_koeder_titel_unmaskiert_wird_erkannt(index_html, node_exe, tmp_path):
    m = _messe(index_html, node_exe, tmp_path, "koeder_esc.js",
               ('var titel=String(o.titel==null?"":o.titel).trim();', 'var titel=String(o.titel==null?"":o.titel).trim();esc=function(t){return t;};'))
    assert "<script>" in m["svgQuatsch"], "KOEDER STUMM: ein unmaskierter Titel bliebe unbemerkt"


def test_bild_fuer_fahrzeug_traegt_zustand(index_html, node_exe, tmp_path):
    m = _messe(index_html, node_exe, tmp_path, "fuer.js")
    f = m["fuer"]
    assert 'aria-label="Transporter, In Betrieb"' in f[0] and "color:#009640" in f[0]
    assert 'aria-label="LKW, Werkstatt"' in f[1] and "color:#c2410c" in f[1]
    assert 'aria-label="Anhänger, In Betrieb"' in f[2]
    # v1051: Fahrzeug D ist typ PKW -> eigene PKW-Zeichnung und Vorlesetext "PKW" (vorher "Transporter")
    assert 'aria-label="PKW, Außer Dienst"' in f[3] and "color:#71717a" in f[3] and 'data-fz-art="pkw"' in f[3]
    # ohne _lesbar (Node) die Rohfarben aus COLORS: Marke / WARNING_FILL / NEUTRAL, Unbekanntes = in Betrieb
    assert m["farben"] == ["#009640", "#c2410c", "#71717a", "#009640"], m["farben"]


# ── 2. Suche ────────────────────────────────────────────────────────────────
def test_suche_kennzeichen_modell_fahrer_umlaut(index_html, node_exe, tmp_path):
    m = _messe(index_html, node_exe, tmp_path, "such.js")
    assert m["leer"] == ["A", "B", "C", "D", "E"]
    for k in ("kz", "kzOhne", "kzTeil"):
        assert m[k] == ["A"], (k, m[k])
    assert m["gross"] == ["B"] and m["modell"] == ["A"]
    assert m["fahrer"] == ["B"] and m["fahrer2"] == ["B"], "Fahrer mit ue = ü"
    assert m["typ"] == ["C"], "Typ Anhänger ohne Umlaut"
    assert m["und"] == [], "mehrere Woerter: UND, nicht ODER"
    assert m["nichts"] == []


def test_koeder_oder_suche_wird_erkannt(index_html, node_exe, tmp_path):
    m = _messe(index_html, node_exe, tmp_path, "koeder_oder.js",
               ("return t.split(/\\s+/).every(", "return t.split(/\\s+/).some("))
    assert m["und"] != [], "KOEDER STUMM: eine ODER-Suche bliebe unbemerkt"


def test_koeder_kennzeichen_ohne_bindestrich(index_html, node_exe, tmp_path):
    m = _messe(index_html, node_exe, tmp_path, "koeder_kz.js",
               ('kz.replace(/[^A-Za-z0-9]/g,""),', ""))
    assert m["kzOhne"] != ["A"], "KOEDER STUMM: 'tu545' ohne Bindestrich-Variante bliebe unbemerkt"


# ── 3. "Mein" ───────────────────────────────────────────────────────────────
def test_mein_haengt_an_der_eigenen_monteur_id(index_html, node_exe, tmp_path):
    m = _messe(index_html, node_exe, tmp_path, "mein.js")
    assert m["meinM1"] == ["A", "E"]
    assert m["meinLeer"] == [] and m["meinUndef"] == [], (
        "ohne Monteur-Id darf NICHTS 'meins' sein - sonst ist jedes Fahrzeug ohne Fahrer "
        "(fahrer='') das eigene: %r / %r" % (m["meinLeer"], m["meinUndef"]))


def test_koeder_mein_ohne_id_wird_erkannt(index_html, node_exe, tmp_path):
    m = _messe(index_html, node_exe, tmp_path, "koeder_mein.js",
               ("return !!(f&&mid&&f.fahrer===mid);", "return !!(f&&f.fahrer===mid);"))
    assert m["meinLeer"] != [], "KOEDER STUMM: 'meins' ohne Id bliebe unbemerkt"


def test_myfzid_im_view_ohne_id_leer(fv):
    c = _code(fv)
    assert '  const myFzId=((curUser&&curUser.monteurId)?(fahrzeuge.find(f=>f.fahrer===curUser.monteurId)||{}).id:null)||null;' in c
    assert 'const _fzMid=(curUser&&curUser.monteurId)||"";' in c


# ── 4. Chips ────────────────────────────────────────────────────────────────
def test_chips_filtern_wie_beschriftet(index_html, node_exe, tmp_path):
    m = _messe(index_html, node_exe, tmp_path, "chips.js")
    assert m["cAlle"] == ["A", "B", "C", "D", "E"] and m["cQuatsch"] == m["cAlle"]
    assert m["cMein"] == ["A", "E"] and m["cMeinOhne"] == []
    # B: Pickerl seit 5 Tagen abgelaufen; C: Service seit 3 Tagen; E: Pickerl in 10 Tagen (30-Tage-Vorwarnung);
    # D ist stillgelegt (ueberfaelliges Pickerl zaehlt NICHT), A ist in Ordnung
    assert m["cFaellig"] == ["B", "C", "E"], m["cFaellig"]
    assert m["cWerkstatt"] == ["B"], m["cWerkstatt"]
    assert m["cSchaden"] == ["C"], "nur status offen zaehlt, erledigt nicht"


def test_koeder_faellig_ohne_stillgelegt_filter(index_html, node_exe, tmp_path):
    m = _messe(index_html, node_exe, tmp_path, "koeder_faellig.js",
               ('return !!(f&&f.status!=="stillgelegt"&&(', 'return !!(f&&('))
    assert "D" in m["cFaellig"], "KOEDER STUMM: ein stillgelegtes Fahrzeug unter 'Fällig' bliebe unbemerkt"


# ── 5. Zahlen deutsch (A55-Fund v1048) ──────────────────────────────────────
def test_zahlen_mit_punkt_und_komma(index_html, node_exe, tmp_path):
    m = _messe(index_html, node_exe, tmp_path, "de.js")
    assert m["de"] == ["5.000", "1.234.567,89", "6,0", "0,123", "2,005", "52,3", "—", "—", "—",
                       "-1.234,5", "0,00", "129.453"], m["de"]


def test_koeder_tausenderpunkt(index_html, node_exe, tmp_path):
    m = _messe(index_html, node_exe, tmp_path, "koeder_de.js", ('.replace(/\\B(?=(\\d{3})+(?!\\d))/g,".")', ""))
    assert m["de"][0] != "5.000", "KOEDER STUMM: fehlender Tausenderpunkt bliebe unbemerkt"


def test_anzeige_ohne_punkt_dezimal_und_schmales_leerzeichen(index_html, fv):
    """Kosten-Ansicht, Fahrzeugakte und die Fahrzeugansicht zeigen Zahlen ueber _fzDE.
    Excel-Export (genXls) und Toasts/Rueckfragen in Schreib-Handlern bleiben unangetastet."""
    a = index_html.index("function FlotteKostenPanel(")
    b = index_html.index("function FahrzeugStammKarte(", a)
    teil = _code(index_html[a:b])
    assert not re.search(r"\b_n\(", teil), "Kosten/Akte zeigen noch _n (Dezimalpunkt)"
    assert "toLocaleString('de-AT')" not in teil, "km mit schmalem Leerzeichen"
    assert "('€ '+_fzDE(sum.euro/sum.litP,3)+'/l')" in teil
    r = fv.index("  return (\n    React.createElement('div', {}")
    render = _code(fv[r:])
    assert not re.search(r"\b_n\(", render)
    assert render.count('toLocaleString("de-AT")') == 1 and "genXls(" in render, "nur der Excel-Export"


# ── 6. Verdrahtung / Rollen ─────────────────────────────────────────────────
def test_helfer_verdrahtet(fv):
    c = _code(fv)
    assert "const _fzGefiltert=visibleFz.filter(f=>_fzChipPasst(f,fzChip,_fzMid)&&_fzSuchTreffer(f,fzSuche,_fzFahrerName(f)));" in c
    assert "_fzListe.map(f=>view===\"kacheln\"?_fzKachel(f):_fzZeile(f))" in c
    assert "dangerouslySetInnerHTML: {__html:_fzBusFuer(f,gr)}" in c
    assert c.count("_fzAvatar(") == 4, "Liste, Kachel, Mein-Karte, Detailkopf"
    assert '&&(!isVAdmin||(view!=="fristen"&&view!=="kosten"))&&' in c


def test_monteur_mit_einem_fahrzeug_ohne_verwalterwerkzeuge(fv):
    c = _code(fv)
    assert "const _einzelFz=!isVAdmin&&visibleFz.length<=1;" in c
    assert ", !sel&&!batchMode&&!_einzelFz&&React.createElement('div', { style: {display:\"flex\",borderRadius:8" in c
    assert ", (!_einzelFz||batchMode)&&React.createElement('button', { title: \"Mehrere Tankbelege" in c
    assert ", !sel&&!batchMode&&!_einzelFz&&React.createElement('button', { onClick: ()=>printLabels(visibleFz" in c
    assert ", !sel&&isVAdmin&&isMob&&_fzKpiKompakt" in c
    assert ", !sel&&isVAdmin&&!isMob&&(React.createElement('div', { style: {display:\"grid\",gridTemplateColumns:\"repeat(auto-fit,minmax(160px,1fr))\"" in c
    assert ", isVAdmin&&!isMob&&React.createElement('p'" in c


def test_mein_karte_oeffnet_nur_bestehende_dialoge(fv):
    c = _code(fv)
    oeffne = re.search(r"const _fzOeffne=\(f,was\)=>\{.*?\};\n", c).group(0)
    for verboten in ("SQ.push", "upd(", "setFahrzeuge", "_sb"):
        assert verboten not in oeffne, verboten
    # dieselben Zustaende wie die Knoepfe im Detailkopf
    assert "setShowTank(f.id);setTankKm(String(f.kmStand||\"\"));" in oeffne
    assert "setShowKm(f.id);setKmVal(String(f.kmStand||\"\"));" in oeffne
    assert "setShowSchaden(f.id);" in oeffne
    for was in ("tank", "km", "schaden"):
        assert "onClick: ()=>_fzOeffne(_meinFz,\"%s\")" % was in c
    assert ", !sel&&!batchMode&&!fzScanMode&&!_fzFilterAktiv&&(!isVAdmin||(view!==\"fristen\"&&view!==\"kosten\"))&&_fzMeinKarte" in c
    assert "const _meinFz=myFzId?(visibleFz.find(f=>f.id===myFzId)||null):null;" in c, "stillgelegtes eigenes Fahrzeug: keine Karte"


def test_dialoge_direkt_unter_dem_kopf(fv):
    i_kopf = fv.index("'data-fz-aktionen': \"1\"")
    i_km = fv.index("/* km Modal */")
    i_tank = fv.index("/* Tank Modal */")
    i_sch = fv.index("/* Schaden Modal */")
    i_akte = fv.index("React.createElement(FahrzeugAkteKarte,")
    i_stamm = fv.index("React.createElement(FahrzeugStammKarte,")
    assert i_kopf < i_km < i_tank < i_sch < i_akte < i_stamm, "Dialoge stehen wieder unter Akte/Stammdaten"
    assert fv.count("showKm===sel&&") == 1 and fv.count("showTank===sel&&") == 1 and fv.count("showSchaden===sel&&") == 1


def test_detailknoepfe_gross_und_klick_unveraendert(fv):
    c = _code(fv)
    for s in ('onClick: ()=>{setShowTank(sel);setTankKm(String(selFz.kmStand||""));}, style: _fzAktStil(bpS)}',
              'onClick: ()=>{setShowKm(sel);setKmVal(String(selFz.kmStand||""));}, style: _fzAktStil(bsS())}',
              'onClick: ()=>setShowSchaden(sel), style: _fzAktStil(bsS(),true)}'):
        assert s in c, s
    assert "minHeight:isMob?56:44" in c
    assert 'minHeight:isMob?48:44' in c, "Suchfeld 48 px am Telefon"
    assert 'padding:"8px 14px",minHeight:44,borderRadius:22' in c, "Chips 44 px"
    assert 'padding:"3px 8px",fontSize:UI.fMeta}' not in c and 'padding:"3px 6px",fontSize:UI.fMeta}' not in c
    assert "minWidth:24" not in c, "Stern im Detail unter 44 px"


def test_abschnitte_und_leiste(fv):
    c = _code(fv)
    for sek in ("fzsek-akte", "fzsek-stamm", "fzsek-termine", "fzsek-svtermine", "fzsek-technik",
                "fzsek-service", "fzsek-schaden", "fzsek-tank", "fzsek-km"):
        assert c.count('"%s"' % sek) == 2, (sek, "Anker UND Leisteneintrag")
    assert "const _fzKleb=_wzKlebTop(ww);" in c
    assert "position:\"sticky\",top:_fzKleb,zIndex:3,background:V.bg" in c


def test_ehrlicher_leerzustand(fv):
    c = _code(fv)
    assert '"Filter zurücksetzen"' in c
    assert "\"Kein Fahrzeug passt zu „\"+fzSuche.trim()+\"“\"" in c
    assert '"Dir ist kein aktives Fahrzeug zugewiesen"' in c
    assert "_fzFilterAktiv&&_fzGefiltert.length===0&&_fzLeerGefiltert" in c


def test_werkstatt_termin_am_telefon_gestapelt(fv):
    c = _code(fv)
    assert "style: isMob?{display:\"grid\",gridTemplateColumns:\"minmax(0,1fr) minmax(0,1fr)\"" in c
    assert 'placeholder: "Beschreibung (optional)"' in c and "placeholder: \"Beschreibung...\"" not in c
    assert "onClick: addPruefTermin, disabled: !tDatum" in c


def test_keine_textdreiecke_und_kein_emoji_in_knoepfen(index_html, fv):
    a = index_html.index("function FlotteKostenPanel(")
    for t in ("▼", "▲"):
        assert t not in _code(fv), t
        assert t not in _code(index_html[a:index_html.index("function FahrzeugView(")]), t
    c = _code(fv)
    for e in ('"💾 Speichern"', '"⚠️ Melden"', '"💰 Literpreis: "', '"💰 Servicekosten gesamt: "'):
        assert e not in c, e
    assert 'chevron:["M6 9l6 6 6-6"]' in index_html


def test_ci_farben_liste(fv):
    c = _code(fv)
    assert 'borderLeft:"4px solid "+(isMine?"#22c55e"' not in c, "alte Randregel (blau als Grundfarbe)"
    assert 'React.createElement(Kpi, { label: "Fahrzeuge", value: aktiv, color: COLORS.EP_GREEN' in c
    assert 'borderColor:"#f97316",color:"#f97316"' not in c, "Sammel-Tanken-Knopf orange"


# ── 7. Schreibwege und Rechte unveraendert ──────────────────────────────────
HANDLER = {
    "upd": "b0a394b6856dc10ff7f8b702f36ede00",  # v3.9.1059 Fahrzeug-Archiv: PUT-Rumpf ohne Archiv-Spalten (_fzOhneArchiv), bewusst neu gehasht
    "addKm": "e07cc31bf5a2a8a5fac318fe65fbcb49",  # v3.9.1096 km-Pruefung (_fzKmPruef: Zahl, >=0, <=2.000.000; addKm liest ueber _ganzZahl statt replace(/[^\\d-]/g)) + addTank kmLogId km_<tankId> (idempotente km-Zeile) - bewusst neu gehasht; vorher 532f6979ad8e6b597713c9fda235ec54
    "addTank": "d3b4616ae7a13e840640f5ed0308aa05",  # v3.9.1051 Tankbuch atomar (_tankAtomar-Hinweis), bewusst neu gehasht | v3.9.1096 km-Pruefung (_fzKmPruef: Zahl, >=0, <=2.000.000; addKm liest ueber _ganzZahl statt replace(/[^\\d-]/g)) + addTank kmLogId km_<tankId> (idempotente km-Zeile) - bewusst neu gehasht; vorher 832cdbd6bdaa642329df7a6bfaba1d9f
    "addSchaden": "31c58844425685f1f49f9fb7f92d6a00",
    "qDoKm": "d4d6533dc1228cb0ee61ef7a51acfc14",  # v3.9.1096 km-Pruefung (_fzKmPruef: Zahl, >=0, <=2.000.000; addKm liest ueber _ganzZahl statt replace(/[^\\d-]/g)) + addTank kmLogId km_<tankId> (idempotente km-Zeile) - bewusst neu gehasht; vorher 43114fce51126af9a5fe1c113182445d |  # v3.9.1093 km/Kosten-Felder text statt number: Leser _ganzZahl/_fzZahl statt parseInt/parseFloat - bewusst neu gehasht; Rueckbau genau dieser Ersetzungen ergibt den alten Hash cc49299a34c3cbbbf787e50d549a6b7d
    "qDoTank": "8156199f1896eb63e49f634558cbd5ac",  # v3.9.1096 km-Pruefung (_fzKmPruef: Zahl, >=0, <=2.000.000; addKm liest ueber _ganzZahl statt replace(/[^\\d-]/g)) + addTank kmLogId km_<tankId> (idempotente km-Zeile) - bewusst neu gehasht (QR-Tank-km); vorher 5aa434dc61cf61a658a33f2b3c27f601 |  # v3.9.1092 Tank-Eingabe text statt number: Liter/Preis ueber _fzZahl statt parseFloat(replace) - gleiche Zahl fuer jede frueher moegliche Eingabe, bewusst neu gehasht
    "qDoSchaden": "6aa09e85b8e7807dcc2e0b3e2c5e1d3a",
    "batchSave": "18d82dbd43ff1d2be6777d4f5f220b88",  # v3.9.1096 km-Pruefung (_fzKmPruef: Zahl, >=0, <=2.000.000; addKm liest ueber _ganzZahl statt replace(/[^\\d-]/g)) + addTank kmLogId km_<tankId> (idempotente km-Zeile) - bewusst neu gehasht (Batch-Tank-km); vorher 92689ceca8d53c59999b3d80c6626f98 |  # v3.9.1092 Tank-Eingabe text statt number: Liter/Preis ueber _fzZahl statt parseFloat(replace) - gleiche Zahl fuer jede frueher moegliche Eingabe, bewusst neu gehasht
    "batchDel": "1af738b359919fc452fd16aca16d46c3",  # v3.9.1051 Tankbuch atomar (fz_tanklog_del), bewusst neu gehasht
    "addFz": "7cfaeb135c4485bdade3e2f6a6c052fd",  # v3.9.1093 km/Kosten-Felder text statt number: Leser _ganzZahl/_fzZahl statt parseInt/parseFloat - bewusst neu gehasht; Rueckbau genau dieser Ersetzungen ergibt den alten Hash aa601e73f08d3f41f0dbbb80b7c34aa7
    "del": "c6d7207e48ad696d2c0858efee2c3339",  # v3.9.1059 GF 19.11.: Archivieren (PATCH, nur Admin) statt DELETE, bewusst neu gehasht
    "addTermin": "dfcc6d696018722f6b5aea97c05bd20d",
    "delTermin": "084d959cc6c925e1f954e86afa33015d",
    "togTermin": "e210143699d9c8bf3ed21734cf025371",
    "addPruefTermin": "61a00e67740aa20ebcdb37dcd5e08397",
    "_finSpeichern": "7c82e1bbb37edb71a3bb5e9ea9daa3d2",
    "_zulHoch": "46a3f041993855a0132297c758c8b8f8",
    "_addSvcDoc": "6cc0824de55065e3a6368d1e488956c7",
    "_delSvcDoc": "efbc0ae450efd673959606349c83aca6",
    "openBatch": "0f3ec99be124a40ed4a2bfe233c5b8db",
}


@pytest.mark.parametrize("name", sorted(HANDLER))
def test_schreib_handler_byte_gleich(index_html, name):
    t = _comp_const(index_html, name)
    assert hashlib.md5(t.encode("utf-8")).hexdigest() == HANDLER[name], (
        "Handler %s hat sich veraendert - der UX-Umbau darf keinen Schreibweg anfassen" % name)


def _schreibaufrufe(fv):
    out = []
    for m in re.finditer(r"(?<![\w.])(upd|SQ\.push)\(", fv):
        e = _scan_to(fv, m.end(), ")")
        out.append(fv[m.start():e + 1])
    return sorted(out)


def test_alle_upd_und_sq_aufrufe_byte_gleich(fv):
    """54 Aufrufe (upd(...) in Handlern UND in onChange der Felder, SQ.push(...)) - als Menge
    vor dem Umbau gehasht. Verschieben ist erlaubt, Aendern nicht."""
    z = _schreibaufrufe(fv)
    # v3.9.1059: SQ.push DELETE /api/fahrzeuge entfaellt (Archivieren per PATCH), der PUT in upd() laeuft ueber _fzOhneArchiv
    assert len(z) == 53, len(z)
    # v3.9.1051: addTank/batchDel tragen den _tankAtomar-Hinweis (Tankbuch atomar) - bewusst neu gehasht
    # v3.9.1093 km/Kosten-Felder text statt number: Leser _ganzZahl/_fzZahl statt parseInt/parseFloat - bewusst neu gehasht; Rueckbau genau dieser Ersetzungen ergibt den alten Hash 4455bf75c593d6605c33b926825217d7 (Serviceheft km/Kosten im onChange)
    # v3.9.1096 km-Pruefung (_fzKmPruef) in addKm/qDoKm/qDoTank/batchSave + addTank kmLogId km_<tankId> - bewusst neu gehasht; vorher 7757af7d11f9740d90e223c58a478501 (Anzahl unveraendert 53)
    assert hashlib.md5("\n".join(z).encode("utf-8")).hexdigest() == "e0e124f9eb623f1703d9af10b8047624"


def test_koeder_schreibaufruf_aenderung_wird_erkannt(fv):
    alt = 'f.schaeden=[{...data,by_user:'
    assert fv.count(alt) == 1
    z = _schreibaufrufe(fv.replace(alt, 'f.schaeden=[{...data,von:', 1))
    assert hashlib.md5("\n".join(z).encode("utf-8")).hexdigest() != "7757af7d11f9740d90e223c58a478501"


def test_neue_teile_schreiben_nichts(fv):
    a = fv.index("  const _einzelFz=")
    b = fv.index("  return (\n    React.createElement('div', {}", a)
    neu = fv[a:b]
    for verboten in ("SQ.push", "upd(", "setFahrzeuge", "localStorage", "_sbPatch", "_sbPost"):
        assert verboten not in neu, verboten


def test_finanzen_und_fahrerwahl_unveraendert(fv):
    c = _code(fv)
    assert "const _darfFin=_maStaffRolle(curUser);" in c
    assert c.count("_maStaffRolle(") == 2, "Finanz-Sichtbarkeit nur ueber _maStaffRolle (Rolle + Fristen-Ansicht)"
    assert "_maWaehlbar((monteure||MONT),selFz.fahrer||\"\")" in c
    assert "_maWaehlbar((monteure||MONT),nf.fahrer)" in c


def test_keine_tageszahl_als_literal(index_html):
    a = index_html.index("function _fzArt(")
    b = index_html.index("function _wzKalibFaellig(", a)
    assert "86400000" not in index_html[a:b]
