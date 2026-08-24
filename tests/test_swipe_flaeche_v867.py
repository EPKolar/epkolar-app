# -*- coding: utf-8 -*-
"""
v3.9.867 - Wischen scheiterte an der GROESSE der Flaeche, nicht an der Geste.

BUG (User-Report: "Riedmann hat das Problem"):
`.main-pad` ist ein normaler Block und damit nur so hoch wie sein INHALT.
Wer viele Daten hat - Buero, Admin - fuellt den Schirm, und jede Geste trifft
die Wischflaeche. Wer wenige hat - ein Monteur mit leerer Projektliste - hat
darunter blanken Hintergrund, der NICHT zum Container gehoert. Ein Wisch dort
erreicht den Hook nie.

LIVE GEMESSEN als Rolle monteur (390x844, echte Touch-Eingabe via CDP,
nicht synthetisch):

    ohne Fix: .main-pad 91..392 von 844px Schirm
              y=430 / 560 / 700 -> ausserhalb -> KEIN WECHSEL
              y=300              -> innerhalb  -> wechselt sofort
    mit Fix:  .main-pad 91..839
              y=430 / 560 / 700 / 780 -> alle innerhalb -> alle wechseln
    Seitenhoehe in BEIDEN Faellen 914 -> kein Layout-Shift, kein Extra-Scroll

Das erklaert, warum die Vorgaenger-Versuche (v825, v834, v836, v863, v865) den
gemeldeten Fall nie trafen: gemessen wurde stets mit vollen Daten oder als
Admin, und da ist die Flaeche gross genug.

FIX: min-height auf .main-pad bis 1199px Breite (Handy + Tablet, beide Touch).
min-height hebt NUR zu kurze Seiten an - laengere sind ohnehin groesser, es
verschiebt sich also nichts. Die 80px Bottom-Padding fuer die Bottom-Nav
stecken durch `box-sizing:border-box` bereits in der Hoehe.
"""
import re


def _regel(index_html):
    m = re.search(r"@media\(max-width:1199px\)\{\.main-pad\{([^}]*)\}\}", index_html)
    assert m, (
        "Die Regel, die der Wischflaeche eine Mindesthoehe gibt, ist weg - "
        "damit ist auf inhaltsarmen Seiten wieder der halbe Schirm tot."
    )
    return m.group(1)


def test_wischflaeche_hat_mindesthoehe(index_html):
    regel = _regel(index_html)
    assert "min-height" in regel, "min-height fehlt:\n" + regel


def test_mindesthoehe_richtet_sich_am_sichtbaren_bereich_aus(index_html):
    """dvh statt vh: auf dem Handy schrumpft der sichtbare Bereich, wenn die
    Browser-Leiste eingeblendet ist. vh wuerde dann zu gross rechnen und auf
    JEDER Seite einen Extra-Scroll erzeugen."""
    regel = _regel(index_html)
    assert "100dvh" in regel, (
        "Die Mindesthoehe rechnet nicht mit dvh - mit vh entsteht auf dem Handy "
        "unnoetiger Scroll:\n" + regel
    )
    m = re.search(r"calc\(100dvh - (\d+)px\)", regel)
    assert m, "Kein calc(100dvh - Kopfhoehe):\n" + regel
    abzug = int(m.group(1))
    assert 60 <= abzug <= 160, (
        "Abzug %dpx ist unplausibel. Zu klein -> die Flaeche ragt unter den "
        "Bildschirm und erzeugt Scroll auf jeder kurzen Seite. Zu gross -> "
        "unten bleibt wieder ein toter Streifen. Gemessen: Kopfzeile bei 91px."
        % abzug
    )


def test_gilt_fuer_handy_und_tablet(index_html):
    """Der Fehler trifft jedes Touch-Geraet, nicht nur Handys - Tablets liegen
    im Bereich 600-1199px und wischen genauso."""
    assert "@media(max-width:1199px){.main-pad{min-height" in index_html, (
        "Die Regel greift nicht bis 1199px - Tablets haetten das Problem weiter."
    )


def test_bestehende_main_pad_regeln_unangetastet(index_html):
    """Der Fix darf nur Hoehe ergaenzen, nicht Abstaende oder touch-action
    veraendern - sonst kippt Layout oder Gesten-Verhalten."""
    assert ".main-pad{padding:20px;touch-action:pan-y}" in index_html, (
        "Die Basis-Regel wurde veraendert - touch-action:pan-y ist die "
        "Voraussetzung dafuer, dass der Hook die Geste ueberhaupt bekommt."
    )
    assert "@media(max-width:600px){.main-pad{padding:10px 8px 80px 8px}}" in index_html, (
        "Das Bottom-Padding fuer die Bottom-Nav wurde veraendert - 80px halten "
        "den Inhalt ueber der fixen Navigationsleiste."
    )


def test_hoehe_und_padding_bleiben_getrennte_regeln(index_html):
    """Beide Regeln muessen nebeneinander existieren: die 600er traegt das
    Padding, die 1199er die Hoehe. Wird die Hoehe in die 600er gezogen,
    verlieren Tablets sie wieder."""
    i_pad = index_html.find("@media(max-width:600px){.main-pad{padding:10px 8px 80px 8px}}")
    i_h = index_html.find("@media(max-width:1199px){.main-pad{min-height")
    assert i_pad != -1 and i_h != -1, "Eine der beiden Regeln fehlt"
    assert i_pad != i_h, "Regeln zusammengefallen"


def test_selbsttest_riegel_schlaegt_beim_rueckbau_an(index_html):
    """Umkehrprobe: die Regel entfernen, die Riegel muessen ROT werden."""
    kaputt = re.sub(r"@media\(max-width:1199px\)\{\.main-pad\{[^}]*\}\}", "", index_html, count=1)
    assert kaputt != index_html, "Rueckbau griff nicht - Anker veraltet"
    assert not re.search(r"@media\(max-width:1199px\)\{\.main-pad\{", kaputt), (
        "Umkehrprobe: der Flaechen-Riegel wuerde nicht anschlagen"
    )
