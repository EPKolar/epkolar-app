# -*- coding: utf-8 -*-
"""Steht der gewaehlte Wert bei JEDEM Auswahlfeld unter den Optionen?

WORAUS DAS ENTSTAND (v3.9.919)
------------------------------
Die Prioritaets-Auswahl der Arbeitsschein-Liste hatte einen Wert, der auf
"keine" fiel, und einen Optionsvorrat, aus dem "keine" herausgefiltert war.
Ein select ohne passende Option zeigt die ERSTE - und die erste Stufe in
AS_PRIO ist "aufgeschoben". Ein Schein ohne Prioritaet sah dadurch aus wie ein
aufgeschobener, und der DOM-Wert des Feldes WAR "aufgeschoben".

Die Regel dieses Repos: eine Reparatur an einer von vier Stellen ist keine.
index.html hat 118 Auswahlfelder. Sie einzeln nachzulesen ist Raten mit
Mehraufwand. Dieses Werkzeug MISST stattdessen die Eigenschaft selbst:

    DER GEWAEHLTE WERT MUSS UNTER DEN ANGEBOTENEN OPTIONEN SEIN.

WIE GEMESSEN WIRD
-----------------
Nicht ueber den DOM. Der DOM kann die Frage gar nicht beantworten: passt der
Wert zu keiner Option, setzt React KEINE Option auf selected, der Browser
waehlt daraufhin die erste - und danach sieht das Feld voellig gesund aus.
Der Beweis ist zu diesem Zeitpunkt schon vernichtet.

Gemessen wird deshalb eine Ebene frueher: `React.createElement` wird
umhuellt. Bei jedem Aufruf mit type==='select' wird die value-Prop mit den
Werten der bereits erzeugten option-Kinder verglichen - genau das Paar, das
React gleich selbst vergleichen wird. Die App schreibt ihre Aufrufe woertlich
als `React.createElement(...)` gegen das globale React, deshalb greift die
Huelle ohne Eingriff in index.html.

Der Vergleich bildet ab, was React tut (ReactDOM.updateOptions):
  * die Option ohne value-Attribut traegt ihren Text als Wert
  * verglichen wird als Zeichenkette ('' + wert)

GEGENPROBE
----------
Ohne Umkehr waere nicht belegt, dass die Huelle ueberhaupt etwas sieht. Mit
--gegenprobe wird ein select mit einem garantiert fremden Wert gerendert und
gerufen; erscheint es NICHT im Bericht, misst das Werkzeug nichts und der Lauf
bricht ab.

BENUTZUNG
---------
    python scripts/select_wert_messen.py               # lokal, mit Saat
    python scripts/select_wert_messen.py --live
"""
import os
import sys
import threading

for _strom in (sys.stdout, sys.stderr):
    try:
        _strom.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)

from tab_sweep import INIT, DB_NAME, SEED_JS  # noqa: E402

LIVE = "https://epkolar.github.io/epkolar-app/index.html"

