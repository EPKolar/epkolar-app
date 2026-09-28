# -*- coding: utf-8 -*-
"""CSS-Wahlmuster auf den `style`-Inhalt muessen die CSS-Schreibweise kennen.

🔴 DER BEFUND, 28.09.2026
Mehrere Regeln zielen auf den Inhalt des `style`-Attributs und suchen darin die
**JavaScript**-Schreibweise. React schreibt dort **CSS**. Gemessen am laufenden
Baum (`as_liste`, 1440 px), mit Gegenprobe direkt daneben:

    [style*="fontSize:24"]    0 Treffer   |   [style*="font-size: 24px"]   11
    [style*="display:flex"]   0 Treffer   |   [style*="display: flex"]    206

`style={{display:"flex"}}` wird zu `style="display: flex"` - mit Bindestrich,
mit Leerzeichen, bei Zahlen mit Einheit. Ein Muster ohne diese Umschreibung
findet nie etwas, und sein Schweigen sieht aus wie „hier gibt es nichts".

🔴 UND ES WAR SCHON HALB AUFGEFALLEN. Bei `width`, `cursor` und `touchAction`
steht BEIDES in der Datei - einmal JS-, einmal CSS-Schreibweise. Jemand hat es
an drei Stellen bemerkt und nicht gesucht, wo es sonst vorkommt. Genau deshalb
gibt es diesen Riegel: nicht damit jemand die Regel KENNT, sondern damit sie an
einer Stelle geprueft wird.

WAS DIESER RIEGEL NICHT KANN: er sieht den Quelltext. Ob ein Wahlmuster am
Schirm wirklich trifft, sagt nur der Browser - die Zahlen oben stammen aus
einem Lauf, nicht aus dieser Datei.
"""
import io
import os
import re
import sys
from collections import Counter

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WURZEL, "scripts"))
import code_scan  # noqa: E402

PFAD = os.path.join(WURZEL, "index.html")
MUSTER = re.compile(r"\[style\*=['\"]([^'\"]{1,60})['\"]\]")

# Muster, die absichtlich in JS-Schreibweise dastehen duerfen, weil die
# CSS-Schreibweise DANEBEN steht. Namentlich, nicht als Regel.
GEPAART = {
    "width:220px": "width: 220px",
    "cursor:pointer": "cursor: pointer",
    "touch-action:none": "touchAction: none",
}

# Die Ueberlagerungs-Familie. Sie bleibt bewusst in JS-Schreibweise, weil die
# Messreihe keine Dialoge oeffnet und ein Fehler dort einen Dialog unbedienbar
# macht statt nur unschoen. Siehe `docs/befunde/TOTE_WAHLMUSTER.md`.
AUFGESCHOBEN = ("position:fixed", "inset:0", "zIndex:1000", "zIndex:1001",
                "zIndex:1500", "zIndex:1501", "zIndex:2000")


def _lies():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def js_schreibweise(text):
    """Muster in JS-Schreibweise: Doppelpunkt OHNE folgendes Leerzeichen."""
    aus = []
    for m in MUSTER.finditer(text):
        w = m.group(1)
        if ":" in w and ": " not in w:
            aus.append(w)
    return aus


def test_die_tippziel_familie_kennt_die_css_schreibweise():
    """Die Regeln, deren Wirkung an `tipp44` ablesbar ist."""
    t = _lies()
    alle = [m.group(1) for m in MUSTER.finditer(t)]
    fehlt = []
    for js, css in (("display:flex", "display: flex"),
                    ("fontSize:10", "font-size: 10px"),
                    ("fontSize:11", "font-size: 11px"),
                    ("fontSize:12", "font-size: 12px")):
        if js in alle and css not in alle:
            fehlt.append((js, css))
    assert not fehlt, (
        "\U0001F534 Diese Wahlmuster stehen nur in JS-Schreibweise da und "
        "treffen deshalb NICHTS:\n    %s\n"
        "  React schreibt `style=\"display: flex\"`, nicht `display:flex`. "
        "Gemessen:\n"
        "  das erste Muster trifft 0 Elemente, das zweite 206.\n"
        "  Die CSS-Schreibweise gehoert ERGAENZT, nicht ersetzt." % fehlt)


def test_die_gepaarten_bleiben_gepaart():
    """Wo beide Schreibweisen dastehen, muessen beide dableiben.

    Sonst faellt beim naechsten Aufraeumen die wirksame weg und die tote
    bleibt - das sieht man niemandem an.
    """
    t = _lies()
    alle = set(m.group(1) for m in MUSTER.finditer(t))
    fehlt = [(js, css) for js, css in GEPAART.items()
             if js in alle and css not in alle]
    assert not fehlt, (
        "\U0001F534 Bei diesen Paaren ist die CSS-Schreibweise verschwunden, "
        "die tote steht noch: %s" % fehlt)


def test_die_aufgeschobene_familie_ist_benannt_und_nicht_gewachsen():
    """🔴 Eine Ausnahme ohne Grenze waere eine Attrappe.

    Die Ueberlagerungs-Regeln bleiben in JS-Schreibweise stehen, weil sie von
    hier aus NICHT messbar sind. Das ist eine bewusste Entscheidung mit
    Begruendung - aber sie darf nicht unbemerkt wachsen.
    """
    t = _lies()
    js = Counter(js_schreibweise(t))
    unbekannt = sorted(w for w in js
                       if w not in AUFGESCHOBEN and w not in GEPAART
                       and not w.startswith("fontSize:")
                       and w != "display:flex")
    assert not unbekannt, (
        "\U0001F534 Neue Wahlmuster in JS-Schreibweise, die niemand "
        "eingeordnet hat: %s\n"
        "  Sie treffen nichts. Entweder die CSS-Schreibweise ergaenzen oder "
        "hier eintragen,\n"
        "  mit Begruendung warum sie aufgeschoben ist." % unbekannt)


def test_koeder_die_erkennung_trifft_und_schweigt():
    """Koeder UND Gegenprobe - ohne die zweite waere ein Melder gruen, der
    alles meldet."""
    assert js_schreibweise('[style*="display:flex"]') == ["display:flex"], (
        "\U0001F534 Die JS-Schreibweise wird nicht erkannt.")
    assert js_schreibweise('[style*="zIndex:1001"]') == ["zIndex:1001"]
    assert not js_schreibweise('[style*="display: flex"]'), (
        "\U0001F534 Die CSS-Schreibweise wird als JS gemeldet - dann meldet "
        "der Riegel alles.")
    assert not js_schreibweise('[style*="min-width"]'), (
        "\U0001F534 Ein Muster ohne Doppelpunkt wird gemeldet.")
    assert not js_schreibweise('[style*="text-align: right"]')


def test_die_grundgesamtheit_ist_nicht_leer():
    t = _lies()
    alle = [m.group(1) for m in MUSTER.finditer(t)]
    assert len(alle) > 20, (
        "\U0001F534 Nur %d style-Wahlmuster gefunden. Erwartet sind ueber 20 - "
        "der Sucher\n  trifft nicht mehr, und jede Zusicherung oben waere "
        "geschenkt." % len(alle))
