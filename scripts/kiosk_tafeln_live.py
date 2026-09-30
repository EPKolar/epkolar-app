# -*- coding: utf-8 -*-
"""Die drei Kiosk-Tafeln AM SCHIRM messen - leer, abgewiesen, ohne Netz.

WARUM AM SCHIRM UND NICHT IM QUELLTEXT
--------------------------------------
Eine CSS-Regel mit `!important` uebersteuert JEDE Inline-Angabe. Ein
Quelltext-Riegel bleibt dabei gruen: im Quelltext steht 20 px, am Schirm
sind es 16. Der Quelltextwert ist NICHT der gemessene Wert. Dieses Werkzeug
misst darum `getComputedStyle` an gerenderten Knoten.

DIE DREI NETZMODI - UND WARUM ALLE DREI GEFAHREN WERDEN
-------------------------------------------------------
    aus    jeder REST-Aufruf wird ABGEBROCHEN         (Netz weg, WLAN aus)
    leer   jeder REST-Aufruf antwortet HTTP 200 []    (Tabelle wirklich leer)
    403    jeder REST-Aufruf antwortet HTTP 403       (Rechte fehlen)

Das ist keine Feinheit, das ist der Kern der Frage. `_sbGet` gibt bei
401/403 ein LEERES ARRAY im ERFOLGSPFAD zurueck - fuer den Aufrufer ist das
von einer wirklich leeren Tabelle nicht zu unterscheiden. Es gibt dafuer
`window.__EP_RLS` und das Array-Merkmal `__rlsFehler`. Gemessen wird, ob die
Tafel am Schirm einen Unterschied ZEIGT.

Die Kiosk-Tafeln werden ueber `?screen=` UND `#hash` erreicht; gefahren wird
mit Rolle `admin` (das ist der Vorschau-Weg, den `_canKiosk` erlaubt). Die
Rollen `lager_display` und `stempel_terminal` koennen hier NICHT gefahren
werden - sie brauchen eine echte Anmeldung. Siehe "Was nicht gemessen ist".

🔴 SELBSTPROBE - EIN KOEDER JE FORM, PLUS GEGENPROBE
----------------------------------------------------
Vor jeder Messreihe wird in dieselbe Seite eingesetzt:

  * ein Hinweistext JE FORM (Warnzeichen, "Fehler", "nicht aktualisiert",
    "Keine Verbindung") - der Hinweis-Melder MUSS alle vier finden;
  * eine Schrift von 9 px - der Schrift-Melder MUSS sie finden;
  * ein Farbpaar #777777 auf #888888 - der Kontrast-Melder MUSS es ruegen.

GEGENPROBEN in die andere Richtung, ohne die "Koeder gefunden" nichts
belegt:

  * dieselben Hinweistexte in einem Knoten mit `display:none` und in einem
    HTML-Kommentar duerfen NICHT gefunden werden;
  * eine 9-px-Schrift mit `visibility:hidden` darf NICHT mitzaehlen;
  * #000000 auf #ffffff darf NICHT geruegt werden;
  * nach dem Entfernen des Koeders muessen alle Zahlen auf den Stand von
    VORHER zurueckfallen (restlos) - ein Melder, der den Koeder auch dann
    noch sieht, misst etwas anderes als die Seite.

Scheitert eine Probe, bricht der Lauf mit 2 ab und nennt KEINE Zahl.

AUFRUF
------
    python scripts/kiosk_tafeln_live.py
    python scripts/kiosk_tafeln_live.py --json docs/befunde/KIOSK_LIVE.json
"""
import io
import json
import os
import sys
import threading

for _strom in (sys.stdout, sys.stderr):
    try:
        _strom.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)

from tab_sweep import INIT  # noqa: E402

ANSICHTEN = ["planung", "monteure", "stempel"]
MODI = ["aus", "leer", "403"]
# 1920x1080 = Wandmonitor/TV.  1280x800 = das EDATEC-Panel, das im Quelltext
# als Zielaufloesung des Stempel-Terminals genannt ist (v3.9.693 Teil G).
GROESSEN = [(1920, 1080), (1280, 800)]

