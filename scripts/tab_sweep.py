# -*- coding: utf-8 -*-
"""
Tab-Durchlauf: oeffnet jede Hauptansicht und meldet Abstuerze.

WOFUER DAS DA IST
-----------------
Am 25.08.2026 stand der Tab "Monatsabrechnung" monatelang kaputt live: die
Callsite reichte die nackte Bindung `approvals` durch (der State heisst
`absApprovals`). Ein Klick darauf riss die GANZE App auf die Fehlerseite.

Kein bestehendes Gate konnte das sehen, und das ist kein Zufall:

  node_check.py   parst die Datei, fuehrt sie nicht aus
  _bracket_check  zaehlt Klammern
  pytest          statisch (String-/Regex-Asserts ueber den Quelltext)
  Browser-Check   laedt nur die Startseite

Der Ausdruck wird wegen des &&-Kurzschlusses NUR ausgewertet, wenn genau dieser
Tab aktiv ist. Und schlimmer: ein pytest-Test hatte den kaputten Wortlaut sogar
WORTGLEICH festgeschrieben und war gruen dabei.

Dieses Skript ist das einzige Gate, das diese Fehlerklasse ueberhaupt sehen kann.
Es kostet rund zwei Minuten.

VORAUSSETZUNG
-------------
    pip install playwright
    playwright install chromium

BENUTZUNG
---------
    python scripts/tab_sweep.py                     # gegen die Live-App
    python scripts/tab_sweep.py http://127.0.0.1:8899/index.html   # lokal

Exit 0 = alle Ansichten sauber. Exit 1 = mindestens eine Ansicht ist kaputt.

HINWEIS ZUR HERKUNFT
--------------------
Die Abfolge war zunaechst eine Transkription des Laufs, der am 25.08.2026 gegen
v3.9.874 live durchgefuehrt wurde (alle 18 Ansichten ok). Das SKRIPT selbst lief
drei Handoffs lang nie, weil im Arbeitsklon kein Playwright installiert war.

Am 29.08.2026 ist es zum ersten Mal echt gelaufen - gegen v3.9.896 live, wieder
alle 18 Ansichten sauber. Der erste Lauf starb allerdings an der ERSTEN Ansicht,
und zwar an sich selbst: siehe die stdout-Umstellung unten. Der Fehler sass
nicht im Messen, sondern im Berichten. Merksatz fuer das naechste Werkzeug:
die Transkription eines Laufs ist kein ausgefuehrter Lauf.
"""
import sys

# ERSTER LAUF, 29.08.2026 - UND DAS GATE STARB AN SICH SELBST, NICHT AN DER APP.
# Die Tab-Namen der App tragen Emoji ("\U0001f3e0 Home"). Windows-stdout ist
# cp1252, und `print("  %-20s ok" % name)` warf beim ERSTEN Tab
# UnicodeEncodeError. Das Skript ist also nie ueber Ansicht 1 hinausgekommen -
# ein Gate, das abstuerzt, bevor es etwas melden kann, ist kein Gate.
#
# Bemerkenswert: der Fehler steckte nicht im Messen, sondern im BERICHTEN. Genau
# deshalb steht in der Kopfnotiz "beim ersten Lauf mit kritischem Blick
# draufschauen" - die Transkription eines Laufs ist eben kein ausgefuehrter Lauf.
for _strom in (sys.stdout, sys.stderr):
    try:
        _strom.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

LIVE = "https://epkolar.github.io/epkolar-app/index.html"

