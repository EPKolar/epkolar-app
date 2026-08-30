# -*- coding: utf-8 -*-
"""v3.9.894 - Tagesplan-Ausdruck fuer den Monteur.

Das letzte offene Stueck aus `HANDOFF_2026-07-15.md` ("Was die Damen brauchen").
Ein Knopf im Spaltenkopf jedes Tages druckt ein A4-Blatt mit einem Abschnitt je
Monteur: Zeit, Kunde und Ort, Scheinnummer, Arbeit, Dauer, Telefonnummer.

DIE WICHTIGSTE EIGENSCHAFT IST, WAS ER NICHT TUT: er rechnet nichts nach.

Die Startzeiten entstehen in `_zelle` ueber `_dispoAblaufBuendel`. Ein Ausdruck,
der sie neu berechnet, waere die naechste zweite Rechnung derselben Groesse -
genau die Krankheit, die v888 bis v893 in dieser Datei aufgeraeumt haben:

    v888  KW-Auslastung ungleich Zell-Balken (Zaehler)
    v891  Zell-Balken ungleich Wochenzahl    (Nenner)
    v886  Warteliste-Dauer ungleich Plan-Dauer
    v892  geschaetzte Dauer nicht als solche erkennbar

Deshalb: `_zelle` legt seine FERTIGEN Zeilen in einer Sammelmappe ab, der Druck
liest nur ab.

KLARTEXT STATT SYMBOLEN auf dem Blatt - auf Papier lesbarer, und es sagt, was es
bedeutet:
  "fix"         vereinbarter Kundentermin
  "~08:15"      aus dem Ablauf gerechnet, NICHT mit dem Kunden vereinbart
  "1.5h ca."    geschaetzte Dauer (dasselbe wie das Naeherungszeichen am Chip)

Eine Uhrzeit, die wie eine Zusage aussieht, aber keine ist, waere auf einem Blatt
in der Hand des Monteurs schlimmer als gar keine.

ZWEI STOLPERSTELLEN, die beim Bauen aufgefallen sind und hier festgehalten werden:

1. Die Sammelmappe benutzt bewusst ANDERE Parameternamen als die Kachel-
   Darstellung. Zwei Bestandstests grenzen die Kachel ueber die Zeichenfolge aus
   Feldname und einbuchstabigem Parameter ein - die Sammelmappe steht davor und
   lieferte ihnen sonst den falschen Block.

2. Der erste Erklaerkommentar dazu nannte genau dieses Suchmuster woertlich - und
   loeste die Kollision damit selbst aus. Er beschreibt es jetzt, ohne es
   auszuschreiben. (Und die dabei entstandenen unbalancierten Klammern im
   Prosatext hatten zugleich die Roh-Klammerbilanz aus test_invariants gekippt.)
"""
import re


def _panel(index_html):
    i = index_html.index("function DispoPanel({")
    j = index_html.index("function ArbeitsscheinView({", i)
    return index_html[i:j]


# ══ Der Druck rechnet nichts nach ═══════════════════════════════════════════

def test_es_gibt_eine_sammelmappe(index_html):
    block = _panel(index_html)
    assert "var _tagesplan={};" in block, (
        "Die Sammelmappe fehlt - dann muesste der Druck die Startzeiten selbst "
        "rechnen, und das waere eine zweite Rechnung derselben Groesse."
    )


def test_die_zellen_fuellen_sie_beim_rendern(index_html):
    block = _panel(index_html)
    assert '_tagesplan[m.id+"_"+t.key]=[].concat(' in block, (
        "_zelle legt seine Zeilen nicht mehr ab - die Sammelmappe bliebe leer "
        "und der Ausdruck druckte nichts."
    )


def test_der_druck_liest_nur_ab(index_html):
    """Der Kern: die Druckfunktion darf _dispoAblaufBuendel nicht aufrufen."""
    i = index_html.find("function _dispoTagesplanDruck(")
    assert i != -1, "Die Druckfunktion fehlt"
    j = index_html.find("const printLabels=", i)
    fn = index_html[i:j]
    for verboten in ("_dispoAblaufBuendel", "_dispoStrecke", "_dispoDauer", "_effDauer"):
        assert verboten not in fn, (
            "Die Druckfunktion ruft %s - sie soll NICHTS nachrechnen, sondern "
            "die fertigen Zeilen aus der Sammelmappe lesen." % verboten
        )


def test_der_knopf_reicht_die_sammelmappe_durch(index_html):
    block = _panel(index_html)
    assert '_tagesplan[m.id+"_"+t.key]||[]' in block, (
        "Der Knopf holt die Zeilen nicht aus der Sammelmappe."
    )
    assert 'filter(function(x){return x.zeilen.length;})' in block, (
        "Monteure ohne Zeilen werden nicht aussortiert - dann kommen leere "
        "Abschnitte aufs Blatt."
    )


# ══ Das Blatt sagt, was seine Zeichen bedeuten ══════════════════════════════

