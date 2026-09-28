# -*- coding: utf-8 -*-
"""Wie lang ist die Tab-Reihenfolge einer Ansicht?

🔴 WARUM DAS VOR DEM BAU GEMESSEN WIRD
Die Arbeitsscheinliste hat drei anklickbare Tabellenzellen je Zeile, und die
Zeile wird bei der echten Saat 185 mal gerendert. Gaebe man jeder Zelle einen
Tab-Stopp, waeren das 555 Stopps allein fuer diese eine Tabelle. Eine
Tab-Reihenfolge, durch die man nicht mehr durchkommt, ist kein Zugang - sie ist
ein neuer Mangel mit dem Aussehen einer Kur.

Gemessen wird, was der Browser WIRKLICH anbietet: jedes sichtbare Element mit
einem Tabindex >= 0 oder von Natur aus fokussierbar. Vorher und nachher, mit
derselben Saat.

Aufruf:
    python scripts/tabreihenfolge_messen.py as_liste planung
"""
import io
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
WURZEL = os.path.dirname(HIER)

import mob_ansicht_messen as M           # noqa: E402
import b3_vier_ansichten_messen as B     # noqa: E402
import b3_stufen_8_11_messen as S        # noqa: E402
import b3_stufen_12_15_messen as B12     # noqa: E402
import echtmengen_saat as SAAT           # noqa: E402
import echtmengen_messen as EM           # noqa: E402

GRUPPEN = [("4-7", B, "_navigieren", 3),
           ("8-11", S, "_navigieren8", 4),
           ("12-15", B12, "_navigieren12", 4)]

JS = r"""() => {
  const sichtbar = (e) => {
    const r = e.getBoundingClientRect();
    if (!r.width || !r.height) return false;
    const s = getComputedStyle(e);
    return s.visibility !== 'hidden' && s.display !== 'none';
  };
  const nativ = 'a[href],button,input,select,textarea,summary,[contenteditable]';
  const alle = [...document.querySelectorAll(nativ + ',[tabindex]')]
      .filter(e => sichtbar(e))
      .filter(e => (e.getAttribute('tabindex') || '0') !== '-1')
      .filter(e => !e.disabled);
  const nachTag = {};
  const rollen = {};
  let ohne_namen = 0;
  for (const e of alle) {
    const t = e.tagName.toLowerCase();
    nachTag[t] = (nachTag[t] || 0) + 1;
    const rolle = e.getAttribute('role') || '(ohne)';
    rollen[rolle] = (rollen[rolle] || 0) + 1;
    const name = (e.getAttribute('aria-label') || e.getAttribute('title')
                  || (e.innerText || '').trim());
    if (!name) ohne_namen++;
  }
  // Wie viele davon haben einen Tastenbehandler? Das laesst sich von aussen
  // nicht ablesen - gemeldet wird deshalb nur, was ablesbar ist.
  const mit_tabindex = alle.filter(e => e.hasAttribute('tabindex'));
  return {stopps: alle.length, nach_tag: nachTag, rollen: rollen,
          ohne_namen: ohne_namen,
          mit_tabindex: mit_tabindex.length};
}"""


def _gruppe(kuerzel):
    for _, modul, navi, argzahl in GRUPPEN:
        if kuerzel in getattr(modul, "ANSICHTEN", {}):
            return modul, navi, argzahl
    return None, None, None


def main(argv):
    from playwright.sync_api import sync_playwright
    ansichten = argv or ["as_liste", "planung"]
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port,
                                      os.environ.get("EPK_INDEX", "index.html"))
    saat = SAAT.saat()
    aus = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for kuerzel in ansichten:
            modul, navi, argzahl = _gruppe(kuerzel)
            if modul is None:
                print("   \U0001F534 unbekannte Ansicht: %s" % kuerzel)
                continue
            for breite in (390, 1440):
                ctx = EM._ctx(browser, breite)
                seite = ctx.new_page()
                try:
                    seite.goto(url, wait_until="domcontentloaded")
                    seite.wait_for_timeout(3800)
                    EM._saeen(seite, saat, still=True)
                    f = getattr(modul, navi)
                    (f(seite, kuerzel, breite, []) if argzahl == 4
                     else f(seite, kuerzel, breite))
                    seite.wait_for_timeout(1600)
                    e = seite.evaluate(JS)
                finally:
                    ctx.close()
                e.update({"kuerzel": kuerzel, "breite": breite})
                aus.append(e)
                print("  %-12s %5d px   Tab-Stopps: %4d   davon mit tabindex: "
                      "%3d   ohne Namen: %3d"
                      % (kuerzel, breite, e["stopps"], e["mit_tabindex"],
                         e["ohne_namen"]))
        browser.close()
    ziel = os.path.join(WURZEL, "docs", "befunde", "TABREIHENFOLGE.json")
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps({"aufnahmen": aus}, ensure_ascii=False, indent=1))
    print("\ngeschrieben:", ziel)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
