# -*- coding: utf-8 -*-
"""Nachtrag zu B3: die FUENF Beschnittstellen auf Home bei 390 px benennen.

WOZU
────
`scripts/b3_vier_ansichten_messen.py` meldet auf Home bei 390 px fuenf
Elemente, deren Inhalt breiter ist als ihr Kasten (scrollWidth > clientWidth)
und die nicht quer gerollt werden duerfen. Fuer einen Aenderungsvorschlag
reicht der DOM-Pfad nicht - gebraucht wird, WORAN man das Element im
Quelltext wiederfindet: die Klasse, der Inline-Stil, die Textumgebung und die
Frage, ob ein Vorfahr das Rollen doch erlaubt.

WAS GEMESSEN WIRD
─────────────────
Je Beschnittstelle: Tag, Klasse, das vollstaendige style-Attribut (das ist
der Anker in einer Inline-React-App), scrollWidth/clientWidth, overflow-x,
text-overflow, die ersten 90 Zeichen Text, die Kette der Vorfahren mit deren
overflow-x - und ob einer davon auto/scroll ist (dann ist der Inhalt durch
Wischen erreichbar und der Befund milder).

WAS NICHT GEMESSEN WIRD
───────────────────────
  * Andere Ansichten und andere Breiten. Diese Sonde ist ausdruecklich der
    Nachtrag zu EINEM Fall: Home bei 390 px.
  * Ob der abgeschnittene Text fuer den Nutzer wichtig ist. Das ist eine
    Frage an Sebastian, keine Messung.

DER KOEDER
──────────
Ein eingehaengtes Feld mit 240 Zeichen in 80 px MUSS in der Liste stehen.
Fehlt es, misst die Sonde nichts und "fuenf Stellen" waere geraten.

AUFRUF
──────
    set EPK_INDEX=_mess_stand_939.html
    python scripts/b3_home390_beschnitt.py
"""
import os
import sys

for _strom in (sys.stdout, sys.stderr):
    try:
        _strom.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)

import mob_ansicht_messen as M                 # noqa: E402
import b3_vier_ansichten_messen as B           # noqa: E402

DETAIL_JS = r"""() => {
  const _cs = e => getComputedStyle(e);
  const kette = e => {
    const t = [];
    let x = e;
    while (x && x !== document.documentElement && t.length < 8) {
      const k = (x.className && typeof x.className === 'string')
        ? '.' + x.className.trim().split(/\s+/).join('.') : '';
      t.push(x.tagName.toLowerCase() + (x.id ? '#' + x.id : '') + k
             + '  ox=' + _cs(x).overflowX
             + ' sw=' + x.scrollWidth + '/cw=' + x.clientWidth);
      x = x.parentElement;
    }
    return t;
  };
  const rollbarUeber = e => {
    let x = e.parentElement;
    while (x && x !== document.body) {
      const ox = _cs(x).overflowX;
      if (ox === 'auto' || ox === 'scroll') return true;
      x = x.parentElement;
    }
    return false;
  };
  const wurzel = document.getElementById('root') || document.body;
  const out = [];
  wurzel.querySelectorAll('*').forEach(e => {
    if (e.scrollWidth <= e.clientWidth + 1) return;
    const t = (e.textContent || '').replace(/\s+/g, ' ').trim();
    if (!t) return;
    const c = _cs(e);
    if (c.overflowX === 'auto' || c.overflowX === 'scroll') return;
    out.push({
      tag: e.tagName.toLowerCase(),
      klasse: (e.className && typeof e.className === 'string') ? e.className : '',
      stil: e.getAttribute('style') || '',
      scroll: e.scrollWidth, sicht: e.clientWidth,
      fehlt: e.scrollWidth - e.clientWidth,
      overflowX: c.overflowX, textOverflow: c.textOverflow,
      whiteSpace: c.whiteSpace, fontSize: c.fontSize,
      text: t.slice(0, 90),
      durch_wischen_erreichbar: rollbarUeber(e),
      kette: kette(e)});
  });
  out.sort((a, b) => b.fehlt - a.fehlt);
  return out;
}"""

KOEDER_EIN = r"""() => {
  const w = document.getElementById('root') || document.body;
  const d = document.createElement('div');
  d.id = '__k_b';
  d.style.cssText = 'width:80px;overflow:hidden;white-space:nowrap';
  d.textContent = 'K'.repeat(240);
  w.appendChild(d);
  return d.scrollWidth > d.clientWidth + 1;
}"""


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt.")
        return 2
    datei = os.environ.get("EPK_INDEX", "index.html")
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port, datei)
    print("Gemessen: %s" % url)

    with sync_playwright() as pw:
        br = pw.chromium.launch()
        ctx = br.new_context(viewport={"width": 390, "height": 844},
                            is_mobile=True, has_touch=True,
                            device_scale_factor=2)
        ctx.add_init_script(M.INIT)
        ctx.add_init_script(
            "try{var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
            "u.monteurId='M1';u.role='admin';localStorage.setItem("
            "'epkolar_user',JSON.stringify(u));}catch(e){}")
        ctx.route("**/rest/v1/**", lambda r: r.abort())
        ctx.route("**/auth/v1/**", lambda r: r.abort())
        seite = ctx.new_page()
        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(3800)
        B._saeen(seite)
        seite.evaluate(M.NAV_OEFFNEN_JS)
        seite.wait_for_timeout(400)
        print("Navigation:", seite.evaluate(B.NAV_MEHR_JS, "Home"))
        seite.wait_for_timeout(2600)
        seite.evaluate(B.MEHR_ZU_JS)
        seite.wait_for_timeout(600)
        nw = seite.evaluate(B.ANSICHT_DA_JS, "home")
        print("Ansicht belegt (%s): %s" % (nw["marke"], nw["da"]))
        if not nw["da"]:
            print("ABBRUCH: nicht Home. Alles darunter waere die falsche Seite.")
            return 1

        # KOEDER
        assert seite.evaluate(KOEDER_EIN)
        liste = seite.evaluate(DETAIL_JS)
        traf = any(x["text"].startswith("KKK") for x in liste)
        print("KOEDER (240 Zeichen in 80 px): %s"
              % ("ANGESCHLAGEN" if traf else "STUMM"))
        seite.evaluate("() => {const e=document.getElementById('__k_b');"
                       "if(e)e.remove();}")
        if not traf:
            print("Der Melder findet seinen eigenen Fall nicht - keine Zahl.")
            br.close()
            return 1

        liste = seite.evaluate(DETAIL_JS)
        print("\n%d Beschnittstellen (ohne die gewollt rollbaren):\n"
              % len(liste))
        for k, x in enumerate(liste, 1):
            print("(%d) %s%s  fehlen %d px  (%d von %d)  ox=%s  "
                  "text-overflow=%s  white-space=%s  fontSize=%s"
                  % (k, x["tag"], ("." + x["klasse"]) if x["klasse"] else "",
                     x["fehlt"], x["sicht"], x["scroll"], x["overflowX"],
                     x["textOverflow"], x["whiteSpace"], x["fontSize"]))
            print("     Text : %r" % x["text"])
            print("     Stil : %s" % (x["stil"][:230] or "(kein style-Attribut)"))
            print("     durch Wischen erreichbar: %s"
                  % x["durch_wischen_erreichbar"])
            for z in x["kette"][:5]:
                print("       ^ %s" % z)
            print()
        br.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
