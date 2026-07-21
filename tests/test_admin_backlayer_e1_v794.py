# -*- coding: utf-8 -*-
"""v3.9.794 — Navigation Schritt 2 E1: Administration-Sub-Tabs auf useBackLayer (System A).

Rollback v792 (System B _navPush/_regSubView/_subViewRef) ist raus (v793). Neuaufbau auf
dem bewaehrten Fahrzeug/Werkzeug-Muster useBackLayer(sub!==default, ()=>setSub(default)).

E1-Scope HART: NUR AdminPanel. AS/Chef/Buero bleiben unangetastet (E2-E4).
Soll: Nicht-Default-Sub-Tab -> Browser-Zurueck -> Default-Tab; weiteres Zurueck ->
Hauptseiten-Nav unveraendert. KEIN history.state-Eigenbau, KEIN _navPush-Sub-Weg,
KEIN Hash-Write (Kiosk-Tabu). popstate-Verhalten ist nicht statisch testbar
(Sebastians Live-Klick ist die Abnahme) — hier wird die Verdrahtung gepinnt.
"""
import re


def _admin(index_html):
    a = index_html.index("function AdminPanel({")
    b = index_html.index("function OfflineBanner(", a)
    return index_html[a:b]


def test_default_tab_einmal_berechnet(index_html):
    c = _admin(index_html)
    # Default-Sub-Tab als eigene Konstante -> Init und Restore teilen ihn (keine Divergenz).
    assert '_admDefaultTab=(curUser&&(curUser.rolle||"").toLowerCase()==="lagerleitung"' in c, \
        "_admDefaultTab-Konstante fehlt/veraendert"
    assert '?"haendler":"benutzer";' in c, "Default-Rollenlogik (lagerleitung->haendler, sonst benutzer) veraendert"
    assert "const [adminTab,setAdminTab]=_react.useState.call(void 0, _admDefaultTab);" in c, \
        "useState-Init nutzt nicht _admDefaultTab"


def test_backlayer_verdrahtung(index_html):
    c = _admin(index_html)
    # Muster woertlich wie Werkzeug: useBackLayer(sub!==default, ()=>setSub(default))
    assert "useBackLayer(adminTab!==_admDefaultTab, ()=>setAdminTab(_admDefaultTab));" in c, \
        "useBackLayer-Sub-Tab-Verdrahtung fehlt"


def test_kein_system_b_und_kein_hash_write(index_html):
    # /* ... */-Kommentare strippen -> nur echter CODE wird geprueft (die v794-Erklaerkommentare
    # nennen die verbotenen Tokens absichtlich; sie duerfen den Ban-Scan nicht ausloesen).
    c = re.sub(r"/\*.*?\*/", "", _admin(index_html), flags=re.S)
    # System B darf in E1 NICHT wieder in den Code auftauchen.
    for bad in ("_navPush", "_regSubView", "_subViewRef", "history.state", "_navSubResolve"):
        assert bad not in c, "System-B-/history.state-Rueckfall in AdminPanel-Code: " + bad
    # Kiosk-Tabu: kein Hash-Write aus AdminPanel.
    assert "location.hash=" not in c, "unerlaubter Hash-Write in AdminPanel (Kiosk-Tabu)"


def test_werkzeug_muster_intakt(index_html):
    # Referenz-Muster (System A) muss unveraendert existieren — E1 kopiert es nur.
    assert 'useBackLayer(sub!=="liste", ()=>setSub("liste"));' in index_html, \
        "Werkzeug-Referenzmuster useBackLayer(sub!==liste) fehlt"


def test_e1_admin_wiring_leakt_nicht_in_as(index_html):
    # E1 war Admin-only. Die Admin-Verdrahtung darf nicht in die AS-View gewandert sein.
    # (Die urspruengliche "AS unberuehrt"-Zusicherung gilt ab v3.9.795/E2 NICHT mehr:
    #  E2 gibt dem AS-Schein-Detail (sub==="form") legitim einen eigenen useBackLayer;
    #  das pinnt test_as_detail_backlayer_e2_v795.py.)
    a = index_html.index("function ArbeitsscheinView({")
    b = index_html.index("function EZKalender(props){", a)  # echte naechste Top-Level-Komponente
    asv = index_html[a:b]
    assert "useBackLayer(adminTab" not in asv, "Admin-E1-Verdrahtung in die AS-View geleakt"