# ═══ DIE HUELLE ═══════════════════════════════════════════════════════════
# Wird NACH dem Laden gesetzt. Die App ruft `React.createElement` gegen das
# globale React auf (index.html schreibt es woertlich aus), also greift jede
# spaetere Neuzeichnung durch die Huelle.
HUELLE_JS = r"""() => {
  if (window.__selHuelle) return 'schon da';
  const R = window.React;
  if (!R || typeof R.createElement !== 'function') return 'kein React';
  const orig = R.createElement;
  window.__selFunde = [];
  window.__selGesehen = 0;
  // Jede gerenderte Stelle EINMAL. Ohne diese Liste waere unbekannt, welche
  // der 118 Auswahlfelder ueberhaupt gemessen wurden - und ein Bericht ueber
  // ungemessene Felder ist genau die Sorte gruen, die nichts wert ist.
  window.__selOrte = {};

  // Der Wert einer Option, so wie der Browser ihn liefert: das value-Attribut,
  // sonst der Text des Elements. Genau daran vergleicht ReactDOM.
  const optWert = (el) => {
    const p = (el && el.props) || {};
    if (Object.prototype.hasOwnProperty.call(p, 'value')) return '' + p.value;
    const t = [];
    const sammel = (c) => {
      if (c === null || c === undefined || typeof c === 'boolean') return;
      if (Array.isArray(c)) { c.forEach(sammel); return; }
      if (typeof c === 'object') { sammel(c.props && c.props.children); return; }
      t.push('' + c);
    };
    sammel(p.children);
    return t.join('').trim();
  };

  const optionen = (knoten, raus) => {
    if (knoten === null || knoten === undefined || typeof knoten === 'boolean') return;
    if (Array.isArray(knoten)) { knoten.forEach(k => optionen(k, raus)); return; }
    if (typeof knoten !== 'object') return;
    if (knoten.type === 'option') { raus.push(optWert(knoten)); return; }
    if (knoten.type === 'optgroup' || typeof knoten.type !== 'function') {
      optionen(knoten.props && knoten.props.children, raus);
    }
  };

  R.createElement = function (typ, props) {
    const el = orig.apply(this, arguments);
    try {
      if (typ === 'select' && props &&
          Object.prototype.hasOwnProperty.call(props, 'value')) {
        window.__selGesehen++;
        const raus = [];
        for (let i = 2; i < arguments.length; i++) optionen(arguments[i], raus);
        const _st0 = (new Error()).stack || '';
        const _ort0 = (_st0.match(/index\.html:(\d+):(\d+)/g) || [])[0] || '?';
        window.__selOrte[_ort0] = (window.__selOrte[_ort0] || 0) + 1;
        if (raus.length) {
          const w = '' + props.value;
          if (raus.indexOf(w) < 0) {
            const st = _st0;
            window.__selFunde.push({
              wert: w,
              roh: props.value === undefined ? '(undefined)'
                   : props.value === null ? '(null)' : typeof props.value,
              zeigt: raus[0],
              anzahl: raus.length,
              optionen: raus.slice(0, 12),
              ort: st.split('\n').slice(1, 5)
                     .map(z => (z.match(/index\.html:(\d+):(\d+)/) || [])[0] || '')
                     .filter(Boolean).slice(0, 2).join(' <- ')
            });
          }
        }
      }
    } catch (e) { /* messen darf nie rendern verhindern */ }
    return el;
  };
  window.__selHuelle = true;
  return 'gesetzt';
}"""

# Die Gegenprobe rendert ein select, dessen Wert garantiert unter KEINER
# Option steht - und verlangt, dass die Huelle genau das meldet.
GEGENPROBE_JS = r"""() => {
  const vorher = (window.__selFunde || []).length;
  const R = window.React;
  R.createElement('select', {value: 'GIBT-ES-NICHT'},
    R.createElement('option', {value: 'a'}, 'A'),
    R.createElement('option', {}, 'B'));
  // Und die Umkehr der Umkehr: ein sauberes select darf NICHT anschlagen.
  R.createElement('select', {value: 'B'},
    R.createElement('option', {value: 'a'}, 'A'),
    R.createElement('option', {}, 'B'));
  const nachher = (window.__selFunde || []).length;
  const neu = (window.__selFunde || []).slice(vorher);
  return {zuwachs: nachher - vorher,
          wert: neu.length ? neu[0].wert : null,
          zeigt: neu.length ? neu[0].zeigt : null};
}"""

TABS_JS = r"""() => {
  const t = e => (e.textContent || '').trim().replace(/\s+/g, ' ');
  const bar = [...document.querySelectorAll('.tab-bar')]
    .find(b => t(b).indexOf('Home') >= 0 && t(b).indexOf('Projekte') >= 0);
  return bar ? [...bar.querySelectorAll('button')].map(b => t(b).slice(0, 18)) : [];
}"""

