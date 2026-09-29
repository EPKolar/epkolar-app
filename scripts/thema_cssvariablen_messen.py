# -*- coding: utf-8 -*-
"""Folgen die CSS-Variablen BEIDEN Themen - und belegt der Lauf das auch?

🔴 MIT EINGEBAUTER SELBSTPROBE. Ein erster Versuch dieser Gegenprobe hat die
Vorgabe still nicht umgestellt und zweimal denselben Hellmodus gemessen -
zwei identische Spalten, die aussahen wie ein Ergebnis. Dieser Lauf prueft
darum ZUERST, dass der gemessene Modus wirklich der verlangte ist, und
verweigert sonst die Zahlen.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mob_ansicht_messen as M           # noqa: E402
import hellmodus_ansichten as HA         # noqa: E402
from tab_sweep import INIT               # noqa: E402

NUTZER = ("try{var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
          "u.role='admin';u.monteurId='M1';u.name='Gerhard Steinbichler';"
          "u.rolle='Geschaeftsfuehrer';"
          "localStorage.setItem('epkolar_user',JSON.stringify(u));}catch(e){}")

MESSEN = """() => {
  const w = getComputedStyle(document.documentElement);
  const aus = {};
  for (const v of ['--bg', '--sb', '--cd', '--bd', '--tx', '--dm', '--mt',
                   '--calinv']) {
    aus[v] = w.getPropertyValue(v).trim() || '(nicht gesetzt)';
  }
  let modus = null;
  try { modus = localStorage.getItem('epk_theme'); } catch (e) {}
  aus.modus = modus;
  aus.koerper = getComputedStyle(document.body).backgroundColor;
  return aus;
}"""


def lauf(browser, url, thema):
    ctx = browser.new_context(viewport={"width": 390, "height": 844},
                              is_mobile=True, has_touch=True,
                              device_scale_factor=1, color_scheme="dark")
    ctx.add_init_script(INIT)
    ctx.add_init_script(NUTZER)
    ctx.add_init_script(
        "try{localStorage.setItem('epk_theme','" + thema + "');}catch(e){}")
    ctx.route("**/rest/v1/**", lambda r: r.abort())
    ctx.route("**/auth/v1/**", lambda r: r.abort())
    s = ctx.new_page()
    try:
        s.goto(url, wait_until="domcontentloaded")
        s.wait_for_timeout(4000)
        HA._saat(s)
        s.wait_for_timeout(1600)
        return s.evaluate(MESSEN)
    finally:
        ctx.close()


def main():
    from playwright.sync_api import sync_playwright
    port = M._server()
    url = "http://127.0.0.1:%d/index.html" % port
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        hell = lauf(b, url, "light")
        dunkel = lauf(b, url, "dark")
        b.close()

    # 🔴 SELBSTPROBE ZUERST.
    if hell.get("modus") != "light" or dunkel.get("modus") != "dark":
        print("\U0001F534 Die Vorgabe hat nicht gegriffen: gemessen %r und %r."
              % (hell.get("modus"), dunkel.get("modus")))
        print("   Das ist kein Ergebnis - NICHT gemessen.")
        return 2
    if hell.get("--bg") == dunkel.get("--bg"):
        print("\U0001F534 Beide Laeufe melden dasselbe --bg (%s). Entweder "
              "folgt die\n   Variable dem Thema nicht, oder die Laeufe messen "
              "denselben Zustand." % hell.get("--bg"))
        return 2

    print("%-10s %-22s %-22s" % ("", "HELL", "DUNKEL"))
    for k in ("--bg", "--sb", "--cd", "--bd", "--tx", "--dm", "--mt",
              "--calinv", "koerper"):
        gleich = "  <<< GLEICH" if hell.get(k) == dunkel.get(k) else ""
        print("%-10s %-22s %-22s%s" % (k, hell.get(k), dunkel.get(k), gleich))
    return 0


sys.exit(main())
