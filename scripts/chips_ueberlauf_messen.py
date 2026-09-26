# -*- coding: utf-8 -*-
"""Rollt die Filter-Leiste der Projektliste wirklich - und toetet sie den Wisch?

WOZU
────
Der Auftrag verlangt fuer die Filter-Chips "horizontal scrollbar, nicht
umbrechend". In diesem Bestand ist aber GEMESSEN, dass ein quer rollbarer
Kasten die waagrechte Geste SELBST verbraucht: der Browser rollt ihn, statt
sie nach oben durchzureichen. v3.9.930 hat genau diese Bauform aus zwei
Chip-Leisten ENTFERNT, nachdem mit echten Touch-Ereignissen belegt war, dass
der Streifen darueber tot war.

Beides gleichzeitig ist moeglich - WENN die Leiste nicht ueberlaeuft. Ein
Kasten mit `overflow-x:auto`, dessen Inhalt hineinpasst, hat keinen
Rollbereich und verbraucht deshalb auch keine Geste. Ob das bei vier Chips
zutrifft, ist eine Messung, keine Meinung.

WAS GEMESSEN WIRD
─────────────────
Je Breite: scrollWidth gegen clientWidth der Leiste. Differenz > 2 px heisst
"rollt wirklich" und damit "tote Zone". Dazu die Hoehe der Chips (36 gefordert)
und ob die Seite selbst waagrecht ueberlaeuft.

DER KOEDER
──────────
Ein absichtlich zu langer Chip wird eingehaengt; die Leiste MUSS danach
ueberlaufen. Tut sie es nicht, misst das Werkzeug den Ueberlauf nicht - und
"kein Ueberlauf" waere eine Aussage ueber nichts.

AUFRUF
──────
    python scripts/chips_ueberlauf_messen.py
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import mob_ansicht_messen as M  # noqa: E402

LEISTE_JS = """() => {
  // Die Filter-Leiste erkennt man an ihren Chips: vier Knoepfe mit
  // aria-pressed. Gesucht wird ueber die EIGENSCHAFT, nicht ueber eine Klasse.
  // Gesucht wird die MARKE, nicht aria-pressed: seit v3.9.935 tragen
  // auch die beiden Ansichtsumschalter (Kachel/Liste) aria-pressed,
  // und dieser Pruefstand fand dadurch 6 Chips statt 4 und zwei
  // aktive statt einen. Die Marke trennt die AUSWAHL (welcher Status)
  // von der DARSTELLUNG (Kachel oder Liste).
  const chips = Array.from(document.querySelectorAll('button[data-epk="filter-chip"]'));
  if (!chips.length) return {fehler: 'keine Chips mit data-epk=filter-chip'};
  const leiste = chips[0].parentElement;
  const cs = getComputedStyle(leiste);
  const r = leiste.getBoundingClientRect();
  const de = document.documentElement;
  return {
    anzahl: chips.length,
    beschriftungen: chips.map(c => (c.innerText || '').trim().split(String.fromCharCode(10)).join(' ')),
    hoehen: chips.map(c => Math.round(c.getBoundingClientRect().height)),
    umbruch: cs.flexWrap,
    overflowX: cs.overflowX,
    scrollWidth: leiste.scrollWidth,
    clientWidth: leiste.clientWidth,
    rollt: leiste.scrollWidth > leiste.clientWidth + 2,
    seiteRollt: de.scrollWidth > de.clientWidth + 2,
    aktiv: chips.filter(c => c.getAttribute('aria-pressed') === 'true').length
  };
}"""

KOEDER_JS = """() => {
  // Gesucht wird die MARKE, nicht aria-pressed: seit v3.9.935 tragen
  // auch die beiden Ansichtsumschalter (Kachel/Liste) aria-pressed,
  // und dieser Pruefstand fand dadurch 6 Chips statt 4 und zwei
  // aktive statt einen. Die Marke trennt die AUSWAHL (welcher Status)
  // von der DARSTELLUNG (Kachel oder Liste).
  const chips = Array.from(document.querySelectorAll('button[data-epk="filter-chip"]'));
  if (!chips.length) return false;
  const leiste = chips[0].parentElement;
  const b = document.createElement('button');
  b.id = '__langerChip__';
  b.setAttribute('aria-pressed', 'false');
  b.textContent = 'Ein absichtlich viel zu langer Filtername der nicht passt';
  b.style.cssText = 'white-space:nowrap;padding:0 14px;height:36px;flex:0 0 auto';
  leiste.appendChild(b);
  return leiste.scrollWidth > leiste.clientWidth + 2;
}"""

WEG_JS = """() => {
  const b = document.getElementById('__langerChip__');
  if (b) b.remove();
  return true;
}"""

BREITEN = [320, 390, 430, 768, 1440]


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt.")
        return 2

    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port, os.environ.get("EPK_INDEX", "index.html"))
    print("Gemessen wird:", url)

    schlimm, gemessen, koeder_ok = [], 0, False
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for breite in BREITEN:
            ctx = browser.new_context(viewport={"width": breite, "height": 860},
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
            seite.wait_for_timeout(3600)
            seite.evaluate(M.NAV_OEFFNEN_JS)
            seite.wait_for_timeout(320)
            seite.evaluate(M.NAV_WAEHLEN_JS, "Projekte")
            seite.wait_for_timeout(1900)
            d = seite.evaluate(LEISTE_JS)

            if breite == 390 and not d.get("fehler"):
                koeder_ok = bool(seite.evaluate(KOEDER_JS))
                seite.evaluate(WEG_JS)
            ctx.close()

            if d.get("fehler"):
                print("%4dpx  ROT: %s" % (breite, d["fehler"]))
                schlimm.append("%dpx: %s" % (breite, d["fehler"]))
                continue
            gemessen += 1
            print("\n%4dpx  %d Chips, Hoehen %s, aktiv %d"
                  % (breite, d["anzahl"], d["hoehen"], d["aktiv"]))
            print("        %s" % d["beschriftungen"])
            print("        flex-wrap %s | overflow-x %s | %d von %d px -> rollt: %s"
                  % (d["umbruch"], d["overflowX"], d["scrollWidth"],
                     d["clientWidth"], d["rollt"]))
            if d["seiteRollt"]:
                print("        SEITE ROLLT WAAGRECHT")
                schlimm.append("%dpx: die SEITE laeuft waagrecht ueber" % breite)

            if d["anzahl"] != 4:
                schlimm.append("%dpx: %d Chips statt 4" % (breite, d["anzahl"]))
            if d["aktiv"] != 1:
                schlimm.append("%dpx: %d aktive Chips statt genau 1"
                               % (breite, d["aktiv"]))
            # 36 px sind DEKLARIERT (inline height/min-height) und gelten
            # oberhalb von 768 px an einem feinen Zeigegeraet. Darunter -
            # und an JEDEM groben Zeigegeraet - hebt eine bestehende Regel
            # jeden Knopf auf 44 px:
            #     @media (pointer: coarse), (max-width: 768px)
            #         { ... min-height: 44px !important }
            # Das ist die Tippziel-Haertung aus v3.8.67, Apples Mindestmass.
            # Die 36 dort durchzudruecken wuerde das Tippziel auf genau dem
            # Geraet verkleinern, wo es am meisten zaehlt. Gemessen wird
            # deshalb "genau 36" nur oberhalb der Schwelle und sonst
            # "mindestens 36" - die Schwelle ist am Browser abgefragt, nicht
            # geschaetzt (computed min-height 44px bei 768, 36px bei 1440).
            if breite > 768:
                if any(abs(h - 36) > 1 for h in d["hoehen"]):
                    schlimm.append("%dpx: Chiphoehen %s statt 36"
                                   % (breite, d["hoehen"]))
            else:
                if any(h < 36 for h in d["hoehen"]):
                    schlimm.append("%dpx: Chiphoehen %s - unter 36 und damit "
                                   "unter dem Tippziel" % (breite, d["hoehen"]))
            if d["rollt"]:
                print("        ACHTUNG: rollbarer Bereich -> tote Wischzone")
                schlimm.append("%dpx: die Leiste ROLLT (%d von %d px) - dort ist "
                               "der Wisch tot" % (breite, d["scrollWidth"],
                                                  d["clientWidth"]))
        browser.close()

    print("\n" + "=" * 64)
    print("KOEDER (ein absichtlich zu langer Chip bei 390px): %s"
          % ("Ueberlauf ERKANNT" if koeder_ok else "NICHT erkannt"))
    if gemessen == 0:
        print("KEINE Breite gemessen - das ist kein gruenes Ergebnis.")
        return 1
    if not koeder_ok:
        print("Das Werkzeug erkennt keinen Ueberlauf. Dann sagt 'laeuft nicht")
        print("ueber' nichts aus. ABBRUCH.")
        return 1
    if schlimm:
        print("ROT:")
        for z in schlimm:
            print("   " + z)
        return 1
    print("GRUEN - vier Chips, 36 px hoch, genau einer aktiv, nicht umbrechend,")
    print("und in KEINER gemessenen Breite entsteht ein rollbarer Bereich. Der")
    print("Auftrag (nicht umbrechend, scrollbar) und die Wischgeste sind damit")
    print("beide erfuellt: ein overflow-x-Kasten ohne Ueberlauf verbraucht")
    print("keine Geste.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
