# -*- coding: utf-8 -*-
"""`index.html` und `sw.js` fuehren AUSSCHLIESSLICH CRLF.

🔴 WARUM DAS EINEN RIEGEL BRAUCHT
Am 28.09.2026 habe ich einen Block in `index.html` eingefuegt, den ich in
Python getippt hatte statt ihn aus der Datei zu schneiden. Er brachte 23 reine
LF-Zeilen mit - in einer Datei, die sonst 30 257 von 30 257 Zeilen auf CRLF
fuehrt. Folgen:

  * `git` meldet bei JEDEM Commit "LF will be replaced by CRLF", und die
    Meldung geht im Rauschen unter.
  * Der naechste Griff mit einem getippten Anker trifft NICHT mehr - genau das
    ist beim zweiten Anlauf derselben Aenderung passiert. `safe_edit` hat es
    gemeldet und auf `schneide` verwiesen; da war der erste Block schon drin.

🔴 UND DIE ANDERE RICHTUNG, die viel teurer war: am 26.09. hat ein Skript mit
`io.open(p,'w')` die GANZE Datei auf CRLF umgestellt - ein Wort geaendert,
10 389 Zeilen angefasst, neunzehn Dateien betroffen. Dieser Riegel verlangt
deshalb nicht "irgendein einheitliches Zeilenende", sondern ausdruecklich CRLF
UND eine plausible Zeilenzahl: eine Datei, deren Zeilenzahl sich ueber Nacht
verdoppelt, ist kein Erfolg, sondern ein Unfall.
"""
import io
import os

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATEIEN = ["index.html", "sw.js"]


def _zaehlen(name):
    b = io.open(os.path.join(WURZEL, name), "rb").read()
    crlf = b.count(b"\r\n")
    return crlf, b.count(b"\n") - crlf, len(b)


def test_keine_reinen_LF_zeilen():
    fund = {}
    for n in DATEIEN:
        crlf, nur_lf, _ = _zaehlen(n)
        if nur_lf:
            fund[n] = (crlf, nur_lf)
    assert not fund, (
        "\U0001F534 Gemischte Zeilenenden (CRLF, reine LF): %s\n"
        "  Ein getippter Anker trifft dann nicht mehr, und git meldet es bei "
        "JEDEM Commit.\n"
        "  Kur: den Anker mit `safe_edit.schneide` AUS DER DATEI schneiden, "
        "nicht tippen -\n"
        "  was geschnitten ist, kann nicht anders geschrieben sein als das "
        "Original." % fund)


def test_die_zeilenzahl_ist_plausibel():
    """\U0001F534 Die Gegenrichtung: eine pauschale Umstellung.

    Am 26.09.2026 hat `io.open(p,'w')` eine Datei komplett umgeschrieben -
    ein Wort geaendert, 10 389 Zeilen angefasst. Wer diesen Riegel gruen
    bekommen will, indem er die ganze Datei durch einen Umsteller schickt,
    faellt hier auf.
    """
    crlf, _, groesse = _zaehlen("index.html")
    assert 25_000 < crlf < 40_000, (
        "\U0001F534 index.html hat %d Zeilen - erwartet sind rund 30 000.\n"
        "  Entweder ist die Datei massiv gewachsen oder ein Umsteller hat sie "
        "angefasst." % crlf)
    assert 3_000_000 < groesse < 5_000_000, (
        "\U0001F534 index.html ist %d Bytes gross - erwartet sind rund 3,7 "
        "Millionen." % groesse)


def test_koeder_der_zaehler_sieht_beide_formen():
    """Ohne diesen Koeder waere ein Zaehler gruen, der gar nichts findet."""
    import tempfile
    d = tempfile.mkdtemp()
    try:
        p = os.path.join(d, "probe.txt")
        io.open(p, "wb").write(b"a\r\nb\nc\r\n")
        b = io.open(p, "rb").read()
        crlf = b.count(b"\r\n")
        nur = b.count(b"\n") - crlf
        assert crlf == 2 and nur == 1, (
            "\U0001F534 Der Zaehler unterscheidet CRLF und reines LF nicht: "
            "%d/%d" % (crlf, nur))
        io.open(p, "wb").write(b"a\r\nb\r\n")
        b = io.open(p, "rb").read()
        assert b.count(b"\n") - b.count(b"\r\n") == 0, (
            "\U0001F534 Der Zaehler meldet reine LF, wo keine sind - dann ist "
            "jeder Alarm wertlos.")
    finally:
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))
        os.rmdir(d)
