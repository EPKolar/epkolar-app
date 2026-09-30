# -*- coding: utf-8 -*-
"""Welche Skripte koennen an ihrer EIGENEN Ausgabe sterben?

🔴 WARUM ES DIESES WERKZEUG GIBT. Am 30.09.2026 haben zwei Tore der Torkette
genau auf ihrem ERFOLGSZWEIG abgebrochen:

    print("   \\U0001F7E2 alle sechs richtig\\n")
    UnicodeEncodeError: 'charmap' codec can't encode character '\\U0001f7e2'

Das Tor hatte gemessen, alles war richtig - und beim Hinschreiben des gruenen
Punktes ist es gestorben. Die Torkette las den Rueckgabewert und meldete ROT.
Ein Haken davor war kurz zuvor an derselben Stelle gestorben, nur meldete der
gar nichts mehr.

🔴 UND MEIN ERSTER ZAEHLER WAR BLIND FUER GENAU DIESE FORM. Er suchte
Nicht-ASCII-ZEICHEN im Quelltext. Im Quelltext steht aber `\\U0001F7E2` - acht
ASCII-Zeichen. Erst zur Laufzeit wird daraus ein Symbol. Die beiden
abgestuerzten Tore standen deshalb NICHT in seiner Liste: er meldete "14
Skripte betroffen", und die zwei, die nachweislich sterben, waren nicht dabei.

ZWEI SCHREIBWEISEN, beide zaehlen:
  roh  - das Zeichen steht direkt in der Zeile
  esc  - \\uXXXX, \\UXXXXXXXX oder \\N{...}, also ASCII im Quelltext

Gemessen wird die AUSGABE-Zeile, nicht die ganze Datei: ein Symbol im
Kommentar oder im Docstring schadet nichts, es wird nie geschrieben.

🔴 ANWESENHEIT IST NICHT WIRKUNG: dass irgendwo `reconfigure` im Text steht,
beweist nichts - es koennte in einem Zweig liegen, der nicht laeuft, oder
hinter der ersten Ausgabe. Dieses Werkzeug zaehlt deshalb nur auf und
BEURTEILT NICHT. Gemessen wird in
`tests/test_tore_ueberleben_cp1252_v995.py`: der faehrt jedes Torskript
wirklich, unter cp1252, und sieht nach, ob es stirbt.

🔴 UND ES FAEHRT NICHTS MEHR SELBST. Der erste Entwurf hatte einen Schalter
`--fahren`, der jedes gefundene Skript startete. Das war ein Fehler und ist
am 30.09.2026 auch prompt einer geworden: in der Liste stehen
`cdn_abdruecke_setzen.py`, `echtmengen_saat.py` und andere, die SCHREIBEN.
Ein Werkzeug, das beim "Messen" den Arbeitsbaum veraendern kann, ist
gefaehrlicher als gar keines - es macht seine eigene Grundlage kaputt,
waehrend es sie misst. Der Lauf wurde abgebrochen; zwei Befund-Dateien waren
neu geschrieben, beide gueltig und inhaltlich nur nachgemessen, index.html
unberuehrt. Der Schalter ist weg.

Wer wirklich starten will, tut es einzeln und mit Absicht:

    set PYTHONIOENCODING=cp1252 && python scripts/<name>.py
"""
import io
import os
import re
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKRIPTE = os.path.join(WURZEL, "scripts")
ESC = re.compile(r"\\u[0-9a-fA-F]{4}|\\U[0-9a-fA-F]{8}|\\N\{")
AUSGABE = re.compile(r"print\(|stdout\.write\(|stderr\.write\(")


def beurteile(text):
    """Kann dieser Quelltext Nicht-ASCII AUSGEBEN? Beide Schreibweisen."""
    zeilen = [z for z in text.splitlines() if AUSGABE.search(z)]
    roh = any(any(ord(c) > 127 for c in z) for z in zeilen)
    esc = any(ESC.search(z) for z in zeilen)
    return roh, esc


