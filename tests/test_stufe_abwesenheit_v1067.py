# -*- coding: utf-8 -*-
"""Stufe 3 Abwesenheiten (GF 19.11.2026, "EINE Oberflaeche, drei Breiten-Stufen").

Vorher: AbsView kannte nur Handy (ww<BP_MOB) und Rest. Am Tablet hochkant
(800 px) stand die Kontingent-Detailtabelle mit zwoelf Spalten, am Handy rollte
sie quer (minWidth 760), und die Kennzahlen waren vier hohe Kacheln.

Was hier gesichert wird:
1. AbsView entscheidet NUR ueber _layoutStufe (Breite + Lage): mit echtem Code
   fuer 384, 412, 800x1280, 1280x800, 1920x1080 ausgefuehrt - Stufe, isMob,
   Karte/Tabelle, Kartenspalten, Kennzahlen-Klasse, Kaesten-Raster.
2. Tabelle nur breit, Karten mittel/schmal - an derselben Entscheidung; die Karte
   traegt alle Felder und dieselben Handlungen (Kalender, vier Eingaben).
3. Abdeckung: keine eigene Breitenabfrage in AbsView (Ausnahme namentlich),
   kein userAgent.
4. Kein Querrollen auf Karten-Stufen; CI (Schrift >= 12, 44 px, tabular-nums,
   kein Rot/Fremdfarbe in der Karte).
Jeder Riegel hat eine Umkehrprobe.
"""
import io
import json
import os
import re

import pytest

from conftest import run_node_snippet
from _hilfen import nur_code

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")

DEKL = ("const _abStufe=_layoutStufe(ww,(typeof window!==\"undefined\"?window.innerHeight:0));"
        "const isMob=_abStufe===\"schmal\";const _abKarte=_abStufe!==\"breit\";")
KARTEN = "kontExpanded&&_abKarte&&React.createElement('div', { 'data-abs-karten': \"1\""
TABELLE = "kontExpanded&&!_abKarte&&(React.createElement('div', { style: {overflowX:\"auto\"}}"
KPI_KLASSE = "className: \"kpi-grid\"+(_abKarte?\" epk-abs-kpi\"+(isMob?\" epk-abs-kpi-schmal\":\"\"):\"\")"
KASTEN = ("gridTemplateColumns:_abStufe===\"breit\"?\"1fr 1fr 1fr\":isMob?\"minmax(0,1fr)\":"
          "\"repeat(auto-fit,minmax(220px,1fr))\"")
KARTEN_SPALTEN = "gridTemplateColumns:isMob?\"minmax(0,1fr)\":\"repeat(2,minmax(0,1fr))\""


@pytest.fixture(scope="module")
def roh():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _abs(src):
    a = src.index("function AbsView(")
    return src[a:src.index("\nfunction SvgBar(", a)]


def _stufe_code(src):
    i = src.index("const BP_MOB=600;")
    mob = src[i:i + len("const BP_MOB=600;")]
    j = src.index("const BP_BREIT=")
    k = src.index("function _grobZeiger(", j)
    return mob + "\n" + src[j:k]


# (Breite, Hoehe) -> (Stufe, isMob, Karte, Kartenspalten, Kennzahlen-Klasse, Kaesten)
FAELLE = [
    ([384, 832], ["schmal", True, True, "minmax(0,1fr)", "kpi-grid epk-abs-kpi epk-abs-kpi-schmal", "minmax(0,1fr)"]),
    ([412, 915], ["schmal", True, True, "minmax(0,1fr)", "kpi-grid epk-abs-kpi epk-abs-kpi-schmal", "minmax(0,1fr)"]),
    ([800, 1280], ["mittel", False, True, "repeat(2,minmax(0,1fr))", "kpi-grid epk-abs-kpi",
                   "repeat(auto-fit,minmax(220px,1fr))"]),
    ([1280, 800], ["breit", False, False, "repeat(2,minmax(0,1fr))", "kpi-grid", "1fr 1fr 1fr"]),
    ([1920, 1080], ["breit", False, False, "repeat(2,minmax(0,1fr))", "kpi-grid", "1fr 1fr 1fr"]),
]