# Test-Sitzung ohne echte Zugangsdaten: die App braucht nur einen plausibel
# geformten Token und einen User im localStorage. Die Daten-Requests laufen
# danach in 401 - das ist erwartet und stoert den Test nicht, weil er auf
# Abstuerze prueft, nicht auf Inhalte.
INIT = """
try{
  var b=function(s){return btoa(s).replace(/=+$/,'');};
  var jwt=b(JSON.stringify({alg:"HS256",typ:"JWT"}))+"."+
          b(JSON.stringify({sub:"1",role:"authenticated",
                            exp:Math.floor(Date.now()/1000)+86400}))+".sig";
  localStorage.setItem('epkolar_auth',JSON.stringify({at:jwt,rt:"r",exp:Date.now()+86400000}));
  localStorage.setItem('epkolar_user',JSON.stringify({
    id:"1",username:"admin",name:"Sweep",role:"admin",
    rolle:"Geschaeftsfuehrer",permissions:[],perms_override:{}}));
}catch(e){}
"""

# Rauschen des Testzugangs - keine echten Befunde.
IGNORIEREN = ("401", "403", "Failed to load", "net::", "supabase",
              "fetch", "Unauthorized", "workers-load")


# Der Name der IndexedDB der App. Steht in index.html:3146 als DB_NAME.
# Beim ersten Versuch stand hier "epkolar" - indexedDB.open legt eine
# fehlende Datenbank WORTLOS neu an, die Saat landete in einer leeren
# Fremd-DB, und der Lauf blieb gruen. Diese Zeile ist deshalb der
# empfindlichste Punkt des Datenmodus.
DB_NAME = "epkolar_offline"

# ═══ DATENMODUS ═══════════════════════════════════════════════════════════
# ZEILENNUMMERN IN DIESER DATEI SIND HINWEISE, KEINE ADRESSEN. index.html
# waechst taeglich; die hier notierten Nummern waren binnen einer Stunde um
# neun Zeilen daneben. Massgeblich ist immer der mitgegebene SUCHBEGRIFF -
# `grep -n '<begriff>' index.html` findet die Stelle auch morgen noch.
#
# Feldformen aus index.html abgelesen, nicht geraten:
#   Monteur      feld-Filter (`var feld=(monteure||[])`, ~5354)
#                -> {id, n, r, austritt}; r darf nicht
#                Backoffice / Verkauf-Buchhaltung / Geschaeftsfuehrer sein
#   Arbeitsschein `var _termISO=function` (~5358) und der fixMap-Aufbau
#                (`var fixMap={};`, ~5402)
#                -> {id, nummer, kundName, arbeitsort, monteur,
#                    terminBestaetigt (ISO), terminZeit, scheinstatus}
#
# Die Termine liegen bewusst in der NAECHSTEN Woche: fixMap nimmt nur Termine
# ab heute auf, und genau diese Schleife hat am 29.08. die App zerrissen.
#
# DRITTER FEHLER DERSELBEN SORTE, 29.08.2026 - EIN EINZIGES WORT.
# Die Saat trug `scheinstatus:"offen"`. Diesen Status gibt es nicht. Die
# Dispo filtert BEIDE Listen ueber `const AS_GRP_OFFEN=` (~3499) =
# ["aufgenommen","freigegeben","in_bearbeitung","aufgeschoben"], und der
# fixMap-Aufbau steigt bei jedem anderen Wert sofort aus. Ergebnis:
# fixMap leer -> `_fx` leer -> die Kachel-Schleife, in der der Absturz sitzt,
# wird NIE betreten -> das Gate blieb gruen gegen die kaputte Kopie.
# Die Saat sah dabei die ganze Zeit gesund aus: fuenf Scheine in der DB,
# "Testmonteur" im Text. Nur der Renderpfad, um den es geht, blieb kalt.
# Merksatz: ein Datenmodus ist nicht daran zu messen, ob Daten ANKOMMEN,
# sondern daran, ob sie den fraglichen Zweig ANSCHALTEN.
SEED_STATUS = "freigegeben"  # MUSS in AS_GRP_OFFEN stehen, sonst siehe oben.
SEED_JS = """
(async (cfg) => {
  // ERSTER VERSUCH, 29.08.2026 - ZWEI FEHLER, BEIDE STILL:
  // (1) Ich habe die Datenbank 'epkolar' geoeffnet. Sie heisst
  //     'epkolar_offline'. indexedDB.open legt eine fehlende Datenbank
  //     WORTLOS NEU an - die Saat landete also in einer leeren Fremd-DB,
  //     und objectStoreNames.contains() war fuer jeden Speicher falsch.
  // (2) Schlimmer: der Rueckgabewert meldete Erfolg aus der EINGABE
  //     (mon.length), nicht aus dem Ergebnis. Das Geraet gab aus, was man
  //     ihm gegeben hatte. Es haette bei jedem denkbaren Fehler
  //     "2 Monteure gesaet" gesagt.
  // Deshalb wird jetzt ZURUECKGELESEN und die tatsaechlich gespeicherte
  //     Zahl gemeldet; der Aufrufer bricht bei 0 ab.
  const oeffnen = (name) => new Promise((res, rej) => {
    const r = indexedDB.open(name);
    r.onsuccess = () => res(r.result);
    r.onerror = () => rej(r.error);
  });
  const db = await oeffnen(cfg.db);
  const vorhanden = Array.from(db.objectStoreNames);
  const fehlend = Object.keys(cfg.daten).filter(s => vorhanden.indexOf(s) < 0);
  for (const store of Object.keys(cfg.daten)) {
    if (vorhanden.indexOf(store) < 0) continue;
    await new Promise((res) => {
      const tx = db.transaction(store, 'readwrite');
      tx.objectStore(store).put(cfg.daten[store], 'data');
      tx.oncomplete = res; tx.onerror = res; tx.onabort = res;
    });
  }
  // ZURUECKLESEN - das ist die eigentliche Messung.
  const gelesen = {};
  for (const store of Object.keys(cfg.daten)) {
    if (vorhanden.indexOf(store) < 0) { gelesen[store] = -1; continue; }
    gelesen[store] = await new Promise((res) => {
      const tx = db.transaction(store, 'readonly');
      const rq = tx.objectStore(store).get('data');
      rq.onsuccess = () => res(Array.isArray(rq.result) ? rq.result.length : -2);
      rq.onerror = () => res(-3);
    });
  }
  return {gelesen: gelesen, fehlend: fehlend, stores: vorhanden.length};
})
"""


