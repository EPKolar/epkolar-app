# -*- coding: utf-8 -*-
"""Klammerbilanz von index.html - zustandsbasiert statt per Streichmuster.

🔴 WARUM ES DEN ALTEN `_bracket_check.py` ABLOESEN SOLL (Frage 15).

Der alte Streicher ist eine Reihe von regulaeren Ausdrucken, und das
Vorlagenliteral-Muster (`` `…` ``) steht VOR dem Kommentarmuster. Diese Datei
zitiert in Kommentaren mit Backticks - jeder einzelne davon wird als ENDE
eines viel frueher geoeffneten Vorlagenliterals gelesen. Ein Treffer lief ueber
375.741 Zeichen echten Code und nahm dessen Klammern mit aus der Bilanz.

Gemessen am heilen Stand: der alte Streicher beurteilt **27,9 %** der Datei.
Die Grundlinie `() -1` ist damit die Restsumme dessen, was uebrig blieb -
keine Aussage ueber die Klammern des Codes.

Dieses Werkzeug benutzt `code_scan.ist_code` - denselben zustandsbasierten
Abtaster, der schon fuenf andere Riegel traegt und eine Eichprobe bestehen
muss. Er kennt Zeichenketten, Kommentare, Vorlagenliterale UND
Regex-Literale, und ein Backtick in einem Kommentar kann ihn nicht aus dem
Tritt bringen.

🔴 EINE ASYMMETRIE MUSSTE DAFUER ERST GEFUNDEN WERDEN, und sie haette das
Ergebnis still verfaelscht. Bei `${…}` in einem Vorlagenliteral markiert
`ist_code` die OEFFNENDE Klammer als Code, die schliessende aber nicht:

    while j < n:
        if text[j] == "{": tiefe += 1
        elif text[j] == "}":
            tiefe -= 1
            if tiefe == 0: break      # <- bricht VOR `aus[j] = 1`
        aus[j] = 1

Das sind in `index.html` genau **561** Stellen, also ein Fehlbetrag von +561
in der Geschweiften-Bilanz. `ist_code` wird deshalb NICHT geaendert - es
traegt andere Riegel, und eine gemeinsame Quelle anzufassen, um das eigene
Ergebnis schoener zu machen, ist die falsche Bewegung. Stattdessen wird die
Stelle hier erkannt und die eine Klammer uebersprungen.

WAS DIESES WERKZEUG ZUSAETZLICH KANN: es sagt, WO. Der alte gibt drei Zahlen
aus; bei `() -1` weiss niemand, welche Klammer gemeint ist. Hier laeuft ein
Stapel mit, und jede unpaarige Klammer wird mit Zeile und Umgebung genannt.

Aufruf:
    python scripts/klammerbilanz.py            # index.html
    python scripts/klammerbilanz.py <datei>
"""
import io
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
WURZEL = os.path.dirname(HIER)

import code_scan  # noqa: E402

PAARE = {"(": ")", "[": "]", "{": "}"}
ZU_AUF = {v: k for k, v in PAARE.items()}
MINDESTGROESSE = 1_000_000


