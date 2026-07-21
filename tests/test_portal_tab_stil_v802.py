# -*- coding: utf-8 -*-
"""v3.9.802 — Buero+Chef-Sub-Tab-Leisten auf AdminPanel-Stil (reines Styling).

Ziel: flach, aktiver Tab nur mit 2px-Border (V.ac) + subtiler V.ac+15-Fuellung (KEINE dicke Kachel,
keine vollflaechige gruene Fuellung), Icon+Label inline wie Admins t.l, minHeight:44 mobil (Tap-Target).
Alle drei Leisten (Admin/Buero/Chef) tragen denselben flachen Stil.

HART UNBERUEHRT: _bxTab/_cdTab-State, localStorage-Persistenz, E3-useBackLayer-Ref-Freeze, Section-Render.
"""


def _buero(index_html):
    a = index_html.index("function VBueroExport({")
    return index_html[a:index_html.index("function AdminPanel({", a)]


def _chef(index_html):
    a = index_html.index("function ChefDashboard({")
    return index_html[a:index_html.index("function FahrtenbuchPanel(", a)]


def test_buero_flacher_admin_stil(index_html):
    b = _buero(index_html)
    # Flacher Stil: 2px-Border in V.ac (aktiv) sonst transparent, subtile V.ac+15-Fuellung, kompakt.
    assert 'border:"2px solid "+(_act?V.ac:"transparent")' in b, "Buero-Tab nicht auf 2px-Border-Stil"
    assert 'background:_act?V.ac+"15":V.bg' in b, "Buero-Tab hat noch vollflaechige Fuellung statt V.ac+15"
    assert "minHeight:_bxMob?44:0" in b, "Buero-Tab: mobiles 44px-Tap-Target fehlt"
    # Alte dicke Kachel raus.
    assert "minHeight:48" not in b, "Buero-Tab traegt noch die dicke Kachel (minHeight:48)"
    assert 'flexDirection:"column"' not in b.split("BX_TABS.map")[1].split(";})),")[0], "Buero-Tab noch Spalten-Kachel"


def test_chef_flacher_admin_stil(index_html):
    c = _chef(index_html)
    assert "border:'2px solid '+(_act?V.ac:'transparent')" in c, "Chef-Tab nicht auf 2px-Border-Stil"
    assert "background:_act?V.ac+'15':V.bg" in c, "Chef-Tab hat noch vollflaechige Fuellung statt V.ac+15"
    assert "minHeight:isMob?44:0" in c, "Chef-Tab: mobiles 44px-Tap-Target fehlt"
    assert "minHeight:48" not in c, "Chef-Tab traegt noch die dicke Kachel (minHeight:48)"


def test_admin_tap_target(index_html):
    # Admin-Leiste hat jetzt auch minHeight:44 mobil (Referenz-Leiste pixelgleich zu Buero/Chef).
    assert "minHeight:isMob?44:0,borderRadius:8,border:\"2px solid \"+(adminTab===t.id?t.c:\"transparent\")" in index_html, \
        "Admin-Tab: minHeight:44 mobil fehlt (Tap-Target/Pixelgleichheit)"


def test_logik_unberuehrt(index_html):
    b, c = _buero(index_html), _chef(index_html)
    # Tab-Logik/Persistenz/useBackLayer HART unberuehrt.
    assert "_setBxTab(_t[0])" in b and "localStorage.getItem('epk_bueroexport_tab')" in b
    assert "_setCdTab(_t[0])" in c and "localStorage.getItem('epk_chefdashboard_tab')" in c
    assert "useBackLayer(_bxTab!==_bxDefaultTab.current, ()=>_setBxTab(_bxDefaultTab.current));" in b, "Buero-E3-Layer veraendert"
    assert "useBackLayer(_cdTab!==_cdDefaultTab.current, ()=>_setCdTab(_cdDefaultTab.current));" in c, "Chef-E3-Layer veraendert"