# 🔴 DIE ROLLE IST KEIN BEIWERK, SIE IST EIN ANDERER DATENWEG.
# `admin` ist der VORSCHAU-Weg: der Bootstrap laedt ueber API.getWorkers /
# API.request, und die Kiosk-Marken `__kioskAsErr` / `__kioskFzErr` werden
# dabei NIE gesetzt. Am echten Wandpanel laeuft `lager_display`, und dort
# gehen dieselben Ansichten ueber die kiosk_*-RPCs. Wer nur `admin` misst,
# misst die Marken an einem Pfad, auf dem es sie gar nicht gibt - und eine
# Null von dort sagt nichts ueber das Panel an der Wand.
# `_canKiosk` nimmt die Rolle aus localStorage (public.users.role), nicht aus
# einem JWT-Anspruch - darum laesst sie sich hier setzen.
ROLLEN = {
    "admin": "admin",                     # Vorschau, braucht ?screen=
    "lager_display": "lager_display",     # das Wandpanel (planung/monteure)
    "stempel_terminal": "stempel_terminal",  # das Panel am Werkstor
}

# Die Formen, in denen diese App einen Ladefehler ueberhaupt ausdrueckt.
# EIN KOEDER JE FORM - ein Melder, der eine Form nicht kennt, meldet
# "kein Hinweis" und das sieht aus wie ein Befund.
HINWEIS_FORMEN = [
    "⚠",                 # Warnzeichen, ohne Variantenselektor
    "Fehler",
    "nicht aktualisiert",
    "Keine Verbindung",
]

# ═══════════════════════════════════════════════════════════════════════════
# Die Melder, als Seitenskripte
# ═══════════════════════════════════════════════════════════════════════════
HINWEIS_JS = """(formen) => {
  const w = document.getElementById('root') || document.body;
  const txt = (w.innerText || '');
  const aus = {};
  for (const f of formen) if (txt.indexOf(f) >= 0) aus[f] = true;
  return {gefunden: Object.keys(aus), textlaenge: txt.length,
          text: txt.slice(0, 1400)};
}"""

# Sichtbar heisst: eine Flaeche > 0 UND nicht visibility:hidden. Ein Knoten
# mit display:none hat keine Flaeche; einer mit visibility:hidden schon -
# darum wird BEIDES gefragt. Ohne die zweite Frage haette der Koeder mit
# visibility:hidden mitgezaehlt, und die Gegenprobe waere gruen geworden,
# obwohl der Melder unsichtbaren Text misst.
#
# 🔴 UND `getComputedStyle().fontSize` IST NICHT DIE GROESSE AM SCHIRM.
# WochenplanTafel und MonteurTafel legen ihren ganzen Inhalt in einen Knoten
# mit `transform: scale(_fitScale)`, Klemmbereich 0,6 bis 1,25. Eine
# Transformation aendert `fontSize` NICHT - der berechnete Wert bleibt 12 px,
# waehrend am Schirm 15 px stehen (oder 7,2). Ein Melder, der nur
# `fontSize` liest, misst also eine Zahl, die es auf dem Bildschirm nicht
# gibt - in BEIDE Richtungen falsch. Darum wird die Streckung aus
# rect.height / offsetHeight zurueckgerechnet und BEIDES ausgewiesen.
SCHRIFT_JS = """() => {
  const w = document.getElementById('root') || document.body;
  const alle = w.querySelectorAll('*');
  const treffer = [];
  let gezaehlt = 0;
  for (const el of alle) {
    let eigen = '';
    for (const k of el.childNodes)
      if (k.nodeType === 3) eigen += k.nodeValue;
    eigen = eigen.replace(/\\s+/g, ' ').trim();
    if (!eigen) continue;
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    const px = parseFloat(cs.fontSize) || 0;
    // Streckung: wie viel groesser ist der Knoten am Schirm, als sein
    // ungestrecktes Layout es vorsieht. 1 = keine Transformation.
    const roh = el.offsetHeight || 0;
    let sk = (roh > 0) ? (r.height / roh) : 1;
    if (!isFinite(sk) || sk <= 0) sk = 1;
    sk = Math.round(sk * 1000) / 1000;
    gezaehlt++;
    treffer.push({px: px, skala: sk,
                  wirksam: Math.round(px * sk * 10) / 10,
                  txt: eigen.slice(0, 40), tag: el.tagName.toLowerCase()});
  }
  treffer.sort((a, b) => a.wirksam - b.wirksam);
  const hist = {};
  for (const t of treffer) hist[t.px] = (hist[t.px] || 0) + 1;
  const skalen = {};
  for (const t of treffer) skalen[t.skala] = (skalen[t.skala] || 0) + 1;
  return {knoten: gezaehlt,
          min: treffer.length ? treffer[0].px : null,
          min_wirksam: treffer.length ? treffer[0].wirksam : null,
          skalen: skalen,
          unter_12: treffer.filter(t => t.px < 12).length,
          unter_16: treffer.filter(t => t.px < 16).length,
          unter_24: treffer.filter(t => t.px < 24).length,
          wirksam_unter_12: treffer.filter(t => t.wirksam < 12).length,
          wirksam_unter_16: treffer.filter(t => t.wirksam < 16).length,
          wirksam_unter_24: treffer.filter(t => t.wirksam < 24).length,
          histogramm: hist,
          kleinste: treffer.slice(0, 12)};
}"""

