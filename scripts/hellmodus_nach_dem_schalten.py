# -*- coding: utf-8 -*-
"""Bleibt eine Ansicht dunkel, wenn man ZUR LAUFZEIT auf hell schaltet?

🔴 DIE LUECKE ZWISCHEN ZWEI RICHTIGEN MESSUNGEN.

`hellmodus_ansichten.py` misst 32 Ansichten mit `epk_theme='light'` - und
meldet 0 dunkle Ansichten. Richtig gemessen. Es setzt die Wahl aber **vor dem
Laden** in den Speicher: gemessen ist der Startzustand.

`hellmodus_schalter_messen.py` betaetigt den Schalter zur Laufzeit - und der
wirkt: ein Tipp, Koerper wird `rgb(240,242,245)`. Auch richtig gemessen. Es
misst aber nur die Ansicht, auf der man gerade steht.

Sebastians Meldung liegt GENAU DAZWISCHEN: *"wenn ich mobil auf hell schalte
bleibt es dunkel"*. Erst umschalten, DANN durch die Ansichten - ohne neu zu
laden. Das hat nie etwas gemessen.

WARUM DAS ein eigener Fall IST UND KEIN DOPPELTES
Die Farben kommen aus `V.bg` & Co., und das sind GETTER auf ein
Modul-`_dark`. Wer den Wert beim ersten Rendern in eine Konstante, ein
`useMemo` oder eine Stil-Zeichenkette uebernommen hat, behaelt die DUNKLE
Farbe, bis die Komponente neu gebaut wird. Beim Setzen VOR dem Laden faellt
das nie auf, weil dann schon der helle Wert dastand. Genau deshalb sieht der
Nutzer etwas, das beide bisherigen Messungen nicht sehen konnten.

GEGENPROBE, OHNE DIE DIE ZAHLEN NICHTS WERT SIND
Dieselbe Ansicht wird ZWEIMAL gemessen: einmal nach dem Umschalten und einmal
nach einem Neuladen mit derselben Wahl. Ist die erste dunkel und die zweite
hell, liegt es am Umschalten - und nur dann ist es dieser Befund.
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
          "localStorage.setItem('epkolar_user',JSON.stringify(u));}catch(e){}")

OHNE_WAHL = "try{localStorage.removeItem('epk_theme');}catch(e){}"
MIT_HELL = "try{localStorage.setItem('epk_theme','light');}catch(e){}"

SCHALTER_JS = r"""() => {
  const e = [...document.querySelectorAll('button,[role="button"]')].find(x => {
    const r = x.getBoundingClientRect();
    if (!r.width || !r.height) return false;
    const t = (x.getAttribute('title') || '') + (x.getAttribute('aria-label') || '');
    return /Theme|Hell|Dunkel|Auto/i.test(t);
  });
  if (!e) return null;
  return {titel: e.getAttribute('title'), text: (e.innerText || '').trim()};
}"""

TIPPEN_JS = r"""() => {
  const e = [...document.querySelectorAll('button,[role="button"]')].find(x => {
    const r = x.getBoundingClientRect();
    if (!r.width || !r.height) return false;
    const t = (x.getAttribute('title') || '') + (x.getAttribute('aria-label') || '');
    return /Theme|Hell|Dunkel|Auto/i.test(t);
  });
  if (!e) return false;
  e.click();
  return true;
}"""

MODUS_JS = "() => { try { return localStorage.getItem('epk_theme'); } " \
           "catch(e) { return null; } }"


def _kontext(browser, breite, hell_vorgeben):
    ctx = browser.new_context(
        viewport={"width": breite, "height": 880},
        is_mobile=breite < 600, has_touch=breite < 600,
        device_scale_factor=1, color_scheme="dark")
    ctx.add_init_script(INIT)
    ctx.add_init_script(NUTZER)
    ctx.add_init_script(MIT_HELL if hell_vorgeben else OHNE_WAHL)
    ctx.route("**/rest/v1/**", lambda r: r.abort())
    ctx.route("**/auth/v1/**", lambda r: r.abort())
    return ctx


def _durchgang(browser, url, breite, umschalten):
    """Einmal durch alle Reiter. `umschalten` = erst dunkel, dann per Tipp hell."""
    ctx = _kontext(browser, breite, hell_vorgeben=not umschalten)
    seite = ctx.new_page()
    aus = {}
    try:
        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(4000)
        HA._saat(seite)
        seite.wait_for_timeout(1500)

        if umschalten:
            if breite < 600:
                seite.evaluate(M.NAV_OEFFNEN_JS)
                seite.wait_for_timeout(700)
            for _ in range(4):
                if not seite.evaluate(TIPPEN_JS):
                    return {"__fehler": "Themenschalter nicht gefunden"}
                seite.wait_for_timeout(800)
                if seite.evaluate(MODUS_JS) == "light":
                    break
            else:
                return {"__fehler": "Modus light nie erreicht"}
            seite.keyboard.press("Escape")
            seite.wait_for_timeout(600)

        modus = seite.evaluate(MODUS_JS)
        if modus != "light":
            return {"__fehler": "Modus ist %r statt light" % modus}

        tabs = seite.evaluate(HA.TABS_JS)
        for name in tabs.get("reiter", []):
            if breite < 600:
                seite.evaluate(M.NAV_OEFFNEN_JS)
                seite.wait_for_timeout(500)
            wie = seite.evaluate(HA.WAEHLEN_JS, name)
            if not str(wie).startswith("geklickt"):
                aus[name] = {"__fehler": wie}
                continue
            seite.wait_for_timeout(1400)
            aus[name] = HA._einmal(seite)
    finally:
        ctx.close()
    return aus


def main(argv):
    from playwright.sync_api import sync_playwright
    breite = int(argv[0]) if argv else 390
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port,
                                      os.environ.get("EPK_INDEX", "index.html"))

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        print("A) UMGESCHALTET zur Laufzeit (Start: keine Wahl, OS dunkel)")
        a = _durchgang(browser, url, breite, umschalten=True)
        print("B) GEGENPROBE: dieselbe Wahl VOR dem Laden gesetzt")
        b = _durchgang(browser, url, breite, umschalten=False)
        browser.close()

    if "__fehler" in a:
        print("\U0001F534 Durchgang A: %s - NICHT gemessen" % a["__fehler"])
        return 2
    if "__fehler" in b:
        print("\U0001F534 Durchgang B: %s - NICHT gemessen" % b["__fehler"])
        return 2

    print("\n%-22s %12s %12s   %s"
          % ("Ansicht", "umgeschaltet", "vorgegeben", "Befund"))
    schlimm = []
    for name in sorted(set(a) | set(b)):
        x, y = a.get(name), b.get(name)
        if not x or not y or "__fehler" in x or "__fehler" in y:
            print("   %-22s %s" % (name, "NICHT gemessen"))
            continue
        sa, sb = x["schirm"], y["schirm"]
        marke = ""
        # 🔴 Der Befund ist der UNTERSCHIED, nicht die absolute Zahl: nur wenn
        #    dieselbe Ansicht nach dem Umschalten dunkel ist und nach dem
        #    Neuladen hell, liegt es am Umschalten.
        if sa >= 25 and sb < 25:
            marke = "\U0001F534 bleibt dunkel NUR nach dem Umschalten"
            schlimm.append((name, sa, sb))
        elif sa >= 25:
            marke = "dunkel in BEIDEN - anderer Befund"
        print("   %-22s %11.1f %% %11.1f %%   %s" % (name, sa, sb, marke))

    ziel = os.path.join(WURZEL, "docs", "befunde",
                        "HELLMODUS_NACH_SCHALTEN_%d.json" % breite)
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps({"breite": breite, "umgeschaltet": a, "vorgegeben": b},
                   ensure_ascii=False, indent=1))
    print("\n%d Ansichten bleiben NUR nach dem Umschalten dunkel." % len(schlimm))
    print("geschrieben:", ziel)
    return 1 if schlimm else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
