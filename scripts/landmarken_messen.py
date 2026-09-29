# -*- coding: utf-8 -*-
"""Hat die Seite einen Bereich, zu dem eine Vorlesehilfe springen kann?

🔴 GEFUNDEN AM 29.09.2026, und es stand auf keiner Liste. Im ganzen Programm
gab es **keinen einzigen Landmark**: kein `<main>`, kein `<nav>`, keine
`role="main"`, nichts. Gemessen am Quelltext, alle Schreibweisen:

    createElement('main'      0
    role: "main"              0
    <main                     0
    role: navigation/banner/  0
        contentinfo/region

Fuer eine Vorlesehilfe heisst das: es gibt keine Stelle, zu der man springen
kann, und keine Auskunft darueber, in welchem Bereich man gerade ist. Man
haengt am Anfang fest und muss durch die ganze Kopfzeile tabben, auf jeder
Ansicht neu.

🔴 DAS IST NICHT FRAGE 14. Dort geht es um eine sichtbare UEBERSCHRIFT, und
eine zu erfinden hiesse, an der auffaelligsten Stelle der Seite etwas zu
behaupten, das niemand entschieden hat. Ein `<main>` ist unsichtbar,
behauptet nichts und braucht keinen Namen - die Norm verlangt ihn nicht.

WAS HIER GEMESSEN WIRD: wie viele Landmarks jede Ansicht traegt, und ob es
genau EIN `<main>` gibt. Mehr als eines ist ein Fehler, keines auch.

🔴 SELBSTPROBE: in dieselbe Seite wird ein zweites `<main>` EINGESETZT und
muss gefunden werden. Ein Zaehler, der auch das nicht sieht, meldet fuer
jede Seite der Welt "genau eines".

Aufruf:  python scripts/landmarken_messen.py [breite]
"""
import io
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
WURZEL = os.path.dirname(HIER)

import mob_ansicht_messen as M           # noqa: E402
import b3_vier_ansichten_messen as B     # noqa: E402
import b3_stufen_8_11_messen as S        # noqa: E402
import b3_stufen_12_15_messen as B12     # noqa: E402
import echtmengen_saat as SAAT           # noqa: E402
import echtmengen_messen as EM           # noqa: E402

GRUPPEN = [(B, "_navigieren", 3), (S, "_navigieren8", 4),
           (B12, "_navigieren12", 4)]
ANSICHTEN = ["as_liste", "werkzeuge", "fahrzeuge", "mitarbeiter", "zeit",
             "plaene", "berichte", "auswertungen", "monatsabr", "chef",
             "baupro", "einstell"]

ZAEHLEN_JS = r"""() => {
  const z = sel => document.querySelectorAll(sel).length;
  return {
    main: z('main, [role="main"]'),
    nav: z('nav, [role="navigation"]'),
    banner: z('header, [role="banner"]'),
    fuss: z('footer, [role="contentinfo"]'),
    main_leer: [...document.querySelectorAll('main, [role="main"]')]
      .filter(m => (m.innerText || '').trim().length < 20).length,
    // 🔴 Die entscheidende Zahl fuer die Frage, ob `nav` eine NAMENSFRAGE
    //    ist: sind je Ansicht mehrere Navigationsleisten SICHTBAR? Wenn
    //    immer nur eine, genuegt ein <nav> ohne Namen und es gibt nichts zu
    //    entscheiden. Sind es mehrere, braucht jede einen Namen - und den
    //    erfindet kein Skript.
    tabbars: [...document.querySelectorAll('.tab-bar')]
      .filter(e => { const r = e.getBoundingClientRect();
                     return r.width > 0 && r.height > 0; }).length,
    tabbar_texte: [...document.querySelectorAll('.tab-bar')]
      .filter(e => { const r = e.getBoundingClientRect();
                     return r.width > 0 && r.height > 0; })
      .map(e => (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60))};
}"""

KOEDER_EIN_JS = r"""() => {
  let z = document.getElementById('__lmprobe');
  if (z) z.remove();
  z = document.createElement('main');
  z.id = '__lmprobe';
  z.style.cssText = 'position:fixed;left:-9999px;top:0';
  z.textContent = 'Koeder-Bereich mit genug Text, um nicht leer zu sein.';
  document.body.appendChild(z);
  return true;
}"""

KOEDER_AUS_JS = r"""() => {
  const z = document.getElementById('__lmprobe');
  if (z) z.remove();
  return !document.getElementById('__lmprobe');
}"""


