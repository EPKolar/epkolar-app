# -*- coding: utf-8 -*-
"""Dieselben Melder, aber INNERHALB einer geoeffneten Ueberlagerung.

🔴 Jeder Grundstand endet mit „keine geoeffneten Dialoge". Das war ehrlich und
es war eine Luecke. Dieses Werkzeug schliesst sie fuer die Ueberlagerungen, die
sich von aussen oeffnen lassen.

DIE ERKUNDUNG VORHER (scripts/dialoge_erkunden.py) hat gezeigt: die App
benutzt ueberwiegend INLINE-Bereiche, keine Modalen. Als echte Ueberlagerung
mit `position: fixed` und mehr als einem Drittel Schirmflaeche fanden sich
genau vier, und alle vier gehoeren zur HUELLE, nicht zu einer Ansicht:
Sync-Fenster, Kamera, Suchpalette (Strg-K) und Benachrichtigungen.

🔴 DIE SELBSTPROBE IST HIER WICHTIGER ALS SONST: wenn die Ueberlagerung gar
nicht aufgeht, misst der Melder die Ansicht dahinter und meldet deren (gute)
Zahlen als Dialog-Ergebnis. Deshalb wird VOR jeder Messung belegt, dass sich
die Zahl der Ueberlagerungen erhoeht hat - und die Messung bricht ab, wenn
nicht.
"""
import io
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
WURZEL = os.path.dirname(HIER)

import mob_ansicht_messen as M           # noqa: E402
import b3_stufen_12_15_messen as B12     # noqa: E402
import echtmengen_saat as SAAT           # noqa: E402
import echtmengen_messen as EM           # noqa: E402

OVERLAYS_JS = r"""() => {
  let n = 0;
  for (const e of document.querySelectorAll('div,section,dialog')) {
    const s = getComputedStyle(e);
    if (s.position !== 'fixed') continue;
    const r = e.getBoundingClientRect();
    if (r.width * r.height < window.innerWidth * window.innerHeight / 3) continue;
    if (s.display === 'none' || s.visibility === 'hidden') continue;
    n++;
  }
  return n;
}"""

# Gemessen wird NUR innerhalb der obersten Ueberlagerung - sonst zaehlt die
# Ansicht dahinter mit, und das Ergebnis waere wertlos.
MESSEN_JS = r"""() => {
  // 🔴 NICHT das GROESSTE feste Element nehmen. Das ist der HINTERGRUND, und
  // der hat keine Kinder mit Text - die Messung meldete dann "0 Elemente",
  // was wie ein makelloses Ergebnis aussieht und keines ist. Gewaehlt wird
  // das feste Element mit den MEISTEN texttragenden Nachfahren.
  let top = null, beste = -1;
  for (const e of document.querySelectorAll('div,section,dialog')) {
    const s = getComputedStyle(e);
    if (s.position !== 'fixed') continue;
    const r = e.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    if (s.display === 'none' || s.visibility === 'hidden') continue;
    let n = 0;
    for (const k of e.querySelectorAll('*')) {
      if (k.children.length === 0 && (k.innerText || '').trim()) n++;
    }
    if (n > beste) { beste = n; top = e; }
  }
  if (!top || beste <= 0) return {leer: true, textkinder: beste};
  const klein = [], tipp = [];
  for (const e of top.querySelectorAll('*')) {
    const t = (e.innerText || '').trim();
    if (e.children.length === 0 && t) {
      const px = parseFloat(getComputedStyle(e).fontSize);
      if (px < 12) klein.push({px: px, text: t.slice(0, 24),
                               tag: e.tagName.toLowerCase()});
    }
    if (e.matches('button,[role="button"],a[href],input,select')) {
      const r = e.getBoundingClientRect();
      if (r.width && r.height && Math.min(r.width, r.height) < 24) {
        tipp.push({w: Math.round(r.width), h: Math.round(r.height),
                   tag: e.tagName.toLowerCase(),
                   text: (e.innerText || '').trim().slice(0, 20)});
      }
    }
  }
  const namenlos = [...top.querySelectorAll('button,[role="button"]')]
      .filter(e => {
        const r = e.getBoundingClientRect();
        if (!r.width || !r.height) return false;
        return !((e.innerText || '').trim() || e.getAttribute('aria-label')
                 || e.getAttribute('title'));
      }).length;
  return {elemente: top.querySelectorAll('*').length,
          unter12: klein.length, unter12_bsp: klein.slice(0, 6),
          unter24: tipp.length, unter24_bsp: tipp.slice(0, 6),
          knoepfe_ohne_namen: namenlos};
}"""


