# -*- coding: utf-8 -*-
"""v3.9.946 - Ausgetretene nur mit Beitrag, und die Befunde aus Stufe 12 bis 15.

AM SCHIRM GEMESSEN (scripts/b3_stufen_12_15_messen.py, 52 Laeufe, 16 Koeder)
───────────────────────────────────────────────────────────────────────────
Saat mit fuenf Monteuren: drei aktiv, M4 ausgetreten MIT Beitrag, M5
ausgetreten OHNE. K14 belegt in jedem Lauf, dass `_maIstEhemalig` genau M4
und M5 erkennt. Aus dem SVG gelesen (K16 - `innerText` ist blind fuer SVG,
und der erste Namensmelder hat deshalb gemeldet, ueberhaupt kein Name stehe
im Bild):

    Roswitha Puchleitner   ausgetreten OHNE Beitrag   vorher 0 / 0   -> WEG
    Ferdinand Aschenbrenner ausgetreten MIT Beitrag    2 / 1          -> BLEIBT
    Bernadette Wieshofer.. AKTIV mit 0                 2 / 0          -> BLEIBT

Eine Nullzeile ist keine leere Zeile: `Math.max(2, 0)` zeichnet einen Stummel
plus Beschriftung plus "0" in voller 18-px-Zeilenhoehe.

WAS DIESE DATEI NICHT KANN
Sie liest Quelltext. Ob im SVG wirklich ein Balken verschwindet, steht am
Schirm. Sie haelt die Ursachen fest, damit ein spaeteres "Aufraeumen"
auffaellt - und sie haelt fest, was NICHT angefasst werden durfte.
"""
import io
import re

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]


def _roh():
    return io.open(str(WURZEL / "index.html"), encoding="utf-8",
                   newline="").read()


# ── Ausgetretene nur mit Beitrag ──────────────────────────────────────────

def test_beide_diagramme_filtern_an_der_quelle():
    """Gefiltert wird in `asMont` und `absPerName`, NICHT in der
    charts-Aufzaehlung.

    Der Unterschied ist nicht kosmetisch: der Excel-Export liest dieselbe
    charts-Liste. Wer dort filtert, filtert nur das Gezeichnete und muss den
    Export nachtragen; wer an der Quelle filtert, hat beide Wege automatisch
    gleich.
    """
    roh = _roh()
    assert roh.count("_maIstEhemalig(o.m)") == 2, (
        "Erwartet zwei Filterstellen an der Quelle (Scheine pro Monteur und "
        "Abwesenheit pro Person), gefunden %d."
        % roh.count("_maIstEhemalig(o.m)"))
    for name, marke in (("asMont", "const asMont=_react.useMemo.call"),
                        ("absPerName", "const absPerName=_react.useMemo.call")):
        i = roh.find(marke)
        assert i > 0, "KOEDER STUMM: %s nicht gefunden." % name
        block = roh[i:i + 1200]
        assert ".filter(o=>!_maIstEhemalig(o.m)||o.d.v>0)" in block, (
            "%s filtert nicht mehr an der Quelle. Dann zeigt das Diagramm "
            "wieder eine Nullzeile fuer jemanden, der nicht mehr da ist - und "
            "der Excel-Export ebenso." % name)


def test_der_aktive_mit_null_und_der_ehemalige_mit_beitrag_bleiben():
    """Die Bedingung ist `!ehemalig ODER v>0` - nicht `v>0`.

    Ein AKTIVER mit 0 muss stehenbleiben ("diese Woche nichts" ist eine
    Aussage ueber jemanden, der da ist), und ein AUSGETRETENER MIT Beitrag
    ebenso (Historie verliert niemanden). Ein Filter, der nur `v>0` prueft,
    wuerde beide Faelle falsch machen und dabei gruen aussehen.
    """
    roh = _roh()
    falsch = re.findall(r"\.filter\(o=>o\.d\.v>0\)", roh)
    assert not falsch, (
        "Es wird nur auf einen Beitrag geprueft, ohne die Ehemalig-Frage. "
        "Damit verschwindet auch ein AKTIVER mit 0.")
    assert roh.count("!_maIstEhemalig(o.m)||o.d.v>0") == 2, (
        "Die Bedingung ist nicht mehr 'nicht ehemalig ODER Beitrag'.")


def test_keine_zweite_datumslogik_und_keine_auswahlliste():
    """`_maIstEhemalig` wird BENUTZT, nicht nachgebaut - und es bleibt
    bytegleich (das haelt scripts/md5_geschuetzt.py fest).

    Der KOEDER ist die Funktion selbst: findet dieser Riegel sie nicht, sagt
    er ueber die beiden Punkte darunter nichts.
    """
    roh = _roh()
    i = roh.find("function _maIstEhemalig(m,heute){")
    assert i > 0, "KOEDER STUMM: _maIstEhemalig nicht gefunden."
    rumpf = roh[i:i + 200]
    assert "String(m.austritt).slice(0,10)<h" in rumpf, (
        "Der Rumpf von _maIstEhemalig hat sich geaendert - er ist eine der "
        "sieben byte-identisch zu haltenden Funktionen.")
    # In den beiden Diagramm-Quellen darf keine eigene Austrittsrechnung stehen.
    for marke in ("const asMont=_react.useMemo.call",
                  "const absPerName=_react.useMemo.call"):
        block = roh[roh.find(marke):roh.find(marke) + 1200]
        assert "austritt" not in block, (
            "In %s steht eine eigene Austrittsrechnung. Zwei Datumslogiken "
            "widersprechen sich frueher oder spaeter - genau das ist im "
            "ChefDashboard schon der Fall (dort `!String(m.austritt||'')"
            ".trim()` statt `austritt < heute`)." % marke)


