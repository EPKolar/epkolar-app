# -*- coding: utf-8 -*-
"""Probe: die Werkzeug-Ansicht am GERENDERTEN Schirm messen.

WOZU
────
`tests/test_werkzeuge_vorbereitet_v940.py` sichert den Quelltext. Der Quelltext
kann aber nur sagen, dass die Teile DASTEHEN. Ob die fuenf Reiter gezeichnet
werden, ob in den Auswahlfeldern wirklich sechs Statuswerte und neun Kategorien
zur Wahl stehen, ob die Chips ihre Zaehler zeigen und ob irgendwo Text
abgeschnitten wird - das sagt nur der Schirm.

WAS GEMESSEN WIRD
─────────────────
  Reiter      die Reiterzeile der Werkzeug-Ansicht: Zahl, Text, title,
              aria-label, Tippflaeche - bei 390 px UND bei 1440 px
  Status      das Auswahlfeld im Listenfilter und das im Formular:
              stehen alle SECHS Statuswerte zur Wahl
  Kategorien  dieselben zwei Felder: stehen alle NEUN Kategorien zur Wahl
  Chips       fuenf Filter-Chips, jeder mit seinem Zaehler in Klammern
  Beschnitt   scrollWidth gegen clientWidth, ueber die ganze Ansicht

DIE KOEDER (Regel 3)
────────────────────
1. SAAT. Die Werkzeuge werden in die IndexedDB gesaet und ZURUECKGELESEN. Kommt
   nichts an, bricht die Probe ab - eine Werkzeugliste mit null Geraeten haette
   fuenf Chips mit "(0)" und waere gruen und wertlos.
2. BESCHNITTMELDER. Ein eigens eingehaengtes Feld mit 240 Zeichen in 80 px MUSS
   gefunden werden. Findet der Melder es nicht, misst er nichts - und "kein
   Beschnitt" heisst dann nur "nichts gesehen".
3. REITERTEXT. Bei 1440 px MUSS mindestens ein Reiter Text tragen. Trifft das
   nirgends zu, sagt "am Telefon tragen sie nur die Ikone" nichts aus.

REGEL 4
───────
Was nicht gemessen werden konnte, steht im Schlusstext als NICHT GEMESSEN und
wird nicht als bestanden gefuehrt.

AUFRUF
──────
    python scripts/werkzeuge_probe.py
"""
import os
import sys

for _strom in (sys.stdout, sys.stderr):
    try:
        _strom.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import mob_ansicht_messen as M  # noqa: E402

# ── Die Saat ──────────────────────────────────────────────────────────────
# Feldformen aus `const defWz=()=>({...})` in index.html abgelesen, nicht
# geraten: id, name, kat, seriennr, inventarnr, status, zugewiesen, projekt,
# standort, letzteKalib, naechsteKalib, anschaffung, wert, notizen,
# zustandBewertung.
#
# WICHTIG, DIESELBE LEHRE WIE BEIM SCHEINSTATUS AM 29.08.: die Saat muss die
# fraglichen ZWEIGE ANSCHALTEN, nicht bloss ankommen. Deshalb je einer fuer
# jeden Chip: verfuegbar, ausgegeben, verloren und einer mit ABGELAUFENER
# Kalibrierung (der Chip `kalib_faellig` zaehlt ueber `_wzKalibFaellig`, nicht
# ueber den Status - ein verfuegbares Geraet kann faellig sein).
MONTEURE = [
    {"id": "M1", "n": "Gerhard Steinbichler", "r": "Monteur", "austritt": ""},
    {"id": "M2", "n": "Johannes Hinterleitner", "r": "Obermonteur",
     "austritt": ""},
]

