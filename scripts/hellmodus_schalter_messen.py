# -*- coding: utf-8 -*-
"""Wirkt der Hell/Dunkel-SCHALTER am Telefon? - die Stelle, die nie gemessen war.

🔴 WARUM DIESE MESSUNG FEHLTE, OBWOHL ES SCHON EINE GAB.
`hellmodus_ansichten.py` misst 32 Ansichten bei 390 und 1440 px mit
`epk_theme='light'` - und meldet 0 dunkle Ansichten im Hellmodus. Das ist
richtig gemessen und beantwortet die falsche Frage: es setzt die Wahl
**vor dem Laden** in den Speicher und misst den STARTZUSTAND.

Sebastian meldet aber etwas anderes: *"wenn ich mobil auf hell schalte bleibt
es dunkel"* - das ist der SCHALTER zur Laufzeit. Zwischen beidem liegt der
ganze Weg `toggleTheme` -> `setThemeMode` -> `setIsDark` + `applyTheme`, und
den hat nie etwas gemessen. Dieselbe Fehlerform wie ueberall: das Instrument
misst einwandfrei, nur eine andere Grundgesamtheit.

WAS GEMESSEN WIRD
Ausgangslage wie beim Nutzer: KEINE gespeicherte Wahl, Betriebssystem auf
dunkel - die App startet also dunkel. Dann wird der Schalter betaetigt, bis
der Modus `light` erreicht ist, und nach JEDEM Schritt gemessen:

  * der Modus im Speicher (`epk_theme`)
  * die tatsaechliche Hintergrundfarbe des Koerpers
  * die Helligkeit der GROESSTEN sichtbaren Flaeche
  * der Anteil des Schirms, der dunkel ist

🔴 DER SCHALTER WIRD ALS MENSCH BETAETIGT, NICHT ALS FUNKTIONSAUFRUF.
`window.setThemeMode('light')` aufzurufen wuerde beweisen, dass die Funktion
wirkt - und genau das ist nicht die Frage. Geklickt wird das Element, das am
Telefon sichtbar ist. Wenn es zwei Wege gibt (Kopfleiste und Einstellungen),
werden beide gemessen.
"""
import io
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
WURZEL = os.path.dirname(HIER)

import mob_ansicht_messen as M           # noqa: E402
import echtmengen_saat as SAAT           # noqa: E402
import echtmengen_messen as EM           # noqa: E402
import hellmodus_ansichten as HA         # noqa: E402
from tab_sweep import INIT               # noqa: E402

STAND_JS = r"""() => {
  const hell = (c) => {
    const m = /rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/.exec(c || '');
    if (!m) return null;
    const r = +m[1], g = +m[2], b = +m[3];
    return Math.round((0.2126 * r + 0.7152 * g + 0.0722 * b) / 255 * 1000) / 1000;
  };
  const W = window.innerWidth, H = window.innerHeight;
  let groesste = null, flaeche = 0, dunkel = 0;
  for (const e of document.querySelectorAll('div,section,main,body,header')) {
    const r = e.getBoundingClientRect();
    if (r.width < 40 || r.height < 40) continue;
    if (r.bottom < 0 || r.top > H) continue;
    const s = getComputedStyle(e);
    const bg = s.backgroundColor;
    if (!bg || bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent') continue;
    const sicht = Math.max(0, Math.min(r.bottom, H) - Math.max(r.top, 0))
                * Math.max(0, Math.min(r.right, W) - Math.max(r.left, 0));
    if (sicht > flaeche) { flaeche = sicht; groesste = {bg: bg, hell: hell(bg)}; }
    const h = hell(bg);
    if (h !== null && h < 0.35 && sicht > 8000) dunkel = Math.max(dunkel, sicht);
  }
  let modus = null;
  try { modus = localStorage.getItem('epk_theme'); } catch (e) {}
  const koerper = getComputedStyle(document.body).backgroundColor;
  return {modus: modus, koerper: koerper, koerper_hell: hell(koerper),
          groesste: groesste,
          dunkel_anteil: Math.round(dunkel / (W * H) * 1000) / 10,
          colorScheme: getComputedStyle(document.documentElement).colorScheme};
}"""

# Alle sichtbaren Bedienelemente, die nach einem Themenschalter aussehen.
SCHALTER_JS = r"""() => {
  const aus = [];
  for (const e of document.querySelectorAll('button,[role="button"]')) {
    const r = e.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    const t = ((e.innerText || '') + '|' + (e.getAttribute('title') || '')
               + '|' + (e.getAttribute('aria-label') || '')).toLowerCase();
    if (/hell|dunkel|dark|light|theme|auto|☀|🌙|🅰/.test(t)) {
      aus.push({text: (e.innerText || '').trim().slice(0, 24),
                titel: e.getAttribute('title'),
                aria: e.getAttribute('aria-label'),
                wh: [Math.round(r.width), Math.round(r.height)]});
    }
  }
  return aus;
}"""

KLICK_JS = r"""([text, titel, aria]) => {
  const e = [...document.querySelectorAll('button,[role="button"]')].find(x => {
    const r = x.getBoundingClientRect();
    if (!r.width || !r.height) return false;
    return (x.innerText || '').trim().slice(0, 24) === text
        && (x.getAttribute('title') || null) === titel
        && (x.getAttribute('aria-label') || null) === aria;
  });
  if (!e) return false;
  e.click();
  return true;
}"""


