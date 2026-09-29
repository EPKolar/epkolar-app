# -*- coding: utf-8 -*-
"""Wie oft feuert der Themenknopf bei EINEM echten Fingertipp?

🔴 DIE SCHICHT, DIE ALLE BISHERIGEN MESSUNGEN AUSGELASSEN HABEN.
`hellmodus_ansichten.py`, `hellmodus_schalter_messen.py`,
`hellmodus_nach_dem_schalten.py` und `thema_schalter_ring_messen.py` rufen
alle `element.click()` im Skript auf. Ein Finger auf Glas erzeugt etwas
anderes: `touchstart` -> `touchend` -> `click`, und je nach Bauweise der
Seite kommt der Klick ZWEIMAL an ("Ghost Click").

Genau dagegen gibt es seit v3.9.721 die 350-ms-Sperre - sie war die Antwort
auf denselben gemeldeten Mangel. Sperrt sie zu kurz, kommt der zweite Tipp
durch. Und dann gilt:

    alter Ringtausch:  Auto -> Hell -> Dunkel      = bleibt dunkel
    neuer Zweiweg:     Dunkel -> Hell -> Dunkel    = bleibt dunkel

BEIDE Bauformen zeigen dasselbe Symptom, wenn ein Tipp doppelt feuert. Ein
Lauf mit `element.click()` kann das prinzipiell nicht sehen: er feuert einmal.

WAS GEMESSEN WIRD
Gezaehlt wird, wie oft der Behandler je PHYSISCHEM Tipp laeuft - ueber einen
Lauscher in der Einfangphase am Knopf, der nichts veraendert, sondern nur
mitschreibt. Dazu die Zeitabstaende: liegt der zweite Aufruf ueber 350 ms,
laesst die Sperre ihn durch.

🔴 SELBSTPROBE: der Lauscher muss bei einem bekannten EINZELKLICK genau
einmal zaehlen. Zaehlt er dort schon zwei, misst er sich selbst.
"""
import io
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
WURZEL = os.path.dirname(HIER)

import mob_ansicht_messen as M           # noqa: E402
import hellmodus_ansichten as HA         # noqa: E402
from tab_sweep import INIT               # noqa: E402

NUTZER = ("try{var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
          "u.role='admin';u.monteurId='M1';u.name='Gerhard Steinbichler';"
          "u.rolle='Geschaeftsfuehrer';"
          "localStorage.setItem('epkolar_user',JSON.stringify(u));"
          "localStorage.removeItem('epk_theme');}catch(e){}")

# Lauscher in der EINFANGPHASE: er sieht jeden Klick, bevor React ihn
# bekommt, und aendert nichts.
LAUSCHER_JS = r"""() => {
  const k = [...document.querySelectorAll('button')]
      .find(x => /Theme/i.test(x.getAttribute('title') || ''));
  if (!k) return false;
  window.__tippe = [];
  window.__zeug = [];
  const merken = (art) => (e) => {
    window.__zeug.push({art: art, t: Math.round(performance.now()),
                        vertraut: !!e.isTrusted});
  };
  for (const art of ['touchstart', 'touchend', 'pointerdown', 'pointerup',
                     'mousedown', 'mouseup', 'click']) {
    k.addEventListener(art, merken(art), true);
  }
  return true;
}"""

STAND_JS = r"""() => {
  const hell = c => {
    const m = /rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/.exec(c || '');
    if (!m) return null;
    return Math.round((0.2126 * +m[1] + 0.7152 * +m[2] + 0.0722 * +m[3])
                      / 255 * 100) / 100;
  };
  let modus = null;
  try { modus = localStorage.getItem('epk_theme'); } catch (e) {}
  return {modus: modus,
          hell: hell(getComputedStyle(document.body).backgroundColor),
          ereignisse: (window.__zeug || []).slice()};
}"""

LEEREN_JS = "() => { window.__zeug = []; }"

KNOPF_JS = r"""() => {
  const k = [...document.querySelectorAll('button')]
      .find(x => /Theme/i.test(x.getAttribute('title') || ''));
  if (!k) return null;
  const r = k.getBoundingClientRect();
  return {x: Math.round(r.left + r.width / 2),
          y: Math.round(r.top + r.height / 2),
          w: Math.round(r.width), h: Math.round(r.height)};
}"""


