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

from conftest import _extract_fn
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


# ---------------------------------------------------------------------------
# BENANNTE TRAEGER STATT GESAMTZAHL (v3.9.922)
#
# Vorher: `nur_code(index_html).count("useBackLayer(") == 11`. Kommentarblind
# und sauber gebaut - aber EINE FESTZAHL UEBER DIE GANZE DATEI. Verschwindet
# der Zurueck-Griff in WerkzeugView und kommt in FahrzeugView ein zweiter
# dazu, bleibt die Summe 11 und der Riegel gruen. Eine Ansicht haette dann
# ihren Hardware-Zurueck-Knopf verloren, ohne dass es jemand merkt.
#
# Der frueher hier notierte Einwand ("ein Verbot laesst sich nicht durch
# benannte Stellen ersetzen, man kann die Stelle, die es nicht geben darf,
# nicht vorher benennen") stimmt - nur folgt daraus keine Festzahl. Das Verbot
# bleibt vollstaendig erhalten als `Summe der benannten Traeger == Gesamtzahl`:
# jeder Aufruf, der nicht in einer benannten Komponente steht, faellt auf.
# Zusaetzlich faellt jetzt der TAUSCH auf, den die Festzahl nicht sah.
#
# Ist-Stand v3.9.922, kommentarblind gemessen: 10 Aufrufe in 9 Komponenten +
# 1 Definition = 11. Roh waeren es 13 - die zwei Zusatztreffer sind Prosa,
# deshalb weiterhin `nur_code()` (siehe tests/_hilfen.py).
# ---------------------------------------------------------------------------
_TRAEGER = {
    # Detail-Auswahl (sel) - Zurueck schliesst das Detail
    "MitarbeiterView": 1,
    "VCheck": 1,
    "FahrzeugView": 1,
    # Unteransicht - Zurueck geht auf die Liste
    "ArbeitsscheinView": 1,
    "WerkzeugView": 1,
    # Portal-/Panel-Tabs - Zurueck geht auf den Mount-Default
    "ChefDashboard": 1,
    "VBueroExport": 1,
    # AdminPanel traegt BEIDE Griffe: Detail-Auswahl UND Admin-Tab (E1)
    "AdminPanel": 2,
    # Modal - Zurueck schliesst den PDF-Betrachter
    "PdfViewerModal": 1,
}


def _backlayer_mangel(code):
    """Abweichungen von den benannten Traegern. Leere Liste = gruen."""
    aus = []
    definitionen = code.count("function useBackLayer(")
    if definitionen != 1:
        aus.append("Definition `function useBackLayer(` kommt %dx vor statt 1x"
                   % definitionen)
    summe = definitionen
    for komp, erwartet in sorted(_TRAEGER.items()):
        region = _extract_fn(code, komp)
        if not region:
            aus.append("Komponente %s nicht gefunden" % komp)
            continue
        ist = region.count("useBackLayer(")
        summe += ist
        if ist != erwartet:
            aus.append("%s: %d useBackLayer-Verdrahtungen statt %d"
                       % (komp, ist, erwartet))
    gesamt = code.count("useBackLayer(")
    if summe != gesamt:
        aus.append("%d useBackLayer-Vorkommen ausserhalb ALLER benannten "
                   "Traeger (benannt %d, gesamt %d) - E3 darf NUR Chef/Buero "
                   "verdrahten" % (gesamt - summe, summe, gesamt))
    return aus


def test_scope_guard_jede_verdrahtung_an_ihrem_traeger(index_html):
    """Jede useBackLayer-Verdrahtung sitzt an ihrer benannten Komponente - und
    keine sitzt sonstwo."""
    assert _backlayer_mangel(nur_code(index_html)) == []


def test_umkehrprobe_tausch_wird_rot(index_html):
    """DER GRUND DER UMSTELLUNG. Der Griff verschwindet in WerkzeugView und
    kommt in FahrzeugView doppelt: Gesamtzahl unveraendert 11 (die alte Zahl
    WAERE gruen), der neue Riegel wird rot und benennt beide Komponenten."""
    code = nur_code(index_html)
    wkz, fhz = _extract_fn(code, "WerkzeugView"), _extract_fn(code, "FahrzeugView")
    kaputt = code.replace(wkz, wkz.replace("useBackLayer(", "useKeinBackLayer(", 1), 1)
    kaputt = kaputt.replace(fhz, fhz.replace(
        "useBackLayer(", "useBackLayer(false,()=>{});useBackLayer(", 1), 1)
    assert kaputt.count("useBackLayer(") == code.count("useBackLayer("), (
        "Vorbedingung der Probe: die Gesamtzahl MUSS beim Tausch gleich "
        "bleiben - sonst zeigt die Probe nicht, was sie zeigen soll"
    )
    schaden = _backlayer_mangel(kaputt)
    assert (any(s.startswith("WerkzeugView:") for s in schaden)
            and any(s.startswith("FahrzeugView:") for s in schaden)), (
        "Der Tausch wird nicht bemerkt - der Riegel misst wieder nur die "
        "Gesamtzahl. Gemeldet wurde: %r" % (schaden,)
    )


def test_umkehrprobe_fremde_verdrahtung_wird_rot(index_html):
    """Das Verbot bleibt: eine Verdrahtung ausserhalb aller benannten Traeger
    faellt weiterhin auf - jetzt mit Angabe, wie viele es sind."""
    code = nur_code(index_html) + chr(10) + "useBackLayer(true,()=>{});"
    assert any("ausserhalb ALLER benannten" in s
               for s in _backlayer_mangel(code)), \
        "Eine ungewollte useBackLayer-Verdrahtung bleibt unbemerkt"


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
