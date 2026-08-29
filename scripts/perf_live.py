# -*- coding: utf-8 -*-
"""Laufzeit-Messung der Live-App: Speicher, DOM-Groesse und Umschaltzeit je Ansicht.

WOFUER DAS DA IST
-----------------
Der Auftrag "schneller und weniger RAM" (v3.9.883) liess sich bisher nur an der
QUELLE belegen: weniger Arbeit im Render, `content-visibility` auf langen
Listen, keine wachsenden Intervalle. Das sind Argumente, keine Messungen.

Was daran fehlte, ist genau die Sorte Beleg, die in diesem Repo schon dreimal
ein Urteil umgedreht hat: eine Zahl, die auch ROT sein kann. Ein Riegel, der nur
zeigen kann, dass etwas da ist, misst nichts.

Dieses Skript liefert drei Zahlen je Ansicht:

    heapKum     genutzter JS-Heap NACH dem Besuch dieser und aller vorherigen
                Ansichten. KUMULATIV, nicht je Ansicht - die Reihenfolge geht
                also ein. Aussagekraeftig ist der Verlauf (waechst er und faellt
                er nie?), nicht der Einzelwert.
    domNodes    Anzahl DOM-Knoten dieser Ansicht - der beste Einzelindikator
                fuer Render-Kosten, und die einzige Spalte, die wirklich je
                Ansicht gilt.
    umschaltMs  Klick auf die Ansicht bis zur letzten DOM-Aenderung. Vorher wird
                auf eine neutrale Ansicht gewechselt, sonst misst man einen
                Klick auf den schon offenen Tab (= gar nichts).

WICHTIG ZUR EINORDNUNG - was diese Zahlen NICHT sind:
  * Kein Vergleich gegen frueher. Es gibt keine gespeicherte Basislinie; der
    erste Lauf IST die Basislinie. Wer eine Verbesserung behaupten will, braucht
    zwei Laeufe gegen zwei Versionen.
  * `performance.memory` ist eine Schaetzung mit grober Koernung und schwankt mit
    dem Zeitpunkt der Muellabfuhr. Deshalb wird vor jeder Messung ein
    Sammel-Lauf erzwungen (--js-flags=--expose-gc), und gemessen wird der Median
    aus mehreren Durchgaengen, nicht ein Einzelwert.
  * Ohne echte Anmeldung sind die Listen LEER. Die Zahlen sind damit eine
    UNTERGRENZE: sie zeigen, was die App schon ohne Daten kostet. Genau das ist
    aber die interessante Groesse fuer "das Geruest ist zu teuer".

DER ERSTE LAUF IST KEINE MESSUNG
--------------------------------
Beim ersten Laden werden Schriften, Skripte und der Service Worker geholt und
uebersetzt. Diese Zahlen gehoeren nicht zur Ansicht. Deshalb laeuft jede Ansicht
zweimal, und der erste Durchgang wird verworfen.

BENUTZUNG
---------
    python scripts/perf_live.py
    python scripts/perf_live.py http://127.0.0.1:8899/index.html
    python scripts/perf_live.py --runden 3

Voraussetzung: pip install playwright && playwright install chromium
"""
import statistics
import sys

for _strom in (sys.stdout, sys.stderr):
    try:
        _strom.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

LIVE = "https://epkolar.github.io/epkolar-app/index.html"

# Gleiche Test-Sitzung wie tab_sweep.py - ein plausibel geformter Token, damit
# die App ueber die Anmeldemaske hinauskommt. Datenabrufe laufen in 401.
INIT = """
try{
  var b=function(s){return btoa(s).replace(/=+$/,'');};
  var jwt=b(JSON.stringify({alg:"HS256",typ:"JWT"}))+"."+
          b(JSON.stringify({sub:"1",role:"authenticated",
                            exp:Math.floor(Date.now()/1000)+86400}))+".sig";
  localStorage.setItem('epkolar_auth',JSON.stringify({at:jwt,rt:"r",exp:Date.now()+86400000}));
  localStorage.setItem('epkolar_user',JSON.stringify({
    id:"1",username:"admin",name:"Perf",role:"admin",
    rolle:"Geschaeftsfuehrer",permissions:[],perms_override:{}}));
}catch(e){}
"""

TABLEISTE = """
  const t = e => (e.textContent||'').trim().replace(/\\s+/g,' ');
  const bar = [...document.querySelectorAll('.tab-bar')]
    .find(b => t(b).indexOf('Home')>=0 && t(b).indexOf('Projekte')>=0);
"""

