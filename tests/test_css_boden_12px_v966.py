# -*- coding: utf-8 -*-
"""Keine CSS-Regel darf eine Schrift unter 12 px ERZWINGEN.

🔴 WARUM ES DIESEN RIEGEL GIBT - und warum er meinen eigenen einen Commit
spaeter widerlegt hat.

`test_fahrzeuge_schriftgroesse_v965` misst den QUELLTEXT: keine feste
Schriftgroesse unter 12 px in FahrzeugView. Der Riegel ist gruen. Und trotzdem
zeigte die Arbeitsscheinliste 24 Stellen unter 12 px bei 390 px, obwohl ihr
Quelltext NULL solche Werte fuehrt.

Am laufenden Element gemessen: inline `font-size: 12px`, berechnet `10px`.
Inline `13px`, berechnet `11px`. Die Ursache war
`.kpi-grid.epk-leiste > div > div:nth-child(4) { font-size: 10px !important }`.
Eine Regel mit !important uebersteuert JEDE Inline-Angabe - also auch alle 115,
die v3.9.965 gehoben hat. Ein Riegel, der nur den Quelltext liest, bleibt dabei
gruen. Das ist Anwesenheit statt Wirkung, an meinem eigenen Werk.

🔴 UND DER ZWEITE FEHLER, beim ZAEHLEN: mein erster Zaehler suchte im ROHEN
Dateitext. Er fand vier Regeln statt drei - die vierte war mein EIGENER
Aenderungstext, in dem die Regel zitiert steht. Wer rohen Dateitext durchsucht,
misst seine eigene Begruendung mit: gruen, sobald jemand sie hinschreibt, rot,
wenn jemand sie loescht. Gezaehlt wird deshalb ausschliesslich INNERHALB der
`<style>`-Bloecke, und ein Koeder belegt, dass ein Vorkommen im Kommentar NICHT
mitzaehlt.

DIE EINE AUSNAHME, namentlich: `svg text` steht auf 10 px. Diagramm-Achsen
stehen dicht nebeneinander; 10 auf 12 px kann sie zum Ueberlappen bringen. Das
ist ein eigener Schritt mit eigener Messung. Sie steht hier als NAME, nicht als
Zahl - eine Ausnahme ohne Begruendung ist eine Attrappe.
"""
import io
import os
import re

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")

REGEL = re.compile(
    r"([^{};]{1,120})\{([^{}]{0,300}?font-size:\s*(\d+(?:\.\d+)?)px"
    r"\s*!important[^{}]{0,200})\}")

# Wahlmuster, die absichtlich unter 12 px bleiben - mit Begruendung im Kopf.
AUSNAHMEN = ("svg text",)


def _lies():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def stilbloecke(text):
    """Nur der Inhalt der <style>-Bloecke. NICHT der rohe Dateitext."""
    return "".join(m.group(1)
                   for m in re.finditer(r"<style[^>]*>(.*?)</style>", text, re.S))


def erzwungen_klein(css):
    """(px, Wahlmuster) je Regel, die unter 12 px erzwingt - ohne Ausnahmen."""
    aus = []
    for m in REGEL.finditer(css):
        if float(m.group(3)) >= 12:
            continue
        sel = " ".join(m.group(1).split())
        if any(a in sel for a in AUSNAHMEN):
            continue
        aus.append((m.group(3), sel[:80]))
    return aus


def test_kein_css_erzwingt_schrift_unter_12px():
    css = stilbloecke(_lies())
    # Gegenprobe auf die Grundgesamtheit: der Stilblock MUSS Regeln mit
    # !important fuehren, sonst ist die Null unten geschenkt.
    alle = [m for m in REGEL.finditer(css)]
    assert len(alle) > 15, (
        "\U0001F534 Nur %d font-size-Regeln mit !important im Stilblock - die "
        "Bloecke wurden\n  nicht richtig gelesen, und eine leere "
        "Grundgesamtheit meldet immer gruen." % len(alle))
    fund = erzwungen_klein(css)
    assert not fund, (
        "\U0001F534 %d CSS-Regeln erzwingen eine Schrift unter 12 px:\n%s\n"
        "  Eine Regel mit !important uebersteuert JEDE Inline-Angabe. Solange "
        "sie steht,\n"
        "  bleibt jede gehobene Zahl im Quelltext wirkungslos - und ein "
        "Riegel, der nur\n"
        "  den Quelltext misst, bleibt dabei gruen."
        % (len(fund), "\n".join("    %spx  %s" % x for x in fund)))


