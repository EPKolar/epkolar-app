# -*- coding: utf-8 -*-
"""Eine einzige Frage: WAS zeigt die Wochenplanung eigentlich?

Tor B hat die Planung bei beiden Breiten als nicht aussagekraeftig gestempelt
(0 bzw. 1 von mindestens 3 Saatmarken), und ihre Zahlen sind zwischen duenner
und voller Saat BYTEGLEICH gleich geblieben. Zwei Erklaerungen sind moeglich,
und sie fuehren zu entgegengesetzten Schluessen:

  (a) Die Ansicht zeigt den Bestand gar nicht - dann ist die Saat nicht die
      Ursache, und ein Umbau der Saat aendert dort nie etwas.
  (b) Die Ansicht zeigt ihn in GEKUERZTER Form ("Steinb" statt
      "Steinbichler"), und mein Tor-B-Melder ist fuer genau diese Form blind -
      dann haette ich mit einem blinden Messgeraet gemessen.

Der Unterschied ist nicht erschliessbar, er ist ablesbar. Diese Sonde liest
den Text der Ansicht und sucht zusaetzlich nach den auf sechs Zeichen
GEKUERZTEN Namen. Genau dafuer stehen zwei Verwechslungspaare in der Saat.

    python scripts/echtmengen_planung_probe.py
"""
import io
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import mob_ansicht_messen as M           # noqa: E402
import b3_vier_ansichten_messen as B     # noqa: E402
import echtmengen_saat as SAAT           # noqa: E402
import echtmengen_messen as EM           # noqa: E402

WURZEL = os.path.dirname(HIER)


def main():
    from playwright.sync_api import sync_playwright
    port = M._server()
    url = "http://127.0.0.1:%d/index.html" % port
    voll = SAAT.saat()
    kurz = sorted(set(m["n"].split()[-1][:6] for m in SAAT.MONTEURE))
    vorn = sorted(set(m["n"].split()[0][:6] for m in SAAT.MONTEURE))
    aus = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for kuerzel in ("planung", "chef"):
            for breite in (390, 1440):
                ctx = EM._ctx(browser, breite)
                seite = ctx.new_page()
                seite.goto(url, wait_until="domcontentloaded")
                seite.wait_for_timeout(3800)
                EM._saeen(seite, voll, still=True)
                B._navigieren(seite, kuerzel, breite) if kuerzel == "planung" \
                    else None
                if kuerzel == "chef":
                    import b3_stufen_12_15_messen as B12
                    B12._navigieren12(seite, kuerzel, breite, [])
                seite.wait_for_timeout(2000)
                t = seite.evaluate(EM.TEXT_JS)
                aus.append((kuerzel, breite, t))
                print("\n═══ %s @ %d px  (%d Zeichen Text)"
                      % (kuerzel, breite, len(t)))
                print("  volle Saatmarken:  %s" % SAAT.marken_im_text(t))
                print("  GEKUERZTE Nachnamen (6 Zeichen) im Text: %s"
                      % [k for k in kurz if k in t])
                print("  Vornamen (6 Zeichen) im Text:            %s"
                      % [k for k in vorn if k in t])
                print("  ── Text ──")
                print("  " + t.replace("\n", " | ")[:1800])
                ctx.close()
        browser.close()
    ziel = os.path.join(HIER, "_echtmengen_planung.txt")
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        "\n\n".join("=== %s @ %d ===\n%s" % x for x in aus))
    print("\nGeschrieben:", ziel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
