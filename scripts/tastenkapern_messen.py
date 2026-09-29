# -*- coding: utf-8 -*-
"""Kapert ein Container-Tastenbehandler den Klick eines inneren Knopfes?

🔴 DER FEHLER, DEN DAS MISST, WAR MEINER. v3.9.975 hat Containern
`role="button"`, `tabIndex:0` und einen Tastenbehandler mit
`preventDefault()` gegeben. Ein echter `<button>` im Teilbaum erzeugt seinen
Klick aus der VORGABEHANDLUNG des keydown - der steigt zum Container auf,
`preventDefault()` faellt, und der Klick des inneren Knopfes fällt aus,
waehrend die Container-Aktion laeuft.

Betroffen war unter anderem "✅ Abnahme bestaetigen — Mangel ist behoben":
ein Geschaeftsvorgang, per Tastatur nicht ausloesbar. Und in der
Arbeitsschein-Karte loeste Enter auf "Storno" das BEARBEITEN aus - eine
falsche Aktion ist schlimmer als keine.

🔴 WARUM KEIN QUELLTEXTRIEGEL DAS FINDEN KANN. Alle Attribute stehen da:
`role`, `tabIndex`, `onKeyDown`, und der Behandler ruft den richtigen
Ausdruck auf. Drei Riegel zum Tastaturzugang waren die ganze Zeit gruen. Der
Mangel entsteht erst aus dem ZUSAMMENSPIEL zweier Elemente im Baum - das
sieht nur der Browser.

WAS GEMESSEN WIRD
Fuer jeden gefundenen Container mit interaktivem Nachfahren: Fokus auf den
INNEREN Knopf, Enter druecken, und pruefen, WESSEN Behandler gelaufen ist.
Dazu wird vor dem Tastendruck ein Lauscher gesetzt, der nur mitschreibt.

🔴 SELBSTPROBE: derselbe Lauf muss an einem Container OHNE inneren Knopf
melden, dass der Container reagiert - sonst misst der Melder gar nichts.
"""
import io
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
WURZEL = os.path.dirname(HIER)

import mob_ansicht_messen as M           # noqa: E402
import hellmodus_ansichten as HA         # noqa: E402
from tab_sweep import INIT               # noqa: E402

NUTZER = ("try{var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
          "u.role='admin';u.monteurId='M1';u.name='Gerhard Steinbichler';"
          "u.rolle='Geschaeftsfuehrer';"
          "localStorage.setItem('epkolar_user',JSON.stringify(u));"
          "localStorage.setItem('epk_theme','dark');}catch(e){}")

# Alle Container mit interaktiver Rolle, die einen echten Knopf enthalten.
SUCHE_JS = r"""() => {
  const innen = 'button,a[href],input,select,textarea,summary,[role="button"]';
  const aus = [];
  // 🔴 Container OHNE inneres Bedienelement werden GESAMMELT, nicht
  //    weggeworfen. Sie sind die Selbstprobe: an ihnen MUSS der Container
  //    selbst reagieren. Tut er das nicht, misst der ganze Melder nichts,
  //    und seine gruenen Ergebnisse an den anderen belegen nichts.
  //    (Bis 29.09.2026 stand diese Probe nur im Kopftext dieser Datei und
  //     war nie gebaut - gefunden von scripts/werkzeug_eichung.py.)
  const allein = [];
  document.querySelectorAll('[role="button"],[role="checkbox"],'
                            + '[role="menuitem"]').forEach((c, i) => {
    const r = c.getBoundingClientRect();
    if (!r.width || !r.height) return;
    const k = [...c.querySelectorAll(innen)].filter(x => {
      const q = x.getBoundingClientRect();
      return q.width && q.height;
    });
    if (!k.length) {
      if (allein.length < 3 && (c.getAttribute('tabindex') !== null)) {
        c.dataset.kapernAllein = 'a' + i;
        allein.push({id: 'a' + i,
                     text: (c.innerText || '').replace(/\s+/g, ' ')
                           .trim().slice(0, 30)});
      }
      return;
    }
    c.dataset.kapernId = 'c' + i;
    k[0].dataset.kapernZiel = 'c' + i;
    aus.push({id: 'c' + i,
              aussen: (c.getAttribute('aria-label') || '').slice(0, 30),
              innen: (k[0].innerText || '').replace(/\s+/g, ' ').trim()
                     .slice(0, 30),
              tag: k[0].tagName.toLowerCase(),
              anzahl: k.length});
  });
  return {faelle: aus, allein: allein};
}"""

# Die Selbstprobe: an einem Container OHNE inneres Bedienelement MUSS der
# Container selbst auf Enter reagieren.
SELBSTPROBE_JS = r"""(id) => {
  window.__allein = [];
  const c = document.querySelector('[data-kapern-allein="' + id + '"]');
  if (!c) return null;
  c.addEventListener('keydown', () => window.__allein.push('CONTAINER-keydown'));
  c.addEventListener('click', () => window.__allein.push('CONTAINER-click'));
  c.focus();
  return document.activeElement === c;
}"""

