# -*- coding: utf-8 -*-
"""Stufe 6 Buero-Export (GF 19.11.2026, "EINE Oberflaeche, drei Breiten-Stufen").

Vorher: VBueroExport entschied an drei Stellen selbst ueber die Breite
((ww||0)<600 fuer die Reiterleiste, ww<BP_MOB fuer die Seite, innerWidth<700
in der Tankbeleg-Ansicht). Am Tablet hochkant quetschte die Monteur-Uebersicht
sieben Spalten ohne Kasten, die Kennzahlen waren vier hohe Kacheln, und der
Krankenstand hatte Spaltenkoepfe "Stunden/Status" ueber Zeilen, die alles als
Fliesstext in EINER Zelle trugen (Status gar nicht).

Entscheidung Tabelle in "mittel": die Listen hier sind Arbeitslisten mit
Handlungen in der Zeile (Bearbeiten-Stift je Monteur, Attest ansehen/loeschen,
Tankbeleg kontrollieren/zuruecksetzen, Sortierkoepfe). Owner-Vorgabe (1070):
solche Listen bleiben am Tablet hochkant Tabelle - erste Spalte klebt, nur der
Tabellenkasten rollt quer, Koepfe brechen nicht um. Karten bzw. gestapelte
Zeilen nur in "schmal".

Was hier gesichert wird (jeder Riegel mit Umkehrprobe):
1. Stufe NUR ueber _layoutStufe - mit echtem Code fuer 384, 412, 800x1280,
   1280x800, 1920x1080 ausgefuehrt.
2. mittel und breit haben dieselben Bedienelemente: _beMittel/_beStufe kommen
   im ganzen Bauteil nur in Darstellungs-Ausdruecken vor.
3. Abdeckung: keine eigene Breitenabfrage mehr ausser dem gemeinsamen,
   gepinnten Seitentitel-Ausdruck.
4. Exporte (Excel/PDF) byte-gleich: Quelltext-md5 der Exportfunktionen.
5. Stundensumme: Monteur-Uebersicht hat eine Summenzeile, und Summe + "ohne
   Mitarbeiter-Zuordnung" = Kachel "Stunden auf Projekten" + Unterzeile -
   mit dem echten Code nachgerechnet. Gemessen 19.11. (Prod, nur lesend,
   Summen): 197 Zeiteintraege 1111,7 h = 869,8 (aktive Projekte) + 39,8
   (archivierte/andere) + 202,0 (ohne Projekt); je Mitarbeiter summiert
   ebenfalls 1111,7 h, keine Buchung ohne bekannten Mitarbeiter. Die
   Tablet-Zahl 863,3 passt dazu (ein 6,5-h-Eintrag kam um 16 Uhr UTC dazu).
   Die vom Tablet gemeldeten 1.125,2 h fuer die Monteur-Zeilen sind mit
   demselben Datenstand nicht erklaerbar: die Zeilensumme kann den
   Kachelwert nur uebersteigen, wenn eine Mitarbeiter-Kennung doppelt in der
   Liste steht - dagegen sichert monteurStats jetzt ab (jede Kennung einmal).
6. ISO-Monat "2026-11" wird "November 2026" (Zulagen-Reiter).
7. Krankenstand: Zeitraum-Zeile traegt ihre Werte in den Spalten (Datum,
   Stunden, Status, Attest); Status lesbar.
8. Trefferflaechen >= 44 px, Kennzahlen am Handy zugeklappt.
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

DEKL = ('const _beStufe=_layoutStufe(ww,(typeof window!=="undefined"?window.innerHeight:0));'
        'const _beMittel=_beStufe==="mittel";var _bxMob=_beStufe==="schmal";')
ISMOB = 'const isMob=_beStufe==="schmal";'
KLEB = 'const _beKleb=(bg)=>_beMittel?{position:"sticky",left:0,zIndex:1,background:bg}:{};'
KPI_KLASSE = ('className: "kpi-grid"+(_beStufe==="breit"?"":(" epk-leiste epk-kachel-kompakt epk-be-kpi "'
              '+(isMob?"epk-kachel-zwei":"epk-kachel-vier")))')


@pytest.fixture(scope="module")
def roh():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _be(src):
    a = src.index("function VBueroExport(")
    return src[a:src.index("\nfunction _supplierSaveBody(", a)]


def _stufe_code(src):
    i = src.index("const BP_MOB=600;")
    mob = src[i:i + len("const BP_MOB=600;")]
    j = src.index("const BP_BREIT=")
    k = src.index("function _grobZeiger(", j)
    return mob + "\n" + src[j:k]


STUFE_KPI = "kpi-grid epk-leiste epk-kachel-kompakt epk-be-kpi "
KLEBT = {"position": "sticky", "left": 0, "zIndex": 1, "background": "x"}
# (Breite, Hoehe) -> (Stufe, isMob, _bxMob, Kennzahlen-Klasse, klebende Spalte)
FAELLE = [
    ([384, 832], ["schmal", True, True, STUFE_KPI + "epk-kachel-zwei", {}]),
    ([412, 915], ["schmal", True, True, STUFE_KPI + "epk-kachel-zwei", {}]),
    ([800, 1280], ["mittel", False, False, STUFE_KPI + "epk-kachel-vier", KLEBT]),
    ([1280, 800], ["breit", False, False, "kpi-grid", {}]),
    ([1920, 1080], ["breit", False, False, "kpi-grid", {}]),
]


def _entscheidung(node_exe, src, faelle):
    """Fuehrt die ECHTEN Ausdruecke aus VBueroExport aus (nicht abgeschrieben)."""
    v = _be(src)
    assert v.count(DEKL) == 1 and v.count(ISMOB) == 1 and v.count(KLEB) == 1 and v.count(KPI_KLASSE) == 1
    kl = KPI_KLASSE[len("className: "):]
    js = ("var window={innerWidth:0,innerHeight:0};\n" + _stufe_code(src) + "\n"
          "function f(ww,hh){window.innerWidth=ww;window.innerHeight=hh;" + DEKL + ISMOB + KLEB
          + "return [_beStufe,isMob,_bxMob," + kl + ",_beKleb(\"x\")];}\n"
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
    """schmal == alte isMob (ww<BP_MOB) und altes _bxMob ((ww||0)<600)."""
    r = _entscheidung(node_exe, roh, [[599, 900], [600, 900]])
    assert [x[1] for x in r] == [True, False] and [x[2] for x in r] == [True, False]


# ── mittel und breit: dieselben Bedienelemente ──────────────────────────────
# Jede Stelle, an der mittel/breit unterschieden wird, ist reine Darstellung:
NUR_DARSTELLUNG = [
    re.escape(DEKL), re.escape(ISMOB), re.escape(KLEB), re.escape(KPI_KLASSE),  # isMob = nur schmal
    re.escape('className: _beMittel?"epk-be-mittel":undefined'),
    re.escape('className:_beMittel?"epk-be-mittel":undefined'),
    re.escape("'data-be-monteure': _beStufe"),
]


def _stufen_reste(v):
    for m in NUR_DARSTELLUNG:
        v = re.sub(m, "", v)
    return re.findall(r"_beMittel|_beStufe", nur_code(v))


def test_mittel_und_breit_unterscheiden_nur_darstellung(roh):
    assert _stufen_reste(_be(roh)) == []


def test_umkehr_handlung_nur_breit_waere_rot(roh):
    v = _be(roh)
    # v3.9.1109: Stift stoppt jetzt das Hochblubbern (ganze Zeile klickbar) - Anker nachgezogen;
    # vorher "React.createElement('button', { onClick: ()=>editMonteurEntries(ms), style: _beStiftSt,"
    alt = "React.createElement('button', { onClick: e=>{e.stopPropagation();editMonteurEntries(ms);}, onKeyDown: e=>e.stopPropagation(), style: _beStiftSt,"
    assert v.count(alt) == 1
    kaputt = v.replace(alt, "_beMittel?null:" + alt, 1)
    assert _stufen_reste(kaputt)


def test_tabellen_in_mittel_mit_klebender_spalte(roh):
    v = _be(roh)
    # vier Tabellen (Monteure, Abwesenheiten, Krankenstand, Tank) tragen die Mittel-Klasse
    assert v.count('_beMittel?"epk-be-mittel":undefined') == 4
    # erste Spalte klebt: Monteure (Kopf, Zeile, Summe), Abwesenheit (Kopf, Zeile),
    # Krankenstand (Kopf, Zeitraum-Zeile), Tank (Kopf, Zeile)
    assert v.count("_beKleb(V.cd)") == 9
    assert "React.createElement('div', { className: \"scroll-x\", 'data-be-monteure': _beStufe}," in v
    css = _css(roh)
    assert "table.epk-be-mittel th { white-space: nowrap; }" in css
    assert "table.epk-be-mittel thead th:first-child { z-index: 2 !important; }" in css


def test_handy_karten_bleiben(roh):
    v = _be(roh)
    assert "isMob?(React.createElement('div',{'data-be-monteure':\"karten\"}" in v
    assert ":isMob?(React.createElement('div',{},view.map(function(r,i){var e=r.e;" in v  # Tank-Karten
    assert ",isMob?(React.createElement('div',{},_absRows().map(function(r){" in v  # Abwesenheit-Karten


# ── Abdeckung ───────────────────────────────────────────────────────────────
# Gepinnter gemeinsamer Ausdruck (Seitentitel, gleiches Muster an vielen Stellen,
# test_d9_seitenueberschriften_v956 / test_seitentitel_v1007 / test_as_hochformat_v1062):
AUSNAHMEN = ["fontSize:window.innerWidth<BP_MOB?UI.fSeiteMob:UI.fSeite"]
BREITEN_MUSTER = re.compile(r"\bww\s*[<>]=?|\(ww\|\|0\)\s*[<>]|innerWidth\s*[<>]=?|matchMedia|userAgent|navigator\.")


def _fremde_breiten(src):
    code = nur_code(_be(src))
    for a in AUSNAHMEN:
        code = code.replace(a, "")
    return [code[max(0, m.start() - 50):m.end() + 30] for m in BREITEN_MUSTER.finditer(code)]


def test_abdeckung_keine_eigenen_breitenvergleiche(roh):
    funde = _fremde_breiten(roh)
    assert not funde, "Eigene Breitenvergleiche statt _layoutStufe:\n" + "\n".join(funde)
    assert _be(roh).count(AUSNAHMEN[0]) == 1


def test_umkehr_abdeckung_findet_neuen_vergleich(roh):
    assert _fremde_breiten(roh.replace(ISMOB, "const isMob=ww<BP_MOB;", 1))
    assert _fremde_breiten(roh.replace("var _bxMob=_beStufe===\"schmal\";", "var _bxMob=(ww||0)<600;", 1))
    v = _be(roh)
    i = v.index('flexDirection:isMob?"column":"row"')
    assert _fremde_breiten(roh.replace(v[i:i + 40], v[i:i + 40].replace("isMob", "window.innerWidth<700"), 1))


def _bloecke(s):
    aus = []
    for m in re.finditer(r"<script\b[^>]*>", s, re.I):
        e = s.find("</script>", m.end())
        aus.append((m.end(), e if e > 0 else len(s)))
    return aus


def test_stufe_steht_im_block_von_vbueroexport(roh):
    bl = _bloecke(roh)
    p1, p2 = roh.index("function _layoutStufe(w,h){"), roh.index("function VBueroExport(")
    n1 = [n for n, (a, b) in enumerate(bl) if a <= p1 < b]
    n2 = [n for n, (a, b) in enumerate(bl) if a <= p2 < b]
    assert n1 and n2 and n1[0] == n2[0]


# ── Exporte byte-gleich ─────────────────────────────────────────────────────
def _quelle(src, anf):
    src = src.replace("\r\n", "\n")
    assert src.count(anf) == 1, (anf, src.count(anf))
    a = src.index(anf)
    e = src.index("\n", a)
    zeile = src[a:e]
    if zeile.rstrip().endswith("{"):
        ind = re.match(r"\s*", zeile).group(0)
        e = src.index("\n" + ind + "};", a) + len(ind) + 3
    return src[a:e]


# md5 des Quelltexts (LF) - Stand origin/main v3.9.1074, durch Stufe 6 NICHT veraendert.
EXPORT_MD5 = {
    "const genXls=(title,subtitle,headers,rows,filename,opts={})=>{": "8472db9de0084b7a6cdf1a492758c930",  # Paket 13a (GF 24.11.2026 abends): 3.9.1115 aendert KEINE Exportdatei - Excel-Aenderungen liegen auf feature/excel-stunden-zahl (test_exporte_golden_v1114.py), Hash wieder wie 3.9.1114 | Z9-Sperre (GF 24.11.2026 abends): CSS-Regel td.xs nur mit stdCols - Aufrufe ohne stdCols liefern dieselbe Datei wie 3.9.1114 (test_z9_exporte_unveraendert_p13c) - vorher 3d91fb63551846ec08715ad213381e94 | Paket 13 (GF 24.11.2026): Stunden-Anzeige zentral ueber fmtStd (genau zwei Nachkommastellen, Komma, leer bleibt leer) - Pin bewusst nachgezogen: opts.stdCols (Stunden-Spalten bleiben Zahl, Format 0,00) - vorher 8472db9de0084b7a6cdf1a492758c930
    "  const generateBWB=(proj,useFilters,scopeKW)=>{": "e72868132f574a32a53df0185a1bdad8",
    "  const generateAll=()=>{": "aea0f49dde6f0c3945b21bd87a31dcc9",
    "  const getProjectData=(projId)=>{": "3084cd316af562b72e5daaa03273f7bd",
    "  const _absExcel=()=>": "f32536f4e32674641996528bcc72d7d7",  # Paket 13a (GF 24.11.2026 abends): 3.9.1115 aendert KEINE Exportdatei - Excel-Aenderungen liegen auf feature/excel-stunden-zahl (test_exporte_golden_v1114.py), Hash wieder wie 3.9.1114 | Paket 13 (GF 24.11.2026): Stunden-Anzeige zentral ueber fmtStd (genau zwei Nachkommastellen, Komma, leer bleibt leer) - Pin bewusst nachgezogen: _n(..,2) + stdCols - vorher f32536f4e32674641996528bcc72d7d7
    "  const _krankExcel=()=>": "2e70fb11e3561d48bbe75caf23e08b7c",  # Paket 13a (GF 24.11.2026 abends): 3.9.1115 aendert KEINE Exportdatei - Excel-Aenderungen liegen auf feature/excel-stunden-zahl (test_exporte_golden_v1114.py), Hash wieder wie 3.9.1114 | Paket 13 (GF 24.11.2026): Stunden-Anzeige zentral ueber fmtStd (genau zwei Nachkommastellen, Komma, leer bleibt leer) - Pin bewusst nachgezogen: _n(..,2) + stdCols - vorher 2e70fb11e3561d48bbe75caf23e08b7c
    "  const _absRows=()=>": "8ccbb08003ce7ccde70d98f016f2485b",
    "  const _krankRows=()=>": "2319691cb0cf9f849bc363ad71d5be4d",
    "  const _pzeBtn=()=>{": "ed90b7902cf89328558d2f74c5f48397",
}


def _md5(t):
    return hashlib.md5(t.encode("utf-8")).hexdigest()


def test_exporte_byte_gleich(roh):
    falsch = {k: _md5(_quelle(roh, k)) for k, h in EXPORT_MD5.items() if _md5(_quelle(roh, k)) != h}
    assert not falsch, falsch


def test_umkehr_export_aenderung_waere_rot(roh):
    kaputt = roh.replace('"Krankenstand_"+_abYr+".xls"', '"Krank_"+_abYr+".xls"', 1)
    assert kaputt != roh
    assert _md5(_quelle(kaputt, "  const _krankExcel=()=>")) != EXPORT_MD5["  const _krankExcel=()=>"]


# ── Stundensumme: Monteur-Zeilen = Kachel + Unterzeile ──────────────────────
def _zeile_ab(src, anf):
    src = src.replace("\r\n", "\n")
    assert src.count(anf) == 1, anf
    a = src.index(anf)
    return src[a:src.index("\n", a)]


def _block(src, anf, ende):
    src = src.replace("\r\n", "\n")
    assert src.count(anf) == 1, anf
    a = src.index(anf)
    return src[a:src.index(ende, a) + len(ende)]


def _kpi_teile(src):
    m = re.search(r"var _pIds=new Set\(activeProjects\.map.*?var _hR=allEntries\.filter\(function\(e\)\{return !e\.projekt;\}\)"
                  r"\.reduce\(function\(s,e\)\{return s\+\(e\.stunden\|\|0\);\},0\);", src)
    assert m, "Kachel-Rechnung nicht gefunden"
    return m.group(0)


MONTEURE = [{"id": "w1", "n": "Alpha", "r": "Monteur"}, {"id": "w2", "n": "Beta", "r": "Monteur"},
            {"id": "w3", "n": "Gamma", "r": "Buero"}]
PROJEKTE = [{"id": "p1", "status": "aktiv", "name": "P1"}, {"id": "p2", "status": "archiviert", "name": "P2"}]
EINTRAEGE = [
    {"id": "e1", "datum": "2026-11-02", "projekt": "p1", "monteur": "w1", "stunden": 8.5},
    {"id": "e2", "datum": "2026-11-03", "projekt": "p1", "monteur": "w2", "stunden": 7.25},
    {"id": "e3", "datum": "2026-11-03", "projekt": "p2", "monteur": "w1", "stunden": 3},     # archiviert
    {"id": "e4", "datum": "2026-11-04", "projekt": "pX", "monteur": "w2", "stunden": 1.5},   # geloeschtes Projekt
    {"id": "e5", "datum": "2026-11-04", "projekt": "", "monteur": "w3", "stunden": 4},       # Schein/Freitext
    {"id": "e6", "datum": "2026-11-05", "projekt": "p1", "monteur": "wZ", "stunden": 2.4},   # Kennung unbekannt
]


def _summen(node_exe, src, monteure=None):
    v = _be(src)
    js = "\n".join([
        "const monteure=" + json.dumps(monteure if monteure is not None else MONTEURE) + ";",
        "const projects=" + json.dumps(PROJEKTE) + ";",
        "const allEntries=" + json.dumps(EINTRAEGE) + ";",
        "const allBT=[],allRegie=[],allMaengel=[];",
        "const activeProjects=projects.filter(p=>p.status!==\"archiviert\");",
        _zeile_ab(v, "  const _localD=(d)=>"),
        _zeile_ab(v, "  const _kwFromDate=(d)=>"),
        _zeile_ab(v, "  const _kwYearFromDate=(d)=>"),
        _block(v, "  const projStats=activeProjects.map(p=>{", "\n  });"),
        _block(v, "  const monteurStats=(monteure||[])", ".sort((a,b)=>b.hrs-a.hrs);"),
        _zeile_ab(v, "  const _beMaIds="),
        _kpi_teile(v),
        "const alle=allEntries.reduce((s,e)=>s+e.stunden,0);",
        "process.stdout.write(JSON.stringify({tabelle:_beMaSumme+_beOhneMa,ohne:_beOhneMa,"
        "kachel:_hP+_hA+_hR,teile:[_hP,_hA,_hR],alle:alle,zeilen:monteurStats.length}));",
    ])
    return json.loads(run_node_snippet(node_exe, js))


def test_summe_monteure_gleich_kachel_mit_unterzeile(roh, node_exe):
    r = _summen(node_exe, roh)
    assert round(r["tabelle"], 2) == round(r["kachel"], 2) == round(r["alle"], 2) == 26.65, r
    assert [round(x, 2) for x in r["teile"]] == [18.15, 4.5, 4.0], r
    assert round(r["ohne"], 2) == 2.4 and r["zeilen"] == 3, r


def test_doppelte_mitarbeiterzeile_zaehlt_nicht_doppelt(roh, node_exe):
    doppelt = MONTEURE + [dict(MONTEURE[0])]
    r = _summen(node_exe, roh, doppelt)
    assert round(r["tabelle"], 2) == round(r["kachel"], 2), r
    assert r["zeilen"] == 3, r


def test_umkehr_ohne_dedupe_waere_rot(roh, node_exe):
    """Ohne die Einmal-Regel uebersteigt die Zeilensumme die Kachel (Tablet-Befund 1.125,2 > 1.105,1)."""
    alt = "  const monteurStats=(monteure||[]).filter((m,i,a)=>m&&a.findIndex(x=>x&&x.id===m.id)===i)"
    assert alt in roh
    kaputt = roh.replace(alt, "  const monteurStats=(monteure||[])", 1)
    r = _summen(node_exe, kaputt, MONTEURE + [dict(MONTEURE[0])])
    assert r["tabelle"] > r["kachel"] + 1, r


def test_umkehr_ohne_zuordnungsrest_waere_rot(roh, node_exe):
    kaputt = roh.replace("const _beOhneMa=allEntries.filter(e=>!_beMaIds.has(e.monteur))", "const _beOhneMa=0&&allEntries.filter(e=>!_beMaIds.has(e.monteur))", 1)
    assert kaputt != roh
    r = _summen(node_exe, kaputt)
    assert round(r["tabelle"], 2) != round(r["kachel"], 2), r


def test_summenzeile_wird_angezeigt(roh):
    v = _be(roh)
    assert v.count("fmtStd(_beMaSumme+_beOhneMa)") == 2  # Tabelle (tfoot) + Handy-Summenkarte (Paket 13 (GF 24.11.2026): Stunden-Anzeige zentral ueber fmtStd (genau zwei Nachkommastellen, Komma, leer bleibt leer) - Pin bewusst nachgezogen)
    assert "React.createElement('tfoot', null, React.createElement('tr', { 'data-be-summe': \"1\"" in v
    assert "\"inkl. \"+fmtStd(_beOhneMa)+\" h ohne Mitarbeiter-Zuordnung\"" in v
    assert "Summe = alle Zeiteintr\\u00e4ge = Kachel \\u201eStunden auf Projekten\\u201c samt Unterzeile" in v


# ── Monat ausgeschrieben ────────────────────────────────────────────────────
def _kv(src):
    a = src.index("function KVZulagenReport(")
    return src[a:src.index("\nfunction PZEView(", a)]


def test_iso_monat_wird_ausgeschrieben(roh, node_exe):
    kv = _kv(roh)
    mon = _zeile_ab(kv, "  const _ezMonW=")
    js = (mon.replace("const _ezMonW", "var _ezMonW").replace("const _kvYmDE", "var _kvYmDE") + "\n"
          "process.stdout.write(JSON.stringify(['2026-11','2027-01','2026-12','x','',null].map(_kvYmDE)));")
    assert json.loads(run_node_snippet(node_exe, js)) == ["November 2026", "Januar 2027", "Dezember 2026", "x", "", ""]
    assert "textAlign:'center',whiteSpace:'nowrap'}},_kvYmDE(ym))" in kv
    assert "'Keine Zulagen im '+_kvYmDE(ym)+'.'" in kv
    assert not re.search(r"\}\},ym\)|'Keine Zulagen im '\+ym", kv)


def test_umkehr_roher_monat_waere_rot(roh):
    kv = _kv(roh).replace("}},_kvYmDE(ym))", "}},ym)", 1)
    assert re.search(r"\}\},ym\)", kv)


def test_pdf_dateiname_bleibt_iso(roh):
    """Nur die Anzeige ist ausgeschrieben; der PDF-Name (Export) bleibt wie er war."""
    assert "_kvYmDE" not in _quelle(roh, "  const _pzeBtn=()=>{")


# ── Krankenstand ────────────────────────────────────────────────────────────
def _krank(v):
    a = v.index("_bxTab==='abwesend' && (()=>{const _krAll=_krankRows();")
    return v[a:v.index("_bxTab==='tank' && (()=>{", a)]


def test_krankenstand_werte_stehen_in_ihren_spalten(roh):
    k = _krank(_be(roh))
    breit = k[k.index(":[React.createElement('td',{key:\"n\""):k.index("]));return _op?")]
    keys = re.findall(r"React\.createElement\('td',\{key:\"(\w)\"", breit)
    assert keys == ["n", "d", "h", "s", "t"], keys
    assert "colSpan" not in breit
    assert "fmtStd(b.h))" in breit and "},_bSt)," in breit and "Attest vorhanden" in breit
    assert '_kStTxt(r.status)' in k and "},r.status)" not in k
    assert "\"Zeiträume\")+\" · \"+kr.length+\" von \"+_krAll.length+\" Tagen\"" in k


def test_umkehr_fliesstextzeile_waere_rot(roh):
    k = _krank(_be(roh))
    kaputt = k.replace(":[React.createElement('td',{key:\"n\"", ":[React.createElement('td',{key:\"n\",colSpan:5", 1)
    breit = kaputt[kaputt.index(":[React.createElement('td',{key:\"n\""):kaputt.index("]));return _op?")]
    assert "colSpan" in breit


def test_status_text(roh, node_exe):
    k = _krank(_be(roh))
    m = re.search(r"const _kStTxt=x=>[^;]*;", k)
    js = m.group(0) + "process.stdout.write(JSON.stringify(['genehmigt','ausstehend','abgelehnt','',undefined].map(_kStTxt)));"
    assert json.loads(run_node_snippet(node_exe, js)) == ["Genehmigt", "Ausstehend", "Abgelehnt", "—", "—"]


# ── Trefferflaechen und Kennzahlen ──────────────────────────────────────────
def test_tippflaechen_44(roh):
    v = _be(roh)
    assert "minHeight:44,borderRadius:8" in v  # Reiterleiste, jede Stufe
    st = re.search(r"const _beStiftSt=\{[^;]*minWidth:(\d+),minHeight:(\d+)", v)
    assert st and min(int(x) for x in st.groups()) >= 44
    assert v.count("style: _beStiftSt") == 1 and v.count("style:_beStiftSt") == 1
    for frag in ['padding:"3px 10px",minHeight:44,fontSize:UI.fMeta},title:"Attest ansehen"',
                 'padding:"3px 8px",minWidth:44,minHeight:44,fontSize:UI.fMeta}',
                 'padding:"3px 10px",minHeight:44,fontSize:UI.fMeta}},_ikVw("auge","Beleg"))',
                 'padding:"2px 8px",minWidth:44,minHeight:44,fontSize:UI.fMeta,fontWeight:_isUndo(r)?700:600}',
                 'padding:"5px 12px",minHeight:44,fontSize:UI.fMeta}},"\\u2713 Als kontrolliert markieren")',
                 "minHeight:44,touchAction:\"manipulation\"}},\"Attest fehlt\")"]:
        assert frag in v, frag
    assert "minHeight:36" not in v and "rgba(59,130,246" not in v


def test_umkehr_kleiner_stift_waere_rot(roh):
    v = _be(roh).replace("minWidth:44,minHeight:44,touchAction:\"manipulation\",flexShrink:0};", "minWidth:24,minHeight:24,touchAction:\"manipulation\",flexShrink:0};", 1)
    st = re.search(r"const _beStiftSt=\{[^;]*minWidth:(\d+),minHeight:(\d+)", v)
    assert min(int(x) for x in st.groups()) < 44


def test_kennzahlen_am_handy_zugeklappt(roh):
    v = _be(roh)
    assert "const [_beKpiAuf,_beSetKpiAuf]=_react.useState.call(void 0, false);" in v
    assert "_bxTab==='projekte' && isMob && React.createElement('button', { type: \"button\", onClick: ()=>_beSetKpiAuf(v=>!v), 'aria-expanded': _beKpiAuf?\"true\":\"false\", 'data-be-kpi-klapp': \"1\"" in v
    assert "_bxTab==='projekte' && (!isMob||_beKpiAuf) && React.createElement('div', { " + KPI_KLASSE in v


def _css(roh):
    a = roh.index("<style")
    return roh[a:roh.index("</style>", a)]


def _kpi_css_ok(css):
    regeln = re.findall(r"[^\n{}]*epk-be-[^{]*\{[^}]*\}", css)
    if len(regeln) < 4:
        return False
    for r in regeln:
        if "overflow-x" in r or "display: none" in r:
            return False
        for px in re.findall(r"font-size:\s*(\d+)px", r):
            if int(px) < 12:
                return False
    return any("epk-be-kpi" in r and "tabular-nums" in r for r in regeln)


def test_css_ohne_querrollen_und_mit_ziffern(roh):
    assert _kpi_css_ok(_css(roh))


def test_umkehr_querrollende_kacheln_waeren_rot(roh):
    alt = ".kpi-grid.epk-leiste.epk-kachel-kompakt.epk-be-kpi > div > div:nth-child(3) { font-variant-numeric: tabular-nums; }"
    assert alt in roh
    assert not _kpi_css_ok(_css(roh.replace(alt, alt.replace("{ ", "{ overflow-x: auto; "), 1)))
