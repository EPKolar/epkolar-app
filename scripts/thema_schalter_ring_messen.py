# -*- coding: utf-8 -*-
"""Aendert JEDER Tipp auf den Themenknopf sichtbar etwas?

🔴 DER GEMELDETE FALL, UND WARUM DREI MESSUNGEN IHN VORHER NICHT SAHEN.
Sebastian, 29.09.2026: *"wenn ich mobil auf hell schalte bleibt es dunkel und
wird nicht weiss."*

  * `hellmodus_ansichten.py` misst 32 Ansichten mit `epk_theme='light'` und
    meldet 0 dunkle - es setzt die Wahl VOR dem Laden.
  * `hellmodus_schalter_messen.py` betaetigt den Schalter und sieht ihn
    wirken - es misst EINEN Tipp.
  * `hellmodus_nach_dem_schalten.py` geht nach dem Umschalten durch alle
    Ansichten - alle hell.

Alle drei richtig gemessen, und keine konnte den Fall sehen. Er liegt im
RING: Hell -> Dunkel -> Auto -> Hell. Auf einem Telefon mit dunklem
Betriebssystem sehen **Dunkel und Auto gleich aus**. Wer auf Dunkel steht,
tippt einmal, sieht keine Aenderung, tippt wieder - und die 350-ms-Sperre
gegen Geisterklicks (v3.9.721) verschluckt den zweiten Tipp.

Gemessen vor der Kur, 390 px, OS dunkel, keine gespeicherte Wahl:

    START  Auto    rgb(15,17,23)     DUNKEL
    Tipp 1 light   rgb(240,242,245)  HELL
    Tipp 2 dark    rgb(15,17,23)     DUNKEL
    Tipp 3 system  rgb(15,17,23)     DUNKEL   <- keine sichtbare Aenderung
    Tipp 4 light   rgb(240,242,245)  HELL

WAS DIESES WERKZEUG PRUEFT
Nicht "der Schalter wirkt" - das war nie die Frage. Sondern: aendert sich die
HELLIGKEIT bei JEDEM Tipp? Ein Tipp ohne sichtbare Wirkung ist der Befund,
auch wenn der Modus dahinter korrekt umspringt.
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

# 🔴 Ausgangslage GENAU wie beim Nutzer: Betriebssystem dunkel, keine
#    gespeicherte Wahl. Wer hier 'light' vorbelegt, misst einen anderen Fall.
NUTZER = ("try{var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
          "u.role='admin';u.monteurId='M1';u.name='Gerhard Steinbichler';"
          "u.rolle='Geschaeftsfuehrer';"
          "localStorage.setItem('epkolar_user',JSON.stringify(u));"
          "localStorage.removeItem('epk_theme');}catch(e){}")

STAND_JS = r"""() => {
  const hell = c => {
    const m = /rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/.exec(c || '');
    if (!m) return null;
    return Math.round((0.2126 * +m[1] + 0.7152 * +m[2] + 0.0722 * +m[3])
                      / 255 * 100) / 100;
  };
  let modus = null;
  try { modus = localStorage.getItem('epk_theme'); } catch (e) {}
  const b = getComputedStyle(document.body).backgroundColor;
  const k = [...document.querySelectorAll('button')]
      .find(x => /Theme/i.test(x.getAttribute('title') || ''));
  return {modus: modus, koerper: b, hell: hell(b),
          knopf: k ? (k.innerText || '').trim() : null,
          titel: k ? k.getAttribute('title') : null};
}"""

TIPP_JS = r"""() => {
  const k = [...document.querySelectorAll('button')]
      .find(x => /Theme/i.test(x.getAttribute('title') || ''));
  if (!k) return false;
  k.click();
  return true;
}"""

TIPPE = 6


def main(argv):
    from playwright.sync_api import sync_playwright
    breite = int(argv[0]) if argv else 390
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port,
                                      os.environ.get("EPK_INDEX", "index.html"))
    stufen = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": breite, "height": 844},
            is_mobile=breite < 600, has_touch=breite < 600,
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
            s = seite.evaluate(STAND_JS)
            if not s.get("titel"):
                print("\U0001F534 Kein Themenknopf gefunden. Das ist kein "
                      "Ergebnis, das ist ein\n   misslungener Griff - NICHT "
                      "gemessen.")
                return 2
            stufen.append(s)
            print("Breite %d px, Betriebssystem DUNKEL, keine gespeicherte "
                  "Wahl" % breite)
            print("START      Modus=%-7s %-22s hell=%-5s Knopf %r"
                  % (s["modus"], s["koerper"], s["hell"], s["knopf"]))
            print("           Titel: %s" % s["titel"])
            for n in range(1, TIPPE + 1):
                if not seite.evaluate(TIPP_JS):
                    print("   \U0001F534 Knopf nach Tipp %d nicht mehr da - "
                          "NICHT gemessen." % n)
                    return 2
                seite.wait_for_timeout(900)
                s = seite.evaluate(STAND_JS)
                stufen.append(s)
                print("Tipp %d     Modus=%-7s %-22s hell=%-5s -> %s"
                      % (n, s["modus"], s["koerper"], s["hell"],
                         "HELL" if (s["hell"] or 0) > 0.6 else "DUNKEL"))
        finally:
            ctx.close()
            browser.close()

    # 🔴 Der Befund ist ein Tipp OHNE sichtbare Aenderung - nicht ein falscher
    #    Modus. Ein Ring, dessen Zustaende korrekt umspringen und gleich
    #    aussehen, ist fuer einen Menschen kaputt.
    stumm = []
    for i in range(1, len(stufen)):
        vor, nach = stufen[i - 1], stufen[i]
        if abs((nach["hell"] or 0) - (vor["hell"] or 0)) < 0.2:
            stumm.append((i, vor["modus"], nach["modus"], nach["hell"]))

    ziel = os.path.join(WURZEL, "docs", "befunde",
                        "THEMA_RING_%d.json" % breite)
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps({"breite": breite, "stufen": stufen, "stumm": stumm},
                   ensure_ascii=False, indent=1))
    if stumm:
        print("\n\U0001F534 %d von %d Tippen aendern SICHTBAR NICHTS:"
              % (len(stumm), TIPPE))
        for i, a, b, h in stumm:
            print("      Tipp %d: %s -> %s, Helligkeit bleibt %s"
                  % (i, a, b, h))
        print("   Genau so entsteht 'ich schalte auf hell und es bleibt "
              "dunkel'.")
    else:
        print("\n\U0001F7E2 Alle %d Tippen aendern die Helligkeit sichtbar."
              % TIPPE)
    print("geschrieben:", ziel)
    return 1 if stumm else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
