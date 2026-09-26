# -*- coding: utf-8 -*-
"""Trennt CODE von KOMMENTAR und ZEICHENKETTE - richtig, nicht ungefaehr.

WARUM ES DIESES MODUL GIBT (26.09.2026)
──────────────────────────────────────
Ich habe Sebastian berichtet, im Code stehe kein `ww<600` mehr. Das war
FALSCH, und er hat es gefunden, indem er eine dieser Zeilen hereinkopiert:

    function WerkzeugView(...){ const isMob=ww<600; ...

Die Ursache war mein Zaehler, nicht der Code. Er suchte Blockkommentare mit

    re.finditer(r"/\\*[\\s\\S]*?\\*/", s)

und hielt damit jedes `/*` fuer einen Kommentaranfang - auch das in

    accept:"application/pdf,image/*"

Dieses `/*` wird nie geschlossen. Alles dahinter galt meinem Zaehler als
Kommentar, also die letzten ~80 kB der Datei mitsamt WerkzeugView. Er meldete
0 statt 1 - und ein Zaehler, der zu WENIG findet, meldet ein gruenes Ergebnis.

Drei Verfahren hatten mir vorher schon drei verschiedene Zahlen geliefert
(31 roh, 28 ueber nur_code, 13 ueber Zitatpaarung). Dass keine davon stimmte,
haette mir das Auseinanderlaufen sagen muessen.

WAS DIESES MODUL ANDERS MACHT
─────────────────────────────
Es laeuft EINMAL durch den Text und fuehrt einen Zustand mit: Code,
einfache/doppelte Zeichenkette, Vorlagenliteral, Zeilenkommentar,
Blockkommentar. Ein `/*` in einer Zeichenkette kann damit keinen Kommentar
eroeffnen, und ein `"` in einem Kommentar keine Zeichenkette.

Regulaere Ausdruecke (`/.../`) werden NICHT als eigener Zustand gefuehrt -
das braeuchte einen Parser, weil `/` auch Division ist. Stattdessen wird eine
vermutete Regex-Literal-Stelle als Code behandelt; das ist die sichere
Richtung, denn ein Fund zu viel laesst sich ansehen, ein Fund zu wenig nicht.

BENUTZUNG
─────────
    from code_scan import nur_code_stellen, ist_code

    for pos in nur_code_stellen(text, "ww<600"):
        ...                      # nur echte Code-Treffer

    ist_code(text)[i]            # True, wenn Zeichen i Code ist

AUFRUF VON HAND
───────────────
    python scripts/code_scan.py "ww<600"
    python scripts/code_scan.py "ww<600" --alle
"""
import io
import os
import re
import sys

CODE, EINF, DOPP, VORL, ZEILE, BLOCK = range(6)


