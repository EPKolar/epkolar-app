# -*- coding: utf-8 -*-
"""v3.9.761 — Register #30f: Datenfrische der Dispo (visibilitychange).

Problem: bleibt der Tab stundenlang offen, plant die Disponentin auf veraltetem Stand. Fix: bei Tab-
Sichtbarkeit die Dispo neu ziehen+rechnen — aber (1) nur wenn der letzte Stand aelter als ~60s ist
(Alters-Guard, kein Refresh-Sturm), (2) NIE waehrend einer aktiven Geste (_chipDrag ODER _dauerDrag),
sonst reisst der Recompute den Chip/Griff aus der Hand -> dann 'defer' bis Gestenende.

PURE Kern (node-eval): _dispoRefreshEntscheidung(visible,lastMs,nowMs,gestureActive,minAgeMs)
  -> 'refresh' | 'skip' | 'defer'.
READ-ONLY: der Refresh liest dispo_blocks (42P01-tolerant) + rechnet via _setTick, schreibt NIE
(v745-Garantie erweitert). Listener wird beim Unmount abgeraeumt (kein Leak, v737).
"""
import re
import subprocess


def _panel(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    return index_html[start:end]


# ---------------------------------------------------------------- static wiring

def test_entscheidung_fn_und_export(index_html):
    assert "function _dispoRefreshEntscheidung(visible,lastMs,nowMs,gestureActive,minAgeMs){" in index_html, \
        "_dispoRefreshEntscheidung fehlt/Signatur veraendert"
    assert "window._dispoRefreshEntscheidung=_dispoRefreshEntscheidung;" in index_html, "kein window-Export"


def test_visibilitychange_listener_mit_cleanup(index_html):
    body = _panel(index_html)
    assert "document.addEventListener('visibilitychange',_onDispoVis)" in body, "kein visibilitychange-Listener"
    assert "document.removeEventListener('visibilitychange',_onDispoVis)" in body, "kein Listener-Cleanup (Leak, v737)"
    assert "_dispoRefreshEntscheidung(" in body, "der Listener nutzt die Frische-Entscheidung nicht"
    assert "60000" in body, "kein 60s-Alters-Guard verdrahtet"


def test_refresh_pfad_ist_readonly(index_html):
    """Der Frische-Refresh liest (dispo_blocks) + rechnet (_setTick), schreibt NIE (v745 erweitert)."""
    body = _panel(index_html)
    i = body.index("var _doDispoRefresh=function()")
    seg = body[i:i + 900]
    assert '_sbGet("dispo_blocks")' in seg, "Refresh zieht dispo_blocks nicht frisch"
    assert "_setTick(" in seg, "Refresh rechnet nicht neu (kein _setTick)"
    for bad in ("_sbPost", "_sbPatch", "_sbUpsert", "_sbDelete", "updAs(", "SQ.push", "_juprowaPush"):
        assert bad not in seg, "Schreibhelfer '%s' im Refresh-Pfad — der Refresh muss read-only sein" % bad


def test_geste_guard_beide_drags(index_html):
    body = _panel(index_html)
    # _gestureRef deckt beide Gesten ab: _chipDrag UND _dauerDrag setzen es (der zweite setzt _dragRef NICHT).
    assert body.count("_gestureRef.current=true;") >= 2, "nicht beide Drags setzen _gestureRef (Dauer-Griff ungedeckt)"
    assert "_gestureEnd();" in body, "kein Gestenende-Hook (Defer-Nachholung)"
    # Defer-Mechanik: aufgeschobener Refresh wird nach Gestenende nachgeholt.
    assert "_pendRefreshRef.current" in body, "kein Pending-Refresh (Defer bis Gestenende)"
    m = re.search(r"var _gestureEnd=function\(\)\{[\s\S]{0,200}?\};", body)
    assert m and "_doDispoRefresh()" in m.group(0), "_gestureEnd holt den aufgeschobenen Refresh nicht nach"


# ---------------------------------------------------------------- node-eval

_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"


def _extract(index_html):
    start = index_html.index("function _dispoRefreshEntscheidung(")
    end = index_html.index("\n}", start) + 2
    return index_html[start:end]


def _run(node_exe, tmp_path, js, name):
    f = tmp_path / name
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout, (r.stdout or "") + (r.stderr or "")


def test_frische_entscheidung(index_html, node_exe, tmp_path):
    js = _extract(index_html) + _OK + u"""
var NOW=1000000;
// sichtbar + alt (>60s) -> refresh:
ok(_dispoRefreshEntscheidung(true, NOW-61000, NOW, false, 60000)==='refresh','sichtbar+alt -> refresh');
// sichtbar + frisch (<60s) -> skip (kein Sturm):
ok(_dispoRefreshEntscheidung(true, NOW-5000, NOW, false, 60000)==='skip','sichtbar+frisch -> skip');
// Tab versteckt -> skip:
ok(_dispoRefreshEntscheidung(false, NOW-99000, NOW, false, 60000)==='skip','versteckt -> skip');
// Geste aktiv -> defer (auch wenn alt+sichtbar):
ok(_dispoRefreshEntscheidung(true, NOW-99000, NOW, true, 60000)==='defer','Geste aktiv -> defer');
ok(_dispoRefreshEntscheidung(true, NOW-5000, NOW, true, 60000)==='defer','Geste dominiert Frische -> defer');
// kein lastMs (erster Lauf) + sichtbar -> refresh:
ok(_dispoRefreshEntscheidung(true, 0, NOW, false, 60000)==='refresh','kein Vor-Stand -> refresh');
// Default-minAge (60000) wenn nicht angegeben:
ok(_dispoRefreshEntscheidung(true, NOW-61000, NOW, false)==='refresh','Default-minAge: alt -> refresh');
ok(_dispoRefreshEntscheidung(true, NOW-5000, NOW, false)==='skip','Default-minAge: frisch -> skip');
// exakte 60s-Grenze: genau 60000 alt ist NICHT mehr frisch -> refresh:
ok(_dispoRefreshEntscheidung(true, NOW-60000, NOW, false, 60000)==='refresh','genau 60s -> refresh');
console.log('OK');
"""
    _run(node_exe, tmp_path, js, "frische761.js")
