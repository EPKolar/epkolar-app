# -*- coding: utf-8 -*-
"""v3.9.742 — Register #23: Chip-Paritaet. Fixe (📌) und Vorschlags-Chips zeigen IDENTISCHE Infozeilen.

Sebastian: EINE gemeinsame Chip-Render-Funktion mit Flag (fix/vorschlag) statt zwei divergierender Pfade —
genau die Divergenz hat die Luecke erzeugt. Beide zeigen: Nummer (+⚠ war DD.MM.), Kunde/BVH (fett),
Arbeit/Titel (~60 Zeichen ellipst), Dauer · km (aus DERSELBEN #19-Kaskade — auch fixe haben Anfahrt) ·
Buendel-Hinweis, Zeitfenster Start–Ende. Fixe MIT termin_zeit -> echte Spanne; fixe OHNE Zeit -> Badge
"ohne Zeit". Einzige Unterschiede: Farbe/durchgezogener Rand + 📌, KEIN Uebernehmen-Button am fixen Chip.
"""


def _panel(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    return index_html[start:end]


def test_gemeinsame_render_funktion(index_html):
    body = _panel(index_html)
    assert "var _chipBox=" in body or "_chipBox=function" in body, "keine gemeinsame Chip-Render-Funktion"
    # Ein Name, zwei Aufrufe (fix + vorschlag).
    assert body.count("_chipBox(") >= 2, "die Chip-Render-Funktion wird nicht fuer beide Arten aufgerufen"


def test_fixer_chip_traegt_arbeit_und_km(index_html):
    body = _panel(index_html)
    # Der fixe Chip fuettert Arbeit (arbeitsanweisungen) UND ein km-Label (Kaskade) in die Render-Funktion.
    # Anker: die fixe .map liest arbeitsanweisungen und ein Strecken-Label.
    fx = body[body.index("_fx.map(function(f"):body.index("chips.map(function(c,ci)")]
    assert "arbeitsanweisungen" in fx, "fixer Chip zeigt keine Arbeit-Zeile"
    assert "_dispoStrecke" in fx or "kmLabel" in fx, "fixer Chip zeigt kein km (Anfahrt) aus der Kaskade"


def test_ohne_zeit_badge(index_html):
    body = _panel(index_html)
    assert "ohne Zeit" in body, "fixer Chip ohne termin_zeit zeigt kein 'ohne Zeit'-Badge"


def test_kein_uebernehmen_am_fixen_chip(index_html):
    body = _panel(index_html)
    fx = body[body.index("_fx.map(function(f"):body.index("chips.map(function(c,ci)")]
    assert "Übernehmen" not in fx and "Uebernehmen" not in fx, "fixer Chip hat faelschlich einen Uebernehmen-Button"