def _entscheidung(node_exe, src, faelle):
    """Fuehrt die ECHTEN Ausdruecke aus AbsView aus (nicht abgeschrieben)."""
    v = _abs(src)
    assert v.count(DEKL) == 1
    karten = v[v.index(KARTEN):]
    # die Ausdruecke werden aus der Quelle genommen - fehlen sie dort, ist der Test rot
    assert KARTEN_SPALTEN + ",gap:8}" in karten
    assert KPI_KLASSE in v and KASTEN + ",gap:12,marginBottom:14" in v
    sp = KARTEN_SPALTEN[len("gridTemplateColumns:"):]
    kl = KPI_KLASSE[len("className: "):]
    ka = KASTEN[len("gridTemplateColumns:"):]
    js = ("var window={innerWidth:0,innerHeight:0};\n" + _stufe_code(src) + "\n"
          "function f(ww,hh){window.innerWidth=ww;window.innerHeight=hh;" + DEKL
          + "return [_abStufe,isMob,_abKarte," + sp + "," + kl + "," + ka + "];}\n"
          "process.stdout.write(JSON.stringify(" + json.dumps(faelle)
          + ".map(function(x){return f(x[0],x[1]);})));")
    return json.loads(run_node_snippet(node_exe, js))


def test_entscheidung_fuer_fuenf_groessen(roh, node_exe):
    r = _entscheidung(node_exe, roh, [f for f, _ in FAELLE])
    assert r == [e for _, e in FAELLE], list(zip([f for f, _ in FAELLE], r))


def test_umkehr_alte_handy_schwelle_als_tabellengrenze_waere_rot(roh, node_exe):
    """Mit BP_BREIT=600 haette das Tablet hochkant wieder die Zwoelf-Spalten-Tabelle."""
    kaputt = roh.replace("const BP_BREIT=1100;", "const BP_BREIT=600;", 1)
    assert kaputt != roh
    assert _entscheidung(node_exe, kaputt, [f for f, _ in FAELLE]) != [e for _, e in FAELLE]


def test_dieselbe_handy_grenze_wie_vorher(roh, node_exe):
    """schmal == alte isMob (ww<BP_MOB) - am Handy aendert sich die Grenze nicht."""
    r = _entscheidung(node_exe, roh, [[599, 900], [600, 900]])
    assert [x[1] for x in r] == [True, False]


# ── Karte und Tabelle ───────────────────────────────────────────────────────
def _zweige(v):
    t = v.index(TABELLE)
    k = v.index(KARTEN, t)
    ende = v.index("className: \"kpi-grid\"", k)
    return v[k:ende], v[t:k]


LISTE = "(isAdmin?_kontNames:_kontNames.filter(n=>n===myMonteurName))"
HANDLUNGEN = [
    "onClick: ()=>{if(isAdmin){setSel(m);setSubView(\"kalender\");}}",
    "e=>setKontingent(p=>({...p,[m]:{...ks,woche:parseFloat(e.target.value)||38.5}}))",
    "e=>setKontingent(p=>({...p,[m]:{...ks,stunden:_ktgStd(e.target.value)}}))",
    "e=>setKontingent(p=>({...p,[m]:{...ks,vorjahr:parseFloat(e.target.value)||0}}))",
    "e=>setKontingent(p=>({...p,[m]:{...ks,ueberstunden:parseFloat(e.target.value)||0}}))",
]
FELDER = ["\"Std/Wo\"", "\"Anspruch h\"", "\"Vorjahr h\"", "\"Gesamt h\"", "AT_T.urlaub.l",
          "AT_T.krankenstand.l", "AT_T.zeitausgleich.l", "\"Sonder\"", "\"Pflege\"", "\"ÜS h\"",
          "\"Rest Urlaub\"", "ys.urlaubStdAusstehend"]


def _karte_ok(v):
    karte, tabelle = _zweige(v)
    if LISTE not in karte or LISTE not in tabelle:
        return False
    for h in HANDLUNGEN:
        if h not in karte or h not in tabelle:
            return False
    return all(f in karte for f in FELDER) and karte.count("editKontingent?_abEin(") == 4


def test_tabelle_nur_breit_karte_nur_mittel_schmal(roh):
    v = _abs(roh)
    assert v.count(TABELLE) == 1 and v.count(KARTEN) == 1
    assert v.count("kontExpanded&&(React.createElement('div', { style: {overflowX:\"auto\"}}") == 0
    karte, tabelle = _zweige(v)
    assert "minWidth:isMob?760:0" in tabelle, "Tabelle (breit) unveraendert"
    assert KARTEN_SPALTEN in karte


