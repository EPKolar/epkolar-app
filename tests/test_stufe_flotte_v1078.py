# -*- coding: utf-8 -*-
"""Stufe 9 Flotte, Fahrzeuge, Bauprovisorien (GF 20.11.2026, "EINE Oberflaeche, drei Breiten-Stufen").

Vorher: FlotteView, FahrzeugView und BauprovisorienView entschieden selbst ueber
die Breite (isMob=ww<BP_MOB, FlotteView zusaetzlich mit einer nackten 600 fuer
den Anfangszustand der Fahrzeugliste). Am Tablet hochkant (800 px) stand in
Bauprovisorien nur EINE Kartenspalte (minmax(440px)), Tankprotokoll und
Monatsauswertung der Fahrzeugakte rollten am Handy mit sieben Spalten quer und
verloren am Tablet beim Querrollen die Datum-/Monatsspalte.

Jetzt (nur Darstellung):
  FlotteView     schmal = Handy-Zweig wie bisher; mittel und breit = Dreifenster
                 mit Ziehleiste wie bisher. Info-Karte (v1058, _fzInfoModus nach
                 Kartenhoehe) unveraendert. Komponente bis auf die Deklaration
                 byte-gleich.
  FahrzeugView   schmal = Tankprotokoll/Monatsauswertung als gestapelte Zeilen
                 mit Feldnamen (CSS epk-fv-karten, dieselben Zellen); mittel =
                 Tabellen bleiben Tabellen, erste Spalte klebt, Koepfe brechen
                 nicht um; breit = wie bisher.
  Bauprovisorien schmal = eine Spalte; mittel = zwei Kartenspalten; breit = wie
                 bisher.

Jeder Riegel mit Umkehrprobe.
"""
import hashlib
import io
import json
import os
import re

import pytest

from conftest import run_node_snippet
from _hilfen import nur_code

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")
HOEHE = '(typeof window!=="undefined"?window.innerHeight:0)'

DEKL_FL = 'const _flStufe=_layoutStufe(ww,' + HOEHE + ');const isMob=_flStufe==="schmal";'
DEKL_FV = ('const _fvStufe=_layoutStufe(ww,' + HOEHE + ');const isMob=_fvStufe==="schmal";const _fvMittel=_fvStufe==="mittel";'
           'const _fvKleb=(bg)=>_fvMittel?{position:"sticky",left:0,zIndex:1,background:bg}:{};')
DEKL_BP = 'const _bpStufe=_layoutStufe(ww,' + HOEHE + ');const isMob=_bpStufe==="schmal";const _bpMittel=_bpStufe==="mittel";'
LISTE_OFFEN = "const [listOpen,setListOpen]=_react.useState.call(void 0, !isMob);"
KLASSE_FV = 'isMob?"epk-fv-karten":_fvMittel?"epk-fv-mittel":undefined'
GRID_BP = 'isMob?"1fr":_bpMittel?"repeat(2,minmax(0,1fr))":"repeat(auto-fill,minmax(440px,1fr))"'

SPANNE = {
    "fl": ("\nfunction FlotteView(props){", "\n//@FLOTTE-AUSBAU-START"),
    "fv": ("\nfunction FahrzeugView({", "\nfunction PdfViewerModal("),
    "bp": ("\nfunction BauprovisorienView({", "\nfunction WerkzeugView("),
}


