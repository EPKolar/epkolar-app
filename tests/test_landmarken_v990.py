# -*- coding: utf-8 -*-
"""Jede Ansicht hat genau einen Bereich, zu dem man springen kann.

🔴 GEFUNDEN AM 29.09.2026, und es stand auf keiner Liste. Im ganzen Programm
gab es **keinen einzigen Landmark**: kein `<main>`, kein `<nav>`, keine
`role="main"`, nichts - in allen Schreibweisen null Treffer.

Fuer eine Vorlesehilfe heisst das: keine Stelle, zu der man springen kann,
und keine Auskunft darueber, in welchem Bereich man gerade ist. Man haengt am
Anfang fest und muss auf JEDER Ansicht neu durch die ganze Kopfzeile tabben.

DIE KUR WAR EIN WORT AN ZWEI STELLEN: `div` -> `main` an `.main-pad` (die
App-Huelle) und an `.proj-main` (die Projekthuelle, die sie ersetzt). Vorher
gemessen: kein `div.main-pad`- oder `div.proj-main`-Selektor, kein
JS-Zugriff auf die Klassen, jede genau EINMAL gerendert. Alle CSS-Regeln
waehlen ueber die Klasse - die Darstellung aendert sich nicht.

🔴 DAS IST NICHT FRAGE 14. Dort geht es um eine sichtbare UEBERSCHRIFT, und
eine zu erfinden hiesse, an der auffaelligsten Stelle der Seite etwas zu
behaupten, das niemand entschieden hat. Ein `<main>` ist unsichtbar,
behauptet nichts und braucht keinen Namen.

AM SCHIRM GEMESSEN, 12 Ansichten, JE MIT FRISCHEM KONTEXT:

    alle 12: genau 1 `main`, keines leer

🔴 UND DER ERSTE LAUF HAT SICH GEIRRT, was hier steht, weil es wiederkommen
wird: er navigierte in EINER Sitzung durch alle Ansichten und meldete sieben
ohne `main`. Die Reihenfolge verriet den Fehler - ALLE Nullen kamen NACH
`plaene`, und das betritt ein Projekt; die Sitzung blieb danach in der
Projekthuelle. Das waere eine Aussage ueber die NAVIGATION gewesen, verkauft
als Aussage ueber die Ansichten.

🔴 WAS NOCH FEHLT, und es steht hier, statt verschwiegen zu werden: `nav` ist
in allen 12 Ansichten **0**. Die Reiterleiste ist kein `<nav>`. Das ist
dieselbe Fehlerklasse, aber kein Ein-Wort-Fix: es gibt mehrere Navigationen
(Reiterleiste, Seitenleiste im Projekt), und welche davon *die* Navigation
ist, gehoert entschieden. Zwei der zwoelf haben ausserdem keinen `header`
(die Projekthuelle).
"""
import io
import json
import os

HIER = os.path.dirname(os.path.abspath(__file__))
BEFUND = os.path.join(HIER, "..", "docs", "befunde", "LANDMARKEN.json")
ERZEUGEN = "python scripts/landmarken_messen.py 1440"
# So viele Ansichten standen am 29.09. in der Aufnahme. Weniger heisst:
# der Lauf ist irgendwo ausgestiegen, und die Nullen sagen nichts.
MINDEST_ANSICHTEN = 12


def _befund():
    assert os.path.exists(BEFUND), (
        "Die Landmarken-Aufnahme fehlt: %s\n  Erzeugen mit:  %s\n"
        "  Ein Riegel, der sich beim Fehlen der Messung selbst ueberspringt, "
        "meldet gruen,\n  ohne etwas zu wissen." % (BEFUND, ERZEUGEN))
    return json.load(io.open(BEFUND, encoding="utf-8"))


def test_die_aufnahme_deckt_genug_ansichten_ab():
    """🔴 Gegenprobe zur Null: eine Aufnahme ueber zwei Ansichten wuerde
    hier alles gruen melden."""
    d = _befund()
    n = len(d.get("ansichten") or {})
    assert n >= MINDEST_ANSICHTEN, (
        "Die Aufnahme deckt nur %d Ansichten ab, am 29.09. waren es %d.\n"
        "  Neu aufnehmen:  %s" % (n, MINDEST_ANSICHTEN, ERZEUGEN))


def test_jede_ansicht_hat_genau_ein_main():
    d = _befund()
    ohne = [k for k, v in (d.get("ansichten") or {}).items()
            if v.get("main") != 1]
    assert not ohne, (
        "%d Ansichten haben nicht genau ein `main`: %s\n"
        "  KEINES heisst: eine Vorlesehilfe hat keine Stelle, zu der sie "
        "springen kann.\n  MEHRERE heisst: sie weiss nicht, welche der "
        "Bereiche der Inhalt ist - die Norm\n  erlaubt nur eines je "
        "Dokument.\n  Messen mit:  %s"
        % (len(ohne), sorted(ohne), ERZEUGEN))


def test_kein_main_ist_leer():
    """Ein Bereich, zu dem man springt und in dem nichts steht, ist
    schlimmer als keiner - er sieht aus wie eine Zusage."""
    d = _befund()
    leer = [k for k, v in (d.get("ansichten") or {}).items()
            if v.get("main_leer")]
    assert not leer, (
        "%d Ansichten haben ein `main` mit fast keinem Text: %s\n"
        "  Wer dorthin springt, landet im Leeren." % (len(leer), sorted(leer)))