def test_karte_traegt_alle_felder_und_handlungen(roh):
    assert _karte_ok(_abs(roh))


def test_umkehr_karte_ohne_eingabe_waere_rot(roh):
    v = _abs(roh)
    karte, _ = _zweige(v)
    alt = "e=>setKontingent(p=>({...p,[m]:{...ks,vorjahr:parseFloat(e.target.value)||0}}))"
    kaputt = v.replace(karte, karte.replace(alt, "()=>{}"), 1)
    assert kaputt != v and not _karte_ok(kaputt)


def test_umkehr_karte_ohne_kalendersprung_waere_rot(roh):
    v = _abs(roh)
    karte, _ = _zweige(v)
    kaputt = v.replace(karte, karte.replace(HANDLUNGEN[0], "onClick: ()=>{}"), 1)
    assert not _karte_ok(kaputt)


def test_ausgetretene_nur_ueber_ma_ist_ehemalig(roh):
    """Die Karten lesen dieselbe Liste wie die Tabelle - _kontNames aus _maIstEhemalig."""
    v = _abs(roh)
    assert "const _kontNames=monteure.filter(m=>!_maIstEhemalig(m,_hkAK)).map(m=>m.n);" in v
    karte, _ = _zweige(v)
    assert "names.map(" not in karte and "monteure.filter(" not in karte


# ── Kennzahlen ──────────────────────────────────────────────────────────────
def test_kennzahlen_am_handy_zugeklappt_mittel_flach(roh):
    v = _abs(roh)
    assert "const [abKpiAuf,setAbKpiAuf]=_react.useState.call(void 0, false);" in v
    assert "isMob&&React.createElement('button', { onClick: ()=>setAbKpiAuf(!abKpiAuf), 'aria-expanded': abKpiAuf?\"true\":\"false\"" in v
    assert "_klappIk(abKpiAuf,16))" in v
    assert "(!isMob||abKpiAuf)&&React.createElement('div', { " + KPI_KLASSE in v
    i = v.index("'data-abs-kpi-klapp'")
    assert "minHeight:44" in v[i:i + 400]


def _css(roh):
    return [m.group(0) for m in re.finditer(r"\.kpi-grid\.epk-abs-kpi[^{]*\{[^}]*\}", roh)]


def _css_ok(regeln):
    if len(regeln) < 4:
        return False
    for r in regeln:
        if "overflow-x" in r or "display: none" in r or "nowrap" in r:
            return False
        for px in re.findall(r"font-size:\s*(\d+)px", r):
            if int(px) < 12:
                return False
    return any("repeat(4,minmax(0,1fr))" in r for r in regeln) and \
        any("epk-abs-kpi-schmal" in r and "repeat(2,minmax(0,1fr))" in r for r in regeln)


def test_kennzahlen_css_ohne_querrollen(roh):
    assert _css_ok(_css(roh))


def test_umkehr_querrollende_kacheln_waeren_rot(roh):
    kaputt = roh.replace(".kpi-grid.epk-abs-kpi { grid-template-columns: repeat(4,minmax(0,1fr)) !important;",
                         ".kpi-grid.epk-abs-kpi { overflow-x: auto; grid-template-columns: repeat(4,minmax(0,1fr)) !important;", 1)
    assert kaputt != roh and not _css_ok(_css(kaputt))


# ── Abdeckung ───────────────────────────────────────────────────────────────
AUSNAHMEN = {
    # Seitentitel: app-weites Muster (23 Stellen), gepinnt von
    # test_d9_seitenueberschriften_v956 / test_seitentitel_v1007 - keine Layoutfrage.
    "fontSize:window.innerWidth<BP_MOB?UI.fSeiteMob:UI.fSeite",
}
BREITEN_MUSTER = re.compile(r"\bww\s*[<>]=?|innerWidth\s*[<>]=?|matchMedia|userAgent|navigator\.")


def _fremde_breiten(src):
    code = nur_code(_abs(src))
    for aus in AUSNAHMEN:
        code = code.replace(aus, "")
    return [code[max(0, m.start() - 50):m.end() + 30] for m in BREITEN_MUSTER.finditer(code)]


def test_abdeckung_keine_eigenen_breitenvergleiche(roh):
    funde = _fremde_breiten(roh)
    assert not funde, "Eigene Breitenvergleiche statt _layoutStufe:\n" + "\n".join(funde)


