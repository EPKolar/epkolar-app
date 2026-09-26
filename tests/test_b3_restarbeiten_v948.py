# -*- coding: utf-8 -*-
"""v3.9.948 - Restarbeiten aus Stufe 8 bis 15: E2, D5, C5. Und D6 als Nicht-Befund.

AM SCHIRM GEMESSEN
──────────────────
E2  scripts/abs_pille_messen.py, 390 und 1440 px, mit der Saat aus
    b3_stufen_12_15_messen (fuenf Monteure, zwei davon ausgetreten):
        Gerhard Steinbichler    193h Rest - 0K   Anspruch: JA   (aktiv)
        Ferdinand Aschenbrenner ausgetreten - 0K Anspruch: NEIN (ausgetreten)
        Roswitha Puchleitner    ausgetreten - 0K Anspruch: NEIN (ausgetreten)
    Der NAME bleibt in beiden Faellen - das verlangt v3.9.931 ausdruecklich.
    Der Krankenstand bleibt auch: er ist Historie und keine Zusage.

D5  b3_stufen_12_15_messen --nur admin: "quer, TATSAECHLICH: kein waagrechter
    Roller ueberhaupt" (vorher 374 gegen 562, drei der sechs Unterreiter
    waren nicht im Bild). Das war der EINZIGE tatsaechliche Querroller in
    26 Laeufen.

D6  ist KEIN Befund, und das ist jetzt belegt statt vermutet. Das eine
    Bedienelement unter 44 px bei 390 px in Flotte ist der
    LEAFLET-ZUSCHREIBUNGSLINK: `a`, 51,4 x 14 px, title "A JavaScript library
    for interactive maps", Weg
    `div.leaflet-container > ... > div.leaflet-control-attribution > a`.
    Eine rechtlich noetige Kartenzuschreibung ist kein Bedienelement der App;
    sie auf 44 px zu vergroessern wuerde die Karte verdecken. Es wird nichts
    geaendert - und es wird auch nicht der Melder umgebaut, damit die Zahl
    schoener aussieht. Die Zahl bleibt 1, und hier steht, warum.
"""
import io
import re

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]


def _roh():
    return io.open(str(WURZEL / "index.html"), encoding="utf-8",
                   newline="").read()


# ── E2: kein Anspruch fuer Ausgetretene, aber der Name bleibt ─────────────

def test_die_pille_zeigt_einem_ausgetretenen_keinen_anspruch():
    roh = _roh()
    i = roh.find("(isAdmin?names:names.filter(m=>m===myMonteurName)).map")
    assert i > 0, "KOEDER STUMM: die Pillenreihe der Abwesenheiten fehlt."
    block = roh[i:i + 2600]
    assert "_maIstEhemalig(_maObj)" in block, (
        "Die Pille fragt nicht mehr, ob der Mensch ausgetreten ist - dann "
        "steht unter einem Ausgetretenen wieder ein Resturlaub. v3.9.931: "
        "'Ein Anspruch fuer jemanden, der nicht mehr da ist, ist keine "
        "Historie.'")
    assert '"ausgetreten · "' in block, (
        "Der neutrale Text fehlt. Ohne ihn waere die Zeile leer statt "
        "erklaerend.")
    assert "ys.krankenstand" in block, (
        "Der Krankenstand ist aus der Pille verschwunden. Der ist Historie "
        "und muss bleiben - auch bei einem Ausgetretenen.")


def test_der_name_bleibt_in_der_auswahl():
    """Die Pille ist die AUSWAHL, ueber die man Kalender und Krankenstaende
    einer Person ansieht. v3.9.931 verbietet ausdruecklich, dort jemanden
    wegzulassen - wer die alten Krankenstaende eines Ausgetretenen sucht,
    muss ihn hier finden.

    Der Riegel prueft, dass NICHT gefiltert wird: taucht in dieser Zeile ein
    Filter auf Ehemalige auf, ist die Auswahl kaputt.
    """
    roh = _roh()
    i = roh.find("(isAdmin?names:names.filter(m=>m===myMonteurName)).map")
    kopf = roh[i:i + 200]
    assert "_maIstEhemalig" not in kopf, (
        "Die Pillenreihe filtert Ausgetretene aus der AUSWAHL - genau das "
        "verbietet v3.9.931. Gefiltert werden darf nur der ANSPRUCH, nicht "
        "der Name.")


