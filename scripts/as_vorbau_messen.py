# -*- coding: utf-8 -*-
"""Der Vorbau ueber der Arbeitsschein-Liste - offener Punkt 27.

WAS GEMESSEN WIRD
-----------------
Nicht "sieht voll aus", sondern: **bei welchem y beginnt die erste
Arbeitsschein-Zeile** - am Rechner-Schirm und am Telefon. Alles darueber ist
Vorbau und muss sich rechtfertigen.

Zusaetzlich, weil das die eigentliche Frage von Punkt 27 ist:
  * jede Kachel einzeln: Beschriftung, Wert, Flaeche, und ob ein KLICK
    daran haengt (role=button ist die Spur, die React hinterlaesst)
  * welche Zustandsgroesse der Klick setzt - abgelesen an der wirklichen
    Wirkung: nach dem Klick wird das Status-Auswahlfeld zurueckgelesen.
    Eine Kachel, die dasselbe Feld setzt wie das Auswahlfeld darunter,
    ist eine Doppelung und keine zweite Bedienung.
  * die Bloecke zwischen Ueberschrift und Tabelle mit ihrer Hoehe

VORHER/NACHHER
--------------
Mit --nachher wird der Vorschlag als CSS im Browser eingespielt
(index.html wird NICHT angefasst). Der Vergleich der beiden y-Werte ist
die Aussage; eine einzelne Zahl waere keine.

BENUTZUNG
---------
    python scripts/as_vorbau_messen.py
    python scripts/as_vorbau_messen.py --nachher
    python scripts/as_vorbau_messen.py --schmal 390
    python scripts/as_vorbau_messen.py --schmal 390 --nachher
"""
import os
import sys
import threading

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)

from tab_sweep import INIT, IGNORIEREN, saeen  # noqa: E402

ZIEL = os.path.join(WURZEL, "screenshots")

# Der Vorschlag als reines CSS - genau das, was die Anker/Ersatz-Paare
# spaeter in index.html schreiben. Wird hier NUR im Browser eingespielt.
NACHHER_CSS = """
.kpi-grid.epk-leiste { grid-template-columns: repeat(6,1fr) !important; gap: 8px !important; }
.kpi-grid.epk-leiste > div { padding: 8px 10px !important; margin-bottom: 0 !important; }
.kpi-grid.epk-leiste > div > div:nth-child(2) { font-size: 11px !important;
  text-transform: none !important; letter-spacing: 0 !important; margin-bottom: 0 !important; }
.kpi-grid.epk-leiste > div > div:nth-child(3) { font-size: 18px !important; }
.kpi-grid.epk-leiste > div > div:nth-child(4) { font-size: 10px !important; margin-top: 0 !important; }
@media(max-width:900px){ .kpi-grid.epk-leiste { grid-template-columns: repeat(4,1fr) !important; } }
@media(max-width:600px){ .kpi-grid.epk-leiste { grid-template-columns: repeat(3,1fr) !important;
    gap: 6px !important; }
  .kpi-grid.epk-leiste > div { padding: 6px 8px !important; }
  .kpi-grid.epk-leiste > div > div:nth-child(3) { font-size: 16px !important; } }
"""

# Zum Ausprobieren einer anderen Spaltenzahl am Telefon, OHNE die Datei zu
# aendern:  EPK_PHONE_COLS=4 python scripts/as_vorbau_messen.py --schmal 390 ...
# Und zum Nachrechnen, was die Unterzeile ("offen"/"fertig"/...) kostet -
# NICHT als Vorschlag, sondern um die Zahl nennen zu koennen, mit der sie
# behalten wird:  EPK_SUB_AUS=1 python scripts/as_vorbau_messen.py ...
if os.environ.get("EPK_SUB_AUS"):
    NACHHER_CSS += ("""
.kpi-grid.epk-leiste > div > div:nth-child(4) { display: none !important; }
""")

_PC = os.environ.get("EPK_PHONE_COLS")
if _PC:
    NACHHER_CSS = NACHHER_CSS.replace("repeat(3,1fr) !important",
                                      "repeat(%s,1fr) !important" % _PC)

EINSPIELEN_JS = """(css) => {
  const g = document.querySelector('.kpi-grid');
  if (g) g.classList.add('epk-leiste');
  const s = document.createElement('style');
  s.id = '__nachher';
  s.textContent = css;
  document.head.appendChild(s);
  return !!g;
}"""