def ist_code(text):
    """Bytefeld gleicher Laenge: True, wo das Zeichen CODE ist."""
    n = len(text)
    aus = bytearray(n)
    zustand = CODE
    i = 0
    while i < n:
        c = text[i]
        if zustand == CODE:
            # REGEX-LITERAL. Ohne diesen Zweig reisst ein Ausdruck wie
            # /['"]/ oder /`/ den Abtaster aus dem Tritt: das
            # Anfuehrungszeichen darin eroeffnet eine Zeichenkette, die nie
            # geschlossen wird, und alles dahinter gilt als Zeichenkette.
            # Genau daran ist die erste Fassung gescheitert (7 von 22).
            # Ob ein / eine Division oder ein Regex-Anfang ist, entscheidet
            # das letzte bedeutsame Zeichen davor - nach ( , = : [ ! & | ? {
            # } ; oder einem Schluesselwort kann kein Divisor stehen.
            if c == "/" and i + 1 < n and text[i + 1] not in "*/":
                k = i - 1
                while k >= 0 and text[k] in " \t\r\n":
                    k -= 1
                davor = text[k] if k >= 0 else "("
                wort = text[max(0, k - 9):k + 1]
                if davor in "(,=:[!&|?{};+-~^%<>" or wort.endswith(
                        ("return", "typeof", "case", "in", "of", "new",
                         "delete", "void", "instanceof")):
                    # Das Ende suchen, DANN entscheiden - der erste Anlauf
                    # hat die Entscheidung in die Schleife gemischt und sich
                    # dabei aufgehaengt.
                    j = i + 1
                    in_klasse = False
                    ende = -1
                    while j < n:
                        d = text[j]
                        if d == "\\":
                            j += 2
                            continue
                        if d == "\n":
                            break          # unbeendet -> war doch keine Regex
                        if d == "[":
                            in_klasse = True
                        elif d == "]":
                            in_klasse = False
                        elif d == "/" and not in_klasse:
                            ende = j
                            break
                        j += 1
                    if ende >= 0:
                        for x in range(i, ende + 1):
                            aus[x] = 1
                        i = ende + 1
                        continue
                    # Doch kein Regex-Literal: das / ist eine Division.
                    aus[i] = 1
                    i += 1
                    continue
            if c == "/" and i + 1 < n and text[i + 1] == "*":
                zustand = BLOCK
                i += 2
                continue
            if c == "/" and i + 1 < n and text[i + 1] == "/":
                zustand = ZEILE
                i += 2
                continue
            if c == "'":
                zustand = EINF
            elif c == '"':
                zustand = DOPP
            elif c == "`":
                zustand = VORL
            else:
                aus[i] = 1
            i += 1
            continue
        if zustand == BLOCK:
            if c == "*" and i + 1 < n and text[i + 1] == "/":
                zustand = CODE
                i += 2
                continue
            i += 1
            continue
        if zustand == ZEILE:
            if c == "\n":
                zustand = CODE
                aus[i] = 1
            i += 1
            continue
        # in einer Zeichenkette
        if c == "\\":
            i += 2
            continue
        if (zustand == EINF and c == "'") or (zustand == DOPP and c == '"') \
                or (zustand == VORL and c == "`"):
            zustand = CODE
        elif zustand == VORL and c == "$" and i + 1 < n and text[i + 1] == "{":
            # Vorlagenliteral mit eingebettetem Ausdruck: der Inhalt IST Code.
            # Vereinfachung: bis zur passenden schliessenden Klammer als Code
            # markieren. Verschachtelte Vorlagen darin sind selten und werden
            # dann konservativ als Code gelesen - die sichere Richtung.
            tiefe = 0
            j = i + 1
            while j < n:
                if text[j] == "{":
                    tiefe += 1
                elif text[j] == "}":
                    tiefe -= 1
                    if tiefe == 0:
                        break
                aus[j] = 1
                j += 1
            i = j + 1
            continue
        i += 1
    return aus


EICHPROBE = [
    # (Muster, Anzahl, die im CODE stehen MUSS)
    # Grundgesamtheit, die sich nachrechnen laesst: jede ww<BP_MOB-Stelle ist
    # Code - in Kommentaren steht BP_MOB nur als Wort, nie als Vergleich.
    ("const isMob=ww<BP_MOB", None),
]


def eichen(text):
    """Prueft den Abtaster an einer Menge, deren Antwort bekannt ist.

    WARUM DAS HIER STEHT
    ────────────────────
    Die erste Fassung dieses Moduls hat 8 von 27 ww<BP_MOB-Stellen als Code
    erkannt und 19 als Zeichenkette - und dabei nicht gemeldet, dass etwas
    faul ist. Ein Abtaster, der zu WENIG findet, liefert ein gruenes
    Ergebnis: "kommt im Code nicht vor" sieht genauso aus wie "ist
    aufgeraeumt".

    Die Probe ist einfach: `const isMob=ww<...` ist immer eine Deklaration,
    also immer Code. Findet der Abtaster eine davon NICHT im Code, irrt er
    sich - und dann verweigert er die Auskunft, statt eine Zahl zu nennen,
    der man nicht trauen kann.

    Gibt (bestanden, gefunden, erwartet) zurueck.
    """
    feld = ist_code(text)
    stellen = [m.start() for m in re.finditer(r"const isMob\s*=\s*ww\s*<", text)]
    # Von diesen sind die in Changelog-Kommentaren abzuziehen. Statt sie zu
    # erraten: eine Deklaration steht IMMER hinter einem { oder ; oder einer
    # Zeilengrenze - im Kommentar steht davor Prosa.
    echte = [p for p in stellen
             if re.search(r"[{};]\s*$", text[max(0, p - 60):p])]
    gefunden = sum(1 for p in echte if feld[p])
    # EINE LEERE GRUNDGESAMTHEIT BESTEHT KEINE PROBE.
    # Der Koeder in tests/test_code_scan_v936.py hat genau das gefunden: mit
    # einem blind gemachten Abtaster war `echte` leer, und 0 == 0 galt als
    # bestanden. Eine Probe, die bei ausgefallener Messung gruen wird, ist
    # dieselbe Fehlerform, gegen die dieses Modul ueberhaupt gebaut wurde.
    if len(echte) < 5:
        return (False, gefunden, len(echte))
    return (gefunden == len(echte), gefunden, len(echte))


