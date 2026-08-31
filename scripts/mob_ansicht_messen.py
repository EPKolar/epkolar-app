# -*- coding: utf-8 -*-
"""Die MOBIL-Ansicht von Arbeitsschein-Liste und Zeiterfassung zusammenhaengend messen.

WARUM DIESES GERAET
-------------------
Die Arbeit der letzten Tage galt dem Rechner-Schirm. Die Mobil-Ansicht wurde
mehrfach als "nicht betroffen" abgehakt - meist zu Recht, aber nie
zusammenhaengend gemessen. Der einzige belastbare Mobilwert war:
390x900, erste Arbeitsschein-Karte bei y = 858 von 900.

Diese Datei misst dasselbe auf vier Geraetegroessen, dazu die Zeiterfassung,
die Tippziele, den Textbeschnitt und die Bedienelemente in der Mobil-Karte.

WAS "SICHTBAR" HEISST - UND WARUM DAS NICHT DIE FENSTERHOEHE IST
----------------------------------------------------------------
Am Telefon ist die Fensterhoehe NICHT die sichtbare Hoehe. Zwei Dinge gehen ab:

  1. die BROWSERLEISTE. Angesetzt werden drei Faelle, jeder benannt:
       * 0 px   - Vollbild / vom Startbildschirm gestartete PWA
       * 56 px  - Chrome auf Android, nur die obere Leiste
       * 100 px - Safari auf iOS, obere Leiste plus untere Tableiste (51+49)
     Gemessen wird JEDER Fall mit einem eigenen Fenster; es wird nichts
     nachgerechnet, was auch falsch nachgerechnet werden koennte.
  2. die eigene FUSSLEISTE der App (.bottom-nav, position:fixed, bottom:0).
     Sie liegt UEBER dem Inhalt. #root traegt zwar padding-bottom:70px, das
     verhindert nur, dass der Inhalt unter ihr endet - es gibt die Bildflaeche
     nicht zurueck. Ihre Hoehe wird GEMESSEN, nicht gesetzt.

Nutzbare Hoehe = Fensterhoehe - Fussleiste.

GEGENPROBEN, DIE HIER FEST EINGEBAUT SIND
-----------------------------------------
In dieser Woche gab es sechs Fehlalarme aus eigenen Werkzeugen, jeder eine
saubere Zahl, die nichts mass. Deshalb misst dieses Geraet nichts, ohne sich
vorher selbst zu widerlegen:

  * BESCHNITT: ein bekannt kurzer Text wird auf 240 Zeichen verlaengert; der
    Melder MUSS anschlagen und danach, zurueckgesetzt, wieder schweigen.
  * TIPPZIELE: die Schnellfilter-Chips tragen laut Quelltext minHeight 36 und
    die Kartenknoepfe ebenfalls 36. Misst das Geraet dort nichts >= 36,
    misst es nicht die Knoepfe.
  * SAAT: uebernommen aus tab_sweep - zuruecklesen UND in der Ansicht suchen.
  * BEZUGSWERT: 390x900 muss die 858 aus v3.9.924 wieder treffen.

BENUTZUNG
---------
    python scripts/mob_ansicht_messen.py
    python scripts/mob_ansicht_messen.py --nur 390x900
    python scripts/mob_ansicht_messen.py --rolle monteur
    python scripts/mob_ansicht_messen.py --nachher
"""
import os
import sys
import json
import threading

for _strom in (sys.stdout, sys.stderr):
    try:
        _strom.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)

from tab_sweep import INIT, IGNORIEREN, DB_NAME, SEED_JS  # noqa: E402

ZIEL = os.path.join(WURZEL, "screenshots")

# Breite x Fensterhoehe (Geraetehoehe in CSS-px).
GERAETE = [
    (360, 740, "Android verbreitet (Galaxy A/M, Redmi)"),
    (390, 844, "iPhone 12/13/14/15"),
    (390, 900, "Bezugsgroesse aus v3.9.924"),
    (414, 896, "iPhone 11 / XR / Plus-Klasse"),
]

LEISTEN = [
    (0, "ohne Leiste (Vollbild / PWA vom Startbildschirm)"),
    (56, "Chrome Android, obere Leiste"),
    (100, "Safari iOS, obere Leiste + untere Tableiste"),
]

# ── Der Vorschlag, im Browser eingespielt (index.html wird NICHT angefasst) ─
# Bauart wie .epk-ruhig (v918), .epk-flach (v920), .epk-leiste (v924):
# EINE Klasse, die nur Geometrie umschaltet, kein Verhalten. Alle elf Kacheln
# bleiben, alle Zahlen bleiben, alle Klicks bleiben - sie stehen am Telefon
# nur in EINER quer rollbaren Zeile statt in vier untereinander.
#
# Das Quer-Rollen ist hier kein neuer Einfall: die Schnellfilter-Leiste direkt
# darunter macht seit v3.5.74 genau das (overflowX:auto, WebkitOverflowScrolling
# touch). Der Vorschlag uebernimmt das Hausmuster, er erfindet keins.
#
# Ueber 600 px passiert NICHTS - die .epk-leiste-Geometrie vom Rechner bleibt
# unberuehrt.
#
# DIE DRITTE ZEILE IST DIE WICHTIGSTE, UND SIE FEHLTE IM ERSTEN ENTWURF:
# content-visibility. Die App traegt fuer JEDES div[role=button][aria-label]
# in .main-pad die Regel content-visibility:auto mit contain-intrinsic-size
# auto 148px (:6203) - gedacht fuer die lange Arbeitsschein-Kartenliste. Die
# elf Kacheln sind aber ebenfalls div[role=button][aria-label] und fallen
# darunter. Sobald sie quer nebeneinander stehen, sind die hinteren
# ausserhalb des Bildes, werden nie gerendert und melden ihre Platzhalter-
# hoehe 148 px; ueber align-items:stretch zieht das ALLE Kacheln auf 162 px
# und der Block ist 166 statt 64 px hoch.
#
# GEFUNDEN NUR, WEIL NACHGEMESSEN WURDE. Die eingespielte Fassung hatte 64 px
# gemeldet - dort waren die Kacheln vorher als Raster GERENDERT worden und
# behielten ihre echten Masse. Diesen Zustand gibt es beim Laden der Seite
# nie. Das war ein Fehlalarm der guten Sorte: eine saubere Zahl aus einem
# Aufbau, den es in Wirklichkeit nicht gibt.
NACHHER_CSS = """
@media(max-width:600px){
  .kpi-grid.epk-kachelband { display: flex !important; flex-wrap: nowrap !important;
    overflow-x: auto !important; -webkit-overflow-scrolling: touch;
    scroll-snap-type: x proximity; gap: 6px !important; padding-bottom: 4px; }
  .kpi-grid.epk-kachelband > div { flex: 0 0 auto !important;
    min-width: 118px !important; margin-bottom: 0 !important;
    content-visibility: visible !important; scroll-snap-align: start; }
}
"""

EINSPIELEN_JS = """(css) => {
  const s = document.createElement('style');
  s.id = '__nachher'; s.textContent = css; document.head.appendChild(s);
  const g = document.querySelector('.kpi-grid');
  if (g) g.classList.add('epk-kachelband');
  return !!g;
}"""

# GEGENPROBE ZUM VORSCHLAG - die Lehre aus v3.9.115 steht im Quelltext:
# die Kachel traegt overflow:hidden und der Wert whiteSpace:nowrap. Wird sie
# zu schmal, werden ZIFFERN abgeschnitten, lautlos. Die Saat liefert einstellige
# Zahlen; damit waere JEDE Breite gruen. Deshalb werden vor der Messung alle
# Kachelwerte auf 12.345 gesetzt - die groesste Zahl, die in diesem Haus
# realistisch in einer AS-Kachel stehen kann. Nur im Browser, nichts wird
# gespeichert.
STRESS_JS = """() => {
  const g = document.querySelector('.kpi-grid');
  if (!g) return 0;
  let n = 0;
  for (const k of g.children) {
    const v = [...k.children].filter(
      c => getComputedStyle(c).position !== 'absolute')[1];
    if (v) { v.textContent = '12.345'; n++; }
  }
  return n;
}"""

