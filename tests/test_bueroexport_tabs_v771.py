# -*- coding: utf-8 -*-
"""v3.9.771 — Büro-Portal (VBueroExport) auf Sub-Tabs statt langer Klapp-Scroll-Seite.

NUR Navigation/Layout — Zulagen-Rechnung, PZE-Tabelle, Vergabe-Kacheln, Zahlen unverändert.
Tabs: Projekte | Stempelzeiten | Zulagen | Abwesenheiten | Tank. Ein Klick zeigt genau eine
Sektion (React false-Guard). Zuletzt gewählter Tab pro Gerät in localStorage
(epk_bueroexport_tab); ungültig/leer -> erster Tab (projekte).
"""
import re


def _vbuero(index_html):
    """Den Rumpf an der NAECHSTEN Funktionsdeklaration abgrenzen, nicht an
    einer festen Laenge.

    v3.9.950: hier stand `index_html[a:a + 95000]`. In v3.9.950 ist in
    `_kapMont` ein erklaerender Kommentar dazugekommen, und der hat den
    Abschnitt `_bxTab==='tank'` aus dem Fenster geschoben - der Riegel meldete
    "Tank nicht an Tab", obwohl an der Bindung nichts falsch war. Eine
    Laengengrenze ist keine Abgrenzung: sie verschiebt sich mit jedem Zeichen,
    das irgendwo davor dazukommt, und der Riegel wird rot, ohne dass die
    geprueft Sache sich geaendert hat.
    Dieselbe Lehre wie bei einer davongelaufenen Klammerzaehlung, nur in die
    andere Richtung - dort war das Fenster zu GROSS, hier zu klein.
    """
    a = index_html.index("function VBueroExport({")
    weiter = [m.start() for m in
              re.finditer(r"\n\s*function\s+[A-Za-z_$][\w$]*\s*\(", index_html)
              if m.start() > a]
    e = weiter[0] if weiter else len(index_html)
    assert 20_000 < e - a < 400_000, (
        "Der Rumpf von VBueroExport umfasst %d Zeichen - das ist keine "
        "Komponente, sondern eine verfehlte Abgrenzung." % (e - a))
    return index_html[a:e]


def test_tabs_definiert(index_html):
    b = _vbuero(index_html)
    assert "var BX_TABS=[['projekte'" in b, "BX_TABS-Definition fehlt"
    for t in ("'projekte'", "'stempel'", "'zulagen'", "'abwesend'", "'tank'"):
        assert t in b, "Tab fehlt: " + t


def test_localstorage_persistenz(index_html):
    b = _vbuero(index_html)
    assert "localStorage.getItem('epk_bueroexport_tab')" in b, "kein localStorage-Load des Tabs"
    assert "localStorage.setItem('epk_bueroexport_tab'" in b, "kein localStorage-Save des Tabs"
    # Fallback auf ersten Tab bei ungültig/leer
    assert "return 'projekte';" in b, "kein Fallback auf ersten Tab (projekte)"


def test_setter_speichert(index_html):
    b = _vbuero(index_html)
    assert "const _setBxTab=function(_t){_setBxTabRaw(_t);try{localStorage.setItem('epk_bueroexport_tab',_t);}catch(_e){}};" in b, \
        "_setBxTab speichert nicht in localStorage"


def test_sektionen_haengen_am_tab(index_html):
    """Jede Sektion nur sichtbar, wenn ihr Tab aktiv ist (false-Guard)."""
    b = _vbuero(index_html)
    assert "_bxTab==='zulagen' && React.createElement(KVZulagenReport" in b, "Zulagen nicht an Tab gebunden"
    assert "_bxTab==='stempel' && React.createElement(PZEView" in b, "Stempelzeiten nicht an Tab gebunden"
    assert "_bxTab==='projekte' && React.createElement('div', { className: \"kpi-grid\"" in b, "KPIs nicht an Projekte-Tab"
    assert "_bxTab==='projekte' && loaded && monteurStats.length>0" in b, "Monteur-Übersicht nicht an Projekte-Tab"
    assert "_bxTab==='projekte' && projStats.map(ps=>(" in b, "Projekt-Karten nicht an Projekte-Tab"
    assert "_bxTab==='abwesend' && React.createElement('div',{style:{marginTop:16}}" in b, "Abwesenheiten nicht an Tab"
    assert "_bxTab==='abwesend' && (()=>{const _krAll=_krankRows();" in b, "Krankenstand nicht an Abwesend-Tab"
    assert "_bxTab==='tank' && (()=>{" in b, "Tank nicht an Tab"


def test_defaultopen_prop(index_html):
    """KVZulagenReport + PZEView starten im Tab offen (defaultOpen), sonst unverändert."""
    # in beiden Komponenten der open-State aus props.defaultOpen
    assert index_html.count("_react.useState.call(void 0, props.defaultOpen||false)") == 2, \
        "defaultOpen nicht in genau 2 Komponenten (KVZulagenReport + PZEView)"
    b = _vbuero(index_html)
    assert "React.createElement(KVZulagenReport, { entries: entries, monteure: monteure, ww: ww, curUser: curUser, abs: abs, approvals: approvals, kontingent: _kontFor, defaultOpen: true} )" in b, \
        "KVZulagenReport bekommt defaultOpen nicht"
    assert "kontingent: _kontFor, defaultOpen: true} )" in b, "PZEView bekommt defaultOpen nicht"


def test_tab_leiste_mit_tap_target(index_html):
    b = _vbuero(index_html)
    assert "_setBxTab(_t[0])" in b, "Tab-Button ruft _setBxTab nicht"
    # v3.9.802: Tab-Leiste auf flachen AdminPanel-Stil umgebaut -> Tap-Target jetzt minHeight:44 mobil (statt 48).
    assert "minHeight:_bxMob?44:0" in b, "Tap-Target der Tab-Buttons nicht >=44 (mobil)"


def test_rechnung_unberuehrt(index_html):
    """Guard: die Kern-Rechenfunktionen sind nicht angefasst (nur Navigation)."""
    # _pzeTagRow / _kvTaggeldTag existieren unverändert weiter
    # (v3.9.774: _kvMontagezulageTag mit der Montagezulage entfernt)
    for fn in ("function _pzeTagRow(", "function _kvTaggeldTag("):
        assert fn in index_html, "Rechenfunktion versehentlich entfernt: " + fn