def _naechste_woche():
    """Fuenf Werktage der KOMMENDEN Woche, lokal gerechnet."""
    import datetime
    heute = datetime.date.today()
    montag = heute + datetime.timedelta(days=(7 - heute.weekday()))
    return [(montag + datetime.timedelta(days=k)).isoformat() for k in range(5)]


def saeen(seite):
    """Fuellt die Caches, laedt neu, und BELEGT die Saat durch Rueckle sen.

    Bricht ab, wenn nichts angekommen ist - eine Saat, die man nicht
    nachweisen kann, macht jeden folgenden gruenen Lauf wertlos.
    """
    tage = _naechste_woche()
    mon = [
        {"id": "M1", "n": "Testmonteur A", "r": "Monteur", "austritt": ""},
        {"id": "M2", "n": "Testmonteur B", "r": "Obermonteur", "austritt": ""},
    ]
    scheine = []
    for k, t in enumerate(tage, start=1):
        scheine.append({
            "id": "S%d" % k, "nummer": "AS-%d" % (1000 + k),
            "kundName": "Kunde %d" % k, "arbeitsort": "Krems", "plz": "3500",
            "monteur": "M1" if k % 2 else "M2",
            "terminBestaetigt": t, "terminZeit": "" if k % 3 == 0 else "08:30",
            "scheinstatus": SEED_STATUS, "prio": "normal", "dauer": "2h",
        })
    cfg = {"db": DB_NAME, "daten": {"monteure": mon, "arbeitsscheine": scheine}}
    ergebnis = seite.evaluate(SEED_JS, cfg)

    gelesen = ergebnis.get("gelesen", {})
    if ergebnis.get("fehlend"):
        print("   WARNUNG: diese Speicher gibt es nicht: %s"
              % ", ".join(ergebnis["fehlend"]))
    schlecht = [k for k, v in gelesen.items() if not isinstance(v, int) or v <= 0]
    print("   zurueckgelesen: " + ", ".join(
        "%s=%s" % (k, v) for k, v in sorted(gelesen.items()))
        + "   (%d Speicher in der DB)" % ergebnis.get("stores", 0))
    if schlecht:
        raise SystemExit(
            "ABBRUCH: die Saat ist nicht angekommen (%s). Ein Lauf, dessen "
            "Daten nicht nachweisbar sind, waere gruen und wertlos - genau "
            "der Fehler, den dieser Modus beheben soll."
            % ", ".join(schlecht))

    seite.reload(wait_until="domcontentloaded")
    seite.wait_for_timeout(6000)

    # ═══ DER WICHTIGSTE TEIL: KOMMT DIE SAAT IN DER ANSICHT AN? ═══
    # Nachgewiesen ist bisher nur, dass sie in der Datenbank LIEGT. Ob
    # die App sie liest und rendert, ist eine andere Frage - und sie war
    # am 29.08. mit NEIN zu beantworten: der Cache-Lesepfad existiert
    # (`ODB.load("arbeitsscheine")`, ~8089, laedt arbeitsscheine und monteure und setzt sie in
    # den Zustand), das Raster der Dispo blieb aber leer. Die Ursache ist
    # UNGEKLAERT.
    #
    # Solange sie das ist, darf dieser Modus NICHT gruen melden. Ein Lauf,
    # der behauptet mit Daten geprueft zu haben und in Wahrheit dieselben
    # leeren Ansichten sieht wie der Lauf ohne Daten, waere schlimmer als
    # gar kein Datenmodus - er wuerde die bekannte Luecke als geschlossen
    # ausweisen. Deshalb: sichtbarer Nachweis oder Abbruch.
    sichtbar = seite.evaluate(
        '() => (document.body.innerText.match(/Testmonteur/g)||[]).length')
    if not sichtbar:
        raise SystemExit(
            "ABBRUCH: die Saat liegt in der Datenbank (%s), erscheint aber" % gelesen
            + " in KEINER Ansicht." + chr(10) +
            "   Der Datenmodus ist damit UNFERTIG: er wuerde dieselben leeren" + chr(10) +
            "   Renderpfade pruefen wie der Lauf ohne Daten und das Ergebnis" + chr(10) +
            "   faelschlich als 'mit Daten geprueft' ausweisen." + chr(10) +
            "   Naechster Schritt fuer den, der hier weitermacht: klaeren," + chr(10) +
            "   warum der Cache-Lesepfad (ODB.load, ~8089) die gesaeten" + chr(10) +
            "   Listen nicht in den Zustand bringt.")

    print("   in der Ansicht sichtbar: %d Treffer" % sichtbar)

    # ═══ RIEGEL 3: SCHALTET DIE SAAT DEN FRAGLICHEN ZWEIG UEBERHAUPT AN? ═══
    # Riegel 1 (Rueckle sen) und 2 (Text der Ansicht) waren beide GRUEN,
    # waehrend die Saat wegen eines einzigen falschen Statuswortes exakt
    # nichts bewirkte. Beide messen ANKUNFT, keiner misst WIRKUNG.
    #
    # Dieser Riegel rechnet deshalb mit der Funktion, an der die Kachel
    # haengt: _dispoBuildInput. Ist fixMap danach leer, bleibt `_fx` leer und
    # die Schleife mit dem Absturz wird nie betreten - dann waere jeder
    # folgende gruene Lauf wertlos, und der Lauf bricht hier ab.
    #
    # Bewusst RECHNEN und nicht das Ergebnis im DOM suchen: gegen die kaputte
    # Fassung stuerzt genau dieses Rendern ab. Ein Riegel, der das Rendern
    # verlangt, koennte gegen eine kaputte App nie gruen werden und wuerde
    # den Fund als eigenen Defekt ausgeben.
    nachweis = seite.evaluate("""(cfg) => {
      if (typeof window._dispoBuildInput !== 'function')
        return {fehler: '_dispoBuildInput ist nicht erreichbar'};
      let b;
      try { b = window._dispoBuildInput(cfg.scheine, cfg.monteure, {}, {},
                                        new Date(), undefined, {}, {}, {}); }
      catch (e) { return {fehler: 'wirft: ' + (e && e.message || e)}; }
      if (!b) return {fehler: 'liefert nichts'};
      const fix = b.fixMap || {};
      const isoWoche = {};
      (b.wochen || []).forEach((W, wi) =>
        (W.tage || []).forEach(t => { isoWoche[t.iso] = wi; }));
      let n = 0; const wochen = {};
      Object.keys(fix).forEach(mid => Object.keys(fix[mid] || {}).forEach(iso => {
        n += (fix[mid][iso] || []).length;
        const wi = isoWoche[iso]; if (wi !== undefined) wochen[wi] = (wochen[wi] || 0) + 1;
      }));
      return {fixTermine: n, monteure: Object.keys(fix).length,
              wochen: wochen, horizont: b.horizont || 0, heute: b.heute || ''};
    }""", {"scheine": scheine, "monteure": mon})

    if nachweis.get("fehler") or not nachweis.get("fixTermine"):
        raise SystemExit(
            "ABBRUCH: die Saat erzeugt KEINEN fixen Dispo-Termin (%s)."
            % (nachweis.get("fehler") or "fixMap ist leer") + chr(10) +
            "   Damit bleibt `_fx` leer und die Kachel-Schleife in DispoPanel" + chr(10) +
            "   (Suchbegriff _tagesplan, ~10370) wird nie betreten - genau" + chr(10) +
            "   der Zweig, in dem" + chr(10) +
            "   der Absturz vom 29.08. sass. Ein gruener Lauf waere wertlos." + chr(10) +
            "   Erste Verdaechtige: scheinstatus muss in AS_GRP_OFFEN stehen," + chr(10) +
            "   terminBestaetigt >= heute und im Horizont, monteur gesetzt und" + chr(10) +
            "   seine Rolle nicht Backoffice/Verkauf/Geschaeftsfuehrer.")

    _w = nachweis.get("wochen") or {}
    print("   Dispo-Wirkung: %d fixe Termine bei %d Monteuren, Wochen %s "
          "(Horizont %d, heute %s)"
          % (nachweis["fixTermine"], nachweis["monteure"],
             ",".join(sorted(_w.keys())) or "-", nachweis.get("horizont", 0),
             nachweis.get("heute", "?")))
    if "0" not in _w:
        print("   -> die Termine liegen NICHT in der Startwoche: ohne Klick auf"
              " '▶' bleibt das Raster kalt.")
    return {k: v for k, v in gelesen.items()}


