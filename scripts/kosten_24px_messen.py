# -*- coding: utf-8 -*-
"""Was kostet das Heben? Die Hoehe der TRAGENDEN Zeile, nicht die des Knopfs.

🔴 Ein Knopf von 14 auf 24 px zu heben macht die Tabellenzeile nur dann
hoeher, wenn er in dieser Zeile das HOECHSTE ist. Steht daneben etwas
Groesseres, kostet die Hebung NICHTS. Das ist der Unterschied zwischen einer
begruendeten Entscheidung und einer Vermutung.
"""
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)
import mob_ansicht_messen as M
import b3_vier_ansichten_messen as B
import b3_stufen_8_11_messen as S
import b3_stufen_12_15_messen as B12
import echtmengen_saat as SAAT
import echtmengen_messen as EM

GRUPPEN = [(B, "_navigieren", 3), (S, "_navigieren8", 4), (B12, "_navigieren12", 4)]

JS = r"""(sel) => {
  const aus = [];
  for (const e of document.querySelectorAll(sel)) {
    const r = e.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    if (Math.min(r.width, r.height) >= 24) continue;
    const zelle = e.closest('td,th,li,div');
    const zeile = e.closest('tr') || (zelle && zelle.parentElement);
    aus.push({
      knopf: [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
      text: (e.innerText || '').trim().slice(0, 10),
      aria: e.getAttribute('aria-label'),
      zelle: zelle ? [Math.round(zelle.getBoundingClientRect().width),
                      Math.round(zelle.getBoundingClientRect().height)] : null,
      zeile: zeile ? [Math.round(zeile.getBoundingClientRect().width),
                      Math.round(zeile.getBoundingClientRect().height)] : null,
      zeile_tag: zeile ? zeile.tagName.toLowerCase() : null
    });
  }
  return aus;
}"""

SEL = 'button,[role="button"],a,summary,input[type="checkbox"]'


def _navi(seite, kuerzel, breite):
    for modul, name, argzahl in GRUPPEN:
        if kuerzel in getattr(modul, "ANSICHTEN", {}):
            f = getattr(modul, name)
            return (f(seite, kuerzel, breite, []) if argzahl == 4
                    else f(seite, kuerzel, breite))
    raise SystemExit("unbekannte Ansicht %s" % kuerzel)


def main(argv):
    from playwright.sync_api import sync_playwright
    port = M._server()
    url = "http://127.0.0.1:%d/index.html" % port
    saat = SAAT.saat()
    alles = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for kuerzel in argv:
            ctx = EM._ctx(b, 1440)
            s = ctx.new_page()
            try:
                s.goto(url, wait_until="domcontentloaded")
                s.wait_for_timeout(3800)
                EM._saeen(s, saat, still=True)
                _navi(s, kuerzel, 1440)
                s.wait_for_timeout(1600)
                fund = s.evaluate(JS, SEL)
                alles[kuerzel] = fund
                print("\n=== %s: %d unter 24 px" % (kuerzel, len(fund)))
                gesehen = set()
                for x in fund:
                    k = (tuple(x["knopf"]), x["aria"], tuple(x["zeile"] or []))
                    if k in gesehen:
                        continue
                    gesehen.add(k)
                    print("   Knopf %sx%s %-22r  Zelle %s  %s %s"
                          % (x["knopf"][0], x["knopf"][1],
                             (x["aria"] or x["text"])[:22], x["zelle"],
                             x["zeile_tag"], x["zeile"]))
            finally:
                ctx.close()
        b.close()
    with open(os.path.join(WURZEL, "docs", "befunde",
                           "KOSTEN_24PX.json"), "w", encoding="utf-8",
              newline="") as f:
        json.dump(alles, f, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["planung", "zeit", "fahrzeuge",
                                   "auswertungen", "werkzeuge"]))