# ── D5 / C5: umbrechen statt rollen ───────────────────────────────────────

def test_die_admin_unterreiter_brechen_um_statt_zu_rollen():
    """Ein quer rollbarer Kasten VERBRAUCHT die waagrechte Wischgeste selbst,
    und die Wischgeste ist in dieser App der Reiterwechsel - eine tote Zone
    mitten im Bedienweg. Derselbe Griff wie in v3.9.930."""
    roh = _roh()
    assert ('display:"flex",gap:4,marginBottom:14,overflowX:"auto",'
            'paddingBottom:4}}') not in roh, (
        "Die Admin-Unterreiter rollen wieder quer. Gemessen waren 562 gegen "
        "374 px bei 390 px - drei der sechs Reiter nicht im Bild.")
    assert ('display:"flex",gap:4,marginBottom:14,flexWrap:"wrap",'
            'paddingBottom:4}}') in roh, (
        "Die Admin-Unterreiter brechen nicht mehr um.")


def test_die_material_reiter_brechen_um_statt_zu_rollen():
    roh = _roh()
    assert ('marginBottom:14,borderBottom:"2px solid "+V.bd,'
            'overflowX:"auto"} }') not in roh, (
        "Die Material-Reiter rollen wieder quer. Gemessen 467 gegen 354 px - "
        "die Zeile endete mitten in 'Bestellung...', 'Katalog' war gar nicht "
        "im Bild.")
    assert ('marginBottom:14,borderBottom:"2px solid "+V.bd,'
            'flexWrap:"wrap"} }') in roh, (
        "Die Material-Reiter brechen nicht mehr um.")


def test_die_projekt_reiterzeile_bleibt_absichtlich_rollbar():
    """KEIN Versehen, sondern ein Handel.

    Die Projekt-Reiterzeile rollt bei 390 px ebenfalls quer (421 gegen 390).
    Dort sind es aber DREIZEHN Reiter - ein Umbruch kostet drei Zeilen auf
    JEDER Projektseite, rund 120 px. Bei sechs bzw. fuenf Reitern (Admin,
    Material) kostet er eine Zeile. Deshalb bleibt diese eine rollbar, und
    deshalb steht es hier: damit es niemand fuer einen vergessenen Fall haelt.

    Faellt dieser Riegel, weil jemand auch sie umgebrochen hat, ist das kein
    Fehler - dann gehoert der Riegel weg und die Entscheidung dokumentiert.
    """
    roh = _roh()
    i = roh.find('_pfHaupt.map(n=>React.createElement')
    assert i > 0, "KOEDER STUMM: die Projekt-Reiterzeile wurde nicht gefunden."
    block = roh[max(0, i - 700):i]
    assert 'overflowX:"auto"' in block, (
        "Die Projekt-Reiterzeile rollt nicht mehr quer. Wenn das Absicht ist: "
        "diesen Riegel entfernen und die Entscheidung in LAUF_UI.md "
        "festhalten - 13 Reiter umgebrochen sind rund 120 px auf jeder "
        "Projektseite.")


# ── D6: ein Nicht-Befund, benannt statt weggezaehlt ───────────────────────

def test_d6_wird_nicht_durch_umbau_des_melders_erledigt():
    """Das eine Element unter 44 px in Flotte ist der Leaflet-Zuschreibungs-
    link - keine Bedienung der App, und rechtlich noetig.

    Die Versuchung waere, den Melder um `.leaflet-control-attribution` zu
    erleichtern. Das waere Blindheit auf Bestellung: derselbe Melder faende
    dann auch eine echte zu kleine Schaltflaeche dort nicht mehr. Die Zahl
    bleibt 1, die Begruendung steht im Riegel und im Grundstand.

    Geprueft wird deshalb nur, dass niemand die Hausregel fuer Tippziele
    aufgeweicht hat.
    """
    roh = _roh()
    m = re.search(r"@media \(pointer: coarse\), \(max-width: 768px\)", roh)
    assert m, "KOEDER STUMM: die 44-px-Hausregel wurde nicht gefunden."
    block = roh[m.start():m.start() + 900]
    assert "min-height:44px" in block.replace(" ", "").replace(
        "min-height:44px", "min-height:44px"), (
        "Die 44-px-Hausregel nennt keine 44 px mehr.")