@pytest.fixture(scope="module")
def roh():
    return io.open(PFAD, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def _teil(src, k):
    a, b = SPANNE[k]
    i = src.index(a)
    return src[i:src.index(b, i)]


def _stufe_code(src):
    i = src.index("const BP_MOB=600;")
    mob = src[i:i + len("const BP_MOB=600;")]
    j = src.index("const BP_BREIT=")
    k = src.index("function _grobZeiger(", j)
    return mob + "\n" + src[j:k]


def _info_modus_code(src):
    i = src.index("function _fzInfoModus(")
    return src[i:src.index("\nfunction _fzPopupMaxH(", i)]


KLEBT = {"position": "sticky", "left": 0, "zIndex": 1, "background": "x"}
EINS, ZWEI, AUTO = "1fr", "repeat(2,minmax(0,1fr))", "repeat(auto-fill,minmax(440px,1fr))"
# (Breite, Hoehe) -> [Flotte: Stufe, isMob, Liste offen, Info-Modus | Fahrzeuge: Stufe, isMob, Klasse, Kleb | Bauprovisorien: Stufe, isMob, Grid]
FAELLE = [
    ([384, 832], ["schmal", True, False, "sheet", "schmal", True, "epk-fv-karten", {}, "schmal", True, EINS]),
    ([412, 915], ["schmal", True, False, "sheet", "schmal", True, "epk-fv-karten", {}, "schmal", True, EINS]),
    ([800, 1280], ["mittel", False, True, "popup", "mittel", False, "epk-fv-mittel", KLEBT, "mittel", False, ZWEI]),
    ([1280, 800], ["breit", False, True, "popup", "breit", False, None, {}, "breit", False, AUTO]),
    ([1920, 1080], ["breit", False, True, "popup", "breit", False, None, {}, "breit", False, AUTO]),
]


def _entscheidung(node_exe, src, faelle):
    """Fuehrt die ECHTEN Ausdruecke aus den drei Komponenten aus (nicht abgeschrieben)."""
    fl, fv, bp = _teil(src, "fl"), _teil(src, "fv"), _teil(src, "bp")
    assert fl.count(DEKL_FL) == 1 and fl.count(LISTE_OFFEN) == 1
    assert fl.count("_fzInfoModus(isMob,_selPosOk,_kartenH)") == 1
    assert fv.count(DEKL_FV) == 1 and fv.count("className: " + KLASSE_FV) == 2
    assert bp.count(DEKL_BP) == 1 and bp.count("gridTemplateColumns:" + GRID_BP) == 1
    js = ("var window={innerWidth:0,innerHeight:0};\n" + _stufe_code(src) + "\n" + _info_modus_code(src) + "\n"
          "function fl(ww){" + DEKL_FL + "return [_flStufe,isMob,!isMob,_fzInfoModus(isMob,true,0)];}\n"
          "function fv(ww){" + DEKL_FV + "return [_fvStufe,isMob," + KLASSE_FV + ",_fvKleb(\"x\")];}\n"
          "function bp(ww){" + DEKL_BP + "return [_bpStufe,isMob," + GRID_BP + "];}\n"
          "function f(ww,hh){window.innerWidth=ww;window.innerHeight=hh;"
          "return fl(ww).concat(fv(ww),bp(ww)).map(function(x){return x===undefined?null:x;});}\n"
          "process.stdout.write(JSON.stringify(" + json.dumps(faelle)
          + ".map(function(x){return f(x[0],x[1]);})));")
    return json.loads(run_node_snippet(node_exe, js))


def test_entscheidung_fuer_fuenf_groessen(roh, node_exe):
    r = _entscheidung(node_exe, roh, [f for f, _ in FAELLE])
    assert r == [e for _, e in FAELLE], list(zip([f for f, _ in FAELLE], r))


def test_umkehr_breite_grenze_auf_handy_waere_rot(roh, node_exe):
    kaputt = roh.replace("const BP_BREIT=1100;", "const BP_BREIT=600;", 1)
    assert kaputt != roh
    assert _entscheidung(node_exe, kaputt, [f for f, _ in FAELLE]) != [e for _, e in FAELLE]


def test_dieselbe_handy_grenze_wie_vorher(roh, node_exe):
    """schmal == alte isMob (ww<BP_MOB) und alte Liste (ww>=600): 599 Handy, 600 nicht - in allen drei."""
    r = _entscheidung(node_exe, roh, [[599, 900], [600, 900]])
    assert [(x[1], x[2], x[5], x[9]) for x in r] == [(True, False, True, True), (False, True, False, False)]


# ── mittel und breit: dieselben Bedienelemente ──────────────────────────────
NUR_DARSTELLUNG = {
    "fl": [re.escape(DEKL_FL)],
    "fv": [re.escape(DEKL_FV), re.escape("className: " + KLASSE_FV), r"\.\.\._fvKleb\(V\.cd\)"],
    "bp": [re.escape(DEKL_BP), re.escape("'data-bp-stufe':_bpStufe,style:{display:\"grid\",gridTemplateColumns:" + GRID_BP)],
}
NAMEN = {"fl": r"_flStufe", "fv": r"_fvMittel|_fvStufe|_fvKleb", "bp": r"_bpMittel|_bpStufe"}


def _stufen_reste(v, k):
    for m in NUR_DARSTELLUNG[k]:
        v = re.sub(m, "", v)
    return re.findall(NAMEN[k], nur_code(v))


@pytest.mark.parametrize("k", ["fl", "fv", "bp"])
def test_mittel_und_breit_unterscheiden_nur_darstellung(roh, k):
    assert _stufen_reste(_teil(roh, k), k) == []


def test_kleb_nur_an_den_ersten_spalten(roh):
    assert _teil(roh, "fv").count("..._fvKleb(V.cd)") == 4  # je Tabelle Kopf + erste Zelle


@pytest.mark.parametrize("k,alt", [
    ("fv", "React.createElement('button', { onClick: ()=>setShowSchaden(sel),"),
    ("bp", "h('button',{onClick:()=>_openEdit(p),"),
])
def test_umkehr_handlung_nur_breit_waere_rot(roh, k, alt):
    v = _teil(roh, k)
    assert v.count(alt) == 1
    stufe = {"fv": "_fvMittel", "bp": "_bpMittel"}[k]
    assert _stufen_reste(v.replace(alt, stufe + "?null:" + alt, 1), k)


# ── Abdeckung ───────────────────────────────────────────────────────────────
# Gepinnter gemeinsamer Seitentitel-Ausdruck (test_d9_seitenueberschriften_v956 u. a.)
AUSNAHMEN = ["fontSize:window.innerWidth<BP_MOB?UI.fSeiteMob:UI.fSeite"]
BREITEN_MUSTER = re.compile(r"\bww\s*[<>]=?|\(ww\|\|0\)\s*[<>]|innerWidth\s*[<>]=?|matchMedia|userAgent")
TITEL = {"fl": 0, "fv": 1, "bp": 1}


def _fremde_breiten(src, k):
    code = nur_code(_teil(src, k))
    for a in AUSNAHMEN:
        code = code.replace(a, "")
    return [code[max(0, m.start() - 50):m.end() + 30] for m in BREITEN_MUSTER.finditer(code)]


@pytest.mark.parametrize("k", ["fl", "fv", "bp"])
def test_abdeckung_keine_eigenen_breitenvergleiche(roh, k):
    funde = _fremde_breiten(roh, k)
    assert not funde, "Eigene Breitenvergleiche statt _layoutStufe:\n" + "\n".join(funde)
    assert _teil(roh, k).count(AUSNAHMEN[0]) == TITEL[k]
    assert "ww<BP_MOB" not in _teil(roh, k)


def test_umkehr_abdeckung_findet_neuen_vergleich(roh):
    assert _fremde_breiten(roh.replace('const isMob=_flStufe==="schmal";', "const isMob=ww<BP_MOB;", 1), "fl")
    assert _fremde_breiten(roh.replace(LISTE_OFFEN, LISTE_OFFEN.replace("!isMob", "ww>=600"), 1), "fl")
    assert _fremde_breiten(roh.replace('const isMob=_bpStufe==="schmal";', "const isMob=ww<BP_MOB;", 1), "bp")
    alt = 'gridTemplateColumns:isMob?"1fr":"1fr 1fr",gap:14'
    assert _teil(roh, "fv").count(alt) == 1
    v = _teil(roh, "fv")
    kaputt = roh.replace(v, v.replace(alt, alt.replace("isMob", "window.innerWidth<700"), 1), 1)
    assert _fremde_breiten(kaputt, "fv")


def _bloecke(s):
    aus = []
    for m in re.finditer(r"<script\b[^>]*>", s, re.I):
        e = s.find("</script>", m.end())
        aus.append((m.end(), e if e > 0 else len(s)))
    return aus


@pytest.mark.parametrize("name", ["function FlotteView(", "function FahrzeugView(", "function BauprovisorienView("])
def test_stufe_steht_im_selben_block(roh, name):
    bl = _bloecke(roh)
    p1, p2 = roh.index("function _layoutStufe(w,h){"), roh.index(name)
    n1 = [n for n, (a, b) in enumerate(bl) if a <= p1 < b]
    n2 = [n for n, (a, b) in enumerate(bl) if a <= p2 < b]
    assert n1 and n2 and n1[0] == n2[0]


# ── Logik byte-gleich (origin/main v3.9.1077, 9eab816) ──────────────────────
def _md5(t):
    return hashlib.md5(t.encode("utf-8")).hexdigest()


def _zurueck(v, dekl, alt):
    m = re.search(re.escape(dekl) + r"/\*.*?\*/", v)
    assert m, "Stufen-Deklaration samt Kommentar nicht gefunden"
    return v[:m.start()] + alt + v[m.end():]


def _flotte_zurueck(src):
    """Ganze FlotteView, zurueckgebaut: muss byte-gleich mit vorher sein (Darstellung UND Logik)."""
    v = _zurueck(_teil(src, "fl"), DEKL_FL, "const isMob=ww<BP_MOB;")
    assert v.count(LISTE_OFFEN) == 1
    return v.replace(LISTE_OFFEN, "const [listOpen,setListOpen]=_react.useState.call(void 0, ww>=600);")


def _fv_kopf_zurueck(src):
    """FahrzeugView vor dem Rendern: Zustaende, Abrufe, Handler, Schreibwege, Archivieren (v1060)."""
    v = _teil(src, "fv")
    v = v[:v.index("\n  return (\n")]
    return _zurueck(v, "  " + DEKL_FV, "  const isMob=ww<BP_MOB;")


def _bp_kopf_zurueck(src):
    v = _teil(src, "bp")
    v = v[:v.index('\n  if(sub==="form"){')]
    return _zurueck(v, "  " + DEKL_BP, "  const isMob=ww<BP_MOB;")


def _bp_formular(src):
    v = _teil(src, "bp")
    i = v.index('\n  if(sub==="form"){')
    return v[i:v.index("\n  return h('div',{className:\"fade-in\"", i + 5)]


MD5 = {
    "fl": "3290ca4052dfcddd7ab06273bf2a5f1c",      # ganze FlotteView
    "fv": "5847268424da811de652bfa2face74cf",      # FahrzeugView bis "return (" - v3.9.1092 Tank-Eingabe text statt number (qDoTank/batchSave/OCR-Vorbelegung ueber _fzZahl/_tankEinDE), bewusst neu gehasht | v3.9.1093 Zahlenfelder text statt number (ZahlEingabe/_fzZahl/_ganzZahl) - bewusst neu gehasht; Rueckbau genau dieser Ersetzungen ergibt den alten Hash 275b179f5e0f0c9692ea622fd50b1780
    "bp": "4d8af86d25a526e296ea68c40e3676cf",      # BauprovisorienView bis zum Formular-Zweig | v3.9.1093 Zahlenfelder text statt number (ZahlEingabe/_fzZahl/_ganzZahl) - bewusst neu gehasht; Rueckbau genau dieser Ersetzungen ergibt den alten Hash 91e2eaadaf5adba8e313c7661b7eb831
    "bpform": "8dee397383a62f07378a303b9286df3d",  # Bauprovisorien-Formular (unveraendert, ohne Rueckbau) | v3.9.1093 Zahlenfelder text statt number (ZahlEingabe/_fzZahl/_ganzZahl) - bewusst neu gehasht; Rueckbau genau dieser Ersetzungen ergibt den alten Hash bcabac6f11906f5c0808ea6623e49d41 | Render-Funde 1096: nur Anzeige - Speichern-Knopf EP_GREEN_DARK statt Verlauf ab #00A948 (3,10:1) mit Linien-Haken statt Textzeichen, summary "Kunde nicht im Stamm?" 44 px hoch - bewusst neu gehasht; der Altstand 5807fce ergibt den alten Hash 803081f9b8fe253ecc8bc07405c95b97
}
ZURUECK = {"fl": _flotte_zurueck, "fv": _fv_kopf_zurueck, "bp": _bp_kopf_zurueck, "bpform": _bp_formular}


@pytest.mark.parametrize("k", ["fl", "fv", "bp", "bpform"])
def test_logik_unveraendert(roh, k):
    assert _md5(ZURUECK[k](roh)) == MD5[k]


@pytest.mark.parametrize("k,alt,neu", [
    ("fl", "var _waehle=function(fid){", "var _waehle=function(fid){;"),
    ("fv", "const _fzZeile=f=>", "const _fzZeile=(f)=>"),
    ("bp", "const _nowYr=new Date().getFullYear();", "const _nowYr=new Date().getFullYear()+0;"),
])
def test_umkehr_handler_aenderung_waere_rot(roh, k, alt, neu):
    assert _teil(roh, k).count(alt) >= 1
    assert _md5(ZURUECK[k](roh.replace(alt, neu, 1))) != MD5[k]


# ── Lese-Tabellen: Feldnamen je Zelle ───────────────────────────────────────
KOEPFE = {
    "tank": ["Datum", "Liter", "Gesamt €", "€/L", "km", "Von", "Beleg"],
    "monate": ["Monat", "Tankungen", "Liter ges.", "Kosten ges.", "Ø €/L", "km gefahren", "Ø L/100km"],
}


TABELLEN_ENDE = {"tank": "(selFz.tankLog||[]).length>1&&", "monate": "(()=>{const totalL="}


def _tabelle(v, name):
    i = v.index("'data-fv-tabelle': \"%s\"" % name)
    return v[i:v.index(TABELLEN_ENDE[name], i)]


def _koepfe(t):
    kopf = t[t.index("React.createElement('thead'"):t.index("React.createElement('tbody'")]
    return re.findall(r"React\.createElement\('th', \{[^}]*\}+, \"([^\"]+)\"", kopf)


def _zellen(t):
    body = t[t.index("React.createElement('tbody'"):]
    z = re.findall(r"React\.createElement\('td', \{ 'data-l': \"([^\"]+)\"", body)
    return [x.replace("\\u20ac", "€").replace("\\u00d8", "Ø") for x in z]


@pytest.mark.parametrize("name", ["tank", "monate"])
def test_jede_zelle_traegt_ihren_feldnamen(roh, name):
    t = _tabelle(_teil(roh, "fv"), name)
    assert _koepfe(t) == KOEPFE[name]
    assert _zellen(t) == KOEPFE[name]
    body = t[t.index("React.createElement('tbody'"):]
    assert body.count("React.createElement('td', {") == len(KOEPFE[name])


def test_umkehr_zelle_ohne_feldnamen_waere_rot(roh):
    v = _teil(roh, "fv").replace("React.createElement('td', { 'data-l': \"km\", ", "React.createElement('td', { ", 1)
    assert _zellen(_tabelle(v, "tank")) != KOEPFE["tank"]


def _css(src):
    a = src.index("<style")
    return src[a:src.index("</style>", a)]


CSS_PFLICHT = [
    "table.epk-fv-mittel th { white-space: nowrap; }",
    "table.epk-fv-mittel thead th:first-child { z-index: 2 !important; }",
    "table.epk-fv-karten thead { display: none; }",
    "table.epk-fv-karten tr { display: grid; grid-template-columns: repeat(3,minmax(0,1fr));",
    "table.epk-fv-karten td[data-l]::before { content: attr(data-l); display: block; font-size: 12px;",
]


def test_css_vorhanden_ohne_breitenabfrage(roh):
    css = _css(roh)
    for z in CSS_PFLICHT:
        assert z in css, z
    regeln = re.findall(r"[^\n{}]*epk-fv-[^{]*\{[^}]*\}", css)
    assert len(regeln) == 7
    for r in regeln:
        assert "@media" not in r, r
        for px in re.findall(r"font-size:\s*(\d+)px", r):
            assert int(px) >= 12, r


def test_umkehr_kleine_feldnamen_waeren_rot(roh):
    alt = "table.epk-fv-karten td[data-l]::before { content: attr(data-l); display: block; font-size: 12px;"
    kaputt = roh.replace(alt, alt.replace("12px", "10px"), 1)
    with pytest.raises(AssertionError):
        test_css_vorhanden_ohne_breitenabfrage(kaputt)
