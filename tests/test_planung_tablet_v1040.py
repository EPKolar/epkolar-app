# -*- coding: utf-8 -*-
"""Planung am Tablet (18.11.2026) - Riegel fuer die Wochenplanung + MA-Uebersicht.

Befund Lenovo-Tablet (1200x1920 hoch / 1920x1200 quer, Chrome-WebAPK, Touch), nachgemessen
lokal mit Playwright (has_touch, pointer:coarse) bei 1200x1920, 1920x1200, 800x1280, 1280x800:
  - Wetterzeile und Tabelle hatten zwei verschiedene Spaltenmodelle (Flex-Raster gegen colgroup):
    Versatz wuchs nach rechts bis 11 px (Sa) bei 1200 px.             -> nachher 0 px
  - Zeilenknoepfe 44x44 (Hausregel pointer:coarse) in einer 54-px-Spalte: 18 px ueber dem
    Tabellenrand abgeschnitten (rechte Kante 1197 gegen Clip 1179).   -> nachher 1175 < 1179
  - Kopier-Ikone im Tageskopf je nach Breite oben rechts oder unter dem Tag; Datum eigene Zeile.
  - Chips/Projektnamen/Rolle liefen aus der Zelle; KW-Schnellwahl in 2-3 Reihen; Tageskopf
    rollte weg; Hilfetext versprach Ziehen mit der Maus auch am Touchgeraet.
Jede Probe hat eine Umkehrprobe: der alte Zustand (oder die naheliegende Rueckentwicklung)
wird von derselben Pruefung als falsch erkannt.
"""
import json
import re
import shutil

import pytest

from conftest import _extract_fn, run_node_snippet


@pytest.fixture(scope="module")
def wp(index_html):
    q = _extract_fn(index_html, "WeekPlan")
    assert q, "function WeekPlan nicht gefunden"
    return q


# ---------------------------------------------------------------- Pruefungen
def _p_spaltenmodell(q):
    """Abwesenheiten, Spezialfahrzeuge, Wetter, Planungstabelle: dieselbe colgroup, Prozente = 100."""
    f = []
    m = re.search(r'const _WP_SP=\{nr:(\d+),bvh:"([\d.]+)%",tag:"([\d.]+)%",sa:"([\d.]+)%",bem:"([\d.]+)%"\}', q)
    if not m:
        return ["_WP_SP fehlt"]
    bvh, tag, sa, bem = (float(x) for x in m.groups()[1:])
    if abs(bvh + 5 * tag + sa + bem - 100) > 0.01:
        f.append("Prozente summieren sich nicht auf 100: %s" % (bvh + 5 * tag + sa + bem))
    if not bem > tag > sa:
        f.append("Bem. muss breiter als ein Tag sein, Sa schmaler (bem=%s tag=%s sa=%s)" % (bem, tag, sa))
    if q.count("_wpCols()") < 4:
        f.append("_wpCols() nur %dx genutzt - Abwesenheiten/Spezial/Wetter/Tabelle teilen nicht dasselbe Modell" % q.count("_wpCols()"))
    if "'data-wp-wetter': \"1\", style: _wpTabStil}, _wpCols()" not in q:
        f.append("Wetterzeile ist keine Tabelle mit der gemeinsamen colgroup")
    if "'data-wp-plan': \"1\", style: _wpTabStil}" not in q:
        f.append("Planungstabelle nutzt den gemeinsamen Tabellenstil nicht")
    if "minWidth:800" in q:
        f.append("altes Flex-Raster/minWidth:800 ist zurueck")
    return f


def _p_knopfspalte(q, html):
    f = []
    if "_wpGrob?React.createElement('col', { style: {width:100}}):React.createElement('col', { style: {width:54}})" not in q:
        f.append("Knopfspalte waechst am Touchgeraet nicht auf 100 px")
    if '...(_wpGrob?{gridTemplateColumns:"44px 44px",gap:4,width:92}:null)' not in q:
        f.append("2x2-Raster der Zeilenknoepfe hat am Touchgeraet keine 44er-Spalten")
    # _wpGrob muss GENAU die Hausregel spiegeln, die [role=button] auf 44x44 zwingt
    if "@media (pointer: coarse), (max-width: 768px) {" not in html:
        f.append("Hausregel 44x44 nicht gefunden")
    if '_wpGrob=_wpMM("(pointer: coarse), (max-width: 768px)")' not in q:
        f.append("_wpGrob spiegelt die Hausregel nicht")
    for lbl in ("Zeile nach oben", "Zeile nach unten", "Zeile leeren", "Zeile löschen"):
        if '"aria-label":"%s"' % lbl not in q:
            f.append("Zeilenknopf ohne aria-label: " + lbl)
    return f


