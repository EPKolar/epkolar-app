# -*- coding: utf-8 -*-
"""Der Themenschalter in SAFARIS Engine, auf einem iPhone-Profil.

🔴 DIE LETZTE UNGEMESSENE SCHICHT. Alles bisher lief in Chromium:
`hellmodus_ansichten.py`, `hellmodus_schalter_messen.py`,
`hellmodus_nach_dem_schalten.py`, `thema_schalter_ring_messen.py`,
`thema_echter_tipp_messen.py`. Fuenf Messungen, eine Engine.

Sebastian meldet den Mangel dreimal und ausdruecklich "am Handy". Sein Handy
laeuft nicht mit Chromium. Eine Messung, die die Engine nicht wechselt, kann
einen Engine-Unterschied prinzipiell nicht finden - das ist kein blinder
Riegel, sondern ein blindes Messgeraet.

Playwright bringt WebKit mit, also dieselbe Engine wie Safari, und ein
iPhone-Profil (Bildschirmmass, Pixelverhaeltnis, Kennung, Beruehrung). Naeher
kommt man ohne Geraet nicht.

WAS GEMESSEN WIRD
Derselbe Ablauf wie in `thema_echter_tipp_messen.py`: echte Fingertippen,
Lage vor jedem Tipp neu bestimmt, und nach jedem Tipp der Modus UND die
tatsaechliche Helligkeit. Dazu die CSS-Variablen - die Kur aus v3.9.980
setzt sie ueber `style.setProperty` auf `documentElement`, und ob das in
WebKit ankommt, ist eine eigene Frage.

🔴 GEGENPROBE IM SELBEN LAUF: dieselbe Messung in Chromium. Stimmen beide
ueberein, liegt es nicht an der Engine - und das ist dann ein Ergebnis, kein
Fehlschlag.
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

KNOPF_JS = r"""() => {
  const k = [...document.querySelectorAll('button')]
      .find(x => /Theme/i.test(x.getAttribute('title') || ''));
  if (!k) return null;
  const r = k.getBoundingClientRect();
  return {x: Math.round(r.left + r.width / 2),
          y: Math.round(r.top + r.height / 2),
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
  const w = getComputedStyle(document.documentElement);
  return {modus: modus,
          hell: hell(getComputedStyle(document.body).backgroundColor),
          koerper: getComputedStyle(document.body).backgroundColor,
          varBg: w.getPropertyValue('--bg').trim(),
          varTx: w.getPropertyValue('--tx').trim(),
          schema: w.colorScheme};
}"""


def lauf(pw, engine, url):
    treiber = getattr(pw, engine)
    geraet = pw.devices["iPhone 13"] if engine == "webkit" else None
    browser = treiber.launch()
    if geraet:
        ctx = browser.new_context(**geraet, color_scheme="dark")
    else:
        ctx = browser.new_context(viewport={"width": 390, "height": 844},
                                  is_mobile=True, has_touch=True,
                                  device_scale_factor=1, color_scheme="dark")
    ctx.add_init_script(INIT)
    ctx.add_init_script(NUTZER)
    ctx.route("**/rest/v1/**", lambda r: r.abort())
    ctx.route("**/auth/v1/**", lambda r: r.abort())
    seite = ctx.new_page()
    schritte = []
    try:
        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(4500)
        HA._saat(seite)
        seite.wait_for_timeout(2500)
        schritte.append(dict(seite.evaluate(STAND_JS), tipp=0))
        for n in range(1, 5):
            lage = seite.evaluate(KNOPF_JS)
            if not lage:
                schritte.append({"tipp": n, "fehler": "Knopf nicht gefunden"})
                break
            seite.touchscreen.tap(lage["x"], lage["y"])
            seite.wait_for_timeout(1200)
            schritte.append(dict(seite.evaluate(STAND_JS), tipp=n,
                                 knopf=lage["text"]))
    finally:
        ctx.close()
        browser.close()
    return schritte


def zeig(engine, schritte):
    print("\n=== %s" % engine.upper())
    for s in schritte:
        if "fehler" in s:
            print("   Tipp %d  \U0001F534 %s" % (s["tipp"], s["fehler"]))
            continue
        print("   %-7s Modus=%-7s hell=%-5s %-22s --bg=%-9s --tx=%-9s %s"
              % ("START" if s["tipp"] == 0 else "Tipp %d" % s["tipp"],
                 s["modus"], s["hell"], s["koerper"], s["varBg"] or "?",
                 s["varTx"] or "?",
                 "HELL" if (s["hell"] or 0) > 0.6 else "DUNKEL"))


def main(argv):
    from playwright.sync_api import sync_playwright
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port,
                                      os.environ.get("EPK_INDEX", "index.html"))
    alles = {}
    with sync_playwright() as pw:
        for engine in ("webkit", "chromium"):
            alles[engine] = lauf(pw, engine, url)
            zeig(engine, alles[engine])

    ziel = os.path.join(WURZEL, "docs", "befunde", "THEMA_IPHONE.json")
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps(alles, ensure_ascii=False, indent=1))

    # 🔴 Das Urteil: wechselt die Helligkeit in BEIDEN Engines bei jedem Tipp?
    schlimm = []
    for engine, schritte in alles.items():
        gute = [s for s in schritte if "fehler" not in s]
        for i in range(1, len(gute)):
            if abs((gute[i]["hell"] or 0) - (gute[i - 1]["hell"] or 0)) < 0.2:
                schlimm.append((engine, gute[i]["tipp"], gute[i]["hell"]))
    print()
    if schlimm:
        print("\U0001F534 Tippe ohne sichtbare Wirkung:")
        for e, n, h in schlimm:
            print("      %-9s Tipp %d, Helligkeit bleibt %s" % (e, n, h))
    else:
        print("\U0001F7E2 In BEIDEN Engines aendert jeder Tipp die Helligkeit.")
    print("geschrieben:", ziel)
    return 1 if schlimm else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
