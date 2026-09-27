# -*- coding: utf-8 -*-
"""Was sehen die Abtaster von v3.9.957 und v3.9.958 WIRKLICH?

Nicht erschlossen, sondern gemessen: die Suchlogik der beiden Abtaster wird
ZEICHENGENAU nachgebildet und auf denselben Text angesetzt wie der neue.

🔴 ZWEI eigene Fehler auf dem Weg hierher, beide derselbe:
1. „v957 wuerde diese Stelle nicht finden" hatte ich aus dem Lesen des
   Musters GESCHLOSSEN und dabei 6 statt 5 und 8 statt 7 gezaehlt.
2. Die erste Fassung dieser Gegenprobe verglich ueber die ZEILENNUMMER. In
   einer Datei mit 1300 Zeichen pro Zeile stehen mehrere Knoepfe auf
   derselben Zeile - die Zeilennummer ist KEIN eindeutiger Schluessel. Sie
   meldete daraufhin, v958 halte Z18442 fuer benannt, obwohl der Treffer zu
   einem ANDEREN Knopf auf derselben Zeile gehoerte. Verglichen wird jetzt
   ueber die ZEICHENPOSITION des Knopfanfangs.

AUFRUF
──────
    BEDIENELEMENTE_PFAD=<abschrift> python \\
        scripts/bedienelemente_gegenprobe_v957_958.py
"""
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
sys.path.insert(0, os.path.join(HIER, "..", "tests"))

import bedienelemente_scan as B  # noqa: E402
import test_symbolknoepfe_haben_namen_v957 as V957  # noqa: E402
import test_emojiknoepfe_haben_namen_v958 as V958  # noqa: E402


def v957_positionen(text):
    """Die Logik von V957._symbolknoepfe, aber mit der Knopfposition.

    Original: fuer jedes `"SYM"` die LETZTE `createElement('button'` in den
    900 Zeichen davor. Der Rueckgabewert ist
    {position des Knopfes: hat_namen}.
    """
    aus = {}
    for sym in V957.SYMBOLE:
        for m in re.finditer(r'"' + re.escape(sym) + r'"', text):
            p = m.start()
            vor = text[max(0, p - 900):p]
            k = vor.rfind("createElement('button'")
            if k < 0:
                continue
            knopf = max(0, p - 900) + k
            props = vor[k:]
            hat = bool(re.search(r"\btitle\s*:", props)) \
                or "aria-label" in props
            # Mehrere Symbole koennen auf denselben Knopf zeigen.
            aus[knopf] = aus.get(knopf, True) and hat
    return aus


def v958_positionen(text):
    """Die Logik von V958._emojiknoepfe, aber mit der Knopfposition."""
    aus = {}
    for m in re.finditer(r"createElement\('button'\s*,", text):
        a = m.end()
        pe = V958._props_ende(text, a)
        if pe is None:
            continue
        props = text[a:pe]
        rest = text[pe:pe + 400]
        rest = re.sub(r"^\s*,\s*", "", rest, count=1)
        rest = re.sub(r"^/\*.*?\*/\s*", "", rest, count=1, flags=re.S)
        mk = re.match(r'"((?:[^"\\]|\\.)*)"\s*\)', rest)
        if not mk:
            continue
        inhalt = mk.group(1)
        if not inhalt or not V958.EMOJI.match(inhalt):
            continue
        hat = bool(re.search(r"\btitle\s*:", props)) or "aria-label" in props
        aus[m.start()] = hat
    return aus


def _knopf_pos(text, s):
    """Position des `createElement('button'` bzw. `h('button'` der Stelle."""
    return s["pos"]