# Kontrast am GERENDERTEN Knoten: die Vordergrundfarbe kommt aus
# getComputedStyle, der Hintergrund wird nach oben gesucht, bis eine
# deckende Farbe kommt. Ein Knoten ohne auffindbaren Hintergrund wird NICHT
# gezaehlt - eine erfundene Zahl waere schlimmer als eine fehlende.
KONTRAST_JS = """() => {
  const zuRgb = (s) => {
    const m = String(s).match(/rgba?\\(([^)]+)\\)/);
    if (!m) return null;
    const p = m[1].split(',').map(x => parseFloat(x.trim()));
    return {r: p[0], g: p[1], b: p[2], a: (p.length > 3 ? p[3] : 1)};
  };
  const lum = (c) => {
    const f = (v) => { v = v / 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b);
  };
  const w = document.getElementById('root') || document.body;
  const aus = [];
  let ohneHg = 0;
  for (const el of w.querySelectorAll('*')) {
    let eigen = '';
    for (const k of el.childNodes) if (k.nodeType === 3) eigen += k.nodeValue;
    eigen = eigen.replace(/\\s+/g, ' ').trim();
    if (!eigen) continue;
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden') continue;
    const vg = zuRgb(cs.color);
    if (!vg) continue;
    let p = el, hg = null;
    while (p) {
      const c = zuRgb(getComputedStyle(p).backgroundColor);
      if (c && c.a >= 0.95) { hg = c; break; }
      p = p.parentElement;
    }
    if (!hg) { ohneHg++; continue; }
    const a = lum(vg), b = lum(hg);
    const k = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    const px = parseFloat(cs.fontSize) || 0;
    const fett = (parseInt(cs.fontWeight, 10) || 400) >= 700;
    const gross = px >= 24 || (px >= 18.66 && fett);
    const soll = gross ? 3.0 : 4.5;
    if (k < soll) aus.push({k: Math.round(k * 100) / 100, px: px,
                            soll: soll, txt: eigen.slice(0, 40)});
  }
  aus.sort((a, b) => a.k - b.k);
  return {geruegt: aus.length, ohne_hintergrund: ohneHg,
          schlimmste: aus.slice(0, 10)};
}"""

# Eingabefelder: die Frage nach dem !important. Im Quelltext der StempelTafel
# steht clamp(20px,...); GCSS fuehrt `input,select,textarea{font-size:16px
# !important}`. Welcher Wert am Schirm ankommt, sagt nur getComputedStyle.
EINGABE_JS = """() => {
  const w = document.getElementById('root') || document.body;
  const aus = [];
  for (const el of w.querySelectorAll('input,select,textarea')) {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    aus.push({tag: el.tagName.toLowerCase(), typ: el.type || '',
              px: parseFloat(cs.fontSize) || 0,
              inline: (el.getAttribute('style') || '').slice(0, 90),
              sichtbar: r.width > 0 && r.height > 0});
  }
  return aus;
}"""

