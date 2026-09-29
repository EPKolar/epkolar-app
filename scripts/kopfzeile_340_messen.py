# -*- coding: utf-8 -*-
"""Was traegt die Kopfzeile bei 340 px - und wirkt die Icon-Only-Regel?

🔴 FRAGE 22. Im Stilblock steht fuer sehr schmale Telefone:

    .header-row .mob-stack button { font-size: 0 !important; }
    .header-row .mob-stack button::first-letter,
    .header-row .mob-stack button { font-size: 16px !important; }

Gleicher Selektor, drei Zeilen spaeter, gleiche Spezifitaet - **die Null
verliert**. Die Absicht („Text weg, Symbol bleibt") hat vermutlich nie
gewirkt.

Der bisherige Befund war am QUELLTEXT gelesen. Hier wird am Schirm gemessen,
und zwar das, was in der Doku ausdruecklich als NICHT gemessen steht: wie
viele Knoepfe die Kopfzeile bei 340 px traegt, wie breit sie zusammen sind,
ob die Zeile ueberlaeuft - und ob die Knoepfe einen Namen haetten, wenn man
ihnen den Text naehme.

🔴 SELBSTPROBE, und sie ist hier der ganze Punkt: der Lauf muss BELEGEN, dass
der `max-width: 340px`-Zweig ueberhaupt aktiv ist. Ein Melder, der bei 390 px
misst und „die Regel wirkt nicht" meldet, hat recht und sagt nichts. Geprueft
wird an einer ANDEREN Angabe desselben Blocks (`.header-row h2` auf 16px),
die nirgends sonst gesetzt wird.

Aufruf:  python scripts/kopfzeile_340_messen.py [breite]
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
# 🔴 Die Ansicht muss GESUCHT werden. Der erste Lauf landete auf einer
#    Ansicht ohne `.header-row` und meldete "keine .header-row" - das sah aus
#    wie ein Befund ueber die Regel und war eine Aussage ueber die Ansicht.
#    Siehe die Hausregel „jede Messung nennt ihren UMFANG".
KANDIDATEN = ["as_liste", "werkzeuge", "fahrzeuge", "mitarbeiter", "home",
              "zeit", "plaene"]


def _navi(seite, kuerzel, breite):
    for modul, name, argzahl in GRUPPEN:
        if kuerzel in getattr(modul, "ANSICHTEN", {}):
            f = getattr(modul, name)
            return (f(seite, kuerzel, breite, []) if argzahl == 4
                    else f(seite, kuerzel, breite))
    raise SystemExit("unbekannte Ansicht: %s" % kuerzel)

ZWEIG_AKTIV_JS = r"""() => {
  // Die Selbstprobe: eine ANDERE Angabe desselben Medienblocks.
  const h2 = document.querySelector('.header-row h2');
  const st = h2 ? getComputedStyle(h2).fontSize : null;
  return {h2_gefunden: !!h2, h2_groesse: st,
          fenster: window.innerWidth,
          passt: !!window.matchMedia('(max-width: 340px)').matches};
}"""

MESSEN_JS = r"""() => {
  const zeile = document.querySelector('.header-row');
  if (!zeile) return {fehler: 'keine .header-row'};
  const stapel = zeile.querySelector('.mob-stack');
  const knoepfe = [...(stapel || zeile).querySelectorAll('button')]
    .filter(b => { const r = b.getBoundingClientRect();
                   return r.width > 0 && r.height > 0; });
  const r0 = zeile.getBoundingClientRect();
  return {
    fenster: window.innerWidth,
    zeile_breite: Math.round(r0.width),
    zeile_laeuft_ueber: zeile.scrollWidth > zeile.clientWidth + 1,
    ueberlauf_px: zeile.scrollWidth - zeile.clientWidth,
    dokument_laeuft_ueber:
      document.documentElement.scrollWidth > window.innerWidth + 1,
    knoepfe: knoepfe.map(b => {
      const r = b.getBoundingClientRect();
      const cs = getComputedStyle(b);
      const txt = (b.innerText || '').replace(/\s+/g, ' ').trim();
      // Was bliebe uebrig, wenn der Text wegfiele? Emoji und Symbole.
      const ohneWort = txt.replace(
        /[\p{L}\p{N}]/gu, '').replace(/\s+/g, '').trim();
      return {text: txt.slice(0, 28),
              schrift: cs.fontSize,
              breite: Math.round(r.width * 10) / 10,
              hoehe: Math.round(r.height * 10) / 10,
              aria: b.getAttribute('aria-label'),
              titel: b.getAttribute('title'),
              zeichen_bleibt: ohneWort.slice(0, 6)};
    }),
    summe_breite: Math.round(knoepfe.reduce(
      (s, b) => s + b.getBoundingClientRect().width, 0))};
}"""


def main(argv):
    from playwright.sync_api import sync_playwright
    breite = int(argv[0]) if argv else 340
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port,
                                      os.environ.get("EPK_INDEX", "index.html"))
    saat = SAAT.saat()

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = EM._ctx(browser, breite)
        seite = ctx.new_page()
        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(3800)
        EM._saeen(seite, saat, still=True)
        seite.wait_for_timeout(1500)
        probe = seite.evaluate(ZWEIG_AKTIV_JS)
        # 🔴 ALLE Kandidaten, nicht der erste Treffer. Der erste Entwurf
        #    hoerte auf, sobald er eine `.header-row` gefunden hatte - das
        #    waere eine Aussage ueber EINE Ansicht gewesen, verkauft als
        #    Aussage ueber die Kopfzeile. Hausregel: jede Messung nennt
        #    ihren UMFANG.
        alle = {}
        erst = seite.evaluate(MESSEN_JS)
        if not erst.get("fehler"):
            alle["Startansicht"] = erst
        for kuerzel in KANDIDATEN:
            try:
                _navi(seite, kuerzel, breite)
            except Exception:          # noqa: BLE001
                continue
            seite.wait_for_timeout(1400)
            e = seite.evaluate(MESSEN_JS)
            if not e.get("fehler"):
                alle[kuerzel] = e
        ctx.close()
        browser.close()
    erg = max(alle.values(), key=lambda e: len(e["knoepfe"])) if alle else \
        {"fehler": "keine .header-row in keiner Ansicht"}
    gefunden_in = next((k for k, v in alle.items() if v is erg), "-")

    # 🔴 SELBSTPROBE ZUERST. Ein Melder, der bei der falschen Breite misst,
    #    meldet "die Regel wirkt nicht" - und hat recht, ohne etwas zu sagen.
    print("Selbstprobe: Fenster %s px, (max-width:340px) trifft: %s, "
          "h2 = %s" % (probe.get("fenster"), probe.get("passt"),
                       probe.get("h2_groesse")))
    if breite <= 340 and not probe.get("passt"):
        print("\U0001F534 Der 340px-Zweig ist NICHT aktiv, obwohl das Fenster "
              "%s px breit ist.\n   Dann misst dieser Lauf einen anderen "
              "Zweig. NICHT GEMESSEN." % probe.get("fenster"))
        return 2
    if breite <= 340 and probe.get("h2_groesse") not in ("16px", None):
        print("\U0001F534 `.header-row h2` ist %s statt 16px - die Angaben "
              "desselben Blocks\n   greifen nicht. Dann belegt dieser Lauf "
              "nichts ueber die Regel daneben." % probe.get("h2_groesse"))
        return 2
    print("   \U0001F7E2 der Zweig ist aktiv.\n")

    if erg.get("fehler"):
        print("\U0001F534 NICHT GEMESSEN: in KEINER der %d gepruefeten "
              "Ansichten gibt es eine\n   `.header-row` (%s). Entweder heisst "
              "die Klasse anders, oder der Waehler\n   greift daneben - eine "
              "Aussage ueber die Regel ist das nicht."
              % (len(KANDIDATEN), ", ".join(KANDIDATEN)))
        return 2
    k = erg["knoepfe"]
    print("Ansichten mit einer `.header-row`: %d von %d gepruefeten"
          % (len(alle), len(KANDIDATEN) + 1))
    for name, e in sorted(alle.items(),
                          key=lambda x: -len(x[1]["knoepfe"])):
        print("   %-14s %d Knoepfe, zusammen %4d px, Ueberlauf %+d px"
              % (name, len(e["knoepfe"]), e["summe_breite"],
                 e["ueberlauf_px"]))
    print("\nDie vollste Ansicht ist %s:" % gefunden_in)
    print("Kopfzeile bei %d px: %d Knoepfe, zusammen %d px breit "
          "(Zeile %d px)" % (erg["fenster"], len(k), erg["summe_breite"],
                             erg["zeile_breite"]))
    print("   Zeile laeuft ueber : %s (%+d px)"
          % (erg["zeile_laeuft_ueber"], erg["ueberlauf_px"]))
    print("   Dokument quer      : %s" % erg["dokument_laeuft_ueber"])
    print()
    stumm = []
    for b in k:
        print("   %-28r %6s  %5.1f x %4.1f px  Zeichen=%r aria=%r"
              % (b["text"], b["schrift"], b["breite"], b["hoehe"],
                 b["zeichen_bleibt"], b["aria"]))
        if not b["zeichen_bleibt"] and not (b["aria"] or b["titel"]):
            stumm.append(b["text"])

    null_wirkt = all(b["schrift"] == "0px" for b in k) if k else False
    print()
    print("Die Icon-Only-Regel wirkt: %s" % ("ja" if null_wirkt else
                                             "\U0001F534 NEIN"))
    if stumm:
        print("\U0001F534 %d Knoepfe haetten OHNE Text keinen Namen mehr "
              "(kein Symbol, kein\n   aria-label, kein title): %s\n"
              "   Wer die Absicht herstellen will, muss ihnen VORHER einen "
              "Namen geben -\n   sonst sind sie fuer eine Vorlesehilfe "
              "stumm." % (len(stumm), stumm))

    ziel = os.path.join(WURZEL, "docs", "befunde",
                        "KOPFZEILE_%d.json" % erg["fenster"])
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps(erg, ensure_ascii=False, indent=1))
    print("\ngeschrieben:", ziel)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
