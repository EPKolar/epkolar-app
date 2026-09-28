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

# 🔴 v3.9.967: WeekPlan ist von AUSGENOMMEN nach GEHOBEN gewandert, und das
# ist gemessen, nicht beschlossen. Die Ausnahme stand hier, weil v3.9.943 den
# Rundumschlag abgelehnt hatte: "bei 1440 px rollte Planung 7 px quer (1398 von
# 1405) und der Beschnitt stieg dort von 1 auf 13 Stellen".
# Am 27.09.2026 wurde beides nachgemessen. Nach dem Heben rollte Planung
# tatsaechlich wieder 7 px quer - das ueberstehende Element war namentlich
# bestimmt (der Loeschknopf der Zeile, rechte Kante bei 1405). Es wurden 8 px
# Polsterung zurueckgenommen (td 2->1 px, drei nicht zerstoerende Knoepfe
# 0 1px -> 0; der Loeschknopf behielt seine). Danach: Querlauf 0, Beschnitt 0,
# Elemente unter 12 px von 44 auf 2 bei 390 px und von 42 auf 9 bei 1440 px.
# Der damalige Preis faellt damit weg - der Beschnitt ist NULL, nicht 13, weil
# die Monteursnamen jetzt umbrechen statt gekuerzt zu werden.
GEHOBEN = ["WerkzeugView", "HomeView", "ArbeitsscheinView", "WeekPlan"]
AUSGENOMMEN = []

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


def test_der_zaehler_findet_ueberhaupt_etwas():
    """🔴 DER KOEDER, DER VORHER DIE DATEI WAR.

    Bis v3.9.966 war die Ausnahme WeekPlan selbst der Koeder fuer die Zaehlung
    darueber: fand sie dort nichts, fand sie nirgends etwas, und die Null bei
    den gehobenen Ansichten waere keine Aussage gewesen.

    Seit v3.9.967 ist WeekPlan gehoben, und damit ist dieser Zeuge weg. Er wird
    NICHT ersatzlos gestrichen - der Beleg steht jetzt an einem selbstgebauten
    Text, und das ist die stabilere Form: der Koeder haengt nicht mehr davon
    ab, dass irgendeine Ansicht einen Mangel behaelt. Ein Riegel, dessen
    Nachweis vom Fortbestehen des Mangels lebt, wird bei der naechsten Kur
    entweder rot oder blind.

    Alle drei Formen, die MUSTER kennt, werden geprueft - eine Form, die es
    nicht kann, meldet 'kommt nicht vor', und das ist von einem echten Befund
    nicht zu unterscheiden.
    """
    for fall, wie in (("fontSize:9,", "Ganzzahl 9"),
                      ("fontSize:10}", "Ganzzahl 10"),
                      ("fontSize:11 ", "Ganzzahl 11"),
                      ("fontSize:isMob?9:14", "mobil-abhaengig")):
        assert MUSTER.findall(fall), (
            "Die Form %r (%s) wird von MUSTER nicht erkannt - dann ist jede "
            "Null dieses\n  Riegels geschenkt." % (fall, wie))
    # Gegenprobe: was NICHT gemeldet werden darf.
    for fall, warum in ((" fontSize:12,", "12 ist der Boden, kein Befund"),
                        ("fontSize:9.5,", "Kommazahl - das Muster endet auf "
                                          "Ganzzahl und darf sie nicht "
                                          "anfassen"),
                        ("fontSize:UI.fMeta,", "Token")):
        assert not MUSTER.findall(fall), (
            "%r wurde gemeldet (%s) - ein Riegel, der alles meldet, misst so "
            "wenig wie einer,\n  der schweigt." % (fall, warum))


