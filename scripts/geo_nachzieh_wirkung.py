# -*- coding: utf-8 -*-
"""Ueberlebt die Geokodier-Arbeit, wenn der CACHE-Schreibvorgang scheitert?

🔴 DER MANGEL, DEN DAS MISST. `_geoSelbstnachzieh` fragt bis zu zwoelf
Postleitzahlen bei Nominatim ab - mit **1,1 Sekunden Pause dazwischen**, wie
es deren Richtlinie verlangt - und danach die Fahrstrecken bei OSRM. Das
Ergebnis wird in einer cdnjs-fremden Tabelle zwischengespeichert:

    try{ await _sbPost("plz_geo",{...}); geoMap[plz]={...}; geocoded++; }
    catch(_w){ /* Tabelle fehlt/RLS -> still weiter */ }

Der Kommentar verspricht „still weiter". Der Code tut etwas anderes: schlaegt
der Cache-Schreibvorgang fehl, werden **`geoMap[plz]` und `geocoded` gar nicht
erst gesetzt**. Dasselbe eine Zeile tiefer mit `matrixRows`.

🔴 UND DAS IST NICHT NUR DER CACHE. Der Aufrufer veroeffentlicht das Ergebnis
nur unter einer Bedingung:

    if(rr && (rr.geocoded>0 || rr.matrixRows>0)){ window.__dispoGeo={...}; }

Bleiben beide Zaehler auf 0, wird die **ganze Arbeit des Laufs verworfen** -
die Geokodierung genauso wie die Entfernungsmatrix, obwohl beide im Speicher
fertig dastehen. Bei einem Monteur, dem die RLS das Schreiben auf `plz_geo`
verwehrt, passiert das bei **jedem** Lauf aufs Neue, samt bis zu 13 Sekunden
Wartezeit und zwoelf Anfragen an einen fremden Dienst.

WAS HIER GEMESSEN WIRD, UND WARUM NICHT IM QUELLTEXT. Ob eine Zuweisung vor
oder hinter einem `try` steht, ist Anwesenheit. Gemessen wird stattdessen die
WIRKUNG: `_sbPost` wird zur Laufzeit durch eine Fassung ersetzt, die immer
wirft, Nominatim und OSRM werden durch feste Antworten ersetzt - und dann
wird nachgesehen, was `_geoSelbstnachzieh` zurueckgibt.

🔴 SELBSTPROBE IN BEIDE RICHTUNGEN, sonst belegt der Lauf nichts:
  * mit funktionierendem `_sbPost` MUSS `geocoded > 0` herauskommen -
    sonst misst der Aufbau ueberhaupt nichts, und die Null im Fehlerfall
    waere von „geht sowieso nicht" nicht zu unterscheiden.
  * der Ersatz fuer `_sbPost` muss auch wirklich gerufen worden sein.
"""
import io
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
WURZEL = os.path.dirname(HIER)

import mob_ansicht_messen as M           # noqa: E402

# Nominatim liefert fuer jede PLZ dieselbe erfundene Antwort; die Zahlen sind
# beliebig, es geht nur darum, dass sie durchkommen.
NOMINATIM = json.dumps([{"lat": "48.2", "lon": "16.37",
                         "display_name": "Teststadt, Niederoesterreich"}])
# OSRM-Antwort fuer zwei Punkte: eine 2x2-Matrix.
OSRM = json.dumps({"code": "Ok",
                   "distances": [[0, 12000], [12000, 0]],
                   "durations": [[0, 900], [900, 0]]})

