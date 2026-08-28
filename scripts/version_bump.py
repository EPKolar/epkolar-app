# -*- coding: utf-8 -*-
"""Versionssprung ueber alle VIER Stellen - in einem Schritt, ohne Handarbeit.

WARUM ES DIESES SKRIPT GIBT (28.08.2026): Die vier Stellen wurden bisher von Hand
nachgezogen. Das ist an einem einzigen Tag VIERMAL danebengegangen - jedes Mal auf
dieselbe Art: der Kopfkommentar in sw.js bekam die Version doppelt

    // EP Kolar Service Worker v3.9.878 - v3.9.878 - Drei fertig geschriebene...

weil die Vorlage `v{neu} - ` schreibt und der uebergebene Text schon mit `v{neu} - `
begann. Folgenlos (es ist ein Kommentar, der Riegel liest die Zahl korrekt), aber es
ist genau die Klasse von Fehler, die Handarbeit erzeugt und Werkzeug verhindert.

DIE VIER STELLEN (aus CLAUDE.md):
  1. index.html  var SW_VER='epkolar-vX.Y.Z';
  2. index.html  const APP_VERSION="X.Y.Z-supabase";/* <text> | <alter text> */
  3. sw.js       // EP Kolar Service Worker vX.Y.Z - <text> vX.Y.Z-1 - <alter text>
  4. sw.js       const CACHE_NAME = "epkolar-vX.Y.Z";

Beschreibung OHNE Versionsprefix uebergeben - das Skript setzt `vX.Y.Z - ` bzw.
`vX.Y.Z ` genau einmal je Stelle davor.

AUFRUF:
    python scripts/version_bump.py 3.9.879 "Kurzbeschreibung der Aenderung"
    python scripts/version_bump.py 3.9.879 --datei beschreibung.txt
    python scripts/version_bump.py --pruefen        # nur Doppelungen melden

Danach IMMER `node sql/_check_version.js` - das Skript ruft es nicht selbst auf,
damit der Riegel eine unabhaengige Instanz bleibt.
"""
import io
import os
import re
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDX = os.path.join(WURZEL, "index.html")
SW = os.path.join(WURZEL, "sw.js")


def _lies(p):
    return io.open(p, encoding="utf-8", newline="").read()


