# -*- coding: utf-8 -*-
"""v3.9.784 — Kiosk-Ansicht pro Tab ueberlebt den SW-Update-Hardreset (Sebastian 21.07.).

Diagnose: der Lager-Display faehrt 2 Tabs (?screen=planung + ?screen=monteure). Die Top-Level-Kiosk-Ansicht
wird NICHT in localStorage persistiert; _scr leitete sich rein aus ?screen ab. Der Hardreset (_forceCacheClear)
reloadete auf pathname+"?cc="+ts und verwarf dabei ?screen -> _kioskScreen=null -> _scr fiel auf den Default
'monteure', der Planungs-Tab sprang auf die Monteurtafel.

Fix (reines Routing/Persistenz): (1) _forceCacheClear setzt cc ADDITIV via new URL() -> ?screen+#hash bleiben.
(2) PURE _kioskScreenPick(hash,query,session): Restore-Prioritaet Hash > ?screen > sessionStorage. (3) Boot-Pin
per-Tab in sessionStorage(epk_kiosk_screen)+#hash (sessionStorage ueberlebt den Reload, per-Tab -> kein
Overwrite). (4) _scr liest window.__kioskScreen. KEIN Eingriff in Auth/RLS/SW-Update-Entscheidung.
"""
import json
from conftest import run_node_snippet, _extract_fn


def test_kiosk_screen_pick_prioritaet(node_exe, index_html):
    """Restore-Prioritaet Hash > ?screen-Query > sessionStorage; ungueltig/leer -> '' (Aufrufer-Default)."""
    fn = _extract_fn(index_html, "_kioskScreenPick")
    assert fn, "_kioskScreenPick nicht gefunden"
    snippet = fn + "\n" + (
        "const r={};"
        "r.hashWins=_kioskScreenPick('#planung','monteure','monteure');"       # Hash > Query/Session
        "r.queryOverSession=_kioskScreenPick('','planung','monteure');"        # Query > Session
        "r.sessionSurvives=_kioskScreenPick('','','planung');"                 # Session ueberlebt Hardreset (Hash+Query weg)
        "r.leerDefault=_kioskScreenPick('','','');"                           # nichts Gueltiges -> ''
        "r.invalidIgnored=_kioskScreenPick('#kaputt','xxx','planung');"       # ungueltige uebersprungen
        "r.normHash=_kioskScreenPick('#PLANUNG','','');"                      # case-insensitiv + #-strip
        "r.monteure=_kioskScreenPick('#monteure','','');"
        "r.stempel=_kioskScreenPick('#stempel','','');"
        "r.robustNull=_kioskScreenPick(null,undefined,null);"                 # null/undefined -> ''
        "process.stdout.write(JSON.stringify(r));"
    )
    r = json.loads(run_node_snippet(node_exe, snippet))
    assert r["hashWins"] == "planung", r
    assert r["queryOverSession"] == "planung", r
    assert r["sessionSurvives"] == "planung", r           # <- der Kern: der Planungs-Tab bleibt nach dem Reset
    assert r["leerDefault"] == "", r
    assert r["invalidIgnored"] == "planung", r
    assert r["normHash"] == "planung", r
    assert r["monteure"] == "monteure", r
    assert r["stempel"] == "stempel", r
    assert r["robustNull"] == "", r


def test_forcecacheclear_behaelt_screen(index_html):
    """Struktur-Pin: der Hardreset-Reload behaelt ?screen+#hash (cc additiv via new URL), kein pathname-Reset."""
    assert "var _u=new URL(window.location.href);_u.searchParams.set('cc',String(Date.now()));window.location.href=_u.toString();" in index_html, \
        "Cache-Buster muss ADDITIV gesetzt werden (?screen/#hash bleiben erhalten)"


def test_boot_pin_sessionstorage_und_hash(index_html):
    """Boot pinnt die aufgeloeste Ansicht per-Tab: sessionStorage epk_kiosk_screen + history.replaceState(#hash)."""
    assert "var pick=_kioskScreenPick(location.hash,_q,_s);" in index_html, "Boot muss die Ansicht aufloesen"
    assert "sessionStorage.setItem('epk_kiosk_screen',pick);" in index_html, "per-Tab sessionStorage-Pin fehlt"
    assert "history.replaceState(null,'','#'+pick)" in index_html, "Hash-Pin (replaceState) fehlt"
    assert "window.__kioskScreen=pick;" in index_html, "aufgeloeste Ansicht nicht fuer _scr exponiert"


def test_scr_liest_resolved_screen(index_html):
    """_scr nutzt die Boot-aufgeloeste Ansicht (Hash/Query/Session), nicht mehr nur die rohe Query."""
    assert "(typeof window!=='undefined'&&window.__kioskScreen)||_kioskScreen||'monteure'" in index_html


def test_kein_geteilter_localstorage_view_key(index_html):
    """Regression: der Kiosk persistiert die Top-Level-Ansicht per-Tab (sessionStorage), NICHT in geteiltem
    localStorage (das waere tab-uebergreifend und wuerde genau den gemeldeten Sprung verursachen)."""
    assert "localStorage.setItem('epk_kiosk_screen'" not in index_html
    assert "localStorage.getItem('epk_kiosk_screen'" not in index_html
    assert "sessionStorage.setItem('epk_kiosk_screen'" in index_html
