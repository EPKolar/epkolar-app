# -*- coding: utf-8 -*-
"""Wo auf dem Telefon-Schirm wirkt ein Wisch - und wo nicht?

DER BEFUND, DER DAZU GEFUEHRT HAT (Sebastian, 25.09.2026)
---------------------------------------------------------
"swipen geht in mobil nicht, muss auf der kompletten bildschirmflaeche laufen
und nicht ausserhalb der kacheln"

VERDACHT (zu pruefen, nicht zu glauben): v3.9.926 hat die Kennzahl-Kacheln am
Telefon in eine quer rollbare Zeile gelegt (`.epk-kachelband`, `overflow-x:
auto`). Ein quer rollbares Element verbraucht waagrechte Gesten selbst - der
Browser rollt den Kasten, statt die Geste nach oben durchzureichen. Waere das
so, haette ich die tote Zone selbst eingebaut.

Es gibt einen aelteren Fall derselben Art: v3.9.869 hat gemessen, dass die fixe
`.bottom-nav` KEIN Kind von `.main-pad` ist - dort erreichte ein Wisch den Hook
nie, und genau dort liegt der Daumen. Die Leiste bekam daraufhin eine eigene
Wisch-Flaeche. Diese Probe misst also auch nach, ob das noch haelt.

WAS GEMESSEN WIRD
-----------------
Echte Touch-Ereignisse ueber CDP (`Input.dispatchTouchEvent`), nicht Mausklicks:
der Hook hoert auf `touchstart`/`touchend`, eine Maus-Geste erreicht ihn nie.
Gewischt wird an mehreren Hoehen, und gemessen wird die EINZIGE Frage, die
zaehlt: **wechselt der Reiter?**

DER KOEDER
----------
Zuerst wird in der Mitte des Inhalts gewischt. Wechselt dort NICHTS, ist die
Probe blind - dann sagt "ueber den Kacheln tot" gar nichts, weil ueberall tot
ist. Ohne diesen Nachweis bricht der Lauf ab.

BENUTZUNG
---------
    python scripts/wisch_flaechen_messen.py                 # Live-App
    python scripts/wisch_flaechen_messen.py --lokal         # Arbeitsbaum
    python scripts/wisch_flaechen_messen.py --breite 414
"""
import os
import sys
import threading

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)

from tab_sweep import INIT, DB_NAME, SEED_JS  # noqa: E402

LIVE = "https://epkolar.github.io/epkolar-app/index.html"

# Welcher Reiter ist gerade offen? Die aktive Hauptnavigation traegt eine
# eigene Farbe; verlaesslicher ist die Ueberschrift der Ansicht.
REITER_JS = """() => {
  const h = document.querySelector('h1,h2');
  const nav = Array.from(document.querySelectorAll('.bottom-nav *'))
    .filter(e => e.children.length === 0).map(e => (e.textContent||'').trim());
  return {
    titel: ((h && h.textContent) || '').trim().slice(0, 40),
    nav: nav.join('|').slice(0, 80),
  };
}"""

FLAECHEN_JS = """() => {
  const nimm = (sel) => {
    const e = document.querySelector(sel);
    if (!e) return null;
    const r = e.getBoundingClientRect();
    if (r.height < 4) return null;
    return {y: Math.round(r.top + r.height / 2), h: Math.round(r.height)};
  };
  const t = document.querySelector('table');
  const karte = document.querySelector('[role="button"][aria-label]');
  // Jeder quer rollende Bereich ist ein Verdacht: er verbraucht die
  // waagrechte Geste selbst. Gesucht wird deshalb nicht nach Namen,
  // sondern nach der EIGENSCHAFT - berechneter overflow-x.
  const roller = Array.from(document.querySelectorAll('*')).filter(e => {
    const cs = getComputedStyle(e);
    if (!/auto|scroll/.test(cs.overflowX)) return false;
    const r = e.getBoundingClientRect();
    return r.height > 20 && r.top < window.innerHeight && r.bottom > 0
        && e.scrollWidth > e.clientWidth + 4;
  }).map(e => { const r = e.getBoundingClientRect();
                return {y: Math.round(r.top + r.height/2),
                        h: Math.round(r.height),
                        was: (e.className||'').toString().slice(0,28)
                             || e.tagName}; });
  return {
    roller: roller,
    kachelband: nimm('.kpi-grid'),
    inhalt: karte ? (() => { const r = karte.getBoundingClientRect();
                             return {y: Math.round(r.top + r.height/2), h: Math.round(r.height)}; })() : null,
    tabelle: t ? (() => { const r = t.getBoundingClientRect();
                          return {y: Math.round(r.top + 20), h: Math.round(r.height)}; })() : null,
    navleiste: nimm('.bottom-nav'),
    schirm: window.innerHeight,
  };
}"""