# ═══ WO DAS DISPO-RASTER WIRKLICH STECKT ══════════════════════════════════
# Gesucht war es unter "Planung". Dort ist es nicht. Belegstellen (Suchbegriff
# gilt, die Nummer ist nur die Naeherung von heute):
#   `l:"Planung",i:"📅"`        ~9151  -> perm "wochenplanung" -> WeekPlan.
#                                        Dort gibt es KEIN Dispo-Raster.
#   `l:"Arbeitsscheine",i:"📋"` ~9150  -> perm "arbeitsscheine"
#   `sub==="dispo"&&React.createElement(DispoPanel`  ~11406
#   `id:"dispo",i:"🗓"`         ~11116  - der Sub-Reiter wird nur gebaut, wenn
#                    ["admin","buero","projektleiter"].indexOf(curUser.role)>=0
# Das Raster haengt also an ZWEI Bedingungen: Haupt-Tab Arbeitsscheine UND
# Sub-Reiter Dispo, letzterer nur fuer Buero/PL/Admin. Der INIT-User oben ist
# role:"admin" - deshalb ist der Reiter da. Steht dort je eine andere Rolle,
# verschwindet der Reiter lautlos und dieser Durchlauf misst wieder nichts;
# der Abschluss-Riegel unten faengt genau das ab.
SUB_DISPO_JS = """() => {
  const t = e => (e.textContent||'').trim().replace(/[\\s]+/g,' ');
  for (const bar of document.querySelectorAll('.tab-bar')) {
    if (t(bar).indexOf('Home') >= 0) continue;      // die Haupt-Leiste nie
    const b = [...bar.querySelectorAll('button')]
      .find(x => t(x).indexOf('Dispo') >= 0 && !x.disabled);
    // Nur dieser eine Reiter wird geklickt. 'QR Scan' waere der Nachbar und
    // startet die Kamera (asStartScan, direkt neben `id:"dispo"`) - nichts anfassen,
    // was mehr tut als die Ansicht wechseln.
    if (b) { b.click(); return true; }
  }
  return false;
}"""

