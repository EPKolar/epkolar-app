# -*- coding: utf-8 -*-
"""Nachtrag zu Stufe 12-15: war die Fussleisten-Beschriftung auch bei 10 px
schon gekuerzt?

WOZU
────
`b3_stufen_12_15_messen.py` misst bei 390 px, dass die Beschriftung des
aktiven Gruppenknopfes in `.bottom-nav` WIRKLICH gekuerzt wird
(`overflow:hidden` + `text-overflow:ellipsis`, Schlitz 74 px):

    Monatsabrechnung  112 -> 74  (37,5 px verloren)
    Abwesenheiten      89 -> 74  (15,3)
    Bauprovisorien     88 -> 74  (13,7)
    Gefahrenstoffe     86 -> 74  (11,9)
    Zeiterfassung      80 -> 74  ( 5,6)

Die Schriftgroesse steht seit v3.9.943 auf `UI.fMeta` (12 px); vorher waren
es 10. Die naheliegende Aussage "das ist eine Folge von v3.9.943" waere
GERECHNET (112 * 10/12 = 93) und nicht gemessen. Diese Sonde misst es:
sie setzt die Schriftgroesse dieser Spannen per CSS-Regel auf 10 px und
liest die Breiten NOCH EINMAL.

WAS SIE NICHT TUT
─────────────────
Sie aendert `index.html` nicht und schreibt nichts. Die 10-px-Regel lebt in
einer eingefuegten `<style>`-Marke im Browser und nur fuer die Dauer der
Messung. Die Ansicht dahinter (ob der Knopf dadurch anders umbricht) wird
NICHT beurteilt - gemessen wird allein die Textbreite gegen den Schlitz.

KOEDER
──────
K-F1  Nach dem Einsetzen der Regel MUSS die gemessene Schriftgroesse 10 sein.
      Ist sie es nicht, hat die Regel nicht gegriffen (die Hausregeln in
      diesem Block tragen `!important`), und alle Zahlen danach waeren die
      alten - eine saubere, falsche Antwort.

AUFRUF
──────
    set EPK_INDEX=_mess_stand_944.html
    python scripts/b3_fussleiste_beschnitt.py
"""
import io
import os
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)

import mob_ansicht_messen as M           # noqa: E402
import b3_vier_ansichten_messen as B     # noqa: E402
import b3_stufen_12_15_messen as Z       # noqa: E402

MESSEN_JS = r"""() => {
  const b = document.querySelector('.bottom-nav');
  if (!b) return {fehler: 'keine .bottom-nav'};
  const aus = [];
  Array.from(b.querySelectorAll('button')).forEach(k => {
    const sp = Array.from(k.children).filter(x => x.tagName === 'SPAN');
    const txt = sp[1] || sp[0];
    if (!txt) return;
    const c = getComputedStyle(txt);
    aus.push({text: (txt.textContent || '').trim(),
              px: Math.round(parseFloat(c.fontSize) * 10) / 10,
              scroll: txt.scrollWidth, sicht: txt.clientWidth,
              gekuerzt: txt.scrollWidth > txt.clientWidth + 0.5,
              verloren: Math.round((txt.scrollWidth - txt.clientWidth) * 10) / 10,
              knopfBreite: Math.round(k.getBoundingClientRect().width),
              leisteHoehe: Math.round(b.getBoundingClientRect().height)});
  });
  return {knoepfe: aus};
}"""

ZEHN_EIN_JS = r"""() => {
  let s = document.getElementById('__zehn');
  if (!s) { s = document.createElement('style'); s.id = '__zehn';
            document.head.appendChild(s); }
  // Hoehere Spezifitaet als alles im GCSS-Block, plus !important -
  // sonst gewinnt `.bottom-nav button > span:nth-child(2)` aus dem
  // 380er-Block bzw. der inline-Stil.
  s.textContent = 'html body .bottom-nav button > span:nth-child(2)'
                + '{font-size:10px !important}';
  return true;
}"""


def main(argv):
    from playwright.sync_api import sync_playwright
    datei = os.environ.get("EPK_INDEX", "index.html")
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port, datei)
    import hashlib
    h = hashlib.md5(io.open(os.path.join(WURZEL, datei), "rb").read()).hexdigest()
    print("Gemessen: %s   md5 %s" % (url, h))

    with sync_playwright() as pw:
        br = pw.chromium.launch()
        ctx = br.new_context(viewport={"width": 390, "height": 844},
                             is_mobile=True, has_touch=True,
                             device_scale_factor=2, color_scheme="dark")
        ctx.add_init_script(M.INIT)
        ctx.add_init_script(
            "try{var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
            "u.monteurId='M1';u.name='Gerhard Steinbichler';u.role='admin';"
            "u.rolle='Geschaeftsfuehrer';"
            "localStorage.setItem('epkolar_user',JSON.stringify(u));"
            "localStorage.setItem('epk_theme','dark');}catch(e){}")
        ctx.route("**/rest/v1/**", lambda r: r.abort())
        ctx.route("**/auth/v1/**", lambda r: r.abort())
        seite = ctx.new_page()
        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(3800)
        Z._saeen12(seite)

        for kuerzel in ("monatsabr", "abwesend", "baupro", "gefahr", "zeit",
                        "auswertungen", "admin"):
            prot = []
            Z._navigieren12(seite, kuerzel, 390, prot)
            nw = seite.evaluate(Z.ANSICHT_DA_JS, kuerzel)
            if not nw["da"]:
                print("%-13s NICHT ERREICHT - nicht gemessen" % kuerzel)
                continue
            a = seite.evaluate(MESSEN_JS)
            seite.evaluate(ZEHN_EIN_JS)
            seite.wait_for_timeout(400)
            b = seite.evaluate(MESSEN_JS)
            # K-F1
            zehner = [x for x in b["knoepfe"] if x["px"] == 10]
            if not zehner:
                print("ABBRUCH (K-F1): die 10-px-Regel hat nicht gegriffen "
                      "(%s). Die Zahlen waeren die alten."
                      % [x["px"] for x in b["knoepfe"]])
                return 1
            print("\n%-13s  Leiste %s px hoch" % (kuerzel,
                                                  a["knoepfe"][0]["leisteHoehe"]))
            for x, y in zip(a["knoepfe"], b["knoepfe"]):
                if not (x["gekuerzt"] or y["gekuerzt"]):
                    continue
                print("   %-18r  %gpx: %s/%s gekuerzt=%s (-%s)   |   "
                      "%gpx: %s/%s gekuerzt=%s (-%s)"
                      % (x["text"], x["px"], x["scroll"], x["sicht"],
                         x["gekuerzt"], x["verloren"],
                         y["px"], y["scroll"], y["sicht"], y["gekuerzt"],
                         y["verloren"]))
            print("   Leistenhoehe 12px: %s   10px: %s"
                  % (a["knoepfe"][0]["leisteHoehe"],
                     b["knoepfe"][0]["leisteHoehe"]))
            seite.evaluate("() => {const s=document.getElementById('__zehn');"
                           "if(s) s.remove(); return true;}")
            seite.wait_for_timeout(300)
        br.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