def _schreib(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def aktuelle_version(idx):
    m = re.search(r'const\s+APP_VERSION\s*=\s*"([\d.]+)-supabase"', idx)
    if not m:
        raise SystemExit("APP_VERSION nicht gefunden - Aufbau von index.html geaendert?")
    return m.group(1)


def doppelungen(sw):
    """Kopfzeilen der Form 'vX - vX - ' melden. Genau der Fehler von oben."""
    kopf = sw.split("\n", 1)[0]
    return sorted(set(re.findall(r"v(\d+\.\d+\.\d+) - v\1 - ", kopf)))


def entdoppeln(sw):
    kopf, rest = sw.split("\n", 1)
    neu = re.sub(r"v(\d+\.\d+\.\d+) - v\1 - ", r"v\1 - ", kopf)
    return neu + "\n" + rest, kopf != neu


def bump(neu_ver, text):
    idx = _lies(IDX)
    sw = _lies(SW)
    alt = aktuelle_version(idx)
    if alt == neu_ver:
        raise SystemExit("Version %s steht schon drin." % neu_ver)

    text = text.strip()
    # Falls doch mit Prefix uebergeben: einmal abschneiden statt doppelt schreiben.
    text = re.sub(r"^v?" + re.escape(neu_ver) + r"\s*[-:]?\s*", "", text)
    if not text:
        raise SystemExit("Leere Beschreibung - der Changelog ist die halbe Uebergabe.")

    aenderungen = []

    # 1) SW_VER
    a = "var SW_VER='epkolar-v%s';" % alt
    if idx.count(a) != 1:
        raise SystemExit("SW_VER nicht eindeutig (%d Treffer)" % idx.count(a))
    idx = idx.replace(a, "var SW_VER='epkolar-v%s';" % neu_ver, 1)
    aenderungen.append("index.html SW_VER")

    # 2) APP_VERSION + Changelog davorhaengen
    a = 'const APP_VERSION="%s-supabase";/* ' % alt
    if idx.count(a) != 1:
        raise SystemExit("APP_VERSION-Anker nicht eindeutig (%d Treffer)" % idx.count(a))
    idx = idx.replace(a, 'const APP_VERSION="%s-supabase";/* v%s %s | ' % (neu_ver, neu_ver, text), 1)
    aenderungen.append("index.html APP_VERSION")

    # 3) sw.js Kopfkommentar - Prefix GENAU EINMAL
    a = "// EP Kolar Service Worker v%s - " % alt
    if sw.count(a) != 1:
        raise SystemExit("sw.js-Kopf nicht eindeutig (%d Treffer)" % sw.count(a))
    sw = sw.replace(a, "// EP Kolar Service Worker v%s - %s v%s - " % (neu_ver, text, alt), 1)
    aenderungen.append("sw.js Kopf")

    # 4) CACHE_NAME
    a = 'const CACHE_NAME = "epkolar-v%s";' % alt
    if sw.count(a) != 1:
        raise SystemExit("CACHE_NAME nicht eindeutig (%d Treffer)" % sw.count(a))
    sw = sw.replace(a, 'const CACHE_NAME = "epkolar-v%s";' % neu_ver, 1)
    aenderungen.append("sw.js CACHE_NAME")

    # Selbstpruefung VOR dem Schreiben: keine neue Doppelung erzeugt?
    doppelt = doppelungen(sw)
    if neu_ver in doppelt:
        raise SystemExit("Selbstpruefung: der Kopf haette 'v%s - v%s - ' bekommen. "
                         "Nichts geschrieben." % (neu_ver, neu_ver))

    _schreib(IDX, idx)
    _schreib(SW, sw)
    print("%s -> %s" % (alt, neu_ver))
    for x in aenderungen:
        print("  ok:", x)
    if doppelt:
        print("  Hinweis: aeltere Doppelungen im Kopf:", ", ".join(doppelt))
    print("\nJetzt:  node sql/_check_version.js")
    return 0


def main(argv):
    if len(argv) >= 1 and argv[0] == "--pruefen":
        sw = _lies(SW)
        d = doppelungen(sw)
        print("Version laut index.html:", aktuelle_version(_lies(IDX)))
        if d:
            print("Doppelte Kopf-Prefixe:", ", ".join(d))
            return 1
        print("Kopfzeile sauber.")
        return 0

    if len(argv) >= 1 and argv[0] == "--reparieren":
        sw = _lies(SW)
        vorher = doppelungen(sw)
        if not vorher:
            print("Nichts zu reparieren.")
            return 0
        neu, geaendert = entdoppeln(sw)
        if not geaendert:
            raise SystemExit("Doppelungen gemeldet, aber Ersetzung griff nicht - Anker pruefen.")
        _schreib(SW, neu)
        nachher = doppelungen(_lies(SW))
        print("repariert:", ", ".join(vorher))
        # Gegenprobe: die Zahlen muessen weg sein UND die Versionen erhalten bleiben.
        for v in vorher:
            if ("v%s - " % v) not in _lies(SW).split("\n", 1)[0]:
                raise SystemExit("Version %s ist beim Entdoppeln VERSCHWUNDEN." % v)
        if nachher:
            raise SystemExit("Noch immer doppelt: %s" % ", ".join(nachher))
        print("Gegenprobe: alle Versionen noch da, keine Doppelung mehr.")
        return 0

    if len(argv) == 3 and argv[1] == "--datei":
        return bump(argv[0], _lies(os.path.abspath(argv[2])))
    if len(argv) == 2:
        return bump(argv[0], argv[1])

    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
