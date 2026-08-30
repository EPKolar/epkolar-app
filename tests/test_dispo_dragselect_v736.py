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
    # BEIDE Drags (Pin/Reschedule _chipDrag UND Hoehen-Griff _dauerDrag) unterdruecken die Textauswahl.
    # v3.9.737: refactored in den geteilten Helfer _dragSelOff() (setzt body userSelect none) — beide rufen ihn.
    assert 'document.body.style.userSelect="none"' in body, "kein globales userSelect none beim Drag"
    # KEINE ZAHL MEHR (v3.9.913). Vorher: `body.count("_dragSelOff()") >= 2`.
    # "Beide Drags rufen ihn" ist eine Aussage ueber ZWEI BENANNTE Handler, nicht
    # ueber eine Summe: zweimal _chipDrag und kein _dauerDrag haette die Zahl
    # ebenso erfuellt. Jetzt wird je Handler geschnitten und dort nachgesehen -
    # damit faellt auch die Anfaelligkeit gegen Kommentartext weg.
    for anker, wer in (
        ("var _chipDrag=function(scheinId,mid,label,dauerMin,opts){return function(e){",
         "der Chip-Drag (Pin/Verschieben)"),
        ("var _dauerDrag=function(scheinId,baseMin,normMin){return function(e){",
         "der Hoehen-Griff (Dauer ziehen)"),
    ):
        i = body.find(anker)
        assert i != -1, "Handler nicht mehr auffindbar: " + wer
        assert "_dragSelOff();" in body[i:i + 600], \
            wer + " ruft den Selektions-Aus-Helfer nicht - dort markiert der Browser weiter Text"


def test_kacheln_userselect_none(index_html):
    body = _panel(index_html)
    assert 'userSelect:"none"' in body, "Kacheln erlauben noch Textselektion (userSelect:none fehlt)"