MESS_JS = r"""() => {
  const raus = {};
  const y = (e) => e ? Math.round(e.getBoundingClientRect().top + window.scrollY) : null;
  const h = (e) => e ? Math.round(e.getBoundingClientRect().height) : null;

  // Die erste Arbeitsschein-ZEILE. Am Rechner ist das ein tr in der
  // Tabelle; am Telefon gibt es keine Tabelle, dort ist es die erste
  // Karte. Beides ueber denselben Anker gesucht: das Element, das die
  // Scheinnummer traegt.
  let tab = document.querySelector('table');
  let zeile = tab ? tab.querySelector('tbody tr') : null;
  let art = 'tabellenzeile';
  if (!zeile) {
    // Die Mobil-Karte traegt eine eigene Klasse (epk-card-hover, :11305)
    // und ein aria-label mit der Scheinnummer. Beides zusammen, damit ein
    // umbenanntes Merkmal nicht stumm zu "KEINE" fuehrt.
    zeile = Array.from(document.querySelectorAll('.epk-card-hover'))
      .filter(d => /AS-\d{4}/.test(d.getAttribute('aria-label') || ''))[0]
      || Array.from(document.querySelectorAll('[role=button]'))
           .filter(d => /AS-\d{4}/.test(d.getAttribute('aria-label') || ''))[0]
      || null;
    art = 'mobilkarte';
  }
  raus.zeilenart = zeile ? art : 'KEINE';
  raus.y_erste_zeile = y(zeile);
  raus.y_tabelle = y(tab);
  raus.schirmhoehe = window.innerHeight;
  raus.schirmbreite = window.innerWidth;
  raus.sichtbar_ohne_rollen = zeile ? (y(zeile) < window.innerHeight) : null;

  // Die Kacheln
  const g = document.querySelector('.kpi-grid');
  raus.kachelgitter = g ? {y: y(g), hoehe: h(g),
    spalten: getComputedStyle(g).gridTemplateColumns.split(' ').length} : null;
  raus.kacheln = g ? Array.from(g.children).map(k => {
    const r = k.getBoundingClientRect();
    // v3.9.115 steht als Lehre im Code: die Kachel traegt overflow:hidden
    // und der Wert whiteSpace:nowrap. Wird die Kachel zu schmal, werden
    // Ziffern ABGESCHNITTEN - lautlos. Eine Kachel schmaler zu machen,
    // ohne das zu pruefen, waere derselbe Fehler ein zweites Mal.
    const innen = Array.from(k.children).filter(
      c => getComputedStyle(c).position !== 'absolute');
    const beschnitt = innen.filter(c => c.scrollWidth > c.clientWidth + 1)
      .map(c => (c.textContent || '').trim().slice(0, 20));
    return {
      text: (k.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 40),
      klickbar: k.getAttribute('role') === 'button',
      tastatur: k.getAttribute('tabindex') === '0',
      aria: k.getAttribute('aria-label') || '',
      breite: Math.round(r.width), hoehe: Math.round(r.height),
      flaeche: Math.round(r.width * r.height),
      beschnitt: beschnitt
    };
  }) : [];

  // Die Bloecke zwischen Ueberschrift und erster Zeile
  const h2 = document.querySelector('h2');
  raus.y_ueberschrift = y(h2);
  raus.bloecke = [];
  let n = g;
  while (n && !Array.from(n.children).some(c => c.classList
           && c.classList.contains('kpi-grid'))) n = n.parentElement;
  if (n) {
    const alles = [];
    const sammeln = (el, tiefe) => {
      for (const c of el.children) {
        const r = c.getBoundingClientRect();
        if (r.height < 1) continue;
        if (zeile && c.contains(zeile) && c !== zeile) { sammeln(c, tiefe + 1); continue; }
        if (zeile && y(c) >= y(zeile)) continue;
        alles.push({t: tiefe, y: y(c), hoehe: Math.round(r.height),
          was: (c.className || c.tagName.toLowerCase()) + '',
          text: (c.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 55)});
      }
    };
    sammeln(n, 0);
    raus.bloecke = alles.sort((a, b) => a.y - b.y);
  }
  return raus;
}"""