def nur_code_stellen(text, muster, regex=False):
    """Positionen, an denen `muster` im CODE steht - nach bestandener Eichung.

    Schlaegt die Eichung fehl, wird GEWORFEN statt gezaehlt. Eine Zahl aus
    einem nachweislich irrenden Abtaster ist schlimmer als keine.
    """
    ok, gef, erw = eichen(text)
    if not ok:
        raise SystemExit(
            "code_scan: EICHUNG GESCHEITERT - %d von %d isMob-Deklarationen "
            "als Code erkannt.\n"
            "  Der Abtaster irrt sich und nennt deshalb keine Zahl. Ein "
            "Abtaster, der zu wenig\n"
            "  findet, meldet ein gruenes Ergebnis - genau daran ist die "
            "erste Fassung dieses\n"
            "  Moduls gescheitert (8 von 27)." % (gef, erw))
    feld = ist_code(text)
    pat = re.compile(muster if regex else re.escape(muster))
    return [m.start() for m in pat.finditer(text) if feld[m.start()]]


def alle_stellen(text, muster, regex=False):
    """(pos, ist_code) fuer jeden Treffer - auch die in Kommentaren.

    Verweigert ebenfalls bei gescheiterter Eichung: sonst haette die
    Auskunftssperre ein Loch, durch das genau die Zahl kaeme, der man nicht
    trauen darf. Die erste Fassung hatte dieses Loch.
    """
    ok, gef, erw = eichen(text)
    if not ok:
        raise SystemExit(
            "code_scan: EICHUNG GESCHEITERT - %d von %d isMob-Deklarationen "
            "als Code erkannt. Keine Zahl." % (gef, erw))
    feld = ist_code(text)
    pat = re.compile(muster if regex else re.escape(muster))
    return [(m.start(), bool(feld[m.start()])) for m in pat.finditer(text)]


def _komponente(text, pos):
    vor = text[:pos]
    best, name = -1, "?"
    for pat in (r"function\s+([A-Za-z_]\w*)\s*\(",
                r"const\s+([A-Z]\w+)\s*=\s*\("):
        t = list(re.finditer(pat, vor))
        if t and t[-1].start() > best:
            best, name = t[-1].start(), t[-1].group(1)
    return name


def main(argv):
    if not argv:
        raise SystemExit('Aufruf: python scripts/code_scan.py "<muster>" [--alle]')
    muster = argv[0]
    wurzel = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    text = io.open(os.path.join(wurzel, "index.html"),
                   encoding="utf-8", newline="").read()
    treffer = alle_stellen(text, muster)
    if not treffer:
        print("%r kommt nirgends vor. Das ist KEIN gruenes Ergebnis - pruefe "
              "das Muster." % muster)
        return 1
    code = [p for p, k in treffer if k]
    rest = [p for p, k in treffer if not k]
    print("%r: %d Treffer gesamt | %d im CODE | %d in Kommentar/Zeichenkette"
          % (muster, len(treffer), len(code), len(rest)))
    print()
    for p in code:
        u = re.sub(r"\s+", " ", text[max(0, p - 90):p + 60])
        print("  CODE      %-9d %-16s %s"
              % (p, _komponente(text, p), u.encode("ascii", "replace").decode()))
    if "--alle" in argv:
        print()
        for p in rest:
            u = re.sub(r"\s+", " ", text[max(0, p - 70):p + 50])
            print("  sonstiges %-9d %s"
                  % (p, u.encode("ascii", "replace").decode()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
