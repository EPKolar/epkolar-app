# -*- coding: utf-8 -*-
"""v3.9.781 — Chef-Portal (ChefDashboard) auf Sub-Tabs statt langer Klapp-Scroll-Seite.

Muster wie VBueroExport (v3.9.771): Tab-Leiste direkt unter dem Header, ein Klick zeigt
genau eine Sektion (React false-Guard via _cdTab===X && ...). Zuletzt gewaehlter Tab pro
Geraet in localStorage (epk_chefdashboard_tab); ungueltig/leer -> erster Tab (ueberblick).

5 Tabs: Ueberblick | Projekte | Arbeit | Personal | Ressourcen.
Gruppierung der 14 _card-Sektionen + KPI-Grid:
  ueberblick : KPI-Grid + sorgen + mt
  projekte   : proj + fin + voltrend + budget
  arbeit     : as
  personal   : zeit + kap + urlaub
  ressourcen : fz + wz + mat + gs

NUR Navigation/Anordnung — KPI-Zahlen, Deep-Links (_drill/onNav/onOpenP), Rechnungen und
die _card-Collapse-Mechanik (openSec/_toggleSec) unveraendert.
"""
import re


def _chef(index_html):
    a = index_html.index("function ChefDashboard({")
    b = index_html.index("function FahrtenbuchPanel(", a)
    return index_html[a:b]


def test_cd_tabs_definiert(index_html):
    c = _chef(index_html)
    assert "var CD_TABS=[['ueberblick'" in c, "CD_TABS-Definition fehlt"
    for t in ("'ueberblick'", "'projekte'", "'arbeit'", "'personal'", "'ressourcen'"):
        assert t in c, "Tab fehlt: " + t


def test_localstorage_persistenz(index_html):
    c = _chef(index_html)
    assert "localStorage.getItem('epk_chefdashboard_tab')" in c, "kein localStorage-Load des Tabs"
    assert "localStorage.setItem('epk_chefdashboard_tab'" in c, "kein localStorage-Save des Tabs"
    # v3.9.792 Etappe 2: Init-Prioritaet history.state.sub > localStorage > Default 'ueberblick' (localStorage bleibt Fallback).
    assert "_navSubResolve(_st,_ls,_cdValid,'ueberblick')" in c, "kein Default 'ueberblick' via _navSubResolve"


def test_setter_speichert(index_html):
    c = _chef(index_html)
    # v3.9.792 Etappe 2: der Setter speichert weiter in localStorage UND pusht den Sub-Tab in die History.
    assert "try{localStorage.setItem('epk_chefdashboard_tab',_t);}catch(_e){}_navPush({sub:_t});" in c, \
        "_setCdTab speichert nicht in localStorage / pusht sub nicht in History"


def test_state_setter_vorhanden(index_html):
    c = _chef(index_html)
    assert "const [_cdTab,_setCdTabRaw]=_react.useState.call(void 0, function()" in c, \
        "_cdTab-State fehlt oder falsches Muster"


def test_tab_leiste_mit_tap_target(index_html):
    c = _chef(index_html)
    assert "CD_TABS.map(function(_t){var _act=(_cdTab===_t[0]);" in c, "Tab-Leiste rendert CD_TABS nicht"
    assert "_setCdTab(_t[0])" in c, "Tab-Button ruft _setCdTab nicht"
    assert "minHeight:48" in c, "Tap-Target der Tab-Buttons nicht >=44 (48)"


# ── jede der 14 Sektionen + KPI-Grid haengt an genau EINEM _cdTab===-Guard ──

# Sektions-Key -> erwarteter Tab
_SEK_TAB = {
    "sorgen": "ueberblick",
    "mt": "ueberblick",
    "proj": "projekte",
    "fin": "projekte",
    "voltrend": "projekte",
    "budget": "projekte",
    "as": "arbeit",
    "zeit": "personal",
    "kap": "personal",
    "urlaub": "personal",
    "fz": "ressourcen",
    "wz": "ressourcen",
    "mat": "ressourcen",
    "gs": "ressourcen",
}


def test_jede_sektion_genau_ein_guard(index_html):
    c = _chef(index_html)
    for key, tab in _SEK_TAB.items():
        # _card('<key>' kommt genau 1x vor
        n_card = len(re.findall(r"_card\('" + key + r"'", c))
        assert n_card == 1, "Sektion %s: _card genau 1x erwartet, gefunden %d" % (key, n_card)
        # und jedes _card('<key>' steht hinter dem erwarteten Tab-Guard
        pat = r"_cdTab==='" + tab + r"' && [^\n]*_card\('" + key + r"'"
        assert re.search(pat, c), "Sektion %s haengt nicht am Guard _cdTab==='%s'" % (key, tab)


def test_kpi_grid_an_ueberblick(index_html):
    c = _chef(index_html)
    assert "_cdTab==='ueberblick' && React.createElement('div',{style:{display:'grid',gridTemplateColumns:isMob?'repeat(2,1fr)':'repeat(5,1fr)'" in c, \
        "KPI-Kachelgrid nicht an Ueberblick-Tab gebunden"


def test_alle_tab_werte_gueltig(index_html):
    """Kein Guard verweist auf einen Tab-Key, den es in CD_TABS nicht gibt."""
    c = _chef(index_html)
    valid = {"ueberblick", "projekte", "arbeit", "personal", "ressourcen"}
    used = set(re.findall(r"_cdTab==='([a-z]+)'", c))
    assert used, "keine _cdTab-Guards gefunden"
    assert used <= valid, "unbekannter Tab-Key in Guard: " + str(used - valid)


# ── Zahlen/Deep-Links/Collapse unberuehrt-Pin ──

def test_deep_links_unberuehrt(index_html):
    c = _chef(index_html)
    assert "window.__asFilter" in c, "Deep-Link window.__asFilter verschwunden"
    assert "window.__asOpenId" in c, "Deep-Link window.__asOpenId verschwunden"
    assert "onNav('projekte')" in c or "onNav('arbeitsscheine')" in c, "onNav-Deep-Links verschwunden"
    assert "const _drill=(label,tab)=>" in c, "_drill-Helper verschwunden"


def test_collapse_mechanik_unberuehrt(index_html):
    c = _chef(index_html)
    assert "const [openSec,setOpenSec]=_react.useState.call(void 0, {});" in c, "openSec-State verschwunden"
    assert "const _toggleSec=(id)=>setOpenSec(p=>({...p,[id]:p[id]===false}));" in c, "_toggleSec verschwunden"
    assert "const _secOpen=(id)=>openSec[id]!==false;" in c, "_secOpen verschwunden"
