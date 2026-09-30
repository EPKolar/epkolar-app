# -*- coding: utf-8 -*-
"""Zwei Nebenwirkungen meiner eigenen Kuren, gefunden von einem Messagenten.

## N4 — die B1-Kur liess die Attestliste LEER

`MAAttesteSection` wird in „Mein Profil" mit
`workerId:(curUser&&curUser.monteurId)||""` aufgerufen. Die Kennung kann also
**leer** sein.

Mein Vorrangfilter aus v3.9.995 lautete:

    r&&r.worker_id ? String(r.worker_id)===String(workerId) : …Name…

Die Bedingung hing an der **Zeile** - hat die Zeile eine Kennung, wird
verglichen. Bei leerem `workerId` heisst das `String(r.worker_id)===""`, und
das schlaegt fuer **jede** Zeile mit Kennung fehl. Der Namenszweig wird gar
nicht erst erreicht. **Ergebnis: die Attestliste ist leer.** Vorher trug der
Name.

Das ist eine **Regression**, die ich gebaut habe, und sie trifft
Gesundheitsdaten: wer seine eigenen Krankmeldungen ansehen will, sieht
nichts, und nichts sieht aus wie „es gibt keine".

**Die Kur:** den Vorrangzweig nur betreten, wenn ich eine Kennung **habe**.

🔴 **Warum der B1-Riegel gruen blieb:** er prueft die Filterzeile selbst.
Dass ein Aufrufer eine leere Kennung uebergibt, steht 19 000 Zeilen weiter
oben. Beide Enden waren gemessen, die Verbindung dazwischen nicht.

## N7 — zehn Eingabestellen behielten bei `d<=0` den ALTEN Wert

`if(d>0)setAddHours(...)` ohne Gegenzweig: ist `Dauer - Pause` null oder
negativ, bleibt die **vorherige** Stundenzahl im Feld stehen und sieht aus
wie ein gerechneter Wert. Dieselbe Familie wie Z6 (v3.9.991), nur an der
Eingabe.

🔴 **Der Agent meldete zwei Stellen, es waren zehn** - und sie stehen in
**zwei Schreibweisen**: `Math.round(d*2)/2` (halbe Stunden) und
`Math.round(d*100)/100` (zwei Nachkommastellen). Mein erster Anker kannte nur
die erste; `safe_edit` hat abgelehnt und nichts geschrieben, statt vier von
acht zu ersetzen.

🔴 **Bewusst ohne Hinweis an den Nutzer.** Diese Zweige haengen an Zeit- und
Auswahlfeldern, die man beim Suchen mehrfach anfasst. Ein Hinweis je Aenderung
waere genau die Falle aus v3.9.995: was zu oft kommt, wird weggeklickt, und
danach ist auch der echte Fall unsichtbar. Statt dessen steht der wahre Wert
da - null.

**Nebenbefund, nicht kuriert:** dieselbe Eingabe rundet an manchen Stellen auf
halbe Stunden und an anderen auf zwei Nachkommastellen. Welche Stufung gelten
soll, ist eine Entscheidung und keine Messung.
"""
import io
import os
import re

HIER = os.path.dirname(os.path.abspath(__file__))
PFAD = os.path.join(HIER, "..", "index.html")

ERWARTET_N7 = 10


def _text():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _ohne_kommentare(s):
    """🔴 Die Kur-Kommentare zitieren die ALTEN Formen woertlich - sowohl
    `r&&r.worker_id?` als auch `if(d>0)...`. Wer rohen Dateitext durchsucht,
    findet seine eigene Begruendung und haelt sie fuer Code."""
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return re.sub(r"//[^\n]*", "", s)


def test_koeder_die_kommentarbehandlung_traegt():
    mit = "/* HIER STAND if(d>0)setAddHours(x); */ y=1;"
    assert "if(d>0)setAddHours" not in _ohne_kommentare(mit), (
        "Ein Kommentar, der die alte Form zitiert, wird mitgezaehlt - und "
        "dieser Riegel\n  meldete dann einen Befund, den es nicht gibt.")


