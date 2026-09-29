# -*- coding: utf-8 -*-
"""Der beschriftete Darstellungs-Schalter steht im MOBILEN Mehr-Menue.

🔴 WARUM ES DIESEN WEG GIBT, OBWOHL DER KOPFKNOPF MESSBAR WIRKT.
Sebastian hat denselben Mangel DREIMAL gemeldet - v3.9.721 war die erste Kur,
v3.9.979 die zweite. Dazwischen und danach haben sechs Messungen belegt, dass
der Kopfknopf umschaltet:

    hellmodus_ansichten.py          32 Ansichten, Wahl vor dem Laden
    hellmodus_schalter_messen.py    ein Tipp zur Laufzeit
    hellmodus_nach_dem_schalten.py  alle Ansichten nach dem Umschalten
    thema_schalter_ring_messen.py   sechs Tippen, jeder wechselt
    thema_echter_tipp_messen.py     ECHTE Fingertippen, genau ein click
    thema_iphone_messen.py          dasselbe in WebKit, iPhone-Profil

Wenn Messung und Nutzer dreimal auseinanderliegen, ist nicht der Nutzer das
Problem. Der Kopfknopf ist ein 44x44 grosses Sinnbild ohne Beschriftung; was
er tut, steht im `title`, und den sieht man am Telefon nie. Er verlangt, dass
man sich merkt, in welchem Zustand man ist.

Dazu ein gemessener Nebeneffekt: nach dem Umschalten erscheint oben eine
klebende Leiste ("Aenderungen warten auf Sync") und schiebt den Kopfbereich
um 56 px nach unten (header.top 0 -> 56). Wer zweimal auf dieselbe Stelle
tippt, trifft beim zweiten Mal daneben - genau das ist meinem eigenen Melder
passiert, er meldete daraufhin drei wirkungslose Tippen.

DIE KUR IST KEIN BESSERER RING, SONDERN EIN WEG OHNE RING: drei beschriftete
Knoepfe, der aktive hervorgehoben, je >=44 px. Man tippt, was man haben will.

Gemessen in BEIDEN Engines mit echten Tippen
(`scripts/thema_mehrmenue_messen.py`): "Hell" macht hell, "Dunkel" macht
dunkel, beim ERSTEN Tipp - in Chromium und in WebKit.

🔴 WAS DIESER RIEGEL MISST: den Quelltext. Ob die Knoepfe am Schirm
erscheinen und wirken, misst das Skript oben.
"""
import io
import os

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")

DREI = ('[["light","☀️ Hell"],["dark","🌙 Dunkel"],'
        '["system","🅰️ Auto"]]')


def _text():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def test_der_schalter_steht_zweimal_da():
    """Einmal in den Einstellungen (seit v3.9.721), einmal im Mehr-Menue.

    Zwei Vorkommen sind hier kein Versehen, sondern der Punkt: der eine Ort
    ist vollstaendig, der andere erreichbar.
    """
    t = _text()
    n = t.count(DREI)
    assert n == 2, (
        "Der Darstellungs-Schalter steht %d mal statt zweimal im Code.\n"
        "  Erwartet: einmal in den Einstellungen (v3.9.721) und einmal im\n"
        "  mobilen Mehr-Menue (v3.9.981). Fehlt der zweite, muss ein\n"
        "  Telefonnutzer wieder den unbeschrifteten Kopfknopf erraten - und\n"
        "  genau das ist dreimal gemeldet worden." % n)


def test_er_haengt_nicht_an_der_zahl_der_reiter():
    """🔴 Die Bedingung `moreTabs.length>0` musste weg.

    Sonst erscheint der Darstellungs-Schalter nur, wenn es ueberhaupt
    zusaetzliche Reiter gibt - eine Rolle mit wenigen Reitern saehe ihn nie.
    """
    t = _text()
    assert "moreOpen&&isMob&&moreTabs.length>0&&" not in t, (
        "Das mobile Mehr-Menue haengt wieder an `moreTabs.length>0`.\n"
        "  Damit verschwindet der Darstellungs-Schalter fuer jede Rolle ohne\n"
        "  zusaetzliche Reiter.")
    assert "moreOpen&&isMob&&React.createElement" in t, (
        "Das mobile Mehr-Menue rendert nicht mehr unbedingt.")


def test_die_knoepfe_sind_gross_genug_und_melden_ihren_zustand():
    t = _text()
    i = t.index(DREI)
    block = t[i:i + 900]
    assert "minHeight:44" in block, (
        "Die Darstellungs-Knoepfe im Mehr-Menue sind unter 44 px hoch.")
    assert "'aria-pressed': _akt" in block, (
        "Die Knoepfe melden ihren Zustand nicht mehr ueber `aria-pressed`.\n"
        "  Ohne das sagt eine Vorlesehilfe nicht, welche Darstellung aktiv "
        "ist -\n  und genau das Nichtwissen war der gemeldete Mangel.")


def test_der_kopfknopf_bleibt_als_schneller_weg():
    """Der neue Weg ERSETZT den alten nicht - er ergaenzt ihn."""
    t = _text()
    assert 'setThemeMode(isDark?"light":"dark");' in t, (
        "Der Kopfknopf ist verschwunden. Er ist der schnelle Weg; das "
        "Mehr-Menue\n  ist der eindeutige. Beide gehoeren dazu.")
