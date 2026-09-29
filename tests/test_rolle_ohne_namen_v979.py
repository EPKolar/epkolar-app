# -*- coding: utf-8 -*-
"""Kein `role="button"` ohne Namen - und der Melder dafuer ist geeicht.

🔴 WARUM ES DIESEN RIEGEL GIBT.
`code_scan.knopf_stellen` findet jedes `<button>`, `hat_namen` prueft den
Namen. Beides ist geeicht und hat 17 namenlose Knoepfe gefunden. Und beides
ist fuer die Klasse, um die es hier geht, **prinzipiell blind**: seine
Grundgesamtheit ist `button`.

Am 28.09.2026 fand eine Messung fuenf `<span role="button">` mit dem Inhalt
`★` - eine Bewertungsanzeige, die erst durch v3.9.975 zu Knoepfen geworden
war. Das Bauwerkzeug gab jeder Flaeche mit einem `onClick` die Rolle und
keinen Namen dazu. Der Melder `scripts/rolle_ohne_namen.py` schliesst die
Luecke im Quelltext und fand daraufhin vier weitere, die keine Messung
erreicht hatte - darunter die drei bildschirmfuellenden Hintergrundflaechen
der Ueberlagerungen.

🔴 DER MELDER HAT SICH DABEI ZWEIMAL SELBST KORRIGIERT, und beide Fassungen
sahen nach einem Ergebnis aus:

  1. Er zaehlte die LITERALE im Kindteil. Eine Sortier-Kopfzeile
     `, h.l, h.c?pfeil(h.c):""` galt damit als namenlos - der Name steht in
     der Variablen `h.l`, das einzige Literal ist das leere aus dem anderen
     Zweig. Genau die Form, an der ich am 27.09. zweimal falsch lag.
  2. Danach gab er auf, sobald IRGENDEIN Teil unbekannt war - und meldete
     `, "Nummer", pfeil("nummer")` als "ansehen". Der Name eines Elements ist
     die Verkettung ALLER Kinder; ein wortfuehrendes Literal genuegt. Aus 7
     unsicheren wurden 55, und eine Liste, die niemand mehr durchsieht, ist
     so wertlos wie eine falsche Null.

Die Einordnung ist jetzt monoton, und beide Fehlalarme stehen als Koeder in
`scripts/rolle_ohne_namen.py`.

🔴 WAS DIESER RIEGEL NICHT KANN.
Der zugaengliche Name eines `role="button"` wird aus dem gesamten Teilbaum
berechnet. Ein `div` mit Rolle, das andere Elemente mit Text enthaelt, ist
benannt - dieser Melder sieht nur eine Ebene und fuehrt solche Faelle als
UNSICHER. Die Zahl der unsicheren ist deshalb hier festgeschrieben: sie darf
nicht unbemerkt wachsen, aber sie ist kein Befund.
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "scripts"))

import rolle_ohne_namen as R  # noqa: E402

# Der Stand am 28.09.2026 nach der Kur. UNSICHER darf fallen, nicht steigen.
UNSICHER_HOECHSTENS = 40


def test_der_melder_ist_geeicht():
    """🔴 Ohne diese Probe ist jede Zahl unten wertlos.

    Dreizehn Koeder, davon zwei Gegenproben und zwei, die genau die beiden
    Fehlalarme abbilden, die dieser Melder schon produziert hat.
    """
    schief = R.eichen()
    assert not schief, (
        "Der Melder ist nicht geeicht:\n%s"
        % "\n".join("   %r: erwartet %s, gemessen %s" % s for s in schief))


def test_kein_rollenknopf_ohne_namen():
    text = R.io.open(os.path.join(HIER, "..", "index.html"),
                     encoding="utf-8", newline="").read()
    namenlos, unsicher, benannt = R.einordnen(text)
    assert not namenlos, (
        "%d Elemente tragen `role=\"button\"` ohne jeden Namen:\n%s\n"
        "Eine Rolle ohne Namen ist fuer eine Vorlesehilfe SCHLECHTER als gar "
        "keine Rolle:\n"
        "das Element heisst dann 'Schaltflaeche' und sonst nichts. Entweder "
        "bekommt es\n"
        "einen Namen (aria-label/title oder Text) - oder die Rolle kommt weg."
        % (len(namenlos),
           "\n".join("   Zeile %d  %s  %s" % n for n in namenlos)))


def test_die_unsicheren_wachsen_nicht():
    """Die Faelle, die ein Mensch ansehen muss - als Zahl festgeschrieben.

    Sie sind KEIN Befund: ein `div` mit Rolle, das Text-Elemente enthaelt,
    ist benannt, und diesen Teilbaum sieht der Melder nicht. Aber die Zahl
    darf nicht unbemerkt wachsen - sonst verschwindet ein echter Fall darin.
    """
    text = R.io.open(os.path.join(HIER, "..", "index.html"),
                     encoding="utf-8", newline="").read()
    namenlos, unsicher, benannt = R.einordnen(text)
    assert len(unsicher) <= UNSICHER_HOECHSTENS, (
        "%d unsichere Faelle, erlaubt sind %d. Entweder ist eine neue Bauform "
        "dazugekommen,\n  die der Melder nicht auswerten kann - dann gehoert "
        "sie ihm beigebracht -,\n  oder es sind wirklich mehr geworden."
        % (len(unsicher), UNSICHER_HOECHSTENS))


def test_die_grundgesamtheit_ist_nicht_leer():
    """🔴 Gegenprobe zur Null: findet der Melder ueberhaupt Rollen-Knoepfe?"""
    text = R.io.open(os.path.join(HIER, "..", "index.html"),
                     encoding="utf-8", newline="").read()
    namenlos, unsicher, benannt = R.einordnen(text)
    gesamt = len(namenlos) + len(unsicher) + len(benannt)
    assert gesamt >= 80, (
        "Nur %d Elemente mit `role=\"button\"` gefunden. v3.9.975 hat allein "
        "41 Flaechen\n  gebaut; bei so wenigen Treffern misst das Muster nicht "
        "mehr die Bauform, und\n  die Null der anderen Pruefung ist wertlos."
        % gesamt)
