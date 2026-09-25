# -*- coding: utf-8 -*-
"""Die Torkette in EINEM Lauf - ohne Pipe, mit einem Urteil am Ende.

WOZU
────
`$?` nach einer Pipe ist der Rueckgabewert des LETZTEN Glieds, nicht der des
Riegels. Vier belegte Faelle, allein am 24.09.2026 dreimal:

    npm run verify | tail      meldete den Code von `tail`
    playwright ... | head      meldete "No tests found" mit exit 0
    vitest ... | ...           lief mit 26 roten Faellen auf exit 0

Die Kette wird deshalb hier gefahren, nicht in der Muschel zusammengesteckt.
Jedes Tor ist ein eigener Prozess, sein Rueckgabewert wird EINZELN gelesen,
und die Ausgabe wird erst NACH dem Lesen gekuerzt.

WAS SIE FAEHRT
──────────────
    1  scripts/node_check.py        jeder <script>-Block parst
    2  scripts/_bracket_check.py    Klammerbilanz () -1 / {} 0 / [] 0
    3  node sql/_check_version.js   die vier Versionsstellen stimmen ueberein
    4  pytest tests/                der gesamte Riegelbestand

AUFRUF
──────
    python scripts/torkette.py              alle vier
    python scripts/torkette.py --schnell    ohne pytest (Zwischenstand)

Rueckgabewert: 0 nur, wenn ALLE gefahrenen Tore gruen waren.
"""
import os
import subprocess
import sys
import time

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TORE = [
    ("node_check", [sys.executable, "scripts/node_check.py"], False),
    ("Klammerbilanz", [sys.executable, "scripts/_bracket_check.py"], False),
    ("Versionsabgleich", ["node", "sql/_check_version.js"], False),
    ("pytest", [sys.executable, "-m", "pytest", "tests/", "-q"], True),
]


def fahre(name, befehl):
    """Faehrt EIN Tor und gibt (gruen, dauer, ausgabe) zurueck.

    Kein `shell=True`, keine Pipe: der Rueckgabewert kommt vom Riegel selbst.
    """
    t0 = time.time()
    try:
        r = subprocess.run(befehl, cwd=WURZEL, capture_output=True, text=True,
                           timeout=1800)
    except FileNotFoundError as e:
        # Ein Tor, das gar nicht startet, ist NICHT gruen. Genau diese
        # Verwechslung hat `nmea-masse` fuenf Tage lang gedeckt.
        return False, time.time() - t0, "liess sich nicht starten: %s" % e
    except subprocess.TimeoutExpired:
        return False, time.time() - t0, "Zeitgrenze ueberschritten (1800 s)"
    return (r.returncode == 0, time.time() - t0,
            ((r.stdout or "") + (r.stderr or "")).strip())


def main(argv):
    schnell = "--schnell" in argv
    rot = []
    print("Torkette - %s" % ("schnell (ohne pytest)" if schnell else "vollstaendig"))
    print("=" * 60)
    for name, befehl, langsam in TORE:
        if schnell and langsam:
            print("%-18s uebersprungen (--schnell)" % name)
            continue
        gruen, dauer, ausgabe = fahre(name, befehl)
        print("%-18s %-6s %5.1f s" % (name, "gruen" if gruen else "ROT", dauer))
        if not gruen:
            rot.append((name, ausgabe))

    print("=" * 60)
    if not rot:
        gefahren = len(TORE) - (1 if schnell else 0)
        print("ALLE %d TORE GRUEN" % gefahren)
        if schnell:
            print("ACHTUNG: pytest wurde uebersprungen. Das ist ein "
                  "Zwischenstand, kein Auslieferungsurteil.")
        return 0

    print("%d TOR(E) ROT - nichts committen." % len(rot))
    for name, ausgabe in rot:
        print("")
        print("--- %s " % name + "-" * (56 - len(name)))
        # Erst NACH dem Lesen des Rueckgabewerts kuerzen, nie per Pipe.
        print(ausgabe[-3000:])
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
