# -*- coding: utf-8 -*-
"""Anker GESCHNITTEN, nicht abgetippt - samt Vorkommenzahl.

WOZU
────
Ein abgetippter Anker trifft in dieser Datei oft nicht: CRLF-Zeilenenden,
schmale Leerzeichen, Varianten-Selektoren hinter Emoji. Diese Hilfe schneidet
den Anker AUS der Datei (Offset + Laenge oder ein Suchbegriff plus Kontext)
und meldet, wie oft die geschnittene Zeichenkette im GANZEN Dokument
vorkommt. Steht dort 1, ist `grep -F` eindeutig.

WAS SIE NICHT TUT
─────────────────
Sie aendert nichts. Sie prueft nicht, ob der Anker sinnvoll ist. Sie sagt
nichts darueber, ob die Stelle im Code oder in einem Kommentar steht - dafuer
ist scripts/code_scan.py da.

AUFRUF
──────
    EPK_INDEX=_mess_stand_942.html python scripts/anker_schneiden.py \
        --suche "fontSize:isMob?9:13" --vor 60 --nach 20
    EPK_INDEX=_mess_stand_942.html python scripts/anker_schneiden.py \
        --offset 2076870 --laenge 120
"""
import io
import os
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def laden():
    datei = os.environ.get("EPK_INDEX", "index.html")
    return io.open(os.path.join(WURZEL, datei), encoding="utf-8",
                   newline="").read(), datei


def zeige(s, a, b, datei):
    stueck = s[a:b]
    n = s.count(stueck)
    print("─" * 72)
    print("Offset %d..%d   Laenge %d Zeichen   Vorkommen im Dokument: %d %s"
          % (a, b, len(stueck), n, "(EINDEUTIG)" if n == 1 else "(NICHT eindeutig!)"))
    print(repr(stueck))
    print()


def main(argv):
    s, datei = laden()
    print("Datei: %s   %d Zeichen" % (datei, len(s)))
    if "--offset" in argv:
        a = int(argv[argv.index("--offset") + 1])
        ln = int(argv[argv.index("--laenge") + 1]) if "--laenge" in argv else 120
        zeige(s, a, a + ln, datei)
        return 0
    if "--suche" in argv:
        nadel = argv[argv.index("--suche") + 1]
        vor = int(argv[argv.index("--vor") + 1]) if "--vor" in argv else 0
        nach = int(argv[argv.index("--nach") + 1]) if "--nach" in argv else 0
        treffer = []
        i = s.find(nadel)
        while i >= 0:
            treffer.append(i)
            i = s.find(nadel, i + 1)
        print("Suchbegriff %r: %d Treffer" % (nadel, len(treffer)))
        for t in treffer:
            zeige(s, max(0, t - vor), min(len(s), t + len(nadel) + nach), datei)
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
