# -*- coding: utf-8 -*-
"""Am Schirm durchtabben, mit Enter UND Leertaste ausloesen, Fokusring messen.

🔴 DAS IST DER TEIL, DEN EIN QUELLTEXTRIEGEL NICHT PRUEFEN KANN. Er sieht, dass
`tabIndex` und `onKeyDown` dastehen. Er sieht nicht, ob der Fokus dort
ankommt, ob die Taste wirklich etwas ausloest, und ob ein Mensch sieht, wo er
gerade steht.

Gemessen wird je Sortierkopf:
  1. Er ist mit der Tabulatortaste erreichbar (Fokus landet auf ihm).
  2. Der Fokusring ist SICHTBAR - `outline-width` groesser als 0 im Zustand
     `:focus-visible`, gemessen nach echtem Tabben, nicht nach `.focus()`.
     (Ein `.focus()` per Skript loest `:focus-visible` in Chromium NICHT
     zuverlaessig aus - deshalb wird getabbt.)
  3. Die EINGABETASTE loest die Sortierung aus - nachgewiesen daran, dass sich
     die Reihenfolge der ersten Tabellenzeile aendert.
  4. Die LEERTASTE ebenso.
  5. Gegenprobe: die Leertaste rollt die Seite NICHT - `preventDefault` wirkt.
"""
import io
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
WURZEL = os.path.dirname(HIER)

import mob_ansicht_messen as M           # noqa: E402
import b3_stufen_8_11_messen as S        # noqa: E402
import echtmengen_saat as SAAT           # noqa: E402
import echtmengen_messen as EM           # noqa: E402

ERSTE_ZEILE = """() => {
  const tr = document.querySelector('tbody tr');
  return tr ? (tr.innerText || '').replace(/\\s+/g, ' ').slice(0, 60) : null;
}"""

FOKUS = """() => {
  const e = document.activeElement;
  if (!e || e === document.body) return null;
  const s = getComputedStyle(e);
  return {tag: e.tagName.toLowerCase(),
          rolle: e.getAttribute('role'),
          text: (e.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 28),
          ring: parseFloat(s.outlineWidth) || 0,
          ringfarbe: s.outlineColor,
          stil: s.outlineStyle};
}"""


def main(argv):
    from playwright.sync_api import sync_playwright
    wieviele = int(argv[0]) if argv else 5
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port,
                                      os.environ.get("EPK_INDEX", "index.html"))
    saat = SAAT.saat()
    bericht = {"geprueft": [], "breite": 1440}
    fehler = 0

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = EM._ctx(browser, 1440)
        seite = ctx.new_page()
        try:
            seite.goto(url, wait_until="domcontentloaded")
            seite.wait_for_timeout(3800)
            EM._saeen(seite, saat, still=True)
            S._navigieren8(seite, "as_liste", 1440, [])
            seite.wait_for_timeout(1800)

            # Bis zum ersten Sortierkopf tabben - und dabei zaehlen, wie viele
            # Stopps davor liegen. Das ist selbst ein Befund.
            seite.evaluate("() => document.body.focus()")
            gefunden = 0
            davor = 0
            for schritt in range(1200):
                seite.keyboard.press("Tab")
                f = seite.evaluate(FOKUS)
                if not f:
                    continue
                if f["tag"] != "th" or f["rolle"] != "button":
                    davor += 1
                    continue

                vorher = seite.evaluate(ERSTE_ZEILE)
                ring_ok = f["ring"] > 0 and f["stil"] not in ("none", "")
                seite.keyboard.press("Enter")
                seite.wait_for_timeout(450)
                nach_enter = seite.evaluate(ERSTE_ZEILE)
                seite.keyboard.press(" ")
                seite.wait_for_timeout(450)
                nach_leer = seite.evaluate(ERSTE_ZEILE)
                rollt = seite.evaluate("() => window.scrollY")

                eintrag = {
                    "nr": gefunden + 1,
                    "text": f["text"],
                    "tab_stopps_davor": davor,
                    "ring_px": f["ring"],
                    "ring_stil": f["stil"],
                    "ring_sichtbar": ring_ok,
                    "enter_wirkt": nach_enter != vorher,
                    "leertaste_wirkt": nach_leer != nach_enter,
                    "seite_rollt_bei_leertaste": rollt > 0,
                }
                bericht["geprueft"].append(eintrag)
                ok = (ring_ok and eintrag["enter_wirkt"]
                      and eintrag["leertaste_wirkt"]
                      and not eintrag["seite_rollt_bei_leertaste"])
                if not ok:
                    fehler += 1
                print("  %s %-26s Ring %s px (%s) | Enter %s | Leertaste %s | "
                      "rollt %s"
                      % ("OK  " if ok else "ROT ", f["text"][:26],
                         f["ring"], f["stil"],
                         "wirkt" if eintrag["enter_wirkt"] else "WIRKT NICHT",
                         "wirkt" if eintrag["leertaste_wirkt"] else "WIRKT NICHT",
                         "JA" if eintrag["seite_rollt_bei_leertaste"] else "nein"))
                gefunden += 1
                if gefunden >= wieviele:
                    break
            bericht["tab_stopps_vor_dem_ersten_sortierkopf"] = davor
        finally:
            ctx.close()
            browser.close()

    if not bericht["geprueft"]:
        print("\U0001F534 KEIN Sortierkopf mit der Tastatur erreicht. Das ist "
              "kein gutes Ergebnis,\n   das ist ein misslungener Versuch.")
        return 2
    ziel = os.path.join(WURZEL, "docs", "befunde", "TASTATUR_PROBE.json")
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps(bericht, ensure_ascii=False, indent=1))
    print("\n%d von %d Koepfen vollstaendig | Tab-Stopps vor dem ersten: %d"
          % (len(bericht["geprueft"]) - fehler, len(bericht["geprueft"]),
             bericht["tab_stopps_vor_dem_ersten_sortierkopf"]))
    print("geschrieben:", ziel)
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