KLICK = """(idx) => {""" + TABLEISTE + """
  if(!bar) return;
  const bs = [...bar.querySelectorAll('button')];
  if(bs[idx]) bs[idx].click();
}"""

MESSEN = """() => {
  const m = (performance.memory && performance.memory.usedJSHeapSize) || 0;
  return { heap: m, nodes: document.getElementsByTagName('*').length };
}"""


def _ruhig(seite, ms=450):
    """Wartet auf einen Frame ohne weitere Renderarbeit."""
    seite.wait_for_timeout(ms)


# ERSTER LAUF, 29.08.2026: DAS MESSGERAET HAT SICH SELBST GEMESSEN.
# Die erste Fassung nahm `performance.now()` vor und nach dem Klick - mit einem
# festen `wait_for_timeout(450)` dazwischen. Ergebnis: 18 Ansichten, alle
# zwischen 460 und 468 ms. Das ist nicht die Umschaltzeit, das IST die
# Wartezeit. Ein Messgeraet, dessen Werte nicht auseinandergehen KOENNEN, misst
# nichts - dieselbe Krankheit wie ein Riegel, der nie rot werden kann.
#
# Jetzt haengt ein MutationObserver an der Seite und merkt sich den Zeitpunkt der
# LETZTEN DOM-Aenderung. Gemessen wird Klick -> letzte Aenderung. Die Wartezeit
# steht danach immer noch im Ablauf, geht aber nicht mehr in die Zahl ein.
BEOBACHTER = """() => {
  if (window.__perfObs) return;
  window.__perfLetzte = 0;
  window.__perfObs = new MutationObserver(() => { window.__perfLetzte = performance.now(); });
  window.__perfObs.observe(document.body, {childList:true, subtree:true,
                                           attributes:true, characterData:true});
}"""

# ZWEITER GERAETEFEHLER, gleicher Nachmittag: 14 von 18 Ansichten lieferten -1,
# also "es hat sich nichts geruehrt". Der Grund war der Messablauf selbst - je
# Ansicht liefen mehrere Runden, und ab Runde 2 wurde auf den BEREITS OFFENEN
# Tab geklickt. Da rendert React nichts nach, voellig zu Recht.
# Deshalb wird vor jeder gemessenen Runde erst auf eine NEUTRALE Ansicht
# gewechselt und dann auf die Zielansicht. Gemessen wird nur der zweite Klick.
# Merksatz: ein Messwert, den man nicht erklaeren kann, ist zuerst ein Verdacht
# gegen den Aufbau - nicht gegen das Gemessene.

# Startpunkt setzen und Zaehler zuruecksetzen - unmittelbar vor dem Klick.
STARTEN = "() => { window.__perfLetzte = 0; return (window.__perfT0 = performance.now()); }"

# Klick -> letzte DOM-Aenderung. 0 bedeutet: es hat sich NICHTS geruehrt.
ABLESEN = """() => (window.__perfLetzte > 0)
    ? (window.__perfLetzte - window.__perfT0) : -1"""


MIN_STREUUNG = 0.05  # 5 % der Mitte

# Welche Spalte der Ergebniszeile welchen Namen und welche Einheit hat.
# (Index in der Zeile, Name, Einheit) - Spalte 2 (domNodes) ist ausgenommen:
# sie darf ueber gleichartige Ansichten durchaus aehnlich sein.
SPALTEN = ((1, "heapKum", "MB"), (3, "umschaltMs", "ms"))