def maske(text):
    """(Code-Maske, Zahl der uebersprungenen Vorlagen-Klammern).

    Die uebersprungenen sind die oeffnenden `{` von `${…}`: ihr Partner ist
    von `ist_code` nicht als Code markiert, sie wuerden also als unpaarig
    gezaehlt. Sie werden hier aus der Maske genommen, nicht von der Summe
    abgezogen - dann stimmt auch der Ort, nicht nur die Zahl.

    🔴 UND SIE SETZT DIE ASYMMETRIE NICHT VORAUS. Der erste Entwurf hat jede
    `${`-Oeffnung blind aus der Maske genommen. Das waere ein Riegel, der vom
    FORTBESTEHEN des Mangels lebt: wuerde `code_scan` eines Tages auch die
    schliessende Klammer markieren - die richtige Verbesserung -, zoege dieses
    Werkzeug 561 Klammern zu viel ab und meldete -561, also rot wegen einer
    Reparatur woanders. Deshalb wird JE STELLE nachgesehen, ob der Partner
    wirklich fehlt.
    """
    aus = bytearray(code_scan.ist_code(text))
    n = len(text)
    weg = 0
    for i in range(n - 1):
        if not (text[i] == "$" and text[i + 1] == "{"
                and not aus[i] and aus[i + 1]):
            continue
        # Den Partner suchen - dieselbe Vereinfachung wie in `code_scan`:
        # rohe Klammerzaehlung innerhalb der Einbettung.
        tiefe, j = 0, i + 1
        while j < n:
            if text[j] == "{":
                tiefe += 1
            elif text[j] == "}":
                tiefe -= 1
                if tiefe == 0:
                    break
            j += 1
        if j < n and not aus[j]:
            # Der Partner ist NICHT als Code gefuehrt - also die Oeffnung
            # ebenfalls herausnehmen, sonst steht sie unpaarig da.
            aus[i + 1] = 0
            weg += 1
    return aus, weg


def bilanz(text, aus=None):
    """(Bilanz je Art, Liste der unpaarigen Stellen).

    Der Stapel macht den Unterschied zur blossen Differenz: `(]` hat die
    Differenz 0 und ist trotzdem falsch.
    """
    if aus is None:
        aus, _ = maske(text)
    stapel = []
    fehler = []          # (position, zeichen, grund)
    zahl = {k: 0 for k in PAARE}
    for i, c in enumerate(text):
        if not aus[i]:
            continue
        if c in PAARE:
            stapel.append((i, c))
            zahl[c] += 1
        elif c in ZU_AUF:
            zahl[ZU_AUF[c]] -= 1
            if not stapel:
                fehler.append((i, c, "schliesst, ohne dass etwas offen ist"))
            elif stapel[-1][1] != ZU_AUF[c]:
                j, auf = stapel.pop()
                fehler.append((i, c, "schliesst ein %r von Zeile %d"
                               % (auf, text.count("\n", 0, j) + 1)))
            else:
                stapel.pop()
    for i, c in stapel:
        fehler.append((i, c, "wird nie geschlossen"))
    return zahl, fehler


def _umgebung(text, i, n=60):
    a = max(0, i - n)
    return text[a:i + n].replace("\n", " ")


def eichen():
    """🔴 Drei Koeder und zwei Gegenproben. Ohne sie ist jede Null wertlos.

    Der wichtigste ist der zweite: ein BACKTICK IN EINEM KOMMENTAR darf das
    Ergebnis nicht bewegen. Genau daran ist der alte Streicher gescheitert,
    und ein neuer, der denselben Fehler macht, waere keine Verbesserung -
    er saehe nur anders aus.
    """
    schief = []

    gut = "function a(){ return [1,2].map(x=>({x})); }"
    z, f = bilanz(gut, bytearray([1] * len(gut)))
    if f or any(z.values()):
        schief.append("Ein ausgeglichener Text wird als falsch gemeldet: "
                      "%r %r" % (z, f))

    for fehlend, art in (("function a(){ return (1; }", "("),
                         ("var x = [1,2;", "["),
                         ("function a(){ return 1;", "{")):
        z, f = bilanz(fehlend, bytearray([1] * len(fehlend)))
        if not f:
            schief.append("Eine fehlende %r-Klammer wird NICHT gefunden: %r"
                          % (art, fehlend))

    kreuz = "function a(){ return (1]; }"
    _z, f = bilanz(kreuz, bytearray([1] * len(kreuz)))
    if not any("schliesst ein" in g for _i, _c, g in f):
        schief.append("`(]` wird nicht als Kreuzung erkannt - die blosse "
                      "Differenz waere 0 und saehe gesund aus.")

    # 🔴 DER ENTSCHEIDENDE: Backtick im Kommentar.
    ohne = "var a = (1);\nvar b = (2);\n"
    mit = "var a = (1);\n/* zitiert `foo` so */\nvar b = (2);\n"
    z1, _ = bilanz(ohne)
    z2, _ = bilanz(mit)
    if z1 != z2:
        schief.append("Ein Backtick im Kommentar bewegt das Ergebnis "
                      "(%r gegen %r). Genau daran ist der alte Streicher "
                      "gescheitert." % (z1, z2))

    # Gegenprobe: ein Backtick, der WIRKLICH ein Vorlagenliteral eroeffnet,
    # muss weiterhin wirken - sonst ist der Abtaster nicht besser, nur blind
    # in die andere Richtung.
    vorlage = "var s = `text ( ohne Partner`;\nvar b = (2);\n"
    z3, f3 = bilanz(vorlage)
    if f3 or z3["("] != 0:
        schief.append("Eine Klammer INNERHALB eines echten Vorlagenliterals "
                      "wird mitgezaehlt: %r %r" % (z3, f3))
    return schief


