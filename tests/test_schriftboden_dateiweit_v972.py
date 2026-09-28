# -*- coding: utf-8 -*-
"""Dateiweit KEINE feste Schriftgroesse unter 12 px - weder fest noch bedingt.

🔴 WARUM DAS JETZT GEHT UND IM SEPTEMBER NICHT
v3.9.944 hat den Rundumschlag ausdruecklich abgelehnt, und die Begruendung war
richtig: *„Alle auf einmal zu heben waere eine Wette: jede steckt in einer
Kachel oder Tabellenzelle, deren Hoehe und Breite mitwandert, und messen kann
ich mit den vorhandenen Sonden VIER Ansichten von 22."*

Die Begruendung ist entfallen, nicht die Vorsicht. Der Pruefstand misst
inzwischen **22 Ansichten in 44 Aufnahmen** bei 390 und 1440 px, mit Meldern
fuer Querlauf UND Textverlust. Die Wette wurde nachgerechnet statt eingegangen:
nach dem Heben ist `verl` ueberall 0 geblieben und kein `roll` gestiegen.

🔴 ZWEI GRUNDGESAMTHEITEN, NICHT EINE. Das ist der Fehler, der v3.9.943/944
unterlaufen ist und den der Kommentar an der Tokenleiter selbst festhaelt:
das damalige Muster suchte die kleine Zahl LINKS vom Doppelpunkt
(`isMob?9:14`). Die Faelle mit der kleinen Zahl RECHTS (`isMob?12:10`, also
der SCHREIBTISCH-Wert unter 12) kamen in seiner Grundgesamtheit ueberhaupt
nicht vor - und genau deshalb stand nach dem ersten Griff bei 390 px ueberall
0 und bei 1440 px nicht.
Dieser Riegel prueft deshalb BEIDE Zweige.

🔴 NUR IM CODE. Die Aenderungslisten dieser Datei zitieren `fontSize:9`
dutzendfach. Wer rohen Dateitext durchsucht, misst seine eigene Begruendung
mit - an einem Tag sechsmal passiert.
"""
import io
import os
import re
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WURZEL, "scripts"))
import code_scan  # noqa: E402

PFAD = os.path.join(WURZEL, "index.html")

FEST = re.compile(r"fontSize\s*:\s*(\d+(?:\.\d+)?)(?![\d.])")

# 🔴 FUENF SCHREIBWEISEN, und jede einzelne hat sich an EINEM Tag als Luecke
# gezeigt. Die Reihenfolge, in der sie aufgefallen sind:
#   1. `fontSize:9`                  - die nackte Zahl
#   2. `fontSize:isMob?9:14`         - Bedingung, kleine Zahl LINKS
#                                      (das einzige Muster, das v3.9.943 hatte)
#   3. `fontSize:isMob?12:10`        - kleine Zahl RECHTS. Der Kommentar an der
#                                      Tokenleiter nennt sie seit v3.9.947, und
#                                      mein Muster hat sie trotzdem nicht erfasst
#   4. `fontSize:isMob?UI.fMeta:8`   - TOKEN auf der einen, Zahl auf der anderen
#                                      Seite. Gefunden, weil `home` bei 1440 px
#                                      noch 19 Stellen meldete
#   5. `fontSize:h>0?13:11`          - die Bedingung ist ein AUSDRUCK mit
#                                      Operator, kein Bezeichner. Gefunden, weil
#                                      `berichte` noch 8 meldete
# Deshalb steht hier EIN Muster, das die Bedingung nicht mehr einschraenkt, und
# eine Wertetabelle, die Token wie Zahlen behandelt.
BEDINGT = re.compile(
    r"fontSize\s*:\s*([^,}?]{1,40}?)\?\s*([\w.]+)\s*:\s*([\w.]+)(?![\w.])")

TOKENWERT = {"UI.fMeta": 12, "UI.fKlein": 13, "UI.fText": 14,
             "UI.fTitel": 15, "UI.fTitelGross": 17, "UI.fZahl": 20,
             "UI.fZahlGross": 24, "UI.fUeber": 28, "UI.fSeite": 22,
             "UI.fSeiteMob": 18}


def _wert(x):
    """Zahl oder bekanntes Token -> Pixel. Sonst None (nicht beurteilbar)."""
    x = x.strip()
    if x.isdigit():
        return int(x)
    return TOKENWERT.get(x)


def _lies():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _bauteil(text, feld, p):
    nm = "(ausserhalb)"
    for m in re.finditer(r"function\s+([A-Z]\w+)\s*\(", text):
        if not feld[m.start()]:
            continue
        if m.start() <= p:
            nm = m.group(1)
        else:
            break
    return nm


def feste_klein(text, feld):
    return [(m.group(1), m.start()) for m in FEST.finditer(text)
            if feld[m.start()] and float(m.group(1)) < 12]


def bedingte_klein(text, feld):
    aus = []
    for m in BEDINGT.finditer(text):
        if not feld[m.start()]:
            continue
        a, b = _wert(m.group(2)), _wert(m.group(3))
        if a is None or b is None:
            continue          # nicht beurteilbar - wird nicht behauptet
        if a < 12 or b < 12:
            aus.append(("%s?%s:%s" % (m.group(1).strip()[:20],
                                      m.group(2), m.group(3)), m.start()))
    return aus