def ungueltige_spalten(ergebnisse, min_streuung=MIN_STREUUNG):
    """SELBSTPRUEFUNG DES MESSGERAETS - liefert Meldungen fuer tote Spalten.

    Eine Spalte, deren Werte ueber achtzehn sehr unterschiedliche Ansichten
    praktisch nicht auseinandergehen, misst hoechstwahrscheinlich den AUFBAU
    statt die App. Genau so ist die erste Fassung dieses Skripts hereingefallen:
    achtzehn Umschaltzeiten zwischen 460 und 468 ms - das war nicht die App, das
    war der eigene `wait_for_timeout(450)`. Und achtzehn identische Heap-Werte,
    weil Chromium `performance.memory` ohne `--enable-precise-memory-info` grob
    rundet.

    Beide Male sahen die Zahlen brauchbar aus. Ein Messwert, der nicht
    auseinandergehen KANN, ist aber dasselbe wie ein Riegel, der nicht rot
    werden kann. Lieber laut ungueltig als leise falsch.

    Rueckgabe: Liste von Meldungen (leer = alle Spalten streuen genug).
    """
    meldungen = []
    for idx, name, einheit in SPALTEN:
        werte = [z[idx] for z in ergebnisse if z[idx] >= 0]
        if len(werte) < 3:
            continue
        spanne = max(werte) - min(werte)
        mitte = statistics.median(werte) or 1
        if spanne / mitte < min_streuung:
            meldungen.append(
                "UNGUELTIG: %s streut ueber alle Ansichten nur um %.2f %s "
                "(%.1f%%).%s   Diese Spalte misst den Messaufbau, nicht die "
                "App. Nicht als Befund verwenden."
                % (name, spanne, einheit, 100 * spanne / mitte, chr(10)))
    return meldungen