# ── D1: der Rueckschlag aus v3.9.943 ──────────────────────────────────────

def test_der_reitername_in_der_fussleiste_steht_wenigstens_im_title():
    """v3.9.943 hat diese Beschriftung von 10 auf 12 px gehoben. Dort wurde
    die HOEHE der Leiste gemessen (58 px, unveraendert) - die BREITE nicht.

    Gemessen (scripts/b3_fussleiste_beschnitt.py): der Schlitz ist 74 px, und
    bei 12 px sind FUENF Namen gekuerzt statt einem.
        Monatsabrechnung 112 px (-37,5) | Abwesenheiten 89 (-15,3)
        Bauprovisorien    88 px (-13,7) | Gefahrenstoffe 86 (-11,9)
        Zeiterfassung     80 px ( -5,6)
    12 px koennen diese Woerter in 74 px nicht tragen; das ist Arithmetik,
    keine Einstellung. Der title kostet kein Pixel und macht den ganzen Namen
    wenigstens erreichbar - er LOEST es am Telefon nur halb. Der richtige Weg
    waere ein Kurzname je Reiter, und der erfindet Woerter.
    """
    roh = _roh()
    i = roh.find("isActive&&gr.g<4&&tabs[safeKat]?tabs[safeKat].l:gr.l")
    assert i > 0, "KOEDER STUMM: der Ausdruck der Fussleisten-Beschriftung fehlt."
    block = roh[max(0, i - 1800):i + 120]
    assert "title: (isActive&&gr.g<4&&tabs[safeKat]?tabs[safeKat].l:gr.l)" in block, (
        "Der volle Reitername steht nicht mehr im title. Dann ist er bei "
        "390 px gar nicht mehr zu erfahren - der Schlitz ist 74 px und der "
        "Name bis zu 112 px breit.")


def test_die_leistenhoehe_haengt_weiter_am_token():
    roh = _roh()
    assert "--epk-bar-h:58px" in roh and "min-height:var(--epk-bar-h,58px)" in roh, (
        "Die Leiste bezieht ihre Hoehe nicht mehr aus --epk-bar-h. Die "
        "Endreserve des Inhalts haengt seit v3.9.932 daran.")


# ── D2/D3/D4: Bedeutung statt Symbol ──────────────────────────────────────

def test_die_abwesenheits_unterreiter_tragen_ihre_beschriftung():
    """Bei 390 px vier Ikonen ohne ein Wort - derselbe Fall wie die
    Plan-Unterreiter und die Werkzeug-Reiter."""
    roh = _roh()
    i = roh.find('setSubView(t.id), style: {padding:isMob?"8px 10px":"10px 18px"')
    assert i > 0, "KOEDER STUMM: die Abwesenheits-Unterreiter wurden nicht gefunden."
    block = roh[max(0, i - 400):i]
    assert "title: t.l" in block and "'aria-label': t.l" in block, (
        "Den vier Abwesenheits-Unterreitern fehlt title/aria-label.")


def test_alle_pfeilknoepfe_tragen_eine_beschriftung():
    """DATEIWEIT gesucht, nicht je Ansicht.

    Dieses Muster ist in diesem Umbau dreimal aufgetaucht (Planung v3.9.942,
    Wochenbericht v3.9.945, Stufe 12-15). Die Ansichtsmessung meldete sechs
    solche Knoepfe, die Dateisuche fand ACHT. Wer je Ansicht sucht, findet
    immer nur die, in die er gerade sieht.

    Der KOEDER ist die Grundgesamtheit: findet dieser Riegel keine Pfeile
    mehr, ist seine Null kein Ergebnis.
    """
    roh = _roh()
    ohne = []
    gefunden = 0
    for zeichen in ("◀", "▶"):
        for m in re.finditer(re.escape('"' + zeichen + '"'), roh):
            b = roh.rfind("React.createElement('button'", max(0, m.start() - 900),
                          m.start())
            if b < 0:
                continue
            gefunden += 1
            umfeld = roh[b:m.start()]
            if "title:" not in umfeld and "aria-label" not in umfeld:
                ohne.append(roh.count("\n", 0, m.start()) + 1)
    assert gefunden >= 8, (
        "KOEDER STUMM: nur %d Pfeilknoepfe im Dokument gefunden, erwartet "
        "mindestens 8. Ohne die Grundgesamtheit sagt die Null darunter nichts."
        % gefunden)
    assert not ohne, (
        "Diese Pfeilknoepfe tragen weder title noch aria-label (Zeilen %s). "
        "Ein Pfeil allein sagt nicht, wohin." % ohne)
