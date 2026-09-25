# -*- coding: utf-8 -*-
"""Den Feiertags-Zweig aus v3.9.915 am ECHTEN Schirm ausloesen.

WARUM DAS BIS HEUTE NICHT GING
------------------------------
Der Absturz vom 30.08. traf jeden Werktags-Feiertag, sobald er in den
Vier-Wochen-Horizont der Dispo rutscht. Repariert wurde er am selben Tag, aber
**der Zweig war nie zu erreichen**: zwischen v3.9.884 und Ende September lag
kein Werktags-Feiertag im Horizont. Die Reparatur war bis heute nur durch
geschnittenen und mit Node ausgefuehrten Code belegt, nie durch die laufende App.

WANN ES GEHT - gemessen mit `_isATFeiertag`, nicht gerechnet:

    ab Mo 2026-09-21 bis 2026-10-18   keine
    ab Mo 2026-09-28 bis 2026-10-25   keine     <- die Doku sagte faelschlich "ab hier"
    ab Mo 2026-10-05 bis 2026-11-01   26.10.    <- HIER
    ab Mo 2026-10-12 bis 2026-11-08   26.10.
    ab Mo 2026-10-19 bis 2026-11-15   26.10.
    ab Mo 2026-10-26 bis 2026-11-22   26.10.

Der Horizont beginnt am Montag der laufenden Woche und umfasst genau 28 Tage;
am 28.09. endet er am 25.10., einen Tag VOR dem Feiertag. Die Schaetzung
"sichtbar ab ca. 28.09." im Handoff war also um eine Woche zu frueh.

WAS DIESE PROBE MISST
---------------------
Nicht, dass die Zeile dasteht - das misst `tests/test_dispo_feiertag_absturz_v915.py`
laengst. Sondern dass die laufende App beim Blaettern in die Feiertagswoche

  * NICHT die Zeile "Vorschlagsplanung konnte nicht berechnet werden" zeigt
    (das waere der Absturz: `_built` wird null und das ganze Raster verschwindet),
  * ein Raster mit Zellen rendert,
  * und am Feiertag den Grund-Chip traegt.

Der KOEDER: bevor gemessen wird, prueft die Probe an der HEUTIGEN Woche, dass
sie ueberhaupt ein Raster sieht. Ohne diesen Nachweis waere "kein Absturz"
dasselbe wie "nichts gerendert" - und die Probe waere gruen, weil sie blind ist.

BENUTZUNG
---------
    python scripts/feiertag_live_probe.py                    # gegen die Live-App
    python scripts/feiertag_live_probe.py --lokal            # gegen den Arbeitsbaum
"""
import io
import os
import sys
import threading

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)

from tab_sweep import INIT, IGNORIEREN, DB_NAME, SEED_JS  # noqa: E402

LIVE = "https://epkolar.github.io/epkolar-app/index.html"
ZIEL_WOCHE = "2026-10-26"   # Nationalfeiertag, ein Montag

RASTER_JS = """() => {
  const txt = document.body.innerText || "";
  const zellen = document.querySelectorAll('[data-norm]').length;
  // ERSTER ENTWURF ZAEHLTE DEN QUELLTEXT MIT: `querySelectorAll('*')` trifft
  // auch <script>, und der Rumpf der App enthaelt das Wort. Die Probe meldete
  // deshalb in JEDER Woche eine 1 - eine saubere Zahl, die nichts sah. Die
  // echte Grundlinie ist 0, und in der Feiertagswoche stehen 2 Chips (einer
  // je Monteur). Gezaehlt wird jetzt nur, was ein Mensch auch sieht.
  const chips = Array.from(document.querySelectorAll('*'))
    .filter(e => e.children.length === 0
             && !/^(SCRIPT|STYLE|TITLE|TEMPLATE)$/.test(e.tagName)
             && (e.offsetParent || e.getClientRects().length)
             && /Feiertag/.test(e.textContent || ""))
    .map(e => (e.textContent || "").trim());
  return {
    absturz: txt.indexOf("konnte nicht berechnet werden") >= 0,
    zellen: zellen,
    feiertagschips: chips.length,
    beispiel: chips[0] || "",
    wochentext: (txt.match(/KW\\s*\\d+[^\\n]*/) || [""])[0].slice(0, 60),
  };
}"""


