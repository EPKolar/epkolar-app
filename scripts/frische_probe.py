# -*- coding: utf-8 -*-
"""Probe: laedt die App Projekte und Mitarbeiter beim Zurueckkommen nach?

WOZU
────
`projects` und `monteure` wurden nur beim Start vom Server gelesen. Bleibt der
Tab offen, arbeitet man eine ganze Sitzung auf dem Stand vom Anmelden.

Ob der neue Sichtbarkeits-Lauscher wirklich EINEN Nachlauf ausloest - und
keinen ohne Sichtbarkeitswechsel - sagt nur ein Lauf, der die Aufrufe ZAEHLT.
Ein Riegel auf den Quelltext koennte nur sagen, dass ein Lauscher dasteht.

WAS GEMESSEN WIRD
─────────────────
Die Aufrufe an die Projekt- und Mitarbeiter-Endpunkte werden abgefangen und
gezaehlt. Dann:

  1. nichts tun            -> die Zahl bleibt stehen (kein Poll)
  2. sichtbar werden       -> genau EIN Nachlauf mehr
  3. sofort noch einmal    -> KEIN weiterer (die 60-s-Schranke)
  4. mit Fokus im Feld     -> KEIN Nachlauf ('defer' - ein Nachlauf mitten im
                              Tippen koennte ein halb gefuelltes Formular neu
                              zeichnen)

DER KOEDER
──────────
Vor allem anderen muss der Zaehler beim ERSTEN Laden hochgehen. Zaehlt er
dort null, faengt die Probe die Aufrufe nicht ab - und alles Weitere waere
eine Aussage ueber nichts.

AUFRUF
──────
    python scripts/frische_probe.py
"""
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import mob_ansicht_messen as M  # noqa: E402

# Der Lauscher haengt an document; visibilityState laesst sich nicht direkt
# setzen, also wird der Getter ueberschrieben und das Ereignis ausgeloest -
# genau so, wie der Browser es tun wuerde.
SICHTBAR_JS = """(zustand) => {
  Object.defineProperty(document, 'visibilityState',
    {configurable: true, get: () => zustand});
  document.dispatchEvent(new Event('visibilitychange'));
  return document.visibilityState;
}"""

FOKUS_JS = """() => {
  const e = document.querySelector('input:not([type=hidden])');
  if (!e) return false;
  e.focus();
  return document.activeElement === e;
}"""