# 🔴 WIRKT DIE !important-REGEL? Nicht: steht sie da.
# GCSS() fuehrt `@media(min-width:601px){input,select,textarea{font-size:
# 14px !important}}`. Ob das eine Inline-Angabe schlaegt, sagt nur ein
# gerendeter Knoten. Eingesetzt wird ein Eingabefeld MIT 30 px inline und -
# als GEGENPROBE - ein div mit denselben 30 px: der Selektor nennt nur
# input/select/textarea, das div MUSS also bei 30 bleiben. Ohne die
# Gegenprobe waere "14 gemessen" auch mit einer Regel vereinbar, die ALLES
# auf 14 zieht, und die Aussage ueber die Eingabefelder waere leer.
EINFLUSS_JS = """() => {
  const w = document.getElementById('root') || document.body;
  let z = document.getElementById('__wichtigprobe');
  if (z) z.remove();
  z = document.createElement('div');
  z.id = '__wichtigprobe';
  z.innerHTML =
    '<input id="__wp_i" style="font-size:30px" value="x">' +
    '<select id="__wp_s" style="font-size:30px"><option>x</option></select>' +
    '<textarea id="__wp_t" style="font-size:30px">x</textarea>' +
    '<div id="__wp_d" style="font-size:30px">x</div>';
  w.appendChild(z);
  const g = (id) => parseFloat(getComputedStyle(
      document.getElementById(id)).fontSize) || 0;
  const aus = {input: g('__wp_i'), select: g('__wp_s'),
               textarea: g('__wp_t'), div_gegenprobe: g('__wp_d')};
  z.remove();
  aus.restlos = !document.getElementById('__wichtigprobe');
  return aus;
}"""

KOEDER_EIN_JS = """(formen) => {
  const w = document.getElementById('root') || document.body;
  let z = document.getElementById('__kioskprobe');
  if (z) z.remove();
  z = document.createElement('div');
  z.id = '__kioskprobe';
  const sicht = formen.map(f => '<div>' + f + '</div>').join('');
  const blind = formen.map(f => '<div>' + f + '</div>').join('');
  z.innerHTML =
    '<div>' + sicht + '</div>' +
    '<div style="display:none">' + blind + '</div>' +
    '<!-- ' + formen.join(' ') + ' -->' +
    '<span style="font-size:9px">winzig sichtbar</span>' +
    '<span style="font-size:9px;visibility:hidden">winzig blind</span>' +
    '<span style="color:#777777;background:#888888;font-size:14px">' +
      'grau auf grau</span>' +
    '<span style="color:#000000;background:#ffffff;font-size:14px">' +
      'schwarz auf weiss</span>';
  w.appendChild(z);
  return true;
}"""

KOEDER_WEG_JS = """() => {
  const z = document.getElementById('__kioskprobe');
  if (z && z.parentElement) z.parentElement.removeChild(z);
  return !document.getElementById('__kioskprobe');
}"""


def _rollen_js(rolle):
    """Die Rolle in den gespeicherten Nutzer schreiben - VOR dem ersten Bild.

    `_canKiosk` liest `curUser.role`; curUser kommt beim Start aus
    localStorage('epkolar_user'). Der INIT aus tab_sweep setzt dort `admin`.
    """
    return ("try{var u=JSON.parse(localStorage.getItem('epkolar_user')"
            "||'{}');u.role=%s;localStorage.setItem('epkolar_user',"
            "JSON.stringify(u));}catch(e){}" % json.dumps(rolle))


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


def _route(modus):
    """Die Netzhaltung als Playwright-Weiche."""
    if modus == "aus":
        return lambda r: r.abort()
    if modus == "leer":
        return lambda r: r.fulfill(status=200, body="[]",
                                   headers={"content-type": "application/json",
                                            "access-control-allow-origin": "*"})
    if modus == "403":
        koerper = json.dumps({"code": "42501",
                              "message": "permission denied for table"})
        return lambda r: r.fulfill(status=403, body=koerper,
                                   headers={"content-type": "application/json",
                                            "access-control-allow-origin": "*"})
    raise ValueError(modus)