def eichen():
    """🔴 SELBSTPROBE. Ohne sie kann dieses Werkzeug seinen eigenen Ausfall
    nicht bemerken: es meldete dann eine Null, und eine Null ist von "es gibt
    keine" nicht zu unterscheiden.

    Der Anlass ist hier besonders deutlich - mein ERSTER Zaehler war blind
    fuer genau die Form, die stirbt (`\\U0001F7E2` ist im Quelltext reines
    ASCII). Er meldete "14 betroffen", und die zwei Tore, die nachweislich
    starben, waren nicht dabei. Ein Koeder JE SCHREIBWEISE haette das sofort
    gezeigt.

    Dazu Gegenproben: ein Symbol im Kommentar oder im Docstring wird NIE
    geschrieben und darf nicht zaehlen - sonst meldet dieses Werkzeug fast
    jede Datei im Haus und ist wertlos.
    """
    faelle = [
        ("K1 Symbol roh in print",
         "print('fertig " + chr(0x1F7E2) + "')\n", (True, False)),
        ("K2 Symbol als \\U-Escape",
         "print('fertig \\U0001F7E2')\n", (False, True)),
        ("K3 Symbol als \\u-Escape",
         "print('pfeil \\u2192')\n", (False, True)),
        ("K4 \\N{...}",
         "print('\\N{BULLET} Punkt')\n", (False, True)),
        ("K5 stderr.write",
         "sys.stderr.write('\\U0001F534 rot')\n", (False, True)),
        ("G1 Symbol NUR im Kommentar",
         "# " + chr(0x1F534) + " Hinweis\nx = 1\n", (False, False)),
        ("G2 Symbol NUR im Docstring",
         '"""' + chr(0x1F534) + ' Hinweis."""\nx = 1\n', (False, False)),
        ("G3 Escape NUR im Kommentar",
         "# siehe \\U0001F534 oben\nx = 1\n", (False, False)),
        ("G4 print ohne Nicht-ASCII",
         "print('alles ascii')\n", (False, False)),
    ]
    schlecht = []
    for name, text, soll in faelle:
        ist = beurteile(text)
        if ist != soll:
            schlecht.append((name, soll, ist))
    for name, soll, ist in schlecht:
        print("   ROT   %-30s erwartet %s, gemessen %s" % (name, soll, ist))
    if schlecht:
        print("\n%d von %d Proben falsch - dieses Werkzeug MISST NICHT."
              % (len(schlecht), len(faelle)))
        return 2
    print("   Eichung: %d Proben - fuenf Koeder (beide Schreibweisen, "
          "beide Stroeme)\n            und vier Gegenproben "
          "(Kommentar, Docstring, reines ASCII)" % len(faelle))
    print("   alle %d richtig\n" % len(faelle))
    return 0


def kandidaten():
    """Jede Datei, die Nicht-ASCII AUSGEBEN kann - in beiden Schreibweisen."""
    aus = []
    for f in sorted(os.listdir(SKRIPTE)):
        if not f.endswith(".py"):
            continue
        t = io.open(os.path.join(SKRIPTE, f), encoding="utf-8",
                    newline="").read()
        roh, esc = beurteile(t)
        if roh or esc:
            aus.append({"datei": f, "roh": roh, "esc": esc,
                        "umgestellt": "reconfigure" in t})
    return aus


def main(argv):
    if "--eichen" in argv:
        return eichen()
    # 🔴 Die Eichung laeuft IMMER mit, nicht nur auf Verlangen. Ein
    # Messwerkzeug, dessen Selbstprobe man erst anfordern muss, laeuft im
    # Regelfall ungeeicht - und der Regelfall ist der, auf den man sich
    # verlaesst.
    if eichen() != 0:
        return 2
    k = kandidaten()
    ohne = [x for x in k if not x["umgestellt"]]
    print("Skripte, die Nicht-ASCII AUSGEBEN koennen : %d" % len(k))
    print("davon ohne Umstellung im Quelltext        : %d" % len(ohne))
    print()
    print("%-36s %-4s %-4s %s" % ("Datei", "roh", "esc", "umgestellt"))
    print("-" * 62)
    for x in k:
        print("%-36s %-4s %-4s %s"
              % (x["datei"], "ja" if x["roh"] else "-",
                 "ja" if x["esc"] else "-",
                 "ja" if x["umgestellt"] else "NEIN"))
    if "--fahren" in argv:
        print("\n\U0001F534 `--fahren` gibt es nicht mehr. Es startete jedes "
              "gefundene Skript -\n"
              "   und in dieser Liste stehen welche, die SCHREIBEN "
              "(cdn_abdruecke_setzen.py,\n"
              "   echtmengen_saat.py und andere). Ein Werkzeug, das beim "
              "Messen den\n"
              "   Arbeitsbaum veraendern kann, misst seine eigene Grundlage "
              "kaputt.\n"
              "   Gemessen wird in tests/test_tore_ueberleben_cp1252_v995.py; "
              "einzeln starten\n"
              "   geht mit:  set PYTHONIOENCODING=cp1252 && python "
              "scripts/<name>.py")
        return 2
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
