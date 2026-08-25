# -*- coding: utf-8 -*-
"""
v3.9.873 - Wer scrollt, entscheidet, wem die Geste gehoert.

DER SATZ, DER ES AUFLOESTE (vom Nutzer):
"im projekt kann ich wischen, rest ned"

Beide Ansichten nutzen denselben Hook - es lag also an der FLAECHE, nicht an der
Logik. Der Unterschied, gemessen:

    Projektansicht   der CONTAINER scrollt (flex:1 + overflow-y:auto in einer
                     100dvh-Spalte)                              -> Wischen ging
    Bottom-Nav       position:fixed, scrollt gar nichts          -> Wischen ging
    Hauptbereich     die SEITE scrollt (interne Scroller: keine,
                     Seite 2880px)                               -> Wischen tot

Scrollt die Seite, arbitriert Chrome die Geste auf oberster Ebene und nimmt sie
sich, bevor ein preventDefault etwas ausrichten kann. Scrollt ein Container,
bleibt die Geste beim Element.

Damit passt zum ersten Mal ALLES zusammen, was ueber Tage gemeldet wurde:
im Projekt ging es, auf der Leiste ging es, quer ging es (kuerzere Flaeche,
weniger Seiten-Scroll) - und im Hauptbereich im Hochformat nie.

FIX: Der Hauptbereich bekommt exakt den Aufbau der Projektansicht. Nur bis
1199px, also auf Touch-Geraeten; Desktop bleibt unveraendert.

Das ersetzt die v867-min-height: mit einem bounded Container ist sie nicht nur
ueberfluessig, sondern schaedlich - sie wuerde den Inhalt ueber die Box hinaus
zwingen.
"""
import re


def _regel(index_html):
    m = re.search(r"@media\(max-width:1199px\)\{\s*\.app-shell\{([^}]*)\}\s*"
                  r"\.app-col\{([^}]*)\}\s*\.main-pad\{([^}]*)\}\s*\}", index_html, re.S)
    assert m, (
        "Der Scroll-Container-Aufbau fuer Touch-Geraete ist weg. Dann scrollt "
        "wieder die Seite - und Chrome nimmt die Wisch-Geste."
    )
    return {"shell": m.group(1), "col": m.group(2), "pad": m.group(3)}


def test_huelle_ist_eine_bildschirmhohe_spalte(index_html):
    r = _regel(index_html)
    assert "height:100dvh" in r["shell"], (
        "Die Huelle hat keine feste Bildschirmhoehe - ohne die kann kein Kind "
        "den Rest ausfuellen:\n" + r["shell"]
    )
    assert "overflow:hidden" in r["shell"], (
        "Ohne overflow:hidden scrollt die Seite weiter mit:\n" + r["shell"]
    )
    assert "display:flex" in r["shell"] and "flex-direction:column" in r["shell"], (
        "Die Huelle ist keine Spalte:\n" + r["shell"]
    )


def test_inhalt_scrollt_selbst(index_html):
    """Das ist der Kern: nicht die Seite, sondern der Inhaltsbereich scrollt."""
    r = _regel(index_html)
    assert "overflow-y:auto" in r["pad"], (
        "Der Inhaltsbereich scrollt nicht selbst - genau dann nimmt Chrome die "
        "Geste wieder auf oberster Ebene:\n" + r["pad"]
    )
    assert "flex:1" in r["pad"], "Der Inhalt fuellt den Rest nicht aus:\n" + r["pad"]
    assert "min-height:0" in r["pad"], (
        "Ohne min-height:0 waechst ein Flex-Kind ueber seine Box hinaus und "
        "scrollt dann doch die Seite:\n" + r["pad"]
    )


def test_zwischenspalte_reicht_die_hoehe_durch(index_html):
    r = _regel(index_html)
    assert "flex:1" in r["col"] and "min-height:0" in r["col"], (
        "Die App-Spalte reicht die Hoehe nicht durch:\n" + r["col"]
    )
    assert "display:flex" in r["col"] and "flex-direction:column" in r["col"], (
        "Die App-Spalte ist keine Spalte - dann kann .main-pad kein flex:1 sein:\n" + r["col"]
    )


def test_klassen_sind_im_markup_vergeben(index_html):
    assert 'React.createElement(\'div\', { className: "app-shell"' in index_html, (
        "Die Huelle traegt die Klasse app-shell nicht - das CSS greift dann ins Leere."
    )
    assert 'React.createElement(\'div\', { className: "app-col"}' in index_html, (
        "Die App-Spalte traegt die Klasse app-col nicht."
    )


def test_alte_min_height_regel_ist_ersetzt(index_html):
    """v867 loeste ein echtes Problem (inhaltsarme Seiten waren unten tot), aber
    mit einem bounded Container ist die Regel schaedlich."""
    assert "@media(max-width:1199px){.main-pad{min-height:calc(100dvh - 96px)}}" not in index_html, (
        "Die v867-min-height steht wieder da. Zusammen mit flex:1 zwingt sie den "
        "Inhalt ueber seine Box hinaus."
    )


def test_desktop_bleibt_unveraendert(index_html):
    """Der Umbau gilt nur fuer Touch-Breiten. Auf dem Desktop wird mit der Maus
    navigiert, dort waere das Risiko ohne Nutzen."""
    r = _regel(index_html)
    assert r, "Regel fehlt"
    # Basisregel unangetastet
    assert ".main-pad{padding:20px;touch-action:pan-y}" in index_html, (
        "Die Basis-Regel wurde veraendert - touch-action:pan-y ist Voraussetzung "
        "dafuer, dass der Hook die Geste bekommt."
    )


def test_bottom_padding_bleibt(index_html):
    """Die Bottom-Nav liegt weiterhin fix ueber dem Inhalt - ohne das Padding
    verschwaende die letzte Zeile dahinter."""
    assert "@media(max-width:600px){.main-pad{padding:10px 8px 80px 8px}}" in index_html, (
        "Das Bottom-Padding fuer die fixe Navigationsleiste ist weg."
    )


def test_selbsttest_riegel_schlaegt_beim_rueckbau_an(index_html):
    kaputt = re.sub(r"@media\(max-width:1199px\)\{\s*\.app-shell\{[^}]*\}\s*"
                    r"\.app-col\{[^}]*\}\s*\.main-pad\{[^}]*\}\s*\}", "", index_html, count=1, flags=re.S)
    assert kaputt != index_html, "Rueckbau griff nicht - Anker veraltet"
    assert not re.search(r"\.app-shell\{[^}]*height:100dvh", kaputt), (
        "Umkehrprobe: der Scroll-Container-Riegel wuerde nicht anschlagen"
    )
