# -*- coding: utf-8 -*-
"""v3.9.1007 - Projekt-Reiter "Zeiten" (VZeit): Stunden mit Komma, KW-Kopf ruhig.

Gemessen 412 px: "Stunden gesamt 616.0h" -> "616,0 h"; Tageskoepfe, Eintraege,
Wochenzeile und Monteur-Knoepfe ebenso. Eine Quelle: _projStdDE (PROJ-HANDY PR6),
dieselbe Rundung wie _n. Nur Anzeige - Exporte rufen VZeit nicht auf.
"""


def _vzeit(html):
    a = html.find("function VZeit({p,entries,setEntries,")
    e = html.find("function BerCell({h})", a)
    assert a != -1 and e > a
    return html[a:e]


def test_vzeit_zeigt_keine_punktstunden_mehr(index_html):
    v = _vzeit(index_html).replace("_projStdDE(", "")
    assert "_n(" not in v, (
        "In VZeit steht wieder _n(...) - das zeigt 616.0h mit Punkt statt "
        "616,0 h. Bitte _projStdDE nehmen.")


def test_stunden_gesamt_ueber_die_eine_quelle(index_html):
    v = _vzeit(index_html)
    i = v.find('"Stunden gesamt"')
    assert i != -1
    assert '_projStdDE(totalH,1), " h")' in v[i:i + 300]


def test_kein_blau_als_auswahl_oder_ziffer(index_html):
    """CI: Blau ist keine Auswahl- und keine Ziffernfarbe (v3.9.1006 Token-Tafel)."""
    assert "#3b82f6" not in _vzeit(index_html)


def test_kw_kopf_in_tinte(index_html):
    v = _vzeit(index_html)
    i = v.find('"KW ", String(calKw).padStart(2,"0")')
    assert i != -1
    kopf = v[v.rfind("React.createElement('span'", 0, i):i]
    assert "color:V.tx" in kopf and "_okG(" not in kopf