# Was setzt ein Kachelklick? Abgelesen am Status-Auswahlfeld, nicht geraten.
#
# ERSTER ANLAUF WAR FALSCH und haette fast eine falsche Aussage gedruckt:
# vorher und nachher wurden im SELBEN Auswertungsschritt gelesen. React hatte
# da noch nicht neu gezeichnet, also stand zweimal derselbe Wert da - und das
# sah aus wie "der Klick tut nichts". Erst der Zeilenversatz ueber elf Zeilen
# verriet, dass sehr wohl gesetzt wurde. Jetzt: klicken, warten, DANN lesen.
STATUS_LESEN_JS = """() => {
  const s = Array.from(document.querySelectorAll('select'))
    .find(x => Array.from(x.options).some(o => o.value === 'offen_bearb'));
  return s ? s.value : null;
}"""

KACHEL_KLICK_JS = """(i) => {
  const g = document.querySelector('.kpi-grid');
  if (!g || !g.children[i]) return null;
  g.children[i].click();
  return (g.children[i].textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 30);
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


def main(breite=1440, schmal=0, nachher=False, stress=False):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt.  pip install playwright && playwright install chromium")
        return 2

    os.makedirs(ZIEL, exist_ok=True)
    port = _server()
    # Zum Nachmessen einer GEPATCHTEN Fassung, ohne index.html anzufassen:
    #   EPK_INDEX=probe.html python scripts/as_vorbau_messen.py
    url = "http://127.0.0.1:%d/%s" % (
        port, os.environ.get("EPK_INDEX", "index.html"))
    print("Gemessen wird:", url)
    fehler = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": breite, "height": 900},
                                  device_scale_factor=1)
        ctx.add_init_script(INIT)
        seite = ctx.new_page()
        seite.on("pageerror", lambda e: fehler.append("pageerror: " + str(e)[:140]))

        def konsole(m):
            art = m.type() if callable(getattr(m, "type", None)) else getattr(m, "type", "")
            if art != "error":
                return
            t = m.text() if callable(getattr(m, "text", None)) else getattr(m, "text", "")
            if not any(x.lower() in str(t).lower() for x in IGNORIEREN):
                fehler.append("console: " + str(t)[:130])
        seite.on("console", konsole)

        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(4000)
        print("Version:", seite.evaluate(
            "() => typeof APP_VERSION!=='undefined' ? APP_VERSION : '?'"))

        saeen(seite)
        seite.wait_for_timeout(3500)

        getroffen = None
        for name in ("Arbeitsscheine", "Scheine"):
            ziel = seite.get_by_text(name, exact=False)
            if ziel.count():
                ziel.first.click()
                getroffen = name
                break
        print("Reiter getroffen:", getroffen or "KEINER")
        seite.wait_for_timeout(2500)

        if schmal:
            seite.set_viewport_size({"width": schmal, "height": 900})
            seite.wait_for_timeout(1500)
            print("Auf %d px verschmaelert (Mobil-Zweig ab ww < 600)" % schmal)

        if nachher:
            ok = seite.evaluate(EINSPIELEN_JS, NACHHER_CSS)
            print("Vorschlag eingespielt:", ok)
            seite.wait_for_timeout(600)

        if stress:
            # GEGENPROBE zur Beschnittpruefung. Die Saat liefert einstellige
            # Zahlen - damit wuerde JEDE Breite als "kein Beschnitt" gruen
            # melden, auch eine viel zu schmale. Erst eine lange Zahl sagt,
            # ob die Kachel wirklich traegt. 12.345 ist die groesste Zahl,
            # die in diesem Haus realistisch je in einer AS-Kachel stehen
            # kann; sie wird NUR im Browser gesetzt, nichts wird gespeichert.
            seite.evaluate("""() => {
              const g = document.querySelector('.kpi-grid');
              if (!g) return 0;
              let n = 0;
              for (const k of g.children) {
                const v = Array.from(k.children).filter(
                  c => getComputedStyle(c).position !== 'absolute')[1];
                if (v) { v.textContent = '12.345'; n++; }
              }
              return n;
            }""")
            seite.wait_for_timeout(400)
            print("STRESS: alle Kachelwerte auf 12.345 gesetzt.")

        seite.evaluate("() => window.scrollTo(0,0)")
        seite.wait_for_timeout(300)
        m = seite.evaluate(MESS_JS)

        wie = ("NACHHER" if nachher else "VORHER")
        print()
        print("=" * 68)
        print("%s  -  Schirm %dx%d" % (wie, m["schirmbreite"], m["schirmhoehe"]))
        print("=" * 68)
        print("  Ueberschrift beginnt bei y =", m["y_ueberschrift"])
        if m["kachelgitter"]:
            print("  Kachelgitter y = %s, Hoehe = %s px, %d Spalten"
                  % (m["kachelgitter"]["y"], m["kachelgitter"]["hoehe"],
                     m["kachelgitter"]["spalten"]))
        print("  Tabelle (mit Kopfzeile) beginnt bei y =", m["y_tabelle"])
        print("  Erste Arbeitsschein-Zeile (%s) beginnt bei y = %s"
              % (m["zeilenart"], m["y_erste_zeile"]))
        if m["y_erste_zeile"] is not None:
            print("  Das sind %.0f %% eines %d-px-Schirms."
                  % (100.0 * m["y_erste_zeile"] / m["schirmhoehe"],
                     m["schirmhoehe"]))
            print("  Ohne Rollen sichtbar:",
                  "JA" if m["sichtbar_ohne_rollen"] else "NEIN")

        print()
        print("  BLOECKE UEBER DER ERSTEN ZEILE")
        for b in m["bloecke"]:
            print("    y=%4s  h=%3s  %-20s %s"
                  % (b["y"], b["hoehe"], str(b["was"])[:20], b["text"]))

        print()
        print("  KACHELN (%d)" % len(m["kacheln"]))
        print("    %-3s %-32s %-6s %-6s %s"
              % ("#", "Beschriftung", "klick", "Taste", "Flaeche"))
        for i, k in enumerate(m["kacheln"]):
            print("    %-3d %-32s %-6s %-6s %sx%s = %s px2"
                  % (i, k["text"][:32], "JA" if k["klickbar"] else "NEIN",
                     "JA" if k["tastatur"] else "NEIN",
                     k["breite"], k["hoehe"], k["flaeche"]))
        if m["kacheln"]:
            ges = sum(k["flaeche"] for k in m["kacheln"])
            print("    Kachelflaeche gesamt: %d px2" % ges)
            schlimm = [(i, k["beschnitt"]) for i, k in enumerate(m["kacheln"])
                       if k["beschnitt"]]
            if schlimm:
                print("    BESCHNITTEN (overflow:hidden schneidet mit):")
                for i, b in schlimm:
                    print("      Kachel %d: %s" % (i, b))
            else:
                print("    Beschnitt: keiner - kein Text laeuft aus einer "
                      "Kachel heraus.")

        # Klickprobe: was setzt der Klick wirklich?
        if not nachher and m["kacheln"]:
            print()
            print("  KLICKPROBE - was setzt der Klick?")
            # GEGENPROBE zuerst: ein Klick auf die UEBERSCHRIFT darf das
            # Status-Feld NICHT aendern. Ohne diese Zeile wuerde das Messgeraet
            # auch dann "setzt" melden, wenn es in Wahrheit irgendetwas
            # anderes misst.
            v0 = seite.evaluate(STATUS_LESEN_JS)
            seite.evaluate("() => document.querySelector('h2').click()")
            seite.wait_for_timeout(350)
            n0 = seite.evaluate(STATUS_LESEN_JS)
            print("    GEGENPROBE Klick auf die Ueberschrift: %s -> %s  (%s)"
                  % (v0, n0, "unveraendert, gut" if v0 == n0
                     else "MESSGERAET FRAGWUERDIG"))
            for i in range(len(m["kacheln"])):
                vor = seite.evaluate(STATUS_LESEN_JS)
                besch = seite.evaluate(KACHEL_KLICK_JS, i)
                seite.wait_for_timeout(400)
                nach = seite.evaluate(STATUS_LESEN_JS)
                print("    %-2d %-26s Status-Feld: %s -> %s"
                      % (i, str(besch or "")[:26], vor, nach))

        bild = os.path.join(ZIEL, "as_vorbau_%s_%d.png"
                            % (wie.lower(), schmal or breite))
        seite.screenshot(path=bild)
        print()
        print("  Bild:", bild)
        if fehler:
            print("  FEHLER:", fehler[:4])
        browser.close()
    return 0


if __name__ == "__main__":
    _b = 1440
    _s = 0
    if "--breite" in sys.argv:
        _b = int(sys.argv[sys.argv.index("--breite") + 1])
    if "--schmal" in sys.argv:
        _s = int(sys.argv[sys.argv.index("--schmal") + 1])
    sys.exit(main(_b, _s, "--nachher" in sys.argv, "--stress" in sys.argv))