KACHEL_JS = """() => {
  const g = document.querySelector('.kpi-grid');
  if (!g) return {fehler: 'kein kpi-grid'};
  const r = g.getBoundingClientRect();
  const kacheln = [...g.children].map(k => {
    const kr = k.getBoundingClientRect();
    const innen = [...k.children].filter(
      c => getComputedStyle(c).position !== 'absolute');
    const beschnitt = innen.filter(c => c.scrollWidth > c.clientWidth + 1)
      .map(c => (c.textContent||'').trim().slice(0, 20));
    return {b: Math.round(kr.width), h: Math.round(kr.height),
      klickbar: k.getAttribute('role') === 'button',
      tastatur: k.getAttribute('tabindex') === '0',
      text: (k.textContent||'').replace(/\\s+/g,' ').trim().slice(0, 26),
      beschnitt: beschnitt};
  });
  return {y: Math.round(r.top + window.scrollY), hoehe: Math.round(r.height),
          anzahl: kacheln.length, kacheln: kacheln,
          quer_rollbar: g.scrollWidth > g.clientWidth + 1};
}"""


# ── Die Saat: echte oesterreichische Faelle, keine "Test A" ────────────────
# Eine Messung, die nur leichte Faelle kennt, ist gruen und nutzlos. Die
# Namen, Orte und Arbeitsanweisungen unten sind so lang, wie sie in diesem
# Haus wirklich vorkommen - Wohnungseigentuemergemeinschaften, Marktgemeinden,
# Landeskliniken, Doppelnamen mit Titel, mehrzeilige Anweisungen.
MONTEURE = [
    {"id": "M1", "n": "Gerhard Steinbichler", "r": "Monteur", "austritt": ""},
    {"id": "M2", "n": "Johannes Hinterleitner", "r": "Obermonteur", "austritt": ""},
    {"id": "M3", "n": "Manuel Payrleithner", "r": "Techniker", "austritt": ""},
]

KUNDEN = [
    ("Wohnungseigentuemergemeinschaft Krems-Stein, Steiner Landstrasse 42-46",
     "K-2019-0447", "Krems an der Donau", "3500"),
    ("Marktgemeinde Sankt Leonhard am Hornerwald - Bauhof",
     "K-2021-1132", "Sankt Leonhard am Hornerwald", "3572"),
    ("Landesklinikum Zwettl, Technische Abteilung Haustechnik",
     "K-2017-0088", "Zwettl-Niederoesterreich", "3910"),
    ("Elektro Ing. Hubert Grabner GmbH & Co KG",
     "K-2020-0913", "Langenlois", "3550"),
    ("Familie Mag. Elisabeth Schoeberl-Hinterberger",
     "K-2023-2201", "Gfoehl", "3542"),
    ("Raiffeisenbank Region Waldviertel Mitte eGen, Zweigstelle Rastenfeld",
     "K-2018-0555", "Rastenfeld", "3532"),
]

ARBEITEN = [
    "Stoerung Heizungsverteiler UV3: FI loest sporadisch aus, vor allem bei "
    "Regen.\nVor Ort Isolationswiderstand aller Abgaenge messen und "
    "protokollieren, Messprotokoll ans Buero.\nErsatzteile mitnehmen: "
    "FI-Schalter 4-polig 40A/0,03A Typ A, zwei Stueck Reserve.",
    "Jaehrliche Ueberpruefung der Sicherheitsbeleuchtung nach OVE E 8101 "
    "inklusive Funktionsdauerpruefung.\nAlle 34 Leuchten einzeln pruefen, "
    "Pruefbuch fuehren, defekte Akkus tauschen.",
    "Neuinstallation Zaehlerverteiler im Stiegenhaus West.\nAchtung: "
    "Abschaltung mit der Hausverwaltung akkordiert, Fenster 07:00 bis 11:30, "
    "danach muss der Strom wieder stehen.\nNetzbetreiber-Anmeldung liegt "
    "beim Sachbearbeiter.",
    "Kurzeinsatz: Steckdose Kueche ohne Spannung.",
    "Inbetriebnahme Waermepumpe Luft/Wasser inklusive Anbindung an die "
    "Gebaeudeleittechnik.\nParametrierung nach Datenblatt, Uebergabe an den "
    "Kunden mit Einschulung, Protokoll unterschreiben lassen.",
    "Behebung der Maengel aus der Abnahme vom 12.08.: Position 3, 7 und 11 "
    "der Maengelliste.\nSchaltschrankbeschriftung ergaenzen, "
    "Potentialausgleich Heizungsraum nachziehen, Not-Aus pruefen.",
]

PROJEKTE = [
    {"id": "P1", "nr": "2024-0117",
     "name": "Wohnhausanlage Steiner Landstrasse - Elektro Neubau Bauteil B",
     "kunde": "WEG Krems-Stein", "status": "aktiv"},
    {"id": "P2", "nr": "2025-0043",
     "name": "Landesklinikum Zwettl - Sanierung Sicherheitsbeleuchtung OG2",
     "kunde": "LK Zwettl", "status": "aktiv"},
]

# MUSS in AS_GRP_OFFEN stehen, sonst siehe die Lehre in tab_sweep.
SEED_STATUS = ["freigegeben", "in_bearbeitung", "aufgenommen",
               "freigegeben", "aufgeschoben", "in_bearbeitung"]
SEED_PRIO = ["hoch", "normal", "keine", "dringend", "normal", "hoch"]
SEED_ART = ["stoerung", "wartung", "montage", "stoerung", "montage", "kein"]


def _woche_iso():
    """Montag bis Sonntag der LAUFENDEN Woche.

    Die Zeiterfassung zeigt immer die aktuelle Kalenderwoche. Ein Eintrag
    ausserhalb waere unsichtbar - derselbe Fehler wie das falsche Statuswort
    vom 29.08.: die Saat kommt an, schaltet aber den fraglichen Zweig nicht an.
    """
    import datetime
    heute = datetime.date.today()
    montag = heute - datetime.timedelta(days=heute.weekday())
    return [(montag + datetime.timedelta(days=k)).isoformat() for k in range(7)]


def _daten():
    tage = _woche_iso()
    scheine = []
    for k in range(6):
        kd = KUNDEN[k]
        scheine.append({
            "id": "S%d" % (k + 1), "nummer": "AS-%d" % (2401 + k),
            "kundName": kd[0], "kundNr": kd[1],
            "arbeitsort": kd[2], "plz": kd[3],
            "arbeitsanweisungen": ARBEITEN[k],
            "monteur": MONTEURE[k % 3]["id"],
            "aufgenommen": tage[0],
            "terminBestaetigt": tage[min(k, 4)],
            "terminVorschlag": "",
            "terminZeit": "07:30",
            "scheinstatus": SEED_STATUS[k],
            "prioritaet": SEED_PRIO[k],
            "scheinart": SEED_ART[k],
            "sachbearbeiter": "Bernadette Wieshofer-Prandtner",
            "projektnr": PROJEKTE[k % 2]["nr"],
            "dauer": "4h",
        })
    eintraege = []
    for k in range(5):
        eintraege.append({
            "id": "E%d" % (k + 1), "worker": "M1", "datum": tage[k],
            "project_id": PROJEKTE[k % 2]["id"] if k % 3 else "",
            "arbeitsschein_id": "" if k % 3 else "S1",
            "taetigkeit": ARBEITEN[k].split("\n")[0][:120],
            "hours": 8 if k < 4 else 6.5,
            "von": "07:00", "bis": "16:00", "pause": 1,
            "gewerk": "elektro",
            "bemerkung": "Anfahrt Krems - Zwettl gemeinsam mit "
                         + MONTEURE[1]["n"],
        })
    return scheine, eintraege


def saeen_schwer(seite):
    """Saat einspielen und BELEGEN. Bricht ab, wenn sie nicht ankommt."""
    scheine, eintraege = _daten()
    cfg = {"db": DB_NAME, "daten": {
        "monteure": MONTEURE, "arbeitsscheine": scheine,
        "projects": PROJEKTE, "entries": eintraege}}
    erg = seite.evaluate(SEED_JS, cfg)
    gelesen = erg.get("gelesen", {})
    if erg.get("fehlend"):
        print("   WARNUNG, diese Speicher gibt es nicht: %s"
              % ", ".join(erg["fehlend"]))
    print("   zurueckgelesen: " + ", ".join(
        "%s=%s" % (k, v) for k, v in sorted(gelesen.items())))
    schlecht = [k for k, v in gelesen.items()
                if not isinstance(v, int) or v <= 0]
    if schlecht:
        raise SystemExit(
            "ABBRUCH: die Saat ist nicht angekommen (%s)." % ", ".join(schlecht))

    seite.reload(wait_until="domcontentloaded")
    seite.wait_for_timeout(6000)

    treffer = seite.evaluate(
        '() => (document.body.innerText.match('
        '/Steinbichler|Hinterleitner|Steiner Landstra/g)||[]).length')
    print("   in der Ansicht sichtbar: %d Treffer" % treffer)
    if not treffer:
        raise SystemExit(
            "ABBRUCH: die Saat liegt in der Datenbank, erscheint aber in "
            "KEINER Ansicht. Ein Lauf, der das uebergeht, misst leere "
            "Renderpfade und waere gruen und wertlos.")
    return scheine, eintraege