def _p_tageskopf(q):
    f = []
    i = q.find("DSHORT.map((d,i)=>{/* v3.9.485: Tag-Kopieren")
    j = q.find("\"Bem.\")", i)
    if i < 0 or j < 0:
        return ["Tageskopf nicht gefunden"]
    th = q[i:j]
    if "React.createElement('br', {})" in th:
        f.append("Tageskopf baut wieder mit <br> (Datum auf eigener Zeile, Ikone daneben)")
    if 'flexDirection:"column",alignItems:"center"' not in th:
        f.append("Tageskopf nicht als Spalte Tag/Datum/Knopf gebaut")
    if "isAdmin&&React.createElement('button', {" not in th or 'type: "button"' not in th:
        f.append("Kopierknopf ist kein echter <button>")
    if "'aria-label': isSrc?\"Kopieren abbrechen\"" not in th:
        f.append("Kopierknopf ohne aria-label")
    if 'position:"relative"' in th:
        f.append("Tageskopf ist position:relative - schlaegt das Kleben (sticky) aus")
    return f


def _p_kleben(q):
    f = []
    if 'position:"sticky",top:ww<1200?-20:0' not in q or "background:_WP_KOPF" not in q:
        f.append("Kopf klebt nicht oder hat keine deckende Flaeche")
    if 'overflow:_wpEng?"hidden":"clip"' not in q:
        f.append("Huelle der Tabelle ist wieder ein Rollbehaelter (faengt sticky ein)")
    if q.count("_wpKopfTh(") < 5:
        f.append("nicht alle Kopfzellen nutzen _wpKopfTh")
    return f


def _p_zellen(q):
    f = []
    if ('whiteSpace:"nowrap",display:"inline-block",maxWidth:"100%",boxSizing:"border-box",overflow:"hidden",textOverflow:"ellipsis"' not in q):
        f.append("Personen-Chip kann ueber die Zelle hinausragen")
    if "title: m.n" not in q:
        f.append("Personen-Chip ohne vollen Namen im title")
    if "(isEmpty?\"\":_wpNameLesbar(r.bvh))" not in q:
        f.append("BVH-Name nicht lesbar aufbereitet")
    if 'lang: "de", style: {fontWeight:isEmpty?400:700,fontSize:15,whiteSpace:"normal",hyphens:"auto",overflowWrap:"anywhere"' not in q:
        f.append("BVH-Name ohne Silbentrennung")
    # Render 1089 P3: leere Nummern V.tx statt #555 (unter Zeilen-Deckkraft .5 nur 1,40 dunkel) - Pin nachgezogen
    # Render-Funde 1096: ganz leere Zeile ueber V.mt gedaempft (statt Zeilen-Deckkraft .5) - Pin nachgezogen
    if 'textAlign:"center",verticalAlign:"top",color:isEmpty&&!hasAnyContent?V.mt:isEmpty?V.tx:"#009640"' not in q:
        f.append("Nr nicht oben ausgerichtet")
    return f


def _p_kwreihe(q):
    f = []
    i = q.find("'data-wp-kwreihe': \"1\"")
    if i < 0:
        return ["KW-Schnellwahl-Reihe fehlt"]
    seg = q[i:i + 1400]
    for need in ('flexWrap:"nowrap"', 'overflowX:"auto"', "minWidth:0", "_ks.map(k=>"):
        if need not in seg:
            f.append("KW-Reihe: %s fehlt" % need)
    # GF 19.11.: Leiste bewusst auf aktuelle + 8 kommende Wochen gekuerzt (test_planung_kwleiste_v1056).
    if "const _ks=_wpKwChipListe(savedKws,kw,yr,curKw,curYr)" not in q:
        f.append("KW-Reihe nutzt nicht die Wochenfenster-Liste")
    return f


def _p_hilfetext(q):
    f = []
    i = q.find("Monteure, Baustellen & Fahrzeuge pro Wochentag planen. ")
    seg = q[i:i + 600]
    if "_wpTouch?" not in seg or "Zelle antippen" not in seg:
        f.append("Touchgeraet bekommt keinen eigenen Hilfetext")
    if "Finger über Zellen ziehen" in q:
        f.append("Hilfetext verspricht Ziehen mit dem Finger - das Ziehen hoert nur auf Maus")
    return f


def _p_ma(q):
    f = []
    if "React.createElement('col', { style: {width:\"14%\"}}), React.createElement('col', { style: {width:\"13%\"}})" not in q:
        f.append("MA-Uebersicht: Rolle-Spalte nicht verbreitert")
    if 'lang: "de", style: {padding:"4px 4px",fontSize:UI.fMeta,color:_lesbar(roleC),fontWeight:600,textAlign:"center",borderRight:"1px solid "+V.bd,hyphens:"auto",overflowWrap:"anywhere"}' not in q:
        f.append("MA-Uebersicht: Rolle bricht nicht in der Zelle um")
    return f


def _p_ueberschriften(q):
    if q.count('padding:"2px 8px 0 "+(_WP_SP.nr+8)+"px"') != 2:
        return ["Abwesenheiten/Spezialfahrzeuge-Ueberschrift ohne Innenabstand"]
    return []