def test_die_ausnahme_ist_aufgehoben_und_das_ist_GEMESSEN():
    """Die Entscheidung, die vorher als Ausnahme hier stand.

    v3.9.943 hatte den Rundumschlag in der Wochenplanung abgelehnt, mit einer
    Messung: "bei 1440 px rollte Planung 7 px quer (1398 von 1405) und der
    Beschnitt stieg dort von 1 auf 13 Stellen". Diese Begruendung war richtig
    und hat drei Wochen gehalten.

    Am 27.09.2026 wurde sie nachgemessen statt uebergangen. Nach dem Heben
    rollte Planung tatsaechlich wieder 7 px quer. Das ueberstehende Element
    wurde NAMENTLICH bestimmt - der Loeschknopf der Zeile, rechte Kante bei
    1405 - und es wurden 8 px Polsterung zurueckgenommen. Danach:
    Querlauf 0, Beschnitt 0, Elemente unter 12 px von 44 auf 2 (390 px) und von
    42 auf 9 (1440 px). Der Beschnitt ist NULL statt 13, weil die
    Monteursnamen jetzt umbrechen statt gekuerzt zu werden.

    Diese Probe haelt fest, dass der Platz auch WIRKLICH geschaffen wurde -
    ohne ihn kehrt der Querlauf zurueck, und dann war die Aufhebung der
    Ausnahme falsch.

    🔴 28.09.2026 - DER ZEUGE IST GETAUSCHT, DIE ABSICHT NICHT.
    Bis heute prueften die Behauptungen unten die 1-px-Polsterung des td und
    die Polsterung der einzelnen Knoepfe. Das war der MECHANISMUS, mit dem
    v3.9.967 die 8 px zurueckgewonnen hat - nicht die Absicht. v3.9.976 hat
    den Mechanismus ersetzt, weil dieselben vier Knoepfe zu KLEIN waren:
    10.3x14, 10.3x14, 8.4x14 und 13.8x14 bei 1440 px, gemessen ueber alle 44
    Aufnahmen; die kleinsten Bedienelemente des ganzen Bestands. Vier Knoepfe
    zu je 24 px NEBENEINANDER waeren 96 statt 43 px gewesen - ein sicherer
    Ueberlauf, und genau der Grund, aus dem v3.9.943 diese Ansicht ausnahm.
    Sie stehen jetzt als 2x2-Raster mit 2 px Abstand (50x50) in einer Spalte
    von 54 px; die Polsterung des td ist 0.

    Der Platz ist also anders geschaffen, aber er IST geschaffen - und das ist
    nachgemessen, nicht gerechnet:

        python scripts/echtmengen_messen.py --nur planung
        planung 1440 px: verl=0 roll=0
        Zwischenstand mit 50-px-Spalte: roll=1, Ueberschuss 5 px
        (scrollWidth 1403 gegen clientWidth 1398) - deshalb 54.

    Ein Riegel, der nach dem Ersetzen des Mechanismus auf dem alten Zeugen
    bestuende, wuerde die richtige Loesung fuer falsch erklaeren. Das ist mir
    am 25./26.09. zweimal passiert; deshalb steht der neue Zeuge hier MIT der
    Messung, die ihn traegt.
    """
    roh = _roh()
    ber = _bereiche(roh)
    a, b, feld = ber["WeekPlan"]
    seg = roh[a:b]
    # 🔴 `gap:2` ist hier NICHT weglassbar. v3.9.967 gab dem Loeschknopf als
    #    einzigem der vier eine Polsterung, mit Begruendung: ein zerstoerender
    #    Knopf, der die Nachbarn beruehrt, wird verklickt. Im lueckenlosen
    #    Raster stand er wieder Kante an Kante an 🗑 und ▼ - der Abstand ist
    #    vom Knopf ins Raster umgezogen, nicht verschwunden.
    assert 'gridTemplateColumns:"24px 24px",gap:2,width:50' in seg, (
        "Das 2x2-Raster der Zeilenknoepfe ist weg oder hat seinen Abstand "
        "verloren.\n  Ohne Raster stehen die vier wieder nebeneinander und "
        "sind entweder unter 24 px\n  breit oder die Tabelle rollt quer - "
        "beides ist gemessen, keines ist hinnehmbar.\n  Ohne `gap:2` beruehrt "
        "der Loeschknopf seine Nachbarn.")
    assert seg.count('width:24,height:24') >= 4, (
        "Weniger als vier Zeilenknoepfe stehen auf 24x24. Genau diese vier "
        "waren bei\n  1440 px 10.3x14, 10.3x14, 8.4x14 und 13.8x14.")
    assert "React.createElement('col', { style: {width:54}}))" in seg, (
        "Die Knopfspalte steht nicht mehr auf 54 px. Mit 50 px rollte die "
        "Tabelle bei\n  1440 px um 5 px quer (scrollWidth 1403 gegen "
        "clientWidth 1398, gemessen).")


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