# ── Navigation ────────────────────────────────────────────────────────────
# Am Telefon scrollt die obere Reiterleiste quer und schneidet die hinteren
# Reiter ab (v3.9.118). Der zuverlaessige Weg ist das Mehr-Menue der
# Fussleiste: dort stehen am Telefon ALLE Reiter (moreTabs=tabs).
NAV_OEFFNEN_JS = """() => {
  const nav = document.querySelector('.bottom-nav');
  if (!nav) return 'keine-fussleiste';
  const mehr = [...nav.querySelectorAll('button')]
    .find(b => (b.getAttribute('aria-label')||'') === 'Mehr');
  if (!mehr) return 'kein-mehr-knopf';
  mehr.click();
  return 'mehr-geoeffnet';
}"""

NAV_WAEHLEN_JS = """(label) => {
  const k = [...document.querySelectorAll('button[aria-label]')]
    .filter(b => b.getAttribute('aria-label') === label);
  if (!k.length) return 'nicht-gefunden';
  k[k.length - 1].click();   // das Mehr-Menue steht spaeter im DOM
  return 'geklickt/' + k.length;
}"""


GRUND_JS = """() => {
  const nav = document.querySelector('.bottom-nav');
  const nr = nav ? nav.getBoundingClientRect() : null;
  const cs = nav ? getComputedStyle(nav) : null;
  return {
    breite: window.innerWidth, hoehe: window.innerHeight,
    fussleiste: (nr && cs && cs.display !== 'none') ? Math.round(nr.height) : 0,
    fuss_lage: cs ? cs.position : '-',
    dokument: Math.round(document.scrollingElement.scrollHeight),
    version: (typeof APP_VERSION !== 'undefined') ? APP_VERSION : '?'
  };
}"""

# Die erste Arbeitsschein-Karte. Zwei unabhaengige Merkmale (Klasse UND
# aria-label mit der Scheinnummer), damit ein umbenanntes Merkmal nicht
# stumm zu "keine" fuehrt.
AS_JS = r"""() => {
  const y = e => Math.round(e.getBoundingClientRect().top + window.scrollY);
  const h = e => Math.round(e.getBoundingClientRect().height);
  const karten = [...document.querySelectorAll('.epk-card-hover')]
    .filter(d => /AS-\d{4}/.test(d.getAttribute('aria-label')||''));
  const ueber = [...document.querySelectorAll('[role=button]')]
    .filter(d => /AS-\d{4}/.test(d.getAttribute('aria-label')||''));
  if (!karten.length) return {gefunden: 0, ueber_rolle: ueber.length};
  const k0 = karten[0];
  // Der Vorbau wird von der SEITENWURZEL aus aufgenommen, nicht erst ab dem
  // Listen-Kasten. Der erste Anlauf lief nur ueber die Geschwister der Karte
  // und meldete vier Bloecke ueber 240 px - bei y = 858. Die fehlenden
  // 600 px standen darueber und waren in der Ausgabe unsichtbar.
  const bloecke = [];
  const sammeln = (el, tiefe) => {
    for (const c of el.children) {
      const r = c.getBoundingClientRect();
      if (r.height < 1) continue;
      const cs = getComputedStyle(c);
      if (cs.position === 'fixed') continue;
      if (c.contains(k0) && c !== k0) { sammeln(c, tiefe + 1); continue; }
      if (y(c) >= y(k0)) continue;
      bloecke.push({t: tiefe, y: y(c), hoehe: Math.round(r.height),
        was: String(c.className || c.tagName.toLowerCase()).slice(0, 18),
        text: (c.textContent||'').replace(/\s+/g,' ').trim().slice(0, 58)});
    }
  };
  sammeln(document.getElementById('root') || document.body, 0);
  bloecke.sort((a, b) => a.y - b.y);
  return {
    gefunden: karten.length, ueber_rolle: ueber.length,
    y: y(k0), hoehe: h(k0),
    y_zweite: karten[1] ? y(karten[1]) : null,
    bloecke: bloecke,
    in_karte: {
      select: k0.querySelectorAll('select').length,
      input: k0.querySelectorAll('input').length,
      button: k0.querySelectorAll('button').length,
      rolle_button: k0.querySelectorAll('[role=button]').length
    }
  };
}"""

# Der erste Zeiteintrag. Anker ist der Knopf "+ Eintrag" - er steht in jeder
# Tageskarte genau einmal, auch in einer LEEREN. Ein Anker, der nur bei
# vorhandenen Eintraegen existiert, haette bei leerer Woche "nichts da"
# gemeldet statt "leer" - und das ist ein anderer Befund.
ZEIT_JS = r"""() => {
  const y = e => Math.round(e.getBoundingClientRect().top + window.scrollY);
  const h = e => Math.round(e.getBoundingClientRect().height);
  const t = e => (e.textContent||'').replace(/\s+/g,' ').trim();
  const knoepfe = [...document.querySelectorAll('button')]
    .filter(b => t(b) === '+ Eintrag');
  if (!knoepfe.length) return {tageskarten: 0};
  const liste = knoepfe[0].parentElement;
  const karte = liste.parentElement;
  const eintraege = [...liste.children].filter(c => c !== knoepfe[0]);
  const e0 = eintraege[0] || null;
  const bloecke = [];
  const sammeln = (el, tiefe) => {
    for (const c of el.children) {
      const r = c.getBoundingClientRect();
      if (r.height < 1) continue;
      if (getComputedStyle(c).position === 'fixed') continue;
      if (c.contains(karte) && c !== karte) { sammeln(c, tiefe + 1); continue; }
      if (y(c) >= y(karte)) continue;
      bloecke.push({t: tiefe, y: y(c), hoehe: Math.round(r.height),
        was: String(c.className || c.tagName.toLowerCase()).slice(0, 18),
        text: t(c).slice(0, 58)});
    }
  };
  sammeln(document.getElementById('root') || document.body, 0);
  bloecke.sort((a, b) => a.y - b.y);
  return {
    tageskarten: knoepfe.length,
    y_karte: y(karte), hoehe_karte: h(karte),
    kopf: t(karte.firstElementChild || karte).slice(0, 40),
    eintraege_tag1: eintraege.length,
    y_eintrag: e0 ? y(e0) : null, hoehe_eintrag: e0 ? h(e0) : null,
    y_addknopf: y(knoepfe[0]), hoehe_addknopf: h(knoepfe[0]),
    bloecke: bloecke
  };
}"""

# ── Tippziele ─────────────────────────────────────────────────────────────
# WCAG 2.2 SC 2.5.8 (AA) verlangt 24x24 CSS-px, SC 2.5.5 (AAA) und die
# Apple-Vorgabe 44x44. Beides wird ausgewiesen.
TIPP_JS = r"""(wurzelWahl) => {
  const wurzel = wurzelWahl ? document.querySelector(wurzelWahl) : document.body;
  if (!wurzel) return {fehler: 'Wurzel nicht gefunden'};
  const wahl = 'button, [role=button], select, input, textarea, a[href], summary';
  const out = [];
  for (const e of wurzel.querySelectorAll(wahl)) {
    const r = e.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    const cs = getComputedStyle(e);
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    if (cs.pointerEvents === 'none') continue;
    const name = (e.getAttribute('aria-label') || e.getAttribute('title')
      || (e.value||'') || (e.textContent||'')).replace(/\s+/g,' ').trim();
    const tag = e.tagName.toLowerCase();
    out.push({tag: tag,
      rolle: e.getAttribute('role') || '',
      // Von den 44er-Regeln des Stylesheets gedeckt sind ECHTE Knoepfe und
      // Felder (:261 button, :265 input/select/textarea). Ein
      // <span role=button> faellt NICHT darunter - fuer den gilt eine eigene
      // Regel (:218). Beide getrennt auszuweisen ist der Unterschied
      // zwischen "gemessen" und "auf eine Null gehofft".
      gedeckt: ['button','input','select','textarea','a'].indexOf(tag) >= 0,
      name: name.slice(0, 34) || '(ohne Beschriftung)',
      b: Math.round(r.width), h: Math.round(r.height),
      klein: Math.round(Math.min(r.width, r.height))});
  }
  return {ziele: out};
}"""

