# -*- coding: utf-8 -*-
"""Vier Kuren aus der Bughunt-Nacht auf den 30.09.2026.

## Z1 — Kalenderjahr neben ISO-Kalenderwoche

`new Date().getFullYear()` stand an zwei Stellen direkt neben `isoW()`.
Beide fallen an **20 von 4380 Tagen** (2024-2035) auseinander - zuletzt am
29.12.2025, als naechstes am 31.12.2026 und 1./2.1.2027. An diesen Tagen
zeigte die Ansicht eine Woche aus einem **anderen Jahr** (+371 bzw. -364
Tage), und wer dort buchte, schrieb das Datum in dieses andere Jahr, mit
gruenem Erfolgs-Toast.

🔴 **Von fuenf Vorkommen sind DREI richtig und bleiben.** Sie filtern
`finkzeit` nach Kalenderjahr oder bauen ein Monatsgitter - dort ist
`getFullYear()` das Richtige. Wer alle fuenf blind ersetzt haette, haette
die Lohndaten-Filter kaputtgemacht.

## Z3 — die Team-Zeitachse zaehlte ab Mittag eine Woche zu viel

Zweifach falsch: der Versatzterm hob sich auf (nach `setDate(...+3)` **ist**
`t2` der Donnerstag, also ist `(t2.getDay()+6)%7` immer 3), und `startMon`
nullte die Uhrzeit nicht - `Math.round` kippte ab Mittag.

Geprueft gegen `isoWof` **derselben Datei** (abgeschrieben, nicht
nachgebaut), 38 353 Zeitpunkte 2024-2038 mit je sieben Uhrzeiten:

    alte Fassung  {"2027":1231,"2028":8,"2038":1231}
    neue Fassung  {}

Ein absichtlich kaputter Koeder (immer KW+1) faellt in **1008 von 1008**
Faellen auf - die Null ist damit belegt und nicht bloss leer.

## D3 — ein Foto konnte lautlos verschwinden

`compressPhoto` wirft belegbar. **Vier** von zehn Aufrufen riefen `.then()`
ohne `.catch`: der Dialog schloss, nichts passierte, keine Meldung - und der
Mangel wurde **ohne Nachweisfoto** gespeichert.

🔴 Der Messagent meldete drei; es sind vier. Den Plan-Upload hatte er nicht.
Selbst nachgezaehlt, bevor gebaut wurde.

## B3 — der Helfer ueberschrieb die Grenze des Aufrufers

`_sbGet`/`_sbGetOrder` haengten `limit=5000` bedingungslos an. Der
Lieferantenkatalog fordert ausdruecklich 10 000; die Adresse trug danach
zwei `limit`-Parameter, und der des Helfers stand zuletzt.

🔴 `_sbGetAnon` bleibt bewusst unangetastet - er kappt **zweifach**, auch per
`Range`-Kopfzeile. Dort eine bedingte Grenze einzubauen waere irrefuehrend.
"""
import io
import os
import re

HIER = os.path.dirname(os.path.abspath(__file__))
PFAD = os.path.join(HIER, "..", "index.html")

# Z1: drei Kalenderjahr-Stellen sind richtig und bleiben.
ERWARTET_KALENDERJAHR = 3


def _text():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _ohne_kommentare(s):
    """🔴 Die Kur-Kommentare zitieren die alte Form. Wer den rohen Text
    durchsucht, misst seine eigene Begruendung mit."""
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return re.sub(r"//[^\n]*", "", s)


def test_koeder_die_kommentarbehandlung_traegt():
    """🔴 Ohne diese Probe waere jede Zahl unten falsch."""
    mit = "/* HIER STAND new Date().getFullYear() */ const yr=isoWY();"
    assert "getFullYear" not in _ohne_kommentare(mit), (
        "Ein Kommentar, der die alte Form zitiert, wird mitgezaehlt.")
    assert "isoWY" in _ohne_kommentare(mit), (
        "Die Kommentarentfernung frisst auch den Code - dann misst hier "
        "nichts mehr.")


def test_z1_nur_die_drei_richtigen_kalenderjahre_bleiben():
    code = _ohne_kommentare(_text())
    n = code.count("const yr=new Date().getFullYear();")
    assert n == ERWARTET_KALENDERJAHR, (
        "%d Stellen setzen `yr` auf das KALENDERjahr, erwartet sind %d.\n"
        "  MEHR heisst: eine ISO-Wochen-Stelle ist zurueckgefallen - dann "
        "zeigt sie am\n  Jahreswechsel eine Woche aus einem anderen Jahr, "
        "und Buchungen landen dort.\n  WENIGER heisst: ein "
        "`finkzeit`-Jahresfilter oder ein Monatsgitter ist auf das\n  "
        "ISO-Wochenjahr umgestellt worden - das waere falsch herum."
        % (n, ERWARTET_KALENDERJAHR))


