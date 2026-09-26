# -*- coding: utf-8 -*-
"""Warum ist der Hellmodus auf dem Telefon dunkel?

NUTZERBEFUND
────────────
"ui ist in mobil auch schon geaendert, mobil hell ist auch sehr dunkel" und
"pwa geht hell und dunkel". Also: die Umschaltung funktioniert, aber auf dem
Telefon bleibt es im Hellmodus dunkel.

Das Theme-Werk selbst ist unverdaechtig: THEMES.light traegt bg #f0f2f5 und
sb #ffffff, und v3.9.711 stellt sicher, dass die App-Wahl die OS-Einstellung
immer schlaegt. Wenn es trotzdem dunkel aussieht, ueberstimmt etwas anderes -
und das findet man nicht im Quelltext, sondern am gerenderten Element.

WAS GEMESSEN WIRD
─────────────────
Dieselben Flaechen bei 390 px und bei 1440 px, beide mit epk_theme='light':
die App-Huelle, der Inhaltsbereich, die Kopfzeile, die Fussleiste, eine Karte.
Je Flaeche die BERECHNETE Hintergrundfarbe und ihre Helligkeit.

Eine Flaeche gilt als dunkel, wenn ihre relative Helligkeit unter 0,5 liegt.
Gemessen wird die tatsaechlich sichtbare Farbe: ist ein Element durchsichtig,
wird der erste nicht durchsichtige Vorfahr genommen - sonst meldet die Messung
"rgba(0,0,0,0)" und man haelt Durchsichtigkeit fuer Schwarz.

EIGENER MESSFEHLER, hier behoben (26.09.)
─────────────────────────────────────────
Die erste Fassung meldete "BEFUND BESTAETIGT: der Hellmodus ist auf beiden
Breiten dunkel" - und die EINZIGE dunkle Flaeche war `html` mit
`rgba(0, 0, 0, 0)`. Das ist keine Farbe, das ist Durchsichtigkeit: `<html>`
hat keinen Hintergrund und keinen Vorfahren, bei dem die Suche weitersuchen
koennte. Meine Helligkeitsformel liest daraus die drei Nullen und ergibt
0,000 - also "schwarz". Damit war das Urteil eine Eigenschaft des Werkzeugs,
nicht der Anwendung. Ein durchsichtiges Element ohne nicht-durchsichtigen
Vorfahren gilt jetzt als UNBESTIMMT und faellt aus der Wertung; es wird
getrennt ausgewiesen, damit das Weglassen selbst sichtbar bleibt.

Und: fuenf benannte Flaechen koennen den Befund verfehlen, wenn die dunkle
Flaeche woanders liegt. Deshalb wird zusaetzlich JEDES sichtbare Element ab
8000 px2 abgetastet und nach Flaeche sortiert ausgegeben - so ist eine
dunkle Grossflaeche zu finden, ohne sie vorher zu kennen.

DER KOEDER
──────────
Derselbe Lauf mit epk_theme='dark' MUSS dunkle Flaechen melden. Tut er das
nicht, misst das Werkzeug die Farbe nicht, und die Aussage ueber den
Hellmodus waere wertlos.

AUFRUF
──────
    python scripts/hellmodus_messen.py
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import mob_ansicht_messen as M  # noqa: E402

FLAECHEN_JS = r"""() => {
  // Die sichtbare Farbe: ein durchsichtiges Element zeigt die Farbe seines
  // ersten nicht durchsichtigen Vorfahren. Gibt es keinen - wie bei <html>,
  // das ganz oben steht -, ist die Farbe UNBESTIMMT und nicht schwarz. Genau
  // das hat meine erste Fassung verwechselt und daraus einen Befund gemacht.
  const sichtbar = (el) => {
    let e = el;
    while (e) {
      const c = getComputedStyle(e).backgroundColor;
      if (c && c !== 'rgba(0, 0, 0, 0)' && c !== 'transparent') return {el: e, c: c, unbestimmt: false};
      e = e.parentElement;
    }
    return {el: null, c: 'rgba(0, 0, 0, 0)', unbestimmt: true};
  };
  const hell = (c) => {
    const m = /rgba?\((\d+), ?(\d+), ?(\d+)(?:, ?([\d.]+))?/.exec(c || '');
    if (!m) return null;
    // Eine Farbe mit Alpha 0 ist keine Farbe. Ohne diese Zeile ergibt
    // rgba(0,0,0,0) die Helligkeit 0,000 und sieht wie Schwarz aus.
    if (m[4] !== undefined && parseFloat(m[4]) === 0) return null;
    const f = [1, 2, 3].map(i => {
      const v = parseInt(m[i], 10) / 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2];
  };
  const ziele = [
    ['app-shell', document.querySelector('.app-shell')],
    ['main-pad', document.querySelector('.main-pad')],
    ['bottom-nav', document.querySelector('.bottom-nav')],
    ['body', document.body],
    ['html', document.documentElement]
  ];
  const aus = [];
  ziele.forEach(([name, el]) => {
    if (!el) { aus.push({name: name, fehlt: true}); return; }
    const s = sichtbar(el);
    aus.push({name: name, farbe: s.c, helligkeit: hell(s.c),
              unbestimmt: s.unbestimmt,
              eigen: getComputedStyle(el).backgroundColor,
              von: s.el === el ? 'selbst' : (s.el ? s.el.className || s.el.tagName : '-')});
  });
  // FLAECHENSUCHE. Fuenf benannte Stellen koennen den Befund verfehlen, wenn
  // die dunkle Flaeche woanders liegt. Also jedes sichtbare Element ab
  // 8000 px2 abtasten, das seine Farbe SELBST setzt (sonst zaehlt man
  // denselben Hintergrund durch jede Verschachtelung mit).
  // Eine halbdurchsichtige Farbe ist nicht die Farbe, die man sieht. Beim
  // ersten Lauf meldete diese Suche neun dunkle Grossflaechen im Hellmodus -
  // acht davon waren Toenungen mit rgba(..., 0.067), also 6,7 Prozent Deckung
  // ueber Weiss. Sichtbar sind sie nahezu weiss; meine Formel las nur die drei
  // Kanaele und ergab 0,23 bis 0,50. Derselbe Messfehler wie bei <html>, eine
  // Ebene tiefer. Jetzt wird gegen den Untergrund GEMISCHT und die gemischte
  // Farbe bewertet.
  const kanaele = (c) => {
    const m = /rgba?\((\d+), ?(\d+), ?(\d+)(?:, ?([\d.]+))?/.exec(c || '');
    if (!m) return null;
    return {r: +m[1], g: +m[2], b: +m[3],
            a: m[4] === undefined ? 1 : parseFloat(m[4])};
  };
  const untergrund = (el) => {
    let e = el.parentElement;
    while (e) {
      const k = kanaele(getComputedStyle(e).backgroundColor);
      if (k && k.a >= 0.999) return k;
      e = e.parentElement;
    }
    return {r: 255, g: 255, b: 255, a: 1};  // Standard-Leinwand des Browsers
  };
  const gemischt = (el, c) => {
    const k = kanaele(c);
    if (!k) return null;
    if (k.a >= 0.999) return c;
    const u = untergrund(el);
    const f = (x, y) => Math.round(k.a * x + (1 - k.a) * y);
    return 'rgb(' + f(k.r, u.r) + ', ' + f(k.g, u.g) + ', ' + f(k.b, u.b) + ')';
  };
  const gross = [];
  document.querySelectorAll('*').forEach(el => {
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none') return;
    if (parseFloat(cs.opacity || '1') < 0.1) return;
    const roh = cs.backgroundColor;
    if (!roh || roh === 'rgba(0, 0, 0, 0)' || roh === 'transparent') return;
    const c = gemischt(el, roh);
    const h = hell(c);
    if (h === null || h >= 0.5) return;
    const r = el.getBoundingClientRect();
    const fl = Math.round(r.width * r.height);
    if (fl < 8000) return;
    // Der ANTEIL am Schirm, nicht die Farbe, trennt eine tragende Flaeche von
    // einem Akzent. Im ersten Lauf blieben nach der Mischung zwei Treffer
    // uebrig: zwei Warnbaender in Amber und Orange, die es nur gibt, weil
    // dieser Aufbau jede Anfrage abbricht. Sie sind 6 Prozent des Schirms.
    // Die dunkle Huelle im Dunkelmodus ist 100 Prozent. Nach FARBE zu
    // filtern waere Blindheit auf Bestellung; nach Anteil zu urteilen ist
    // eine Aussage. Gelistet wird weiterhin ALLES ab 8000 px2.
    gross.push({tag: el.tagName.toLowerCase(),
                klasse: String(el.className || '').slice(0, 60),
                farbe: c, roh: roh, helligkeit: h, flaeche: fl,
                anteil: fl / Math.max(1, innerWidth * innerHeight),
                text: String(el.innerText || '').replace(/\s+/g, ' ').slice(0, 70),
                oben: Math.round(r.top), breit: Math.round(r.width)});
  });
  gross.sort((a, b) => b.flaeche - a.flaeche);
  return {flaechen: aus, dunkelGross: gross.slice(0, 12),
          dunkelGrossAnzahl: gross.length,
          tragend: gross.filter(g => g.anteil >= 0.25)
                        .map(g => (g.tag + '.' + g.klasse).slice(0, 40)),
          elemente: document.querySelectorAll('*').length,
          colorScheme: getComputedStyle(document.documentElement).colorScheme,
          htmlKlasse: document.documentElement.className,
          textfarbe: getComputedStyle(document.body).color};
}"""


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt.")
        return 2

    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port, os.environ.get("EPK_INDEX", "index.html"))
    print("Gemessen wird:", url)

    ergebnis = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for thema in ("light", "dark"):
            for breite in (390, 1440):
                ctx = browser.new_context(
                    viewport={"width": breite, "height": 880},
                    is_mobile=breite < 600, has_touch=breite < 600,
                    # Das OS bewusst auf DUNKEL stellen: die App-Wahl muss
                    # trotzdem gewinnen (v3.9.711). Nur so ist der Fall
                    # ueberhaupt gemessen, um den es geht.
                    color_scheme="dark")
                ctx.add_init_script(M.INIT)
                ctx.add_init_script(
                    "try{localStorage.setItem('epk_theme','%s');"
                    "var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
                    "u.role='admin';u.monteurId='M1';"
                    "localStorage.setItem('epkolar_user',JSON.stringify(u));}catch(e){}"
                    % thema)
                ctx.route("**/rest/v1/**", lambda r: r.abort())
                ctx.route("**/auth/v1/**", lambda r: r.abort())
                seite = ctx.new_page()
                seite.goto(url, wait_until="domcontentloaded")
                seite.wait_for_timeout(4000)
                d = seite.evaluate(FLAECHEN_JS)
                ctx.close()
                ergebnis[(thema, breite)] = d

                print("\n-- epk_theme=%s, %d px  (OS steht auf dunkel)" % (thema, breite))
                print("   color-scheme am <html>: %r | Klasse: %r"
                      % (d["colorScheme"], d["htmlKlasse"]))
                print("   Textfarbe body: %s" % d["textfarbe"])
                for f in d["flaechen"]:
                    if f.get("fehlt"):
                        print("   %-12s NICHT VORHANDEN" % f["name"])
                        continue
                    if f.get("unbestimmt"):
                        print("   %-12s %-22s UNBESTIMMT - durchsichtig und ohne"
                              " nicht-durchsichtigen Vorfahren, faellt aus der"
                              " Wertung" % (f["name"], f["farbe"]))
                        continue
                    h = f["helligkeit"]
                    print("   %-12s %-22s Helligkeit %s  (eigen %s, von %s)"
                          % (f["name"], f["farbe"],
                             ("%.3f" % h) if h is not None else "?",
                             f["eigen"], f["von"]))
                print("   %d Elemente im Baum, dunkel und ueber 8000 px2: %d"
                      % (d["elemente"], d["dunkelGrossAnzahl"]))
                for g in d["dunkelGross"]:
                    _r = ("" if g["roh"] == g["farbe"]
                          else "  [roh %s]" % g["roh"])
                    print("      %7d px2  %-20s Helligkeit %.3f  %s.%s"
                          "  (y=%d, b=%d)%s"
                          % (g["flaeche"], g["farbe"], g["helligkeit"],
                             g["tag"], g["klasse"], g["oben"], g["breit"], _r))
                    if g["text"]:
                        print("                 Text: %s" % g["text"])
                if d["tragend"]:
                    print("   TRAGENDE dunkle Flaechen (ab 25%% des Schirms): %s"
                          % ", ".join(d["tragend"]))
        browser.close()

    # ── Urteil ────────────────────────────────────────────────────────────
    print("\n" + "=" * 68)

    def dunkle(thema, breite):
        """Nur MESSBAR dunkle Flaechen. Ein durchsichtiges Element ohne
        nicht-durchsichtigen Vorfahren hat keine Farbe - es als dunkel zu
        zaehlen war der Messfehler der ersten Fassung, siehe Dateikopf."""
        d = ergebnis[(thema, breite)]
        return [f["name"] for f in d["flaechen"]
                if not f.get("fehlt") and not f.get("unbestimmt")
                and f["helligkeit"] is not None
                and f["helligkeit"] < 0.5]

    def grossflaechig(thema, breite):
        return ergebnis[(thema, breite)]["dunkelGrossAnzahl"]

    def tragend(thema, breite):
        """Dunkle Flaechen ab einem Viertel des Schirms. Ein Warnband in
        Amber ist 6 Prozent und keine Themenflaeche; die Huelle im
        Dunkelmodus ist 100 Prozent."""
        return ergebnis[(thema, breite)]["tragend"]

    koeder = dunkle("dark", 390)
    print("KOEDER - im Dunkelmodus dunkle Flaechen bei 390 px: %s" % (koeder or "KEINE"))
    if not koeder:
        print("   Das Werkzeug erkennt keine dunkle Flaeche. Dann sagt es ueber")
        print("   den Hellmodus nichts. ABBRUCH.")
        return 1

    hell_mob = dunkle("light", 390)
    hell_desk = dunkle("light", 1440)
    print("Im HELLMODUS dunkle Flaechen bei  390 px: %s" % (hell_mob or "keine"))
    print("Im HELLMODUS dunkle Flaechen bei 1440 px: %s" % (hell_desk or "keine"))

    if hell_mob and not hell_desk:
        print("\nBEFUND BESTAETIGT und EINGEGRENZT: der Hellmodus ist NUR auf")
        print("dem schmalen Schirm dunkel. Damit liegt es an einer")
        print("breitenabhaengigen Regel, nicht am Thema selbst.")
        return 1
    if hell_mob and hell_desk:
        print("\nBEFUND BESTAETIGT, ABER NICHT breitenabhaengig: der Hellmodus")
        print("ist auf BEIDEN Breiten dunkel. Dann liegt es nicht an einer")
        print("Mobilregel, sondern daran, dass das Thema nicht greift.")
        return 1
    print("\nIm Hellmodus ist keine der fuenf benannten Flaechen dunkel.")
    print("Die Flaechensuche (jedes sichtbare Element ab 8000 px2) fand dunkle")
    print("Elemente:")
    print("   Hellmodus    390 px: %d | 1440 px: %d"
          % (grossflaechig("light", 390), grossflaechig("light", 1440)))
    print("   Dunkelmodus  390 px: %d | 1440 px: %d   (Koeder)"
          % (grossflaechig("dark", 390), grossflaechig("dark", 1440)))
    print("   davon TRAGEND (ab 25% des Schirms):")
    print("      Hellmodus    390 px: %s | 1440 px: %s"
          % (tragend("light", 390) or "keine", tragend("light", 1440) or "keine"))
    print("      Dunkelmodus  390 px: %s   (Koeder)"
          % (tragend("dark", 390) or "KEINE"))
    if not tragend("dark", 390):
        print("\nDer Koeder findet im Dunkelmodus keine tragende dunkle Flaeche.")
        print("Dann sagt dieses Mass ueber den Hellmodus nichts. ABBRUCH.")
        return 1
    if tragend("light", 390) or tragend("light", 1440):
        print("\nIm Hellmodus ist eine TRAGENDE Flaeche dunkel. Die Liste oben")
        print("nennt sie mit Klasse und Lage - dort weitermessen.")
        return 1
    print("\nIm Hellmodus ist keine TRAGENDE Flaeche dunkel, waehrend im")
    print("Dunkelmodus fuenf es sind. Die zwei bzw. eine dunkle Kleinflaeche")
    print("oben sind die Warnbaender, die es nur gibt, weil dieser Aufbau jede")
    print("Anfrage abbricht - Akzentfarben, keine Themenflaechen (Text steht")
    print("dabei). Der Nutzerbefund ist mit DIESEM Aufbau nicht nachstellbar.")
    print("WAS DER AUFBAU NICHT ABDECKT, damit niemand mehr hineinliest:")
    print("  * ein echtes Geraet (hier laeuft Chromium ohne Geraeteprofil)")
    print("  * ein gespeicherter Dienstarbeiter mit einer aelteren Fassung")
    print("  * jede Ansicht ausser der beim Start gezeigten")
    return 0


if __name__ == "__main__":
    sys.exit(main())