# ---------------------------------------------------------------- Riegel
def test_spaltenmodell_gemeinsam(wp):
    assert _p_spaltenmodell(wp) == []


def test_knopfspalte_touch(wp, index_html):
    assert _p_knopfspalte(wp, index_html) == []


def test_tageskopf_einheitlich(wp):
    assert _p_tageskopf(wp) == []


def test_kopf_klebt(wp):
    assert _p_kleben(wp) == []


def test_zellen_halten_inhalt(wp):
    assert _p_zellen(wp) == []


def test_kw_reihe_eine_zeile(wp):
    assert _p_kwreihe(wp) == []


def test_hilfetext_touch(wp):
    assert _p_hilfetext(wp) == []


def test_ma_rolle(wp):
    assert _p_ma(wp) == []


def test_ueberschriften_innenabstand(wp):
    assert _p_ueberschriften(wp) == []


def test_ziehen_hoert_nur_auf_maus(wp):
    """Der Touch-Hilfetext stimmt nur, solange die Mehrtagesauswahl rein mausgesteuert ist.
    Kommt Touch-Ziehen dazu, muss der Text mitwandern - dann bitte diesen Riegel anpassen."""
    i = wp.find("const renderCell=")
    j = wp.find("return (", wp.find("isLastPick&&", i))
    zelle = wp[i:j] if i >= 0 else ""
    assert "onMouseDown: e=>onCellMouseDown(" in zelle
    assert "onTouchStart" not in zelle and "onPointerDown" not in zelle


@pytest.mark.skipif(shutil.which("node") is None, reason="node fehlt")
def test_name_lesbar_fuer_silbentrennung(node_exe, index_html):
    m = re.search(r"function _wpNameLesbar\(s\)\{.*?\n\}", index_html, re.S)
    assert m
    r = json.loads(run_node_snippet(node_exe, m.group(0) + "console.log(JSON.stringify([_wpNameLesbar('DR.-GSCHMEIDLERSTRASSE 10'),_wpNameLesbar('BVH Sparkasse Ravelsbach')]));"))
    assert r == ["Dr.-Gschmeidlerstrasse 10", "BVH Sparkasse Ravelsbach"]


# ---------------------------------------------------------------- Umkehrproben
UMKEHR = [
    (_p_spaltenmodell, "'data-wp-wetter': \"1\", style: _wpTabStil}, _wpCols()", "'data-wp-wetter': \"1\", style: _wpTabStil}, null"),
    (_p_spaltenmodell, 'bem:"18%"', 'bem:"12%"'),
    (_p_tageskopf, 'flexDirection:"column",alignItems:"center",gap:2,lineHeight:1.15', 'alignItems:"center",gap:2,lineHeight:1.15'),
    (_p_tageskopf, "isAdmin&&React.createElement('button', {", "isAdmin&&React.createElement('span', {"),
    (_p_kleben, 'overflow:_wpEng?"hidden":"clip"', 'overflow:"hidden"'),
    (_p_kleben, 'position:"sticky",top:ww<1200?-20:0', 'position:"relative",top:0'),
    (_p_zellen, 'maxWidth:"100%",boxSizing:"border-box",overflow:"hidden",textOverflow:"ellipsis"', 'boxSizing:"border-box"'),
    (_p_zellen, "(isEmpty?\"\":_wpNameLesbar(r.bvh))", "(isEmpty?\"\":r.bvh)"),
    (_p_zellen, 'textAlign:"center",verticalAlign:"top",color:isEmpty', 'textAlign:"center",color:isEmpty'),
    (_p_kwreihe, 'flexWrap:"nowrap",gap:4,overflowX:"auto"', 'flexWrap:"wrap",gap:4,overflowX:"visible"'),
    (_p_hilfetext, "(_wpTouch?", "(false?"),
    (_p_ma, "React.createElement('col', { style: {width:\"13%\"}})", "React.createElement('col', { style: {width:\"8%\"}})"),
    (_p_ueberschriften, 'padding:"2px 8px 0 "+(_WP_SP.nr+8)+"px"', 'padding:0'),
]


@pytest.mark.parametrize("pruef,alt,neu", UMKEHR, ids=[u[0].__name__ + "_" + str(k) for k, u in enumerate(UMKEHR)])
def test_umkehrprobe(wp, pruef, alt, neu):
    assert alt in wp, "Anker fuer die Umkehrprobe fehlt: " + alt
    assert pruef(wp) == []
    kaputt = wp.replace(alt, neu)
    assert pruef(kaputt) != [], "Mutation nicht erkannt: %s -> %s" % (alt, neu)


def test_umkehrprobe_knopfspalte(wp, index_html):
    for alt, neu in (("_wpGrob?React.createElement('col', { style: {width:100}}):", ""),
                     ('...(_wpGrob?{gridTemplateColumns:"44px 44px",gap:4,width:92}:null)', "")):
        assert alt in wp
        assert _p_knopfspalte(wp.replace(alt, neu), index_html) != []
