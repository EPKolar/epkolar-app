# -*- coding: utf-8 -*-
"""
v3.9.867 - Wischen scheiterte an der GROESSE der Flaeche.
v3.9.873 - ABGELOEST: dieselbe Absicht, besserer Weg.

URSPRUENGLICHER BEFUND (v867, weiterhin gueltig):
`.main-pad` war ein normaler Block und damit nur so hoch wie sein INHALT. Wer
viele Daten hat - Buero, Admin - fuellte den Schirm, und jede Geste traf die
Wischflaeche. Wer wenige hat - ein Monteur mit leerer Projektliste - hatte
darunter blanken Hintergrund, der NICHT zum Container gehoerte.

    ohne Fix: .main-pad 91..392 von 844px Schirm
              y=430 / 560 / 700 -> ausserhalb -> KEIN WECHSEL
              y=300              -> innerhalb  -> wechselt sofort

v867 loeste das mit `min-height: calc(100dvh - 96px)`.

WARUM DAS JETZT ANDERS GELOEST IST (v873): Der eigentliche Grund, warum Wischen
im Hauptbereich nie ankam, war ein anderer - die SEITE scrollte statt eines
Containers, und damit nahm Chrome die Geste auf oberster Ebene. Seit v873 ist
der Hauptbereich selbst der Scroller (Aufbau wie die Projektansicht):

    .app-shell  height:100dvh, overflow:hidden, Spalte
    .app-col    flex:1, min-height:0, Spalte
    .main-pad   flex:1, min-height:0, overflow-y:auto

Damit fuellt `.main-pad` den sichtbaren Bereich per Konstruktion - die
v867-min-height ist ueberfluessig UND schaedlich geworden, weil sie zusammen mit
`flex:1` den Inhalt ueber seine Box hinaus zwingen wuerde.

Diese Datei prueft weiterhin die URSPRUENGLICHE ABSICHT: unterhalb des Inhalts
darf keine tote Flaeche entstehen. Nur der Weg dorthin ist ein anderer.
"""
import re


def _container_regel(index_html):
    m = re.search(r"@media\(max-width:1199px\)\{\s*\.app-shell\{([^}]*)\}\s*"
                  r"\.app-col\{([^}]*)\}\s*\.main-pad\{([^}]*)\}\s*\}", index_html, re.S)
    assert m, (
        "Der Scroll-Container-Aufbau ist weg. Dann ist .main-pad wieder nur so "
        "hoch wie sein Inhalt - und auf inhaltsarmen Seiten ist der halbe Schirm "
        "wieder tot (der urspruengliche v867-Befund)."
    )
    return m


def test_inhaltsflaeche_fuellt_den_sichtbaren_bereich(index_html):
    """Die Absicht von v867 - keine tote Flaeche unter dem Inhalt - wird jetzt
    per Konstruktion erreicht statt per Mindesthoehe."""
    m = _container_regel(index_html)
    pad = m.group(3)
    assert "flex:1" in pad, (
        "Der Inhaltsbereich fuellt den Rest der Spalte nicht aus - auf einer "
        "kurzen Seite entsteht darunter wieder tote Flaeche:\n" + pad
    )
    assert "min-height:0" in pad, (
        "Ohne min-height:0 waechst der Flex-Kasten ueber seine Box hinaus:\n" + pad
    )


def test_die_hoehe_kommt_von_einer_bildschirmhohen_huelle(index_html):
    m = _container_regel(index_html)
    shell = m.group(1)
    assert "height:100dvh" in shell, (
        "Die Huelle gibt keine Bildschirmhoehe vor - dann hat flex:1 nichts "
        "auszufuellen:\n" + shell
    )
    assert "100dvh" in shell and "100vh" not in shell.replace("100dvh", ""), (
        "Es wird mit vh statt dvh gerechnet - auf dem Handy schrumpft der "
        "sichtbare Bereich, wenn die Browser-Leiste eingeblendet ist:\n" + shell
    )


def test_gilt_fuer_handy_und_tablet(index_html):
    """Der Fehler trifft jedes Touch-Geraet, nicht nur Handys - Tablets liegen
    im Bereich 600-1199px und wischen genauso."""
    assert "@media(max-width:1199px){" in index_html, (
        "Die Regel greift nicht bis 1199px - Tablets haetten das Problem weiter."
    )


def test_alte_mindesthoehe_ist_verschwunden(index_html):
    """Beide Wege zusammen waeren ein Widerspruch: min-height wuerde den Inhalt
    ueber die Box hinaus zwingen, die dann doch wieder die Seite scrollen laesst."""
    assert "min-height:calc(100dvh - 96px)" not in index_html, (
        "Die v867-Mindesthoehe steht wieder neben dem Container-Aufbau - das "
        "hebt den v873-Fix teilweise wieder auf."
    )


def test_bestehende_main_pad_regeln_unangetastet(index_html):
    """Der Umbau darf nur Hoehe/Scrollen regeln, nicht Abstaende oder
    touch-action - sonst kippt Layout oder Gesten-Verhalten."""
    assert ".main-pad{padding:20px;touch-action:pan-y}" in index_html, (
        "Die Basis-Regel wurde veraendert - touch-action:pan-y ist die "
        "Voraussetzung dafuer, dass der Hook die Geste ueberhaupt bekommt."
    )
    assert "@media(max-width:600px){.main-pad{padding:10px 8px 80px 8px}}" in index_html, (
        "Das Bottom-Padding fuer die fixe Navigationsleiste wurde veraendert - "
        "80px halten den Inhalt ueber der Leiste."
    )


def test_selbsttest_riegel_schlaegt_beim_rueckbau_an(index_html):
    kaputt = re.sub(r"@media\(max-width:1199px\)\{\s*\.app-shell\{[^}]*\}\s*"
                    r"\.app-col\{[^}]*\}\s*\.main-pad\{[^}]*\}\s*\}", "",
                    index_html, count=1, flags=re.S)
    assert kaputt != index_html, "Rueckbau griff nicht - Anker veraltet"
    assert not re.search(r"\.app-shell\{[^}]*height:100dvh", kaputt), (
        "Umkehrprobe: der Flaechen-Riegel wuerde nicht anschlagen"
    )
