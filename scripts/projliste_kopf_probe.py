# -*- coding: utf-8 -*-
"""Probe: Kopf und Kennzahlenzeile der Projektliste - gerendert, nicht gelesen.

WOZU
────
Die Kennzahlenzeile ist neu. Zwei Dinge koennen an ihr schiefgehen, und
beide sieht man dem Quelltext nicht an:

1. TDZ. `_kz` liest `hoursByProject`. Steht die Berechnung vor dessen
   Deklaration, wirft React beim Rendern 'Cannot access ... before
   initialization', ViewBoundary faengt es, und der Tab zeigt einen Fehler
   statt der Liste. `node_check` PARST nur und bleibt dabei gruen.
   Genau das ist beim Bauen passiert - gefunden hat es erst dieser Lauf.

2. Die Auftragssumme haengt an `_seeBetrag`. Monteure duerfen sie NICHT
   sehen (v3.9.456). Eine neue Zeile, die sie ungefragt zeigt, waere ein
   Datenleck - und zwar ein huebsches.

Gemessen wird deshalb in DREI Faellen: Admin schmal, Monteur schmal, Admin
breit.

DER KOEDER
──────────
Der Admin-Fall MUSS ein Eurozeichen zeigen. Zeigt keiner der drei eines,
misst die Probe nicht die Summe, sondern nichts - und "Monteur sieht kein
Euro" waere wertlos.

AUFRUF
──────
    python scripts/projliste_kopf_probe.py
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import mob_ansicht_messen as M  # noqa: E402

KOPF_JS = """() => {
  const h = Array.from(document.querySelectorAll('h2'))
    .find(e => (e.innerText || '').trim() === 'Projekte');
  if (!h) {
    const txt = (document.body.innerText || '').slice(0, 160);
    return {fehler: 'kein h2 "Projekte"', seite: txt};
  }
  const z = h.parentElement.children[1];
  const cs = getComputedStyle(h);
  return {
    groesse: parseFloat(cs.fontSize),
    gewicht: cs.fontWeight,
    familie: cs.fontFamily.slice(0, 40),
    zeile: z ? z.innerText.split(String.fromCharCode(10)).join(' ').trim() : null
  };
}"""

FAELLE = [("admin", 390, 22), ("monteur", 390, 22), ("admin", 1440, 28)]


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt.")
        return 2

    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port, os.environ.get("EPK_INDEX", "index.html"))
    print("Gemessen wird:", url)

    schlimm, euro_gesehen, gemessen = [], False, 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for rolle, breite, soll in FAELLE:
            ctx = browser.new_context(
                viewport={"width": breite, "height": 844},
                is_mobile=breite < 600, has_touch=breite < 600)
            ctx.add_init_script(M.INIT)
            ctx.add_init_script(
                "try{var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
                "u.role='%s';u.monteurId='M1';u.name='Gerhard Steinbichler';"
                "localStorage.setItem('epkolar_user',JSON.stringify(u));}catch(e){}"
                % rolle)
            ctx.route("**/rest/v1/**", lambda r: r.abort())
            ctx.route("**/auth/v1/**", lambda r: r.abort())
            seite = ctx.new_page()
            seite.goto(url, wait_until="domcontentloaded")
            seite.wait_for_timeout(3800)
            seite.evaluate(M.NAV_OEFFNEN_JS)
            seite.wait_for_timeout(350)
            seite.evaluate(M.NAV_WAEHLEN_JS, "Projekte")
            seite.wait_for_timeout(2000)
            d = seite.evaluate(KOPF_JS)
            ctx.close()

            if d.get("fehler"):
                print("%-8s %4dpx  ROT: %s" % (rolle, breite, d["fehler"]))
                print("          Seite: %r" % d.get("seite", "")[:140])
                schlimm.append("%s/%dpx: %s" % (rolle, breite, d["fehler"]))
                continue

            gemessen += 1
            print("%-8s %4dpx  Titel %.0fpx/%s  %s"
                  % (rolle, breite, d["groesse"], d["gewicht"], d["familie"]))
            print("          Zeile: %r" % d["zeile"])

            if abs(d["groesse"] - soll) > 0.6:
                schlimm.append("%s/%dpx: Titel %.0f statt %d px"
                               % (rolle, breite, d["groesse"], soll))
            if str(d["gewicht"]) not in ("700", "bold"):
                schlimm.append("%s/%dpx: Titelgewicht %s statt 700"
                               % (rolle, breite, d["gewicht"]))
            if "Archivo" not in d["familie"]:
                schlimm.append("%s/%dpx: Schrift ist %r, nicht Archivo"
                               % (rolle, breite, d["familie"]))
            z = d["zeile"] or ""
            if "aktiv" not in z or " h" not in z:
                schlimm.append("%s/%dpx: Kennzahlenzeile unvollstaendig: %r"
                               % (rolle, breite, z))
            hat_euro = "€" in z
            if rolle == "monteur" and hat_euro:
                schlimm.append("MONTEUR SIEHT DIE AUFTRAGSSUMME: %r" % z)
            if rolle != "monteur":
                euro_gesehen = euro_gesehen or hat_euro

    print("\n" + "=" * 62)
    if gemessen == 0:
        print("KEIN EINZIGER FALL GEMESSEN - das ist kein gruenes Ergebnis.")
        return 1
    if not euro_gesehen:
        print("KOEDER GESCHEITERT: in keinem Admin-Fall stand ein Eurozeichen.")
        print("Dann misst die Probe die Summe gar nicht, und 'der Monteur")
        print("sieht keine' waere eine Aussage ueber nichts.")
        return 1
    if schlimm:
        print("ROT:")
        for z in schlimm:
            print("   " + z)
        return 1
    print("GRUEN - Titel 22/28 px in 700, Archivo, Kennzahlenzeile vollstaendig,")
    print("und die Auftragssumme bleibt vor dem Monteur verborgen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
