# -*- coding: utf-8 -*-
"""v3.9.796 — Navigation Schritt 2 E3: Chef-Portal + Buero-Portal Sub-Tabs auf useBackLayer.

Gleiches System-A-Muster wie E1 (Admin). Einzige echte Falle: der Default kommt hier aus
localStorage (epk_chefdashboard_tab / epk_bueroexport_tab) und der Setter SCHREIBT bei jedem
Wechsel dorthin. Der Back-Restore darf daher NICHT den laufend gespeicherten aktuellen Tab
treffen, sondern den BEIM MOUNT aufgeloesten Default -> dieser wird EINMAL (initialer
_cdTab/_bxTab) in eine Ref eingefroren; useBackLayer restauriert die Ref.

popstate ist nicht statisch testbar (Sebastians Live-Klick ist die Abnahme) -> hier wird die
Verdrahtung gepinnt.
"""
import re

from _hilfen import nur_code


def _chef(index_html):
    a = index_html.index("function ChefDashboard({")
    b = index_html.index("function FahrtenbuchPanel(", a)
    return index_html[a:b]


def _buero(index_html):
    a = index_html.index("function VBueroExport({")
    b = index_html.index("function AdminPanel({", a)
    return index_html[a:b]


def test_chef_einzeiler_und_mount_default(index_html):
    c = _chef(index_html)
    assert "const _cdDefaultTab=_react.useRef.call(void 0, void 0);" in c, "Chef: _cdDefaultTab-Ref fehlt"
    # Mount-Default EINMAL einfrieren = initialer _cdTab (nicht der laufend gespeicherte aktuelle Tab).
    assert "if(_cdDefaultTab.current===void 0)_cdDefaultTab.current=_cdTab;" in c, \
        "Chef: Mount-Default nicht EINMAL aus initialem _cdTab eingefroren"
    # Restore auf die aufgeloeste Ref, ueber den persistierenden Setter _setCdTab (NICHT Literal, NICHT _setCdTabRaw).
    assert "useBackLayer(_cdTab!==_cdDefaultTab.current, ()=>_setCdTab(_cdDefaultTab.current));" in c, \
        "Chef: useBackLayer-Einzeiler (Restore auf Mount-Default-Ref via _setCdTab) fehlt/veraendert"


def test_buero_einzeiler_und_mount_default(index_html):
    b = _buero(index_html)
    assert "const _bxDefaultTab=_react.useRef.call(void 0, void 0);" in b, "Buero: _bxDefaultTab-Ref fehlt"
    assert "if(_bxDefaultTab.current===void 0)_bxDefaultTab.current=_bxTab;" in b, \
        "Buero: Mount-Default nicht EINMAL aus initialem _bxTab eingefroren"
    assert "useBackLayer(_bxTab!==_bxDefaultTab.current, ()=>_setBxTab(_bxDefaultTab.current));" in b, \
        "Buero: useBackLayer-Einzeiler (Restore auf Mount-Default-Ref via _setBxTab) fehlt/veraendert"


def test_restore_ist_kein_literal(index_html):
    # HARTE AUFLAGE: Restore geht auf den aufgeloesten Default (Ref), NICHT hart auf den ersten Tab.
    c, b = _chef(index_html), _buero(index_html)
    assert '()=>_setCdTab("ueberblick")' not in c and "()=>_setCdTab('ueberblick')" not in c, \
        "Chef: Restore haengt am Literal 'ueberblick' statt am Mount-Default"
    assert '()=>_setBxTab("projekte")' not in b and "()=>_setBxTab('projekte')" not in b, \
        "Buero: Restore haengt am Literal 'projekte' statt am Mount-Default"


def test_localstorage_bleibt_erstload_fallback(index_html):
    c, b = _chef(index_html), _buero(index_html)
    assert "localStorage.getItem('epk_chefdashboard_tab')" in c, "Chef: localStorage-Load (Mount-Default-Quelle) entfernt"
    assert "localStorage.getItem('epk_bueroexport_tab')" in b, "Buero: localStorage-Load (Mount-Default-Quelle) entfernt"
    # Persistenz-Schreibweg byte-identisch (Bestandsverhalten, nicht angefasst).
    assert "const _setCdTab=function(_t){_setCdTabRaw(_t);try{localStorage.setItem('epk_chefdashboard_tab',_t);}catch(_e){}};" in c, \
        "Chef: Persistenz-Setter veraendert"
    assert "const _setBxTab=function(_t){_setBxTabRaw(_t);try{localStorage.setItem('epk_bueroexport_tab',_t);}catch(_e){}};" in b, \
        "Buero: Persistenz-Setter veraendert"


def test_scope_guard_keine_neue_verdrahtung_ausserhalb(index_html):
    # Scope-Guard: E3 fuegt useBackLayer NUR in den zwei Portalen hinzu. Kommentare strippen
    # (Versions-Kommentare erwaehnen useBackLayer(...) -> sonst bruechig), dann Call-Sites zaehlen.
    # Ist-Stand v3.9.796: 10 Call-Sites + 1 Definition = 11. Aendert sich das ohne neue Etappe,
    # ist irgendwo eine ungewollte useBackLayer-Verdrahtung dazugekommen/verschwunden.
    #
    # v3.9.913 - DIE ZAHL BLEIBT (11), die eigene Strippregel geht.
    # Warum die Zahl bleibt: das hier ist ein VERBOT ("nirgendwo sonst"), und ein
    # Verbot laesst sich nicht durch benannte Stellen ersetzen - man kann die
    # Stelle, die es nicht geben darf, nicht vorher benennen. Dass die Zahl beim
    # Bau einer neuen Etappe nachgezogen werden muss, ist hier kein Mangel,
    # sondern der Zweck: sie soll dann rot werden.
    # Warum die Strippregel geht: sie war die zweite Kopie von nur_code() und
    # kannte den image/*-Falschoeffner nicht (s. tests/_hilfen.py). Neue Zahl:
    # 11 - unveraendert, denn keine der 11 Stellen lag im verschluckten Bereich.
    # Dateiweit ohne Strippen waeren es 13; die zwei Zusatztreffer sind Prosa.
    code = nur_code(index_html)
    assert code.count("useBackLayer(") == 11, (
        "useBackLayer-Gesamtzahl ist %d statt 11 (10 Call-Sites + 1 Definition). E3 darf NUR "
        "Chef/Buero verdrahten — pruefen, wo eine useBackLayer-Verdrahtung dazu/weg ist."
        % code.count("useBackLayer(")
    )


def test_e1_e2_intakt(index_html):
    assert "useBackLayer(adminTab!==_admDefaultTab, ()=>setAdminTab(_admDefaultTab));" in index_html, \
        "E1-Admin-Verdrahtung verschwunden"
    assert 'useBackLayer(sub==="form", ()=>setSub(_asPrevSub.current||"liste"));' in index_html, \
        "E2-AS-Detail-Verdrahtung verschwunden"


def test_kein_system_b_kein_hash_write(index_html):
    for region in (_chef(index_html), _buero(index_html)):
        code = re.sub(r"/\*.*?\*/", "", region, flags=re.S)
        for bad in ("_navPush", "_regSubView", "_subViewRef", "_navSubResolve", "history.state"):
            assert bad not in code, "System-B-/history.state-Rueckfall: " + bad
        assert "location.hash=" not in code, "unerlaubter Hash-Write (Kiosk-Tabu)"
