# -*- coding: utf-8 -*-
"""v3.9.746 — Register #25: vereinbarte Zeit != geplante Zeit — muss unterscheidbar sein.

Sebastian: Fixer Termin MIT termin_zeit -> Zeit wie bisher (fett, verbindlich). Fixer Termin OHNE
termin_zeit, von der Ablaufrechnung eingereiht -> Zeit mit "~" und kursiv/gedimmt + kleines Label "geplant"
+ Tooltip "Uhrzeit nicht vereinbart — von der Dispo eingeplant". Der Chip laesst sich weiter per Geste
verschieben; erst die GESTE schreibt die Zeit (22a-Schreibgesetz) und macht sie verbindlich (Umschlag auf
fett). Vereinbarte Zeit NIE mit Tilde.
"""


def _panel(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    return index_html[start:end]


def test_chipbox_kennt_geplant_flag(index_html):
    body = _panel(index_html)
    assert "o.geplant" in body, "_chipBox unterscheidet 'geplant' (Dispo-Zeit) nicht von 'vereinbart'"
    assert "geplant" in body, "kein 'geplant'-Label"
    assert "nicht vereinbart" in body, "kein Tooltip 'Uhrzeit nicht vereinbart'"


def test_fixe_ohne_zeit_wird_geplant(index_html):
    body = _panel(index_html)
    fx = body[body.index("_fx.map(function(f"):body.index("chips.map(function(c,ci)")]
    # fixe ohne termin_zeit bekommt eine GEPLANTE Zeit aus der Ablaufrechnung (nicht mehr nur 'ohne Zeit').
    assert "geplant:" in fx, "fixe Kachel ohne Zeit setzt kein geplant-Flag"
    assert "_slot" in fx or "_fxSlot" in fx, "fixe Kachel ohne Zeit bekommt keinen Ablauf-Slot (_fxSlot)"
    # v3.9.749 #27: der Ablauf-Slot fuer fixe-ohne-Zeit kommt jetzt aus der kombinierten Einreihung (_combAb):
    assert "_combAb" in _panel(index_html), "kein kombinierter _dispoAblauf-Slot fuer fixe ohne Zeit (_combAb)"
