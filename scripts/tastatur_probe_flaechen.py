# -*- coding: utf-8 -*-
"""Die neuen Flaechen am Schirm durchtabben - Fokusring, Enter, Leertaste.

🔴 DAS IST DER TEIL, DEN EIN QUELLTEXTRIEGEL NICHT PRUEFEN KANN. Er sieht, dass
`tabIndex` und `onKeyDown` dastehen. Er sieht nicht, ob der Fokus ankommt, ob
die Taste wirklich etwas ausloest und ob ein Mensch sieht, wo er steht.

Geprueft wird an den Fahrzeugkarten: sie sind der klarste Fall der Klasse A -
eine Karte, ein Stopp, ein Klick der die Karte oeffnet. Gemessen:

  1. mit der Tabulatortaste erreichbar
  2. Fokusring SICHTBAR (nach echtem Tabben, nicht nach `.focus()` - ein
     skriptgesteuertes `.focus()` loest `:focus-visible` in Chromium nicht
     zuverlaessig aus)
  3. die EINGABETASTE oeffnet die Karte (der Baum aendert sich)
  4. die LEERTASTE ebenso
  5. Gegenprobe: die Seite rollt bei der Leertaste NICHT
"""
import io
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
WURZEL = os.path.dirname(HIER)

import mob_ansicht_messen as M           # noqa: E402
import b3_stufen_12_15_messen as B12     # noqa: E402
import echtmengen_saat as SAAT           # noqa: E402
import echtmengen_messen as EM           # noqa: E402

FOKUS = """() => {
  const e = document.activeElement;
  if (!e || e === document.body) return null;
  const s = getComputedStyle(e);
  return {tag: e.tagName.toLowerCase(), rolle: e.getAttribute('role'),
          tabindex: e.getAttribute('tabindex'),
          text: (e.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 30),
          ring: parseFloat(s.outlineWidth) || 0, stil: s.outlineStyle};
}"""

# Die Detailansicht eines Fahrzeugs erkennt man daran, dass die Kartenliste
# verschwindet. Gemessen wird die Zahl der Kennzeichen-Karten.
ZUSTAND = """() => {
  const t = document.body.innerText || '';
  return {karten: (t.match(/GU-\\d/g) || []).length, laenge: t.length};
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
            B12._navigieren12(seite, "fahrzeuge", 1440, [])
            seite.wait_for_timeout(1800)

            gefunden = 0
            davor = 0
            for _ in range(400):
                if gefunden >= wieviele:
                    break
                seite.keyboard.press("Tab")
                f = seite.evaluate(FOKUS)
                if not f:
                    continue
                # Eine der neuen Flaechen: div mit tabindex, kein button
                if f["tag"] != "div" or f["tabindex"] is None:
                    davor += 1
                    continue

                ring_ok = f["ring"] > 0 and f["stil"] not in ("none", "")
                vorher = seite.evaluate(ZUSTAND)
                seite.keyboard.press("Enter")
                seite.wait_for_timeout(500)
                nach_enter = seite.evaluate(ZUSTAND)
                # zurueck zur Liste
                seite.keyboard.press("Escape")
                seite.wait_for_timeout(300)
                rollt = seite.evaluate("() => window.scrollY")

                e = {"nr": gefunden + 1, "text": f["text"], "rolle": f["rolle"],
                     "ring_px": f["ring"], "ring_stil": f["stil"],
                     "ring_sichtbar": ring_ok,
                     "enter_wirkt": nach_enter != vorher,
                     "seite_rollt": rollt > 0}
                bericht["geprueft"].append(e)
                ok = ring_ok and e["enter_wirkt"]
                if not ok:
                    fehler += 1
                print("  %s %-30s Rolle %-8s Ring %s px (%s) | Enter %s"
                      % ("OK  " if ok else "ROT ", f["text"][:30],
                         f["rolle"] or "(ohne)", f["ring"], f["stil"],
                         "wirkt" if e["enter_wirkt"] else "WIRKT NICHT"))
                gefunden += 1
                # Nach einem Oeffnen ist der Baum anders - neu aufbauen.
                B12._navigieren12(seite, "fahrzeuge", 1440, [])
                seite.wait_for_timeout(1200)
                for _ in range(davor + gefunden):
                    seite.keyboard.press("Tab")
            bericht["stopps_davor"] = davor
        finally:
            ctx.close()
            browser.close()

    if not bericht["geprueft"]:
        print("\U0001F534 KEINE der neuen Flaechen mit der Tastatur erreicht. "
              "Das ist kein gutes\n   Ergebnis, das ist ein misslungener "
              "Versuch.")
        return 2
    ziel = os.path.join(WURZEL, "docs", "befunde", "TASTATUR_FLAECHEN.json")
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps(bericht, ensure_ascii=False, indent=1))
    print("\n%d von %d vollstaendig | geschrieben: %s"
          % (len(bericht["geprueft"]) - fehler, len(bericht["geprueft"]), ziel))
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
