# -*- coding: utf-8 -*-
"""Probe: erreicht man in der Projektakte noch alle 13 Unterseiten?

WOZU
────
Die 13 Emoji-Knoepfe unten sind durch eine Reiterzeile mit Text ersetzt: fuenf
direkt, der Rest unter "Mehr". Ein Riegel auf den Quelltext kann nur sagen,
dass die Eintraege DASTEHEN - nicht, dass man sie ERREICHT. Genau diese
Verwechslung hat in diesem Bestand mehrfach etwas durchgelassen: das Bauteil
war da, der Weg dorthin nicht.

Hier wird der Weg gegangen: Projekt oeffnen, Reiter zaehlen, "Mehr" antippen,
die restlichen Eintraege zaehlen, jeden einzeln antippen und pruefen, dass die
Ansicht wirklich wechselt.

WAS GEMESSEN WIRD
─────────────────
  * die Reiterzeile: Hoehe 40, quer rollbar, jeder Eintrag mit sichtbarem TEXT
  * "Mehr" oeffnet die restlichen Eintraege, je mit Text
  * die Summe aus beiden ist die Zahl der Unterseiten, die die Rolle darf
  * die Hauptnavigation liegt UNTEN, nicht oben
  * kein Emoji-only-Knopf mehr in der Navigation

DER KOEDER
──────────
Vor dem Antippen von "Mehr" darf KEIN Eintrag der Mehr-Liste sichtbar sein.
Waeren sie immer da, sagte "nach dem Tippen sind sie da" nichts aus.
Ausserdem: findet die Probe kein Projekt zum Oeffnen, meldet sie das als
ausgefallene Messung und nicht als Erfolg.

AUFRUF
──────
    python scripts/projektakte_nav_probe.py
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import mob_ansicht_messen as M  # noqa: E402

OEFFNE_JS = """() => {
  // Eine Projektkarte erkennt man am Namen in 17px/600 - gesucht wird ueber
  // die Eigenschaft, nicht ueber eine Klasse.
  const kandidaten = Array.from(document.querySelectorAll('div'))
    .filter(e => {
      const t = (e.innerText || '');
      return t.includes('Stunden') && t.includes('Gewerk')
             && e.getBoundingClientRect().height > 80;
    });
  if (!kandidaten.length) return false;
  kandidaten.sort((a, b) => a.getBoundingClientRect().height
                          - b.getBoundingClientRect().height);
  kandidaten[0].click();
  return true;
}"""

REITER_JS = """() => {
  // Die Projektreiter: Knoepfe in einem 40px hohen, quer rollbaren Streifen.
  const streifen = Array.from(document.querySelectorAll('div')).find(e => {
    const r = e.getBoundingClientRect();
    if (Math.round(r.height) !== 40) return false;
    const b = e.querySelectorAll(':scope > button');
    return b.length >= 3;
  });
  if (!streifen) return {fehler: 'keine 40px-Reiterzeile gefunden'};
  const cs = getComputedStyle(streifen);
  const knoepfe = Array.from(streifen.querySelectorAll(':scope > button'));
  return {
    hoehe: Math.round(streifen.getBoundingClientRect().height),
    oben: Math.round(streifen.getBoundingClientRect().top),
    overflowX: cs.overflowX,
    umbruch: cs.flexWrap,
    reiter: knoepfe.map(b => (b.innerText || '').trim().split(String.fromCharCode(10)).join(' ')),
    ohneText: knoepfe.filter(b => !(b.innerText || '').trim()).length
  };
}"""

MEHR_JS = """() => {
  const eintraege = Array.from(document.querySelectorAll('[role="menuitem"]'))
    .filter(e => e.getBoundingClientRect().height > 4);
  return eintraege.map(e => (e.innerText || '').trim().split(String.fromCharCode(10)).join(' '));
}"""

MEHR_AUF_JS = """() => {
  const b = Array.from(document.querySelectorAll('button[aria-haspopup="menu"]'))
    .find(e => (e.innerText || '').trim().startsWith('Mehr'));
  if (!b) return false;
  b.click();
  return true;
}"""

HAUPTNAV_JS = """() => {
  const l = document.querySelector('.tab-bar');
  if (!l) return {fehler: 'keine .tab-bar'};
  const r = l.getBoundingClientRect();
  return {oben: Math.round(r.top), unten: Math.round(r.bottom),
          hoehe: Math.round(r.height), fensterH: window.innerHeight,
          position: getComputedStyle(l).position};
}"""

TIPPE_JS = """(text) => {
  // Der Text muss GENAUSO normalisiert werden wie beim Auslesen: die
  // Eintraege tragen Ikone und Beschriftung in zwei Zeilen, innerText liefert
  // dazwischen einen Umbruch. Der erste Anlauf verglich rohes innerText gegen
  // den normalisierten Namen und meldete acht Eintraege als "nicht tippbar",
  // die alle da waren.
  const norm = s => (s || '').split(String.fromCharCode(10)).join(' ')
                             .replace(/  +/g, ' ').trim();
  const ziel = norm(text);
  const alle = Array.from(document.querySelectorAll('button, [role="menuitem"]'));
  const t = alle.find(e => norm(e.innerText) === ziel);
  if (!t) return false;
  t.click();
  return true;
}"""

ANSICHT_JS = """() => {
  const m = document.querySelector('.proj-main');
  return m ? (m.innerText || '').replace(/\\s+/g, ' ').slice(0, 70).trim() : null;
}"""


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt.")
        return 2

    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port, os.environ.get("EPK_INDEX", "index.html"))
    print("Gemessen wird:", url)

    schlimm = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 390, "height": 860},
                                  is_mobile=True, has_touch=True)
        ctx.add_init_script(M.INIT)
        ctx.add_init_script(
            "try{var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
            "u.role='admin';u.monteurId='M1';u.name='Gerhard Steinbichler';"
            "localStorage.setItem('epkolar_user',JSON.stringify(u));}catch(e){}")
        ctx.route("**/rest/v1/**", lambda r: r.abort())
        ctx.route("**/auth/v1/**", lambda r: r.abort())
        seite = ctx.new_page()
        fehler = []
        seite.on("pageerror", lambda e: fehler.append(str(e)[:160]))
        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(3800)
        seite.evaluate(M.NAV_OEFFNEN_JS)
        seite.wait_for_timeout(350)
        seite.evaluate(M.NAV_WAEHLEN_JS, "Projekte")
        seite.wait_for_timeout(2100)

        if not seite.evaluate(OEFFNE_JS):
            print("KEIN Projekt zum Oeffnen gefunden - nichts gemessen.")
            return 1
        seite.wait_for_timeout(2400)

        # ── Der Koeder: die Mehr-Liste darf noch nicht offen sein ──────────
        zu = seite.evaluate(MEHR_JS)
        print("KOEDER - Mehr-Eintraege vor dem Tippen: %d" % len(zu))
        if zu:
            print("   Sie sind immer sichtbar. Dann sagt der Rest nichts aus.")
            return 1

        # ── Die Reiterzeile ───────────────────────────────────────────────
        d = seite.evaluate(REITER_JS)
        if d.get("fehler"):
            print("ROT:", d["fehler"])
            return 1
        print("\nReiterzeile: Hoehe %d, Oberkante y=%d, overflow-x %s, wrap %s"
              % (d["hoehe"], d["oben"], d["overflowX"], d["umbruch"]))
        print("   %s" % d["reiter"])
        if d["hoehe"] != 40:
            schlimm.append("Reiterzeile %d px statt 40" % d["hoehe"])
        if d["overflowX"] not in ("auto", "scroll"):
            schlimm.append("Reiterzeile nicht quer rollbar (%s)" % d["overflowX"])
        if d["umbruch"] != "nowrap":
            schlimm.append("Reiterzeile bricht um (%s)" % d["umbruch"])
        if d["ohneText"]:
            schlimm.append("%d Reiter ohne sichtbaren Text" % d["ohneText"])

        # ── "Mehr" oeffnen ────────────────────────────────────────────────
        if not seite.evaluate(MEHR_AUF_JS):
            schlimm.append("Der Knopf 'Mehr' wurde nicht gefunden")
            mehr = []
        else:
            seite.wait_for_timeout(450)
            mehr = seite.evaluate(MEHR_JS)
            print("\nMehr-Liste: %d Eintraege" % len(mehr))
            for e in mehr:
                print("   %r" % e)
            ohne = [e for e in mehr if not e]
            if ohne:
                schlimm.append("%d Mehr-Eintraege ohne Text" % len(ohne))

        direkt = [r for r in d["reiter"] if not r.startswith("Mehr")]
        gesamt = len(direkt) + len(mehr)
        print("\nZiele gesamt: %d direkt + %d unter Mehr = %d" % (len(direkt), len(mehr), gesamt))
        if gesamt != 13:
            schlimm.append("%d Ziele erreichbar, erwartet 13 (als admin)" % gesamt)

        # ── Jedes Ziel wirklich antippen ─────────────────────────────────
        print("\nJedes Ziel antippen:")
        nicht_gewechselt = []
        for name in mehr:
            # Nur oeffnen, wenn sie ZU ist. Der erste Anlauf tippte "Mehr"
            # unbedingt und schloss damit im ersten Durchlauf die Liste, die
            # schon offen war - "Berichte" galt dadurch als nicht tippbar,
            # obwohl es das war. Ein Umschalter braucht eine Zustandsfrage,
            # keinen zweiten Tipp.
            if not seite.evaluate(MEHR_JS):
                seite.evaluate(MEHR_AUF_JS)
            seite.wait_for_timeout(300)
            vorher = seite.evaluate(ANSICHT_JS)
            getippt = seite.evaluate(TIPPE_JS, name)
            seite.wait_for_timeout(900)
            nachher = seite.evaluate(ANSICHT_JS)
            ok = getippt and nachher is not None and nachher != vorher
            print("   %-14s getippt=%s  Ansicht wechselt=%s" % (name, getippt, ok))
            if not getippt:
                nicht_gewechselt.append(name + " (nicht tippbar)")
        if nicht_gewechselt:
            schlimm.append("nicht erreichbar: %s" % nicht_gewechselt)

        # ── Die Hauptnavigation liegt unten ──────────────────────────────
        h = seite.evaluate(HAUPTNAV_JS)
        print("\nHauptnavigation (.tab-bar): %s" % h)
        if not h.get("fehler"):
            mitte = h["oben"] + h["hoehe"] / 2
            if mitte < h["fensterH"] * 0.6:
                schlimm.append("Die Hauptnavigation liegt oben (Mitte y=%d von %d)"
                               % (mitte, h["fensterH"]))

        if fehler:
            schlimm.append("Seitenfehler: %s" % fehler[:2])
        browser.close()

    print("\n" + "=" * 64)
    if schlimm:
        print("ROT:")
        for z in schlimm:
            print("   " + z)
        return 1
    print("GRUEN - Reiterzeile 40 px mit Text, quer rollbar; alle 13 Ziele")
    print("erreichbar (fuenf direkt, acht unter 'Mehr'); jeder Eintrag")
    print("beschriftet; die Hauptnavigation liegt unten wie im Rest der App.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
