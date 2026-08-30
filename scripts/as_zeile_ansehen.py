# -*- coding: utf-8 -*-
"""Die AS-Zeile am RECHNER-Schirm ansehen - der offene Punkt 24 aus dem Handoff.

WOFUER DAS DA IST
-----------------
v3.9.918 hat vier der sechs Zeilen-Editoren im Ruhezustand rahmenlos gemacht.
Ausgeliefert wurde das mit einer ehrlichen Luecke: **es hat kein Browser
gesehen.** Dass die Bedienelemente ohne Rahmen auffindbar bleiben, war
begruendet (Pfeil und Kalendersymbol bleiben stehen) und per Riegel
festgenagelt - aber nicht angesehen. Genau die Sorte Aussage, die sich in
diesem Repo schon mehrfach als falsch herausgestellt hat.

WARUM `tab_sweep.py` DAS NICHT KONNTE
-------------------------------------
Der Durchlauf faehrt mit 390x844 und `is_mobile=True`. Die App schaltet bei
`ww < 600` auf die Mobil-Karte - und die hat GAR KEINE Zeilen-Editoren
(0 select, 0 input, 0 updAs). Das Gate haette die geaenderte Stelle also nie
gerendert und trotzdem gruen gemeldet. Ein Messgeraet, das den fraglichen
Zweig nicht betritt, misst nichts.

WAS DIESES SKRIPT MISST
-----------------------
Denselben Schirm ZWEIMAL: einmal wie ausgeliefert, einmal mit abgeschalteter
Ruhe-Klasse. Der Vergleich ist die eigentliche Aussage - ein einzelnes Bild
zeigt nur, dass etwas da ist, nicht was sich geaendert hat.

Zusaetzlich wird GEMESSEN statt geschaut:
  * wieviele Bedienelemente in einer Zeile stehen
  * wie hoch ihre Tippziele wirklich sind (der Handoff nennt ~18-20 px als
    GERECHNET - hier steht die gemessene Zahl)
  * ob der Rahmen beim Zeigen zurueckkommt
  * ob Pfeil und Kalendersymbol noch da sind (die letzte Bedienbarkeitsanzeige)

BENUTZUNG
---------
    python scripts/as_zeile_ansehen.py
    python scripts/as_zeile_ansehen.py --breite 1024

Legt PNGs neben sich ab und meldet die Zahlen auf stdout.
"""
import io
import os
import subprocess
import sys
import threading
import time

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)

from tab_sweep import INIT, IGNORIEREN, saeen  # noqa: E402

# Fester Port war ein Fehler: bleibt ein Lauf haengen, scheitert der
# naechste an "Adresse belegt" statt an der Sache. 0 = das Betriebssystem
# sucht einen freien.
PORT = 0
ZIEL = os.path.join(WURZEL, "screenshots")

# Die Ruhe-Klasse aus v3.9.918. Zum Abschalten wird sie im Browser
# ueberschrieben - index.html wird NICHT angefasst.
AUS_JS = """() => {
  const s = document.createElement('style');
  s.id = '__aus';
  s.textContent = '.epk-ruhig{border-color:#4b5563 !important}';
  document.head.appendChild(s);
}"""


