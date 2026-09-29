# -*- coding: utf-8 -*-
"""Sieht das NEUE Klammertor, was das alte uebersieht? Am echten Text gezeigt.

🔴 WARUM DIESER VERGLEICH NOETIG IST. `klammerbilanz.py` meldet an der heilen
Datei `() 0 / [] 0 / {} 0`, wo der alte `_bracket_check.py` `() -1` meldet.
Zwei Zahlen, und die neue ist die schoenere - das allein ist KEIN Argument.
Ein Tor auszutauschen, weil die neue Zahl gefaelliger aussieht, ist dieselbe
Bewegung wie eine Pruefung anzupassen, damit sie gruen wird.

Das Argument muss sein: **das neue Tor findet einen Fehler, den das alte
nicht findet.** Und zwar nicht in einem Kunsttext, sondern in `index.html`.

WAS HIER PASSIERT
1. Die blinden Zonen des ALTEN Streichers werden bestimmt: seine Treffer, die
   mit einem Backtick beginnen und laenger als 20.000 Zeichen sind. Das sind
   die Stellen, an denen ein Backtick aus einem KOMMENTAR als Ende eines viel
   frueher geoeffneten Vorlagenliterals gelesen wird.
2. In die groesste dieser Zonen wird eine einzelne unpaarige `(` gesetzt -
   an eine Stelle, die der neue, zustandsbasierte Abtaster als CODE fuehrt.
3. Beide Tore laufen ueber die so veraenderte Kopie.

Erwartung, und sie ist die ganze Aussage:
    altes Tor  -> unveraendert, meldet weiter seine Grundlinie
    neues Tor  -> findet die Klammer, mit Zeile

🔴 Die Datei selbst wird NIE veraendert. Gearbeitet wird auf einer Kopie im
Kladdeordner, und die Pruefung am Ende vergleicht den Abdruck des Originals
vor und nach dem Lauf.
"""
import hashlib
import io
import os
import re
import subprocess
import sys
import tempfile

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
WURZEL = os.path.dirname(HIER)

import code_scan          # noqa: E402
import klammerbilanz      # noqa: E402

ORIGINAL = os.path.join(WURZEL, "index.html")

# Die Musterreihe des ALTEN Streichers, unveraendert abgeschrieben.
ALTE_MUSTER = [
    r'"(?:[^"\\]|\\.)*"',
    r"'(?:[^'\\]|\\.)*'",
    r"`(?:[^`\\]|\\.)*`",
    r"/\*[\s\S]*?\*/",
    r"//[^\n]*",
]


def blinde_zonen(text, mindest=20000):
    """Treffer des alten Streichers, die mit einem Backtick beginnen und
    laenger als `mindest` sind - seine blinden Zonen."""
    aus = []
    for m in re.finditer("|".join(ALTE_MUSTER), text):
        if m.group(0).startswith("`") and (m.end() - m.start()) >= mindest:
            aus.append((m.start(), m.end()))
    return aus


def _codestelle_in(text, von, bis, aus):
    """Eine Stelle in [von,bis), die der neue Abtaster als Code fuehrt.

    Gesucht wird ein Semikolon: dahinter eine Klammer einzusetzen ist
    syntaktisch harmlos genug, um den Fund eindeutig der Klammer und nicht
    einer Folgewirkung zuzuschreiben.
    """
    for i in range(von + 200, min(bis, len(text)) - 200):
        if text[i] == ";" and aus[i]:
            return i + 1
    return -1


def main(argv):
    text = io.open(ORIGINAL, encoding="utf-8", newline="").read()
    vorher = hashlib.md5(text.encode("utf-8")).hexdigest()
    aus, _v = klammerbilanz.maske(text)

    zonen = blinde_zonen(text)
    gesamt = sum(b - a for a, b in zonen)
    print("Blinde Zonen des ALTEN Streichers: %d Treffer, %d Zeichen "
          "(%.1f %% der Datei)"
          % (len(zonen), gesamt, 100.0 * gesamt / len(text)))
    if not zonen:
        print("\U0001F534 KEINE blinde Zone gefunden. Das ist kein Ergebnis - "
              "entweder ist der\n   alte Streicher repariert worden, oder "
              "dieser Sucher greift daneben.")
        return 2

    zonen.sort(key=lambda z: z[1] - z[0], reverse=True)
    von, bis = zonen[0]
    print("   groesste Zone: Zeile %d bis %d, %d Zeichen"
          % (text.count("\n", 0, von) + 1, text.count("\n", 0, bis) + 1,
             bis - von))

    stelle = _codestelle_in(text, von, bis, aus)
    if stelle < 0:
        print("\U0001F534 In der groessten blinden Zone liegt keine Stelle, "
              "die der neue Abtaster\n   als Code fuehrt. Dann laesst sich "
              "der Unterschied dort nicht zeigen.")
        return 2
    print("   Klammer wird gesetzt in Zeile %d\n"
          % (text.count("\n", 0, stelle) + 1))

    kopie = os.path.join(tempfile.gettempdir(), "__klammerprobe.html")
    io.open(kopie, "w", encoding="utf-8", newline="").write(
        text[:stelle] + "(" + text[stelle:])
    try:
        alt = subprocess.run([sys.executable, os.path.join(
            HIER, "_bracket_check.py"), kopie], capture_output=True, text=True)
        neu = subprocess.run([sys.executable, os.path.join(
            HIER, "klammerbilanz.py"), kopie], capture_output=True, text=True)
    finally:
        if os.path.exists(kopie):
            os.remove(kopie)

    alt_txt = (alt.stdout or "").strip()
    print("ALTES Tor (_bracket_check.py), Rueckgabe %d:" % alt.returncode)
    for z in alt_txt.splitlines():
        print("   " + z)
    print("\nNEUES Tor (klammerbilanz.py), Rueckgabe %d:" % neu.returncode)
    for z in (neu.stdout or "").strip().splitlines()[-8:]:
        print("   " + z)

    nachher = hashlib.md5(
        io.open(ORIGINAL, encoding="utf-8", newline="").read()
        .encode("utf-8")).hexdigest()
    print("\nindex.html unveraendert: %s" % ("ja" if vorher == nachher
                                             else "\U0001F534 NEIN"))
    if vorher != nachher:
        return 2

    alt_blind = alt.returncode == 0
    neu_sieht = neu.returncode == 1
    print()
    if alt_blind and neu_sieht:
        print("\U0001F7E2 DAS IST DAS ARGUMENT: eine einzelne unpaarige "
              "Klammer in echtem Code -\n   das alte Tor bleibt GRUEN, das "
              "neue findet sie mit Zeile.")
        return 0
    if not alt_blind:
        print("\U0001F7E1 Das alte Tor hat die Klammer auch gefunden. An "
              "DIESER Stelle ist es\n   nicht blind - der Vergleich belegt "
              "hier nichts.")
        return 1
    print("\U0001F534 Das NEUE Tor hat sie NICHT gefunden. Dann ist es keine "
          "Verbesserung.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
