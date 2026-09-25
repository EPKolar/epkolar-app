# -*- coding: utf-8 -*-
"""Probe: erreicht man die drei Projekt-Aktionen nach dem Umbau noch?

WOZU
────
Die drei Knoepfe "Bearbeiten / Archivieren / Loeschen" sind in ein Menue
gewandert. Ein Riegel auf den Quelltext kann nur sagen, dass die Handler
DASTEHEN - nicht, dass man sie ERREICHT. Genau diese Verwechslung hat in
diesem Bestand schon mehrfach etwas durchgelassen: das Bauteil war da, der
Weg dorthin nicht.

Hier wird der Weg gegangen: Menue oeffnen, Eintraege zaehlen, Beschriftungen
lesen, "Bearbeiten" antippen und pruefen, ob das Formular aufgeht.

DER KOEDER
──────────
Vor der eigentlichen Probe wird gemessen, dass das Menue GESCHLOSSEN keine
Eintraege zeigt. Waeren sie immer sichtbar, sagte "nach dem Klick sind sie
da" nichts aus.

AUFRUF
──────
    python scripts/projliste_menue_probe.py
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import mob_ansicht_messen as M  # noqa: E402

# Zaehlt die sichtbaren Menue-Eintraege und gibt ihre Beschriftungen zurueck.
EINTRAEGE_JS = """() => {
  const m = Array.from(document.querySelectorAll('[role="menuitem"]'))
    .filter(e => { const r = e.getBoundingClientRect();
                   return r.width > 4 && r.height > 4; });
  return m.map(e => (e.innerText || '').trim());
}"""

# Findet den ersten Aktionen-Knopf einer Projektkarte und tippt ihn an.
MENUE_AUF_JS = """() => {
  const b = Array.from(document.querySelectorAll('button[aria-haspopup="menu"]'))
    .filter(e => { const r = e.getBoundingClientRect();
                   return r.width > 4 && r.height > 4; });
  if (!b.length) return {fehler: 'kein Knopf mit aria-haspopup=menu'};
  const erster = b[0];
  const vorher = erster.getAttribute('aria-expanded');
  erster.click();
  return {anzahl: b.length, vorher: vorher,
          label: erster.getAttribute('aria-label')};
}"""

# aria-expanded MUSS nach dem Neuzeichnen gelesen werden. Wer es synchron
# hinter dem Klick liest, misst den Zustand VOR dem Rendern und meldet einen
# Fehler, den es nicht gibt - genau das ist mir hier zuerst passiert.
EXPANDED_JS = """() => {
  const b = document.querySelector('button[aria-haspopup="menu"]');
  return b ? b.getAttribute('aria-expanded') : null;
}"""

TIPPE_JS = """(text) => {
  const m = Array.from(document.querySelectorAll('[role="menuitem"]'))
    .find(e => (e.innerText || '').trim().toLowerCase().includes(text));
  if (!m) return false;
  m.click();
  return true;
}"""

FORMULAR_JS = """() => {
  const p = Array.from(document.querySelectorAll('input[placeholder]'))
    .map(e => e.getAttribute('placeholder'));
  return p.filter(x => /PA24|BVH|Musterstra/.test(x || ''));
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

    EXTRA = ("try{ var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
             " u.role=\"admin\"; u.monteurId=\"M1\"; u.name=\"Gerhard Steinbichler\";"
             " localStorage.setItem('epkolar_user',JSON.stringify(u)); }catch(e){}")

    schlimm = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 390, "height": 844},
                                  device_scale_factor=1, is_mobile=True,
                                  has_touch=True)
        ctx.add_init_script(M.INIT)
        ctx.add_init_script(EXTRA)
        ctx.route("**/rest/v1/**", lambda r: r.abort())
        ctx.route("**/auth/v1/**", lambda r: r.abort())
        seite = ctx.new_page()
        fehler = []
        seite.on("pageerror", lambda e: fehler.append(str(e)[:160]))
        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(4000)

        seite.evaluate(M.NAV_OEFFNEN_JS)
        seite.wait_for_timeout(400)
        ok = seite.evaluate(M.NAV_WAEHLEN_JS, "Projekte")
        seite.wait_for_timeout(2200)
        if not ok:
            print("Projekte nicht erreichbar - nichts gemessen.")
            return 1

        # ── Koeder: geschlossen darf nichts zu sehen sein ──────────────────
        zu = seite.evaluate(EINTRAEGE_JS)
        print("KOEDER - Menueeintraege bei geschlossenem Menue: %d %s"
              % (len(zu), zu))
        if zu:
            print("  Die Eintraege sind IMMER sichtbar. Dann sagt der Rest "
                  "dieser Probe nichts aus. ABBRUCH.")
            return 1

        # ── Menue oeffnen ──────────────────────────────────────────────────
        auf = seite.evaluate(MENUE_AUF_JS)
        if auf.get("fehler"):
            print("FEHLER:", auf["fehler"])
            return 1
        seite.wait_for_timeout(300)
        print("Aktionen-Knoepfe auf der Seite: %d" % auf["anzahl"])
        print("  aria-label: %r" % auf["label"])
        seite.wait_for_timeout(250)
        nachher = seite.evaluate(EXPANDED_JS)
        print("  aria-expanded  vorher %r -> nachher %r"
              % (auf["vorher"], nachher))
        if nachher != "true":
            schlimm.append("aria-expanded bleibt %r" % nachher)

        eintraege = seite.evaluate(EINTRAEGE_JS)
        print("Menueeintraege nach dem Tippen: %d" % len(eintraege))
        for e in eintraege:
            print("   %r" % e)
        # "Loeschen" steht im Menue mit Umlaut - die App spricht Deutsch.
        # Der erste Anlauf dieser Probe suchte "loesch" und meldete das Fehlen
        # eines Eintrags, der da war. Gesucht wird deshalb nach einem Stamm
        # ohne Umlaut-Stelle.
        for muss, stamm in (("Bearbeiten", "bearbeit"),
                            ("Archivieren", "archivier"),
                            ("Loeschen", "schen")):
            if not any(stamm in (x or "").lower() for x in eintraege):
                schlimm.append("%s fehlt im Menue" % muss)
        if eintraege and "schen" in (eintraege[0] or "").lower():
            schlimm.append("Loeschen ist der ERSTE Eintrag")

        # ── Bearbeiten wirklich ausloesen ─────────────────────────────────
        getippt = seite.evaluate(TIPPE_JS, "bearbeit")
        seite.wait_for_timeout(1200)
        felder = seite.evaluate(FORMULAR_JS)
        print("\n'Bearbeiten' getippt: %s -> Formularfelder sichtbar: %s"
              % (getippt, felder))
        if not getippt:
            schlimm.append("'Bearbeiten' liess sich nicht tippen")
        elif not felder:
            schlimm.append("Nach 'Bearbeiten' ist kein Projektformular da")

        nach = seite.evaluate(EINTRAEGE_JS)
        if nach:
            schlimm.append("Das Menue blieb nach der Wahl offen (%d Eintraege)"
                           % len(nach))

        if fehler:
            schlimm.append("Seitenfehler: %s" % fehler[:3])
        browser.close()

    print("\n" + "=" * 60)
    if schlimm:
        print("ROT:")
        for z in schlimm:
            print("   " + z)
        return 1
    print("GRUEN - Menue oeffnet, traegt alle drei Aktionen, Loeschen ist")
    print("nicht der erste Eintrag, 'Bearbeiten' oeffnet das Formular, und")
    print("das Menue schliesst danach.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
