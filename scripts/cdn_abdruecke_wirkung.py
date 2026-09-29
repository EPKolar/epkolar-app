# -*- coding: utf-8 -*-
"""Laedt die App wirklich und prueft, ob die Abdruecke sie NICHT toeten.

🔴 EIN QUELLTEXT-RIEGEL KANN DAS NICHT. `integrity` steht entweder da oder
nicht - das ist Anwesenheit. Ob der Browser die Datei danach noch ausfuehrt,
entscheidet sich beim Laden, und zwar still: schlaegt ein Abdruck fehl,
laedt der Browser das Skript gar nicht, die Seite bleibt weiss, und die
einzige Spur steht in der Konsole.

Gemessen wird dreierlei, weil jedes einzeln gruen sein kann, waehrend die
App tot ist:

  1. Keine Konsolenmeldung, die von einem fehlgeschlagenen Abdruck spricht.
  2. Jede der acht Dateien ist mit Status 200 ANGEKOMMEN - eine, die gar
     nicht abgerufen wurde, kann auch nicht scheitern und wuerde bei 1.
     gruen aussehen.
  3. React haengt wirklich im Baum (`#root` hat Kinder) UND die drei
     Bibliotheken, die nur per Skript kommen, sind als Objekt da.

🔴 SELBSTPROBE: mit `--koeder` wird EIN Abdruck absichtlich verdorben. Dann
MUESSEN 1 und 3 rot werden. Meldet der Lauf auch dann gruen, misst er
nichts - und eine gruene Meldung ohne diese Gegenprobe ist wertlos.
Die Datei wird dafuer nie veraendert; der Koeder lebt in einer Kopie.
"""
import io
import os
import re
import shutil
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
WURZEL = os.path.dirname(HIER)

import mob_ansicht_messen as M           # noqa: E402

ERWARTET = ["react/18.2.0", "react-dom/18.2.0", "bcryptjs/2.4.3",
            "pdf.js/3.11.174", "qrcode-generator/1.4.4", "jspdf/2.5.1",
            "leaflet/1.9.4/leaflet.min.js", "leaflet/1.9.4/leaflet.min.css"]

# Wonach in der Konsole gesucht wird. Chromium schreibt bei einem
# fehlgeschlagenen Abdruck woertlich "Failed to find a valid digest in the
# 'integrity' attribute".
VERDACHT = re.compile(r"integrity|Subresource Integrity|valid digest", re.I)

LEBT_JS = r"""() => {
  const r = document.getElementById('root');
  return {wurzel_kinder: r ? r.children.length : -1,
          react: typeof window.React,
          reactdom: typeof window.ReactDOM,
          bcrypt: typeof window.dcodeIO !== 'undefined'
                    ? 'dcodeIO' : typeof window.bcrypt,
          pdfjs: typeof window.pdfjsLib,
          leaflet: typeof window.L,
          jspdf: typeof window.jspdf,
          qr: typeof window.qrcode};
}"""


def main(argv):
    from playwright.sync_api import sync_playwright
    koeder = "--koeder" in argv
    datei = "index.html"
    if koeder:
        # 🔴 NIE am Original. Der Koeder bekommt eine eigene Datei, und die
        #    wird am Ende wieder entfernt.
        datei = "__koeder_integrity.html"
        t = io.open(os.path.join(WURZEL, "index.html"),
                    encoding="utf-8", newline="").read()
        alt = 'integrity="sha512-8Q6Y9XnTbOE'
        assert t.count(alt) == 1, "Der Koeder-Anker passt nicht mehr."
        t = t.replace(alt, 'integrity="sha512-XXXXXXXXXXX')
        io.open(os.path.join(WURZEL, datei), "w",
                encoding="utf-8", newline="").write(t)
        print("KOEDERLAUF: der Abdruck von react ist absichtlich verdorben.")
        print("Dieser Lauf MUSS rot werden. Wird er gruen, misst er nichts.\n")

    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port, datei)
    meldungen, antworten = [], {}

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            ctx = browser.new_context(viewport={"width": 1440, "height": 880})
            seite = ctx.new_page()
            seite.on("console", lambda m: meldungen.append(
                "%s: %s" % (m.type, m.text[:220])))
            seite.on("pageerror", lambda e: meldungen.append(
                "pageerror: %s" % str(e)[:220]))
            seite.on("response", lambda r: antworten.__setitem__(
                r.url, r.status) if "cdnjs.cloudflare.com" in r.url else None)
            seite.goto(url, wait_until="domcontentloaded")
            seite.wait_for_timeout(9000)
            lebt = seite.evaluate(LEBT_JS)
            ctx.close()
            browser.close()
    finally:
        if koeder:
            p = os.path.join(WURZEL, datei)
            if os.path.exists(p):
                os.remove(p)

    schief = []

    verdaechtig = [m for m in meldungen if VERDACHT.search(m)]
    print("1. Konsole: %d Meldungen, davon %d zum Thema Abdruck"
          % (len(meldungen), len(verdaechtig)))
    for m in verdaechtig[:6]:
        print("   \U0001F534 " + m)
    if verdaechtig:
        schief.append("%d Konsolenmeldungen sprechen von einem "
                      "fehlgeschlagenen Abdruck" % len(verdaechtig))

    print("2. Abgerufen von cdnjs: %d Adressen" % len(antworten))
    fehlend = []
    for teil in ERWARTET:
        treffer = [(u, s) for u, s in antworten.items() if teil in u]
        if not treffer:
            fehlend.append(teil)
            print("   \U0001F534 %-34s gar nicht abgerufen" % teil)
        else:
            u, s = treffer[0]
            zeichen = "\U0001F7E2" if s == 200 else "\U0001F534"
            print("   %s %-34s HTTP %s" % (zeichen, teil, s))
            if s != 200:
                schief.append("%s kam mit HTTP %s" % (teil, s))
    if fehlend:
        schief.append("%d Dateien wurden gar nicht abgerufen: %s"
                      % (len(fehlend), ", ".join(fehlend)))

    print("3. Lebt die App? %s" % lebt)
    if lebt.get("wurzel_kinder", 0) < 1:
        schief.append("`#root` hat %s Kinder - React haengt NICHT im Baum, "
                      "die Seite ist weiss" % lebt.get("wurzel_kinder"))
    for name, schluessel in (("React", "react"), ("ReactDOM", "reactdom"),
                             ("pdf.js", "pdfjs"), ("Leaflet", "leaflet")):
        if lebt.get(schluessel) == "undefined":
            schief.append("%s ist nicht geladen" % name)

    print()
    if koeder:
        if schief:
            print("\U0001F7E2 KOEDERLAUF richtig rot - der Melder sieht einen "
                  "verdorbenen Abdruck:")
            for s in schief:
                print("   " + s)
            return 0
        print("\U0001F534 KOEDERLAUF GRUEN. Der Melder sieht einen "
              "absichtlich verdorbenen\n   Abdruck NICHT - er misst nichts, "
              "und seine gruene Meldung am echten\n   Lauf belegt gar nichts.")
        return 2

    if schief:
        print("\U0001F534 %d Befunde:" % len(schief))
        for s in schief:
            print("   " + s)
        return 1
    print("\U0001F7E2 Alle acht Dateien kamen mit 200 an, keine Meldung zum "
          "Abdruck,\n   React haengt im Baum. Die Abdruecke wirken, ohne die "
          "App zu toeten.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