def main(url=LIVE, runden=2):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt.  pip install playwright && playwright install chromium")
        return 2

    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--js-flags=--expose-gc",
                                           "--enable-precise-memory-info"])
        ctx = browser.new_context(viewport={"width": 390, "height": 844},
                                  has_touch=True, is_mobile=True)
        ctx.add_init_script(INIT)
        seite = ctx.new_page()

        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(6000)

        version = seite.evaluate(
            "() => typeof APP_VERSION!=='undefined' ? APP_VERSION : '?'")
        hatMemory = seite.evaluate("() => !!performance.memory")
        print("Version:  %s" % version)
        print("Messpunkt: %s" % url)
        if not hatMemory:
            print("WARNUNG: performance.memory fehlt - heapMB bleibt 0. "
                  "Ohne diese Zahl misst der Lauf nur DOM und Zeit.")

        namen = seite.evaluate("""() => {""" + TABLEISTE + """
            return bar ? [...bar.querySelectorAll('button')].map(b => t(b).slice(0,18)) : [];
        }""")
        if not namen:
            print("FEHLER: keine Tab-Leiste gefunden.")
            browser.close()
            return 1

        # Ruhezustand: was kostet das Geruest, bevor irgendeine Ansicht offen war?
        seite.evaluate("() => { try{ window.gc && window.gc(); }catch(e){} }")
        _ruhig(seite, 700)
        grund = seite.evaluate(MESSEN)
        grundheap = grund["heap"] / 1048576.0
        print("Grundlast: %.1f MB Heap, %d DOM-Knoten" % (grundheap, grund["nodes"]))
        print()
        print("%-20s %9s %9s %9s" % ("Ansicht", "heapKum", "domNodes", "umschaltMs"))
        print("-" * 52)

        ergebnisse = []
        for i, name in enumerate(namen):
            heaps, knoten, zeiten = [], [], []
            for runde in range(runden):
                seite.evaluate(BEOBACHTER)
                # Neutrale Ansicht: irgendeine ANDERE als die zu messende.
                seite.evaluate(KLICK, 1 if i != 1 else 0)
                _ruhig(seite, 350)
                seite.evaluate(STARTEN)
                seite.evaluate(KLICK, i)
                _ruhig(seite)
                dauer = seite.evaluate(ABLESEN)
                seite.evaluate("() => { try{ window.gc && window.gc(); }catch(e){} }")
                _ruhig(seite, 250)
                w = seite.evaluate(MESSEN)
                # DER ERSTE DURCHGANG IST KEINE MESSUNG - er enthaelt das
                # einmalige Uebersetzen und Nachladen dieser Ansicht.
                if runde == 0:
                    continue
                heaps.append(w["heap"] / 1048576.0)
                knoten.append(w["nodes"])
                if dauer >= 0:
                    zeiten.append(dauer)

            if not heaps:
                continue
            # -1 = der Klick hat die Seite nicht veraendert. Das ist ein
            # Ergebnis, keine fehlende Messung: die Ansicht war schon offen.
            zeile = (name, statistics.median(heaps), int(statistics.median(knoten)),
                     statistics.median(zeiten) if zeiten else -1.0)
            ergebnisse.append(zeile)
            print("%-20s %9.1f %9d %9.0f" % zeile)

        # ── ZWEITER DURCHGANG: die entscheidende Frage ──────────────────
        # Der Heap waechst ueber die 18 Ansichten monoton und faellt trotz
        # erzwungener Muellabfuhr nie. Das kann ZWEI ganz verschiedene Dinge
        # heissen, und die Zahl allein sagt nicht welche:
        #
        #   (a) je Ansicht wird einmalig Code nachgeladen (`lazy()`), der danach
        #       zu Recht liegen bleibt  -> harmlos, waechst NUR beim ersten Mal
        #   (b) beim Rendern bleibt etwas haengen (Zuhoerer, Zeitgeber, Verweise)
        #       -> waechst bei JEDEM Durchgang weiter
        #
        # Beides sieht im ersten Durchgang gleich aus. Der zweite Durchgang
        # trennt sie: derselbe Weg noch einmal, ohne neu zu laden. Bleibt der
        # Heap jetzt stehen, war es (a). Waechst er nochmal um denselben Betrag,
        # ist es (b) - und das waere ein Befund.
        seite.evaluate("() => { try{ window.gc && window.gc(); }catch(e){} }")
        _ruhig(seite, 700)
        nach_pass1 = seite.evaluate(MESSEN)["heap"] / 1048576.0

        for i in range(len(namen)):
            seite.evaluate(KLICK, i)
            _ruhig(seite, 220)
        seite.evaluate("() => { try{ window.gc && window.gc(); }catch(e){} }")
        _ruhig(seite, 700)
        nach_pass2 = seite.evaluate(MESSEN)["heap"] / 1048576.0

        for i in range(len(namen)):
            seite.evaluate(KLICK, i)
            _ruhig(seite, 220)
        seite.evaluate("() => { try{ window.gc && window.gc(); }catch(e){} }")
        _ruhig(seite, 700)
        nach_pass3 = seite.evaluate(MESSEN)["heap"] / 1048576.0

        browser.close()

    if not ergebnisse:
        print("Keine Messwerte - runden muss mindestens 2 sein.")
        return 1

    print()
    teuer_dom = max(ergebnisse, key=lambda z: z[2])
    teuer_zeit = max(ergebnisse, key=lambda z: z[3])
    print("Meiste DOM-Knoten: %s (%d)" % (teuer_dom[0], teuer_dom[2]))
    print("Laengste Umschaltzeit: %s (%.0f ms)" % (teuer_zeit[0], teuer_zeit[3]))

    for meldung in ungueltige_spalten(ergebnisse):
        print()
        print(meldung)
    print()
    print("Diese Zahlen sind eine UNTERGRENZE (keine Daten geladen) und keine")
    print("Aussage ueber frueher - fuer einen Vergleich braucht es einen zweiten")
    print("Lauf gegen eine andere Version.")

    print()
    print("Heap nach vollstaendigem Rundgang (alle %d Ansichten):" % len(namen))
    print("   Grundlast          %5.1f MB" % grundheap)
    print("   nach Rundgang 1    %5.1f MB   (+%.1f)" %
          (nach_pass1, nach_pass1 - grundheap))
    print("   nach Rundgang 2    %5.1f MB   (+%.1f)" %
          (nach_pass2, nach_pass2 - nach_pass1))
    print("   nach Rundgang 3    %5.1f MB   (+%.1f)" %
          (nach_pass3, nach_pass3 - nach_pass2))

    w1 = nach_pass1 - grundheap
    w2 = nach_pass3 - nach_pass1
    print()
    if w1 <= 0.2:
        print("Kein Wachstum messbar - der Aufbau ist zu grob fuer diese Frage.")
    elif w2 > w1 * 0.5:
        print("BEFUND: der Heap waechst in den WIEDERHOLUNGEN weiter "
              "(+%.1f MB nach dem ersten Rundgang, gegenueber +%.1f MB beim "
              "ersten). Nachgeladener Code erklaert das NICHT - der wird nur "
              "einmal geholt. Verdacht auf haengende Zuhoerer, Zeitgeber oder "
              "Verweise." % (w2, w1))
    else:
        print("Kein Leck erkennbar: das Wachstum faellt nach dem ersten "
              "Rundgang von +%.1f auf +%.1f MB. Das ist die Form von einmalig "
              "nachgeladenem Code (lazy-Bausteine), nicht die eines Lecks - "
              "ein Leck waechst bei jeder Wiederholung gleich weiter." % (w1, w2))
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    r = 2
    for a in sys.argv[1:]:
        if a.startswith("--runden"):
            r = int(a.split("=", 1)[1]) if "=" in a else 3
    sys.exit(main(args[0] if args else LIVE, r))