LAUF_JS = r"""(soll_werfen) => {
  if (typeof _geoSelbstnachzieh !== 'function')
    return {fehler: '_geoSelbstnachzieh gibt es nicht'};
  window.__postRufe = 0;
  const echt = window._sbPost;
  window._sbPost = async function(){
    window.__postRufe++;
    if (soll_werfen) throw new Error('HTTP403 {"code":"42501"}');
    return {ok: 1};
  };
  // Die Schleife nimmt bis zu zwoelf Misses mit je 1,1 s Pause. Zwei
  // genuegen fuer die Aussage und halten den Lauf kurz.
  const geoMap = {}, distMatrix = {};
  return _geoSelbstnachzieh('3470', ['2100', '2101'], geoMap, distMatrix)
    .then(r => ({erg: r,
                 postRufe: window.__postRufe,
                 geoMapGroesse: Object.keys(geoMap).length,
                 matrixGroesse: Object.keys(distMatrix).length}))
    .catch(e => ({fehler: String(e && e.message || e)}))
    .finally(() => { window._sbPost = echt; });
}"""


def _lauf(seite, werfen):
    return seite.evaluate(LAUF_JS, werfen)


def main(argv):
    from playwright.sync_api import sync_playwright
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port,
                                      os.environ.get("EPK_INDEX", "index.html"))
    schief = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1440, "height": 880})
        ctx.add_init_script(M.INIT)
        ctx.route("**/rest/v1/**", lambda r: r.abort())
        ctx.route("**/auth/v1/**", lambda r: r.abort())
        ctx.route("**nominatim.openstreetmap.org**", lambda r: r.fulfill(
            status=200, content_type="application/json", body=NOMINATIM))
        ctx.route("**router.project-osrm.org**", lambda r: r.fulfill(
            status=200, content_type="application/json", body=OSRM))
        seite = ctx.new_page()
        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(5000)

        print("1. Selbstprobe: mit FUNKTIONIERENDEM Cache-Schreiben")
        gut = _lauf(seite, False)
        print("   %s" % gut)
        if gut.get("fehler"):
            print("\U0001F534 Der Aufbau laeuft nicht: %s" % gut["fehler"])
            ctx.close()
            browser.close()
            return 2
        if not gut.get("postRufe"):
            schief.append("Der Ersatz fuer `_sbPost` wurde nie gerufen - "
                          "dann misst der Lauf nichts.")
        if (gut.get("erg") or {}).get("geocoded", 0) < 1:
            schief.append(
                "Schon im GUTEN Fall ist `geocoded` 0. Dann waere die Null im "
                "Fehlerfall\n     von „geht sowieso nicht“ nicht zu "
                "unterscheiden - der Lauf belegt nichts.")
        if schief:
            for s in schief:
                print("   \U0001F534 " + s)
            ctx.close()
            browser.close()
            return 2
        print("   \U0001F7E2 geocoded=%s, geoMap=%s Eintraege\n"
              % ((gut.get("erg") or {}).get("geocoded"),
                 gut.get("geoMapGroesse")))

        print("2. Der Fall: Cache-Schreiben wirft (RLS/403)")
        seite.reload(wait_until="domcontentloaded")
        seite.wait_for_timeout(5000)
        schlecht = _lauf(seite, True)
        print("   %s" % schlecht)
        ctx.close()
        browser.close()

    erg = schlecht.get("erg") or {}
    geocoded = erg.get("geocoded", 0)
    matrix = erg.get("matrixRows", 0)
    inRam = schlecht.get("geoMapGroesse", 0)

    print()
    if geocoded < 1 and matrix < 1:
        print("\U0001F534 BEFUND: der Cache-Schreibvorgang scheitert, und "
              "damit ist die GANZE\n   Arbeit des Laufs verworfen - "
              "geocoded=%s, matrixRows=%s, geoMap=%s.\n"
              "   Der Aufrufer veroeffentlicht nur bei "
              "`geocoded>0 || matrixRows>0`;\n   `window.__dispoGeo` bleibt "
              "also leer, obwohl die Daten dastanden.\n"
              "   Der Kommentar im `catch` verspricht "
              "„still weiter“. Das stimmt nicht."
              % (geocoded, matrix, inRam))
        return 1
    print("\U0001F7E2 Die Arbeit ueberlebt den fehlgeschlagenen "
          "Cache-Schreibvorgang:\n   geocoded=%s, matrixRows=%s, geoMap=%s "
          "Eintraege." % (geocoded, matrix, inRam))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
