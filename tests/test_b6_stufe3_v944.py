# -*- coding: utf-8 -*-
"""v3.9.944 - B6 Stufe 3: die 9er, 10er und 11er, ansichtsweise.

WARUM NICHT ALLE AUF EINMAL
───────────────────────────
Im ganzen Dokument stehen rund 1150 Stellen auf 9, 10 oder 11 px. Mit den
vorhandenen Sonden messbar sind vier Ansichten von 31. Ein Griff, dessen
Wirkung man zu 87 Prozent nicht sieht, ist kein Bauschritt, sondern eine
Wette - also eine Ansicht nach der anderen, jede mit eigener Messung.

GEMESSEN (scripts/b3_vier_ansichten_messen.py, 375/390/1440 px, zwoelf Laeufe,
alle acht Koeder in jedem Lauf angeschlagen), Textstellen unter 12 px:

    Werkzeuge      390 px  55 -> 15   |  1440 px  25 -> 15
    Home           390 px  69 ->  2   |  1440 px 111 -> 26   | 375 px 69 -> 7
    Arbeitsscheine 390 px  43 -> 24   |  1440 px  43 -> 30   | 375 px 43 -> 29
    Planung                 unveraendert - siehe unten

Kein neuer Querroller, keine Tabelle ueber Schirmbreite, Tippziele unter 44 px
bei 375 und 390 px weiterhin 0, Mengengeruest der Arbeitsscheine unveraendert
(44 Knoepfe / 22 Felder / 4 Auswahlfelder - genau der Grundstand).

WEEKPLAN IST DRAUSSEN, UND DAS IST EIN MESSERGEBNIS
Mit gehobener Schrift rollte Planung bei 1440 px 7 px quer (1398 von 1405),
und der Beschnitt stieg dort von 1 auf 13 Stellen. Am Telefon waere es der
groesste Einzelgewinn der Stufe gewesen (49 auf 2 bei 390 px) - dreizehn
abgeschnittene Texte am Schreibtisch sind kein Preis dafuer. Die Tabelle
fuehrt feste Spaltenbreiten (width:130 sechsmal, minWidth:800 sechsmal); wer
sie hebt, muss dort zuerst Platz schaffen. Der Griff wurde zurueckgenommen,
nicht abgeschwaecht.

EIN EIGENER FEHLGRIFF, ZURUECKGENOMMEN
Mein erster Versuch grenzte die Komponenten ueber eine Klammerzaehlung ab und
lief davon: er meldete fuer HomeView einen "Rumpf" von 1 769 509 Zeichen und
hob 1744 Stellen quer durch die Datei. node_check wurde rot.
`git checkout -- index.html`, danach Abgrenzung an der NAECHSTEN
Funktionsdeklaration - mit einer Obergrenze, weil eine Komponente dieser App
88 bis 160 kB gross ist und alles darueber kein Rumpf mehr ist, sondern ein
Messfehler.

WAS DIESE DATEI NICHT KANN
Sie liest Quelltext. Ob eine Kachel dadurch umbricht, steht am Schirm, nicht
hier. Sie haelt fest, WELCHE Komponenten gehoben sind und welche absichtlich
nicht - damit ein spaeterer Rundumschlag auffaellt.
"""
import io
import re

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]

GEHOBEN = ["WerkzeugView", "HomeView", "ArbeitsscheinView"]
AUSGENOMMEN = ["WeekPlan"]

MUSTER = re.compile(r"fontSize:(?:isMob\?(?:9|10|11):\d+|(?:9|10|11)(?![\d.]))")


def _roh():
    return io.open(str(WURZEL / "index.html"), encoding="utf-8",
                   newline="").read()


