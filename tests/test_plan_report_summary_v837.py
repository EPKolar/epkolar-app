"""
PlanRadar Plan-Report Status-Zusammenfassung (v3.9.837).

Der Übergabe-Report (_genPlanReportPdf) bekommt eine Kopfzeile mit dem Status-
Überblick (N Pins gesamt / offen / in Bearbeitung / erledigt / überfällig), damit
der Leser den Stand auf einen Blick sieht. Additiv.
"""
import re


def _fn_body(index_html):
    i = index_html.find("async function _genPlanReportPdf(")
    assert i != -1
    j = index_html.find("\nfunction ", i + 10)
    return index_html[i:j]


def test_summe_wird_berechnet(index_html):
    b = _fn_body(index_html)
    assert "const _sum={offen:0,in_bearbeitung:0,erledigt:0,rest:0,ueberfaellig:0};" in b, "keine Status-Zählung"
    # überfällig = Frist in der Vergangenheit UND nicht abgeschlossen
    assert 't.dueDate&&String(t.dueDate)<_today&&!_done' in b, "Überfällig-Kriterium fehlt/falsch"


def test_zusammenfassung_im_kopf(index_html):
    b = _fn_body(index_html)
    assert 'Pins gesamt' in b, "keine Zusammenfassungs-Kopfzeile"
    assert '"offen"' in b and '"überfällig"' in b or '" überfällig"' in b or "überfällig" in b


def test_nur_erste_seite(index_html):
    b = _fn_body(index_html)
    # die Zusammenfassung erscheint einmal (Seite 1), nicht auf jeder Plan-Seite
    assert "if(pi===0){const _parts=" in b, "Zusammenfassung nicht auf pi===0 begrenzt"
