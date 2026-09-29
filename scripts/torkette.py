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
                                    🔴 beurteilt nur 27,9 % - siehe Tor 3
    3  scripts/klammerbilanz.py     dieselbe Frage zustandsbasiert: 54,9 %
                                    beurteilt, () 0 / [] 0 / {} 0, und es
                                    sagt WO
    4  node sql/_check_version.js   die vier Versionsstellen stimmen ueberein
    5  scripts/md5_geschuetzt.py    die sieben TABU-Funktionen sind bytegleich
    6  scripts/bestand.py           118 Begriffe in 17 Gruppen sind noch da
    7  scripts/icons_erzeugen.py    die vier PWA-Icons sind aktuell (--pruefen)
    8  pytest tests/                der gesamte Riegelbestand

🔴 WARUM 4 BIS 6 AM 27.09.2026 DAZUGEKOMMEN SIND
────────────────────────────────────────────────
Alle drei gab es schon, und KEINER lief irgendwo. Der Dateikopf von
`md5_geschuetzt.py` beginnt sogar mit den Worten "Gate 5" - es war als Tor
gedacht und ist nie eines geworden.

Das wiegt bei ihm am schwersten: es haelt die Byte-Identitaet von sieben
Funktionen mit Lohn- und Eskalationslogik (`_ezEffTage`, `_asEskalierbar`,
`_dispoPlan`, `_maIstEhemalig`, `_maWaehlbar`, `_juprowaPush`,
`_juprowaSanitize`). Gemessen: **keine einzige der sieben Pruefsummen stand in
irgendeiner Testdatei** - und ZWEI Tests verwiesen ausdruecklich darauf ("das
haelt scripts/md5_geschuetzt.py fest"). Die Zusicherung war an etwas delegiert,
das nie gefahren wurde. Sie lief nur, weil ich sie im Lauf vom 26./27.09. nach
jeder Stufe von Hand getippt habe - und Disziplin ist kein Riegel.

Kosten: zusammen rund EINE Sekunde. Die schnelle Kette 3 -> 4 s, die ganze
283 -> 284 s. Ein Tor, das die Kette merklich bremst, wird irgendwann
uebersprungen; diese drei tun das nicht.

🔴 `icons_erzeugen.py` braucht ZWINGEND `--pruefen`. Ohne das Argument SCHREIBT
es vier PNG ins Repo. Belegt vor dem Einhaengen: mit `--pruefen` rc 0 und
`git status` unveraendert.

AUFRUF
──────
    python scripts/torkette.py              alle sieben
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
    # 🔴 29.09.2026 (Frage 15): das Tor darueber beurteilt nur 27,9 % der Datei.
    #    Sein Vorlagenliteral-Muster steht VOR dem Kommentarmuster, und diese
    #    Datei zitiert in Kommentaren mit Backticks - jeder einzelne wird als
    #    ENDE eines viel frueher geoeffneten Literals gelesen. BELEGT: eine
    #    einzelne unpaarige `(` in echten Code bei Zeile 11380 gesetzt ->
    #    altes Tor GRUEN (Rueckgabe 0), neues Tor rot MIT Zeilenangabe. Der
    #    Beleg laeuft auf einer Kopie und vergleicht den Abdruck der echten
    #    Datei davor und danach: scripts/klammertor_vergleich.py
    #    Das alte bleibt trotzdem stehen: test_klammertor_blindheit_v956 misst
    #    es und haelt seine Blindheit fest, damit sie nicht weiter waechst.
    #    Hier kommt ein Tor DAZU, es wird keines ersetzt.
    ("Klammern zustandsbasiert",
     [sys.executable, "scripts/klammerbilanz.py"], False),
    ("Versionsabgleich", ["node", "sql/_check_version.js"], False),
    ("Tabu-Funktionen", [sys.executable, "scripts/md5_geschuetzt.py"], False),
    ("Bestand", [sys.executable, "scripts/bestand.py"], False),
    # --pruefen ist NICHT optional: ohne das Argument schreibt das Skript.
    ("PWA-Icons", [sys.executable, "scripts/icons_erzeugen.py", "--pruefen"],
     False),
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