def test_keine_feste_schriftgroesse_unter_12px():
    text = _lies()
    feld = code_scan.ist_code(text)
    fund = feste_klein(text, feld)
    assert not fund, (
        "\U0001F534 %d feste Schriftgroessen unter 12 px im Code:\n    %s\n"
        "  UI.fMeta (12) ist der Boden der App."
        % (len(fund),
           sorted({(w, _bauteil(text, feld, p)) for w, p in fund})[:12]))


def test_kein_bedingter_zweig_unter_12px():
    """\U0001F534 Die zweite Grundgesamtheit, die v3.9.943/944 nicht kannte."""
    text = _lies()
    feld = code_scan.ist_code(text)
    fund = bedingte_klein(text, feld)
    assert not fund, (
        "\U0001F534 %d bedingte Schriftgroessen mit einem Zweig unter 12 px:\n"
        "    %s\n"
        "  Ein Muster, das nur EINE Seite des Doppelpunkts ansieht, meldet "
        "hier nichts -\n"
        "  und genau das ist v3.9.943/944 passiert. BEIDE Zweige zaehlen."
        % (len(fund),
           sorted({(w, _bauteil(text, feld, p)) for w, p in fund})[:12]))


def test_die_grundgesamtheit_ist_nicht_leer():
    """Gegenprobe: es MUSS Schriftgroessen geben, sonst ist die Null geschenkt."""
    text = _lies()
    feld = code_scan.ist_code(text)
    alle = len([m for m in re.finditer(r"fontSize\s*:", text) if feld[m.start()]])
    assert alle > 1500, (
        "\U0001F534 Nur %d fontSize-Angaben im Code. Erwartet sind ueber 1500 -"
        " der Abtaster\n  trifft nicht mehr, und beide Nullen oben waeren "
        "geschenkt." % alle)
    token = len([m for m in re.finditer(r"fontSize\s*:\s*UI\.f", text)
                 if feld[m.start()]])
    assert token > 600, (
        "\U0001F534 Nur %d Angaben benutzen die Tokenleiter. Nach dem "
        "Rundumschlag sollten es\n  ueber 600 sein - sonst ist etwas "
        "zurueckgedreht worden." % token)


def test_koeder_beide_formen_werden_gefunden():
    """Ein Koeder JE FORM, plus die Gegenproben."""
    t = 'h("div",{style:{fontSize:9}},"x")'
    f = code_scan.ist_code(t)
    assert feste_klein(t, f), "\U0001F534 Die feste Form wird nicht gefunden."

    t2 = 'h("div",{style:{fontSize:isMob?12:10}},"x")'
    f2 = code_scan.ist_code(t2)
    assert bedingte_klein(t2, f2), (
        "\U0001F534 Die bedingte Form mit der kleinen Zahl RECHTS wird nicht "
        "gefunden -\n  genau die Luecke von v3.9.943/944.")

    t3 = 'h("div",{style:{fontSize:isMob?9:14}},"x")'
    f3 = code_scan.ist_code(t3)
    assert bedingte_klein(t3, f3), (
        "\U0001F534 Die bedingte Form mit der kleinen Zahl LINKS wird nicht "
        "gefunden.")

    # 🔴 Form 4: TOKEN auf der einen, Zahl auf der anderen Seite.
    t4 = 'h("div",{style:{fontSize:isMob?UI.fMeta:8}},"x")'
    f4 = code_scan.ist_code(t4)
    assert bedingte_klein(t4, f4), (
        "\U0001F534 Die gemischte Form (Token/Zahl) wird nicht gefunden.\n"
        "  Sie hat `home` bei 1440 px 19 Stellen kosten lassen, nachdem alle "
        "anderen\n  Formen schon gehoben waren.")

    # 🔴 Form 5: die Bedingung ist ein AUSDRUCK, kein Bezeichner.
    t5 = 'h("td",{style:{fontSize:h>0?13:11}},"x")'
    f5 = code_scan.ist_code(t5)
    assert bedingte_klein(t5, f5), (
        "\U0001F534 Eine Bedingung mit Operator (`h>0`) wird nicht gefunden.\n"
        "  Genau daran hingen die letzten acht Stellen in `berichte`.")

    # Gegenproben: was NICHT gemeldet werden darf.
    for gut in ('h("div",{style:{fontSize:12}},"x")',
                'h("div",{style:{fontSize:UI.fMeta}},"x")',
                'h("div",{style:{fontSize:isMob?14:12}},"x")'):
        fg = code_scan.ist_code(gut)
        assert not feste_klein(gut, fg) and not bedingte_klein(gut, fg), (
            "\U0001F534 %s wurde gemeldet - der Riegel meldet dann alles." % gut)


def test_koeder_ein_kommentar_zaehlt_NICHT_mit():
    """\U0001F534 Sechsmal an einem Tag passiert: die eigene Begruendung
    mitgemessen."""
    t = ('var a=1;/* die Falle: fontSize:9 wurde zu UI.fMeta gehoben */'
         'var b=2;')
    f = code_scan.ist_code(t)
    assert not feste_klein(t, f), (
        "\U0001F534 Ein `fontSize:9` im KOMMENTAR wird mitgezaehlt. Dann wird "
        "dieser Riegel\n  rot, sobald jemand seine eigene Begruendung "
        "hinschreibt.")
    t2 = t + 'h("div",{style:{fontSize:9}})'
    f2 = code_scan.ist_code(t2)
    assert feste_klein(t2, f2), (
        "\U0001F534 Am selben Text wird die ECHTE Stelle nicht gefunden - dann "
        "schweigt der\n  Riegel immer.")
