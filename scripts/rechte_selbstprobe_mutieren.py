# -*- coding: utf-8 -*-
"""Mutationsprobe an den Selbstproben von `rechte_*_messen.py`.

WARUM
─────
Eine Selbstprobe, die immer gruen meldet, ist kein Riegel, sondern Zierrat.
Dieses Skript macht die Messwerkzeuge absichtlich KAPUTT und prueft, ob ihre
Selbstprobe das MERKT. Es misst WIRKUNG, nicht Anwesenheit.

Vier Mutationen muessen ROT werden, eine Kontrolle bleibt GRUEN.
Rueckgabewert: 0 = alle Erwartungen erfuellt, 2 = mindestens eine nicht.

AUFRUF
──────
    python scripts/rechte_selbstprobe_mutieren.py
"""
import importlib.util
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)


def lade(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(HIER, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def still(fn):
    """Die Selbstprobe laufen lassen, ohne ihre Ausgabe durchzureichen."""
    import io as _io
    alt = sys.stdout
    sys.stdout = _io.StringIO()
    try:
        return fn()
    finally:
        sys.stdout = alt


def main():
    r = lade("rechte_rollen_messen")
    s = lade("rechte_schreibwege_messen")
    faelle = []

    # ── 1: Der Koeder verliert die einfach zitierte Schreibweise ──
    alt = r.KOEDER
    r.KOEDER = alt.replace("u.role==='monteur'", 'u.role=="monteur"')
    faelle.append(("Rollen: einfach zitierte Schreibweise aus dem Koeder",
                   still(r.selbstprobe), False))
    r.KOEDER = alt

    # ── 2: Die Kommentar-Ausblendung wird abgeschaltet ──
    alt_ic = r.ist_code
    r.ist_code = lambda t: bytearray(b"\x01" * len(t))
    faelle.append(("Rollen: Kommentar-Ausblendung abgeschaltet",
                   still(r.selbstprobe), False))
    r.ist_code = alt_ic

    # ── 3 (KONTROLLE): eine Aenderung, die die Richtigkeit NICHT beruehrt ──
    alt2 = s.KOEDER
    s.KOEDER = alt2.replace("url:`/api/koederC/${id}`", 'url:"/api/koederC/1"')
    faelle.append(("KONTROLLE: Vorlagenliteral im Koeder durch Zeichenkette "
                   "ersetzt", still(s.selbstprobe), True))
    s.KOEDER = alt2

    # ── 4: Der Klammerabgleich hoert bei der ersten ) auf ──
    alt_kz = s.klammer_zu

    def kaputt(text, feld, i, auf, zu):
        m = re.search(r"\)", text[i:])
        return m.start() + i if m else -1
    s.klammer_zu = kaputt
    faelle.append(("Schreibwege: Klammerabgleich auf die erste ) verkuerzt",
                   still(s.selbstprobe), False))
    s.klammer_zu = alt_kz

    # ── 5: Die zweite Maske faellt auf ist_code zurueck ──
    alt_kk = s.ist_kein_kommentar
    s.ist_kein_kommentar = lambda t: s.ist_code(t)
    faelle.append(("Schreibwege: ist_kein_kommentar durch ist_code ersetzt",
                   still(s.selbstprobe), False))
    s.ist_kein_kommentar = alt_kk

    print("MUTATIONSPROBE an den Selbstproben")
    print()
    schief = 0
    for name, ist, soll in faelle:
        passt = (ist == soll)
        if not passt:
            schief += 1
        print("%-6s erwartet %-6s  %s%s" %
              ("GRUEN" if ist else "ROT", "GRUEN" if soll else "ROT", name,
               "" if passt else "   <- ERWARTUNG NICHT ERFUELLT"))
    print()
    if schief:
        print("%d von %d Mutationen verhalten sich NICHT wie erwartet - die "
              "Selbstproben sind KEIN Riegel." % (schief, len(faelle)))
        return 2
    print("Alle %d Erwartungen erfuellt: vier Mutationen roetten die "
          "Selbstprobe, die Kontrolle bleibt gruen." % len(faelle))
    print()
    print("GRENZE, und sie gehoert dazu: Fall 3 zeigt sie. Nimmt man dem "
          "Koeder eine FORM weg, statt das Werkzeug kaputtzumachen, bleibt "
          "die Selbstprobe gruen - sie kann nur pruefen, was im Koeder "
          "steht. Gegen einen zu duennen Koeder hilft keine Mutation, nur "
          "Nachsehen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
