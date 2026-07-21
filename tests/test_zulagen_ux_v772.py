# -*- coding: utf-8 -*-
"""v3.9.772 — Zulagen-Tab-Seite UX (VBueroExport/KVZulagenReport). NUR Anzeige.

(1) Vorschau-Warnkasten kompakt + Details-Aufklapp (_ezDetail).
(3) Vergabe-Panel flach (kein mzOpen-Klappblock mehr).
Rechnung/Sätze/Ergebnis-Zahlen unberührt (test_rechnung_unberuehrt in v771 bleibt grün).
"""
import re


def test_warnkasten_kompakt(index_html):
    # v3.9.785: kompakter lohnrelevanter Warnkasten, Wortlaut auf das 3-Stufen-Modell aktualisiert
    # (frueher "eff. Tage" -> jetzt "Stufe je Tag: klein/mittel/groß").
    assert "⚠ Entfernungszulage — lohnrelevant: die Kalender-Vergabe (Stufe je Tag: klein/mittel/groß) bestimmt die abgerechnete Menge. Genau eine Stufe pro Tag. Lohnverrechner maßgeblich." in index_html, "kompakter lohnrelevanter Warnkasten fehlt"
    assert "⚠ VORSCHAU — der Lohnverrechner ist maßgeblich. Die App-Zahl" not in index_html, "alter langer Dauer-Warnkasten noch vorhanden"


def test_details_aufklapp(index_html):
    assert "const [_ezDetail,_setEzDetail]=_react.useState.call(void 0, false)" in index_html, \
        "Detail-Aufklapp-State fehlt"
    assert "_setEzDetail(function(v){return !v;})" in index_html, "Details-Toggle verdrahtet nicht _setEzDetail"
    # der Prüfpunkt-Text lebt jetzt im Detail-Block
    assert "_ezDetail?h('div'" in index_html, "Detail-Block nicht an _ezDetail gebunden"


def test_rechnung_zahlen_unberuehrt(index_html):
    """Entfernungszulage-Satz klein + Rechenkern. v3.9.785: KV-Satz klein 11,94 (Alt 11,71 war der FALSCHE Wert,
    KV-Blatt gueltig ab 01.01.2026); die Rechenfunktionen selbst bleiben bestehen."""
    assert "taggeldAb6h:11.94," in index_html, "Entfernungszulage klein nicht auf 11,94 (war 11,71 falsch)"
    for fn in ("function _kvTaggeldTag(", "function _kvZulagenMonat("):
        assert fn in index_html, "Rechenfunktion versehentlich entfernt: " + fn
