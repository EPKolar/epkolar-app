# -*- coding: utf-8 -*-
"""Steht unter einem Ausgetretenen in der Abwesenheits-Pille noch ein Anspruch?

DER BEFUND (B3_STUFEN_12_15.md, E2)
───────────────────────────────────
Die Pillenreihe in `AbsView` fuehrt alle Namen, und unter jedem stand
`193h Rest · 0K` - auch unter den beiden AUSGETRETENEN. Der NAME gehoert
dorthin: die Pille ist die Auswahl, ueber die man Kalender und Krankenstaende
einer Person ansieht, und v3.9.931 haelt ausdruecklich fest, dass diese Liste
vollstaendig bleiben muss. Der ANSPRUCH gehoert nicht dorthin, und das sagt
derselbe Kommentar mit denselben Worten: "Ein Anspruch fuer jemanden, der
nicht mehr da ist, ist keine Historie."

WAS HIER GEMESSEN WIRD
──────────────────────
Der TEXT jeder Pille, je Person, bei 390 und 1440 px. Fuer jede wird gesagt,
ob sie einen Anspruch nennt ("Rest" bzw. "h · ") und ob sie den Krankenstand
nennt ("K") - der bleibt, denn der ist Historie und keine Zusage.

Geprueft wird DREIFACH, weil ein einzelner Blick zu wenig ist:
  * der Ausgetretene darf keinen Anspruch tragen
  * er MUSS weiter in der Liste stehen (sonst ist die Auswahl kaputt, und
    genau das verbietet v3.9.931)
  * ein AKTIVER muss seinen Anspruch behalten - sonst hat der Filter zu viel
    genommen und niemand haette es gemerkt

DER KOEDER
──────────
Der dritte Punkt IST der Koeder: findet die Messung bei keinem Aktiven ein
"Rest", dann liest sie die Pillen gar nicht, und ihre Aussage ueber die
Ausgetretenen waere wertlos.

WAS SIE NICHT MISST
───────────────────
Ob die Zahl richtig gerechnet ist. Nur, wo sie steht und wo nicht.

AUFRUF
──────
    python scripts/abs_pille_messen.py
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import mob_ansicht_messen as M  # noqa: E402
import b3_stufen_12_15_messen as B  # noqa: E402

# Gesaet wird mit DERSELBEN Saat wie in b3_stufen_12_15_messen: fuenf
# Monteure, davon M4 ausgetreten MIT Beitrag und M5 ausgetreten OHNE.
# Mein erster Lauf nahm die Standardsaat - darin ist NIEMAND ausgetreten,
# und die Sonde meldete folgerichtig 'kein Ausgetretener in der Liste'.
# Das war keine Aussage ueber die App, sondern eine leere
# Grundgesamtheit: der Fall war gar nicht da.

ZIEL_JS = """(namen) => {
  const k = [...document.querySelectorAll('button, a, [role="button"]')]
    .filter(b => !b.closest('.bottom-nav'));
  for (const n of namen) {
    const t = k.find(b => (b.innerText || '').trim() === n
                          || (b.getAttribute('aria-label') || '') === n);
    if (t) { t.click(); return n; }
  }
  return null;
}"""

PILLEN_JS = """() => {
  // Die Pille ist ein button, dessen erster Textknoten ein Name ist und der
  // darunter eine eigene Zeile fuehrt. Gesucht wird ueber den Namen, den die
  // Saat setzt - nicht ueber eine Klasse, die es nicht gibt.
  const aus = [];
  document.querySelectorAll('button').forEach(b => {
    const t = (b.innerText || '').replace(/\\s+/g, ' ').trim();
    if (!t || t.length > 60) return;
    if (!/\\d+\\s*K$|ausgetreten/.test(t)) return;
    const r = b.getBoundingClientRect();
    if (r.width <= 0) return;
    aus.push({text: t, breit: Math.round(r.width), hoch: Math.round(r.height)});
  });
  return aus;
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
        for breite in (390, 1440):
            ctx = browser.new_context(viewport={"width": breite, "height": 880},
                                      is_mobile=breite < 600,
                                      has_touch=breite < 600)
            ctx.add_init_script(M.INIT)
            ctx.add_init_script(
                "try{var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
                "u.role='admin';u.monteurId='M1';"
                "localStorage.setItem('epkolar_user',JSON.stringify(u));}catch(e){}")
            ctx.route("**/rest/v1/**", lambda r: r.abort())
            ctx.route("**/auth/v1/**", lambda r: r.abort())
            seite = ctx.new_page()
            seite.goto(url, wait_until="domcontentloaded")
            seite.wait_for_timeout(3800)
            B._saeen12(seite)
            seite.wait_for_timeout(1200)
            gewaehlt = seite.evaluate(ZIEL_JS, ["Abwesenheiten", "Abwesenheit"])
            seite.wait_for_timeout(2000)
            pillen = seite.evaluate(PILLEN_JS)
            ctx.close()
            ergebnis[breite] = pillen
            print("\n-- %d px  (Ansicht: %s)" % (breite, gewaehlt or "NICHT ERREICHT"))
            for p in pillen:
                anspruch = ("Rest" in p["text"]) or ("h · " in p["text"])
                print("   %-46s Anspruch: %-5s  %dx%d"
                      % (p["text"][:46], anspruch, p["breit"], p["hoch"]))
        browser.close()

    print("\n" + "=" * 68)
    alle = [p for b in ergebnis for p in ergebnis[b]]
    if not alle:
        print("KEINE PILLE GEFUNDEN. Dann misst diese Sonde nichts und sagt")
        print("ueber den Befund gar nichts. ABBRUCH.")
        return 1

    mit_anspruch = [p for p in alle
                    if ("Rest" in p["text"]) or ("h · " in p["text"])]
    ausgetreten = [p for p in alle if "ausgetreten" in p["text"]]

    print("KOEDER - Pillen MIT Anspruch (das sind die Aktiven): %d"
          % len(mit_anspruch))
    if not mit_anspruch:
        print("   Keine einzige Pille nennt einen Anspruch. Entweder hat der")
        print("   Filter zu viel genommen, oder die Messung liest die Pillen")
        print("   nicht. In beiden Faellen ist das Ergebnis unten wertlos.")
        print("   ABBRUCH.")
        return 1

    print("Pillen mit 'ausgetreten': %d" % len(ausgetreten))
    if not ausgetreten:
        print("\nKein Ausgetretener in der Liste. Entweder fuehrt die Saat")
        print("keinen, oder - schlimmer - die Auswahl hat ihn VERLOREN. Das")
        print("waere genau der Fehler, den v3.9.931 verbietet: wer die alten")
        print("Krankenstaende eines Ausgetretenen sucht, muss ihn hier finden.")
        return 1

    schlecht = [p["text"] for p in ausgetreten
                if ("Rest" in p["text"]) or ("h · " in p["text"])]
    if schlecht:
        print("\nBEFUND: diese Pillen nennen einen Ausgetretenen UND einen")
        print("Anspruch: %s" % schlecht)
        return 1
    print("\nKein Ausgetretener traegt mehr einen Anspruch, die Aktiven tragen")
    print("ihn weiter, und beide stehen in der Liste. Der Krankenstand bleibt")
    print("ueberall - er ist Historie und keine Zusage.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
