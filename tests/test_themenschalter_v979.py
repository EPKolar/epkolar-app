# -*- coding: utf-8 -*-
"""Der Themenknopf entscheidet nach dem SICHTBAREN Zustand, nicht nach dem Modus.

🔴 DER GEMELDETE FALL. Sebastian, 29.09.2026: *"wenn ich mobil auf hell
schalte bleibt es dunkel und wird nicht weiss."*

Der Kopfknopf war ein Ringtausch: Hell -> Dunkel -> Auto -> Hell. Auf einem
Telefon mit dunklem Betriebssystem sehen **Dunkel und Auto gleich aus**. Wer
auf Dunkel stand, tippte einmal (Auto, sieht identisch aus), hielt den Knopf
fuer kaputt, tippte wieder - und die 350-ms-Sperre gegen Geisterklicks
(v3.9.721, selbst eine Kur gegen Doppelfeuer) verschluckte den zweiten Tipp.

Nachgestellt bei 390 px, OS dunkel, ohne gespeicherte Wahl:

    Tipp 2  dark    rgb(15,17,23)   DUNKEL
    Tipp 3  system  rgb(15,17,23)   DUNKEL   <- keine sichtbare Aenderung

🔴 DREI FRUEHERE MESSUNGEN KONNTEN DAS NICHT SEHEN, und alle drei waren
richtig:

  * `hellmodus_ansichten.py` setzt `epk_theme` VOR dem Laden - 32 Ansichten,
    0 dunkle. Misst den Startzustand, nicht den Schalter.
  * `hellmodus_schalter_messen.py` betaetigt den Schalter - und er wirkt.
    Misst EINEN Tipp.
  * `hellmodus_nach_dem_schalten.py` geht nach dem Umschalten durch alle
    Ansichten - alle hell. Misst den Zustand NACH einem erfolgreichen Tipp.

Der Fall lag zwischen allen dreien: im RING, ab dem zweiten Tipp. Keine
Messung war falsch; jede hatte den falschen Umfang.

DIE KUR: entschieden wird nach `isDark` - dem Zustand, den man SIEHT -, nicht
nach `_themeMode()`, dem gespeicherten Wert. Damit aendert jeder Tipp sichtbar
etwas, egal ob man aus "dark" oder aus "system" kommt.

AUTO GEHT NICHT VERLOREN: Einstellungen -> "🎨 Darstellung" fuehrt seit
v3.9.721 eine Segmented Control (Hell / Dunkel / Auto, je >=44 px, mit
`aria-pressed`), die den Modus DIREKT setzt. Dieser Riegel prueft, dass sie
dasteht - eine Kur, die dem Kopfknopf einen Zustand nimmt, ohne dass er
anderswo erreichbar ist, waere eine Verschlechterung.

🔴 WAS DIESER RIEGEL MISST UND WAS NICHT. Er liest den QUELLTEXT: dass die
Entscheidung an `isDark` haengt und der Ring weg ist. Er sieht NICHT, ob am
Schirm wirklich etwas passiert. Die Wirkung misst daneben:

    python scripts/thema_schalter_ring_messen.py 390

Stand 29.09.2026: alle sechs Tippen aendern die Helligkeit sichtbar.
Bericht: `docs/befunde/THEMA_RING_390.json`.
"""
import io
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "scripts"))

import code_scan  # noqa: E402

PFAD = os.path.join(HIER, "..", "index.html")

# Die Entscheidung des Kopfknopfs, wie sie jetzt dasteht.
ZWEIWEG = 'setThemeMode(isDark?"light":"dark");'

# Der Ring, der den Fehler verursacht hat. Er darf NICHT zurueckkommen.
RING = 'const next=cur==="light"?"dark":cur==="dark"?"system":"light";'

# Die Segmented Control in den Einstellungen - der Ort, an dem Auto lebt.
SEGMENTE = '[["light","☀️ Hell"],["dark","🌙 Dunkel"],["system","🅰️ Auto"]]'


def _text():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _im_code(text, muster):
    ist = code_scan.ist_code(text)
    aus, i = [], text.find(muster)
    while i >= 0:
        if ist[i]:
            aus.append(i)
        i = text.find(muster, i + 1)
    return aus


def test_koeder_der_sucher_findet_beide_formen():
    """🔴 SELBSTPROBE. Ohne sie waere jede Aussage unten wertlos - ein Sucher,
    der die Form nicht kennt, meldet 'kommt nicht vor'."""
    for muster, name in ((ZWEIWEG, "Zweiwegschalter"), (RING, "Ringtausch"),
                         (SEGMENTE, "Segmented Control")):
        kuenstlich = "var a=1;" + muster + "var b=2;"
        assert _im_code(kuenstlich, muster), (
            "Der Sucher findet %s nicht einmal in einem Text, der nur daraus "
            "besteht." % name)


def test_gegenprobe_im_kommentar_zaehlt_nicht():
    """Der Ring steht in der Begruendung dieser Kur ausgeschrieben da. Ein
    Sucher auf rohem Dateitext wuerde ihn dort finden und rot werden, sobald
    jemand den Fehler erklaert."""
    kuenstlich = "/* frueher stand hier " + RING + " */\nvar y=1;"
    assert not _im_code(kuenstlich, RING), (
        "Der Sucher zaehlt ein Vorkommen im KOMMENTAR mit.")


def test_der_knopf_entscheidet_nach_dem_sichtbaren_zustand():
    t = _text()
    assert _im_code(t, ZWEIWEG), (
        "Der Themenknopf entscheidet nicht mehr nach `isDark`.\n"
        "  Wer hier wieder den gespeicherten Modus nimmt, bekommt auf einem "
        "dunklen\n  Telefon zwei Zustaende, die gleich aussehen - und der "
        "Nutzer sieht wieder\n  'ich schalte auf hell und es bleibt dunkel'.")


def test_der_ringtausch_ist_weg():
    t = _text()
    stellen = _im_code(t, RING)
    zeilen = [t.count("\n", 0, i) + 1 for i in stellen]
    assert not stellen, (
        "Der Ringtausch Hell->Dunkel->Auto ist zurueck (Zeile %s).\n"
        "  Auf einem Telefon mit dunklem Betriebssystem sehen Dunkel und Auto "
        "GLEICH aus.\n  Gemessen: scripts/thema_schalter_ring_messen.py 390"
        % zeilen)


def test_auto_bleibt_in_den_einstellungen_erreichbar():
    """🔴 Eine Kur, die einen Zustand unerreichbar macht, ist keine.

    Der Kopfknopf kennt nur noch Hell und Dunkel. Auto MUSS deshalb anderswo
    stehen - sonst haette diese Aenderung eine Einstellung abgeschafft.
    """
    t = _text()
    assert _im_code(t, SEGMENTE), (
        "Die Segmented Control in den Einstellungen ist weg. Damit gibt es "
        "KEINEN Weg\n  mehr zu 'Auto (System)': der Kopfknopf schaltet seit "
        "v3.9.979 nur noch\n  zwischen Hell und Dunkel. Entweder kommt sie "
        "zurueck - oder der Kopfknopf\n  braucht den dritten Zustand wieder, "
        "und dann gehoert der gemessene Mangel\n  aus v3.9.979 anders "
        "geloest.")
