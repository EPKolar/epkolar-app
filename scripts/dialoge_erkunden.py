# -*- coding: utf-8 -*-
"""Welche Dialoge gibt es, und wie kommt man hinein?

🔴 DER GROESSTE BLINDE FLECK DES PRUEFSTANDS. Jeder Grundstand seit Wochen
endet mit dem Satz „keine geoeffneten Dialoge" - die Messreihe misst Ansichten
im Ruhezustand. Modale, Schubladen und Detailfenster sind NIE erfasst worden.
Alle Nullen der Messreihe gelten deshalb nur fuer den Ruhezustand.

Dieses Werkzeug misst nichts. Es sucht: welche Knoepfe oeffnen eine
Ueberlagerung, und woran erkennt man, dass sie offen ist. Erst wenn das
belegt ist, kann man drinnen messen - sonst misst man einen Dialog, der gar
nicht aufging, und meldet eine makellose Null.

Erkennungsmerkmal einer Ueberlagerung: ein Element mit `position: fixed`, das
mehr als ein Drittel des Schirms bedeckt und beim Ruhezustand nicht da war.
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

# Die Knoepfe, die vermutlich etwas oeffnen. Gesucht wird ueber den TEXT, weil
# die Datei keine Klassen fuer Dialoge fuehrt.
UEBERLAGERUNG_JS = r"""() => {
  const aus = [];
  for (const e of document.querySelectorAll('div,section,dialog')) {
    const s = getComputedStyle(e);
    if (s.position !== 'fixed') continue;
    const r = e.getBoundingClientRect();
    if (r.width * r.height < window.innerWidth * window.innerHeight / 3) continue;
    if (s.display === 'none' || s.visibility === 'hidden') continue;
    aus.push({b: Math.round(r.width), h: Math.round(r.height),
              text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 50)});
  }
  return aus;
}"""

KNOEPFE_JS = r"""() => {
  return [...document.querySelectorAll('button')]
    .filter(e => {
      const r = e.getBoundingClientRect();
      return r.width && r.height && !e.disabled;
    })
    .map((e, i) => ({i: i, text: (e.innerText || '').replace(/\s+/g, ' ')
                       .trim().slice(0, 40),
                     titel: e.getAttribute('title'),
                     aria: e.getAttribute('aria-label')}))
    .filter(x => x.text || x.titel || x.aria);
}"""


def _gruppe(kuerzel):
    for _, modul, navi, argzahl in GRUPPEN:
        if kuerzel in getattr(modul, "ANSICHTEN", {}):
            return modul, navi, argzahl
    return None, None, None


def main(argv):
    from playwright.sync_api import sync_playwright
    ansichten = argv or ["fahrzeuge", "as_liste", "mitarbeiter"]
    breite = 1440
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port,
                                      os.environ.get("EPK_INDEX", "index.html"))
    saat = SAAT.saat()
    fund = {}

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for kuerzel in ansichten:
            modul, navi, argzahl = _gruppe(kuerzel)
            if modul is None:
                print("   \U0001F534 unbekannte Ansicht: %s" % kuerzel)
                continue
            ctx = EM._ctx(browser, breite)
            seite = ctx.new_page()
            treffer = []
            try:
                seite.goto(url, wait_until="domcontentloaded")
                seite.wait_for_timeout(3800)
                EM._saeen(seite, saat, still=True)
                f = getattr(modul, navi)
                (f(seite, kuerzel, breite, []) if argzahl == 4
                 else f(seite, kuerzel, breite))
                seite.wait_for_timeout(1600)

                ruhe = seite.evaluate(UEBERLAGERUNG_JS)
                knoepfe = seite.evaluate(KNOEPFE_JS)
                print("\n=== %s: %d Knoepfe, im Ruhezustand %d Ueberlagerungen"
                      % (kuerzel, len(knoepfe), len(ruhe)))

                for k in knoepfe[:40]:
                    try:
                        seite.evaluate(
                            "(i)=>{const b=[...document.querySelectorAll('button')]"
                            ".filter(e=>{const r=e.getBoundingClientRect();"
                            "return r.width&&r.height&&!e.disabled;});"
                            "if(b[i]) b[i].click();}", k["i"])
                        seite.wait_for_timeout(700)
                        jetzt = seite.evaluate(UEBERLAGERUNG_JS)
                        if len(jetzt) > len(ruhe):
                            treffer.append({"knopf": k["text"] or k["titel"]
                                            or k["aria"],
                                            "overlay": jetzt[-1]["text"][:40],
                                            "groesse": "%dx%d"
                                            % (jetzt[-1]["b"], jetzt[-1]["h"])})
                            print("   \U0001F7E2 %-38s -> %s"
                                  % ((k["text"] or k["titel"] or k["aria"])[:38],
                                     jetzt[-1]["text"][:40]))
                            seite.keyboard.press("Escape")
                            seite.wait_for_timeout(500)
                            # Wenn Escape nicht schliesst: neu aufbauen.
                            if len(seite.evaluate(UEBERLAGERUNG_JS)) > len(ruhe):
                                (f(seite, kuerzel, breite, []) if argzahl == 4
                                 else f(seite, kuerzel, breite))
                                seite.wait_for_timeout(1200)
                    except Exception as e:
                        print("   (Knopf %d: %s)" % (k["i"], str(e)[:60]))
            finally:
                ctx.close()
            fund[kuerzel] = treffer
        browser.close()

    ziel = os.path.join(WURZEL, "docs", "befunde", "DIALOGE.json")
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps(fund, ensure_ascii=False, indent=1))
    print("\nGefundene Oeffner: %s"
          % {k: len(v) for k, v in fund.items()})
    print("geschrieben:", ziel)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
