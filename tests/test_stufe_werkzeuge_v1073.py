# -*- coding: utf-8 -*-
"""Stufe 4 Werkzeuge (GF 19.11.2026, "EINE Oberflaeche, drei Breiten-Stufen").

Vorher: WerkzeugView kannte ww<BP_MOB (isMob) und ww<768 (Karten statt
Tabelle). 768-1099 bekam die volle Tabelle mit fester Mindestbreite, die
Kennzahlen waren vier hohe Kacheln, und am Tablet hiessen zwei verschiedene
Zahlen gleich ("Kalibrierung faellig (6)" im Filter, "(1)" in der Auswertung).

Entscheidung Tabelle statt Karten in "mittel": die Werkzeugliste ist eine
Arbeitsliste mit Handlungen IN der Zeile (Auswahlkaestchen fuer die
Sammelaenderung Status/Ausgeben/Standort, Ausleihen/Zurueck, Bearbeiten,
Sortierkoepfe). Owner-Vorgabe aus den Arbeitsscheinen (1070): solche Listen
bleiben am Tablet hochkant Tabelle; nur der Tabellenkasten rollt quer, die
Erkennungsspalte (Kaestchen + Inventar-Nr.) klebt links, Koepfe brechen nicht
um. Karten gibt es nur in "schmal" (Handy).

Was hier gesichert wird:
1. Stufe NUR ueber _layoutStufe - mit echtem Code fuer 384, 412, 800x1280,
   1280x800, 1920x1080 ausgefuehrt (Stufe, isMob, Karte, Kennzahlen-Klasse,
   Tabellen-Mindestbreite, klebende Spalte).
2. EIN Tabellenzweig fuer mittel und breit - die Handlungen in der Zeile sind
   dieselben; die Stufe darf dort nur Darstellung steuern.
3. Abdeckung: keine eigene Breitenabfrage in WerkzeugView, kein userAgent.
4. Zaehlung: ein Name je Zahl ("Kalibrierung faellig" = _wzKalibFaellig in
   Kachel, Filter, Klappzeile, Startseiten-Kachel; der Status heisst
   "Zur Kalibrierung"). Gemessen am 19.11. (Prod, nur lesend): 296 Geraete,
   6 nach _wzKalibFaellig, 1 mit Status kalibrierung (liegt in den 6).
5. Trefferflaechen >= 44 px: Zustand-Sterne (Formular), Auswahlkaestchen,
   Bearbeiten-Stift; Kennzahlen am Handy zugeklappt, kein Querrollen.
6. Ausleihe (1062/1063: wzSelfOut, wzSelfIn, _wzQuickBtn) byte-gleich.
Jeder Riegel hat eine Umkehrprobe.
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

DEKL = ('const _wzStufe=_layoutStufe(ww,(typeof window!=="undefined"?window.innerHeight:0));'
        'const isMob=_wzStufe==="schmal";const _wzKarte=_wzStufe==="schmal";const _wzMittel=_wzStufe==="mittel";')
KPI_KLASSE = ('className: "kpi-grid"+(_wzStufe==="breit"?"":(" epk-leiste epk-kachel-kompakt epk-wz-kpi "'
              '+(isMob?"epk-kachel-zwei":"epk-kachel-vier")))')
TAB_MIN = "minWidth:_wzMittel?0:800"
KLEB = 'const _wzKlebSp=(links,bg)=>_wzMittel?{position:"sticky",left:links,zIndex:1,background:bg}:{};'
KARTEN = "_wzKarte&&filtered.length>0&&React.createElement('div', {"
TABELLE = "!_wzKarte&&React.createElement('div', { 'data-wz-tabelle': _wzStufe"
TAB_ENDE = "/* ═══ CHECK-IN / CHECK-OUT ═══ */"


@pytest.fixture(scope="module")
def roh():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _wz(src):
    a = src.index("function WerkzeugView(")
    # WerkzeugView steht am Dateiende ohne Nachfolge-Funktion; der Rumpf ist eingerueckt,
    # die erste "}" am Zeilenanfang schliesst sie.
    return src[a:src.index("\n}", a) + 2]


def _stufe_code(src):
    i = src.index("const BP_MOB=600;")
    mob = src[i:i + len("const BP_MOB=600;")]
    j = src.index("const BP_BREIT=")
    k = src.index("function _grobZeiger(", j)
    return mob + "\n" + src[j:k]


STUFE_KPI = "kpi-grid epk-leiste epk-kachel-kompakt epk-wz-kpi "
KLEBT = {"position": "sticky", "left": 44, "zIndex": 1, "background": "x"}
# (Breite, Hoehe) -> (Stufe, isMob, Karte, Kennzahlen-Klasse, Tabellen-Mindestbreite, klebende Spalte)
FAELLE = [
    ([384, 832], ["schmal", True, True, STUFE_KPI + "epk-kachel-zwei", 800, {}]),
    ([412, 915], ["schmal", True, True, STUFE_KPI + "epk-kachel-zwei", 800, {}]),
    ([800, 1280], ["mittel", False, False, STUFE_KPI + "epk-kachel-vier", 0, KLEBT]),
    ([1280, 800], ["breit", False, False, "kpi-grid", 800, {}]),
    ([1920, 1080], ["breit", False, False, "kpi-grid", 800, {}]),
]


def _entscheidung(node_exe, src, faelle):
    """Fuehrt die ECHTEN Ausdruecke aus WerkzeugView aus (nicht abgeschrieben)."""
    v = _wz(src)
    assert v.count(DEKL) == 1
    assert v.count(KPI_KLASSE) == 1 and v.count(TAB_MIN) == 1 and v.count(KLEB) == 1
    kl = KPI_KLASSE[len("className: "):]
    mi = TAB_MIN[len("minWidth:"):]
    js = ("var window={innerWidth:0,innerHeight:0};\n" + _stufe_code(src) + "\n"
          "function f(ww,hh){window.innerWidth=ww;window.innerHeight=hh;" + DEKL + KLEB
          + "return [_wzStufe,isMob,_wzKarte," + kl + "," + mi + ",_wzKlebSp(44,\"x\")];}\n"
          "process.stdout.write(JSON.stringify(" + json.dumps(faelle)
          + ".map(function(x){return f(x[0],x[1]);})));")
    return json.loads(run_node_snippet(node_exe, js))


def test_entscheidung_fuer_fuenf_groessen(roh, node_exe):
    r = _entscheidung(node_exe, roh, [f for f, _ in FAELLE])
    assert r == [e for _, e in FAELLE], list(zip([f for f, _ in FAELLE], r))


def test_umkehr_breite_grenze_auf_handy_waere_rot(roh, node_exe):
    """Mit BP_BREIT=600 bekaeme das Tablet hochkant wieder Mindestbreite 800 und hohe Kacheln."""
    kaputt = roh.replace("const BP_BREIT=1100;", "const BP_BREIT=600;", 1)
    assert kaputt != roh
    assert _entscheidung(node_exe, kaputt, [f for f, _ in FAELLE]) != [e for _, e in FAELLE]


def test_dieselbe_handy_grenze_wie_vorher(roh, node_exe):
    """schmal == alte isMob (ww<BP_MOB): Karten am Handy wie bisher."""
    r = _entscheidung(node_exe, roh, [[599, 900], [600, 900]])
    assert [x[1] for x in r] == [True, False] and [x[2] for x in r] == [True, False]


# ── Ein Tabellenzweig fuer mittel und breit ─────────────────────────────────
def _tabelle(v):
    t = v.index(TABELLE)
    return v[t:v.index(TAB_ENDE, t)]


HANDLUNGEN = [
    "onChange: _selectAll",
    "onChange: ()=>_toggleSelect(w.id)",
    "_wzQuickBtn(w)",
    "onClick: e=>{e.stopPropagation();openEdit(w);}",
    "onClick: ()=>{if(isAdmin)openEdit(w);}",
    "onClick: h.c?()=>toggleSort(h.c):undefined",
]
# Stufenabhaengig im Tabellenzweig ist NUR Darstellung:
NUR_DARSTELLUNG = [
    re.compile(re.escape(TABELLE)),  # das Tor des Zweigs selbst (mittel UND breit)
    re.compile(r"_wzKlebSp\((?:0|44),(?:_wzKopfBg|_wzZeileBg\(w\))\)"),
    re.compile(re.escape('className: _wzMittel?"epk-wz-mittel":undefined')),
    re.compile(re.escape(TAB_MIN)),
    re.compile(re.escape("'data-wz-tabelle': _wzStufe")),
    re.compile(r"fontSize:isMob\?"),
]


def _stufen_reste(tab):
    for m in NUR_DARSTELLUNG:
        tab = m.sub("", tab)
    return re.findall(r"_wzMittel|_wzStufe|_wzKarte|isMob", tab)


def test_ein_tabellenzweig_handlungen_gleich(roh):
    v = _wz(roh)
    assert v.count(TABELLE) == 1 and v.count(KARTEN) == 2
    assert "(ww<768)" not in v and "(ww>=768)" not in v
    tab = _tabelle(v)
    for h in HANDLUNGEN:
        assert h in tab, h
    assert _stufen_reste(tab) == [], "Stufe steuert im Tabellenzweig mehr als Darstellung"


def test_umkehr_handlung_nur_breit_waere_rot(roh):
    v = _wz(roh)
    tab = _tabelle(v)
    kaputt = tab.replace("_wzQuickBtn(w)/*", "_wzMittel?null:_wzQuickBtn(w)/*", 1)
    assert kaputt != tab and _stufen_reste(kaputt)


def test_mittel_klebt_links_und_rollt_nur_im_kasten(roh):
    v = _wz(roh)
    tab = _tabelle(v)
    assert "className: \"scroll-x\"" in tab and "style: {...CC(),padding:0,overflow:\"hidden\"}" in tab
    assert tab.count("_wzKlebSp(0,") == 2 and tab.count("_wzKlebSp(44,") == 2
    assert "...(i===0?_wzKlebSp(44,_wzKopfBg):{})" in tab
    css = _css(roh)
    assert "table.epk-wz-mittel th { white-space: nowrap; }" in css
    assert "table.epk-wz-mittel thead th:nth-child(-n+2) { z-index: 2 !important; }" in css


# ── Kennzahlen ──────────────────────────────────────────────────────────────
def test_kennzahlen_am_handy_zugeklappt(roh):
    v = _wz(roh)
    assert "const [_wzKpiAuf,_wzSetKpiAuf]=_react.useState.call(void 0, false);" in v
    i = v.index("'data-wz-kpi-klapp'")
    knopf = v[v.rfind("React.createElement('button'", 0, i):v.index("_klappIk(_wzKpiAuf,16))", i)]
    assert "minHeight:44" in knopf and "'aria-expanded': _wzKpiAuf?\"true\":\"false\"" in knopf
    assert "!(isMob&&_wzFeld)&&isMob&&React.createElement('button'" in v
    assert "!(isMob&&_wzFeld)&&(!isMob||_wzKpiAuf)&&React.createElement('div', { " + KPI_KLASSE in v
    assert "!(isMob&&_wzFeld)&&(!isMob||_wzKpiAuf)&&_wzRestTeile.length>0" in v


def _css(roh):
    a = roh.index("<style")
    return roh[a:roh.index("</style>", a)]


def _kpi_css_ok(css):
    regeln = re.findall(r"[^\n{}]*epk-wz-[^{]*\{[^}]*\}", css)
    if len(regeln) < 3:
        return False
    for r in regeln:
        if "overflow-x" in r or "display: none" in r:
            return False
        for px in re.findall(r"font-size:\s*(\d+)px", r):
            if int(px) < 12:
                return False
    return any("epk-wz-kpi" in r and "tabular-nums" in r for r in regeln)


def test_css_ohne_querrollen_und_mit_ziffern(roh):
    assert _kpi_css_ok(_css(roh))


def test_umkehr_querrollende_kacheln_waeren_rot(roh):
    alt = ".kpi-grid.epk-wz-kpi > div > div:nth-child(3) { font-variant-numeric: tabular-nums; }"
    assert alt in roh
    assert not _kpi_css_ok(_css(roh.replace(alt, alt.replace("{ ", "{ overflow-x: auto; "), 1)))


# ── Abdeckung ───────────────────────────────────────────────────────────────
# Gepinnte gemeinsame Ausdruecke, die ww nur WEITERGEBEN (kein eigener Vergleich):
#   _wzKlebTop(ww)  - Klebehoehe der Suchzeile, gemeinsam mit FahrzeugView, gepinnt in
#                     test_scan1051_funde_v1053 / test_fahrzeuge_ux_v1049. Bleibt.
BREITEN_MUSTER = re.compile(r"\bww\s*[<>]=?|innerWidth\s*[<>]=?|matchMedia|userAgent|navigator\.(?!mediaDevices)")
# navigator.mediaDevices = Kamera fuer den QR-Scan, keine Breiten- oder Geraeteerkennung.


def _fremde_breiten(src):
    code = nur_code(_wz(src))
    return [code[max(0, m.start() - 50):m.end() + 30] for m in BREITEN_MUSTER.finditer(code)]


def test_abdeckung_keine_eigenen_breitenvergleiche(roh):
    funde = _fremde_breiten(roh)
    assert not funde, "Eigene Breitenvergleiche statt _layoutStufe:\n" + "\n".join(funde)


def test_abdeckung_fragt_die_stufe(roh):
    v = _wz(roh)
    assert DEKL in v and "const isMob=ww<BP_MOB;" not in v
    assert "const _wzKleb=_wzKlebTop(ww);" in v  # gepinnter gemeinsamer Ausdruck (s.o.)


def test_umkehr_abdeckung_findet_neuen_vergleich(roh):
    kaputt = roh.replace("const _wzKarte=_wzStufe===\"schmal\";", "const _wzKarte=ww<768;", 1)
    assert kaputt != roh and _fremde_breiten(kaputt)
    kaputt2 = roh.replace(TAB_MIN, "minWidth:window.innerWidth<1000?640:800", 1)
    assert kaputt2 != roh and _fremde_breiten(kaputt2)
    kaputt3 = roh.replace(DEKL, DEKL + "const _ua=/Android/.test(navigator.userAgent);", 1)
    assert _fremde_breiten(kaputt3)


def _bloecke(s):
    aus = []
    for m in re.finditer(r"<script\b[^>]*>", s, re.I):
        e = s.find("</script>", m.end())
        aus.append((m.end(), e if e > 0 else len(s)))
    return aus


def test_stufe_steht_im_block_von_werkzeugview(roh):
    bl = _bloecke(roh)
    p1, p2 = roh.index("function _layoutStufe(w,h){"), roh.index("function WerkzeugView(")
    n1 = [n for n, (a, b) in enumerate(bl) if a <= p1 < b]
    n2 = [n for n, (a, b) in enumerate(bl) if a <= p2 < b]
    assert n1 and n2 and n1[0] == n2[0]


# ── Zaehlung: ein Name je Zahl ──────────────────────────────────────────────
GERAETE = [
    {"id": 1, "status": "verfuegbar", "naechsteKalib": "2026-06-30"},    # ueberfaellig
    {"id": 2, "status": "kalibrierung", "naechsteKalib": "2027-01-15"},  # Hand-Status
    {"id": 3, "status": "verfuegbar", "naechsteKalib": "0000-00-00"},    # Junk
    {"id": 4, "status": "ausgegeben", "naechsteKalib": "2026-08-29"},    # heute
    {"id": 5, "status": "verfuegbar", "naechsteKalib": "2027-03-01"},    # gut
]


def _zeile(src, nadel, anker=False):
    z = [l for l in nur_code(src).splitlines() if (re.match(nadel, l) if anker else nadel in l)]
    assert len(z) == 1, (nadel, len(z))
    return z[0]


def _benennung(src):
    """Name -> Zahl fuer jede Stelle, die die Faelligkeit oder den Status nennt.
    Namen und Zaehlausdruecke kommen aus index.html."""
    v = _wz(src)
    kpi = re.search(r"React\.createElement\(Kpi, \{ label: \"([^\"]+)\" , value: kalibFaellig,", v).group(1)
    chip = re.search(r"\{key:'kalib_faellig',label:'([^']+)'\}", v).group(1)
    klapp = re.search(r"kalibFaellig, \" ([^\"]+)\"\), _klappIk\(_wzKpiAuf", v).group(1)
    start = re.search(r"_metric\('([^']+)',wzKalibFaellig,", src).group(1)
    assert "const wzKalibFaellig=werkzeuge.filter(w=>_wzKalibFaellig(w)).length;" in src
    # Auswertung "Werkzeuge nach Status": Name = WZ_STATUS[k].l, Zahl = Status-Zaehlung
    assert "Object.entries(WZ_STATUS).map(([k,v])=>({l:v.l,v:werkzeuge.filter(w=>w.status===k).length" in src
    wzs = re.search(r"const WZ_STATUS=\{.*?\};", src).group(0)
    js = "\n".join([
        "const GER=" + json.dumps(GERAETE) + ";",
        "const R=Date;global.Date=class extends R{constructor(...a){if(a.length===0)super('2026-08-29T09:00:00+02:00');"
        "else super(...a);}static now(){return new R('2026-08-29T09:00:00+02:00').getTime();}};",
        _zeile(src, r"^const _ymd=d=>", True),
        _zeile(src, r"^const td2=\(\)=", True),
        _zeile(src, "function _isValidKalibDate(s){"),
        _zeile(src, "function _wzKalibFaellig(w){"),
        "const COLORS={ERROR:'#ef4444'};" + wzs,
        "const werkzeuge=GER;",
        _zeile(src, "const kalibFaellig=werkzeuge.filter("),
        "const cnt={kalib_faellig:0};for(const w of GER){" + _zeile(src, "cnt.kalib_faellig++").strip() + "}",
        "process.stdout.write(JSON.stringify({kalib:kalibFaellig,chip:cnt.kalib_faellig,"
        "statusName:WZ_STATUS.kalibrierung.l,status:GER.filter(w=>w.status==='kalibrierung').length}));",
    ])
    return kpi, chip, klapp, start, js


def _paare(node_exe, src):
    kpi, chip, klapp, start, js = _benennung(src)
    r = json.loads(run_node_snippet(node_exe, js))
    return [(kpi, r["kalib"]), (chip, r["chip"]), (klapp, r["kalib"]), (start, r["kalib"]),
            (r["statusName"], r["status"])]


def _ein_name_je_zahl(paare):
    namen = {}
    for n, z in paare:
        namen.setdefault(n, set()).add(z)
    return all(len(z) == 1 for z in namen.values())


def test_kalibrierung_faellig_eine_zahl_ein_name(roh, node_exe):
    p = _paare(node_exe, roh)
    assert p[0][1] == p[1][1] == 3, p  # Geraet 1, 2, 4 - Junk 3 nicht
    assert p[4][1] == 1, p
    assert _ein_name_je_zahl(p), p
    # dieselbe Zahl heisst ueberall gleich
    assert len({n for n, _ in p[:4]}) == 1 and p[0][0] == "Kalibrierung fällig", p
    assert p[4][0] == "Zur Kalibrierung"


def test_umkehr_alter_statusname_waere_rot(roh, node_exe):
    """Der Tablet-Befund: Status hiess wie die Faelligkeit -> "Kalibrierung faellig" = 3 UND 1."""
    kaputt = roh.replace('kalibrierung:{l:"Zur Kalibrierung"', 'kalibrierung:{l:"Kalibrierung fällig"', 1)
    assert kaputt != roh and not _ein_name_je_zahl(_paare(node_exe, kaputt))


def test_umkehr_alter_kachelname_waere_rot(roh, node_exe):
    kaputt = roh.replace('label: "Kalibrierung fällig" , value: kalibFaellig', 'label: "Service fällig" , value: kalibFaellig', 1)
    assert kaputt != roh
    p = _paare(node_exe, kaputt)
    assert len({n for n, _ in p[:4]}) != 1


def test_export_farbe_folgt_dem_statusnamen(roh):
    assert '"Zur Kalibrierung":"#eab308"' in _wz(roh) and '"Kalibrierung fällig":"#eab308"' not in roh


# ── Trefferflaechen ─────────────────────────────────────────────────────────
def _treffer(v):
    st = _zeile(v, "const Stars=({val,onChange})=>")
    w = int(re.search(r"minWidth:onChange\?(\d+):0", st).group(1))
    h = int(re.search(r"minHeight:onChange\?(\d+):0", st).group(1))
    f = int(re.search(r"fontSize:onChange\?(\d+):16", st).group(1))
    kasten = re.search(r"const _wzKastenFl=\{[^}]*minWidth:(\d+),minHeight:(\d+)", v)
    stift = re.search(r"'aria-label': \"Bearbeiten\",/\*.*?\*/style: \{\.\.\.bsS\(\),minWidth:(\d+),minHeight:(\d+)", v)
    return {"stern": (w, h, f), "kasten": tuple(int(x) for x in kasten.groups()),
            "kasten_n": v.count("React.createElement('label', { style: _wzKastenFl}"),
            "stift": tuple(int(x) for x in stift.groups())}


def _treffer_ok(t):
    w, h, f = t["stern"]
    return (w >= 44 and h >= 44 and f <= 22 and min(t["kasten"]) >= 44 and t["kasten_n"] == 2
            and min(t["stift"]) >= 44)


def test_sterne_kaestchen_stift_44(roh):
    t = _treffer(_wz(roh))
    assert _treffer_ok(t), t


def test_umkehr_kleine_sterne_waeren_rot(roh):
    v = _wz(roh)
    assert not _treffer_ok(_treffer(v.replace("minWidth:onChange?44:0,minHeight:onChange?44:0",
                                              "minWidth:onChange?24:0,minHeight:onChange?24:0", 1)))
    assert not _treffer_ok(_treffer(v.replace("minWidth:44,minHeight:44,cursor:\"pointer\",margin:0}",
                                              "minWidth:24,minHeight:24,cursor:\"pointer\",margin:0}", 1)))


# ── Ausleihe unveraendert (1062/1063) ───────────────────────────────────────
AUSLEIHE = {
    "  const wzSelfOut=(id)=>": "4f12eabdcbaef065d15dd4338a3c3d10",
    "  const wzSelfIn=(id)=>": "f4a5de7a2a41ca1f74cfa9f73240323a",
    "  const _wzQuickBtn=(w)=>": "7d3a0e21834b9fb95f27dfb87a641a27",
}


def test_ausleihe_byte_gleich(roh):
    for k, h in AUSLEIHE.items():
        a = roh.index(k)
        z = roh[a:roh.index("\n", a)].rstrip("\r")
        assert hashlib.md5(z.encode("utf-8")).hexdigest() == h, k
    assert roh.count("function _wzAusleiheBedingt(") == 1