def _bereiche(roh):
    """Komponenten an der naechsten Funktionsdeklaration abgrenzen.

    NICHT ueber eine Klammerzaehlung: die ist mir davongelaufen und hat fuer
    HomeView 1,77 MB gemeldet. Die Obergrenze unten ist der Riegel dagegen.
    """
    import sys
    sys.path.insert(0, str(WURZEL / "scripts"))
    from code_scan import ist_code, eichen
    ok, gefunden, erwartet = eichen(roh)
    assert ok, ("Eichung von code_scan gescheitert (%d von %d) - ohne sie "
                "sagt keine Zaehlung hier etwas." % (gefunden, erwartet))
    feld = ist_code(roh)
    decl = sorted((m.start(), m.group(1)) for m in
                  re.finditer(r"function\s+([A-Za-z_$][\w$]*)\s*\(", roh)
                  if feld[m.start()])
    assert len(decl) > 300, (
        "KOEDER STUMM: nur %d Funktionsdeklarationen im Code gefunden. Diese "
        "App hat ueber 400 - ohne die Grundgesamtheit sagt nichts hier etwas."
        % len(decl))
    idx = {n: k for k, (p, n) in enumerate(decl)}
    aus = {}
    for name in GEHOBEN + AUSGENOMMEN:
        assert name in idx, "Komponente %s nicht gefunden." % name
        k = idx[name]
        a = decl[k][0]
        b = decl[k + 1][0] if k + 1 < len(decl) else len(roh)
        assert 5_000 < b - a < 200_000, (
            "%s umfasst %d Zeichen - das ist kein Komponentenrumpf, sondern "
            "eine davongelaufene Abgrenzung. Genau daran ist mein erster "
            "Versuch gescheitert." % (name, b - a))
        aus[name] = (a, b, feld)
    return aus


def test_die_drei_gehobenen_ansichten_sind_frei_von_kleiner_schrift():
    roh = _roh()
    ber = _bereiche(roh)
    rest = {}
    for name in GEHOBEN:
        a, b, feld = ber[name]
        t = [m.start() for m in MUSTER.finditer(roh)
             if a <= m.start() < b and feld[m.start()]]
        if t:
            rest[name] = len(t)
    assert not rest, (
        "Diese gehobenen Ansichten tragen wieder Schrift unter 12 px: %r. "
        "UI.fMeta ist der Boden der App." % rest)


def test_weekplan_ist_ausgenommen_und_das_ist_gemessen():
    """KOEDER UND ENTSCHEIDUNG IN EINEM.

    Traegt WeekPlan keine kleinen Groessen mehr, ist eine von zwei Dingen
    passiert: jemand hat die Tabelle breiter gemacht und die Schrift danach
    gehoben (dann gehoert dieser Riegel weg, samt der Begruendung an der
    Token-Deklaration) - oder jemand hat den Rundumschlag doch gemacht, und
    dann rollt Planung bei 1440 px wieder 7 px quer mit 13 abgeschnittenen
    Texten. Das soll auffallen.

    Gleichzeitig ist dieser Riegel der Koeder fuer den darueber: findet er
    hier NICHTS, dann findet die Zaehlung ueberhaupt nichts, und die Null bei
    den drei gehobenen Ansichten waere keine Aussage.
    """
    roh = _roh()
    ber = _bereiche(roh)
    a, b, feld = ber["WeekPlan"]
    t = [m.start() for m in MUSTER.finditer(roh)
         if a <= m.start() < b and feld[m.start()]]
    assert t, (
        "WeekPlan traegt keine Schriftgroesse unter 12 px mehr. Entweder ist "
        "die Tabelle jetzt breit genug und die Ausnahme aufgehoben - dann "
        "gehoert dieser Riegel weg - oder es wurde ohne Messung gehoben, und "
        "Planung rollt bei 1440 px wieder quer (gemessen: 1398 von 1405, "
        "Beschnitt 1 -> 13).")


def test_die_begruendung_steht_an_der_deklaration():
    """218 Fundstellen brauchen nicht 218 Kommentare, aber EINEN. Ohne ihn
    sieht die Ausnahme fuer WeekPlan wie ein vergessener Fall aus."""
    roh = _roh()
    i = roh.find("const UI={")
    block = roh[i:i + 3600]
    assert "WEEKPLAN IST ABSICHTLICH DRAUSSEN" in block, (
        "Die Begruendung, warum WeekPlan ausgenommen ist, steht nicht mehr an "
        "der Token-Deklaration.")
    assert "1398 von 1405" in block, (
        "Die gemessene Zahl fehlt in der Begruendung - ohne sie ist es eine "
        "Meinung.")


def test_die_dezimalgroessen_sind_weiter_unberuehrt():
    """`fontSize:9.5` ist einem zu weiten Muster schon einmal zum Opfer
    gefallen (node_check: 'Unexpected number'). Hinter die Zahl gehoert
    `(?![\\d.])`."""
    roh = _roh()
    assert roh.count("fontSize:9.5") >= 2, (
        "fontSize:9.5 ist verschwunden - ein zu weites Muster hat die Zahl "
        "vermutlich zerschnitten.")