def _server():
    import http.server
    import socketserver
    os.chdir(WURZEL)

    class Still(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    srv = socketserver.TCPServer(("127.0.0.1", 0), Still)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv.server_address[1]


def _wisch(cdp, x0, y, x1, schritte=10):
    """Echte Touch-Geste. Eine Maus-Geste erreicht den Hook NICHT."""
    cdp.send("Input.dispatchTouchEvent", {
        "type": "touchStart",
        "touchPoints": [{"x": x0, "y": y}],
    })
    for k in range(1, schritte + 1):
        cdp.send("Input.dispatchTouchEvent", {
            "type": "touchMove",
            "touchPoints": [{"x": x0 + (x1 - x0) * k / schritte, "y": y}],
        })
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})


def _saat():
    mon = [{"id": "M1", "n": "Michael Hofbauer", "r": "Monteur", "austritt": ""}]
    return {"monteure": mon,
            "arbeitsscheine": [{"id": "S%d" % k, "nummer": "AS-%d" % (8000 + k),
                                "kundName": "Kunde %d" % k, "arbeitsort": "Krems",
                                "scheinstatus": "freigegeben", "prioritaet": "normal",
                                "monteur": "M1"} for k in range(1, 7)]}


def main(url, breite=390):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        b = pw.chromium.launch()
        c = b.new_context(viewport={"width": breite, "height": 844},
                          has_touch=True, is_mobile=True)
        c.add_init_script(INIT)
        p = c.new_page()
        cdp = c.new_cdp_session(p)

        p.goto(url, wait_until="domcontentloaded")
        p.wait_for_timeout(5000)
        print("Version:", p.evaluate("()=>typeof APP_VERSION!=='undefined'?APP_VERSION:'?'"))
        print("Schirm:", breite, "x 844, Touch an")

        p.evaluate(SEED_JS, {"db": DB_NAME, "daten": _saat()})
        p.reload(wait_until="domcontentloaded")
        p.wait_for_timeout(5000)

        # ZUR ANSICHT MIT DEN KACHELN - per WISCH, nicht per Klick.
        # Bei 390 px steckt der Reiter hinter dem Klappmenue; der Knopf
        # existiert, ist aber unsichtbar, und ein Klick darauf laeuft in
        # einen Zeitueberlauf. Der Wisch in der Bildmitte wirkt (siehe
        # Koeder unten) und ist damit der verlaesslichere Weg.
        _mitte = 844 // 2
        _gefunden = False
        for _k in range(18):
            _t = p.evaluate(REITER_JS)["titel"]
            if "Arbeitsschein" in _t:
                _gefunden = True
                break
            _wisch(cdp, breite - 40, _mitte, 40)
            p.wait_for_timeout(700)
        print("Ansicht:", repr(p.evaluate(REITER_JS)["titel"][:34]),
              "" if _gefunden else "  <- NICHT erreicht")
        if not _gefunden:
            print("  Die Ansicht mit den Kacheln wurde nicht erreicht -")
            print("  hier wird nichts behauptet.")
            b.close()
            return 2

        f = p.evaluate(FLAECHEN_JS)
        print()
        print("Flaechen auf dem Schirm:")
        for name in ("kachelband", "inhalt", "tabelle", "navleiste"):
            w = f.get(name)
            print("  %-12s %s" % (name, ("y=%d (hoch %d)" % (w["y"], w["h"])) if w else "nicht sichtbar"))

        x0, x1 = breite - 40, 40          # von rechts nach links = vorwaerts

        def zur_as():
            """Zurueck auf die Arbeitsschein-Ansicht. JEDE Flaeche braucht einen
            frischen Anlauf: ein erfolgreicher Wisch wechselt die Ansicht, und
            die naechste Messung faende dort womoeglich gar keine Kacheln.
            Der erste Entwurf hat genau das getan und 'Kachelband tot' gemeldet,
            waehrend er auf einer fremden Ansicht mass."""
            # ERST GANZ ZURUECK, DANN VORWAERTS. Der Wisch klemmt am letzten
            # Reiter (_swipeVor clampt); wer einmal daran vorbei ist, kommt
            # vorwaerts nie zurueck. Der erste Entwurf lief genau dort fest
            # und meldete fuer JEDE Flaeche 'Ansicht nicht erreicht'.
            for _ in range(20):
                _v = p.evaluate(REITER_JS)["titel"]
                _wisch(cdp, 40, 844 // 2, breite - 40)   # zurueck
                p.wait_for_timeout(500)
                if p.evaluate(REITER_JS)["titel"] == _v:
                    break
            for _ in range(20):
                if "Arbeitsschein" in p.evaluate(REITER_JS)["titel"]:
                    return True
                _v = p.evaluate(REITER_JS)["titel"]
                _wisch(cdp, breite - 40, 844 // 2, 40)   # vorwaerts
                p.wait_for_timeout(500)
                if p.evaluate(REITER_JS)["titel"] == _v:
                    break   # klemmt am Ende
            return "Arbeitsschein" in p.evaluate(REITER_JS)["titel"]

        def probe(name):
            if not zur_as():
                print("  %-12s Ansicht nicht erreicht - nicht gemessen" % name)
                return None
            w = p.evaluate(FLAECHEN_JS).get(name)
            if not w:
                print("  %-12s auf dieser Ansicht nicht vorhanden" % name)
                return None
            y = w["y"]
            if not (8 <= y <= f["schirm"] - 8):
                print("  %-12s y=%-4d liegt AUSSERHALB des Schirms - nicht gemessen"
                      % (name, y))
                return None
            vor = p.evaluate(REITER_JS)["titel"]
            _wisch(cdp, x0, y, x1)
            p.wait_for_timeout(900)
            nach = p.evaluate(REITER_JS)["titel"]
            ok = vor != nach
            print("  %-12s y=%-4d %-30s %s" % (name, y, repr(vor[:28]),
                                               "WECHSELT" if ok else "TOT"))
            return ok

        print()
        print("KOEDER - wischt es in der Mitte des Inhalts ueberhaupt?")
        if not zur_as():
            print("  Arbeitsschein-Ansicht nicht erreichbar. Abbruch.")
            b.close()
            return 2
        _v = p.evaluate(REITER_JS)["titel"]
        _wisch(cdp, x0, f["schirm"] // 2, x1)
        p.wait_for_timeout(900)
        if p.evaluate(REITER_JS)["titel"] == _v:
            print("  In der Mitte wechselt NICHTS. Die Probe ist blind - 'ueber den")
            print("  Kacheln tot' saegte dann gar nichts aus. Abbruch.")
            b.close()
            return 2
        print("  Mitte y=%d: WECHSELT -> die Probe kann etwas messen." % (f["schirm"] // 2))

        print()
        print("Die einzelnen Flaechen, jede mit frischem Anlauf:")
        erg = {}
        for name in ("kachelband", "inhalt", "tabelle", "navleiste"):
            r = probe(name)
            if r is not None:
                erg[name] = r

        p.screenshot(path=os.path.join(WURZEL, "screenshots", "wisch_flaechen.png"))
        b.close()

    print()
    # EINE LEERE MESSUNG IST KEIN ERFOLG. Der erste Entwurf meldete
    # "alle Flaechen wechseln", waehrend KEINE einzige gemessen worden war -
    # dieselbe Krankheit wie ein Riegel ohne Koeder, nur eine Ebene hoeher.
    if not erg:
        print("🔴 GAR NICHTS GEMESSEN. Diese Probe belegt nichts.")
        return 2
    tot = [k for k, v in erg.items() if not v]
    if tot:
        print("\U0001f534 TOTE FLAECHEN:", ", ".join(tot))
        return 1
    print("Alle gemessenen Flaechen wechseln den Reiter.")
    return 0


if __name__ == "__main__":
    _url = LIVE
    if "--lokal" in sys.argv:
        _url = "http://127.0.0.1:%d/index.html" % _server()
    _b = 390
    if "--breite" in sys.argv:
        _b = int(sys.argv[sys.argv.index("--breite") + 1])
    sys.exit(main(_url, _b))