KLICK_TAB_JS = r"""(idx) => {
  const t = e => (e.textContent || '').trim().replace(/\s+/g, ' ');
  const bar = [...document.querySelectorAll('.tab-bar')]
    .find(b => t(b).indexOf('Home') >= 0 && t(b).indexOf('Projekte') >= 0);
  if (!bar) return false;
  const bs = [...bar.querySelectorAll('button')];
  if (!bs[idx]) return false;
  bs[idx].click();
  return true;
}"""

# Unter-Reiter derselben Ansicht durchklicken. Ohne das bleiben Dispo,
# Kalender, Mangel-Listen und die Fahrzeug-Unteransichten ungemessen.
SUBTABS_JS = r"""() => {
  const t = e => (e.textContent || '').trim().replace(/\s+/g, ' ');
  let n = 0;
  for (const bar of document.querySelectorAll('.tab-bar')) {
    if (t(bar).indexOf('Home') >= 0 && t(bar).indexOf('Projekte') >= 0) continue;
    for (const b of [...bar.querySelectorAll('button')]) {
      if (b.disabled) continue;
      const s = t(b);
      // Nichts anfassen, was mehr tut als die Ansicht wechseln.
      if (/Scan|Kamera|Foto|Löschen|Senden|Export|Druck|PDF/i.test(s)) continue;
      try { b.click(); n++; } catch (e) {}
    }
  }
  return n;
}"""


# Formulare und Detailansichten oeffnen. Ohne diesen Schritt bleiben rund ein
# Drittel der Auswahlfelder ungemessen - sie stehen in Modalen (Schein
# bearbeiten, Fahrzeug anlegen, Werkzeug-Service), die kein Tab-Klick erreicht.
# Geklickt wird nur, was OEFFNET. Alles, was speichern, loeschen, senden,
# scannen oder drucken koennte, ist ausgeschlossen; die Auswahl ist eine
# Positivliste, keine Negativliste, damit ein neuer Knopf nicht stillschweigend
# mitgeklickt wird.
OEFFNEN_JS = r"""(runde) => {
  const t = e => (e.textContent || '').trim().replace(/\s+/g, ' ');
  const OEFFNET = /^(\+|＋|➕|✏️?|📝|Neu|Neue[rs]?|Bearbeiten|Details?|Öffnen|Hinzufügen|Zuweisen)\b/i;
  const kandidaten = [...document.querySelectorAll('button,[role=button]')]
    .filter(b => !b.disabled && OEFFNET.test(t(b)));
  const b = kandidaten[runde];
  if (!b) return {fertig: true, anzahl: kandidaten.length};
  try { b.click(); } catch (e) {}
  return {fertig: false, anzahl: kandidaten.length, text: t(b).slice(0, 30)};
}"""

# Ein geoeffnetes Modal muss wieder zu, sonst verdeckt es die naechsten Knoepfe.
SCHLIESSEN_JS = r"""() => {
  const t = e => (e.textContent || '').trim();
  const zu = [...document.querySelectorAll('button')]
    .filter(b => !b.disabled && /^(×|✕|✖|X|Abbrechen|Schließen|Zurück)$/i.test(t(b)));
  if (zu.length) { try { zu[zu.length - 1].click(); return true; } catch (e) {} }
  return false;
}"""