WERKZEUGE = [
    {"id": "W1", "name": "Hilti TE 30-A36 Kombihammer", "kat": "elektro",
     "seriennr": "TE30-2019-4471", "inventarnr": "EK-E001",
     "status": "verfuegbar", "zugewiesen": "", "projekt": "",
     "standort": "Lager", "letzteKalib": "", "naechsteKalib": "",
     "anschaffung": "2019-04-11", "wert": 1290, "notizen": "",
     "zustandBewertung": 4},
    {"id": "W2", "name": "Fluke 1664 FC Installationstester", "kat": "mess",
     "seriennr": "FL1664-7788", "inventarnr": "EK-M002",
     "status": "verfuegbar", "zugewiesen": "", "projekt": "",
     "standort": "Lager", "letzteKalib": "2024-02-01",
     "naechsteKalib": "2025-02-01", "anschaffung": "2018-09-03",
     "wert": 2480, "notizen": "Kalibrierung ueberfaellig",
     "zustandBewertung": 5},
    {"id": "W3", "name": "Knipex Kabelschere 95 32 038", "kat": "kabel",
     "seriennr": "KN-95-038", "inventarnr": "EK-K003",
     "status": "ausgegeben", "zugewiesen": "M1", "projekt": "",
     "standort": "Baustelle", "letzteKalib": "", "naechsteKalib": "",
     "anschaffung": "2021-06-22", "wert": 210, "notizen": "",
     "zustandBewertung": 4},
    {"id": "W4", "name": "Guenzburger Stehleiter 8 Stufen", "kat": "leiter",
     "seriennr": "GZ-8ST-1190", "inventarnr": "EK-L004",
     "status": "verloren", "zugewiesen": "", "projekt": "",
     "standort": "unbekannt", "letzteKalib": "", "naechsteKalib": "",
     "anschaffung": "2017-03-14", "wert": 340,
     "notizen": "Auf der Baustelle Marktgemeinde Sankt Leonhard verschwunden",
     "zustandBewertung": 2},
    {"id": "W5", "name": "Bosch GBH 18V-26 F Akku-Bohrhammer mit Wechselfutter",
     "kat": "maschine", "seriennr": "GBH-18V-26F-55231",
     "inventarnr": "EK-A005", "status": "reparatur", "zugewiesen": "",
     "projekt": "", "standort": "Werkstatt/Service", "letzteKalib": "",
     "naechsteKalib": "", "anschaffung": "2022-11-08", "wert": 620,
     "notizen": "", "zustandBewertung": 3},
    {"id": "W6", "name": "Schutzhelm uvex pheos alpine", "kat": "sicherheit",
     "seriennr": "UV-PH-0091", "inventarnr": "EK-S006",
     "status": "stillgelegt", "zugewiesen": "", "projekt": "",
     "standort": "Lager", "letzteKalib": "", "naechsteKalib": "",
     "anschaffung": "2015-05-19", "wert": 45,
     "notizen": "Ablaufdatum erreicht", "zustandBewertung": 1},
]

STATUS_SOLL = ["Verfügbar", "Ausgegeben", "In Reparatur",
               "Kalibrierung fällig", "Verloren/Defekt", "Stillgelegt"]

KAT_SOLL = ["Elektrowerkzeug", "Messgeräte", "Handwerkzeug", "Maschinen",
            "Sicherheit/PSA", "Verbrauchsmaterial", "Kabelwerkzeug",
            "Leiter/Gerüst", "Sonstiges"]

CHIPS_SOLL = ["Alle", "Verfügbar", "Ausgegeben", "Kalibrierung fällig",
              "Defekt"]

REITER_SOLL = ["\U0001f4f7", "\U0001f4cb", "\U0001f4e4", "\U0001f527",
               "✏"]