def _kopie_mit_horizont(wochen):
    """index.html in den Kritzelordner kopieren und den Horizont weiten.

    NOETIG, weil der Vorwaerts-Knopf am Ende des Horizonts GESPERRT ist
    (Titel: "Planungshorizont: 4 Wochen (einstellbar)") - der Feiertag ist
    bis Mo 05.10.2026 also nicht nur unsichtbar, sondern unerreichbar.
    Die Fensterbreite beruehrt den Feiertags-Zweig nicht, nur seine
    Erreichbarkeit: `t.feiertag` haengt am Tag, nicht an der Woche.

    Gemessen wird gegen die WIRKLICH geaenderte Datei, nicht gegen eine ins
    Fenster eingespielte Fassung - am 31.08. hat genau dieser Unterschied
    einen Umbau vor seinem Gegenteil bewahrt.
    """
    import shutil
    ordner = os.environ.get("CLAUDE_SCRATCH") or os.path.join(WURZEL, ".probe")
    os.makedirs(ordner, exist_ok=True)
    ziel = os.path.join(ordner, "index.html")
    shutil.copyfile(os.path.join(WURZEL, "index.html"), ziel)
    s = io.open(ziel, encoding="utf-8", newline="").read()
    alt = "DISPO_HORIZONT_WOCHEN=4"
    n = s.count(alt)
    assert n == 1, "Horizont-Konstante %dx statt 1x gefunden" % n
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        s.replace(alt, "DISPO_HORIZONT_WOCHEN=%d" % wochen, 1))
    print("Kopie mit Horizont %d Wochen:" % wochen, ziel)
    return ordner


