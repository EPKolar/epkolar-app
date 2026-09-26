# -*- coding: utf-8 -*-
"""Reagieren die 38 window.innerWidth-Stellen auf eine Drehung?

DER BEFUND, DER GEMESSEN WERDEN SOLL
────────────────────────────────────
In v3.9.940 wurden 38 Stellen von `window.innerWidth<600` auf
`window.innerWidth<BP_MOB` umbenannt. Das ist reine Benennung. Die Frage
darunter ist eine andere und wurde bisher NICHT gemessen:

    `window.innerWidth` wird beim ZEICHNEN gelesen. React zeichnet nicht neu,
    wenn sich das Fenster aendert - es zeichnet neu, wenn sich Zustand aendert.
    Also koennte eine Ueberschrift nach dem Drehen des Telefons auf der
    Desktop-Groesse stehenbleiben, bis irgendein anderer Zustand sie zufaellig
    mitnimmt.

Die 28 Stellen mit `ww<BP_MOB` sind davon NICHT betroffen: `ww` kommt aus
einem Haken, der auf resize hoert, und eine Zustandsaenderung zeichnet neu.
Genau das macht den Vergleich moeglich.

WIE GEMESSEN WIRD
─────────────────
1. Bei 1440 px laden, ausmessen.
2. Das Fenster auf 390 px verkleinern - OHNE neu zu laden und ohne zu klicken,
   damit kein Zustand wechselt und React nicht aus einem anderen Grund
   zeichnet.
3. Dieselben Elemente erneut ausmessen.

Gemessen wird die BERECHNETE Schriftgroesse (getComputedStyle), nicht der
Quelltext. Ein Wert, der sich nicht aendert, ist der Befund.

DER KOEDER
──────────
Mindestens ein Element, dessen Groesse an `ww` haengt, MUSS sich aendern.
Aendert sich gar nichts, dann hat die Verkleinerung nicht gewirkt oder die
Messung greift daneben - und die Aussage ueber die 38 Stellen waere wertlos.
Zusaetzlich wird innerWidth selbst gemeldet: steht dort nach dem Verkleinern
noch 1440, hat Playwright nicht verkleinert und die ganze Messung ist nichtig.

WAS DIESE MESSUNG NICHT ABDECKT
───────────────────────────────
Ein echtes Drehen eines Telefons ist mehr als ein resize: es kann die App
durch ein orientationchange-Ereignis oder durch das Wiederanzeigen der Seite
ohnehin zum Neuzeichnen bringen. Diese Messung sagt also: "ohne weiteren
Anlass bleibt der Wert stehen" - nicht: "auf jedem Geraet bleibt er stehen".

AUFRUF
──────
    python scripts/innerwidth_reaktion_messen.py
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import mob_ansicht_messen as M  # noqa: E402

MESS_JS = """() => {
  const aus = [];
  document.querySelectorAll('h2').forEach((el, i) => {
    const r = el.getBoundingClientRect();
    if (r.width <= 0 && r.height <= 0) return;
    aus.push({art: 'h2', nr: i,
              text: String(el.innerText || '').replace(/\\s+/g, ' ').slice(0, 40),
              fontSize: getComputedStyle(el).fontSize});
  });
  // Gitter, die im Quelltext an der Schwelle haengen - beide Schreibweisen.
  document.querySelectorAll('[style*="grid-template-columns"], div').forEach((el) => {
    const cs = getComputedStyle(el);
    if (cs.display !== 'grid') return;
    const r = el.getBoundingClientRect();
    if (r.width < 200) return;
    aus.push({art: 'grid',
              klasse: String(el.className || '').slice(0, 30),
              spalten: cs.gridTemplateColumns.slice(0, 60),
              breit: Math.round(r.width)});
  });
  return {elemente: aus, innerWidth: window.innerWidth,
          // Der Koeder: die Fussleiste haengt an der CSS-Regel und muss
          // sich bei 390 px anders verhalten als bei 1440.
          leisteAnzeige: (() => {
            const b = document.querySelector('.pf-hauptnav, .bottom-nav');
            return b ? getComputedStyle(b).position + '/' +
                       Math.round(b.getBoundingClientRect().width) : 'keine';
          })()};
}"""


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt.")
        return 2

    port = M._server()
    datei = os.environ.get("EPK_INDEX", "index.html")
    url = "http://127.0.0.1:%d/%s" % (port, datei)
    print("Gemessen wird:", url)

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        ctx.add_init_script(M.INIT)
        ctx.add_init_script(
            "try{var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
            "u.role='admin';u.monteurId='M1';"
            "localStorage.setItem('epkolar_user',JSON.stringify(u));}catch(e){}")
        ctx.route("**/rest/v1/**", lambda r: r.abort())
        ctx.route("**/auth/v1/**", lambda r: r.abort())
        seite = ctx.new_page()
        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(4500)

        # Die Startansicht fuehrt KEINE h2 - gemessen: 0 Stueck. Also erst in
        # eine Ansicht wechseln, die eine hat. Geklickt wird nach SICHTBAREM
        # TEXT, nicht nach aria-label: in v3.9.937 ist die Beschriftung der
        # Hauptnavigation von aria-label auf sichtbaren Text umgestellt worden,
        # und ein Klickpfad nach aria-label greift seither ins Leere.
        ZIEL_JS = """(namen) => {
          const k = [...document.querySelectorAll('button, a, [role="button"]')];
          for (const n of namen) {
            const t = k.find(b => (b.innerText || '').trim() === n
                                  || (b.getAttribute('aria-label') || '') === n);
            if (t) { t.click(); return n; }
          }
          return null;
        }"""
        gewaehlt = None
        for versuch in (["Auswertungen"], ["Fahrzeuge"], ["Mitarbeiter"],
                        ["Werkzeuge"], ["Mehr"]):
            r = seite.evaluate(ZIEL_JS, versuch)
            if not r:
                continue
            seite.wait_for_timeout(1800)
            if seite.evaluate("() => document.querySelectorAll('h2').length") > 0:
                gewaehlt = r
                break
        print("   Ansicht gewaehlt: %s" % (gewaehlt or "KEINE - keine h2 erreicht"))

        vorher = seite.evaluate(MESS_JS)
        print("\n-- bei 1440 px")
        print("   innerWidth: %d | Leiste: %s"
              % (vorher["innerWidth"], vorher["leisteAnzeige"]))
        print("   %d Elemente erfasst" % len(vorher["elemente"]))

        # NUR verkleinern. Kein Klick, kein Nachladen, keine Navigation -
        # sonst zeichnet React aus einem anderen Grund und die Messung sagt
        # nichts ueber die Schwelle.
        seite.set_viewport_size({"width": 390, "height": 880})
        seite.wait_for_timeout(2500)
        nachher = seite.evaluate(MESS_JS)
        print("\n-- nach dem Verkleinern auf 390 px (ohne Neuladen, ohne Klick)")
        print("   innerWidth: %d | Leiste: %s"
              % (nachher["innerWidth"], nachher["leisteAnzeige"]))
        print("   %d Elemente erfasst" % len(nachher["elemente"]))
        browser.close()

    print("\n" + "=" * 68)
    if nachher["innerWidth"] >= 1000:
        print("Die Verkleinerung hat nicht gewirkt (innerWidth ist %d)."
              % nachher["innerWidth"])
        print("Damit ist diese Messung nichtig. ABBRUCH.")
        return 1

    # ── Der Koeder: hat sich UEBERHAUPT etwas geaendert? ──────────────────
    h2_vor = {e["nr"]: e for e in vorher["elemente"] if e["art"] == "h2"}
    h2_nach = {e["nr"]: e for e in nachher["elemente"] if e["art"] == "h2"}
    gemeinsam = sorted(set(h2_vor) & set(h2_nach))

    leiste_anders = vorher["leisteAnzeige"] != nachher["leisteAnzeige"]
    gitter_vor = [e["spalten"] for e in vorher["elemente"] if e["art"] == "grid"]
    gitter_nach = [e["spalten"] for e in nachher["elemente"] if e["art"] == "grid"]
    gitter_anders = gitter_vor != gitter_nach

    print("KOEDER - hat die Verkleinerung ueberhaupt gewirkt?")
    print("   Fussleiste anders: %s (%s -> %s)"
          % ("JA" if leiste_anders else "NEIN",
             vorher["leisteAnzeige"], nachher["leisteAnzeige"]))
    print("   Gitterspalten anders: %s (%d bzw. %d Gitter)"
          % ("JA" if gitter_anders else "NEIN", len(gitter_vor), len(gitter_nach)))
    if not (leiste_anders or gitter_anders):
        print("   NICHTS hat sich geaendert - auch nicht das, was sich aendern")
        print("   MUSS. Dann misst diese Sonde nicht. ABBRUCH.")
        return 1

    if not gemeinsam:
        print("\nKeine gemeinsam vorhandene Ueberschrift - nicht gemessen.")
        return 1

    stehen = [nr for nr in gemeinsam
              if h2_vor[nr]["fontSize"] == h2_nach[nr]["fontSize"]]
    gewandert = [nr for nr in gemeinsam
                 if h2_vor[nr]["fontSize"] != h2_nach[nr]["fontSize"]]
    print("\nUEBERSCHRIFTEN (h2), %d gemeinsam vorhanden:" % len(gemeinsam))
    print("   Groesse GEWANDERT : %d" % len(gewandert))
    print("   Groesse STEHEN GEBLIEBEN: %d" % len(stehen))
    for nr in gemeinsam[:12]:
        print("      [%2d] %-40s %6s -> %6s  %s"
              % (nr, h2_vor[nr]["text"], h2_vor[nr]["fontSize"],
                 h2_nach[nr]["fontSize"],
                 "steht" if nr in stehen else "wandert"))

    if stehen and not gewandert:
        print("\nBEFUND: keine einzige Ueberschrift hat ihre Groesse geaendert,")
        print("obwohl die Verkleinerung gewirkt hat (siehe Koeder). Die Stellen")
        print("lesen window.innerWidth beim Zeichnen, und ohne Zustandswechsel")
        print("zeichnet React nicht neu. Auf dem Telefon heisst das: nach dem")
        print("Drehen steht die Desktop-Groesse, bis irgendetwas anderes ein")
        print("Neuzeichnen ausloest.")
        return 1
    if stehen:
        print("\nBEFUND, TEILWEISE: %d Ueberschriften wandern, %d bleiben stehen."
              % (len(gewandert), len(stehen)))
        print("Die stehengebliebenen lesen die Breite beim Zeichnen.")
        return 1
    print("\nAlle gemessenen Ueberschriften haben ihre Groesse geaendert. Die")
    print("Stellen werden also neu gezeichnet - in DIESEM Aufbau. Was das nicht")
    print("abdeckt, steht im Dateikopf.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
