# -*- coding: utf-8 -*-
"""v3.9.771 — Büro-Portal (VBueroExport) auf Sub-Tabs statt langer Klapp-Scroll-Seite.

NUR Navigation/Layout — Zulagen-Rechnung, PZE-Tabelle, Vergabe-Kacheln, Zahlen unverändert.
Tabs: Projekte | Stempelzeiten | Zulagen | Abwesenheiten | Tank. Ein Klick zeigt genau eine
Sektion (React false-Guard). Zuletzt gewählter Tab pro Gerät in localStorage
(epk_bueroexport_tab); ungültig/leer -> erster Tab (projekte).
"""
import re


def _vbuero(index_html):
    a = index_html.index("function VBueroExport({")
    return index_html[a:a + 95000]


def test_tabs_definiert(index_html):
    b = _vbuero(index_html)
    assert "var BX_TABS=[['projekte'" in b, "BX_TABS-Definition fehlt"
    for t in ("'projekte'", "'stempel'", "'zulagen'", "'abwesend'", "'tank'"):
        assert t in b, "Tab fehlt: " + t


def test_localstorage_persistenz(index_html):
    b = _vbuero(index_html)
    assert "localStorage.getItem('epk_bueroexport_tab')" in b, "kein localStorage-Load des Tabs"
    assert "localStorage.setItem('epk_bueroexport_tab'" in b, "kein localStorage-Save des Tabs"
    # v3.9.792 Etappe 2: Init-Prioritaet history.state.sub > localStorage > Default 'projekte' (localStorage bleibt Fallback).
    assert "_navSubResolve(_st,_ls,_bxValid,'projekte')" in b, "kein Default 'projekte' via _navSubResolve"


def test_setter_speichert(index_html):
    b = _vbuero(index_html)
    # v3.9.792 Etappe 2: der Setter speichert weiter in localStorage UND pusht den Sub-Tab in die History.
    assert "try{localStorage.setItem('epk_bueroexport_tab',_t);}catch(_e){}_navPush({sub:_t});" in b, \
        "_setBxTab speichert nicht in localStorage / pusht sub nicht in History"


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
    assert "minHeight:48" in b, "Tap-Target der Tab-Buttons nicht >=44 (48)"


def test_rechnung_unberuehrt(index_html):
    """Guard: die Kern-Rechenfunktionen sind nicht angefasst (nur Navigation)."""
    # _pzeTagRow / _kvTaggeldTag existieren unverändert weiter
    # (v3.9.774: _kvMontagezulageTag mit der Montagezulage entfernt)
    for fn in ("function _pzeTagRow(", "function _kvTaggeldTag("):
        assert fn in index_html, "Rechenfunktion versehentlich entfernt: " + fn
