# -*- coding: utf-8 -*-
"""v3.9.737 — Drag&Drop unterdrueckt Textauswahl ENDGUELTIG (Sebastian: "jetzt endgueltig sauber").

v736 (body userSelect none) reichte nicht: andere Zellen blieben selektierbar und die Browser-Selektion
begann trotzdem. Bulletproof: beide Drag-Gesten (_chipDrag Pin/Reschedule + _dauerDrag Hoehen-Griff)
  * preventDefault am pointerdown,
  * blockieren 'selectstart' auf document (haerteste Bremse — cancelt jede Selektion waehrend der Geste),
  * setzen body userSelect none + leeren die bestehende Selektion,
  * stellen ALLES bei pointerup UND pointercancel wieder her (Touch-Abbruch liess sonst userSelect haengen).
"""


def _panel(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    return index_html[start:end]


def test_selectstart_blocker(index_html):
    body = _panel(index_html)
    assert "selectstart" in body, "kein selectstart-Blocker waehrend des Drags"


def test_beide_drags_preventdefault_am_pointerdown(index_html):
    body = _panel(index_html)
    # _chipDrag UND _dauerDrag rufen preventDefault am pointerdown (e ist der pointerdown-Event).
    assert body.count("if(e&&e.preventDefault)e.preventDefault()") >= 2, "nicht beide Drags preventDefault am pointerdown"


def test_pointercancel_stellt_wieder_her(index_html):
    body = _panel(index_html)
    # Touch-Abbruch (pointercancel) muss dieselbe Aufraeum-/Restore-Logik ausloesen wie pointerup,
    # sonst bleibt die Seite unselektierbar (Review-Befund 6a).
    assert body.count("'pointercancel'") >= 2, "pointercancel wird in beiden Drags nicht behandelt"


def test_selektion_wird_geleert(index_html):
    body = _panel(index_html)
    assert "removeAllRanges" in body, "bestehende Selektion wird beim Drag-Start nicht geleert"