# ── Die Messungen im Browser ──────────────────────────────────────────────
# Die Reiterzeile der Werkzeug-Ansicht traegt die Klasse `tab-bar` - die
# HAUPTNAVIGATION aber auch. Gesucht wird deshalb nicht nach der Klasse,
# sondern nach der EIGENSCHAFT: der Streifen, dessen Knoepfe die Kamera-Ikone
# enthalten. Wer hier die erste .tab-bar nimmt, misst die Hauptnavigation und
# bekommt eine saubere Zahl fuer die falsche Sache.
REITER_JS = """() => {
  const streifen = Array.from(document.querySelectorAll('.tab-bar')).find(e => {
    const b = Array.from(e.querySelectorAll(':scope > button'));
    return b.length >= 3 && b.some(x => (x.textContent || '').includes('\\uD83D\\uDCF7'));
  });
  if (!streifen) return {fehler: 'keine Werkzeug-Reiterzeile gefunden'};
  const knoepfe = Array.from(streifen.querySelectorAll(':scope > button'));
  return {
    anzahl: knoepfe.length,
    reiter: knoepfe.map(b => {
      const r = b.getBoundingClientRect();
      return {
        text: (b.textContent || '').trim(),
        nurIkone: (b.textContent || '').trim().replace(/[\\s\\uFE0F]/g, '').length <= 2,
        title: b.getAttribute('title'),
        aria: b.getAttribute('aria-label'),
        breite: Math.round(r.width),
        hoehe: Math.round(r.height)
      };
    }),
    quer_rollbar: streifen.scrollWidth > streifen.clientWidth + 1
  };
}"""

# Reiter antippen - ueber die Ikone, denn am Telefon ist sie der ganze Text.
REITER_TIPPEN_JS = """(ikone) => {
  const streifen = Array.from(document.querySelectorAll('.tab-bar')).find(e => {
    const b = Array.from(e.querySelectorAll(':scope > button'));
    return b.length >= 3 && b.some(x => (x.textContent || '').includes('\\uD83D\\uDCF7'));
  });
  if (!streifen) return 'keine-reiterzeile';
  const t = Array.from(streifen.querySelectorAll(':scope > button'))
    .find(b => (b.textContent || '').includes(ikone));
  if (!t) return 'reiter-nicht-gefunden';
  t.click();
  return 'geklickt';
}"""

# Alle Auswahlfelder der Ansicht mit ihren Optionstexten. Zugeordnet wird
# NICHT ueber die Reihenfolge im DOM (die verschiebt sich beim Umbau), sondern
# ueber den gebundenen Wert bzw. die Optionsmenge.
SELECTS_JS = """() => {
  return Array.from(document.querySelectorAll('select')).map(s => {
    const r = s.getBoundingClientRect();
    return {
      wert: s.value,
      sichtbar: r.width > 0 && r.height > 0,
      optionen: Array.from(s.options).map(o => (o.textContent || '').trim())
    };
  });
}"""

CHIPS_JS = """() => {
  // Ein Filter-Chip ist ein Knopf mit runder Ecke, dessen Text auf "(n)"
  // endet. Gesucht wird ueber diese Form, nicht ueber eine Klasse.
  const alle = Array.from(document.querySelectorAll('button'))
    .filter(b => /\\(\\d+\\)\\s*$/.test((b.textContent || '').trim()));
  return alle.map(b => {
    const t = (b.textContent || '').trim();
    const m = t.match(/\\((\\d+)\\)\\s*$/);
    const r = b.getBoundingClientRect();
    return {text: t, zahl: m ? parseInt(m[1], 10) : null,
            beschnitt: b.scrollWidth > b.clientWidth + 1,
            hoehe: Math.round(r.height)};
  });
}"""

AUSLEIHEN_JS = """() => {
  const n = Array.from(document.querySelectorAll('button'))
    .filter(b => (b.textContent || '').includes('Ausleihen'));
  return {anzahl: n.length,
          hoehen: n.map(b => Math.round(b.getBoundingClientRect().height))};
}"""