def test_abdeckung_fragt_die_stufe(roh):
    v = _abs(roh)
    assert DEKL in v
    assert "const isMob=ww<BP_MOB;" not in v


def test_umkehr_abdeckung_findet_neuen_vergleich(roh):
    kaputt = roh.replace("const _abKarte=_abStufe!==\"breit\";", "const _abKarte=ww<1100;", 1)
    assert kaputt != roh and _fremde_breiten(kaputt)
    kaputt2 = roh.replace(KASTEN, "gridTemplateColumns:window.innerWidth<768?\"1fr\":\"1fr 1fr 1fr\"", 1)
    assert kaputt2 != roh and _fremde_breiten(kaputt2)
    kaputt3 = roh.replace(DEKL, DEKL + "const _ua=/Android/.test(navigator.userAgent);", 1)
    assert _fremde_breiten(kaputt3)


def _bloecke(s):
    aus = []
    for m in re.finditer(r"<script\b[^>]*>", s, re.I):
        e = s.find("</script>", m.end())
        aus.append((m.end(), e if e > 0 else len(s)))
    return aus


def test_stufe_steht_im_block_von_absview(roh):
    bl = _bloecke(roh)
    p1, p2 = roh.index("function _layoutStufe(w,h){"), roh.index("function AbsView(")
    n1 = [n for n, (a, b) in enumerate(bl) if a <= p1 < b]
    n2 = [n for n, (a, b) in enumerate(bl) if a <= p2 < b]
    # wie test_as_hochformat_v1062: der erste umschliessende Block zaehlt
    assert n1 and n2 and n1[0] == n2[0]


# ── Kein Querrollen, CI ─────────────────────────────────────────────────────
def _ci_funde(karte):
    f = []
    for m in re.finditer(r"fontSize:(\d+)", karte):
        if int(m.group(1)) < 12:
            f.append("Schrift " + m.group(0))
    for m in re.finditer(r"(?:minWidth|width):(\d+)", karte):
        if int(m.group(1)) > 300:
            f.append("feste Breite " + m.group(0))
    for rot in ("#ef4444", "#dc2626", "COLORS.ERROR", "239,68,68", "#3b82f6", "#a855f7", "#f59e0b"):
        if rot in karte:
            f.append("Farbe " + rot)
    if re.search(u"[☀-➿\U0001F300-\U0001FAFF]", karte):
        f.append("Emoji")
    if karte.count("minHeight:44") < 2:
        f.append("Tippziel")
    if "tabular-nums" not in karte:
        f.append("tabular-nums")
    return f


def test_karte_ci_und_ohne_feste_ueberbreite(roh):
    karte, _ = _zweige(_abs(roh))
    assert _ci_funde(karte) == []


def test_umkehr_rot_oder_ueberbreite_in_der_karte_waere_rot(roh):
    karte, _ = _zweige(_abs(roh))
    assert _ci_funde(karte.replace("rest<=20?UI.achtungTxt", "rest<=20?\"#ef4444\"", 1))
    assert _ci_funde(karte.replace("style: {minWidth:0,padding:\"10px 12px\"", "style: {minWidth:760,padding:\"10px 12px\"", 1))


def test_kopfknoepfe_44_auf_karten_stufen(roh):
    v = _abs(roh)
    assert v.count("padding:_abKarte?\"8px 12px\":\"3px 10px\",fontSize:UI.fMeta,minHeight:_abKarte?44:0") == 2
    assert "minHeight:isMob?38:0,touchAction:\"manipulation\"" not in v


# ── Nachtrag Tablet-Vollpruefung: Jahresfarben, ein Leerzustand, Rundung ────
def _jahr_code(src):
    i = src.index("const ABW_MON_TYP={")
    t = src[i:src.index("\n", i)]
    j = src.index("function _abwMonTyp(t){")
    k = src.index("function _abwJahrBalken(get,yr,mi){")
    return t + "\n" + src[j:src.index("\n", j)] + "\n" + src[k:src.index("\n", k)]


LEGENDE = re.compile(
    r"Object\.keys\((\w+)\)\.map\(k=>React\.createElement\('div', \{ key: k, style: \{display:\"flex\",alignItems:\"center\",gap:4\}\}, "
    r"React\.createElement\('div', \{ 'data-abw-legende': k, style: \{width:12,height:12,borderRadius:2,background:([^}]+)\}\}")


