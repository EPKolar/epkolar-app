# -*- coding: utf-8 -*-
"""Gemeinsame Helfer fuer Riegel der Form "Begriff kommt NICHT mehr vor".

WARUM ES DAS GIBT (v3.9.896): Ein `assert "x" not in index_html` hat zwei
Tuecken, die beide in dieser Sitzung zugeschnappt sind.

1. ER MISST DEN KOMMENTAR MIT. Wer etwas ausbaut, schreibt daneben, WAS er
   ausgebaut hat - und nennt den Begriff damit erneut. Der Riegel schlaegt an,
   obwohl der Code sauber ist. Das ist im Repo inzwischen zum zehnten Mal
   passiert, zuletzt beim Ausbau von `wocheKm`: der Erklaerkommentar zur
   Entfernung enthielt das Wort.

2. ER LAESST DEN LAUF HAENGEN STATT FEHLZUSCHLAGEN. Schlaegt er an, bereitet
   pytest den 3,5-MB-String als Fehlermeldung auf. Der Test faellt dann nicht
   um, er steht - und blockiert die ganze Suite.

Deshalb EINE Definition an EINER Stelle, statt sie je Testdatei nachzubauen -
zwei Kopien waeren die naechste Groesse mit zwei Rechnungen.
"""
import re


def nur_code(index_html):
    """index.html ohne Blockkommentare und ohne die APP_VERSION-Changelogzeile."""
    ohne = re.sub(r"/\*[\s\S]*?\*/", "", index_html)
    return chr(10).join(l for l in ohne.splitlines()
                        if not l.startswith("const APP_VERSION="))


def fundstellen(text, begriff, umfeld=60, max_treffer=3):
    """Kurze Ausschnitte statt der ganzen Datei - damit die Meldung lesbar ist."""
    aus, i = [], text.find(begriff)
    while i != -1 and len(aus) < max_treffer:
        aus.append(text[max(0, i - umfeld):i + len(begriff) + umfeld].replace(chr(10), " "))
        i = text.find(begriff, i + 1)
    return (chr(10) + "  ...").join(aus) if aus else "(keine)"