def main():
    roh = B.lies()
    mk = B.maske(roh)
    st = B.stellen(roh, mk)
    neu = sorted(B.klasse_a_immer(roh, mk, st), key=lambda s: s["pos"])

    p957 = v957_positionen(roh)
    p958 = v958_positionen(roh)
    # v957 zeigt auf `createElement('button'`, mein Abtaster auf `React.`
    # davor. Beide auf denselben Knopf abbilden: ein Treffer gilt, wenn er
    # innerhalb von 30 Zeichen hinter meinem Anfang liegt.
    def gesehen(tab, pos):
        for q in range(pos, pos + 31):
            if q in tab:
                return tab[q]
        return None

    print("Grundgesamtheiten auf DEMSELBEN Text (%d Bytes)"
          % len(roh.encode("utf-8")))
    print("  v957-Logik, zeichengenau : %d Knoepfe" % len(p957))
    print("  v958-Logik, zeichengenau : %d Knoepfe" % len(p958))
    print("  neu, `klasse_a_immer`    : %d Knoepfe" % len(neu))
    print()
    print("Die %d Knoepfe, die NIE ein Wort zeigen und keinen Namen tragen:"
          % len(neu))
    print()
    print("  %-7s %-14s %-24s %-18s %s"
          % ("Zeile", "Form", "Inhalt", "v957-Logik", "v958-Logik"))
    z957 = z958 = beide = 0
    for s in neu:
        g7, g8 = gesehen(p957, s["pos"]), gesehen(p958, s["pos"])
        t7 = ("nicht gesehen" if g7 is None
              else "GESEHEN, benannt" if g7 else "GESEHEN, gemeldet")
        t8 = ("nicht gesehen" if g8 is None
              else "GESEHEN, benannt" if g8 else "GESEHEN, gemeldet")
        print("  %-7d %-14s %-24s %-18s %s"
              % (s["zeile"], B.schreibweise(roh, s),
                 " ".join(s["kinder"])[:22], t7, t8))
        b7 = g7 is None or g7
        b8 = g8 is None or g8
        z957 += 1 if b7 else 0
        z958 += 1 if b8 else 0
        beide += 1 if (b7 and b8) else 0
    print()
    print("  von v957 nicht gemeldet : %d von %d" % (z957, len(neu)))
    print("  von v958 nicht gemeldet : %d von %d" % (z958, len(neu)))
    print("  von BEIDEN nicht gemeldet: %d von %d" % (beide, len(neu)))
    print()
    print("Warum je Stelle (ausgezaehlt, nicht geschlossen):")
    hform = [s for s in neu if B.schreibweise(roh, s) == "h("]
    einf = [s for s in neu
            if " ".join(s["kinder"]).lstrip().startswith("'")]
    tern = [s for s in neu if any(
        B._ternaer_zweige(roh, mk, x, y) is not None for x, y in s["_kspans"])]
    nichtbutton = [s for s in neu if s["tag"] != "button"]
    print("  in der `h(`-Form (beide Abtaster suchen nur "
          "`createElement('button'`) : %d  %s"
          % (len(hform), [s["zeile"] for s in hform]))
    print("  Inhalt EINFACH gesetzt (v958 liest nur \"...\")"
          "                      : %d  %s"
          % (len(einf), [s["zeile"] for s in einf]))
    print("  Inhalt ein Ternaer (kein Literal, beide Abtaster sehen keines)"
          "      : %d  %s" % (len(tern), [s["zeile"] for s in tern]))
    print("  gar kein `button` (ein `a`)"
          "                                        : %d  %s"
          % (len(nichtbutton), [s["zeile"] for s in nichtbutton]))
    print()
    print("KOEDER auf diese Gegenprobe: die alten Abtaster sind nicht leer -")
    print("  v957-Logik : %d als benannt, %d gemeldet"
          % (sum(1 for v in p957.values() if v),
             sum(1 for v in p957.values() if not v)))
    print("  v958-Logik : %d als benannt, %d gemeldet"
          % (sum(1 for v in p958.values() if v),
             sum(1 for v in p958.values() if not v)))
    print("  Eine leere Grundgesamtheit besteht keine Probe. Beide sind")
    print("  nicht leer, also ist das \"nicht gesehen\" oben eine Aussage")
    print("  ueber die Stelle und nicht ueber den Abtaster.")


if __name__ == "__main__":
    main()
