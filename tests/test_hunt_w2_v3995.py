"""v3.9.110 — Bug-Hunt Welle 2 (Agententeam) — Regressions-Guards.

JUPROWA-Prio-Push, Excel-Summenspalte, Bescheinigung-Escaping.
"""


def test_juprowa_prio_rev_has_dringend(index_html):
    import re
    m = re.search(r"const JUPROWA_PRIO_REV=\{([^}]*)\}", index_html)
    assert m, "JUPROWA_PRIO_REV nicht gefunden"
    body = m.group(1)
    assert "dringend:'1'" in body, "dringend muss auf '1' gemappt sein (sonst Priorität-Verlust beim Push)"
    assert "niedrig:'0'" in body, "niedrig (korrekt geschrieben) muss vorhanden sein"
    assert "niedig" not in body, "Tippfehler-Key 'niedig' muss weg sein"


def test_exportxls_sumcol_is_hours(index_html):
    # Die KW-Zeiterfassungs-Export-genXls muss die Stunden-Spalte (5) summieren, nicht Typ (4).
    assert 'leftCols:[0,1,2,3,5,6,7],boldCols:[2],sumCol:5}' in index_html, (
        "exportXls muss sumCol:5 (Stunden) nutzen, nicht 4 (Typ-String → Gesamt 0,00)"
    )


def test_bescheinigung_escapes_freetext(index_html):
    start = index_html.index("function genBescheinigung(")
    body = index_html[start:start + 1200]
    assert "const _eB=" in body, "genBescheinigung muss einen Escape-Helfer definieren"
    assert "fahrer=_eB(fahrer)" in body and "ort=_eB(ort)" in body, (
        "Freitext-Felder (fahrer/ort/…) müssen vor der Template-Interpolation escaped werden"
    )
