"""
Checklisten-Protokoll-PDF (v3.9.840).

Button "📄 PDF" im Checklisten-Detail erzeugt ein A4-Protokoll: je Punkt Status
[x]/[ ] (via _clItemDone, deckt auch typisierte ③a-Werte), Wert+Einheit, Anmerkung,
plus die zwei Unterschriften. Neue reine Funktion _genChecklistPdf, latin1-sicher.
"""
import re


def _fn(index_html):
    i = index_html.find("async function _genChecklistPdf(")
    assert i != -1, "_genChecklistPdf fehlt"
    j = index_html.find("\nfunction ", i + 10)
    return index_html[i:j]


def test_funktion_und_export(index_html):
    assert "async function _genChecklistPdf(cl,proj)" in index_html
    assert "window._genChecklistPdf=_genChecklistPdf" in index_html


def test_button_verdrahtet(index_html):
    assert "_genChecklistPdf(selCl,p)" in index_html, "PDF-Button nicht mit selCl/p verdrahtet"


def test_latin1_sicher_kein_unicode_haken(index_html):
    b = _fn(index_html)
    # kein Unicode-Häkchen/Kreis (würde von _pdfStr gestrippt) — stattdessen [x]/[ ]
    assert '"[x]":"[ ]"' in b, "kein latin1-sicherer [x]/[ ]-Marker"
    assert "✓" not in b and "○" not in b, "Unicode-Haken/Kreis im PDF-Text (würde gestrippt)"


def test_nutzt_bausteine(index_html):
    b = _fn(index_html)
    for s in ("_clItemDone", "_pdfStr", "cl.sigMA", "cl.sigKunde", "splitTextToSize", "getNumberOfPages"):
        assert s in b, f"_genChecklistPdf nutzt {s} nicht"


def test_status_via_clitemdone(index_html):
    b = _fn(index_html)
    # Fortschritt/Status über _clItemDone (typisierte Felder zählen mit)
    assert "items.filter(_clItemDone)" in b