def selbstprobe(seite):
    """Koeder je Form, Gegenprobe, Restlos-Probe. Gibt (ok, zeilen)."""
    z = []
    ok = True

    def sagt(name, ist, soll):
        nonlocal ok
        gut = (ist == soll)
        if not gut:
            ok = False
        z.append("    %-40s %-14s soll %-14s %s"
                 % (name, ist, soll, "OK" if gut else "GESCHEITERT"))

    vor_h = seite.evaluate(HINWEIS_JS, HINWEIS_FORMEN)["gefunden"]
    vor_s = seite.evaluate(SCHRIFT_JS)
    vor_k = seite.evaluate(KONTRAST_JS)["geruegt"]

    seite.evaluate(KOEDER_EIN_JS, HINWEIS_FORMEN)
    nach_h = seite.evaluate(HINWEIS_JS, HINWEIS_FORMEN)["gefunden"]
    nach_s = seite.evaluate(SCHRIFT_JS)
    nach_k = seite.evaluate(KONTRAST_JS)

    sagt("Hinweis: alle vier Formen gefunden",
         sorted(nach_h), sorted(HINWEIS_FORMEN))
    # Der Koeder setzt JE FORM einen sichtbaren, einen display:none-Knoten und
    # einen HTML-Kommentar. innerText liefert nur den sichtbaren - waere das
    # anders, stuenden die Formen dreifach im Text.
    sagt("Schrift: 9-px-Koeder gefunden",
         nach_s["min"], 9)
    # visibility:hidden-Zwilling darf NICHT mitzaehlen: sonst waeren es zwei.
    sagt("Schrift: nur der SICHTBARE 9-px-Knoten",
         nach_s["unter_12"] - vor_s["unter_12"], 1)
    sagt("Kontrast: grau auf grau geruegt",
         nach_k["geruegt"] - vor_k, 1)

    # Die !important-Probe traegt ihre Gegenprobe in sich: das div MUSS bei
    # 30 bleiben. Bleibt es das nicht, misst der Melder nicht die Regel fuer
    # Eingabefelder, sondern irgendetwas, das alles kleinmacht.
    ei = seite.evaluate(EINFLUSS_JS)
    sagt("!important-Probe: div bleibt 30 px", ei["div_gegenprobe"], 30)
    sagt("!important-Probe restlos entfernt", ei["restlos"], True)

    weg = seite.evaluate(KOEDER_WEG_JS)
    rest_h = seite.evaluate(HINWEIS_JS, HINWEIS_FORMEN)["gefunden"]
    rest_s = seite.evaluate(SCHRIFT_JS)
    rest_k = seite.evaluate(KONTRAST_JS)["geruegt"]
    sagt("Koeder restlos entfernt", weg, True)
    sagt("Hinweis zurueck auf Stand VORHER", sorted(rest_h), sorted(vor_h))
    sagt("Schrift zurueck auf Stand VORHER",
         rest_s["unter_12"], vor_s["unter_12"])
    sagt("Kontrast zurueck auf Stand VORHER", rest_k, vor_k)
    return ok, z


def uhrprobe(b, port, minuten=40):
    """Was steht nach <minuten> ohne Netz im Kopf der Tafel?

    🔴 DER KOEDER STECKT IN DER PROBE SELBST - und er ist bewusst NICHT
    selbstgebaut, sondern der ZWILLING. Die MonteurTafel hat seit v3.9.939
    einen Alterstext ("seit N min nicht aktualisiert"). Erscheint der nach
    der Zeitreise NICHT, dann hat die vorgestellte Uhr nicht gewirkt - und
    "die WochenplanTafel zeigt kein Alter" waere dann eine Eigenschaft
    meines Werkzeugs, nicht der Tafel. Genau diese Verwechslung ist die
    teuerste Form eines Fehlbefunds: eine saubere Zahl, die nichts misst.

    Gibt {ansicht: {vor, nach}} zurueck, plus 'koeder_ok'.
    """
    aus = {}
    for scr in ("monteure", "planung"):
        ctx = b.new_context(viewport={"width": 1920, "height": 1080})
        ctx.add_init_script(INIT)
        ctx.add_init_script(_rollen_js("lager_display"))
        ctx.route("**/rest/v1/**", _route("aus"))
        ctx.route("**/auth/v1/**", _route("aus"))
        s = ctx.new_page()
        s.clock.install()
        s.goto("http://127.0.0.1:%d/index.html#%s" % (port, scr),
               wait_until="domcontentloaded")
        s.wait_for_timeout(5200)
        vor = s.evaluate("()=>document.getElementById('root')"
                         ".innerText.slice(0,150)")
        s.clock.run_for("%d:00" % minuten)
        s.wait_for_timeout(1200)
        nach = s.evaluate("()=>document.getElementById('root')"
                          ".innerText.slice(0,150)")
        aus[scr] = {"vor": vor.replace("\n", " | "),
                    "nach": nach.replace("\n", " | "),
                    "alterstext": "nicht aktualisiert" in nach}
        ctx.close()
    aus["minuten"] = minuten
    aus["koeder_ok"] = aus["monteure"]["alterstext"]
    return aus


