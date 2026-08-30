"""Static invariants about the index.html shape."""


def test_index_exists(index_html):
    assert len(index_html) > 0


def test_index_size_plausible(index_html):
    # Single-file app, expected ~16k+ lines
    lines = index_html.count("\n")
    assert 10_000 < lines < 50_000, f"index.html has {lines} lines, expected 10k-50k"


def test_index_doctype(index_html):
    assert index_html.lstrip().startswith("<!DOCTYPE html>")


def test_index_german_lang(index_html):
    assert 'lang="de"' in index_html[:500]


# ── GESTRICHEN v3.9.921: test_bracket_baseline ──────────────────────────────
# Hier stand `assert (paren, brace, bracket) == (-7, 0, 0)` ueber die ROHE
# Datei - Strings, HTML-Text und Kommentare mitgezaehlt.
#
# WARUM ERSATZLOS WEG (damit es niemand wieder einbaut):
#
# 1. Die Zahl misst Fliesstext, nicht Code. Gemessen an v3.9.920 stehen allein
#    in den JS-Blockkommentaren 6.879 "(" und 6.998 ")" - Saldo -119. Wie
#    jemand einen Erklaerkommentar formuliert, entscheidet ueber gruen/rot.
# 2. Der Sollwert IST der Defekt. Er wurde nachweislich schon von -5 auf -7
#    nachgezogen (v3.9.703, siehe die geloeschte Begruendung). Eine Zahl, die
#    man beim Bauen anpasst, kann keinen Fehler finden - sie schreibt ihn mit.
# 3. Das Echte ist doppelt abgedeckt und misst NUR Code:
#      scripts/_bracket_check.py  entfernt Strings/Kommentare, verlangt
#                                 () -1 / {} 0 / [] 0  -> test_bracket_drift_guard
#      node --check je Skriptblock -> test_integration_smoke
#    Gefangen hat die zwei kaputten Dateien vom 29.08. genau der node-Riegel;
#    die rohe Zahl hat dort nichts beigetragen (siehe test_keine_werkzeugspuren).
# 4. Dass die Streichung nichts kostet, ist BELEGT und nicht behauptet:
#    tests/test_bracket_drift_guard.py enthaelt seit v3.9.921 zwei Umkehrproben
#    - fehlende Klammer im CODE macht _bracket_check rot, ueberzaehlige Klammer
#    im KOMMENTAR laesst ihn gruen. Genau diese zweite Probe ist der Beweis,
#    dass die rohe Zahl Prosa gemessen hat.
#
# Auch die "{} 0 / [] 0"-Haelfte ist mit weg: roh sind sie nur deshalb 0, weil
# sich Strings und Prosa zufaellig ausgleichen. Die belastbare Aussage darueber
# trifft _bracket_check.py am gestrippten Code.