def test_z1_die_beiden_iso_stellen_rechnen_mit_dem_wochenjahr():
    code = _ohne_kommentare(_text())
    n = code.count("const yr=isoWY();")
    assert n >= 2, (
        "Nur %d Stellen setzen `yr` auf das ISO-Wochenjahr, erwartet sind "
        "mindestens 2\n  (ProjectShell und VZeit). Beide reichen `yr` "
        "zusammen mit einer ISO-Woche\n  weiter bzw. rechnen selbst damit." % n)


def test_z3_der_versatzterm_ist_weg():
    code = _ohne_kommentare(_text())
    assert "(t2.getDay()+6)%7+3)/7" not in code, (
        "Der alte Versatzterm ist zurueck. Er hebt sich auf - nach "
        "`setDate(...+3)` IST t2\n  der Donnerstag - und die Zeitachse "
        "zaehlte 2027 an 362 Tagen ab Mittag eine\n  Woche zu viel.")
    assert "don1.setDate(jan4.getDate()-((jan4.getDay()+6)%7)+3)" in code, (
        "Die korrigierte Rechnung ist weg. Beide Enden muessen Donnerstage "
        "sein, dann ist\n  die Differenz ein exaktes Vielfaches von sieben "
        "Tagen.")


def test_z3_die_zeitachse_beginnt_um_mitternacht():
    code = _ohne_kommentare(_text())
    i = code.find("const startMon=")
    assert i > 0, "`startMon` ist nicht mehr zu finden."
    assert "setHours(0,0,0,0)" in code[i:i + 320], (
        "`startMon` nullt die Uhrzeit nicht mehr. Dann tragen alle Tage der "
        "Zeitachse die\n  aktuelle Uhrzeit, und die Wochenrechnung kippt ab "
        "Mittag.")


def test_d3_jeder_fotoaufruf_meldet_einen_fehler():
    """🔴 Die Klassenregel: kein `compressPhoto(...).then(` ohne Absicherung.

    Gemessen wird am Aufrufmuster, nicht an vier Orten. Wer einen fuenften
    Aufruf dazulegt und ihn ungesichert laesst, wird rot.
    """
    code = _ohne_kommentare(_text())
    offen = []
    for m in re.finditer(r"compressPhoto\(", code):
        # Die Definition selbst zaehlt nicht.
        if code[max(0, m.start() - 20):m.start()].rstrip().endswith("function"):
            continue
        rest = code[m.start():m.start() + 400]
        if ".then(" in rest and ".catch" not in rest:
            vor = code[max(0, m.start() - 12):m.start()]
            if "await" not in vor:
                offen.append(code.count("\n", 0, m.start()) + 1)
    assert not offen, (
        "%d Aufrufe von `compressPhoto` haengen ein `.then()` ohne `.catch` "
        "an (Zeile %s).\n  `compressPhoto` wirft bei einem HEIC vom iPhone in "
        "Android-Chrome und bei einer\n  abgebrochenen Kameradatei. Dann "
        "schliesst der Dialog, nichts passiert, keine\n  Meldung - und der "
        "Mangel wird OHNE Nachweisfoto gespeichert.\n  Benutze "
        "`_fotoAufbereiten(...)`: es meldet und reicht den Fehler weiter."
        % (len(offen), offen))


def test_d3_der_helfer_meldet_dem_nutzer():
    t = _text()
    i = t.find("function _fotoAufbereiten(")
    assert i > 0, "`_fotoAufbereiten` ist weg - dann sind die Aufrufe wieder "\
                  "ungesichert."
    rumpf = t[i:i + 900]
    assert "__toast" in rumpf, (
        "`_fotoAufbereiten` meldet dem NUTZER nichts - es schreibt nur in "
        "die Konsole.\n  Genau das war der Befund.")
    assert "Promise.reject" in rumpf, (
        "`_fotoAufbereiten` verschluckt den Fehler. Dann laeuft das `.then` "
        "mit `undefined`\n  weiter und es entsteht ein Vorschaubild aus dem "
        "Nichts.")


def test_b3_die_grenze_des_aufrufers_gewinnt():
    code = _ohne_kommentare(_text())
    n = code.count('hatGrenze?"":"limit=5000"')
    assert n == 2, (
        "%d der beiden Leser respektieren die Grenze des Aufrufers, "
        "erwartet sind 2.\n  Ohne das traegt die Adresse zwei "
        "limit-Parameter, und der des Helfers steht\n  zuletzt - der "
        "Lieferantenkatalog fordert ausdruecklich 10000 und bekaeme 5000."
        % n)
    # 🔴 Gegenprobe: der Aufrufer, um den es geht, fordert weiterhin mehr.
    assert "&limit=10000" in code, (
        "Der Aufruf mit `limit=10000` ist weg. Dann misst die Pruefung "
        "darueber nichts mehr.")
