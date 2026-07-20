"""v3.9.120 — Kunden-Nr aus OFFA sichtbar bei Arbeitsscheinen.

Vorher: Parser extrahierte kein kundNr, commitImport setzte kundNr:"" hart, und Liste/Karte
zeigten nur kundName → Kunden-Nr nirgends sichtbar (obwohl JUPROWA sie als AK_BAUADR_NUMMER liefert).

v3.9.780: Der manuelle OFFA-PDF-Import (Parser _parseOffaPdf + commitImport) wurde als toter
Code entfernt (Kunden-Nr kommt nun ausschliesslich via Juprowa-Pull als AK_BAUADR_NUMMER).
Die Parser-/Commit-Tests sind daher Removal-Pins; die LISTEN-/KARTEN-Anzeige der Kd-Nr bleibt
und wird weiter gepinnt.
"""


def test_pdf_parser_removed_v780(index_html):
    assert 'const r={nummer:"",kundNr:"",kundName:""' not in index_html, (
        "v3.9.780: OFFA-PDF-Parser (_parseOffaPdf) muss entfernt bleiben"
    )
    assert "if(mKd)r.kundNr=mKd[1];" not in index_html, (
        "v3.9.780: Kd-Nr-Extraktion aus dem PDF-Parser muss entfernt bleiben"
    )


def test_commit_import_removed_v780(index_html):
    assert "const commitImport=" not in index_html, (
        "v3.9.780: commitImport (OFFA-PDF-Import-Commit) muss entfernt bleiben"
    )
    assert 'kundNr:r.kundNr||""' not in index_html, (
        "v3.9.780: commitImport-Mapping (kundNr:r.kundNr) muss mit dem Import-Flow entfernt sein"
    )


def test_kundnr_rendered_in_list_views(index_html):
    assert '"· Kd-Nr ", a.kundNr)' in index_html, "AS-Karte muss Kd-Nr anzeigen"
    assert index_html.count("a.kundNr&&React.createElement('span'") == 2, "Karte UND Tabelle zeigen Kd-Nr"