def test_die_ausnahme_ist_noch_die_ausnahme():
    """Genau EINE Regel darf drunter bleiben, und nur die benannte.

    Ohne diese Probe koennte die Ausnahmeliste wachsen, bis der Riegel nichts
    mehr misst.
    """
    css = stilbloecke(_lies())
    drunter = [(px, sel) for px, sel in
               [(m.group(3), " ".join(m.group(1).split()))
                for m in REGEL.finditer(css)] if float(px) < 12]
    assert len(drunter) == 1, (
        "\U0001F534 %d Regeln unter 12 px im Stilblock, erwartet ist genau "
        "eine (svg text):\n    %s" % (len(drunter), drunter))
    assert "svg text" in drunter[0][1], (
        "\U0001F534 Die verbliebene Regel ist nicht mehr `svg text`, sondern "
        "%r - die Ausnahme\n  hat sich verschoben und braucht eine eigene "
        "Begruendung." % drunter[0][1])
    assert len(AUSNAHMEN) == 1, (
        "\U0001F534 Die Ausnahmeliste ist gewachsen (%s). Jede Ausnahme braucht "
        "ein Messdatum\n  im Kopf dieser Datei, sonst misst der Riegel "
        "irgendwann nichts mehr." % (AUSNAHMEN,))


def test_koeder_eine_erzwungene_kleine_regel():
    """Eine 10-px-Regel MUSS gemeldet werden."""
    fund = erzwungen_klein(".irgendwas > div { font-size: 10px !important; }")
    assert fund and fund[0][0] == "10", (
        "\U0001F534 Eine erzwungene 10-px-Regel wurde nicht gemeldet.")


def test_koeder_kommentar_zaehlt_NICHT_mit():
    """\U0001F534 Der Fehler, der mir beim Zaehlen selbst passiert ist.

    Mein erster Zaehler las den ROHEN Dateitext und fand vier Regeln statt
    drei: die vierte war mein eigener Aenderungstext, in dem die Regel zitiert
    steht. Diese Probe belegt, dass der Riegel seine eigene Begruendung nicht
    mitmisst.
    """
    text = ('<html><head><style>.a{font-size:14px !important;}'
            '.b{font-size:13px !important;}.c{font-size:12px !important;}'
            '.d{color:red !important;}.e{font-size:16px !important;}'
            '.f{font-size:15px !important;}.g{font-size:18px !important;}'
            '.h{font-size:20px !important;}.i{font-size:22px !important;}'
            '.j{font-size:24px !important;}.k{font-size:26px !important;}'
            '.l{font-size:28px !important;}.m{font-size:30px !important;}'
            '.n{font-size:32px !important;}.o{font-size:34px !important;}'
            '.p{font-size:36px !important;}</style></head><body>'
            '<script>/* die Regel .z{font-size: 9px !important;} war der '
            'Traeger des Befunds */</script></body></html>')
    css = stilbloecke(text)
    assert "font-size: 9px" not in css, (
        "\U0001F534 Der Kommentar im script-Block ist in den Stilblock "
        "geraten.")
    assert not erzwungen_klein(css), (
        "\U0001F534 Der Riegel hat seine eigene Begruendung mitgezaehlt - "
        "genau der Fehler,\n  den er verhindern soll.")
    # Und die Gegenrichtung am SELBEN Text: im echten Stilblock wird gemeldet.
    assert erzwungen_klein(css + ".z{font-size: 9px !important;}"), (
        "\U0001F534 Am selben Text meldet der Riegel eine echte Regel nicht - "
        "dann schweigt er\n  immer, und die Probe oben ist wertlos.")


def test_gegenprobe_zwoelf_und_groesser_schweigen():
    for fall in (".a { font-size: 12px !important; }",
                 ".b { font-size: 14px !important; }",
                 ".c { font-size: 18px !important; }"):
        assert not erzwungen_klein(fall), (
            "\U0001F534 %s wurde gemeldet - der Riegel meldet dann alles." % fall)