def main(json_ziel=None):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt.  pip install playwright && "
              "playwright install chromium")
        return 2

    port = _server()
    erg = {"breiten": GROESSEN, "laeufe": [], "selbstprobe": []}
    probe_gefahren = False
    alles_ok = True

    # ── Die Auftragsliste. Jeder Eintrag nennt seinen WEG ausdruecklich:
    #    "query+hash", "nur hash" oder "ohne" (das Terminal landet ohne
    #    jeden Zusatz auf seinem Schirm). Der Weg ist selbst ein Befund -
    #    `_canKiosk` verlangt fuer `admin` die QUERY, nicht den Hash.
    auftraege = []
    for (bw, bh) in GROESSEN:
        for scr in ANSICHTEN:
            for modus in MODI:
                auftraege.append(("admin", scr, modus, bw, bh, "query+hash"))
    for scr in ("planung", "monteure"):
        for modus in MODI:
            auftraege.append(("lager_display", scr, modus, 1920, 1080,
                              "nur hash"))
    for modus in MODI:
        auftraege.append(("stempel_terminal", "stempel", modus, 1280, 800,
                          "ohne"))
    # Wegprobe: derselbe Schirm, derselbe Modus, NUR der Hash - fuer `admin`.
    auftraege.append(("admin", "planung", "leer", 1920, 1080, "nur hash"))
    # 🔴 DIE ANDERE RICHTUNG DER AUTO-STRECKUNG.
    # `_fit` rechnet sc = min(1.25, max(0.6, wh/ch)): Fensterhoehe durch
    # Inhaltshoehe. Bei LEEREM Brett ist ch klein, sc steht auf 1,25 - die
    # Schrift wird GROESSER. Bei einer vollen Woche waechst ch, und sc
    # faellt bis auf 0,6: aus 12 px werden dann 7,2. Die Messung oben faehrt
    # nur den leeren Fall und wuerde allein den freundlichen Wert nennen.
    # Ein grosses ch laesst sich hier nicht saeen, ein kleines wh schon -
    # im Bruch wh/ch ist das dieselbe Rechnung. 380 px Fensterhoehe
    # entspricht damit einem Brett mit knapp dreimal so viel Inhalt.
    for scr in ("planung", "monteure"):
        auftraege.append(("lager_display", scr, "leer", 1920, 380,
                          "nur hash"))

    with sync_playwright() as pw:
        b = pw.chromium.launch()
        if True:
            if True:
                for (rolle, scr, modus, bw, bh, weg) in auftraege:
                    ctx = b.new_context(viewport={"width": bw, "height": bh})
                    ctx.add_init_script(INIT)
                    ctx.add_init_script(_rollen_js(ROLLEN[rolle]))
                    ctx.route("**/rest/v1/**", _route(modus))
                    ctx.route("**/auth/v1/**", _route(modus))
                    fehler = []
                    s = ctx.new_page()
                    s.on("pageerror",
                         lambda e: fehler.append(str(e)[:150]))
                    zusatz = {"query+hash": "?screen=%s#%s" % (scr, scr),
                              "nur hash": "#%s" % scr,
                              "ohne": ""}[weg]
                    s.goto("http://127.0.0.1:%d/index.html%s"
                           % (port, zusatz), wait_until="domcontentloaded")
                    s.wait_for_timeout(5200)

                    if not probe_gefahren:
                        ok, zeilen = selbstprobe(s)
                        erg["selbstprobe"] = zeilen
                        print("SELBSTPROBE (%s, %dx%d, Netz=%s)"
                              % (scr, bw, bh, modus))
                        pass
                        for l in zeilen:
                            print(l)
                        if not ok:
                            print("\nABBRUCH: eine Probe ist gescheitert. "
                                  "Es wird KEINE Zahl genannt.")
                            ctx.close()
                            b.close()
                            return 2
                        print("    -> alle Proben bestanden\n")
                        probe_gefahren = True

                    hin = s.evaluate(HINWEIS_JS, HINWEIS_FORMEN)
                    sch = s.evaluate(SCHRIFT_JS)
                    kon = s.evaluate(KONTRAST_JS)
                    eing = s.evaluate(EINGABE_JS)
                    einfluss = s.evaluate(EINFLUSS_JS)
                    marken = s.evaluate(
                        "()=>({rls:(window.__EP_RLS||[]).length,"
                        "asErr:window.__kioskAsErr===undefined?'(nie gesetzt)'"
                        ":String(window.__kioskAsErr),"
                        "fzErr:window.__kioskFzErr===undefined?'(nie gesetzt)'"
                        ":String(window.__kioskFzErr),"
                        "screen:String(window.__kioskScreen||'')})")

                    d = {"ansicht": scr, "modus": modus,
                         "rolle": rolle, "weg": weg,
                         "breite": bw, "hoehe": bh,
                         "hinweise": hin["gefunden"],
                         "textlaenge": hin["textlaenge"],
                         "text": hin["text"],
                         "schrift_min": sch["min"],
                         "schrift_min_wirksam": sch["min_wirksam"],
                         "schrift_knoten": sch["knoten"],
                         "skalen": sch["skalen"],
                         "unter_12": sch["unter_12"],
                         "unter_16": sch["unter_16"],
                         "unter_24": sch["unter_24"],
                         "wirksam_unter_12": sch["wirksam_unter_12"],
                         "wirksam_unter_16": sch["wirksam_unter_16"],
                         "wirksam_unter_24": sch["wirksam_unter_24"],
                         "histogramm": sch["histogramm"],
                         "kleinste": sch["kleinste"][:8],
                         "wichtig_probe": einfluss,
                         "kontrast_geruegt": kon["geruegt"],
                         "kontrast_ohne_hg": kon["ohne_hintergrund"],
                         "kontrast_schlimmste": kon["schlimmste"][:5],
                         "eingaben": eing,
                         "marken": marken,
                         "pagefehler": fehler[:4]}
                    erg["laeufe"].append(d)
                    print("%-16s %-9s %-5s %-10s %4dx%-4d  Hinweise:%-22s "
                          "Text:%5d  <24px:%3d (wirksam %3d)  min:%-5s "
                          "(wirksam %-5s)  Ruegen:%-3d __EP_RLS:%-3d "
                          "input@30px->%s"
                          % (rolle, scr, modus, weg, bw, bh,
                             (",".join(hin["gefunden"]) or "KEINE"),
                             hin["textlaenge"], sch["unter_24"],
                             sch["wirksam_unter_24"],
                             sch["min"], sch["min_wirksam"],
                             kon["geruegt"], marken["rls"],
                             einfluss["input"]))
                    ctx.close()

        # ── Zeitreise: 40 Minuten ohne Netz ───────────────────────────────
        up = uhrprobe(b, port)
        erg["uhrprobe"] = up
        print("\nUHRPROBE - %d Minuten ohne Netz, Rolle lager_display"
              % up["minuten"])
        if not up["koeder_ok"]:
            print("  ABBRUCH: der KOEDER hat nicht angeschlagen. Die "
                  "MonteurTafel MUSS nach %d Minuten 'nicht aktualisiert' "
                  "zeigen; tut sie es nicht, hat die vorgestellte Uhr nicht "
                  "gewirkt und jede Aussage ueber die WochenplanTafel waere "
                  "eine Aussage ueber dieses Werkzeug." % up["minuten"])
            b.close()
            return 2
        for scr in ("monteure", "planung"):
            print("  %-9s t+0   : %s" % (scr, up[scr]["vor"][:120]))
            print("  %-9s t+%dm : %s  -> Alterstext: %s"
                  % (scr, up["minuten"], up[scr]["nach"][:120],
                     "JA" if up[scr]["alterstext"] else "NEIN"))
        b.close()

    if json_ziel:
        with io.open(json_ziel, "w", encoding="utf-8", newline="") as f:
            f.write(json.dumps(erg, ensure_ascii=False, indent=1))
        print("\ngeschrieben: %s" % json_ziel)
    return 0 if alles_ok else 2


if __name__ == "__main__":
    ziel = None
    if "--json" in sys.argv:
        ziel = sys.argv[sys.argv.index("--json") + 1]
    sys.exit(main(ziel))