def _server():
    import http.server
    import socketserver
    os.chdir(WURZEL)

    class Still(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    srv = socketserver.TCPServer(("127.0.0.1", 0), Still)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv.server_address[1]


def _saat():
    """Absichtlich VERALTETE Verweise - das ist der Kern der Messung.

    Ein Datenbestand, in dem jeder Verweis noch auf ein lebendes Ziel zeigt,
    kann die Frage gar nicht beantworten. Gesaet wird deshalb genau das, was
    im Betrieb entsteht und was ein select aus seinem Vorrat wirft:
      * ein AUSGETRETENER Monteur, der noch Scheine traegt
      * ein Monteur, den es GAR NICHT MEHR gibt (Verweis ins Leere)
      * ein ARCHIVIERTES Projekt, auf das noch gebucht ist
      * ein Schein ohne Prioritaet / ohne Status / ohne Sachbearbeiter
    """
    import datetime
    heute = datetime.date.today()
    frueher = (heute - datetime.timedelta(days=90)).isoformat()
    montag = heute + datetime.timedelta(days=(7 - heute.weekday()))
    tage = [(montag + datetime.timedelta(days=k)).isoformat() for k in range(5)]

    monteure = [
        {"id": "M1", "n": "Aktiv Anton", "r": "Monteur", "austritt": "", "fs": "B,C"},
        {"id": "M2", "n": "Aktiv Berta", "r": "Obermonteur", "austritt": "", "fs": "B"},
        # Der entscheidende Fall: ausgetreten, traegt aber noch Scheine.
        {"id": "M9", "n": "Ehemalig Egon", "r": "Monteur", "austritt": frueher, "fs": "B,C"},
    ]
    projekte = [
        {"id": "P1", "nr": "24-001", "name": "Aktiv Projekt", "status": "aktiv", "ort": "Krems"},
        {"id": "P9", "nr": "20-009", "name": "Archiv Projekt", "status": "archiv", "ort": "Wien"},
    ]
    scheine = []
    for k, t in enumerate(tage, start=1):
        scheine.append({
            "id": "S%d" % k, "nummer": "AS-%d" % (1000 + k),
            "kundName": "Kunde %d" % k, "arbeitsort": "Krems", "plz": "3500",
            "monteur": ["M1", "M2", "M9", "M_GELOESCHT", "M1"][k - 1],
            "terminBestaetigt": t, "terminZeit": "08:30",
            # Schein 4 traegt GAR KEINEN Status - dieselbe Leerform, aus der
            # v3.9.919 entstand, nur an einem anderen Feld.
            "scheinstatus": "freigegeben" if k != 4 else None,
            "sachbearbeiter": "" if k % 2 else "Gibt Es Nicht",
            "projekt": "P9" if k == 3 else "P1",
            "dauer": "2h",
        })
    fahrzeuge = [
        {"id": "F1", "kennzeichen": "KR-1", "marke": "VW", "typ": "Bus",
         "fahrer": "M9", "vignette_typ": ""},
    ]
    # p7 ist ein Projekt, das es WIRKLICH gibt (INIT_PROJECTS), aber mit
    # status "abgeschlossen". Genau das entsteht im Betrieb: das Projekt wird
    # fertig, das Geraet liegt noch darauf. Ein erfundener Verweis (P_WEG)
    # steht daneben, weil er die GRENZE der Reparatur zeigt: ein Projekt, das
    # gar nicht mehr in der Liste ist, kann kein Filter zurueckholen.
    werkzeuge = [
        {"id": "W1", "inventarnr": "WZ-1", "name": "Bohrer", "kat": "elektro",
         "status": "verfuegbar", "zugewiesen": "M9", "projekt": "p7"},
        {"id": "W2", "inventarnr": "WZ-2", "name": "Messgeraet", "kat": "mess",
         "status": "verfuegbar", "zugewiesen": "M1", "projekt": "P_WEG"},
    ]
    return {"monteure": monteure, "arbeitsscheine": scheine, "projects": projekte,
            "fahrzeuge": fahrzeuge, "werkzeuge": werkzeuge}


def main(argv):
    from playwright.sync_api import sync_playwright

    live = "--live" in argv
    url = LIVE if live else None

    port = None
    if not live:
        port = _server()
        url = "http://127.0.0.1:%d/index.html" % port

    funde = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        c = b.new_context(viewport={"width": 1440, "height": 900})
        c.add_init_script(INIT)
        p = c.new_page()
        p.goto(url, wait_until="domcontentloaded")
        p.wait_for_timeout(5000)

        daten = _saat()
        erg = p.evaluate(SEED_JS, {"db": DB_NAME, "daten": daten})
        print("Saat zurueckgelesen:", erg.get("gelesen"), " fehlend:", erg.get("fehlend"))
        gelesen = erg.get("gelesen") or {}
        if not any(v and v > 0 for v in gelesen.values()):
            print("ABBRUCH: nichts angekommen - ein Lauf ohne Daten misst die "
                  "Datenfaelle gar nicht.")
            b.close()
            return 2

        p.reload(wait_until="domcontentloaded")
        p.wait_for_timeout(5000)

        print("Huelle:", p.evaluate(HUELLE_JS))

        gp = p.evaluate(GEGENPROBE_JS)
        print("Gegenprobe:", gp)
        if gp.get("zuwachs") != 1 or gp.get("wert") != "GIBT-ES-NICHT":
            print("ABBRUCH: die Huelle sieht den gebauten Fehler NICHT (oder "
                  "schlaegt beim sauberen Feld an). Jeder gruene Bericht waere "
                  "wertlos.")
            b.close()
            return 2
        p.evaluate("() => { window.__selFunde = []; }")

        tabs = p.evaluate(TABS_JS)
        if not tabs:
            print("ABBRUCH: keine Tab-Leiste - laedt die App ueberhaupt?")
            b.close()
            return 2
        print("Ansichten:", len(tabs))

        for i, name in enumerate(tabs):
            p.evaluate(KLICK_TAB_JS, i)
            p.wait_for_timeout(900)
            n = p.evaluate(SUBTABS_JS)
            p.wait_for_timeout(900)
            # Formulare oeffnen - hoechstens 12 je Ansicht, sonst laeuft der
            # Durchgang aus dem Ruder.
            for runde in range(12):
                r = p.evaluate(OEFFNEN_JS, runde)
                if r.get("fertig"):
                    break
                p.wait_for_timeout(500)
                p.evaluate(SCHLIESSEN_JS)
                p.wait_for_timeout(250)
            orte = p.evaluate("() => Object.keys(window.__selOrte).length")
            print("  %-20s Unter-Reiter %-3d Stellen bisher %d"
                  % (name, n, orte))

        funde = p.evaluate("() => window.__selFunde")
        gesehen = p.evaluate("() => window.__selGesehen")
        orte = p.evaluate("() => window.__selOrte")
        b.close()

    print()
    # Ehrlichkeit ueber die Reichweite: welche Fundorte hat dieser Lauf
    # ueberhaupt angefasst? Ein Bericht ueber 118 Auswahlfelder, der nur 25
    # gerendert hat, muss das sagen - sonst liest sich "keine Funde" wie
    # "alles geprueft". Nichts wird in den Baum geschrieben.
    print("gemessene Stellen (verschiedene Fundorte in index.html): %d" % len(orte))
    print("   " + ", ".join(sorted(orte, key=lambda k: k)))

    print()
    print("select-Aufrufe mit value insgesamt gesehen:", gesehen)
    if not funde:
        print("KEIN Auswahlfeld hatte einen Wert ausserhalb seiner Optionen.")
        return 0

    # Nach Fundort zusammenfassen - dieselbe Stelle rendert oft hundertfach.
    nach_ort = {}
    for f in funde:
        s = nach_ort.setdefault((f["ort"], f["wert"]), dict(f, n=0))
        s["n"] += 1
    print("FUNDE: %d Stellen (%d Aufrufe)" % (len(nach_ort), len(funde)))
    print()
    for (ort, wert), f in sorted(nach_ort.items(), key=lambda x: -x[1]["n"]):
        print("  %s   x%d" % (ort or "(ohne Ort)", f["n"]))
        print("     Wert %r (%s) steht NICHT unter %d Optionen"
              % (wert, f["roh"], f["anzahl"]))
        print("     Das Feld zeigt stattdessen: %r" % f["zeigt"])
        print("     Optionen: %s" % ", ".join(repr(o) for o in f["optionen"]))
        print()
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
