# -*- coding: utf-8 -*-
"""B5 — am Kiosk wurde jedes Eingabefeld auf 14 px gedrückt.

**Am Schirm gemessen, in allen 30 Aufnahmen:** ein eingesetztes Feld mit
`font-size:30px` misst am Kiosk **14 px**. Die Inline-Angabe ist wirkungslos,
und ein Quelltextriegel bleibt dabei grün — genau die Klasse *der Wert im
Quelltext ist nicht der gemessene Wert*.

## Die Regel ist nicht falsch, und das ist der Punkt

    input,select,textarea{font-size:16px !important}
    @media(min-width:601px){input,select,textarea{font-size:14px !important}}

Die 16 px verhindern den **iOS-Zoom** — Safari zoomt beim Antippen, sobald
ein Feld unter 16 px liegt. Ab 601 px Breite gilt 14 px, gedacht für den
**Schreibtisch**.

**Der Fehler steckt in der Annahme:** „breit" wird als Stellvertreter für
„nah am Nutzer" benutzt. Eine Wand ist breit **und** weit weg — sie bricht
genau diese Annahme. Am Stempel-Terminal stehen Eingabefelder (die
Datumsfelder des Urlaubsantrags, erreichbar nach einem Chip-Scan), und wer
davor steht, liest 14 px aus zwei Metern nicht.

## Die Kur bleibt eng

Eine Kennung am Dokument, und eine Regel, die **ohne** diese Kennung
wirkungslos ist. Für Handy, Tablet und Schreibtisch ändert sich nichts — die
16 px für iOS bleiben unberührt. **Beides einzeln ist inert**, deshalb prüft
dieser Riegel beide Hälften.

## 🔴 Gemessen, nicht behauptet

Dieser Riegel liest die **Schirmmessung** (`docs/befunde/KIOSK_LIVE.json`,
erzeugt von `scripts/kiosk_tafeln_live.py`) und nicht den Quelltext. Nach der
Kur: **29 von 30** Aufnahmen bei 20 px.

**Die eine bei 14 px ist richtig so** — es ist die Admin-Vorschau über den
Hash allein, und dort öffnet sich gar kein Kiosk (`_canKiosk` liest nur
`location.search`, eigener Befund B6). Dort rendert die normale App, und dort
gehören 14 px hin. Das ist zugleich die Gegenprobe, dass die Regel **nicht
überall** feuert.
"""
import io
import json
import os
import re

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
PFAD = os.path.join(WURZEL, "index.html")
MESSUNG = os.path.join(WURZEL, "docs", "befunde", "KIOSK_LIVE.json")

ERWARTET_PX = 20
MINDESTENS_GROSS = 29    # Kiosk-Aufnahmen
ERWARTET_KLEIN = 1       # die Admin-Vorschau ohne Kiosk

REGEL = ("html[data-kiosk] input,html[data-kiosk] select,"
         "html[data-kiosk] textarea{font-size:20px !important}")
KENNUNG = "document.documentElement.setAttribute('data-kiosk','1')"


def _text():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _ohne_kommentare(s):
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return re.sub(r"//[^\n]*", "", s)


def _laeufe():
    d = json.loads(io.open(MESSUNG, encoding="utf-8", newline="").read())
    return d.get("laeufe") or []


def test_koeder_die_kommentarbehandlung_traegt():
    mit = "/* HIER STAND html[data-kiosk] input */ x=1;"
    assert "html[data-kiosk] input" not in _ohne_kommentare(mit), (
        "Ein Kommentar, der die Regel zitiert, wird mitgezaehlt.")


def test_beide_haelften_sind_da_denn_einzeln_ist_jede_inert():
    """🔴 Die Regel ohne die Kennung tut nichts, die Kennung ohne die Regel
    auch nicht. Wer eine Hälfte entfernt, hinterlässt etwas, das aussieht
    wie eine Kur und keine ist."""
    code = _ohne_kommentare(_text())
    assert REGEL in code, (
        "\U0001F534 Die Kiosk-Regel fuer Eingabefelder fehlt. Dann drueckt "
        "die 601-px-Regel am\n  Kiosk wieder jedes Feld auf 14 px - und wer "
        "an der Wand steht, liest das aus\n  zwei Metern nicht.")
    assert KENNUNG in code, (
        "\U0001F534 Die Kennung `data-kiosk` wird nicht mehr gesetzt. Die "
        "Regel darueber ist\n  damit WIRKUNGSLOS - sie sieht aus wie eine "
        "Kur und ist keine.")