def test_das_blatt_erklaert_seine_zeichen(index_html):
    i = index_html.find("function _dispoTagesplanDruck(")
    fn = index_html[i:i + 6000]
    assert "nicht mit dem Kunden vereinbart" in fn, (
        "Das Blatt erklaert die Tilde nicht - eine gerechnete Uhrzeit saehe dann "
        "aus wie eine Zusage. In der Hand des Monteurs waere das schlimmer als "
        "gar keine Uhrzeit."
    )
    assert "geschaetzt, nicht vereinbart" in fn, (
        "Das Blatt erklaert die ca.-Markierung bei der Dauer nicht."
    )
    assert "fixer Kundentermin" in fn, (
        "Das Blatt erklaert die fix-Markierung nicht."
    )


def test_die_geschaetzte_dauer_ist_auch_auf_papier_markiert(index_html):
    i = index_html.find("function _dispoTagesplanDruck(")
    fn = index_html[i:i + 6000]
    assert 'r.geschaetzt?" ca.":""' in fn, (
        "Die geschaetzte Dauer ist auf dem Blatt nicht markiert - am Bildschirm "
        "steht seit v892 ein Naeherungszeichen, auf Papier waere die Zahl dann "
        "wieder eine scheinbare Zusage."
    )


def test_ein_blockiertes_popup_wird_gemeldet(index_html):
    i = index_html.find("function _dispoTagesplanDruck(")
    fn = index_html[i:i + 6000]
    assert "Druckfenster wurde blockiert" in fn, (
        "Ein blockiertes Popup scheitert still - der Nutzer drueckt dann "
        "mehrfach und nichts passiert."
    )
    assert "ist nichts eingeplant" in fn, (
        "Ein leerer Tag erzeugt ein leeres Blatt statt eines Hinweises."
    )


def test_das_blatt_ist_auf_a4_festgelegt(index_html):
    i = index_html.find("function _dispoTagesplanDruck(")
    fn = index_html[i:i + 6000]
    assert "@page{size:A4" in fn, (
        "Ohne @page richtet sich das Papierformat nach dem Treiber."
    )
    assert "thead{display:table-header-group}" in fn, (
        "Der Spaltenkopf wiederholt sich auf Folgeseiten nicht."
    )


# ══ Die Stolperstellen bleiben festgehalten ═════════════════════════════════

def test_die_sammelmappe_kollidiert_nicht_mit_den_bestandstests(index_html):
    """Zwei Bestandstests grenzen die Kachel-Darstellung ueber ein Textmuster
    ein. Die Sammelmappe steht davor - kaeme sie diesem Muster in die Quere,
    pruefen jene Tests still den falschen Block."""
    marke_a = "_fx.map(function(" + "f"
    marke_b = "chips.map(function(" + "c,ci)"
    assert index_html.count(marke_a) == 1, (
        "Das Erkennungsmuster der Kachel-Darstellung kommt %d mal vor - dann "
        "greifen test_dispo_chipparitaet_v742 und test_dispo_geplantezeit_v746 "
        "womoeglich den falschen Block ab." % index_html.count(marke_a)
    )
    assert index_html.count(marke_b) == 1, (
        "Die zweite Schnittmarke kommt %d mal vor." % index_html.count(marke_b)
    )


# ── GESTRICHEN v3.9.921: test_die_rohe_klammerbilanz_ist_unveraendert ───────
# Hier stand `assert index_html.count("(") - index_html.count(")") == -7`.
# Die eigene Docstring gab den Fehler schon zu ("Prosatext zaehlt also mit") -
# und zog daraus den falschen Schluss, naemlich die Zahl festzuschreiben,
# statt sie loszuwerden.
#
# WARUM ERSATZLOS WEG (damit es niemand wieder einbaut):
# Gemessen an v3.9.920 stehen 6.879 "(" und 6.998 ")" in den JS-Blockkommentaren
# (Saldo -119). Der Riegel hat also gemessen, wie jemand FLIESSTEXT formuliert,
# und war beim Erweitern regelmaessig im Weg - der Sollwert wurde deshalb schon
# von -5 auf -7 nachgezogen. Ein Sollwert, den man nachzieht, ist kein Riegel.
# Wer beim Bauen eine Zahl anpasst, findet damit nie einen Fehler.
#
# Das Echte misst NUR Code und liegt woanders:
#   scripts/_bracket_check.py -> tests/test_bracket_drift_guard.py  (() -1/{}0/[]0)
#   node --check je Skriptblock -> tests/test_integration_smoke.py
# Belegt statt behauptet: test_bracket_drift_guard.py hat seit v3.9.921 zwei
# Umkehrproben - fehlende Klammer im CODE macht den Riegel rot, ueberzaehlige
# Klammer im KOMMENTAR laesst ihn gruen. Die zweite Probe ist genau der Beweis,
# dass diese Zeile hier Prosa gemessen hat.
#
# Der Schwesterriegel in tests/test_invariants.py ist aus demselben Grund weg.


# ══ Umkehrprobe ═════════════════════════════════════════════════════════════

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    z1 = index_html.replace("var _tagesplan={};", "", 1)
    assert z1 != index_html, "Rueckbau 1 griff nicht"
    assert "var _tagesplan={};" not in _panel(z1), (
        "Umkehrprobe: der Sammelmappen-Riegel wuerde nicht anschlagen"
    )

    z2 = index_html.replace('r.geschaetzt?" ca.":""', '""', 1)
    assert z2 != index_html, "Rueckbau 2 griff nicht"
    assert 'r.geschaetzt?" ca.":""' not in z2, (
        "Umkehrprobe: der Schaetz-Riegel wuerde nicht anschlagen"
    )
