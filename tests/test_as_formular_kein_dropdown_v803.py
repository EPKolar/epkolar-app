# -*- coding: utf-8 -*-
"""v3.9.803 — Kein-Dropdown-Grundsatz im AS-Formular (Sebastian).

Was die App im Detail-Formular NICHT aenderbar halten kann, wird von Select/Input auf reine
Text-Anzeige umgebaut:
1) Auftragstyp (v799 disabled-Select) -> Text (Icon+Label wie Liste) + OFFA-Badge.
2) Sachbearbeiter (im Formular nicht bearbeitbar) -> Text-Anzeige (Wert sichtbar).

Die LISTE bleibt byte-identisch: dort editiert das Buero SB/Prio/Status/Monteur inline wie gehabt.
"""


def _as(index_html):
    a = index_html.index("function ArbeitsscheinView({")
    return index_html[a:index_html.index("function EZKalender(props){", a)]


def test_formular_auftragstyp_ist_text(index_html):
    a = _as(index_html)
    # Kein disabled-Select mehr fuer den Auftragstyp im Formular.
    assert "value: form.scheinart, disabled: true" not in a, "Auftragstyp im Formular noch als (disabled) Select"
    assert "value: form.scheinart, onChange" not in a, "Auftragstyp im Formular noch editierbarer Select"
    # Reine Text-Anzeige (Icon+Label aus AS_ART) + OFFA-Badge.
    assert '(AS_ART[form.scheinart]?(AS_ART[form.scheinart].i+" "+AS_ART[form.scheinart].l):"—")' in a, \
        "Auftragstyp-Text-Anzeige (Icon+Label) fehlt"
    assert '"OFFA")))' in a, "OFFA-Badge am Auftragstyp fehlt"


def test_formular_sachbearbeiter_ist_text(index_html):
    a = _as(index_html)
    assert "value: form.sachbearbeiter, onChange" not in a, "Sachbearbeiter im Formular noch editierbarer Select"
    # Text-Anzeige des Werts.
    assert "React.createElement('span', {}, form.sachbearbeiter||\"—\")" in a, "Sachbearbeiter-Text-Anzeige fehlt"


def test_liste_sb_dropdown_unveraendert(index_html):
    # HART: das SB-Dropdown in der LISTE bleibt editierbar (updAs-Weg).
    assert 'value: a.sachbearbeiter||"", onChange: e=>{e.stopPropagation();updAs(a.id,{sachbearbeiter:e.target.value});}' in index_html, \
        "Listen-SB-Inline-Editor veraendert"
    # Liste: Prio + Status + Monteur inline weiter editierbar (byte-identisch).
    assert "updAs(a.id,{prioritaet:e.target.value})" in index_html, "Listen-Prio-Editor veraendert"
    assert "updAs(a.id,{scheinstatus:_newS})" in index_html, "Listen-Status-Editor veraendert"
    assert "updAs(a.id,{monteur:e.target.value})" in index_html, "Listen-Monteur-Editor veraendert"
