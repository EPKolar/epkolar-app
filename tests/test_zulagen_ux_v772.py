# -*- coding: utf-8 -*-
"""v3.9.772 — Zulagen-Tab-Seite UX (VBueroExport/KVZulagenReport). NUR Anzeige.

(1) Vorschau-Warnkasten kompakt + Details-Aufklapp (_ezDetail).
(3) Vergabe-Panel flach (kein mzOpen-Klappblock mehr).
Rechnung/Sätze/Ergebnis-Zahlen unberührt (test_rechnung_unberuehrt in v771 bleibt grün).
"""
import re


def test_warnkasten_kompakt(index_html):
    assert "'⚠ Vorschau — Lohnverrechner maßgeblich, keine Abrechnungsgrundlage.'" in index_html, \
        "kompakter Ein-/Zweizeiler-Warnkasten fehlt"
    # der alte lange Dauertext ist nicht mehr dauerhaft sichtbar, sondern im Detail-Aufklapp
    assert "'⚠ VORSCHAU — der Lohnverrechner ist maßgeblich. Die App-Zahl" not in index_html, \
        "alter langer Dauer-Warnkasten noch vorhanden"


def test_details_aufklapp(index_html):
    assert "const [_ezDetail,_setEzDetail]=_react.useState.call(void 0, false)" in index_html, \
        "Detail-Aufklapp-State fehlt"
    assert "_setEzDetail(function(v){return !v;})" in index_html, "Details-Toggle verdrahtet nicht _setEzDetail"
    # der Prüfpunkt-Text lebt jetzt im Detail-Block
    assert "_ezDetail?h('div'" in index_html, "Detail-Block nicht an _ezDetail gebunden"
    assert "167 h vs. Zeiteinträge 158 h" in index_html, "Prüfpunkt-Text (167/158) nicht mehr vorhanden"


def test_vergabe_flach_kein_klappblock(index_html):
    assert "(mzOpen&&!mzMissing)?_mzPanel():null" not in index_html, \
        "Vergabe haengt noch am mzOpen-Klappblock"
    assert "(mzOpen?'▲':'▼')+' \U0001F527 Montagezulage-Tage vergeben'" not in index_html, \
        "Klapp-Button 'Montagezulage-Tage vergeben' noch vorhanden"
    assert ",!mzMissing?_mzPanel():null" in index_html, "Vergabe-Panel nicht flach direkt gerendert"
    assert "h('div',{style:{fontSize:13,fontWeight:700,marginBottom:8}},'\U0001F527 Montagezulage-Tage vergeben')" in index_html, \
        "flacher Vergabe-Titel fehlt"


def test_rechnung_zahlen_unberuehrt(index_html):
    """Sätze + Rechenkern unverändert (harte Grenze)."""
    assert "taggeldAb6h:11.71," in index_html, "Entfernungszulage-Satz verändert"
    assert "montagezulageStd:1.13," in index_html, "Montagezulage-Satz verändert"
    for fn in ("function _kvMontagezulageTag(", "function _kvTaggeldTag(", "function _kvZulagenMonat("):
        assert fn in index_html, "Rechenfunktion versehentlich entfernt: " + fn