BLUR_JS = """() => { if (document.activeElement && document.activeElement.blur)
                       document.activeElement.blur();
                     return true; }"""


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt.")
        return 2

    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port, os.environ.get("EPK_INDEX", "index.html"))
    print("Gemessen wird:", url)

    zaehler = {"n": 0}
    # Gezaehlt werden LISTENLADUNGEN, nicht Existenzproben.
    # GEMESSEN: in diesem Aufbau (alle Anfragen abgebrochen) laeuft alle
    # 30 s ein workers?select=id&limit=1. Das ist NICHT ein Poll der Liste,
    # sondern die Existenzprobe des Seed-Waechters (v3.9.208/928) - sie
    # greift nur, weil der Ladeversuch scheitert. Wer sie mitzaehlt, meldet
    # einen Poll, den es nicht gibt. Der erste Anlauf dieser Probe tat das
    # und war nur deshalb gruen, weil sein Ruhefenster sechs Sekunden lang
    # war und den 30-s-Zyklus damit verpasste.
    MUSTER = re.compile(r"(/rest/v1/(projects|workers)|/api/projects|/api/workers)")
    NUR_PROBE = re.compile(r"select=id&limit=1")

    schlimm = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1280, "height": 900})
        ctx.add_init_script(M.INIT)
        ctx.add_init_script(
            "try{var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
            "u.role='admin';u.monteurId='M1';"
            "localStorage.setItem('epkolar_user',JSON.stringify(u));}catch(e){}")

        def _route(route):
            _u = route.request.url
            if MUSTER.search(_u) and not NUR_PROBE.search(_u):
                zaehler["n"] += 1
            route.abort()

        ctx.route("**/rest/v1/**", _route)
        ctx.route("**/api/**", _route)
        ctx.route("**/auth/v1/**", lambda r: r.abort())
        seite = ctx.new_page()
        fehler = []
        seite.on("pageerror", lambda e: fehler.append(str(e)[:160]))
        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(4200)
        # In eine Ansicht mit Eingabefeld wechseln, sonst ist Fall 4 nicht
        # messbar - und ein nicht gemessener Fall darf im Urteil nicht als
        # gruen auftauchen.
        seite.evaluate(M.NAV_OEFFNEN_JS)
        seite.wait_for_timeout(350)
        seite.evaluate(M.NAV_WAEHLEN_JS, "Projekte")
        seite.wait_for_timeout(2200)

        beim_start = zaehler["n"]
        print("\nKOEDER - Aufrufe beim ersten Laden: %d" % beim_start)
        if beim_start == 0:
            print("   Die Probe faengt die Aufrufe nicht ab. ABBRUCH - alles")
            print("   Weitere waere eine Aussage ueber nichts.")
            return 1

        # ── 1. Nichts tun: es darf kein Poll laufen ───────────────────────
        vor_ruhe = zaehler["n"]
        # 35 s, nicht 6: ein Ruhefenster, das kuerzer ist als der
        # laengste Zyklus im Bestand (30 s), kann keinen Poll
        # ausschliessen.
        seite.wait_for_timeout(35000)
        nach_ruhe = zaehler["n"]
        print("\n1) 35 Sekunden nichts tun: %d -> %d" % (vor_ruhe, nach_ruhe))
        if nach_ruhe != vor_ruhe:
            schlimm.append("Ohne Sichtbarkeitswechsel liefen %d Aufrufe - es "
                           "gibt einen Poll, den es nicht geben soll."
                           % (nach_ruhe - vor_ruhe))

        # ── 2. Sichtbar werden: genau EIN Nachlauf ────────────────────────
        seite.evaluate(SICHTBAR_JS, "hidden")
        seite.wait_for_timeout(250)
        vor = zaehler["n"]
        seite.evaluate(SICHTBAR_JS, "visible")
        seite.wait_for_timeout(3000)
        nach = zaehler["n"]
        dazu = nach - vor
        print("2) sichtbar werden: %d -> %d  (+%d)" % (vor, nach, dazu))
        if dazu == 0:
            schlimm.append("Der Wechsel in den Vordergrund loest KEINEN "
                           "Nachlauf aus - dann wirkt die Aenderung nicht.")
        # Der Boot-Effekt holt mehrere Ressourcen; gezaehlt werden nur die
        # beiden, um die es geht. Mehr als einer je Ressource waere doppelt.
        elif dazu > 4:
            schlimm.append("Der Wechsel loeste %d Aufrufe aus - das sieht nach "
                           "mehrfachem Nachladen aus." % dazu)

        # ── 3. Sofort noch einmal: die 60-s-Schranke ──────────────────────
        seite.evaluate(SICHTBAR_JS, "hidden")
        seite.wait_for_timeout(200)
        vor2 = zaehler["n"]
        seite.evaluate(SICHTBAR_JS, "visible")
        seite.wait_for_timeout(2500)
        nach2 = zaehler["n"]
        print("3) sofort noch einmal: %d -> %d  (+%d)" % (vor2, nach2, nach2 - vor2))
        if nach2 != vor2:
            schlimm.append("Ein zweiter Wechsel innerhalb von 60 s loeste %d "
                           "weitere Aufrufe aus - die Altersschranke greift "
                           "nicht." % (nach2 - vor2))

        # ── 4. Mit Fokus im Eingabefeld: 'defer' ─────────────────────────
        hat_fokus = seite.evaluate(FOKUS_JS)
        print("4) Fokus in ein Eingabefeld gesetzt: %s" % hat_fokus)
        fall4_gemessen = False
        if not hat_fokus:
            print("   Kein Eingabefeld gefunden - Fall 4 NICHT gemessen.")
        else:
            # HIER MUSS GEWARTET WERDEN, und zwar wirklich.
            # Die 60-s-Altersschranke wuerde denselben Nullwert erzeugen wie
            # 'defer' - ein +0 ohne Wartezeit beweist also NICHTS ueber den
            # Fokus. Der erste Anlauf dieser Probe rief eine
            # window.__epkFrischeReset auf, die es gar nicht gibt (und die es
            # auch nicht geben soll - Pruefhaken gehoeren nicht in den
            # Auslieferungsstand). Also wird die Schranke ABGEWARTET; danach
            # ist der Fokus der einzige Grund, der noch bremsen kann.
            print("   warte 62 s, damit die Altersschranke nicht mehr greift")
            seite.wait_for_timeout(62000)
            seite.evaluate(SICHTBAR_JS, "hidden")
            seite.wait_for_timeout(200)
            vor3 = zaehler["n"]
            seite.evaluate(SICHTBAR_JS, "visible")
            seite.wait_for_timeout(2500)
            nach3 = zaehler["n"]
            print("   mit Fokus, sichtbar werden: %d -> %d  (+%d)"
                  % (vor3, nach3, nach3 - vor3))
            fall4_gemessen = True
            if nach3 != vor3:
                schlimm.append("Mit Fokus im Eingabefeld liefen %d Aufrufe - "
                               "'defer' greift nicht, ein halb gefuelltes "
                               "Formular koennte neu gezeichnet werden."
                               % (nach3 - vor3))
            # GEGENPROBE: ohne Fokus muss nach derselben Wartezeit geladen
            # werden. Ohne sie koennte der Nullwert oben auch daran liegen,
            # dass ueberhaupt nichts mehr laedt.
            seite.evaluate(BLUR_JS)
            seite.evaluate(SICHTBAR_JS, "hidden")
            seite.wait_for_timeout(200)
            vor4 = zaehler["n"]
            seite.evaluate(SICHTBAR_JS, "visible")
            seite.wait_for_timeout(3000)
            nach4 = zaehler["n"]
            print("   GEGENPROBE ohne Fokus: %d -> %d  (+%d)"
                  % (vor4, nach4, nach4 - vor4))
            if nach4 == vor4:
                schlimm.append("Auch OHNE Fokus wurde nach der Wartezeit "
                               "nicht geladen - dann sagt Fall 4 nichts "
                               "ueber den Fokus, sondern nur, dass gar "
                               "nichts mehr laedt.")

        if fehler:
            schlimm.append("Seitenfehler: %s" % fehler[:2])
        browser.close()

    print("\n" + "=" * 62)
    if schlimm:
        print("ROT:")
        for z in schlimm:
            print("   " + z)
        return 1
    print("GRUEN - kein Poll ohne Sichtbarkeitswechsel, der Wechsel in den")
    print("Vordergrund laedt nach, ein zweiter Wechsel innerhalb von 60 s")
    if fall4_gemessen:
        print("nicht, und mit Fokus im Eingabefeld wird nicht nachgeladen.")
    else:
        # Ein nicht gemessener Fall darf im Urteil nicht als gruen
        # auftauchen. Der erste Anlauf dieser Probe behauptete genau das -
        # die Fehlerform, gegen die in diesem Bestand die halbe
        # Riegelsammlung gebaut ist.
        print("nicht. FALL 4 (Fokus im Eingabefeld) wurde NICHT gemessen -")
        print("darueber sagt dieser Lauf nichts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