def main(argv):
    from playwright.sync_api import sync_playwright
    breite = int(argv[0]) if argv else 1440
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port,
                                      os.environ.get("EPK_INDEX", "index.html"))
    saat = SAAT.saat()
    aus = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = EM._ctx(browser, breite)
        seite = ctx.new_page()
        try:
            seite.goto(url, wait_until="domcontentloaded")
            seite.wait_for_timeout(3800)
            EM._saeen(seite, saat, still=True)
            B12._navigieren12(seite, "fahrzeuge", breite, [])
            seite.wait_for_timeout(1600)

            ruhe = seite.evaluate(OVERLAYS_JS)
            print("Ueberlagerungen im Ruhezustand: %d" % ruhe)

            for name, muster in (("Suchpalette", "⌘K"),
                                 ("Benachrichtigungen", "\U0001F514"),
                                 ("Sync-Fenster", "ausstehend"),
                                 ("Foto-Warteschlange", "📷")):
                seite.evaluate(
                    "(m)=>{const b=[...document.querySelectorAll('button')]"
                    ".find(e=>((e.innerText||'')+(e.getAttribute('title')||''))"
                    ".includes(m)); if(b) b.click();}", muster)
                seite.wait_for_timeout(900)
                jetzt = seite.evaluate(OVERLAYS_JS)
                if jetzt <= ruhe:
                    print("  \U0001F534 %-20s ging NICHT auf (%d Ueberlagerungen"
                          " wie vorher) - NICHT gemessen." % (name, jetzt))
                    aus.append({"dialog": name, "offen": False})
                    continue
                e = seite.evaluate(MESSEN_JS)
                if e.get("leer"):
                    print("  \U0001F534 %-20s ging auf, aber die Auswahl "
                          "findet KEIN Element mit Text.\n"
                          "        Das ist kein Ergebnis, das ist ein "
                          "misslungener Griff - NICHT gemessen." % name)
                    e = {"dialog": name, "offen": True, "messbar": False}
                    aus.append(e)
                    seite.keyboard.press("Escape"); seite.wait_for_timeout(600)
                    continue
                e.update({"dialog": name, "offen": True, "messbar": True,
                          "breite": breite})
                aus.append(e)
                print("  \U0001F7E2 %-20s %4d Elemente | unter 12 px: %2d | "
                      "unter 24 px: %2d | Knoepfe ohne Namen: %d"
                      % (name, e["elemente"], e["unter12"], e["unter24"],
                         e["knoepfe_ohne_namen"]))
                for b in e["unter12_bsp"][:3]:
                    print("        %spx %s %r" % (b["px"], b["tag"], b["text"]))
                for b in e["unter24_bsp"][:3]:
                    print("        %dx%d %s %r"
                          % (b["w"], b["h"], b["tag"], b["text"]))
                seite.keyboard.press("Escape")
                seite.wait_for_timeout(600)
                if seite.evaluate(OVERLAYS_JS) > ruhe:
                    B12._navigieren12(seite, "fahrzeuge", breite, [])
                    seite.wait_for_timeout(1200)
        finally:
            ctx.close()
            browser.close()

    ziel = os.path.join(WURZEL, "docs", "befunde", "DIALOG_MESSUNG.json")
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps({"breite": breite, "dialoge": aus},
                   ensure_ascii=False, indent=1))
    print("\ngeschrieben:", ziel)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