def _server(ordner=None):
    import http.server
    import socketserver
    os.chdir(ordner or WURZEL)

    class Still(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    srv = socketserver.TCPServer(("127.0.0.1", 0), Still)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv.server_address[1]


def _saat():
    """Monteure und Scheine rund um den Feiertag.

    Die Termine liegen in der Feiertagswoche selbst - ein Raster ohne Daten
    rendert zwar, aber der Zweig, um den es geht, laeuft je Monteur und Tag.
    """
    mon = [{"id": "M1", "n": "Michael Hofbauer", "r": "Monteur", "austritt": ""},
           {"id": "M2", "n": "Franz Huber", "r": "Obermonteur", "austritt": ""}]
    tage = ["2026-10-27", "2026-10-28", "2026-10-29"]
    scheine = [{"id": "S%d" % k, "nummer": "AS-%d" % (9000 + k),
                "kundName": "Kunde %d" % k, "arbeitsort": "Krems", "plz": "3500",
                "monteur": "M1" if k % 2 else "M2",
                "terminBestaetigt": t, "terminZeit": "08:30",
                "scheinstatus": "freigegeben", "prioritaet": "normal", "dauer": "2h"}
               for k, t in enumerate(tage, start=1)]
    return {"monteure": mon, "arbeitsscheine": scheine}


def main(url):
    from playwright.sync_api import sync_playwright

    fehler = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        c = b.new_context(viewport={"width": 1440, "height": 900})
        c.add_init_script(INIT)
        p = c.new_page()
        p.on("pageerror", lambda e: fehler.append("pageerror: " + str(e)[:160]))

        def konsole(m):
            art = m.type() if callable(getattr(m, "type", None)) else getattr(m, "type", "")
            if art != "error":
                return
            t = m.text() if callable(getattr(m, "text", None)) else getattr(m, "text", "")
            if not any(x.lower() in str(t).lower() for x in IGNORIEREN):
                fehler.append("console: " + str(t)[:160])
        p.on("console", konsole)

        p.goto(url, wait_until="domcontentloaded")
        p.wait_for_timeout(5000)
        print("Version:", p.evaluate("()=>typeof APP_VERSION!=='undefined'?APP_VERSION:'?'"))

        p.evaluate(SEED_JS, {"db": DB_NAME, "daten": _saat()})
        p.reload(wait_until="domcontentloaded")
        p.wait_for_timeout(5000)

        p.get_by_text("Arbeitsscheine", exact=False).first.click()
        p.wait_for_timeout(2000)
        p.get_by_text("Dispo", exact=False).first.click()
        p.wait_for_timeout(2500)

        # KOEDER: sieht die Probe ueberhaupt ein Raster? Ohne diesen Nachweis
        # waere "kein Absturz" dasselbe wie "nichts gerendert".
        start = p.evaluate(RASTER_JS)
        print()
        print("KOEDER - die heutige Woche:")
        print("  Zellen:", start["zellen"], " Absturz-Zeile:", start["absturz"])
        if start["zellen"] == 0:
            print()
            print("  KEIN RASTER SICHTBAR. Diese Probe kann nichts belegen -")
            print("  'kein Absturz' waere hier nur 'nichts gerendert'. Abbruch.")
            b.close()
            return 2
        print("  -> die Probe sieht ein Raster, sie kann also etwas sehen.")

        # Vorwaerts bis in die Feiertagswoche.
        print()
        print("Blaettere vorwaerts bis", ZIEL_WOCHE, "...")
        getroffen = False
        for schritt in range(1, 12):
            knopf = p.get_by_text("▶", exact=False)
            if not knopf.count():
                knopf = p.get_by_role("button", name="▶")
            if not knopf.count():
                print("  Kein Vorwaerts-Knopf gefunden - hier wird nichts behauptet.")
                break
            knopf.first.click()
            p.wait_for_timeout(1400)
            d = p.evaluate(RASTER_JS)
            drin = ZIEL_WOCHE in (p.evaluate("()=>document.body.innerText") or "") or \
                   p.evaluate("()=>!!document.querySelector('[data-tag*=\"2026-10-26\"]')") or \
                   p.evaluate("()=>(document.body.innerHTML||'').indexOf('2026-10-26')>=0")
            print("  Schritt %2d: Zellen %3d, Absturz %-5s, Feiertags-Chips %d%s"
                  % (schritt, d["zellen"], d["absturz"], d["feiertagschips"],
                     "   <- Feiertagswoche" if drin else ""))
            if d["absturz"]:
                print()
                print("  \U0001f534 ABSTURZ-ZEILE SICHTBAR. Das Raster ist weg.")
                b.close()
                return 1
            if drin:
                getroffen = True
                if d["feiertagschips"] > 0:
                    print("  Chip-Beispiel:", repr(d["beispiel"][:40]))
                break

        p.screenshot(path=os.path.join(WURZEL, "screenshots", "feiertag_live.png"))
        b.close()

    print()
    if not getroffen:
        print("Die Feiertagswoche wurde nicht erreicht - die Probe belegt nur,")
        print("dass die davorliegenden Wochen sauber rendern.")
        return 3
    if fehler:
        print("FEHLER auf der Seite:")
        for f in fehler[:6]:
            print("  -", f)
        return 1
    print("Kein Absturz, keine Seitenfehler, Raster gerendert.")
    return 0


if __name__ == "__main__":
    _url = LIVE
    if "--horizont" in sys.argv:
        _w = int(sys.argv[sys.argv.index("--horizont") + 1])
        _url = "http://127.0.0.1:%d/index.html" % _server(_kopie_mit_horizont(_w))
    elif "--lokal" in sys.argv:
        _url = "http://127.0.0.1:%d/index.html" % _server()
    sys.exit(main(_url))
