# -*- coding: utf-8 -*-
"""v3.9.736 — Dispo: keine Text-Markierung (blaue Selektion) waehrend Drag&Drop.

Sebastian (16.07., live): "bei drag und drop werden die anderen termine noch textlich blau markiert, das
ist bloed. verschieben geht jedoch." Beim Ziehen selektiert der Browser Text auf den anderen Kacheln.
Fix: waehrend der Geste global die Textauswahl unterdruecken (document.body userSelect='none', bei
pointerup wiederherstellen) + die Kacheln selbst userSelect:none. Kein Verhalten geaendert (verschieben
funktioniert weiter), nur die Selektion weg.
"""


def _panel(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    return index_html[start:end]


def test_drag_unterdrueckt_globale_textauswahl(index_html):
    body = _panel(index_html)
    # BEIDE Drags (Pin/Reschedule _chipDrag UND Hoehen-Griff _dauerDrag) unterdruecken die Textauswahl
    # global und stellen sie bei pointerup wieder her (Sebastian: Dauer-Ziehen markierte nur Text).
    assert body.count('document.body.style.userSelect="none"') >= 2, "nicht beide Drags unterdruecken die Textauswahl"


def test_kacheln_userselect_none(index_html):
    body = _panel(index_html)
    assert 'userSelect:"none"' in body, "Kacheln erlauben noch Textselektion (userSelect:none fehlt)"
