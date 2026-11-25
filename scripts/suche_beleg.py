# -*- coding: utf-8 -*-
"""Belegsuche: findet JEDE Zeile mit einem Begriff - oder bricht laut ab.

Hintergrund (24./25.11.2026): Die Suche `grep -o ".\\{N\\}begriff.\\{M\\}"` findet einen Treffer nur,
wenn mindestens N Zeichen davor und M Zeichen danach stehen. Kurze Zeilen und Treffer am Zeilenanfang
fallen STILL heraus. So wurden der login_lookup-Aufruf (index.html:3848), der einzige last_login-
Schreibweg (3887) und die changePassword-Definition (3898) uebersehen.

Regel: Eine Suche ist nur ein Beleg, wenn sie
  1. woertlich sucht (kein Regex mit fester Breite),
  2. jede Zeile zaehlt (Zeilennummer + Spalte),
  3. mit einer Positivkontrolle geeicht ist (ein Begriff, der sicher vorkommt, wird gefunden).
Fehlt die Kontrolle oder wird sie nicht gefunden, ist das Ergebnis KEIN Beleg (Exitcode 2).

Aufruf:  python scripts/suche_beleg.py BEGRIFF DATEI --kontrolle BEKANNTER_BEGRIFF [--kontext 80]
Ausgabe: je Treffer "zeile:spalte: <Ausschnitt>", am Ende "TREFFER n in m Zeilen".
Exitcodes: 0 = geeichte Suche (auch bei 0 Treffern), 2 = Kontrolle fehlt/nicht gefunden,
           3 = Begriff sieht nach Regex mit fester Breite aus (abgelehnt).
"""
import argparse
import re
import sys

# .\{40\}  .{40}  .\{40,\}  .{40,200}  - jede Untergrenze > 0 vor oder nach dem Begriff laesst Zeilen weg
FESTE_BREITE = re.compile(r"\.\\?\{\s*([1-9]\d*)\s*(?:,\s*\d*\s*)?\\?\}")


def ist_feste_breite(muster):
    return bool(FESTE_BREITE.search(muster))


def suche(text, begriff, kontext=80):
    """Alle Vorkommen, woertlich. -> Liste (zeile, spalte, ausschnitt); Zeilen/Spalten ab 1."""
    treffer = []
    for nr, zeile in enumerate(text.splitlines(), 1):
        start = 0
        while True:
            i = zeile.find(begriff, start)
            if i < 0:
                break
            a = max(0, i - kontext)  # offene Grenze: weniger Kontext ist erlaubt, nie ein Ausfall
            e = min(len(zeile), i + len(begriff) + kontext)
            treffer.append((nr, i + 1, zeile[a:e]))
            start = i + max(1, len(begriff))
    return treffer


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("begriff")
    p.add_argument("datei")
    p.add_argument("--kontrolle", default="", help="Begriff, der sicher in der Datei steht (Pflicht)")
    p.add_argument("--kontext", type=int, default=80)
    a = p.parse_args(argv)
    try:  # Windows-Konsole (cp1252) darf an Umlauten/Pfeilen nicht abstuerzen - sonst fehlen Treffer
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if ist_feste_breite(a.begriff):
        print("ABGELEHNT: Muster mit fester Breite laesst Zeilen still weg - woertlich suchen.", file=sys.stderr)
        return 3
    with open(a.datei, encoding="utf-8", errors="replace", newline="") as f:
        text = f.read()
    if not a.kontrolle:
        print("KEIN BELEG: --kontrolle fehlt (Positivkontrolle ist Pflicht).", file=sys.stderr)
        return 2
    k = suche(text, a.kontrolle, 0)
    if not k:
        print("KEIN BELEG: Positivkontrolle '%s' nicht gefunden - Suche nicht geeicht." % a.kontrolle, file=sys.stderr)
        return 2
    t = suche(text, a.begriff, a.kontext)
    for nr, sp, aus in t:
        print("%d:%d: %s" % (nr, sp, aus))
    print("KONTROLLE '%s': %d Treffer" % (a.kontrolle, len(k)))
    print("TREFFER %d in %d Zeilen" % (len(t), len({x[0] for x in t})))
    return 0


if __name__ == "__main__":
    sys.exit(main())