LAUSCHER_JS = r"""(id) => {
  window.__wer = [];
  const c = document.querySelector('[data-kapern-id="' + id + '"]');
  const k = document.querySelector('[data-kapern-ziel="' + id + '"]');
  if (!c || !k) return false;
  c.addEventListener('keydown', () => window.__wer.push('CONTAINER-keydown'));
  c.addEventListener('click', () => window.__wer.push('CONTAINER-click'));
  k.addEventListener('click', () => window.__wer.push('KNOPF-click'));
  k.focus();
  return document.activeElement === k;
}"""


def main(argv):
    from playwright.sync_api import sync_playwright
    ansicht = argv[0] if argv else "Arbeitsscheine"
    breite = int(argv[1]) if len(argv) > 1 else 390
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port,
                                      os.environ.get("EPK_INDEX", "index.html"))
    bericht = {"ansicht": ansicht, "breite": breite, "faelle": []}

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": breite, "height": 880},
            is_mobile=breite < 600, has_touch=breite < 600,
            device_scale_factor=1, color_scheme="dark")
        ctx.add_init_script(INIT)
        ctx.add_init_script(NUTZER)
        ctx.route("**/rest/v1/**", lambda r: r.abort())
        ctx.route("**/auth/v1/**", lambda r: r.abort())
        seite = ctx.new_page()
        try:
            seite.goto(url, wait_until="domcontentloaded")
            seite.wait_for_timeout(4000)
            HA._saat(seite)
            seite.wait_for_timeout(1500)
            seite.evaluate(HA.WAEHLEN_JS, ansicht)
            seite.wait_for_timeout(2000)

            gefunden = seite.evaluate(SUCHE_JS)
            faelle = gefunden["faelle"]
            allein = gefunden["allein"]
            print("%s bei %d px: %d Container mit innerem Bedienelement, "
                  "%d ohne" % (ansicht, breite, len(faelle), len(allein)))

            # 🔴 SELBSTPROBE ZUERST. Ohne sie waere jedes gruene Ergebnis
            #    unten von „der Melder misst gar nichts" nicht zu
            #    unterscheiden. Sie stand bis 29.09.2026 nur im Kopftext.
            if not allein:
                print("\U0001F534 Kein Container OHNE inneres Bedienelement "
                      "in dieser Ansicht -\n   die Selbstprobe kann hier "
                      "nicht laufen. NICHT GEMESSEN.")
                return 2
            geprobt = False
            for a in allein:
                if not seite.evaluate(SELBSTPROBE_JS, a["id"]):
                    continue
                seite.keyboard.press("Enter")
                seite.wait_for_timeout(300)
                wer = seite.evaluate("() => window.__allein")
                print("   Selbstprobe an %-24r -> %s"
                      % (a["text"][:24], wer or ["NICHTS"]))
                if wer:
                    geprobt = True
                    break
            if not geprobt:
                print("\U0001F534 An KEINEM Container ohne inneres "
                      "Bedienelement hat der Container\n   selbst auf Enter "
                      "reagiert. Dann misst dieser Melder nichts, und seine\n"
                      "   Ergebnisse unten belegen nichts. NICHT GEMESSEN.")
                return 2
            print("   \U0001F7E2 Selbstprobe bestanden - der Melder sieht "
                  "einen Tastendruck.\n")
            seite.evaluate(HA.WAEHLEN_JS, ansicht)
            seite.wait_for_timeout(1200)

            if not faelle:
                print("\U0001F534 Keiner gefunden. Das ist kein Ergebnis - "
                      "entweder gibt es hier\n   keine, oder der Sucher "
                      "greift daneben. NICHT gemessen.")
                return 2

            for f in faelle[:8]:
                if not seite.evaluate(LAUSCHER_JS, f["id"]):
                    print("   \U0001F534 %-28s Fokus kam nicht an - NICHT "
                          "gemessen" % f["innen"][:28])
                    continue
                seite.keyboard.press("Enter")
                seite.wait_for_timeout(400)
                wer = seite.evaluate("() => window.__wer")
                ok = "KNOPF-click" in wer
                f["wer"] = wer
                f["knopf_wirkt"] = ok
                bericht["faelle"].append(f)
                print("   %s %-28s (in %-22r) -> %s"
                      % ("\U0001F7E2" if ok else "\U0001F534",
                         f["innen"][:28], f["aussen"][:22],
                         wer or ["NICHTS"]))
                seite.evaluate(HA.WAEHLEN_JS, ansicht)
                seite.wait_for_timeout(1200)
        finally:
            ctx.close()
            browser.close()

    ziel = os.path.join(WURZEL, "docs", "befunde",
                        "TASTENKAPERN_%s_%d.json" % (ansicht, breite))
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps(bericht, ensure_ascii=False, indent=1))
    kaputt = [f for f in bericht["faelle"] if not f.get("knopf_wirkt")]
    print()
    if kaputt:
        print("\U0001F534 %d innere Bedienelemente reagieren NICHT auf Enter:"
              % len(kaputt))
        for f in kaputt:
            print("      %r in %r" % (f["innen"], f["aussen"]))
    else:
        print("\U0001F7E2 Jedes innere Bedienelement reagiert auf Enter.")
    print("geschrieben:", ziel)
    return 1 if kaputt else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