# Der Beschnittmelder. Gemessen wird der HAUPTBEREICH, nicht das ganze
# Dokument - sonst faengt man die Randleiste mit. Bereiche, die querrollen
# DUERFEN (overflow-x auto/scroll), werden getrennt gefuehrt und nicht als
# Fehler gemeldet.
BESCHNITT_JS = """() => {
  const wurzel = document.querySelector('.main-pad') || document.body;
  const schlimm = [], gewollt = [];
  wurzel.querySelectorAll('*').forEach(e => {
    if (e.scrollWidth <= e.clientWidth + 1) return;
    const t = (e.textContent || '').replace(/\\s+/g, ' ').trim();
    if (!t) return;
    const ox = getComputedStyle(e).overflowX;
    const eintrag = {tag: e.tagName.toLowerCase(),
                     text: t.slice(0, 44),
                     scroll: e.scrollWidth, sicht: e.clientWidth,
                     overflowX: ox};
    if (ox === 'auto' || ox === 'scroll') gewollt.push(eintrag);
    else schlimm.push(eintrag);
  });
  return {schlimm: schlimm.slice(0, 20), gewollt: gewollt.slice(0, 20),
          wurzel: wurzel.className || wurzel.tagName};
}"""

# KOEDER zum Beschnittmelder: ein Feld, das garantiert abschneidet. Findet der
# Melder es nicht, misst er nichts.
KOEDER_EIN_JS = """() => {
  const wurzel = document.querySelector('.main-pad') || document.body;
  const d = document.createElement('div');
  d.id = '__koeder_beschnitt';
  d.style.cssText = 'width:80px;overflow:hidden;white-space:nowrap';
  d.textContent = 'K'.repeat(240);
  wurzel.appendChild(d);
  return d.scrollWidth > d.clientWidth + 1;
}"""

KOEDER_AUS_JS = """() => {
  const d = document.getElementById('__koeder_beschnitt');
  if (d && d.parentElement) d.parentElement.removeChild(d);
  return !d;
}"""

# SELBSTPROBE DER ZAEHLENDEN MELDER (Regel 3).
# CHIPS_JS und SELECTS_JS ZAEHLEN. Ein Zaehler, der beim eigenen Ausfall nichts
# findet, meldet "nichts gefunden" - und das sieht aus wie "alles in Ordnung".
# Deshalb wird am ENDE des Laufs je EIN Chip und je EINE Option aus dem DOM
# genommen; die Melder MUESSEN das bemerken. Danach wird nicht mehr gerendert,
# der Zustand wird verworfen.
KOEDER_CHIP_WEG_JS = """() => {
  const b = Array.from(document.querySelectorAll('button'))
    .filter(x => /\\(\\d+\\)\\s*$/.test((x.textContent || '').trim()));
  if (b.length < 2) return -1;
  b[b.length - 1].remove();
  return b.length;
}"""

KOEDER_OPTION_WEG_JS = """() => {
  const s = Array.from(document.querySelectorAll('select'))
    .find(x => Array.from(x.options).some(o => (o.textContent||'').trim() === 'Alle Status'));
  if (!s) return -1;
  const n = s.options.length;
  s.options[n - 1].remove();
  return n;
}"""


def _saeen(seite):
    """Saat einspielen und BELEGEN. Bricht ab, wenn sie nicht ankommt."""
    cfg = {"db": M.DB_NAME,
           "daten": {"monteure": MONTEURE, "werkzeuge": WERKZEUGE}}
    erg = seite.evaluate(M.SEED_JS, cfg)
    if erg.get("fehlend"):
        raise SystemExit("ABBRUCH: diese Speicher gibt es nicht: %s"
                         % ", ".join(erg["fehlend"]))
    gelesen = erg.get("gelesen", {})
    print("   zurueckgelesen: " + ", ".join(
        "%s=%s" % (k, v) for k, v in sorted(gelesen.items())))
    schlecht = [k for k, v in gelesen.items()
                if not isinstance(v, int) or v <= 0]
    if schlecht:
        raise SystemExit("ABBRUCH: die Saat ist nicht angekommen (%s)."
                         % ", ".join(schlecht))
    seite.reload(wait_until="domcontentloaded")
    seite.wait_for_timeout(6000)