# "▶" = eine Woche vorwaerts, "◀" zurueck; beide tragen den title
# "Planungshorizont" (~10510 / ~10519).
# Der erste Anlauf klickte BEIDE (Filter nur ueber title+disabled) - React
# fasst die zwei Klicks zu einem Rendern zusammen, netto blieb die Woche
# stehen und das Raster kalt. Ab jetzt ausschliesslich vorwaerts.
WOCHE_VOR_JS = """() => {
  const b = [...document.querySelectorAll('button')].find(x =>
    (x.title||'').indexOf('Planungshorizont') >= 0
    && (x.textContent||'').indexOf('\\u25b6') >= 0 && !x.disabled);
  if (!b) return false; b.click(); return true;
}"""

# Absturz-Erkennung. Bisher wurde nur auf "App-Fehler" geprueft - das ist der
# GLOBALE Boundary. Ein Render-Fehler in einer einzelnen Ansicht wird aber
# vorher von _ViewBoundary (`class _ViewBoundary`, ~6943) gefangen und meldet sich mit
# 'Tab "<name>" konnte nicht geladen werden'. Genau so kam der Fehler vom
# 29.08. an - und genau deshalb sah der Durchlauf ihn nicht.
ZUSTAND_JS = """(basis) => {
  const txt = document.body.innerText;
  const zeilen = txt.split('\\n').map(z => z.trim()).filter(Boolean);
  const iBound = zeilen.findIndex(z => z.indexOf('konnte nicht geladen werden') >= 0);
  const neue = (window.__EP_ERRORS || []).slice(basis)
                 .map(x => String((x && x.msg) || '').slice(0, 120));
  const global = txt.indexOf('App-Fehler') >= 0;
  return {
    crash: global || iBound >= 0 || neue.length > 0,
    meldung: (iBound >= 0 ? zeilen.slice(iBound, iBound + 2).join(' | ')
              : (neue[0] || (global ? zeilen.slice(0, 3).join(' | ') : '')))
             .slice(0, 130),
    zellen: document.querySelectorAll('[data-dispocell]').length,
    mainPad: !!document.querySelector('.main-pad')
  };
}"""