def test_die_16px_fuer_ios_bleiben_unberuehrt():
    """🔴 Gegenprobe: die Kur darf die iOS-Schranke nicht mitnehmen.

    Safari zoomt beim Antippen, sobald ein Feld unter 16 px liegt. Wer die
    Grundregel anfasst, holt sich den iOS-Zoom zurück — und der ist auf
    einer Baustelle mit einer Hand am Gerät das Gegenteil von hilfreich.
    """
    code = _ohne_kommentare(_text())
    # 🔴 Der Anker endet NICHT mit einer Klammer: die Regel traegt noch
    # `-webkit-appearance:none` und `border-radius:8px`. Mein erster Versuch
    # erwartete das `}` direkt dahinter und wurde rot, obwohl die Regel
    # unveraendert dastand - ein Riegel, der einen Befund erfindet.
    assert "input,select,textarea{font-size:16px !important" in code, (
        "\U0001F534 Die 16-px-Grundregel ist weg oder geaendert. Dann zoomt "
        "iOS beim Antippen\n  jedes Eingabefelds.")


def test_am_schirm_gemessen_zwanzig_px_im_kiosk():
    """🔴 Die Aussage, auf die es ankommt — und sie kommt aus der MESSUNG.

    Eine Quelltextsuche kann hier nichts belegen: eine Regel mit
    `!important` übersteuert jede Inline-Angabe, und welche von zwei Regeln
    gewinnt, entscheidet die Kaskade, nicht die Reihenfolge im Text.
    """
    l = _laeufe()
    assert len(l) >= 30, (
        "\U0001F534 Nur %d Aufnahmen in der Schirmmessung, erwartet sind "
        "mindestens 30.\n  Lauf: python scripts/kiosk_tafeln_live.py --json "
        "docs/befunde/KIOSK_LIVE.json" % len(l))
    gross = [x for x in l
             if (x.get("wichtig_probe") or {}).get("input") == ERWARTET_PX]
    klein = [x for x in l if (x.get("wichtig_probe") or {}).get("input") == 14]
    assert len(gross) >= MINDESTENS_GROSS, (
        "\U0001F534 Nur %d von %d Aufnahmen messen %d px im Eingabefeld, "
        "erwartet sind\n  mindestens %d. Gemessen wird am SCHIRM - wenn diese "
        "Zahl faellt, drueckt die\n  601-px-Regel wieder durch, und zwar "
        "ohne dass der Quelltext sich aendert.\n  Lauf: python "
        "scripts/kiosk_tafeln_live.py --json docs/befunde/KIOSK_LIVE.json"
        % (len(gross), len(l), ERWARTET_PX, MINDESTENS_GROSS))
    assert len(klein) <= ERWARTET_KLEIN, (
        "\U0001F534 %d Aufnahmen messen noch 14 px, erwartet ist hoechstens "
        "%d (die\n  Admin-Vorschau ueber den Hash allein - dort oeffnet sich "
        "kein Kiosk, und dort\n  sind 14 px richtig)." % (len(klein),
                                                          ERWARTET_KLEIN))


def test_die_gegenprobe_der_messung_traegt():
    """🔴 Ohne sie beweist die Zahl oben nichts.

    Der Prüfstand setzt neben dem Eingabefeld auch ein einfaches `div` mit
    30 px ein. Bleibt das bei 30, misst er wirklich die berechnete Größe.
    Käme dort ebenfalls 20 heraus, würde er etwas anderes messen als er
    behauptet — und eine 20 im Eingabefeld wäre bedeutungslos.
    """
    l = _laeufe()
    schlecht = [(x.get("rolle"), x.get("ansicht"), x.get("modus"))
                for x in l
                if (x.get("wichtig_probe") or {}).get("div_gegenprobe") != 30]
    assert not schlecht, (
        "\U0001F534 In %d Aufnahmen misst das Gegenproben-div nicht 30 px: "
        "%s\n  Dann misst der Pruefstand nicht die berechnete Groesse, und "
        "die Zahl im\n  Eingabefeld belegt nichts."
        % (len(schlecht), schlecht[:4]))


def test_die_messung_passt_zur_regel_im_quelltext():
    """🔴 Sperrklinke gegen eine veraltete Messung.

    Wer die Pixelzahl in der Regel ändert, ohne am Schirm nachzumessen,
    hinterlässt eine Messdatei, die etwas anderes behauptet als der Code
    tut. Genau diese Form hat am 30.09. drei Befunde als bestehend geführt,
    die längst kuriert waren.
    """
    code = _ohne_kommentare(_text())
    m = re.search(r"html\[data-kiosk\] textarea\{font-size:(\d+)px", code)
    assert m, "\U0001F534 Die Kiosk-Regel ist nicht lesbar."
    im_code = int(m.group(1))
    gemessen = sorted({(x.get("wichtig_probe") or {}).get("input")
                       for x in _laeufe()} - {None, 14})
    assert gemessen == [im_code], (
        "\U0001F534 Die Regel sagt %d px, am Schirm gemessen wurde %s.\n"
        "  Entweder ist die Regel geaendert worden, ohne nachzumessen, oder "
        "eine andere\n  Regel uebersteuert sie. Beides gehoert angesehen.\n"
        "  Lauf: python scripts/kiosk_tafeln_live.py --json "
        "docs/befunde/KIOSK_LIVE.json" % (im_code, gemessen))