def test_n4_der_vorrang_braucht_eine_vorhandene_kennung():
    code = _ohne_kommentare(_text())
    assert "filter(r=>r&&r.worker_id?String(r.worker_id)" not in code, (
        "\U0001F534 Die alte Form ist zurueck: die Bedingung haengt wieder an "
        "der ZEILE statt\n  daran, ob eine Kennung zum Vergleichen DA ist. "
        "In \"Mein Profil\" wird\n  `workerId:(curUser&&curUser.monteurId)"
        "||\"\"` uebergeben - bei leerer Kennung\n  ist die Attestliste dann "
        "LEER, und leer sieht aus wie \"es gibt keine\".\n  Gesundheitsdaten.")
    assert "filter(r=>(workerId&&r&&r.worker_id)?String(r.worker_id)" in code, (
        "\U0001F534 Der Schutz gegen die leere Kennung fehlt.")


def test_n4_koeder_der_aufrufer_uebergibt_wirklich_leer():
    """🔴 Gegenprobe zur Praemisse: stimmt sie ueberhaupt?

    Waere die Kennung nie leer, waere die ganze Kur auf eine Behauptung
    gebaut - und der Riegel wuerde etwas festhalten, das nichts bedeutet.
    """
    code = _ohne_kommentare(_text())
    n = code.count('workerId:(curUser&&curUser.monteurId)||""')
    assert n >= 1, (
        "Kein Aufrufer uebergibt eine moeglicherweise leere Kennung mehr. "
        "Dann ist die\n  Begruendung dieses Riegels veraltet - ansehen, nicht "
        "wegzaehlen.")


def test_n7_kein_stiller_verwurf_mehr_an_den_eingaben():
    code = _ohne_kommentare(_text())
    rest = re.findall(r"if\(d>0\)setAddHours\(", code)
    assert not rest, (
        "\U0001F534 %d Stelle(n) verwerfen wieder still: bei `d<=0` bleibt "
        "die VORHERIGE\n  Stundenzahl im Feld stehen und sieht aus wie ein "
        "gerechneter Wert.\n  08:00 bis 09:00 mit einer Stunde Pause ergibt "
        "null Arbeitszeit - im Feld\n  steht dann weiter, was vorher drin "
        "war." % len(rest))


def test_n7_beide_schreibweisen_sind_kuriert():
    """🔴 Zwei Schreibweisen, und mein erster Anker kannte nur eine.

    `Math.round(d*2)/2` und `Math.round(d*100)/100`. Ein Riegel, der nur
    eine kennt, wird gruen, waehrend die Haelfte offen steht.
    """
    code = _ohne_kommentare(_text())
    n = len(re.findall(r"setAddHours\(d>0\?Math\.round\(d\*(?:2\)/2|100\)/100)"
                       r":0\);", code))
    assert n == ERWARTET_N7, (
        "\U0001F534 %d kurierte Stellen, gebucht sind %d.\n"
        "  Weniger heisst: eine ist zurueckgefallen. Mehr heisst: eine ist "
        "dazugekommen -\n  dann gehoert diese Zahl angesehen, nicht "
        "weggezaehlt." % (n, ERWARTET_N7))
    for form in ("Math.round(d*2)/2", "Math.round(d*100)/100"):
        assert ("setAddHours(d>0?%s:0);" % form) in code, (
            "\U0001F534 Die Schreibweise `%s` ist nicht kuriert. Genau so "
            "war mein erster\n  Anker zu eng - er traf vier von acht, und "
            "safe_edit hat zu Recht abgelehnt." % form)


def test_n7_kein_hinweis_an_dieser_stelle():
    """🔴 Gegenprobe zur Kur selbst: sie darf NICHT melden.

    Diese Zweige haengen an Feldern, die man beim Suchen mehrfach anfasst.
    Ein Hinweis je Aenderung waere die Falle aus v3.9.995 - was zu oft kommt,
    wird weggeklickt, und danach ist auch der echte Fall unsichtbar.
    """
    code = _ohne_kommentare(_text())
    for m in re.finditer(r"setAddHours\(d>0\?[^;]{0,40};", code):
        umfeld = code[m.start():m.start() + 200]
        assert "__toast" not in umfeld, (
            "\U0001F534 An einer der Eingabestellen steht jetzt ein Hinweis. "
            "Der feuert bei\n  jeder Zeit- und Pausenaenderung.")