# ── Beschnitt ─────────────────────────────────────────────────────────────
# Zwei Sorten, die auseinandergehalten werden muessen:
#   LAUTLOS  - overflow hidden/clip, kein Ellipsis, keine Zeilenklammer.
#              Der Text hoert einfach auf. Niemand sieht es.
#   ELLIPSIS - text-overflow ellipsis ODER -webkit-line-clamp. Gekappt, aber
#              die drei Punkte sagen es.
# overflow auto/scroll wird NICHT gemeldet: rollbar heisst erreichbar.
#
# ACHTUNG, EIGENER FEHLALARM AUS DEM ERSTEN ANLAUF DIESES GERAETS:
# Der Vergleich scrollHeight > clientHeight FINDET EINE ZEILENKLAMMER NICHT.
# Bei display:-webkit-box mit -webkit-line-clamp meldet Chromium beide Werte
# gleich gross; der erste Durchgang gab deshalb "0 Beschnitt" aus, waehrend
# die Karte sichtbar zweizeilig kappte. Eine saubere Null, die nichts mass -
# genau die Krankheit dieser Woche. Deshalb misst KLAMMER_JS unten zusaetzlich
# gegen einen unbeschnittenen Zwilling.
BESCHNITT_JS = r"""(wurzelWahl) => {
  const wurzel = wurzelWahl ? document.querySelector(wurzelWahl) : document.body;
  if (!wurzel) return {fehler: 'Wurzel nicht gefunden'};
  const out = [];
  for (const e of [wurzel, ...wurzel.querySelectorAll('*')]) {
    const cs = getComputedStyle(e);
    const r = e.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    const klemmtX = (cs.overflowX === 'hidden' || cs.overflowX === 'clip');
    const klemmtY = (cs.overflowY === 'hidden' || cs.overflowY === 'clip');
    const zuBreit = e.scrollWidth > e.clientWidth + 1;
    const zuHoch = e.scrollHeight > e.clientHeight + 1;
    if (!((klemmtX && zuBreit) || (klemmtY && zuHoch))) continue;
    const voll = (e.textContent||'').replace(/\s+/g,' ').trim();
    if (!voll) continue;
    const eigen = [...e.childNodes]
      .filter(n => n.nodeType === 3 && (n.textContent||'').trim().length).length;
    const klammer = cs.webkitLineClamp && cs.webkitLineClamp !== 'none';
    const punkte = cs.textOverflow === 'ellipsis';
    out.push({
      tag: e.tagName.toLowerCase(),
      art: (klammer || punkte) ? 'ELLIPSIS' : 'LAUTLOS',
      eigen: eigen,
      klammer: klammer ? String(cs.webkitLineClamp) : '',
      breit: zuBreit ? (e.scrollWidth - e.clientWidth) : 0,
      hoch: zuHoch ? (e.scrollHeight - e.clientHeight) : 0,
      text: voll.slice(0, 90)
    });
  }
  return {funde: out};
}"""

# ── Zeilenklammer, gegen einen unbeschnittenen Zwilling gemessen ──────────
# Fuer jedes Element mit -webkit-line-clamp oder mit nowrap+ellipsis wird ein
# unsichtbarer Zwilling gleicher Breite und Schrift OHNE Klammer gebaut. Ist
# der hoeher (bzw. breiter), fehlt Text auf dem Schirm - und zwar so viel.
# Die Gegenprobe steckt im selben Ergebnis: ein Element, das PASST, muss
# fehlend = 0 liefern. Kaeme dort auch etwas heraus, misst der Zwilling falsch.
KLAMMER_JS = r"""(wurzelWahl) => {
  const wurzel = wurzelWahl ? document.querySelector(wurzelWahl) : document.body;
  if (!wurzel) return {fehler: 'Wurzel nicht gefunden'};
  const buehne = document.createElement('div');
  buehne.style.cssText = 'position:absolute;left:-99999px;top:0;visibility:hidden';
  document.body.appendChild(buehne);
  const out = [];
  for (const e of wurzel.querySelectorAll('*')) {
    const cs = getComputedStyle(e);
    const geklammert = cs.webkitLineClamp && cs.webkitLineClamp !== 'none';
    const einzeilig = (cs.whiteSpace === 'nowrap'
      && (cs.overflowX === 'hidden' || cs.overflowX === 'clip'));
    if (!geklammert && !einzeilig) continue;
    const voll = (e.textContent||'').replace(/\s+/g,' ').trim();
    if (!voll) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    const z = document.createElement('div');
    z.style.cssText = 'width:' + e.clientWidth + 'px;'
      + 'font:' + cs.font + ';letter-spacing:' + cs.letterSpacing + ';'
      + 'line-height:' + cs.lineHeight + ';white-space:normal;word-break:'
      + cs.wordBreak + ';';
    z.textContent = voll;
    buehne.appendChild(z);
    const vollHoehe = z.scrollHeight;
    const vollBreite = z.scrollWidth;
    buehne.removeChild(z);
    const fehltHoehe = Math.max(0, vollHoehe - e.clientHeight);
    const zeilenH = parseFloat(cs.lineHeight) || parseFloat(cs.fontSize) * 1.2 || 14;
    out.push({
      tag: e.tagName.toLowerCase(),
      art: geklammert ? ('klammer-' + cs.webkitLineClamp) : 'einzeilig',
      breite: Math.round(r.width),
      gezeigt: e.clientHeight, gebraucht: vollHoehe,
      fehlt_px: fehltHoehe,
      fehlt_zeilen: Math.round(fehltHoehe / zeilenH * 10) / 10,
      fehlt_breit: einzeilig ? Math.max(0, vollBreite - e.clientWidth) : 0,
      text: voll.slice(0, 100)
    });
  }
  document.body.removeChild(buehne);
  return {funde: out};
}"""

# ── Ueberbreite: was ragt seitlich aus dem Schirm? ────────────────────────
# Bei max-width 600 traegt das Stylesheet `html, body { overflow-x: hidden }`
# (:254, v3.9.816, gegen Quer-Rollen der ganzen Seite). Das verhindert das
# Rollen - es verhindert NICHT, dass etwas zu breit ist. Was rechts hinausragt,
# ist damit weg, ohne Hinweis und ohne Weg dorthin. Genau die Sorte lautloser
# Verlust, um die es hier geht, nur in der anderen Achse.
#
# Elemente in einem eigenen Quer-Roller (overflow-x auto/scroll) werden NICHT
# gemeldet: die sind erreichbar. Ohne diese Ausnahme haette das Geraet die
# Schnellfilter-Leiste und jede Tabelle als Fund gemeldet - lauter saubere
# Zahlen ueber nichts.
UEBERBREIT_JS = r"""() => {
  const W = window.innerWidth;
  const inRoller = (e) => {
    for (let p = e.parentElement; p; p = p.parentElement) {
      const c = getComputedStyle(p);
      if (c.overflowX === 'auto' || c.overflowX === 'scroll') return true;
      if (p === document.body) break;
    }
    return false;
  };
  const out = [];
  for (const e of document.body.querySelectorAll('*')) {
    const r = e.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    const cs = getComputedStyle(e);
    if (cs.position === 'fixed') continue;
    const raus = Math.round(Math.max(0, r.right - W) + Math.max(0, -r.left));
    if (raus < 2) continue;
    if (inRoller(e)) continue;
    // Nur das aeusserste ueberbreite Element je Zweig melden.
    if (e.parentElement) {
      const pr = e.parentElement.getBoundingClientRect();
      if (pr.right > W + 1 || pr.left < -1) continue;
    }
    out.push({tag: e.tagName.toLowerCase(),
      links: Math.round(r.left), rechts: Math.round(r.right),
      breite: Math.round(r.width), raus: raus,
      text: (e.textContent||'').replace(/\s+/g,' ').trim().slice(0, 60)});
  }
  return {schirm: W, dokument: Math.round(document.body.scrollWidth), funde: out};
}"""

# ── Liegen die Zwischenspeicher-Zeiten wirklich da, waehrend die Woche leer
#    aussieht? ────────────────────────────────────────────────────────────
# Ohne diese Frage waere "die Woche ist leer" nur "keine Daten". Erst der
# Nachweis, dass die Eintraege IM GERAET liegen und trotzdem nicht erscheinen,
# macht daraus einen Befund.
ODB_ZEITEN_JS = r"""(cfg) => new Promise((res) => {
  const r = indexedDB.open(cfg.db);
  r.onerror = () => res({fehler: 'DB nicht zu oeffnen'});
  r.onsuccess = () => {
    const db = r.result;
    if (!Array.from(db.objectStoreNames).includes('entries'))
      return res({fehler: 'kein entries-Speicher'});
    const tx = db.transaction('entries', 'readonly');
    const rq = tx.objectStore('entries').get('data');
    rq.onerror = () => res({fehler: 'Lesefehler'});
    rq.onsuccess = () => {
      const alle = Array.isArray(rq.result) ? rq.result : [];
      const passend = alle.filter(e =>
        (e.worker || e.w || e.worker_id) === cfg.worker
        && cfg.tage.indexOf(String(e.datum || e.date || '').slice(0, 10)) >= 0);
      res({gesamt: alle.length, in_der_woche: passend.length});
    };
  };
})"""