def _navi(seite, kuerzel, breite):
    for modul, name, argzahl in GRUPPEN:
        if kuerzel in getattr(modul, "ANSICHTEN", {}):
            f = getattr(modul, name)
            return (f(seite, kuerzel, breite, []) if argzahl == 4
                    else f(seite, kuerzel, breite))
    raise SystemExit("unbekannte Ansicht: %s" % kuerzel)


def main(argv):
    from playwright.sync_api import sync_playwright
    breite = int(argv[0]) if argv else 1440
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port,
                                      os.environ.get("EPK_INDEX", "index.html"))
    saat = SAAT.saat()
    bericht = {"breite": breite, "ansichten": {}}

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = EM._ctx(browser, breite)
        seite = ctx.new_page()
        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(3800)
        EM._saeen(seite, saat, still=True)
        seite.wait_for_timeout(1500)

        # 🔴 SELBSTPROBE ZUERST.
        ohne = seite.evaluate(ZAEHLEN_JS)["main"]
        seite.evaluate(KOEDER_EIN_JS)
        mit = seite.evaluate(ZAEHLEN_JS)["main"]
        seite.evaluate(KOEDER_AUS_JS)
        print("Selbstprobe: ohne Koeder %d `main`, mit Koeder %d"
              % (ohne, mit))
        if mit != ohne + 1:
            print("\U0001F534 Der Zaehler sieht das EINGESETZTE `main` nicht "
                  "(%d -> %d).\n   Dann meldet er fuer jede Seite der Welt "
                  "dieselbe Zahl. NICHT GEMESSEN." % (ohne, mit))
            ctx.close()
            browser.close()
            return 2
        print("   \U0001F7E2 der Zaehler sieht ein zusaetzliches `main`.\n")

        ctx.close()

        # 🔴 JE ANSICHT EIN FRISCHER KONTEXT. Der erste Lauf navigierte in
        #    EINER Sitzung durch alle Ansichten und meldete: sieben ohne
        #    `main`. Die Reihenfolge verriet den Fehler - ALLE Nullen kamen
        #    NACH `plaene`, und das betritt ein Projekt. Die Sitzung blieb
        #    danach in der Projekthuelle. Das waere eine Aussage ueber die
        #    Navigation gewesen, verkauft als Aussage ueber die Ansichten.
        #    Der Preis sind rund zehn Sekunden je Ansicht; er ist der Grund,
        #    warum zwei Messungen ueberhaupt vergleichbar sind.
        for kuerzel in ANSICHTEN:
            ctx = EM._ctx(browser, breite)
            seite = ctx.new_page()
            try:
                seite.goto(url, wait_until="domcontentloaded")
                seite.wait_for_timeout(3500)
                EM._saeen(seite, saat, still=True)
                _navi(seite, kuerzel, breite)
                seite.wait_for_timeout(1300)
                bericht["ansichten"][kuerzel] = seite.evaluate(ZAEHLEN_JS)
            except Exception as e:     # noqa: BLE001
                print("   %-14s uebersprungen (%s)"
                      % (kuerzel, type(e).__name__))
            finally:
                ctx.close()
        browser.close()

    if not bericht["ansichten"]:
        print("\U0001F534 KEINE Ansicht gemessen. Das ist kein Ergebnis.")
        return 2

    print("%-14s %-6s %-5s %-7s %-6s %-10s %s"
          % ("Ansicht", "main", "nav", "banner", "fuss", "main leer",
             "sichtbare tab-bars"))
    schief = []
    for k in sorted(bericht["ansichten"]):
        z = bericht["ansichten"][k]
        print("%-14s %-6d %-5d %-7d %-6d %-10d %d  %s"
              % (k, z["main"], z["nav"], z["banner"], z["fuss"],
                 z["main_leer"], z.get("tabbars", -1),
                 " | ".join(t[:34] for t in (z.get("tabbar_texte") or []))))
        if z["main"] != 1:
            schief.append("%s hat %d `main` statt genau einem"
                          % (k, z["main"]))
        if z["main_leer"]:
            schief.append("%s hat ein `main` mit fast keinem Text - dann "
                          "springt man ins Leere" % k)

    ziel = os.path.join(WURZEL, "docs", "befunde", "LANDMARKEN.json")
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps(bericht, ensure_ascii=False, indent=1))
    print()
    if schief:
        print("\U0001F534 %d Befunde:" % len(schief))
        for s in schief:
            print("   " + s)
        print("\ngeschrieben:", ziel)
        return 1
    print("\U0001F7E2 Jede der %d Ansichten hat genau EIN `main`, und es "
          "traegt Inhalt." % len(bericht["ansichten"]))
    print("geschrieben:", ziel)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
