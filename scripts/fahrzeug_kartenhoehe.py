# -*- coding: utf-8 -*-
"""Wie hoch ist eine Fahrzeugkarte? Vorher/nachher, an der echten Saat.

Punkt 2 des Auftrags verlangt, die Schriften zu heben, "ohne die Karte hoeher
zu machen als noetig". Das ist eine Aussage ueber eine Zahl, die bisher
nirgends gemessen wird: `echtmengen_messen` zaehlt Elemente unter 12 px, keine
Hoehen. Ohne diese Sonde waere "die Karte ist nicht hoeher geworden" eine
Behauptung.

🔴 GEMESSEN WIRD DER MEDIAN EINER KARTE, NICHT DIE SUMME. Die Summe waechst
schon, wenn eine Karte mehr da ist; sie kann also steigen, ohne dass eine
einzige Karte hoeher wurde. Die Kartenzahl wird mitgemeldet - faellt oder
steigt sie, sind zwei Laeufe nicht vergleichbar, und das muss sichtbar sein
statt in einem Mittelwert zu verschwinden.

🔴 SELBSTPROBE: findet die Sonde weniger als drei Karten, gibt sie KEINE Zahl
aus, sondern sagt, dass sie nichts gemessen hat. Eine leere Grundgesamtheit,
die einen Median von None meldet, sieht sonst aus wie ein Ergebnis.

Aufruf:
    python scripts/fahrzeug_kartenhoehe.py 390
    EPK_INDEX=_vorher.html python scripts/fahrzeug_kartenhoehe.py 390
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import mob_ansicht_messen as M           # noqa: E402
import b3_stufen_12_15_messen as B12     # noqa: E402
import echtmengen_saat as SAAT           # noqa: E402
import echtmengen_messen as EM           # noqa: E402

# Die Karten tragen in dieser Datei keine Klasse, an der man sie greifen
# koennte. Gesucht wird deshalb ueber die FORM: ein Element mit sichtbarem
# Rahmen, das den Namen oder das Kennzeichen eines Fahrzeugs aus der Saat
# enthaelt - und davon nur die innersten, sonst zaehlt jede umschliessende
# Huelle mit und der Median waere die Hoehe der Liste.
HOEHEN_JS = r"""(marken) => {
  // 🔴 Die erste Fassung nahm die INNERSTEN Elemente, die ein Kennzeichen
  // enthalten. Das ist die Kennzeichen-Beschriftung (rund 20 px), nicht die
  // Karte - alle fielen durch den Hoehenfilter und die Sonde meldete 0.
  // Die Karte ist das AEUSSERSTE Element, das GENAU EIN Kennzeichen enthaelt:
  // sobald zwei darin stehen, ist es die Liste.
  const alle = [...document.querySelectorAll('div,li,article,tr')];
  const proMarke = {};
  for (const e of alle) {
    const t = e.innerText || '';
    const drin = marken.filter(m => t.includes(m));
    if (drin.length !== 1) continue;
    const h = Math.round(e.getBoundingClientRect().height);
    if (h < 40) continue;
    const m = drin[0];
    if (!proMarke[m] || h > proMarke[m].h) proMarke[m] = {h: h, len: t.length};
  }
  const namen = Object.keys(proMarke);
  const h = namen.map(m => proMarke[m].h).sort((a, b) => a - b);
  const med = h.length ? (h.length % 2 ? h[(h.length - 1) / 2]
              : Math.round((h[h.length / 2 - 1] + h[h.length / 2]) / 2)) : null;
  return {anzahl: h.length, median: med, klein: h[0] || null,
          gross: h[h.length - 1] || null, alle: h.slice(0, 24),
          textlaenge: namen.length ? proMarke[namen[0]].len : null};
}"""


def messen(breite):
    from playwright.sync_api import sync_playwright
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port,
                                      os.environ.get("EPK_INDEX", "index.html"))
    saat = SAAT.saat()
    marken = []
    for f in (saat.get("fahrzeuge") or []):
        for schluessel in ("kennzeichen", "plate", "name", "bezeichnung"):
            if f.get(schluessel):
                marken.append(str(f[schluessel]))
                break
    marken = marken[:10]
    if len(marken) < 3:
        print("\U0001F534 Nur %d Fahrzeugmarken aus der Saat gelesen - die "
              "Sonde kann die Karten\n   nicht sicher erkennen. KEINE ZAHL."
              % len(marken))
        return None

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = EM._ctx(browser, breite)
        seite = ctx.new_page()
        try:
            seite.goto(url, wait_until="domcontentloaded")
            seite.wait_for_timeout(3800)
            EM._saeen(seite, saat, still=True)
            B12._navigieren12(seite, "fahrzeuge", breite, [])
            seite.wait_for_timeout(1800)
            aus = seite.evaluate(HOEHEN_JS, marken)
        finally:
            ctx.close()
            browser.close()

    if not aus or (aus.get("anzahl") or 0) < 3:
        print("\U0001F534 Nur %s Karten gefunden - das ist keine Messung, das "
              "ist eine leere\n   Grundgesamtheit. KEINE ZAHL."
              % (aus or {}).get("anzahl"))
        return None
    return aus


def main(argv):
    breite = int(argv[0]) if argv else 390
    a = messen(breite)
    if a is None:
        return 2
    print("Fahrzeugkarten bei %d px  (%s)"
          % (breite, os.environ.get("EPK_INDEX", "index.html")))
    print("  Karten gefunden : %d" % a["anzahl"])
    print("  Median          : %s px" % a["median"])
    print("  kleinste        : %s px" % a["klein"])
    print("  groesste        : %s px" % a["gross"])
    print("  die ersten      : %s" % a["alle"])
    print("  Textlaenge einer Karte: %s Zeichen  - eine Karte traegt rund 90;"
          " deutlich mehr heisst, die Sonde hat die Liste erwischt." % a["textlaenge"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