def _enthaelt(texte, soll):
    """Welche Soll-Werte in KEINEM der Texte vorkommen."""
    return [s for s in soll if not any(s in t for t in texte)]


def _lauf(pw, url, breite, hoehe, bericht):
    """Ein Fenster durchmessen. Gibt (befunde, nicht_gemessen) zurueck."""
    befunde, offen = [], []
    marke = "%dx%d" % (breite, hoehe)
    ctx = pw.new_context(viewport={"width": breite, "height": hoehe},
                         is_mobile=breite < 600, has_touch=breite < 600)
    ctx.add_init_script(M.INIT)
    # OHNE DIESE ZEILE MISST DIE PROBE DEN AUSLEIH-KNOPF NICHT.
    # `_wzQuickBtn` gibt nur dann einen Knopf zurueck, wenn der Angemeldete
    # eine eigene Monteur-Id hat (`_myMid`). Der Sweep-Zugang aus INIT hat
    # keine - der erste Lauf meldete deshalb "0 Ausleih-Knoepfe" und haette das
    # als Ist-Zustand durchgehen lassen. Das war kein Befund an der App,
    # sondern ein nicht angeschalteter Zweig: dieselbe Fehlerform wie der
    # falsche Scheinstatus am 29.08.
    ctx.add_init_script(
        "try{var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
        "u.monteurId='M1';localStorage.setItem('epkolar_user',"
        "JSON.stringify(u));}catch(e){}")
    ctx.route("**/rest/v1/**", lambda r: r.abort())
    ctx.route("**/auth/v1/**", lambda r: r.abort())
    seite = ctx.new_page()
    fehler = []
    seite.on("pageerror", lambda e: fehler.append(str(e)[:170]))
    seite.goto(url, wait_until="domcontentloaded")
    seite.wait_for_timeout(3800)

    print("\n── %s ──────────────────────────────────────────" % marke)
    _saeen(seite)

    seite.evaluate(M.NAV_OEFFNEN_JS)
    seite.wait_for_timeout(350)
    weg = seite.evaluate(M.NAV_WAEHLEN_JS, "Werkzeuge")
    seite.wait_for_timeout(2200)
    print("   Navigation: %s" % weg)
    if weg == "nicht-gefunden":
        befunde.append("%s: die Ansicht Werkzeuge ist nicht erreichbar" % marke)
        ctx.close()
        return befunde, ["%s: alles (Ansicht nicht erreichbar)" % marke]

    # ── Reiter ────────────────────────────────────────────────────────────
    r = seite.evaluate(REITER_JS)
    if r.get("fehler"):
        befunde.append("%s: %s" % (marke, r["fehler"]))
        offen.append("%s: Reiter, Auswahlfelder, Chips" % marke)
        ctx.close()
        return befunde, offen

    print("   Reiter: %d  (quer rollbar: %s)" % (r["anzahl"], r["quer_rollbar"]))
    mit_text = 0
    for t in r["reiter"]:
        print("      %-26r  title=%-6r aria=%-6r  %dx%d px  nurIkone=%s"
              % (t["text"], t["title"], t["aria"], t["breite"], t["hoehe"],
                 t["nurIkone"]))
        if not t["nurIkone"]:
            mit_text += 1
        if t["hoehe"] < 44:
            befunde.append("%s: Reiter %r ist nur %d px hoch (Tippziel 44)"
                           % (marke, t["text"], t["hoehe"]))
    bericht["mit_text"][marke] = mit_text
    if r["anzahl"] != 5:
        befunde.append("%s: %d Reiter statt 5 - erwartet werden mit der "
                       "Admin-Rolle alle fuenf" % (marke, r["anzahl"]))
    fehlend = [i for i in REITER_SOLL
               if not any(i in t["text"] for t in r["reiter"])]
    if fehlend:
        befunde.append("%s: diese Reiter-Ikonen fehlen: %s"
                       % (marke, " ".join(fehlend)))

    # ── Chips ─────────────────────────────────────────────────────────────
    c = seite.evaluate(CHIPS_JS)
    print("   Filter-Chips: %d" % len(c))
    for x in c:
        print("      %-34r zahl=%-4s beschnitten=%s h=%d"
              % (x["text"], x["zahl"], x["beschnitt"], x["hoehe"]))
    if len(c) != 5:
        befunde.append("%s: %d Filter-Chips mit Zaehler statt 5"
                       % (marke, len(c)))
    fehlend = _enthaelt([x["text"] for x in c], CHIPS_SOLL)
    if fehlend:
        befunde.append("%s: diese Chips fehlen: %s" % (marke, ", ".join(fehlend)))
    if c and all((x["zahl"] or 0) == 0 for x in c):
        befunde.append("%s: ALLE Chip-Zaehler stehen auf 0 - dann ist die "
                       "Liste leer und diese Messung sagt nichts" % marke)
    bericht["chipsummen"][marke] = [(x["text"], x["zahl"]) for x in c]

    # ── Auswahlfelder im Listenfilter ─────────────────────────────────────
    s = seite.evaluate(SELECTS_JS)
    filt_st = [x for x in s if any("Alle Status" in o for o in x["optionen"])]
    filt_kat = [x for x in s
                if any("Alle Kategorien" in o for o in x["optionen"])]
    if not filt_st:
        befunde.append("%s: der Statusfilter der Liste ist nicht da" % marke)
        offen.append("%s: die sechs Statuswerte im Listenfilter" % marke)
    else:
        opt = filt_st[0]["optionen"]
        print("   Statusfilter: %d Optionen" % len(opt))
        for o in opt:
            print("      %r" % o)
        fehlend = _enthaelt(opt, STATUS_SOLL)
        if fehlend:
            befunde.append("%s: im Statusfilter fehlen: %s"
                           % (marke, ", ".join(fehlend)))
        if len(opt) != 7:
            befunde.append("%s: Statusfilter hat %d Optionen statt 7 "
                           "(Alle + 6)" % (marke, len(opt)))
    if not filt_kat:
        befunde.append("%s: der Kategoriefilter der Liste ist nicht da" % marke)
        offen.append("%s: die neun Kategorien im Listenfilter" % marke)
    else:
        opt = filt_kat[0]["optionen"]
        print("   Kategoriefilter: %d Optionen" % len(opt))
        fehlend = _enthaelt(opt, KAT_SOLL)
        if fehlend:
            befunde.append("%s: im Kategoriefilter fehlen: %s"
                           % (marke, ", ".join(fehlend)))
        if len(opt) != 10:
            befunde.append("%s: Kategoriefilter hat %d Optionen statt 10 "
                           "(Alle + 9)" % (marke, len(opt)))

    # ── "Ausleihen" je Geraet ─────────────────────────────────────────────
    # Gesaet sind ZWEI verfuegbare Geraete (W1, W2) - der Knopf steht je Geraet,
    # also muessen zwei da sein. Eine Zahl ohne diese Grundgesamtheit waere
    # nicht pruefbar: 0 sieht dann aus wie "richtig so".
    a = seite.evaluate(AUSLEIHEN_JS)
    verfuegbar = len([w for w in WERKZEUGE if w["status"] == "verfuegbar"])
    print("   Ausleih-Knoepfe: %d (erwartet %d, je verfuegbares Geraet) %s"
          % (a["anzahl"], verfuegbar, a["hoehen"]))
    bericht["ausleihen"][marke] = a["anzahl"]
    if a["anzahl"] != verfuegbar:
        befunde.append(
            "%s: %d Ausleih-Knoepfe fuer %d verfuegbare Geraete - der "
            "Schnellknopf je Geraet fehlt oder ist doppelt"
            % (marke, a["anzahl"], verfuegbar))

    # ── Beschnitt, mit Koeder ─────────────────────────────────────────────
    koeder_gefunden = seite.evaluate(KOEDER_EIN_JS)
    b_mit = seite.evaluate(BESCHNITT_JS)
    gefangen = any(x["text"].startswith("KKKK") for x in b_mit["schlimm"])
    seite.evaluate(KOEDER_AUS_JS)
    b = seite.evaluate(BESCHNITT_JS)
    print("   Beschnittmelder: Koeder im Aufbau=%s, vom Melder gefangen=%s"
          % (koeder_gefunden, gefangen))
    if not gefangen:
        befunde.append("%s: KOEDER GESCHEITERT - der Beschnittmelder hat ein "
                       "Feld mit 240 Zeichen in 80 px nicht gefunden. Seine "
                       "Auskunft 'kein Beschnitt' ist damit wertlos." % marke)
        offen.append("%s: Textbeschnitt" % marke)
    else:
        print("   Beschnitt (Wurzel %r): %d schlimm, %d gewollt querrollend"
              % (b["wurzel"], len(b["schlimm"]), len(b["gewollt"])))
        for x in b["schlimm"]:
            print("      ABGESCHNITTEN %-6s %4d>%4d  %r"
                  % (x["tag"], x["scroll"], x["sicht"], x["text"]))
        for x in b["gewollt"]:
            print("      querrollend   %-6s %4d>%4d  %r"
                  % (x["tag"], x["scroll"], x["sicht"], x["text"]))
        bericht["beschnitt"][marke] = b["schlimm"]

    # ── Das Formular: dort stehen Status und Kategorie zum SCHREIBEN ───────
    getippt = seite.evaluate(REITER_TIPPEN_JS, "✏")
    seite.wait_for_timeout(1400)
    if getippt != "geklickt":
        befunde.append("%s: der Stift-Reiter war nicht antippbar (%s)"
                       % (marke, getippt))
        offen.append("%s: Status/Kategorie im Formular" % marke)
    else:
        s2 = seite.evaluate(SELECTS_JS)
        f_st = [x for x in s2
                if len(x["optionen"]) == 6
                and not _enthaelt(x["optionen"], STATUS_SOLL)]
        f_kat = [x for x in s2
                 if len(x["optionen"]) == 9
                 and not _enthaelt(x["optionen"], KAT_SOLL)]
        print("   Formular: Statusfeld gefunden=%s, Kategoriefeld gefunden=%s"
              % (bool(f_st), bool(f_kat)))
        if not f_st:
            gr = sorted(len(x["optionen"]) for x in s2)
            befunde.append("%s: im Formular steht kein Feld mit genau den "
                           "sechs Statuswerten (gefundene Feldgroessen: %s)"
                           % (marke, gr))
        else:
            for o in f_st[0]["optionen"]:
                print("      Status  %r" % o)
        if not f_kat:
            befunde.append("%s: im Formular steht kein Feld mit genau den "
                           "neun Kategorien" % marke)
        else:
            for o in f_kat[0]["optionen"]:
                print("      Kat.    %r" % o)

    # ── Selbstprobe der zaehlenden Melder, GANZ ZULETZT ───────────────────
    # Erst zurueck auf die Liste (im Formular gibt es keine Chips), dann je ein
    # Stueck aus dem DOM nehmen. Danach wird nichts mehr gerendert.
    zurueck = seite.evaluate(REITER_TIPPEN_JS, "\U0001f4cb")
    seite.wait_for_timeout(1200)
    if zurueck != "geklickt":
        befunde.append("%s: der Klemmbrett-Reiter fuehrte nicht zurueck zur "
                       "Liste (%s)" % (marke, zurueck))
        offen.append("%s: Selbstprobe der zaehlenden Melder" % marke)
    else:
        vorher_chips = len(seite.evaluate(CHIPS_JS))
        weg = seite.evaluate(KOEDER_CHIP_WEG_JS)
        nachher_chips = len(seite.evaluate(CHIPS_JS))
        vorher_opt = seite.evaluate(KOEDER_OPTION_WEG_JS)
        s3 = seite.evaluate(SELECTS_JS)
        st = [x for x in s3 if any("Alle Status" in o for o in x["optionen"])]
        rest = _enthaelt(st[0]["optionen"], STATUS_SOLL) if st else ["(kein Feld)"]
        print("   Selbstprobe: Chips %d -> %d nach Entnahme (Melder sah %d); "
              "Statusoptionen %s -> fehlend %s"
              % (vorher_chips, nachher_chips, weg, vorher_opt, rest))
        if weg == -1 or nachher_chips >= vorher_chips:
            befunde.append(
                "%s: SELBSTPROBE GESCHEITERT - ein entfernter Filter-Chip "
                "wurde weiter mitgezaehlt (%d -> %d). Der Chip-Melder kann "
                "nicht rot werden." % (marke, vorher_chips, nachher_chips))
        if vorher_opt == -1 or not rest:
            befunde.append(
                "%s: SELBSTPROBE GESCHEITERT - eine entfernte Statusoption "
                "fiel dem Melder nicht auf. Sein 'alle sechs sind da' ist "
                "damit wertlos." % marke)

    echte = [f for f in fehler
             if not any(w.lower() in f.lower() for w in M.IGNORIEREN)]
    if echte:
        befunde.append("%s: Seitenfehler %s" % (marke, echte[:3]))
    ctx.close()
    return befunde, offen


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt - `pip install playwright` und "
              "`playwright install chromium`.")
        return 2

    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port,
                                      os.environ.get("EPK_INDEX", "index.html"))
    print("Gemessen wird:", url)

    bericht = {"mit_text": {}, "chipsummen": {}, "beschnitt": {},
               "ausleihen": {}}
    befunde, offen = [], []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for breite, hoehe in ((390, 860), (1440, 900)):
            b, o = _lauf(browser, url, breite, hoehe, bericht)
            befunde += b
            offen += o
        browser.close()

    print("\n" + "=" * 70)
    print("IST-ZUSTAND")
    print("=" * 70)
    for marke, n in sorted(bericht["mit_text"].items()):
        print("  %s: %d von 5 Reitern tragen Text" % (marke, n))
    for marke, chips in sorted(bericht["chipsummen"].items()):
        print("  %s: Chips %s" % (marke, chips))
    for marke, n in sorted(bericht["ausleihen"].items()):
        print("  %s: %d Ausleih-Knoepfe" % (marke, n))
    for marke, liste in sorted(bericht["beschnitt"].items()):
        print("  %s: %d abgeschnittene Stellen" % (marke, len(liste)))

    # KOEDER 3: ohne einen Fall mit Text sagt "am Telefon nur Ikonen" nichts.
    if bericht["mit_text"] and not any(n > 0 for n in bericht["mit_text"].values()):
        print("\nKOEDER GESCHEITERT: in KEINER Breite trug ein Reiter Text.")
        print("Dann kann die Probe nicht belegen, dass sie Text ueberhaupt")
        print("sehen wuerde - die Aussage 'am Telefon nur Ikonen' ist wertlos.")
        return 1

    if offen:
        print("\nNICHT GEMESSEN (Regel 4 - das sind KEINE bestandenen Faelle):")
        for z in offen:
            print("   " + z)

    if befunde:
        print("\nROT:")
        for z in befunde:
            print("   " + z)
        return 1
    if offen:
        print("\nTEILWEISE - was oben unter NICHT GEMESSEN steht, ist offen.")
        return 1
    print("\nGRUEN - fuenf Reiter in beiden Breiten, sechs Statuswerte und neun")
    print("Kategorien in Listenfilter UND Formular waehlbar, fuenf Chips mit")
    print("Zaehlern, ein Ausleih-Knopf je verfuegbarem Geraet - und alle drei")
    print("Melder haben ihren Koeder gefangen (Beschnitt, Chipzahl, Optionen).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
