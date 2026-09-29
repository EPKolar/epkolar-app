# -*- coding: utf-8 -*-
"""Der beschriftete Weg: Mehr-Menue oeffnen, "Hell" antippen, hell?

🔴 DIE FRAGE IST EINE ANDERE ALS BISHER. Sechs Messungen haben belegt, dass
der Kopfknopf umschaltet - in Chromium und in WebKit, mit echten
Fingertippen. Sebastian meldet den Mangel trotzdem zum dritten Mal.

Hier wird nicht mehr geprueft, ob ein Ring korrekt weiterzaehlt, sondern ob
der DIREKTE Weg traegt: man oeffnet "Mehr", tippt auf den Knopf, auf dem
"Hell" steht, und es ist hell. Ein Weg ohne Zwischenzustaende kann nicht
"zwei Tippen zu weit" gehen und braucht kein Gedaechtnis.

Gemessen in BEIDEN Engines (Chromium und WebKit auf iPhone-Profil) und mit
echten Tippen, weil beides schon einmal einen Unterschied gemacht hat.

🔴 MIT GEGENPROBE: nach "Hell" wird "Dunkel" getippt. Bleibt es dann hell,
misst der Lauf nicht den Schalter, sondern irgendetwas anderes.
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

MEHR_JS = r"""() => {
  const nav = document.querySelector('.bottom-nav');
  if (!nav) return 'keine-fussleiste';
  const mehr = [...nav.querySelectorAll('button')]
      .find(b => (b.getAttribute('aria-label') || '') === 'Mehr');
  if (!mehr) return 'kein-mehr-knopf';
  const r = mehr.getBoundingClientRect();
  return {x: Math.round(r.left + r.width / 2),
          y: Math.round(r.top + r.height / 2)};
}"""

# Der Knopf im Menue, auf dem das Wort steht - gesucht ueber den TEXT, nicht
# ueber eine Position: eine Position kann sich verschieben, ein Wort nicht.
WAHL_JS = r"""(wort) => {
  const k = [...document.querySelectorAll('button[aria-pressed]')]
      .find(b => (b.innerText || '').indexOf(wort) >= 0);
  if (!k) return null;
  const r = k.getBoundingClientRect();
  if (!r.width || !r.height) return null;
  return {x: Math.round(r.left + r.width / 2),
          y: Math.round(r.top + r.height / 2),
          gedrueckt: k.getAttribute('aria-pressed'),
          text: (k.innerText || '').trim()};
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
          hell: hell(getComputedStyle(document.body).backgroundColor)};
}"""


def lauf(pw, engine, url):
    treiber = getattr(pw, engine)
    browser = treiber.launch()
    if engine == "webkit":
        ctx = browser.new_context(**pw.devices["iPhone 13"],
                                  color_scheme="dark")
    else:
        ctx = browser.new_context(viewport={"width": 390, "height": 844},
                                  is_mobile=True, has_touch=True,
                                  device_scale_factor=1, color_scheme="dark")
    ctx.add_init_script(INIT)
    ctx.add_init_script(NUTZER)
    ctx.route("**/rest/v1/**", lambda r: r.abort())
    ctx.route("**/auth/v1/**", lambda r: r.abort())
    seite = ctx.new_page()
    aus = {"engine": engine, "schritte": []}
    try:
        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(4500)
        HA._saat(seite)
        seite.wait_for_timeout(2500)
        aus["start"] = seite.evaluate(STAND_JS)

        mehr = seite.evaluate(MEHR_JS)
        if not isinstance(mehr, dict):
            aus["fehler"] = "Mehr-Knopf: %s" % mehr
            return aus
        seite.touchscreen.tap(mehr["x"], mehr["y"])
        seite.wait_for_timeout(900)

        for wort in ("Hell", "Dunkel", "Hell"):
            ziel = seite.evaluate(WAHL_JS, wort)
            if not ziel:
                aus["schritte"].append({"wort": wort,
                                        "fehler": "Knopf nicht sichtbar"})
                break
            seite.touchscreen.tap(ziel["x"], ziel["y"])
            seite.wait_for_timeout(1100)
            s = seite.evaluate(STAND_JS)
            aus["schritte"].append({"wort": wort, "modus": s["modus"],
                                    "hell": s["hell"],
                                    "vorher_gedrueckt": ziel["gedrueckt"]})
    finally:
        ctx.close()
        browser.close()
    return aus


def main(argv):
    from playwright.sync_api import sync_playwright
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port,
                                      os.environ.get("EPK_INDEX", "index.html"))
    alles, schlimm = [], []
    with sync_playwright() as pw:
        for engine in ("chromium", "webkit"):
            r = lauf(pw, engine, url)
            alles.append(r)
            print("\n=== %s" % engine.upper())
            if "fehler" in r:
                print("   \U0001F534 %s - NICHT gemessen" % r["fehler"])
                schlimm.append((engine, r["fehler"]))
                continue
            print("   START            Modus=%-7s hell=%s"
                  % (r["start"]["modus"], r["start"]["hell"]))
            for s in r["schritte"]:
                if "fehler" in s:
                    print("   Tipp auf %-8s \U0001F534 %s" % (s["wort"], s["fehler"]))
                    schlimm.append((engine, s["wort"] + ": " + s["fehler"]))
                    continue
                soll = s["wort"] == "Hell"
                ist = (s["hell"] or 0) > 0.6
                marke = "\U0001F7E2" if ist == soll else "\U0001F534 FALSCH"
                print("   Tipp auf %-8s Modus=%-7s hell=%-5s %s"
                      % (s["wort"], s["modus"], s["hell"], marke))
                if ist != soll:
                    schlimm.append((engine, "%s ergab hell=%s"
                                    % (s["wort"], s["hell"])))

    ziel = os.path.join(WURZEL, "docs", "befunde", "THEMA_MEHRMENUE.json")
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps(alles, ensure_ascii=False, indent=1))
    print()
    if schlimm:
        print("\U0001F534 %d Fehlschlaege:" % len(schlimm))
        for e, w in schlimm:
            print("      %-9s %s" % (e, w))
    else:
        print("\U0001F7E2 In BEIDEN Engines: 'Hell' macht hell, 'Dunkel' "
              "macht dunkel - beim ersten Tipp.")
    print("geschrieben:", ziel)
    return 1 if schlimm else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