def main(url=LIVE, mit_daten=False):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt.  pip install playwright && playwright install chromium")
        return 2

    fehler = []
    kaputt = []
    _dispo_knopf = False   # wurde der Sub-Reiter Dispo ueberhaupt gefunden?
    _dispo_zellen = 0      # groesste je gesehene Zahl an Raster-Zellen
    _dispo_crash = False   # das Raster ist beim Blaettern zerbrochen

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 390, "height": 844},
                                  has_touch=True, is_mobile=True)
        ctx.add_init_script(INIT)
        seite = ctx.new_page()
        seite.on("pageerror", lambda e: fehler.append("pageerror: " + str(e)[:140]))

        def konsole(m):
            # In Playwright-fuer-Python sind .type/.text je nach Version Eigenschaft
            # ODER Methode. Trifft man die falsche Variante, vergleicht man gegen ein
            # Funktionsobjekt - der Vergleich ist dann IMMER falsch und das Skript
            # meldet faelschlich "sauber". Genau die Sorte stiller Fehlgruen, die
            # dieses Gate eigentlich verhindern soll. Deshalb beide Formen bedienen.
            art = m.type() if callable(getattr(m, "type", None)) else getattr(m, "type", "")
            if art != "error":
                return
            t = m.text() if callable(getattr(m, "text", None)) else getattr(m, "text", "")
            t = str(t)
            if not any(x.lower() in t.lower() for x in IGNORIEREN):
                fehler.append("console: " + t[:130])
        seite.on("console", konsole)

        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(6000)

        version = seite.evaluate("() => typeof APP_VERSION!=='undefined' ? APP_VERSION : '?'")
        print("Version:", version)
        if mit_daten:
            print("Datenmodus: saee Monteure und Arbeitsscheine mit "
                  "Terminen in der KOMMENDEN Woche ...")
            gesaet = saeen(seite)
            print("   belegt: %d Monteure, %d Arbeitsscheine im Cache"
                  % (gesaet["monteure"], gesaet["arbeitsscheine"]))

        namen = seite.evaluate("""() => {
            const t = e => (e.textContent||'').trim().replace(/\\s+/g,' ');
            const bar = [...document.querySelectorAll('.tab-bar')]
              .find(b => t(b).indexOf('Home')>=0 && t(b).indexOf('Projekte')>=0);
            return bar ? [...bar.querySelectorAll('button')].map(b => t(b).slice(0,18)) : [];
        }""")
        if not namen:
            print("FEHLER: keine Tab-Leiste gefunden - laedt die App ueberhaupt?")
            browser.close()
            return 1

        for i, name in enumerate(namen):
            # __EP_ERRORS wird ueber die ganze Seitensitzung fortgeschrieben.
            # Ohne diesen Stand wuerde ein Fehler aus Tab 4 in Tab 5 bis 18
            # weitergemeldet - achtzehn Ansichten "kaputt", eine Ursache.
            _ep_basis = seite.evaluate(
                "() => (window.__EP_ERRORS||[]).length")
            seite.evaluate("""(idx) => {
                const t = e => (e.textContent||'').trim().replace(/\\s+/g,' ');
                const bar = [...document.querySelectorAll('.tab-bar')]
                  .find(b => t(b).indexOf('Home')>=0 && t(b).indexOf('Projekte')>=0);
                if(!bar) return;
                const bs = [...bar.querySelectorAll('button')];
                if(bs[idx]) bs[idx].click();
            }""", i)
            seite.wait_for_timeout(1100)

            # ═══ NACHKLICK ═══════════════════════════════════════════
            # Ein Durchlauf, der nur TABS oeffnet, sieht nichts, was hinter
            # einem Klick liegt. Genau daran ist er am 29.08. gescheitert:
            # der Absturz sass in der Dispo, aber erst NACH dem Wechsel auf
            # eine spaetere Woche - fixMap nimmt nur Termine ab heute auf,
            # und die Startwoche war an jenem Samstag komplett Vergangenheit.
            # Geklickt wird nur, was eindeutig eine ANSICHT wechselt und
            # nichts schreibt: der Sub-Reiter Dispo und danach "▶".
            zustand = seite.evaluate(ZUSTAND_JS, _ep_basis)
            if not zustand["crash"] and seite.evaluate(SUB_DISPO_JS):
                _dispo_knopf = True
                seite.wait_for_timeout(1200)
                zustand = seite.evaluate(ZUSTAND_JS, _ep_basis)
                _dispo_zellen = max(_dispo_zellen, zustand["zellen"])
                # Durch den ganzen Horizont blaettern und nach JEDEM Schritt
                # messen. Wer erst am Ende hinsieht, verliert den Befund: ein
                # spaeterer Klick auf eine heile Woche kann die Boundary
                # zuruecksetzen und den Absturz wieder wegrendern.
                for _w in range(4):
                    if zustand["crash"] or not seite.evaluate(WOCHE_VOR_JS):
                        break
                    seite.wait_for_timeout(1000)
                    zustand = seite.evaluate(ZUSTAND_JS, _ep_basis)
                    _dispo_zellen = max(_dispo_zellen, zustand["zellen"])
                if zustand["crash"]:
                    _dispo_crash = True

            if zustand["crash"]:
                print("  %-20s KAPUTT -> %s" % (name, zustand["meldung"]))
                kaputt.append(name)
                seite.reload(wait_until="domcontentloaded")
                seite.wait_for_timeout(5000)
            elif not zustand["mainPad"]:
                print("  %-20s kein Inhaltsbereich" % name)
                kaputt.append(name)
            else:
                print("  %-20s ok" % name)

        browser.close()

    print()
    # ═══ RIEGEL 4: IST DAS RASTER UEBERHAUPT BETRETEN WORDEN? ═══════════
    # Der teuerste Zustand dieses Werkzeugs ist nicht "rot", sondern "gruen,
    # ohne hingesehen zu haben". Im Datenmodus ist deshalb ausdruecklich
    # nachzuweisen, dass der Renderpfad LIEF: Sub-Reiter gefunden UND
    # entweder Zellen gerendert ODER ein Absturz gemeldet. Fehlt beides,
    # bricht der Lauf ab, statt eine Ansicht als geprueft auszuweisen, die
    # nie gemountet war.
    if mit_daten and not _dispo_crash:
        if not _dispo_knopf:
            raise SystemExit(
                "ABBRUCH: der Sub-Reiter 'Dispo' wurde in KEINER Ansicht"
                " gefunden." + chr(10) +
                "   Er haengt an der Rolle (Suchbegriff id:'dispo', ~11116,"
                " nur admin/buero/projektleiter)" + chr(10) +
                "   und sitzt im Haupt-Tab Arbeitsscheine, NICHT unter"
                " 'Planung'." + chr(10) +
                "   Ohne ihn ist das Dispo-Raster nie gemountet und dieser"
                " Lauf hat" + chr(10) +
                "   den Renderpfad nicht geprueft, um den es geht.")
        if _dispo_zellen <= 0:
            raise SystemExit(
                "ABBRUCH: der Sub-Reiter 'Dispo' war da, aber das Raster hat"
                " KEINE Zelle" + chr(10) +
                "   gerendert ([data-dispocell] = 0). Ohne Raster-Zeile keine"
                " Kachel" + chr(10) +
                "   und ohne Kachel kein Absturz - der Lauf haette gruen"
                " gemeldet," + chr(10) +
                "   ohne zu messen. Verdaechtig: die Rollen der gesaeten"
                " Monteure" + chr(10) +
                "   (feld-Filter, Suchbegriff var feld=, ~5354) oder ein Austritt.")
        print("Dispo-Raster betreten: bis zu %d Zellen gerendert." % _dispo_zellen)
    if kaputt:
        print("KAPUTT: " + ", ".join(kaputt))
    if fehler:
        print("JS-Fehler:")
        for f in fehler[:10]:
            print("   " + f)
    if not kaputt and not fehler:
        print("Alle %d Ansichten sauber." % len(namen))
        if not mit_daten:
            print()
            print("ACHTUNG: Lauf OHNE Daten. Alle Listen sind leer, jeder"
                  " Renderpfad,")
            print("   der Inhalt braucht, wurde NICHT betreten - genau dort"
                  " sass der")
            print("   Absturz vom 29.08. Zusaetzlich mit --daten laufen"
                  " lassen.")
        return 0
    return 1


if __name__ == "__main__":
    _args = [a for a in sys.argv[1:] if not a.startswith("--")]
    _daten = "--daten" in sys.argv[1:]
    sys.exit(main(_args[0] if _args else LIVE, _daten))
