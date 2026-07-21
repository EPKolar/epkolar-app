# -*- coding: utf-8 -*-
"""v3.9.795 — Navigation Schritt 2 E2 (Detail-Layer, Symptom 2).

AS-Schein-Detail (sub==="form") haengt jetzt am System-A-Back-Layer (useBackLayer,
Muster wie Werkzeug/Mangel). Browser-/Android-Zurueck aus dem geoeffneten Schein ->
genau der Sub-Tab, aus dem er geoeffnet wurde (Liste/Kalender/QR), nicht eine Ebene
zu hoch. Restore-Ziel kommt aus _asPrevSub (bei JEDEM openEdit frisch, nie stale);
Deep-Link/Dispo/ungueltiger Ursprung -> Fallback "liste".

Scope HART: NUR der form-Layer. Die AS-Sub-Tab-Leiste (liste/kalender/dispo/qrscan
untereinander) ist NICHT E2 -> genau EIN useBackLayer in der AS-View, und zwar der
form-Layer. popstate-Verhalten ist nicht statisch testbar (Sebastians Live-Klick ist
die Abnahme) — hier wird die Verdrahtung gepinnt.
"""
import re


def _as(index_html):
    # ACHTUNG: die AS-View enthaelt einen PDF-Template-String mit eingebettetem
    # "function sharePdf(){" (Spalte 0 im String) -> "\nfunction " als Grenze wuerde
    # zu frueh schneiden. Echte naechste Top-Level-Komponente = EZKalender.
    a = index_html.index("function ArbeitsscheinView({")
    b = index_html.index("function EZKalender(props){", a)
    return index_html[a:b]


def test_backlayer_einzeiler(index_html):
    c = _as(index_html)
    assert 'const _asPrevSub=_react.useRef.call(void 0, "liste");' in c, "_asPrevSub-Ref fehlt"
    assert 'useBackLayer(sub==="form", ()=>setSub(_asPrevSub.current||"liste"));' in c, \
        "useBackLayer-Einzeiler (form-Layer, Restore aus Ref) fehlt/veraendert"


def test_nur_ein_backlayer_in_as(index_html):
    # Scope: NUR der form-Detail-Layer. Die Sub-Tab-Leiste bekommt in E2 KEINEN eigenen Layer.
    c = _as(index_html)
    assert c.count("useBackLayer(") == 1, "AS-View hat != 1 useBackLayer (Scope: nur der form-Layer)"


def test_openEdit_setzt_prevsub_frisch(index_html):
    c = _as(index_html)
    assert "const openEdit=(a,_origin)=>{" in c, "openEdit-Signatur (a,_origin) fehlt"
    # frisch bei jedem Aufruf: aktueller sub (oder expliziter Ursprung), sonst Fallback liste.
    assert '_asPrevSub.current=(_o!=="form"&&(_o==="liste"||_o==="kalender"||_o==="dispo"||_o==="qrscan"))?_o:"liste";' in c, \
        "frisches/validiertes _asPrevSub-Capture in openEdit fehlt"


def test_deeplink_und_dispo_fallback_liste(index_html):
    c = _as(index_html)
    # Deep-Link __asOpenId ohne bekannten Ursprung -> explizit liste.
    assert 'delete window.__asOpenId;openEdit(_a,"liste");' in c, \
        "Deep-Link-Fallback openEdit(_a,'liste') fehlt"
    # Dispo-onOpenSchein oeffnet in Listen-Kontext -> explizit liste.
    assert c.count('openEdit(_a,"liste")') == 2, "erwartet genau 2 explizite liste-Fallbacks (Deep-Link + Dispo)"


def test_direkte_ui_aufrufer_ohne_origin(index_html):
    c = _as(index_html)
    # Liste/Kalender/QR rufen openEdit(a) einarmig -> Ursprung = aktueller sub.
    assert "openEdit(a)" in c, "direkter UI-Aufrufer openEdit(a) fehlt (Liste/Kalender)"
    assert "openEdit(asScannedAs)" in c, "QR-Scan-Aufrufer openEdit(asScannedAs) fehlt"


def test_kein_system_b_kein_hash_write(index_html):
    # /* ... */-Kommentare strippen -> nur echter CODE (Kommentare nennen Tokens bewusst).
    c = re.sub(r"/\*.*?\*/", "", _as(index_html), flags=re.S)
    for bad in ("_navPush", "_regSubView", "_subViewRef", "_navSubResolve"):
        assert bad not in c, "System-B-Rueckfall in AS-View-Code: " + bad
    assert "location.hash=" not in c, "unerlaubter Hash-Write in AS-View (Kiosk-Tabu)"


def test_e1_admin_intakt(index_html):
    # E1 (Admin) darf durch E2 nicht kaputtgehen.
    assert "useBackLayer(adminTab!==_admDefaultTab, ()=>setAdminTab(_admDefaultTab));" in index_html, \
        "E1-Admin-Verdrahtung verschwunden/veraendert"