# ── Was steht in der Karte, was steht in der Zeile? ───────────────────────
# Die Frage aus dem Auftrag: gibt es Inhalte oder Bedienungen, die es am
# Rechner gibt und am Telefon nicht? Beantwortet wird sie nicht durch Lesen
# des Quelltextes, sondern durch Abgleich des gesaeten Textes mit dem, was im
# DOM der Karte bzw. der Tabellenzeile wirklich steht.
ABGLEICH_JS = r"""(saat) => {
  const norm = s => String(s||'').replace(/\s+/g,' ').trim();
  const karte = (nummer) => {
    let e = [...document.querySelectorAll('.epk-card-hover')]
      .find(d => (d.getAttribute('aria-label')||'').indexOf(nummer) === 0);
    if (e) return {art: 'karte', el: e};
    const tr = [...document.querySelectorAll('tbody tr')]
      .find(t => norm(t.textContent).indexOf(nummer) >= 0);
    return tr ? {art: 'zeile', el: tr} : null;
  };
  const out = [];
  for (const s of saat) {
    const t = karte(s.nummer);
    if (!t) { out.push({nummer: s.nummer, gefunden: false}); continue; }
    const txt = norm(t.el.innerText || t.el.textContent);
    const feld = (wert) => {
      const w = norm(wert);
      if (!w) return 'leer';
      if (txt.indexOf(w) >= 0) return 'ganz';
      // teilweise: der Anfang steht da, der Rest nicht
      for (let n = w.length; n > 8; n -= 4)
        if (txt.indexOf(w.slice(0, n)) >= 0)
          return 'nur ' + n + '/' + w.length + ' Zeichen';
      return 'FEHLT';
    };
    const anw = norm(s.arbeitsanweisungen);
    const erste = norm(String(s.arbeitsanweisungen||'').split('\n')[0]);
    out.push({
      nummer: s.nummer, gefunden: true, art: t.art,
      kunde: feld(s.kundName),
      kundNr: feld(s.kundNr),
      arbeitsort: feld(s.arbeitsort),
      sachbearbeiter: feld(s.sachbearbeiter),
      projektnr: feld(s.projektnr),
      anweisung_ganz: feld(s.arbeitsanweisungen),
      anweisung_erste_zeile: feld(erste),
      anweisung_zeichen: anw.length,
      anweisung_zeilen: String(s.arbeitsanweisungen||'').split('\n').length,
      steuer: {select: t.el.querySelectorAll('select').length,
               input: t.el.querySelectorAll('input').length,
               button: t.el.querySelectorAll('button').length}
    });
  }
  return out;
}"""

# Die UMKEHRPROBE zum Beschnitt-Melder. Ohne sie waere "kein Beschnitt" eine
# Behauptung ueber das Geraet, nicht ueber die App.
UMKEHR_JS = r"""() => {
  let ziel = null;
  for (const e of document.body.querySelectorAll('*')) {
    const cs = getComputedStyle(e);
    if (cs.overflowX !== 'hidden' && cs.overflowY !== 'hidden') continue;
    const eigen = [...e.childNodes].filter(n => n.nodeType === 3
      && (n.textContent||'').trim().length);
    if (!eigen.length) continue;
    if (e.scrollWidth > e.clientWidth + 1) continue;
    if (e.scrollHeight > e.clientHeight + 1) continue;
    ziel = e; break;
  }
  if (!ziel) return {ok: false, grund: 'kein ruhiges Klemm-Element gefunden'};
  window.__umkehrZiel = ziel;
  window.__umkehrAlt = ziel.textContent;
  ziel.textContent = 'X'.repeat(240);
  return {ok: true, tag: ziel.tagName.toLowerCase(),
          text: String(window.__umkehrAlt||'').slice(0, 40)};
}"""

UMKEHR_ZURUECK_JS = """() => {
  if (window.__umkehrZiel) window.__umkehrZiel.textContent = window.__umkehrAlt;
  return true;
}"""

# ── Positivprobe fuer Zwilling und Ueberbreiten-Melder ────────────────────
# Beide meldeten im ersten vollen Lauf eine NULL: keine gekappte Zeilenklammer,
# keine ueberbreite Stelle. Eine Null ist erst dann ein Ergebnis, wenn das
# Geraet nachweislich anschlagen KANN. Hier werden deshalb zwei Stellen
# absichtlich kaputt gemacht - eine zweizeilig geklammerte mit 400 Zeichen und
# eine 200 px zu breite - und wieder entfernt. Schlaegt das Geraet dabei nicht
# an, ist jede vorher gemessene Null wertlos.
POSITIV_JS = r"""() => {
  const halter = document.createElement('div');
  halter.id = '__positivprobe';
  const a = document.createElement('div');
  a.style.cssText = 'display:-webkit-box;-webkit-line-clamp:2;'
    + '-webkit-box-orient:vertical;overflow:hidden;font-size:12px;'
    + 'line-height:15px;width:200px';
  a.textContent = 'Pruefsatz mit vierhundert Zeichen. ' + 'lang '.repeat(72);
  const b = document.createElement('div');
  b.style.cssText = 'width:' + (window.innerWidth + 200) + 'px;height:8px;'
    + 'background:transparent';
  b.textContent = 'zu breit';
  halter.appendChild(a); halter.appendChild(b);
  (document.getElementById('root') || document.body).appendChild(halter);
  return true;
}"""

