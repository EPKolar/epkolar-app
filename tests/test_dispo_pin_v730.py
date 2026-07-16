# -*- coding: utf-8 -*-
"""v3.9.730 Pin-Mechanik — ENTFERNT in v3.9.741 (#22b, Sebastian).

Der Drag&Drop-Pin (localStorage epk_dispo_pins + cfg.pins in _dispoPlan) war ein lokaler Zwischenzustand.
Mit dem EINEN Schreibgesetz (#22a/v740) schreibt jede Geste sofort in den Schein (onDrop -> updAs/E4b),
darum ist die Pin-Mechanik tot und wurde ersatzlos entfernt (0 Referenzen im Code). Die alten Pin-Tests
entfallen; das Drop-Verhalten deckt jetzt test_dispo_dropwrite_v740.py ab.
(Hinweis: die Wortmarke steht noch in der Versions-Historie des APP_VERSION-Kommentars — hier wird nur der
ausfuehrbare Code geprueft.)
"""


def _dispoplan_body(index_html):
    start = index_html.index("function _dispoPlan(cfg){")
    end = index_html.index("function _dispoBuildInput(", start)
    return index_html[start:end]


def _panel_body(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    return index_html[start:end]


def test_pin_mechanik_ist_aus_dem_code(index_html):
    plan = _dispoplan_body(index_html)
    panel = _panel_body(index_html)
    assert "cfg.pins" not in plan, "cfg.pins in _dispoPlan noch vorhanden"
    assert "epk_dispo_pins" not in panel, "Pin-localStorage im DispoPanel noch vorhanden"
    assert "_setPin" not in panel, "_setPin im DispoPanel noch vorhanden"
    assert "_pinned" not in panel, "_pinned im DispoPanel noch vorhanden"