def _legende_gleich_balken(node_exe, src, vorspann=""):
    """Fuer JEDEN Typ der App: ein Monat nur mit diesem Typ -> Balkenfarbe == Legendenfarbe.
    Tafel und Farbausdruck der Legende werden aus AbsView gelesen, nicht abgeschrieben."""
    v = _abs(src)
    m = LEGENDE.search(v)
    assert m, "Legende nicht gefunden"
    tafel, farbe = m.group(1), m.group(2)
    assert "const _jb=_abwJahrBalken(d=>ga(m,d),yr,mi);const c=_jb.c||V.empty;" in v
    js = (vorspann + "\n" + _jahr_code(src) + "\nvar aus=Object.keys(ABW_MON_TYP).map(function(k){"
          "var b=_abwJahrBalken(function(d){return d.getDate()<=3?{type:k}:null;},2026,10);"
          "return [k,b.t,b.ges,b.c,(function(){return " + farbe + ";})()];});"
          "process.stdout.write(JSON.stringify(aus));")
    return json.loads(run_node_snippet(node_exe, js)), tafel


def test_legende_und_balken_aus_einer_tafel(roh, node_exe):
    r, tafel = _legende_gleich_balken(node_exe, roh)
    assert tafel == "ABW_MON_TYP"
    assert len(r) >= 15
    for k, t, ges, c_balken, c_legende in r:
        assert t == k and ges == 3, (k, t, ges)
        assert c_balken == c_legende, (k, c_balken, c_legende)


def test_umkehr_legende_aus_at_t_waere_rot(roh, node_exe):
    """Die alte Legende (AT_T.c) zeigte Urlaub blau ueber gruenen Balken."""
    alt = "background:ABW_MON_TYP[k].c}} ), (AT_T[k]&&AT_T[k].l)||k))"
    kaputt = roh.replace(alt, "background:AT_T[k].c}} ), (AT_T[k]&&AT_T[k].l)||k))", 1)
    assert kaputt != roh
    i = roh.index("const AT_T={")
    at_t = roh[i:roh.index("\n};", i) + 3].replace("COLORS.ERROR", "\"#ef4444\"")
    r, _ = _legende_gleich_balken(node_exe, kaputt, vorspann=at_t)
    assert any(cb != cl for _, _, _, cb, cl in r)


def test_haeufigster_typ_gewinnt_gleichstand_urlaub(roh, node_exe):
    js = (_jahr_code(roh) + "\nfunction g(map){return function(d){return map[d.getDate()]||null;};}"
          "process.stdout.write(JSON.stringify(["
          "_abwJahrBalken(g({1:{type:'urlaub'},2:{type:'krankenstand'},3:{type:'krankenstand'}}),2026,0).t,"
          "_abwJahrBalken(g({1:{type:'urlaub'},2:{type:'krankenstand'}}),2026,0).t,"
          "_abwJahrBalken(g({1:{type:'krank'}}),2026,0).t,"
          "_abwJahrBalken(g({}),2026,0)]));")
    r = json.loads(run_node_snippet(node_exe, js))
    assert r == ["krankenstand", "urlaub", "krankenstand", {"t": None, "ges": 0, "c": None}]


def _leer_ok(v):
    return ")):antragOffen===0?null/*" in v


def test_antraege_nur_ein_leerzustand(roh):
    v = _abs(roh)
    assert _leer_ok(v)
    i = v.index(")):antragOffen===0?null/*")
    assert v.rfind("pendingEntries.length>0?(React.createElement('div'", 0, i) != -1


def test_umkehr_zweiter_leerzustand_waere_rot(roh):
    v = _abs(roh)
    kaputt = v.replace(")):antragOffen===0?null/*", ")):/*", 1)
    assert kaputt != v and not _leer_ok(kaputt)


def _rundung_funde(v):
    return [a for a in ("_absH(mRest,0)", "_absH(rest,0)", "_n(rest,0)", "Math.round(rest)", "Math.round(mRest)")
            if a in v]


def test_rest_ueberall_eine_nachkommastelle(roh):
    v = _abs(roh)
    assert _rundung_funde(v) == []
    assert "kontUnlesbar?\"–\":(_absH(mRest,1)+\"h\")" in v


def test_umkehr_gerundeter_rest_waere_rot(roh):
    v = _abs(roh)
    assert _rundung_funde(v.replace("_absH(mRest,1)", "_absH(mRest,0)", 1))