POSITIV_WEG_JS = """() => {
  const h = document.getElementById('__positivprobe');
  if (h && h.parentElement) h.parentElement.removeChild(h);
  return true;
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


def _rollen(y, hoehe, nutzbar):
    """Wieviel muss man rollen, bis das Ding oben bzw. ganz sichtbar ist."""
    if y is None:
        return (None, None)
    return (max(0, y - nutzbar + 1), max(0, y + (hoehe or 0) - nutzbar))


def main(nur=None, rolle="admin", nachher=False, netz="aus"):
    """netz='aus'  - die REST-Aufrufe werden abgebrochen (Monteur ohne Netz).
       netz='401'  - sie laufen ins 401 des Testzugangs.

    DER UNTERSCHIED IST KEINE FEINHEIT, ER IST EIN BEFUND. _sbGet gibt bei
    401/403 ein LEERES ARRAY im ERFOLGSPFAD zurueck (:2071). loadWeek in der
    Zeiterfassung (:25132) nimmt dieses leere Array als Antwort und erreicht
    seinen eigenen Auffangzweig NIE - der greift nur, wenn fetch WIRFT. Mit
    401 zeigt die Woche also nichts, obwohl Eintraege im Zwischenspeicher
    liegen. Beide Faelle werden hier gemessen, damit die Zahl nicht davon
    abhaengt, welchen man zufaellig erwischt hat.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt.  pip install playwright && playwright install chromium")
        return 2

    os.makedirs(ZIEL, exist_ok=True)
    port = _server()
    url = "http://127.0.0.1:%d/%s" % (port, os.environ.get("EPK_INDEX", "index.html"))
    print("Gemessen wird:", url, " Rolle:", rolle)

    # Der INIT-Nutzer aus tab_sweep hat KEINE monteurId. Ohne die bleibt
    # selWorker leer, die Zeiterfassung zeigt "kein Mitarbeiter gewaehlt" -
    # ein leerer Renderpfad, und jede Zahl daraus waere wertlos.
    EXTRA = ("try{ var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
             " u.role=%s; u.monteurId=\"M1\"; u.name=\"Gerhard Steinbichler\";"
             " u.rolle=\"Monteur\";"
             " localStorage.setItem('epkolar_user',JSON.stringify(u)); }catch(e){}"
             % json.dumps(rolle))

    ergebnisse = []
    fehler = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for (bw, bh, wie) in GERAETE:
            if nur and ("%dx%d" % (bw, bh)) != nur:
                continue
            for (leiste, leistenname) in LEISTEN:
                hoehe = bh - leiste
                ctx = browser.new_context(
                    viewport={"width": bw, "height": hoehe},
                    device_scale_factor=1, is_mobile=True, has_touch=True)
                ctx.add_init_script(INIT)
                ctx.add_init_script(EXTRA)
                if netz == "aus":
                    ctx.route("**/rest/v1/**", lambda r: r.abort())
                    ctx.route("**/auth/v1/**", lambda r: r.abort())
                seite = ctx.new_page()
                seite.on("pageerror",
                         lambda e: fehler.append("pageerror: " + str(e)[:140]))

                def konsole(m, _f=fehler):
                    try:
                        art = m.type if isinstance(m.type, str) else m.type()
                        txt = m.text if isinstance(m.text, str) else m.text()
                    except Exception:
                        return
                    if art != "error":
                        return
                    if not any(x.lower() in str(txt).lower() for x in IGNORIEREN):
                        _f.append("console: " + str(txt)[:120])
                seite.on("console", konsole)

                print("\n-- %dx%d, Leiste %d px (%s), Netz %s"
                      % (bw, bh, leiste, leistenname, netz))
                seite.goto(url, wait_until="domcontentloaded")
                seite.wait_for_timeout(4000)
                scheine, _e = saeen_schwer(seite)

                d = {"breite": bw, "fenster": bh, "leiste": leiste,
                     "leistenname": leistenname, "geraet": wie, "netz": netz}

                # ── Arbeitsscheine ──
                d["nav_oeffnen"] = seite.evaluate(NAV_OEFFNEN_JS)
                seite.wait_for_timeout(500)
                d["nav_as"] = seite.evaluate(NAV_WAEHLEN_JS, "Arbeitsscheine")
                seite.wait_for_timeout(2500)
                seite.evaluate("() => window.scrollTo(0,0)")
                seite.wait_for_timeout(300)
                d["grund"] = seite.evaluate(GRUND_JS)
                if nachher:
                    d["nachher_n"] = seite.evaluate(EINSPIELEN_JS, NACHHER_CSS)
                    seite.wait_for_timeout(400)
                d["kachel_ruhig"] = seite.evaluate(KACHEL_JS)
                d["as"] = seite.evaluate(AS_JS)
                d["as_tipp"] = seite.evaluate(TIPP_JS, None)
                d["as_beschnitt"] = seite.evaluate(BESCHNITT_JS, None)
                d["as_klammer"] = seite.evaluate(KLAMMER_JS, None)
                d["as_breit"] = seite.evaluate(UEBERBREIT_JS)
                d["abgleich"] = seite.evaluate(ABGLEICH_JS, scheine)
                if leiste == 0:
                    u = seite.evaluate(UMKEHR_JS)
                    seite.wait_for_timeout(250)
                    mit = seite.evaluate(BESCHNITT_JS, None)
                    seite.evaluate(UMKEHR_ZURUECK_JS)
                    seite.wait_for_timeout(250)
                    zur = seite.evaluate(BESCHNITT_JS, None)
                    d["umkehr"] = {"ziel": u,
                                   "vorher": len(d["as_beschnitt"].get("funde", [])),
                                   "mit_langtext": len(mit.get("funde", [])),
                                   "zurueck": len(zur.get("funde", []))}
                    # Positivprobe fuer Zwilling und Ueberbreiten-Melder
                    def _kapp(res):
                        return len([f for f in res.get("funde", [])
                                    if f["fehlt_px"] >= 4 or f["fehlt_breit"] >= 4])
                    vor_k = _kapp(d["as_klammer"])
                    vor_b = len(d["as_breit"].get("funde", []))
                    seite.evaluate(POSITIV_JS)
                    seite.wait_for_timeout(300)
                    mit_k = _kapp(seite.evaluate(KLAMMER_JS, None))
                    mit_b = len(seite.evaluate(UEBERBREIT_JS).get("funde", []))
                    seite.evaluate(POSITIV_WEG_JS)
                    seite.wait_for_timeout(300)
                    d["positiv"] = {"klammer_vor": vor_k, "klammer_mit": mit_k,
                                    "breit_vor": vor_b, "breit_mit": mit_b}
                seite.screenshot(path=os.path.join(
                    ZIEL, "mob_as_%dx%d_l%d.png" % (bw, bh, leiste)))
                # Die Ziffernprobe ganz zuletzt - sie veraendert die
                # Kacheltexte, und alles davor soll die echten Werte sehen.
                d["stress_n"] = seite.evaluate(STRESS_JS)
                seite.wait_for_timeout(400)
                d["kachel_stress"] = seite.evaluate(KACHEL_JS)

                # ── Zeiterfassung ──
                seite.evaluate(NAV_OEFFNEN_JS)
                seite.wait_for_timeout(500)
                d["nav_zeit"] = seite.evaluate(NAV_WAEHLEN_JS, "Zeiterfassung")
                seite.wait_for_timeout(3500)
                seite.evaluate("() => window.scrollTo(0,0)")
                seite.wait_for_timeout(300)
                d["zeit_grund"] = seite.evaluate(GRUND_JS)
                d["zeit"] = seite.evaluate(ZEIT_JS)
                d["zeit_tipp"] = seite.evaluate(TIPP_JS, None)
                d["zeit_beschnitt"] = seite.evaluate(BESCHNITT_JS, None)
                d["zeit_klammer"] = seite.evaluate(KLAMMER_JS, None)
                d["zeit_breit"] = seite.evaluate(UEBERBREIT_JS)
                d["odb_zeiten"] = seite.evaluate(
                    ODB_ZEITEN_JS, {"db": DB_NAME, "worker": "M1",
                                    "tage": _woche_iso()})
                seite.screenshot(path=os.path.join(
                    ZIEL, "mob_zeit_%dx%d_l%d.png" % (bw, bh, leiste)))

                print("   AS: %s Karten, y=%s | Zeit: %s Tageskarten, "
                      "y_eintrag=%s" % (d["as"].get("gefunden"), d["as"].get("y"),
                                        d["zeit"].get("tageskarten"),
                                        d["zeit"].get("y_eintrag")))
                ergebnisse.append(d)
                ctx.close()

        # ── Der Rechner-Schirm als Vergleichsmass ──────────────────────────
        # Ohne ihn waere "am Telefon fehlt etwas" eine Behauptung. Gemessen
        # wird dieselbe Saat in derselben Ansicht, nur breit.
        rechner = None
        if not nur:
            ctx = browser.new_context(viewport={"width": 1440, "height": 900},
                                      device_scale_factor=1)
            ctx.add_init_script(INIT)
            ctx.add_init_script(EXTRA)
            if netz == "aus":
                ctx.route("**/rest/v1/**", lambda r: r.abort())
                ctx.route("**/auth/v1/**", lambda r: r.abort())
            seite = ctx.new_page()
            print("\n-- Vergleich: 1440x900 (Rechner)")
            seite.goto(url, wait_until="domcontentloaded")
            seite.wait_for_timeout(4000)
            scheine, _e = saeen_schwer(seite)
            for name in ("Arbeitsscheine",):
                ziel = seite.get_by_text(name, exact=False)
                if ziel.count():
                    ziel.first.click()
            seite.wait_for_timeout(2500)
            seite.evaluate("() => window.scrollTo(0,0)")
            seite.wait_for_timeout(300)
            rechner = {"abgleich": seite.evaluate(ABGLEICH_JS, scheine),
                       "tipp": seite.evaluate(TIPP_JS, None),
                       "klammer": seite.evaluate(KLAMMER_JS, None)}
            seite.screenshot(path=os.path.join(ZIEL, "mob_vergleich_1440.png"))
            ctx.close()
        browser.close()

    _bericht(ergebnisse, fehler, nachher, rechner)
    with open(os.path.join(ZIEL, "mob_ansicht_messung.json"), "w",
              encoding="utf-8") as f:
        json.dump({"mobil": ergebnisse, "rechner": rechner},
                  f, ensure_ascii=False, indent=1)
    print("\n  Rohwerte: screenshots/mob_ansicht_messung.json")
    return 0