def main(argv):
    schief = eichen()
    print("Eichung: 6 Proben (davon eine zum Backtick im Kommentar)")
    if schief:
        for s in schief:
            print("   \U0001F534 " + s)
        print("\nNICHT GEMESSEN. Ein ungeeichter Abtaster meldet eine Bilanz, "
              "die von einer\nechten nicht zu unterscheiden ist.")
        return 2
    print("   \U0001F7E2 alle sechs richtig\n")

    ziel = argv[0] if argv else os.path.join(WURZEL, "index.html")
    text = io.open(ziel, encoding="utf-8", newline="").read()

    # v3.9.894 LEBENSZEICHEN, uebernommen aus `_bracket_check.py`: eine LEERE
    # Datei hat ausgeglichene Klammern. Wer nur auf die Zahlen sieht, haelt
    # den Totalverlust fuer eine Verbesserung.
    if len(text) < MINDESTGROESSE:
        print("%s ist nur %d Zeichen gross - das ist Datenverlust, keine "
              "Klammerbilanz.\nNICHT committen: git checkout -- %s"
              % (os.path.basename(ziel), len(text), os.path.basename(ziel)))
        return 1

    aus, vorlagen = maske(text)
    anteil = 100.0 * sum(aus) / len(text)
    zahl, fehler = bilanz(text, aus)
    print("%s: %d Zeichen, davon %.1f %% als Code beurteilt"
          % (os.path.basename(ziel), len(text), anteil))
    print("   (%d Vorlagen-Einbettungen `${` uebersprungen - siehe Kopftext)"
          % vorlagen)
    for auf, zu in sorted(PAARE.items()):
        print("   %s%s %+d" % (auf, zu, zahl[auf]))

    if not fehler:
        print("\n\U0001F7E2 Jede Klammer hat ihren Partner. Kein Fehlbetrag, "
              "keine Kreuzung.")
        return 0
    print("\n\U0001F534 %d unpaarige Klammern:" % len(fehler))
    for i, c, grund in fehler[:20]:
        print("   Zeile %-7d %r %s\n      ...%s..."
              % (text.count("\n", 0, i) + 1, c, grund, _umgebung(text, i)))
    return 1


if __name__ == "__main__":
    # v3.9.995: DIE KONSOLE VERTRAEGT NICHT JEDES ZEICHEN. Auf Windows
    # laeuft sie auf cp1252; ein Symbol in der Ausgabe beendet das Tor
    # dann mit einem UnicodeEncodeError - und zwar oft auf dem
    # ERFOLGSZWEIG, beim Hinschreiben des gruenen Punktes. Die Torkette
    # liest den Rueckgabewert und meldet ROT, obwohl die Messung selbst
    # in Ordnung war. Am 30.09.2026 ist genau das zwei Toren passiert.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
