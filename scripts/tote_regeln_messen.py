# -*- coding: utf-8 -*-
"""Greifen die drei verdaechtigen Stilregeln irgendwo - oder nirgends?

🔴 FRAGE 24. Am 27.09.2026 wurden `.ber-table`, `.badge` und das Sync-Banner
von 11 px auf 12 px gehoben - richtig gedacht, und vermutlich wirkungslos,
weil die Selektoren im Hauptdokument nichts treffen.

Die Doku nennt als NICHT gemessen: ob `.ber-table` frueher existiert hat und
umbenannt wurde. **Die Historie kann das nicht beantworten** - `index.html`
kam mit Commit 1eb4bfc bereits fertig ins Repo, die Regeln waren von Anfang
an da. Was davor war, steht hier nirgends.

Es gibt aber eine schaerfere Messung als Geschichte: **greift der Selektor
JETZT irgendwo?** Eine Regel, die in keiner Ansicht ein Element trifft, ist
tot - unabhaengig davon, was frueher einmal war.

🔴 SELBSTPROBE, und ohne sie waere jede Null wertlos: in dieselbe Seite wird
ein Element mit genau diesen Merkmalen EINGESETZT und muss gefunden werden.
Ein Zaehler, der auch den eingesetzten Koeder nicht sieht, meldet „trifft
nichts" fuer jede Regel der Welt.

🔴 UND EINE GEGENPROBE: eine Regel, die nachweislich GREIFT (`.header-row`),
laeuft mit. Findet der Zaehler auch die nicht, misst er gar nichts.

Aufruf:  python scripts/tote_regeln_messen.py [breite]
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

# Die Verdaechtigen, genau wie sie im Stilblock stehen.
VERDAECHTIG = {
    "ber-table": ".ber-table",
    "badge": ".badge",
    "sync-banner": '[style*="Änderungen warten"]',
    "sync-knopf": '[title*="Jetzt sync"]',
}
# 🔴 Die Gegenprobe: eine Regel, die nachweislich greift.
GEGENPROBE = {"header-row": ".header-row"}

ZAEHLEN_JS = r"""(wahlen) => {
  const aus = {};
  for (const [name, sel] of Object.entries(wahlen)) {
    try { aus[name] = document.querySelectorAll(sel).length; }
    catch (e) { aus[name] = 'FEHLER: ' + e.message; }
  }
  return aus;
}"""

KOEDER_EIN_JS = r"""() => {
  let z = document.getElementById('__toteprobe');
  if (z) z.remove();
  z = document.createElement('div');
  z.id = '__toteprobe';
  z.style.cssText = 'position:fixed;left:-9999px;top:0';
  const t = document.createElement('table');
  t.className = 'ber-table';
  const b = document.createElement('span');
  b.className = 'badge';
  b.textContent = 'x';
  const s = document.createElement('div');
  s.setAttribute('style', 'color:red');
  s.style.cssText += '';
  // Das Sync-Banner sucht im STYLE-Attribut nach dem Text - genau das wird
  // hier nachgestellt, damit der Koeder dieselbe Form hat wie die Regel.
  s.setAttribute('style', 'color:red;/*Änderungen warten*/');
  const k = document.createElement('button');
  k.setAttribute('title', 'Jetzt sync');
  z.appendChild(t); z.appendChild(b); z.appendChild(s); z.appendChild(k);
  (document.getElementById('root') || document.body).appendChild(z);
  return true;
}"""

KOEDER_AUS_JS = r"""() => {
  const z = document.getElementById('__toteprobe');
  if (z) z.remove();
  return !document.getElementById('__toteprobe');
}"""

ANSICHTEN = ["as_liste", "werkzeuge", "fahrzeuge", "mitarbeiter", "zeit",
             "plaene", "berichte", "auswertungen", "monatsabr", "chef"]


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
    alle_wahlen = dict(VERDAECHTIG)
    alle_wahlen.update(GEGENPROBE)
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
        seite.evaluate(KOEDER_EIN_JS)
        mit = seite.evaluate(ZAEHLEN_JS, alle_wahlen)
        seite.evaluate(KOEDER_AUS_JS)
        fehlt = [n for n in VERDAECHTIG if not isinstance(mit.get(n), int)
                 or mit.get(n) < 1]
        print("Selbstprobe mit eingesetztem Koeder: %r" % mit)
        if fehlt:
            print("\U0001F534 Der Zaehler findet den EINGESETZTEN Koeder "
                  "nicht fuer: %s.\n   Dann meldet er „trifft "
                  "nichts“ fuer jede Regel der Welt. NICHT GEMESSEN."
                  % ", ".join(fehlt))
            ctx.close()
            browser.close()
            return 2
        print("   \U0001F7E2 alle vier Selektoren finden ihren Koeder.\n")

        for kuerzel in ANSICHTEN:
            try:
                _navi(seite, kuerzel, breite)
            except Exception as e:      # noqa: BLE001
                print("   %-14s uebersprungen (%s)"
                      % (kuerzel, type(e).__name__))
                continue
            seite.wait_for_timeout(1300)
            bericht["ansichten"][kuerzel] = seite.evaluate(
                ZAEHLEN_JS, alle_wahlen)
        ctx.close()
        browser.close()

    if not bericht["ansichten"]:
        print("\U0001F534 KEINE Ansicht gemessen. Das ist kein Ergebnis.")
        return 2

    namen = sorted(alle_wahlen)
    print("%-14s %s" % ("Ansicht", "  ".join("%-11s" % n for n in namen)))
    summe = {n: 0 for n in namen}
    for k in sorted(bericht["ansichten"]):
        z = bericht["ansichten"][k]
        print("%-14s %s" % (k, "  ".join("%-11s" % z.get(n) for n in namen)))
        for n in namen:
            if isinstance(z.get(n), int):
                summe[n] += z[n]

    print("\n%-14s %s" % ("SUMME", "  ".join("%-11d" % summe[n]
                                             for n in namen)))
    # 🔴 GEGENPROBE: greift die Regel, von der wir wissen, dass sie greift?
    if summe.get("header-row", 0) < 1:
        print("\n\U0001F534 Auch `.header-row` trifft nirgends - und die "
              "greift nachweislich.\n   Dann misst dieser Lauf gar nichts, "
              "und die Nullen darueber belegen nichts.")
        return 2

    tot = [n for n in VERDAECHTIG if summe.get(n, 0) == 0]
    print("\n\U0001F7E2 Gegenprobe: `.header-row` trifft %d mal - der "
          "Zaehler misst." % summe["header-row"])
    if tot:
        print("\U0001F534 Diese Selektoren treffen in %d Ansichten "
              "NICHTS: %s\n   Eine Regel fuer ein Bauteil, das es nicht "
              "gibt, taeuscht den naechsten Leser -\n   sie sieht aus wie "
              "eine Zusage."
              % (len(bericht["ansichten"]), ", ".join(tot)))
    lebt = [n for n in VERDAECHTIG if summe.get(n, 0) > 0]
    if lebt:
        print("\U0001F7E2 Diese treffen doch etwas: %s"
              % ", ".join("%s (%d)" % (n, summe[n]) for n in lebt))

    ziel = os.path.join(WURZEL, "docs", "befunde", "TOTE_REGELN.json")
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps(bericht, ensure_ascii=False, indent=1))
    print("\ngeschrieben:", ziel)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