def _server():
    """Statischer Server auf dem Repo - die Live-App traegt v918 evtl. noch nicht."""
    import http.server
    import socketserver
    os.chdir(WURZEL)
    class Still(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = socketserver.TCPServer(("127.0.0.1", PORT), Still)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv.server_address[1]


MESS_JS = """() => {
  const tr = Array.from(document.querySelectorAll('tr'))
    .filter(r => r.querySelectorAll('select,input').length >= 3)
    .sort((a,b) => b.querySelectorAll('select,input,button').length
                 - a.querySelectorAll('select,input,button').length)[0];
  if (!tr) return {gefunden:false};

  const el = Array.from(tr.querySelectorAll('select,input,button,td[onclick]'));
  const bed = Array.from(tr.querySelectorAll('select,input'));
  const kn  = Array.from(tr.querySelectorAll('button'));

  const beschreibe = (e) => {
    const cs = getComputedStyle(e);
    const r  = e.getBoundingClientRect();
    return {
      tag: e.tagName.toLowerCase(),
      typ: e.getAttribute('type') || '',
      ruhig: e.classList.contains('epk-ruhig'),
      rahmen: cs.borderTopColor,
      breite_rahmen: cs.borderTopWidth,
      appearance: cs.appearance,
      hoehe: Math.round(r.height * 10) / 10,
      breite: Math.round(r.width * 10) / 10,
      hintergrund: cs.backgroundColor,
      textfarbe: cs.color,
      zellgrund: getComputedStyle(e.closest('td') || e).backgroundColor,
    };
  };

  return {
    gefunden: true,
    zeilenbreite: Math.round(tr.getBoundingClientRect().width),
    editoren: bed.length,
    knoepfe: kn.length,
    // React haengt onClick als EIGENSCHAFT an, nicht als Attribut:
    // td[onclick] findet nie etwas und meldete stumm 0. Ueber die
    // interne Faser gezaehlt; geht das nicht, wird -1 gemeldet und
    // der Aufrufer sagt 'nicht messbar' statt einer Zahl.
    klickzellen: (() => {
      const tds = Array.from(tr.querySelectorAll('td'));
      let konnte = false, n = 0;
      for (const td of tds) {
        const k = Object.keys(td).find(x => x.startsWith('__reactProps$'));
        if (!k) continue;
        konnte = true;
        if (typeof td[k].onClick === 'function') n++;
      }
      return konnte ? n : -1;
    })(),
    klickziele: el.length,
    ruhig: bed.filter(e => e.classList.contains('epk-ruhig')).length,
    felder: bed.map(beschreibe),
    // v3.9.919: knopf_flaechen wurde eingesammelt und NIE gedruckt - die
    // Groesse, um die in Punkt 25 gestritten wird, war also gar nicht
    // gemessen. Jetzt vollstaendig: Flaeche, Fuellung, Rahmen, Beschriftung.
    knoepfe_detail: kn.map(e => {
      const cs = getComputedStyle(e), r = e.getBoundingClientRect();
      return {
        text: (e.textContent || '').trim(),
        titel: e.getAttribute('title') || '',
        fuellung: cs.backgroundColor,
        rahmen: cs.borderTopStyle === 'none' ? '' : cs.borderTopColor,
        rahmenbreite: cs.borderTopWidth,
        textfarbe: cs.color,
        breite: Math.round(r.width * 10) / 10,
        hoehe: Math.round(r.height * 10) / 10,
        flaeche: Math.round(r.width * r.height),
      };
    }),
    knopf_flaechen: kn.map(e => getComputedStyle(e).backgroundColor),
    seitengrund: getComputedStyle(document.body).backgroundColor,
    zeilengrund: getComputedStyle(tr).backgroundColor,
  };
}"""



# Der Rahmen kommt laut CSS in `currentColor` zurueck - das ist die TEXTFARBE
# des Elements. Ob er damit SICHTBAR ist, entscheidet der Kontrast zum
# Untergrund. Genau das war bisher eine Annahme und keine Messung.
ZEIG_JS = """() => {
  const e = document.querySelector('select.epk-ruhig:hover');
  if (!e) return null;
  const cs = getComputedStyle(e);
  // ERSTER VERSUCH WAR FALSCH und hat lautstark Alarm geschlagen:
  // die Zeile traegt rgba(0,0,0,0.03) - fast durchsichtig. Der alte Code
  // nahm die ersten drei Zahlen und rechnete damit REINES SCHWARZ, kam auf
  // 1,25:1 und meldete 'ZU SCHWACH'. Ein Messgeraet, das seinen eigenen
  // Fehler als Befund ausgibt, ist schlimmer als keines.
  // Alpha muss ueber den Elterngrund VERRECHNET werden.
  const zahl4 = (s) => {
    const m = (s || '').match(/[0-9.]+/g) || ['0','0','0'];
    const v = m.slice(0,3).map(Number);
    return [v[0]||0, v[1]||0, v[2]||0, m.length > 3 ? Number(m[3]) : 1];
  };
  const grundVon = (el) => {
    const schichten = [];
    while (el) {
      const c = zahl4(getComputedStyle(el).backgroundColor);
      if (c[3] > 0) schichten.push(c);
      if (c[3] >= 1) break;
      el = el.parentElement;
    }
    let r = [255,255,255];
    for (let i = schichten.length - 1; i >= 0; i--) {
      const s = schichten[i], a = s[3];
      r = [0,1,2].map(k => s[k]*a + r[k]*(1-a));
    }
    return r;
  };
  const zahl = (s) => zahl4(s).slice(0,3);
  const leucht = (rgb) => {
    const f = rgb.map(v => { v /= 255;
      return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); });
    return 0.2126*f[0] + 0.7152*f[1] + 0.0722*f[2];
  };
  const rand = cs.borderTopColor, grund = grundVon(e);
  const a = leucht(zahl(rand)), b = leucht(grund);
  const hell = Math.max(a,b), dunkel = Math.min(a,b);
  return {rand: rand,
          grund: 'rgb(' + grund.map(x => Math.round(x)).join(', ') + ')',
          textfarbe: cs.color,
          kontrast: (hell + 0.05) / (dunkel + 0.05)};
}"""



# Wie weit muss man scrollen, bis der erste Arbeitsschein zu sehen ist?
# Ein erster Entwurf hat KACHELN GEZAEHLT und dabei 0 gemeldet - die
# Heuristik traf die Kacheln nicht. Eine 0, die "nicht erkannt" heisst,
# sieht aus wie "keine da". Genau die Krankheit, gegen die dieses Repo diese
# Woche gekaempft hat. Also raus damit: gemessen wird nur, was sich
# eindeutig messen laesst - wie weit unten die Tabelle anfaengt. Wieviele
# Kacheln davor stehen, sagt der Blick aufs Bild.
VORBAU_JS = """() => {
  const t = document.querySelector('table');
  return {
    tabelle_y: t ? Math.round(t.getBoundingClientRect().top + window.scrollY) : -1,
    schirm: window.innerHeight,
    seitenhoehe: Math.round(document.documentElement.scrollHeight),
  };
}"""


# v3.9.920 - der VORSCHLAG zu Punkt 25, im Browser aufgesetzt, ohne
# index.html anzufassen. Genau das, was die Anker/Ersatz-Paare tun:
# PDF und QR verlieren ihre Fuellung, der Rahmen und die Beschriftung nehmen
# die bisherige Fuellfarbe, beim Zeigen kehrt die Fuellung zurueck - dieselbe
# Bauart wie .epk-ruhig aus v3.9.918 (Ruhe/Rueckkehr-Paar, echte Farbe steht
# inline, die Klasse schaltet nur um).
#
# BEARBEITEN und STORNIEREN werden NICHT angefasst:
#   * Bearbeiten ist die Vorgabehandlung der Zeile selbst (drei td tragen
#     onClick -> _openEditGuarded -> openEdit).
#   * Stornieren ist ein Warnzeichen. Ein Warnzeichen leiser zu machen ist
#     etwas anderes als eine Alltagshandlung leiser zu machen.
UMRISS_JS = """(gruen) => {
  const s = document.createElement('style');
  s.id = '__umriss';
  s.textContent = '.epk-flach{background:transparent !important;'
                + 'border:1px solid currentColor !important}'
                + '.epk-flach:hover,.epk-flach:focus-visible'
                + '{background:currentColor !important}';
  document.head.appendChild(s);
  let n = 0;
  document.querySelectorAll('button[title]').forEach(b => {
    const t = b.getAttribute('title') || '';
    let f = null;
    if (t.indexOf('PDF') === 0) f = gruen;
    else if (t.indexOf('QR') === 0) f = '#8b5cf6';
    if (!f) return;
    b.classList.add('epk-flach');
    b.style.color = f;
    // Der Rahmen kommt ZUSAETZLICH zum Kasten - ohne Ausgleich waechst jeder
    // Knopf um 2 px in jeder Richtung. Die Aktionsspalte ist 110 px breit und
    // laeuft mit vier Knoepfen schon ueber; ein Vorschlag, der die Zeile
    // BREITER macht, waere keine Entlastung. Also 1 px Polsterung raus.
    const pol = getComputedStyle(b).padding.split(' ');
    const minus = (v) => (parseFloat(v) - 1) + 'px';
    b.style.padding = minus(pol[0]) + ' ' + minus(pol[1] || pol[0]);
    n++;
  });
  return n;
}"""

# Was die Fuellung wegzunehmen KOSTET: bleibt der Rahmen auf dem Untergrund
# ueberhaupt sichtbar? Das ist die eine Groesse, die der Vorschlag riskiert -
# ein gruener Haarrahmen auf hellem Grund kann unter 3:1 fallen. (Er TAT es:
# #22c55e kam auf 2,28:1. Deshalb wird die Farbe ueber _okG geschickt.)
UMRISS_MESS_JS = """() => {
  const zahl4 = (s) => {
    const m = (s || '').match(/[0-9.]+/g) || ['0','0','0'];
    const v = m.slice(0,3).map(Number);
    return [v[0]||0, v[1]||0, v[2]||0, m.length > 3 ? Number(m[3]) : 1];
  };
  const grundVon = (el) => {
    const schichten = [];
    while (el) {
      const c = zahl4(getComputedStyle(el).backgroundColor);
      if (c[3] > 0) schichten.push(c);
      if (c[3] >= 1) break;
      el = el.parentElement;
    }
    let r = [255,255,255];
    for (let i = schichten.length - 1; i >= 0; i--) {
      const s = schichten[i], a = s[3];
      r = [0,1,2].map(k => s[k]*a + r[k]*(1-a));
    }
    return r;
  };
  const leucht = (rgb) => {
    const f = rgb.map(v => { v /= 255;
      return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); });
    return 0.2126*f[0] + 0.7152*f[1] + 0.0722*f[2];
  };
  const kontrast = (a, b) => {
    const x = leucht(a), y = leucht(b);
    return (Math.max(x,y) + 0.05) / (Math.min(x,y) + 0.05);
  };
  return Array.from(document.querySelectorAll('button.epk-flach'))
    .slice(0, 4).map(b => {
      const cs = getComputedStyle(b), r = b.getBoundingClientRect();
      const grund = grundVon(b.parentElement);
      return {
        titel: b.getAttribute('title') || '',
        text: (b.textContent || '').trim(),
        rahmen: cs.borderTopColor,
        rahmenbreite: cs.borderTopWidth,
        fuellung: cs.backgroundColor,
        grund: 'rgb(' + grund.map(x => Math.round(x)).join(', ') + ')',
        kontrast: kontrast(zahl4(cs.borderTopColor).slice(0,3), grund),
        breite: Math.round(r.width * 10) / 10,
        hoehe: Math.round(r.height * 10) / 10,
        flaeche: Math.round(r.width * r.height),
      };
    });
}"""

# Kommt die Fuellung beim Zeigen zurueck? Ohne diese Gegenprobe waere der
# Vorschlag dasselbe wie ein Knopf, der einfach blasser ist.
ZEIG_KNOPF_JS = """() => {
  const b = document.querySelector('button.epk-flach:hover');
  if (!b) return null;
  const cs = getComputedStyle(b);
  return {titel: b.getAttribute('title') || '', fuellung: cs.backgroundColor};
}"""


def _tinte(bild_bytes, rand=4):
    """Anteil Bildpunkte IM INNEREN, die nicht der Grundfarbe entsprechen.

    WOZU: der Kontrast-Rechner misst den RAHMEN gegen den Grund. Er sagt
    nichts darueber, ob die BESCHRIFTUNG noch zu sehen ist. Bei den Emoji ist
    das keine Nebensache - U+2B1C ist ein WEISSES Quadrat und stand bisher auf
    Violett. Auf durchsichtigem Grund im hellen Thema koennte es
    verschwinden. Das laesst sich nicht aus Farbwerten ableiten, weil die
    Emoji ihre eigenen Farben mitbringen; also wird das Bild selbst gezaehlt.

    ERSTER ENTWURF WAR FALSCH und haette eine schoene Zahl gemeldet: er nahm
    den ECKPUNKT als Grund. Der liegt wegen borderRadius ausserhalb der
    abgerundeten Form und ist deshalb immer der Seitengrund - gezaehlt wurde
    damit die FUELLUNG samt Rahmen, nicht das Zeichen. Beim gefuellten Knopf
    kam 0,95 heraus; das war die Fuellung, nicht die Beschriftung. Genau die
    Krankheit dieses Repos: eine Zahl, die etwas anderes misst als ihr Name.

    Jetzt: `rand` Punkte ringsum weg (schneidet Rundung UND Rahmen ab), dann
    die HAEUFIGSTE Farbe des Restes als Grund nehmen und zaehlen, was davon
    abweicht. Das ist das Zeichen.
    """
    from PIL import Image
    b = Image.open(io.BytesIO(bild_bytes)).convert("RGB")
    br, ho = b.size
    if br <= 2 * rand or ho <= 2 * rand:
        return None
    b = b.crop((rand, rand, br - rand, ho - rand))
    px = list(b.getdata())
    haeufig = {}
    for p in px:
        k = (p[0] // 8, p[1] // 8, p[2] // 8)
        haeufig[k] = haeufig.get(k, 0) + 1
    grund = max(haeufig, key=haeufig.get)
    anders = sum(1 for p in px
                 if max(abs(p[0] - grund[0] * 8 - 4),
                        abs(p[1] - grund[1] * 8 - 4),
                        abs(p[2] - grund[2] * 8 - 4)) > 24)
    return float(anders) / max(1, len(px))


def _knopf_tinte(seite, titel_anfang):
    """Tinte des ersten Knopfes, dessen Titel so anfaengt. None wenn keiner."""
    kn = seite.locator("button[title^='%s']" % titel_anfang)
    if not kn.count():
        return None
    try:
        return _tinte(kn.first.screenshot())
    except Exception:
        return None


KARTE_JS = """() => Array.from(document.querySelectorAll('button[title]'))
  .filter(b => ['Bearbeiten','PDF','QR','Stornieren']
                 .indexOf(b.getAttribute('title')) >= 0)
  .slice(0, 4).map(b => {
    const cs = getComputedStyle(b), r = b.getBoundingClientRect();
    return {
      text: (b.textContent || '').trim(),
      titel: b.getAttribute('title') || '',
      fuellung: cs.backgroundColor,
      breite: Math.round(r.width * 10) / 10,
      hoehe: Math.round(r.height * 10) / 10,
      flaeche: Math.round(r.width * r.height),
    };
  })"""


def _ist_gefuellt(farbe):
    """Zaehlt eine Hintergrundfarbe als FLAECHE?

    Nicht am Wortlaut gemessen, sondern an der Eigenschaft: eine Fuellung ist
    sie nur, wenn sie deckend genug ist, um als eigener Block zu lesen.
    rgba(...,0) und 'transparent' sind keine Flaeche.
    """
    zahlen = [float(x) for x in (farbe or "").replace(",", " ")
              .replace("(", " ").replace(")", " ").split()
              if _istzahl(x)]
    if len(zahlen) < 3:
        return False
    alpha = zahlen[3] if len(zahlen) > 3 else 1.0
    return alpha >= 0.5


def _istzahl(x):
    try:
        float(x)
        return True
    except ValueError:
        return False


def main(breite=1440, umriss=False, thema="system", schmal=0):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt.  pip install playwright && playwright install chromium")
        return 2

    os.makedirs(ZIEL, exist_ok=True)
    port = _server()
    url = "http://127.0.0.1:%d/index.html" % port
    fehler = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        # RECHNER-Schirm: is_mobile bleibt aus, sonst rendert die Mobil-Karte
        # und die geaenderte Stelle kommt gar nicht vor.
        ctx = browser.new_context(viewport={"width": breite, "height": 900},
                                  device_scale_factor=2)
        ctx.add_init_script(INIT)
        if thema in ("light", "dark"):
            ctx.add_init_script(
                "try{localStorage.setItem('epk_theme','%s');}catch(e){}"
                % thema)
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
        print("Schirmbreite:", breite, "px (is_mobile aus)")

        saeen(seite)
        seite.wait_for_timeout(3500)

        # Zur Arbeitsschein-Liste. Der Reiter traegt ein Emoji davor
        # ("📋 Arbeitsscheine"), exact=True trifft ihn deshalb NICHT -
        # erster Fehlschlag dieses Skripts, und einer, der leise war: es hat
        # anstandslos weitergemacht und erst an der leeren Zeile gemerkt,
        # dass es auf dem falschen Schirm steht.
        getroffen = None
        for name in ("Arbeitsscheine", "Scheine"):
            ziel = seite.get_by_text(name, exact=False)
            if ziel.count():
                ziel.first.click()
                getroffen = name
                break
        print("Reiter getroffen:", getroffen or "KEINER")
        seite.wait_for_timeout(2500)

        # MOBIL-KARTE: bei 390 px steht der Reiter hinter dem Klappmenue und
        # ist nicht anklickbar - ein Lauf mit --breite 390 lief deshalb in
        # einen Zeitueberlauf statt auf die Karte. Also: am breiten Schirm
        # hinnavigieren und ERST DANN schmal machen. Gemessen wird trotzdem
        # der Mobil-Zweig (die App entscheidet an ww < 600, nicht am Weg
        # dorthin).
        if schmal:
            seite.set_viewport_size({"width": schmal, "height": 900})
            seite.wait_for_timeout(1500)
            print("Auf %d px verschmaelert (Mobil-Zweig ab ww < 600)" % schmal)

        mess = seite.evaluate(MESS_JS)
        if schmal and not mess.get("gefunden"):
            # Die Mobil-Karte hat gar keine tr - MESS_JS findet nichts, und das
            # ist kein Fehler, sondern der Befund aus v3.9.918. Gemessen wird
            # hier nur, was es dort gibt: die Knoepfe.
            print()
            print("Mobil-Karte: keine Tabellenzeile (erwartet - dort stehen "
                  "die Werte als Chips).")
            print("KNOEPFE auf der Karte:")
            for k in seite.evaluate(KARTE_JS):
                print("  %-8s %-14s %-9s %-22s %s"
                      % (k["text"] or "?", k["titel"][:14],
                         str(k["flaeche"]) + " px2", k["fuellung"],
                         "%sx%s" % (k["breite"], k["hoehe"])))
            if umriss:
                gruen = seite.evaluate(
                    "() => { const c = getComputedStyle(document.body)"
                    ".backgroundColor.match(/[0-9.]+/g).slice(0,3).map(Number);"
                    "  const l = 0.2126*c[0] + 0.7152*c[1] + 0.0722*c[2];"
                    "  return l > 140 ? '#006e30' : '#22c55e'; }")
                vor_pdf = _knopf_tinte(seite, "PDF")
                vor_qr = _knopf_tinte(seite, "QR")
                n = seite.evaluate(UMRISS_JS, gruen)
                seite.wait_for_timeout(400)
                print()
                print("VORSCHLAG auf der Karte (%d Knoepfe, Gruen=%s)"
                      % (n, gruen))
                for u in seite.evaluate(UMRISS_MESS_JS):
                    print("  %-8s %-9s %-9s %-20s %.2f:1 auf %s"
                          % (u["text"] or u["titel"][:6],
                             str(u["flaeche"]) + " px2",
                             "%sx%s" % (u["breite"], u["hoehe"]),
                             u["rahmen"], u["kontrast"], u["grund"]))
                    if u["kontrast"] < 3.0:
                        print("     ROT: unter 3,0:1 - auf dem Handy gibt es "
                              "KEIN Zeigen, der Rahmen ist alles.")
                nach_pdf = _knopf_tinte(seite, "PDF")
                nach_qr = _knopf_tinte(seite, "QR")
                for name, v, w in (("PDF", vor_pdf, nach_pdf),
                                   ("QR", vor_qr, nach_qr)):
                    if v is None or w is None:
                        print("    %-4s Tinte nicht messbar" % name)
                    else:
                        print("    %-4s Tinte vorher %.3f  nachher %.3f"
                              % (name, v, w))
                seite.screenshot(path=os.path.join(
                    ZIEL, "as_karte_UMRISS_%s_%d.png" % (thema, schmal)))
            return 1 if fehler else 0
        if not mess.get("gefunden"):
            print("KEINE Zeile mit Editoren gefunden - der Schirm zeigt die Liste nicht.")
            print("Ein Bild davon waere wertlos; hier wird nichts behauptet.")
            return 1

        print()
        print("GEMESSEN an der echten Zeile")
        print("  Zeilenbreite  :", mess["zeilenbreite"], "px")
        print("  Editoren      :", mess["editoren"], " davon ruhig:", mess["ruhig"])
        print("  Knoepfe       :", mess["knoepfe"])
        print("  klickbare td  :",
              "nicht messbar (keine React-Faser gefunden)"
              if mess["klickzellen"] < 0 else mess["klickzellen"])
        print("  Seitengrund   :", mess["seitengrund"],
              " Zeilengrund:", mess["zeilengrund"])
        print("  Klickziele    :", mess["klickziele"])
        print()
        print("  %-16s %-6s %-9s %-22s %s" % ("Feld", "ruhig", "Hoehe", "Rahmenfarbe", "Pfeil/Symbol"))
        for f in mess["felder"]:
            name = f["tag"] + (":" + f["typ"] if f["typ"] else "")
            hinweis = "appearance=" + (f["appearance"] or "?")
            print("  %-16s %-6s %-9s %-22s %s"
                  % (name, "ja" if f["ruhig"] else "NEIN",
                     str(f["hoehe"]) + " px", f["rahmen"], hinweis))

        # v3.9.919: Punkt 25 - die gefuellten Flaechen der Aktionsspalte.
        print()
        print("  %-8s %-30s %-9s %-22s %s"
              % ("Knopf", "Titel", "Flaeche", "Fuellung", "Rahmen"))
        gefuellt = 0
        summe = 0
        for k in mess.get("knoepfe_detail", []):
            voll = _ist_gefuellt(k["fuellung"])
            if voll:
                gefuellt += 1
                summe += k["flaeche"]
            print("  %-8s %-30s %-9s %-22s %s"
                  % (k["text"] or "?", k["titel"][:30],
                     str(k["flaeche"]) + " px2", k["fuellung"],
                     (k["rahmen"] + " " + k["rahmenbreite"]) if k["rahmen"]
                     else "keiner"))
        print()
        print("  Gefuellte Knopfflaechen je Zeile: %d von %d  (%d px2)"
              % (gefuellt, len(mess.get("knoepfe_detail", [])), summe))
        print("  Hochgerechnet auf %d sichtbare Zeilen: %d Flaechen, %d px2"
              % (30, gefuellt * 30, summe * 30))

        klein = [f for f in mess["felder"] if f["hoehe"] < 24]
        print()
        print("  Tippziele unter 24 px (WCAG): %d von %d"
              % (len(klein), len(mess["felder"])))

        # ERSTER LAUF FOTOGRAFIERTE DIE FALSCHE STELLE. Der Schirm war voll
        # mit Kennzahl-Kacheln, die Zeile lag unterhalb - das Bild zeigte alles
        # ausser dem, worum es ging, und sah dabei voellig in Ordnung aus.
        # Deshalb wird jetzt zur Zeile GESCROLLT und vorher gemessen, wie weit
        # unten sie ueberhaupt anfaengt.
        vorbau = seite.evaluate(VORBAU_JS)
        print()
        print("VORBAU ueber der Liste")
        print("  Tabelle beginnt bei y =", vorbau["tabelle_y"], "px")
        print("  Schirmhoehe          =", vorbau["schirm"], "px")
        print("  Seitenhoehe          =", vorbau["seitenhoehe"], "px")
        print("  Anteil Vorbau        = %.0f%% der Seite"
              % (100.0 * vorbau["tabelle_y"] / max(1, vorbau["seitenhoehe"])))
        if vorbau["tabelle_y"] > vorbau["schirm"]:
            print("  🔴 Die Liste beginnt UNTERHALB des sichtbaren Bereichs -")
            print("     wer die Ansicht oeffnet, sieht keinen einzigen Schein.")

        seite.evaluate("() => { const t = document.querySelector('table');"
                       "  if (t) t.scrollIntoView({block:'start'}); }")
        seite.wait_for_timeout(600)
        seite.screenshot(path=os.path.join(ZIEL, "as_zeile_JETZT_%s.png" % thema), full_page=False)

        # Zeigen: kommt der Rahmen zurueck?
        erstes = seite.locator("select.epk-ruhig").first
        if erstes.count():
            erstes.hover()
            seite.wait_for_timeout(400)
            # KEIN Rueckfall auf das nicht gezeigte Element: der haette eine
            # Farbe geliefert, ohne dass je gezeigt wurde.
            zeig = seite.evaluate(ZEIG_JS)
            if not zeig:
                print("  Zeigen: :hover hat NICHT gegriffen - hier wird nichts behauptet.")
            else:
                print("  Rahmen beim Zeigen :", zeig["rand"],
                      "  auf Grund", zeig["grund"])
                print("  Kontrast Rahmen/Grund: %.2f:1  (ab 3,0 gilt eine" % zeig["kontrast"],
                      "Umrandung als erkennbar)")
                if zeig["kontrast"] < 3.0:
                    print("  🔴 ZU SCHWACH - der Rahmen kommt zwar zurueck,")
                    print("     aber er ist auf diesem Untergrund kaum zu sehen.")
            seite.mouse.move(5, 5)
            seite.wait_for_timeout(300)

        # v3.9.920 Punkt 25: den Vorschlag aufsetzen und NACHMESSEN.
        if umriss:
            # Tinte VORHER - ohne den Vergleichswert sagt die Zahl nachher
            # nichts. Erst das Paar ist eine Aussage.
            vor_pdf = _knopf_tinte(seite, "PDF")
            vor_qr = _knopf_tinte(seite, "QR")

            # Welches Gruen? Im hellen Thema faellt #22c55e als Haarrahmen
            # auf 2,28:1 - GEMESSEN, nicht vermutet. _okG(#22c55e) liefert
            # dort EP_GREEN_DARK und im dunklen Thema die Farbe unveraendert.
            gruen = seite.evaluate(
                "() => { const c = getComputedStyle(document.body)"
                ".backgroundColor.match(/[0-9.]+/g).slice(0,3).map(Number);"
                "  const l = 0.2126*c[0] + 0.7152*c[1] + 0.0722*c[2];"
                "  return l > 140 ? '#006e30' : '#22c55e'; }")
            n = seite.evaluate(UMRISS_JS, gruen)
            seite.wait_for_timeout(400)
            print()
            print("VORSCHLAG v3.9.920 aufgesetzt (%d Knoepfe umgestellt, "
                  "Gruen=%s)" % (n, gruen))
            nach = seite.evaluate(MESS_JS)
            neu_gef = [k for k in nach.get("knoepfe_detail", [])
                       if _ist_gefuellt(k["fuellung"])]
            print("  Gefuellte Knopfflaechen je Zeile: %d von %d  (%d px2)"
                  % (len(neu_gef), len(nach.get("knoepfe_detail", [])),
                     sum(k["flaeche"] for k in neu_gef)))
            print("  Davon Warnung (Stornieren): %d px2"
                  % sum(k["flaeche"] for k in neu_gef
                        if k["titel"].startswith("Storn")))
            print()
            print("  %-8s %-9s %-9s %-20s %s"
                  % ("Knopf", "Flaeche", "Groesse", "Rahmen", "Kontrast/Grund"))
            for u in seite.evaluate(UMRISS_MESS_JS):
                print("  %-8s %-9s %-9s %-20s %.2f:1 auf %s"
                      % (u["text"] or u["titel"][:6],
                         str(u["flaeche"]) + " px2",
                         "%sx%s" % (u["breite"], u["hoehe"]),
                         u["rahmen"], u["kontrast"], u["grund"]))
                if u["kontrast"] < 3.0:
                    print("     ROT: der Rahmen faellt unter 3,0:1 - der Knopf")
                    print("     verliert im Ruhezustand seine Umrandung.")

            # Bleibt die Beschriftung sichtbar? Der Kontrast-Rechner misst den
            # RAHMEN, nicht das Zeichen darin.
            nach_pdf = _knopf_tinte(seite, "PDF")
            nach_qr = _knopf_tinte(seite, "QR")
            print()
            print("  Tinte im Knopf (Anteil Punkte, die nicht Grund sind)")
            for name, v, w in (("PDF", vor_pdf, nach_pdf),
                               ("QR", vor_qr, nach_qr)):
                if v is None or w is None:
                    print("    %-4s nicht messbar" % name)
                    continue
                print("    %-4s vorher %.3f  nachher %.3f" % (name, v, w))
                if w < 0.05:
                    print("       ROT: im Knopf ist fast nichts mehr zu "
                          "sehen - die Beschriftung ist verschwunden.")

            # GEGENPROBE zur Ruhe: kehrt die Fuellung beim Zeigen zurueck?
            kn = seite.locator("button.epk-flach").first
            if kn.count():
                kn.hover()
                seite.wait_for_timeout(300)
                z = seite.evaluate(ZEIG_KNOPF_JS)
                if not z:
                    print("  Zeigen am Knopf: :hover hat NICHT gegriffen - "
                          "hier wird nichts behauptet.")
                else:
                    print("  Fuellung beim Zeigen (%s): %s  -> %s"
                          % (z["titel"][:18], z["fuellung"],
                             "kehrt zurueck" if _ist_gefuellt(z["fuellung"])
                             else "BLEIBT WEG"))
                    # Die Rueckkehr setzt background:currentColor - also
                    # dieselbe Farbe wie color. Ein TEXT-Zeichen waere damit
                    # unsichtbar. Die Emoji bringen eigene Farben mit; ob das
                    # wirklich so ist, wird hier gezaehlt statt behauptet.
                    t = _tinte(kn.first.screenshot())
                    print("  Tinte beim Zeigen: %.3f  -> %s" % (
                        t, "Zeichen bleibt sichtbar" if t >= 0.05
                        else "ROT: das Zeichen verschwindet in der Fuellung"))
                seite.mouse.move(5, 5)
                seite.wait_for_timeout(200)
                # UMKEHRPROBE FUER DAS MESSGERAET SELBST: ein Zaehler, der
                # nie klein wird, beweist nichts. Das Zeichen wird kuenstlich
                # unsichtbar gemacht - faellt die Zahl dann nicht, misst sie
                # nicht das Zeichen.
                seite.evaluate(
                    "() => { const b = document.querySelector("
                    "'button.epk-flach'); if (b) {"
                    "  b.style.color = getComputedStyle(b.parentElement)"
                    ".backgroundColor;"
                    "  b.style.opacity = '0'; } }")
                seite.wait_for_timeout(250)
                leer = _tinte(kn.first.screenshot())
                print("  Umkehrprobe Tinte (Zeichen verdeckt): %.3f  -> %s"
                      % (leer, "der Zaehler faellt, er misst das Zeichen"
                         if leer < 0.05 else
                         "ROT: der Zaehler faellt NICHT - er misst etwas "
                         "anderes als die Beschriftung"))
                seite.mouse.move(5, 5)
                seite.wait_for_timeout(200)
            seite.screenshot(
                path=os.path.join(ZIEL, "as_zeile_UMRISS_%s_%d.png"
                                  % (thema, breite)),
                full_page=False)

        # Und derselbe Schirm mit abgeschalteter Ruhe-Klasse.
        seite.evaluate(AUS_JS)
        seite.wait_for_timeout(400)
        seite.screenshot(path=os.path.join(ZIEL, "as_zeile_VORHER_%s.png" % thema), full_page=False)

        browser.close()

    print()
    if fehler:
        print("FEHLER auf der Seite:")
        for f in fehler[:8]:
            print("  -", f)
    else:
        print("Keine Seitenfehler.")
    print("Bilder:", ZIEL)
    return 1 if fehler else 0


if __name__ == "__main__":
    _b = 1440
    if "--breite" in sys.argv:
        _b = int(sys.argv[sys.argv.index("--breite") + 1])
    _t = "system"
    if "--thema" in sys.argv:
        _t = sys.argv[sys.argv.index("--thema") + 1]
    _s = 0
    if "--schmal" in sys.argv:
        _s = int(sys.argv[sys.argv.index("--schmal") + 1])
    sys.exit(main(_b, umriss="--umriss" in sys.argv, thema=_t, schmal=_s))