def _bericht(ergebnisse, fehler, nachher, rechner=None):
    print()
    print("=" * 78)
    print("MESSTABELLE  -  %s" % ("NACHHER" if nachher else "VORHER"))
    if ergebnisse:
        print("App-Fassung: %s" % ergebnisse[0]["grund"].get("version"))
    print("=" * 78)
    print("%-10s %-4s %-6s %-5s %-6s %-6s %-7s %-6s"
          % ("Geraet", "Lst", "Fenst", "Fuss", "nutzb", "y-AS", "rollen", "sicht"))
    print("-" * 78)
    for d in ergebnisse:
        g = d["grund"]
        nutzbar = g["hoehe"] - g["fussleiste"]
        a = d["as"]
        y = a.get("y")
        oben, _ganz = _rollen(y, a.get("hoehe"), nutzbar)
        print("%-10s %-4d %-6d %-5d %-6d %-6s %-7s %-6s"
              % ("%dx%d" % (d["breite"], d["fenster"]), d["leiste"],
                 g["hoehe"], g["fussleiste"], nutzbar,
                 y if y is not None else "-",
                 oben if oben is not None else "-",
                 ("JA" if (y is not None and y < nutzbar) else "NEIN")))
    print()
    print("  Lst    = Browserleiste in px, die vom Geraetefenster abgeht")
    print("  Fuss   = GEMESSENE Hoehe der App-Fussleiste (.bottom-nav, liegt")
    print("           ueber dem Inhalt)")
    print("  nutzb  = Fensterhoehe minus Fussleiste")
    print("  y-AS   = Oberkante der ersten Arbeitsschein-Karte im Dokument")
    print("  rollen = px, die man rollen muss, damit diese Oberkante erscheint")

    print()
    print("=" * 78)
    print("ZEITERFASSUNG")
    print("=" * 78)
    print("%-10s %-4s %-6s %-7s %-7s %-4s %-6s %-6s"
          % ("Geraet", "Lst", "nutzb", "y-Tag1", "y-Eintr", "h", "roll-ob",
             "roll-gz"))
    print("-" * 78)
    for d in ergebnisse:
        g = d.get("zeit_grund") or d["grund"]
        nutzbar = g["hoehe"] - g["fussleiste"]
        z = d["zeit"]
        ye = z.get("y_eintrag")
        oben, ganz = _rollen(ye, z.get("hoehe_eintrag"), nutzbar)
        print("%-10s %-4d %-6d %-7s %-7s %-4s %-6s %-6s"
              % ("%dx%d" % (d["breite"], d["fenster"]), d["leiste"], nutzbar,
                 z.get("y_karte", "-"), ye if ye is not None else "-",
                 z.get("hoehe_eintrag", "-"),
                 oben if oben is not None else "-",
                 ganz if ganz is not None else "-"))
    print("  roll-ob = px bis die Oberkante des ersten Eintrags erscheint")
    print("  roll-gz = px bis der erste Eintrag GANZ zu sehen ist")
    if ergebnisse:
        z = ergebnisse[0]["zeit"]
        print("\n  Tageskarten: %s   Eintraege am ersten Tag: %s"
              % (z.get("tageskarten"), z.get("eintraege_tag1")))

    if ergebnisse:
        print()
        print("=" * 78)
        print("VORBAU UEBER DER ERSTEN ARBEITSSCHEIN-KARTE (%dx%d)"
              % (ergebnisse[0]["breite"], ergebnisse[0]["fenster"]))
        print("=" * 78)
        for b in ergebnisse[0]["as"].get("bloecke", []):
            print("  y=%4d  h=%3d  %s%-18s %s"
                  % (b["y"], b["hoehe"], "  " * b.get("t", 0),
                     b.get("was", ""), b["text"]))
        print()
        print("VORBAU UEBER DER ERSTEN TAGESKARTE")
        for b in ergebnisse[0]["zeit"].get("bloecke", []):
            print("  y=%4d  h=%3d  %s%-18s %s"
                  % (b["y"], b["hoehe"], "  " * b.get("t", 0),
                     b.get("was", ""), b["text"]))

    for feld, titel in (("as_tipp", "ARBEITSSCHEIN-LISTE"),
                        ("zeit_tipp", "ZEITERFASSUNG")):
        print()
        print("=" * 78)
        print("TIPPZIELE %s   (WCAG 2.2 AA: 24x24 px, Apple/AAA: 44x44)" % titel)
        print("=" * 78)
        for d in ergebnisse:
            if d["leiste"] != 0:
                continue
            ziele = d.get(feld, {}).get("ziele", [])
            if not ziele:
                print("  %dx%d: KEIN Tippziel gefunden - Messgeraet pruefen."
                      % (d["breite"], d["fenster"]))
                continue
            unter24 = [z for z in ziele if z["klein"] < 24]
            unter44 = [z for z in ziele if z["klein"] < 44]
            gross = [z for z in ziele if z["klein"] >= 36]
            print("  %dx%d: %d Ziele, %d unter 24 px, %d unter 44 px"
                  % (d["breite"], d["fenster"], len(ziele),
                     len(unter24), len(unter44)))
            gezeigt = set()
            for z in sorted(unter44, key=lambda x: x["klein"]):
                k = (z["tag"], z["name"], z["b"], z["h"])
                if k in gezeigt:
                    continue
                gezeigt.add(k)
                print("      %3d px  %-4s %-14s %-30s %dx%d"
                      % (z["klein"], "AA!" if z["klein"] < 24 else "",
                         z["tag"] + (("/" + z["rolle"]) if z["rolle"] else ""),
                         z["name"], z["b"], z["h"]))
            print("      GEGENPROBE: %d Ziele mit >= 36 px gemessen "
                  "(Chips und Kartenknoepfe tragen minHeight 36; waeren es 0, "
                  "misst das Geraet die Knoepfe nicht)" % len(gross))
            # Die Null bei "unter 24 px" waere sonst eine Hoffnung. Das
            # Stylesheet deckt echte button/input/select bei <=600px mit
            # min-height 44 (:261, :265) - ein <span role=button> aber NICHT.
            # Fuer den gilt :218 mit min-height UND min-width 44. Getrennt
            # ausgewiesen, damit sichtbar ist, dass beide Gruppen gemessen
            # wurden und nicht nur die leichte.
            frei = [z for z in ziele if not z.get("gedeckt")]
            frei_klein = [z for z in frei if z["klein"] < 44]
            print("      davon %d ohne echtes Knopf-Element (span/div mit "
                  "role=button), die die 44er-Regel fuer button/input/select "
                  "NICHT deckt - davon unter 44 px: %d"
                  % (len(frei), len(frei_klein)))

    for feld, titel in (("as_beschnitt", "ARBEITSSCHEIN-LISTE"),
                        ("zeit_beschnitt", "ZEITERFASSUNG")):
        print()
        print("=" * 78)
        print("TEXTBESCHNITT %s" % titel)
        print("=" * 78)
        for d in ergebnisse:
            if d["leiste"] != 0:
                continue
            funde = d.get(feld, {}).get("funde", [])
            lautlos = [f for f in funde if f["art"] == "LAUTLOS"]
            ell = [f for f in funde if f["art"] == "ELLIPSIS"]
            print("  %dx%d: %d lautlos, %d mit Ellipsis/Zeilenklammer"
                  % (d["breite"], d["fenster"], len(lautlos), len(ell)))
            for f in lautlos:
                print("      LAUTLOS  <%s> +%d px breit, +%d px hoch | %s"
                      % (f["tag"], f["breit"], f["hoch"], f["text"][:58]))
            for f in ell[:10]:
                print("      sichtbar <%s> klammer=%s | %s"
                      % (f["tag"], f["klammer"] or "-", f["text"][:58]))

    for feld, titel in (("as_klammer", "ARBEITSSCHEIN-LISTE"),
                        ("zeit_klammer", "ZEITERFASSUNG")):
        print()
        print("=" * 78)
        print("ZEILENKLAMMER / EINZEILER, gegen einen freien Zwilling gemessen"
              " - %s" % titel)
        print("=" * 78)
        for d in ergebnisse:
            if d["leiste"] != 0:
                continue
            funde = d.get(feld, {}).get("funde", [])
            # Schwelle 4 px, nicht 1: ein Emoji-Glyph ragt in Chromium
            # regelmaessig 2-3 px ueber seine Zeilenbox hinaus. Bei Schwelle 1
            # meldete dieses Geraet im ersten Anlauf fuenf Fussleisten-Symbole
            # als "Beschnitt" - fuenf saubere Zahlen ueber nichts.
            gekappt = [f for f in funde if f["fehlt_px"] >= 4
                       or f["fehlt_breit"] >= 4]
            passt = [f for f in funde if f["fehlt_px"] < 4
                     and f["fehlt_breit"] < 4]
            print("  %dx%d: %d von %d geklammerten Stellen kappen wirklich"
                  % (d["breite"], d["fenster"], len(gekappt), len(funde)))
            for f in gekappt:
                print("      <%-4s %-12s b=%3d  zeigt %3d von %3d px "
                      "(%s Zeilen fehlen)  %s"
                      % (f["tag"] + ">", f["art"], f["breite"], f["gezeigt"],
                         f["gebraucht"], f["fehlt_zeilen"], f["text"][:46]))
            print("      Gegenprobe: %d geklammerte Stellen kappen NICHT - "
                  "der Zwilling misst also nicht pauschal zu gross."
                  % len(passt))
            p = d.get("positiv")
            if p and feld == "as_klammer":
                ok = p["klammer_mit"] > p["klammer_vor"]
                print("      POSITIVPROBE: eine absichtlich zweizeilig "
                      "geklammerte Stelle mit 400 Zeichen eingesetzt -> "
                      "%d statt %d Funde  ->  %s"
                      % (p["klammer_mit"], p["klammer_vor"],
                         "ZWILLING SCHLAEGT AN" if ok
                         else "ZWILLING TAUGT NICHT, jede Null oben ist wertlos"))

    print()
    print("=" * 78)
    print("KACHELBLOCK  (der groesste einzelne Block ueber der Liste)")
    print("=" * 78)
    for d in ergebnisse:
        if d["leiste"] != 0:
            continue
        k = d.get("kachel_ruhig") or {}
        s = d.get("kachel_stress") or {}
        if k.get("fehler"):
            print("  %dx%d: %s" % (d["breite"], d["fenster"], k["fehler"]))
            continue
        br = [x for x in k.get("kacheln", []) if x["beschnitt"]]
        brs = [x for x in s.get("kacheln", []) if x["beschnitt"]]
        klick = len([x for x in k.get("kacheln", []) if x["klickbar"]])
        tast = len([x for x in k.get("kacheln", []) if x["tastatur"]])
        breiten = sorted(set(x["b"] for x in k.get("kacheln", [])))
        print("  %dx%d  y=%s  Hoehe=%s px  %s Kacheln  Breiten %s  "
              "klickbar %d  Taste %d  quer rollbar %s"
              % (d["breite"], d["fenster"], k.get("y"), k.get("hoehe"),
                 k.get("anzahl"), breiten, klick, tast,
                 "JA" if k.get("quer_rollbar") else "nein"))
        print("       Ziffernbeschnitt mit echten Werten: %d Kacheln"
              % len(br))
        print("       ZIFFERNPROBE alle Werte auf 12.345 (%s gesetzt): "
              "%d Kacheln beschnitten%s"
              % (d.get("stress_n"), len(brs),
                 ("  -> " + ", ".join(x["text"][:18] for x in brs[:4]))
                 if brs else " - keine"))

    print()
    print("=" * 78)
    print("UEBERBREITE  (html,body tragen bei <=600px overflow-x:hidden -")
    print("was rechts hinausragt, ist weg und nicht errollbar)")
    print("=" * 78)
    for feld, titel in (("as_breit", "Arbeitsscheine"), ("zeit_breit", "Zeit")):
        for d in ergebnisse:
            if d["leiste"] != 0:
                continue
            u = d.get(feld) or {}
            f = u.get("funde", [])
            print("  %-14s %dx%d: Schirm %s px, breitester Inhalt %s px, "
                  "%d Stellen ragen hinaus"
                  % (titel, d["breite"], d["fenster"], u.get("schirm"),
                     u.get("dokument"), len(f)))
            for x in f[:6]:
                print("       <%s> %d px hinaus (links %d, rechts %d) | %s"
                      % (x["tag"], x["raus"], x["links"], x["rechts"],
                         x["text"][:46]))
            p = d.get("positiv")
            if p and feld == "as_breit":
                ok = p["breit_mit"] > p["breit_vor"]
                print("       POSITIVPROBE: ein 200 px zu breiter Kasten "
                      "eingesetzt -> %d statt %d Funde  ->  %s"
                      % (p["breit_mit"], p["breit_vor"],
                         "MELDER SCHLAEGT AN" if ok
                         else "MELDER TAUGT NICHT, die Null oben ist wertlos"))

    print()
    print("=" * 78)
    print("ZEITEN IM GERAET GEGEN ZEITEN AUF DEM SCHIRM")
    print("=" * 78)
    for d in ergebnisse:
        if d["leiste"] != 0:
            continue
        o = d.get("odb_zeiten") or {}
        z = d["zeit"]
        print("  %dx%d  Netz=%s:  im Zwischenspeicher %s Eintraege, davon %s "
              "in dieser Woche fuer M1  ->  auf dem Schirm am ersten Tag: %s"
              % (d["breite"], d["fenster"], d.get("netz"), o.get("gesamt"),
                 o.get("in_der_woche"), z.get("eintraege_tag1")))

    print()
    print("=" * 78)
    print("INHALT DER MOBIL-KARTE GEGEN DIE GESAETEN DATEN")
    print("=" * 78)
    for d in ergebnisse:
        if d["leiste"] != 0:
            continue
        print("  --- %dx%d ---" % (d["breite"], d["fenster"]))
        for a in d.get("abgleich", []):
            if not a.get("gefunden"):
                print("      %s NICHT GEFUNDEN" % a["nummer"])
                continue
            print("      %s (%s)  Kunde=%-9s KdNr=%-5s Ort=%-5s SB=%-5s "
                  "ProjNr=%-5s"
                  % (a["nummer"], a["art"], a["kunde"], a["kundNr"],
                     a["arbeitsort"], a["sachbearbeiter"], a["projektnr"]))
            print("           Anweisung %d Zeichen / %d Zeilen -> ganz: %s, "
                  "erste Zeile: %s"
                  % (a["anweisung_zeichen"], a["anweisung_zeilen"],
                     a["anweisung_ganz"], a["anweisung_erste_zeile"]))
        break
    if rechner:
        print("  --- 1440x900 (Rechner), dieselbe Saat ---")
        for a in rechner.get("abgleich", []):
            if not a.get("gefunden"):
                print("      %s NICHT GEFUNDEN" % a["nummer"])
                continue
            print("      %s (%s)  Kunde=%-9s KdNr=%-5s Ort=%-5s SB=%-5s "
                  "ProjNr=%-5s"
                  % (a["nummer"], a["art"], a["kunde"], a["kundNr"],
                     a["arbeitsort"], a["sachbearbeiter"], a["projektnr"]))
            print("           Anweisung %d Zeichen / %d Zeilen -> ganz: %s, "
                  "erste Zeile: %s"
                  % (a["anweisung_zeichen"], a["anweisung_zeilen"],
                     a["anweisung_ganz"], a["anweisung_erste_zeile"]))

        print()
        print("=" * 78)
        print("BEDIENELEMENTE: KARTE (Telefon) GEGEN ZEILE (Rechner)")
        print("=" * 78)
        m = None
        for d in ergebnisse:
            if d["leiste"] == 0:
                m = d
                break
        if m:
            for a, b in zip(m.get("abgleich", []), rechner.get("abgleich", [])):
                if not (a.get("gefunden") and b.get("gefunden")):
                    continue
                print("  %s  Telefon(%s): select=%d input=%d button=%d"
                      "   |   Rechner(%s): select=%d input=%d button=%d"
                      % (a["nummer"], a["art"], a["steuer"]["select"],
                         a["steuer"]["input"], a["steuer"]["button"],
                         b["art"], b["steuer"]["select"], b["steuer"]["input"],
                         b["steuer"]["button"]))

    print()
    print("=" * 78)
    print("UMKEHRPROBE ZUM BESCHNITT-MELDER")
    print("=" * 78)
    for d in ergebnisse:
        u = d.get("umkehr")
        if not u:
            continue
        ok = (u["mit_langtext"] > u["vorher"] and u["zurueck"] == u["vorher"])
        print("  %dx%d  ruhig=%d  mit 240 Zeichen=%d  zurueck=%d  -> %s"
              % (d["breite"], d["fenster"], u["vorher"], u["mit_langtext"],
                 u["zurueck"], "MELDER TAUGT" if ok else "MELDER FRAGWUERDIG"))

    print()
    print("=" * 78)
    print("BEDIENELEMENTE IN DER MOBIL-KARTE")
    print("=" * 78)
    for d in ergebnisse:
        if d["leiste"] != 0:
            continue
        ik = d["as"].get("in_karte", {})
        print("  %dx%d  select=%s  input=%s  button=%s  role=button=%s"
              % (d["breite"], d["fenster"], ik.get("select"), ik.get("input"),
                 ik.get("button"), ik.get("rolle_button")))

    if fehler:
        print()
        print("SEITENFEHLER:", fehler[:6])


if __name__ == "__main__":
    _nur = None
    _rolle = "admin"
    _netz = "aus"
    if "--nur" in sys.argv:
        _nur = sys.argv[sys.argv.index("--nur") + 1]
    if "--rolle" in sys.argv:
        _rolle = sys.argv[sys.argv.index("--rolle") + 1]
    if "--netz" in sys.argv:
        _netz = sys.argv[sys.argv.index("--netz") + 1]
    sys.exit(main(_nur, _rolle, "--nachher" in sys.argv, _netz))