def _zeile(marke, s):
    g = s.get("groesste") or {}
    return ("   %-22s Modus=%-7s Koerper=%-22s (%.3f) | groesste Flaeche %s "
            "(%s) | dunkel %.1f %% | colorScheme=%s"
            % (marke, s.get("modus"), s.get("koerper"),
               s.get("koerper_hell") if s.get("koerper_hell") is not None else -1,
               g.get("bg"), g.get("hell"), s.get("dunkel_anteil"),
               s.get("colorScheme")))


def main(argv):
    from playwright.sync_api import sync_playwright
    breite = int(argv[0]) if argv else 390
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port,
                                      os.environ.get("EPK_INDEX", "index.html"))
    saat = SAAT.saat()
    bericht = {"breite": breite, "schritte": []}

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        # 🔴 Ausgangslage wie beim Nutzer: Betriebssystem DUNKEL, keine Wahl
        #    gespeichert. Alles andere misst einen Fall, den es nicht gibt.
        ctx = browser.new_context(viewport={"width": breite, "height": 844},
                                  device_scale_factor=1,
                                  is_mobile=breite < 600,
                                  has_touch=breite < 600,
                                  color_scheme="dark")
        # 🔴 OHNE ANMELDUNG MISST MAN DIE ANMELDESEITE. Der erste Lauf meldete
        #    "0 Themenschalter sichtbar" und nannte das selbst einen
        #    misslungenen Griff - richtig, aber der Grund war ein anderer als
        #    vermutet: die App stand auf dem Anmeldeschirm, weil mein Kontext
        #    keinen Nutzer gesetzt hatte. Dieselbe Vorbelegung wie in
        #    `hellmodus_ansichten.py`, nur OHNE `epk_theme`: die Wahl soll
        #    genau die sein, die der Nutzer vorfindet - keine.
        ctx.add_init_script(INIT)
        ctx.add_init_script(
            "try{localStorage.removeItem('epk_theme');"
            "var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
            "u.role='admin';u.monteurId='M1';u.name='Gerhard Steinbichler';"
            "u.rolle='Geschaeftsfuehrer';"
            "localStorage.setItem('epkolar_user',JSON.stringify(u));}catch(e){}")
        ctx.route("**/rest/v1/**", lambda r: r.abort())
        ctx.route("**/auth/v1/**", lambda r: r.abort())
        seite = ctx.new_page()
        try:
            seite.goto(url, wait_until="domcontentloaded")
            seite.wait_for_timeout(3800)
            EM._saeen(seite, saat, still=True)
            seite.wait_for_timeout(1200)

            start = seite.evaluate(STAND_JS)
            print("Breite %d px, Betriebssystem DUNKEL, keine gespeicherte "
                  "Wahl" % breite)
            print(_zeile("START", start))
            bericht["start"] = start

            schalter = seite.evaluate(SCHALTER_JS)
            # 🔴 AM TELEFON STECKT DER SCHALTER HINTER DEM MENUE. Der erste
            #    Lauf meldete "0 Themenschalter sichtbar" und nannte das
            #    selbst einen misslungenen Griff - richtig: bei 390 px ist die
            #    Kopfleiste eingeklappt. Wer hier nicht oeffnet, misst die
            #    Abwesenheit seines eigenen Blicks.
            menue_offen = False
            if not schalter and breite < 600:
                seite.evaluate(M.NAV_OEFFNEN_JS)
                seite.wait_for_timeout(700)
                schalter = seite.evaluate(SCHALTER_JS)
                menue_offen = True
                print("   (Menue geoeffnet, um den Schalter zu erreichen)")
            bericht["menue_noetig"] = menue_offen
            print("\n%d Themenschalter sichtbar:" % len(schalter))
            for s in schalter:
                print("   %r titel=%r aria=%r %sx%s"
                      % (s["text"], s["titel"], s["aria"], *s["wh"]))
            if not schalter:
                print("\U0001F534 KEIN Themenschalter sichtbar. Das ist kein "
                      "Ergebnis, das ist ein\n   misslungener Griff - "
                      "NICHT gemessen.")
                return 2

            k = schalter[0]
            for n in range(1, 5):
                ok = seite.evaluate(KLICK_JS, [k["text"], k["titel"], k["aria"]])
                if not ok:
                    print("   \U0001F534 Schalter nach Schritt %d nicht mehr "
                          "gefunden - NICHT gemessen." % n)
                    break
                seite.wait_for_timeout(900)
                s = seite.evaluate(STAND_JS)
                bericht["schritte"].append(s)
                print(_zeile("nach Tipp %d" % n, s))
                if s.get("modus") == "light":
                    hell_ok = (s.get("koerper_hell") or 0) > 0.6
                    print("\n   Modus steht auf LIGHT. Koerper %s -> %s"
                          % (s.get("koerper"),
                             "HELL (richtig)" if hell_ok
                             else "\U0001F534 IMMER NOCH DUNKEL"))
                    bericht["ergebnis"] = "hell" if hell_ok else "dunkel"
                    break
            else:
                print("   \U0001F534 Nach vier Tippen nie im Modus light.")
                bericht["ergebnis"] = "light nie erreicht"
        finally:
            ctx.close()
            browser.close()

    ziel = os.path.join(WURZEL, "docs", "befunde",
                        "HELLMODUS_SCHALTER_%d.json" % breite)
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps(bericht, ensure_ascii=False, indent=1))
    print("\ngeschrieben:", ziel)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
