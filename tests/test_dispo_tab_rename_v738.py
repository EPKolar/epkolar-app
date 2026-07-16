# -*- coding: utf-8 -*-
"""v3.9.738 — Register #21: der AS-Sub-Tab heisst "Dispo" (vorher "Vorschlag").

Sebastian: der Ort heisst Dispo. Tab-Label (Desktop + Mobile-Label-unter-Icon aus v720) und Panel-
Ueberschrift ("Vorschlagsplanung · KW" -> "Dispo · KW") ziehen um. Die FACHBEGRIFFE "Vorschlags-Chip"
und "Vorschlag uebernehmen" im Fliesstext bleiben (ein Vorschlag bleibt ein Vorschlag — nur der Ort
heisst Dispo).
"""


def test_tab_label_ist_dispo(index_html):
    # Der Sub-Tab (nur admin/buero/projektleiter) traegt jetzt l:"Dispo".
    assert '{id:"dispo",i:"🗓",l:"Dispo"}' in index_html, "Tab-Label nicht auf 'Dispo' umgezogen"
    assert '{id:"dispo",i:"🗓",l:"Vorschlag"}' not in index_html, "altes Tab-Label 'Vorschlag' noch da"


def test_panel_ueberschrift_ist_dispo(index_html):
    assert '"🗓 Dispo · "' in index_html, "Panel-Ueberschrift nicht 'Dispo · KW'"
    assert "🗓 Vorschlagsplanung · " not in index_html, "alte Ueberschrift 'Vorschlagsplanung · KW' noch da"


def test_fachbegriffe_bleiben(index_html):
    # Die inhaltlichen Begriffe bleiben unangetastet (nur der TAB/Titel heisst Dispo).
    assert "Vorschlag übernommen" in index_html, "Fachbegriff 'Vorschlag uebernommen' faelschlich entfernt"
    assert "Reiner Vorschlag" in index_html, "Fachtext 'Reiner Vorschlag (read-only)' faelschlich entfernt"