def main(argv):
    from playwright.sync_api import sync_playwright
    breite = int(argv[0]) if argv else 390
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port,
                                      os.environ.get("EPK_INDEX", "index.html"))
    bericht = {"breite": breite, "tippe": []}

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": breite, "height": 844},
            is_mobile=True, has_touch=True,
            device_scale_factor=1, color_scheme="dark")
        ctx.add_init_script(INIT)
        ctx.add_init_script(NUTZER)
        ctx.route("**/rest/v1/**", lambda r: r.abort())
        ctx.route("**/auth/v1/**", lambda r: r.abort())
        seite = ctx.new_page()
        try:
            seite.goto(url, wait_until="domcontentloaded")
            seite.wait_for_timeout(4000)
            HA._saat(seite)
            seite.wait_for_timeout(1600)

            if not seite.evaluate(LAUSCHER_JS):
                print("\U0001F534 Kein Themenknopf gefunden - NICHT gemessen.")
                return 2
            lage = seite.evaluate(KNOPF_JS)
            print("Knopf bei (%d,%d), %dx%d px" % (lage["x"], lage["y"],
                                                   lage["w"], lage["h"]))

            vor = seite.evaluate(STAND_JS)
            print("START   Modus=%-7s hell=%s" % (vor["modus"], vor["hell"]))

            for n in range(1, 5):
                # 🔴 VOR JEDEM TIPP NEU SUCHEN. Der erste Entwurf hat die
                #    Lage EINMAL gemerkt und viermal dorthin getippt. Nach dem
                #    ersten Tipp wandert der Knopf aber um 56 px nach unten -
                #    die Tippen 2 bis 4 trafen den Kopfbereich daneben und
                #    erzeugten GAR KEIN Ereignis. Das sah aus wie "der Knopf
                #    reagiert nicht mehr" und war mein eigener Fehlgriff.
                lage = seite.evaluate(KNOPF_JS)
                if not lage:
                    print("   🔴 Knopf vor Tipp %d nicht gefunden - "
                          "NICHT gemessen." % n)
                    break
                seite.evaluate(LEEREN_JS)
                # 🔴 ECHTER TIPP, nicht element.click(): tap() erzeugt die
                #    volle Kette touchstart/touchend und laesst den Browser
                #    den Klick daraus ableiten - genau wie ein Finger.
                seite.touchscreen.tap(lage["x"], lage["y"])
                seite.wait_for_timeout(1100)
                jetzt = seite.evaluate(STAND_JS)
                ev = jetzt["ereignisse"]
                klicks = [e for e in ev if e["art"] == "click"]
                abstand = (klicks[-1]["t"] - klicks[0]["t"]) if len(klicks) > 1 else 0
                bericht["tippe"].append(
                    {"nr": n, "modus": jetzt["modus"], "hell": jetzt["hell"],
                     "klicks": len(klicks), "abstand_ms": abstand,
                     "kette": [e["art"] for e in ev]})
                print("Tipp %d  Modus=%-7s hell=%-5s | click-Ereignisse: %d"
                      "%s\n        Kette: %s"
                      % (n, jetzt["modus"], jetzt["hell"], len(klicks),
                         ("  Abstand %d ms" % abstand) if abstand else "",
                         " ".join(e["art"] for e in ev)))
        finally:
            ctx.close()
            browser.close()

    doppelt = [t for t in bericht["tippe"] if t["klicks"] > 1]
    ziel = os.path.join(WURZEL, "docs", "befunde",
                        "THEMA_ECHTER_TIPP_%d.json" % breite)
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps(bericht, ensure_ascii=False, indent=1))
    if doppelt:
        print("\n\U0001F534 %d von %d Tippen erzeugen MEHR ALS EINEN Klick."
              % (len(doppelt), len(bericht["tippe"])))
        for t in doppelt:
            print("      Tipp %d: %d Klicks, %d ms auseinander%s"
                  % (t["nr"], t["klicks"], t["abstand_ms"],
                     "  -> Sperre (350 ms) laesst ihn DURCH"
                     if t["abstand_ms"] >= 350 else ""))
    else:
        print("\n\U0001F7E2 Jeder Tipp erzeugt genau EIN click-Ereignis.")
    # Und der eigentliche Punkt: wechselt die Helligkeit bei jedem Tipp?
    stumm = [t for t in bericht["tippe"][1:]
             if abs((t["hell"] or 0)
                    - (bericht["tippe"][t["nr"] - 2]["hell"] or 0)) < 0.2]
    if stumm:
        print("\U0001F534 %d Tippe aendern die Helligkeit NICHT: %s"
              % (len(stumm), [t["nr"] for t in stumm]))
    print("geschrieben:", ziel)
    return 1 if (doppelt or stumm) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
