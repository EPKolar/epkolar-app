"""v3.9.120 — Kunden-Nr aus OFFA sichtbar bei Arbeitsscheinen.

Vorher: Parser extrahierte kein kundNr, commitImport setzte kundNr:"" hart, und Liste/Karte
zeigten nur kundName → Kunden-Nr nirgends sichtbar (obwohl JUPROWA sie als AK_BAUADR_NUMMER liefert).
"""
import json
import re
from conftest import run_node_snippet


def test_parser_has_kundnr_field_and_regex(index_html):
    assert 'const r={nummer:"",kundNr:"",kundName:""' in index_html, "OFFA-Parser braucht kundNr im Ergebnis-Objekt"
    assert "if(mKd)r.kundNr=mKd[1];" in index_html, "OFFA-Parser braucht Kunden-Nr-Extraktion"


def test_kundnr_regex_behavior(node_exe, index_html):
    m = re.search(r"const mKd=chunk\.match\((/.+?/i)\);", index_html)
    assert m, "Kd-Regex nicht gefunden"
    rx = m.group(1)
    snippet = (
        "const rx=" + rx + ";"
        "const t=s=>{const m=s.match(rx);return m?m[1]:null;};"
        "process.stdout.write(JSON.stringify(["
        "t('Kunden-Nr.: 200668 Sachbearb.: X'),"
        "t('Kd-Nr: 123456'),"
        "t('KdNr 9876'),"
        "t('Sachbearb.: MAYER Projektnr.: PA241923')"  # kein Treffer
        "]));"
    )
    res = json.loads(run_node_snippet(node_exe, snippet))
    assert res == ["200668", "123456", "9876", None], f"Kd-Regex-Verhalten falsch: {res}"


def test_commit_import_maps_kundnr(index_html):
    assert 'kundNr:r.kundNr||""' in index_html, "commitImport muss geparste Kd-Nr übernehmen (nicht hartkodiert leer)"
    assert "if(r.kundNr)upd.kundNr=r.kundNr;" in index_html, (
        "Re-Import: Kd-Nr nur setzen wenn geparst — nie Bestehendes mit leer überschreiben"
    )


def test_kundnr_rendered_in_list_views(index_html):
    assert '"· Kd-Nr ", a.kundNr)' in index_html, "AS-Karte muss Kd-Nr anzeigen"
    assert index_html.count("a.kundNr&&React.createElement('span'") == 2, "Karte UND Tabelle zeigen Kd-Nr"
