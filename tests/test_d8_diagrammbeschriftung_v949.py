# -*- coding: utf-8 -*-
"""v3.9.949 - D8: die dritte Form des Beschnitts, und zwei Kappungen hintereinander.

WARUM DAS KEIN MELDER SEHEN KONNTE
──────────────────────────────────
Der Beschnitt-Melder unterscheidet zwei Formen: (a) `overflow:hidden` mit
`text-overflow:ellipsis`, wo wirklich gekuerzt wird, und (b) Kastenueberlauf
bei `overflow:visible`, wo der Text ausserhalb gezeichnet wird und nichts
verloren geht. Hier ist es eine DRITTE: der Text wird IN JAVASCRIPT gekappt,
bevor er ins DOM kommt. Es gibt kein overflow, kein ellipsis und keinen
Kasten, an dem man messen koennte. Der Melder meldete fuer die Auswertungen
"0 wirklich gekuerzt" - korrekt nach seiner Vorschrift und trotzdem die
falsche Antwort auf die Frage, ob Text verloren geht.

WAS GEMESSEN WURDE (b3_stufen_12_15_messen --nur auswertungen)
──────────────────────────────────────────────────────────────
    vorher   'Gerhard Steinb...'  'Bernadette Wie...'  'DR.-GSCH...'
    nachher  title 'Gerhard Steinbichler', sichtbar 'Gerhard Steinbic...'
             title 'DR.-GSCHMEIDLERSTRASSE 10', sichtbar 'DR.-GSCH...'

ZWEI KAPPUNGEN HINTEREINANDER
`prjFort` schnitt den Projektnamen auf 12 Zeichen, BEVOR das Diagramm ihn sah,
und das Diagramm schnitt danach noch einmal auf 8. Der title trug deshalb erst
nur "DR.-GSCHMEID" - der volle Wert war schon vorher weg. Die Anzeige kuerzt
weiterhin (das gehoert ins Diagramm), der WERT geht vollstaendig hinein.
"""
import io

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]


def _roh():
    return io.open(str(WURZEL / "index.html"), encoding="utf-8",
                   newline="").read()


def test_die_waagrechten_balken_nutzen_ihre_spaltenbreite_aus():
    """14 Zeichen ergaben 14*8+10 = 122 px, obwohl die Schranke darunter
    140 px erlaubt. 16 Zeichen sind 138 px und nutzen sie aus, ohne sie zu
    verschieben. Die Kartenhoehe haengt nur an data.length und bleibt."""
    roh = _roh()
    assert "const maxChars=14;" not in roh, (
        "SvgHBar kappt wieder bei 14 Zeichen - die Beschriftungsspalte darf "
        "bis 140 px wachsen, das sind 16 Zeichen.")
    assert "const maxChars=16;" in roh, "SvgHBar kappt nicht mehr bei 16."
    assert "Math.min(140,longestLabel*8+10)" in roh, (
        "Die 140-px-Schranke der Beschriftungsspalte ist weg. Dann passt die "
        "Rechnung hinter maxChars=16 nicht mehr.")


def test_beide_diagrammarten_tragen_den_vollen_wert_im_title():
    """Im SVG ist `<title>` der Tooltip. Er steht nur dort, wo wirklich
    gekappt wird - ein title auf jedem Balken waere Laerm."""
    roh = _roh()
    assert "lbl.length>maxChars?React.createElement('title',null,lbl):null" in roh, (
        "Den waagrechten Balken fehlt der volle Wert im title.")
    assert "_lbl.length>maxL?React.createElement('title',null,_lbl):null" in roh, (
        "Den senkrechten Balken fehlt der volle Wert im title.")


def test_die_projektnamen_werden_nicht_zweimal_gekappt():
    """Der title kann nur zeigen, was er bekommt. Solange `prjFort` auf 12
    Zeichen vorkuerzte, trug er "DR.-GSCHMEID" statt
    "DR.-GSCHMEIDLERSTRASSE 10"."""
    roh = _roh()
    assert 'p.kurz||(p.name||"").slice(0,12)' not in roh, (
        "Die Projektnamen werden wieder vorgekuerzt, bevor das Diagramm sie "
        "sieht. Dann zeigt der title nicht den vollen Namen, und der "
        "Excel-Export der Diagramme auch nicht.")
    assert 'p.kurz||(p.name||"")' in roh, (
        "Die Datenquelle des Fortschritts-Diagramms wurde nicht gefunden.")


def test_die_kleinste_schrift_der_senkrechten_balken_ist_gehoben():
    """8 bzw. 9 px waren die kleinste Schrift, die in den Auswertungen noch
    stand."""
    roh = _roh()
    assert 'fontSize: many?8:9, fontFamily: "system-ui"}' not in roh, (
        "Die Balkenbeschriftung steht wieder auf 8 bzw. 9 px.")
    assert "fontSize: many?UI.fMeta:UI.fMeta" in roh, (
        "Die Balkenbeschriftung haengt nicht an UI.fMeta.")


def test_koeder_die_beiden_diagrammbauteile_existieren_noch():
    """Ohne die Grundgesamtheit sagt keine Zeile hier etwas. Verschwinden
    SvgBar oder SvgHBar, ist dieser Riegel gruen und blind."""
    roh = _roh()
    for name in ("function SvgBar(", "function SvgHBar("):
        assert name in roh, (
            "KOEDER STUMM: %s nicht gefunden. Dieser Riegel prueft dann "
            "nichts mehr." % name)
