# -*- coding: utf-8 -*-
"""C1 und C2: die Reiterzeilen nach dem Umbruch, und die Ueberschrift-Kandidaten.

C1 - IST UMBRECHEN DIE RICHTIGE LOESUNG?
────────────────────────────────────────
Admin und Material brechen seit v3.9.948 um statt zu rollen. Gemessen ist
seither "kein waagrechter Roller" - aber das sagt nicht, ob die Zeile dadurch
gut aussieht. Die Frage dahinter: traegt die Zeile schlicht zu viele
Eintraege? Gemessen wird deshalb, in WIE VIELEN ZEILEN sie jetzt steht und wie
hoch sie geworden ist. Zwei Zeilen sind ein Preis, fuenf sind ein Befund.

C2 - DIE UEBERSCHRIFT-KANDIDATEN
────────────────────────────────
Drei Ansichten fuehren keine h1/h2/h3. Im Bild steht dort eine Ueberschrift,
sie sitzt nur in einem div. WELCHES Element die Seitenueberschrift sein soll,
ist eine Gestaltungsfrage - diese Sonde RAET NICHT, sie listet die Kandidaten
mit ihren Messwerten: Text, Schriftgroesse, Gewicht, Lage von oben, Breite.
Sebastian entscheidet in drei Zeilen.

Kandidat ist, was im oberen Drittel steht, fett ist (>= 600) und keine reine
Zahl trägt.

AUFRUF
──────
    python scripts/c_reste_messen.py
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import mob_ansicht_messen as M  # noqa: E402
import b3_stufen_12_15_messen as B  # noqa: E402

REITER_JS = """(auswahl) => {
  // Die Reiterzeile: ein flex-Behaelter mit mehreren Knoepfen darin.
  const aus = [];
  document.querySelectorAll('div').forEach(el => {
    const cs = getComputedStyle(el);
    if (cs.display !== 'flex') return;
    const knoepfe = [...el.children].filter(c => c.tagName === 'BUTTON');
    if (knoepfe.length < 4) return;
    const r = el.getBoundingClientRect();
    if (r.width <= 0) return;
    // In wie vielen Zeilen stehen die Knoepfe? Ueber ihre Oberkanten zaehlen.
    const kanten = [...new Set(knoepfe.map(k =>
      Math.round(k.getBoundingClientRect().top)))];
    aus.push({knoepfe: knoepfe.length, zeilen: kanten.length,
              hoehe: Math.round(r.height), breit: Math.round(r.width),
              wrap: cs.flexWrap, ox: cs.overflowX,
              scrollW: el.scrollWidth, clientW: el.clientWidth,
              texte: knoepfe.map(k => (k.innerText || '').trim().slice(0, 18))});
  });
  return aus;
}"""

UEBER_JS = """() => {
  const H = innerHeight;
  const aus = [];
  document.querySelectorAll('div, span, h1, h2, h3').forEach(el => {
    if (el.children.length > 0 && el.tagName !== 'H1'
        && el.tagName !== 'H2' && el.tagName !== 'H3') return;
    const t = (el.textContent || '').replace(/\\s+/g, ' ').trim();
    if (!t || t.length < 3 || t.length > 48) return;
    if (/^[\\d.,:%\\s\\u20ac-]+$/.test(t)) return;   // reine Zahl
    const cs = getComputedStyle(el);
    const gew = parseInt(cs.fontWeight, 10) || 400;
    const gr = parseFloat(cs.fontSize) || 0;
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return;
    if (r.top > H * 0.45) return;                   // nur oben
    if (gew < 600 && gr < 16) return;
    aus.push({tag: el.tagName.toLowerCase(), text: t,
              gr: Math.round(gr * 10) / 10, gew: gew,
              oben: Math.round(r.top), breit: Math.round(r.width)});
  });
  aus.sort((a, b) => a.oben - b.oben || b.gr - a.gr);
  return aus.slice(0, 8);
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

    ZIELE = [("admin", "C1"), ("material", "C1"),
             ("zeit", "C2"), ("flotte", "C2"), ("baupro", "C2")]
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for name, teil in ZIELE:
            for breite in (390, 1440):
                ctx = browser.new_context(
                    viewport={"width": breite, "height": 880},
                    is_mobile=breite < 600, has_touch=breite < 600,
                    color_scheme="dark")
                ctx.add_init_script(M.INIT)
                ctx.add_init_script(
                    "try{var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
                    "u.monteurId='M1';u.role='admin';"
                    "localStorage.setItem('epkolar_user',JSON.stringify(u));}catch(e){}")
                ctx.route("**/rest/v1/**", lambda r: r.abort())
                ctx.route("**/auth/v1/**", lambda r: r.abort())
                seite = ctx.new_page()
                seite.goto(url, wait_until="domcontentloaded")
                seite.wait_for_timeout(3800)
                try:
                    B._saeen12(seite)
                    seite.wait_for_timeout(1200)
                except Exception as e:
                    print("   (Saat fehlgeschlagen: %s)" % str(e)[:80])
                erreicht = B._navigiere(seite, name) if hasattr(B, "_navigiere") else None
                if erreicht is None:
                    # Ueber den sichtbaren Text navigieren, Fussleiste ausgenommen
                    erreicht = seite.evaluate(
                        """(n)=>{const k=[...document.querySelectorAll(
                             'button,a,[role="button"]')]
                             .filter(b=>!b.closest('.bottom-nav'));
                           const t=k.find(b=>(b.innerText||'').toLowerCase()
                             .includes(n));
                           if(t){t.click();return true;} return false;}""",
                        {"admin": "admin", "material": "material",
                         "zeit": "zeiterfassung", "flotte": "flotte",
                         "baupro": "bauprovisorien"}[name])
                seite.wait_for_timeout(1800)

                print("\n── %s [%s] @ %d px  (erreicht: %s)"
                      % (name, teil, breite, erreicht))
                if teil == "C1":
                    for z in seite.evaluate(REITER_JS, name):
                        print("   %d Knoepfe in %d Zeile(n), %d px hoch, "
                              "wrap=%s ox=%s, scroll %d/%d"
                              % (z["knoepfe"], z["zeilen"], z["hoehe"],
                                 z["wrap"], z["ox"], z["scrollW"], z["clientW"]))
                        print("      %s" % z["texte"])
                else:
                    for k in seite.evaluate(UEBER_JS):
                        print("   %-5s %-42s %5.1f px  Gewicht %d  y=%d  b=%d"
                              % (k["tag"], k["text"][:42], k["gr"], k["gew"],
                                 k["oben"], k["breit"]))
                ctx.close()
        browser.close()
    print("\nGemessen, nicht geraten - und bei C2 ausdruecklich NICHT gebaut.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
