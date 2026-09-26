# -*- coding: utf-8 -*-
"""B3 Stufen 12-15: DREIZEHN Hauptansichten am GERENDERTEN Schirm messen.

WOZU
────
Fortsetzung von `b3_stufen_8_11_messen.py` (Stufen 8-11) und
`b3_vier_ansichten_messen.py` (Stufen 4-7). Dieselben Regeln, dieselben
Koeder - nur andere Ansichten, und diesmal dreizehn statt fuenf:

  Stufe 12  Chef-Dashboard · Zeiterfassung · Abwesenheiten
  Stufe 13  Monatsabrechnung · Fahrzeuge · Flotte
  Stufe 14  Mitarbeiter · Auswertungen · Buero-Portal
  Stufe 15  Admin · Einstellungen · Gefahrenstoffe · Bauprovisorien

Alle dreizehn sind HAUPTREITER (`_allTabs`), keine Projekt-Unterseiten.
Navigiert wird deshalb ueber die obere Reiterleiste (>=600 px, `aria-label`
= Reiterbeschriftung) bzw. ueber das Mehr-Menue der Fussleiste (<600 px) -
und in beiden Faellen NIE ueber einen Knopf in `.bottom-nav` (Messfehler 4
aus B3_STUFEN_4_7.md: der Gruppenknopf der Fussleiste oeffnet den zuletzt
aktiven Reiter SEINER GRUPPE, und ein Agent hat so ein Chef-Dashboard
vermessen und "Home" darueber geschrieben).

WAS GEMESSEN WIRD
─────────────────
  Die sieben Regeln aus Stufe 4-7, unveraendert importiert:
    SCHRIFT_JS (berechnet, nicht im Quelltext) · TIPP_JS (Knopf-Topf und
    Feld/Beschriftungs-Topf GETRENNT) · EMOJI_JS · QUER_JS (jeder Behaelter,
    nicht document.scrollingElement) · BESCHNITT_JS · TABELLE_JS ·
    MENGEN_JS · VERDECKUNG_JS · BIS_UNTEN_JS
  Dazu aus Stufe 8-11:
    EMOJI_ZAHL_JS (ohne BUCHSTABEN statt ohne Text - `🎫3` ist keine
    Bedeutung) · BESCHNITT_ECHT_JS (wirklich gekuerzt GEGEN blossen
    Kastenueberlauf) · DUNKEL_JS (Flaechenfarbe im Hellmodus, gemischt,
    geurteilt nach ANTEIL am Schirm ab 25 %)
  NEU in dieser Stufe:
    MENGEN_BENANNT_JS  Bestandsschutz gegen docs/GRUNDSTAND_UI_v3.9.930.md
                       nach BENANNTEN STUECKEN (Knopf-/Reiter-/Spalten-
                       WORTLAUT), nicht gegen rohe Knopfzahlen. Verglichen
                       wird nach Abzug aller Nicht-Buchstaben, und gesucht
                       wird NUR in Knoepfen/Reitern - nicht in <option>
                       (Messfehler N-1/N-2 aus Stufe 8-11: eine Zaehlung auf
                       Gleichheit meldete 9 von 11 Kacheln als verschwunden,
                       die reparierte fand die Woerter dann in Auswahlfeldern).
    SPEZIFITAET_JS     Findet CSS-Regeln, die die 44-px-Hausregel durch
                       hoehere Spezifitaet schlagen, und NENNT die
                       Spezifitaet (Vorbild: die drei Regeln aus v3.9.942,
                       `.header-row .mob-stack button` = 0,2,1 gegen
                       `button` = 0,0,1).
    CHART_MA_JS        Stufe 14, Sonderauftrag "Ehemalige nur mit Beitrag":
                       liest aus dem gerenderten Diagramm die Balken mit
                       ihren Beschriftungen und Werten, damit sichtbar wird,
                       ob ein Ausgetretener mit NULL erscheint.

WAS NICHT GEMESSEN WIRD
───────────────────────
  * Rollen-Gatter. Gefahren wird role=admin, monteurId=M1. Chef, Admin,
    Einstellungen, Flotte und Buero-Portal sind rollengeschuetzt; ein
    Monteur sieht sie gar nicht, ein Buero/PL anders.
  * Echte Serverdaten. REST/Auth werden abgebrochen. Jede Ansicht, die ihre
    Zeilen ueber `API.request`/`_sbGet` holt (Bauprovisorien, Gefahrenstoffe,
    Flotte-Positionen, Admin-Nutzer, Buero-Portal-Exporte), ist in diesem
    Aufbau LEER. Das wird als leere Grundgesamtheit AUSGEWIESEN - eine
    serverleere Ansicht ist KEIN gemessener Ist-Zustand.
  * Farbkontrast von TEXT. Gemessen wird nur die Flaeche.
  * Die Tastaturbedienung und die Fokusreihenfolge.
  * Unterzustaende, die erst nach einer Eingabe entstehen (Formulare,
    Modale) - ausser den ausdruecklich angefahrenen Unterreitern.

DIE KOEDER
──────────
K1-K8   unveraendert aus b3_vier_ansichten_messen.py (`_koeder`).
K9      Beschnitt-Einordnung, zwei Baits (aus Stufe 8-11).
K12     Flaechenmelder im Dunkelmodus als Positivkontrolle (aus Stufe 8-11).
K13     "nur Symbol + Zahl" - Knopf `🔩7`, den der ALTE Melder durchlaesst
        und der neue fangen MUSS (aus Stufe 8-11).
K14 NEU Ehemalige. Die Saat traegt FUENF Monteure: drei aktive, einen
        Ausgetretenen MIT Beitrag (M4, hat Scheine und Abwesenheiten) und
        einen Ausgetretenen OHNE jeden Beitrag (M5, hat nichts).
        `_maIstEhemalig` MUSS fuer M4 und M5 wahr sein und fuer M1-M3
        falsch - sonst misst die Sonde die Frage nicht, die sie stellt.
        Und: M5 MUSS in einer Zuweisungs-Auswahl FEHLEN (`_maWaehlbar`
        greift) und in einer Filter-/Reportliste STEHEN. Schlaegt das nicht
        an, ist der Unterschied Diagramm/Auswahlliste nicht gemessen.
K15 NEU Bestandsschutz-Zaehler. Zu jeder benannten Prueflistenzeile wird
        zusaetzlich ein WORT gesucht, das es in dieser Ansicht mit
        Sicherheit NICHT gibt (`Kalibrierungsintervallpruefung`). Findet der
        Zaehler es, zaehlt er nicht, was er behauptet.

AUFRUF
──────
    set EPK_INDEX=_mess_stand_944.html
    python scripts/b3_stufen_12_15_messen.py --json b3_12_15.json
    python scripts/b3_stufen_12_15_messen.py --nur auswertungen
    python scripts/b3_stufen_12_15_messen.py --nur chef --hell
    EPK_BREITEN="390,1440" python scripts/b3_stufen_12_15_messen.py
    python scripts/b3_stufen_12_15_messen.py --erkunden   (nur Inventar)

index.html wird NICHT angefasst. Gemessen wird die Datei aus EPK_INDEX.
"""
import io
import json
import os
import sys

for _strom in (sys.stdout, sys.stderr):
    try:
        _strom.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)

import mob_ansicht_messen as M           # noqa: E402
import b3_vier_ansichten_messen as B     # noqa: E402
import b3_stufen_8_11_messen as S        # noqa: E402

BREITEN = B.BREITEN


# ══════════════════════════════════════════════════════════════════════════
# Saat
# ══════════════════════════════════════════════════════════════════════════
# FUENF Monteure statt drei. M4 und M5 sind AUSGETRETEN; M4 hat im
# Auswertungszeitraum einen Beitrag (Scheine, Abwesenheiten, Zeiten), M5 hat
# KEINEN. Genau dieses Paar ist der Koeder K14: ohne M5 waere "Ausgetretene
# erscheinen mit Null" nicht pruefbar, ohne M4 waere "Ausgetretene mit
# Beitrag muessen bleiben" nicht pruefbar.
MONTEURE = [
    {"id": "M1", "n": "Gerhard Steinbichler", "r": "Monteur", "austritt": "",
     "rolle": "Monteur", "aktiv": True},
    {"id": "M2", "n": "Johannes Hinterleitner", "r": "Obermonteur",
     "austritt": "", "rolle": "Obermonteur", "aktiv": True},
    {"id": "M3", "n": "Bernadette Wieshofer-Prandtner", "r": "Monteur",
     "austritt": "", "rolle": "Monteur", "aktiv": True},
    # AUSGETRETEN, MIT Beitrag
    {"id": "M4", "n": "Ferdinand Aschenbrenner", "r": "Monteur",
     "austritt": "2026-03-31", "rolle": "Monteur", "aktiv": False},
    # AUSGETRETEN, OHNE jeden Beitrag
    {"id": "M5", "n": "Roswitha Puchleitner", "r": "Helfer",
     "austritt": "2025-09-30", "rolle": "Helfer", "aktiv": False},
]


def _iso_vor(tage):
    return S._iso_vor(tage)


def _scheine12():
    """Die sechs Scheine aus Stufe 8-11, plus zwei auf M4 (Ausgetretener MIT
    Beitrag). Auf M5 liegt KEIN Schein - das ist der Punkt."""
    sch = S._scheine8()
    sch = sch + [
        {"id": "S7", "nummer": "AS-2407", "kunde": "Steiner Landstrasse 12",
         "scheinstatus": "erledigt", "scheinart": "wartung", "monteur": "M4",
         "arbeitsanweisungen": "Jahreswartung Verteiler Stiege 3",
         "erfassungsdatum": _iso_vor(120), "prio": "normal"},
        {"id": "S8", "nummer": "AS-2408", "kunde": "Steiner Landstrasse 12",
         "scheinstatus": "abgerechnet", "scheinart": "reparatur",
         "monteur": "M4",
         "arbeitsanweisungen": "Trafostation Hilti-Anker nachsetzen",
         "erfassungsdatum": _iso_vor(140), "prio": "hoch"},
    ]
    return sch


def _eintraege12():
    e = list(S._eintraege8())
    for i, tage in enumerate((95, 96)):
        e.append({"id": "Z9%d" % i, "w": "M4", "worker": "M4", "pid": "P1",
                  "p": "P1", "date": _iso_vor(tage), "datum": _iso_vor(tage),
                  "stunden": 8, "hours": 8, "gw": "Elektro",
                  "gewerk": "Elektro", "taetigkeit": "Verteiler"})
    return e


def _fahrzeuge12():
    return [
        {"id": "F1", "kennzeichen": "GU-123EP", "marke": "Mercedes",
         "modell": "Sprinter", "status": "aktiv", "fahrer": "M1",
         "kmStand": 84210, "naechstePickerl": _iso_vor(-40),
         "tankLog": [{"datum": _iso_vor(6), "liter": 62.4, "preis": 108.2,
                      "km": 84100}],
         "schaeden": [{"id": "SD1", "status": "offen",
                       "beschreibung": "Seitenschiebetuer klemmt",
                       "datum": _iso_vor(14)}],
         "serviceheft": [], "verbrauchsmaterial": {}},
        {"id": "F2", "kennzeichen": "GU-777EP", "marke": "VW",
         "modell": "Crafter", "status": "aktiv", "fahrer": "M2",
         "kmStand": 132880, "naechstePickerl": _iso_vor(10),
         "tankLog": [{"datum": _iso_vor(3), "liter": 71.0, "preis": 124.9,
                      "km": 132700}],
         "schaeden": [], "serviceheft": [], "verbrauchsmaterial": {}},
        {"id": "F3", "kennzeichen": "GU-902EP", "marke": "Ford",
         "modell": "Transit", "status": "stillgelegt", "fahrer": "",
         "kmStand": 291400, "naechstePickerl": "",
         "tankLog": [{"datum": _iso_vor(400), "liter": 55.0, "preis": 92.0,
                      "km": 291000}],
         "schaeden": [], "serviceheft": [], "verbrauchsmaterial": {}},
    ]


def _abs12():
    """Abwesenheiten. Der Schluessel ist `<monteurId>_<datum>` (die App
    liest ihn mit `key.startsWith(id+'_')`). M4 hat welche, M5 KEINE."""
    a = {}
    for tag in (_iso_vor(20), _iso_vor(19), _iso_vor(18)):
        a["M1_" + tag] = {"type": "urlaub", "status": "genehmigt",
                          "worker": "M1"}
    a["M2_" + _iso_vor(5)] = {"type": "krank", "status": "genehmigt",
                              "worker": "M2"}
    a["M4_" + _iso_vor(130)] = {"type": "urlaub", "status": "genehmigt",
                                "worker": "M4"}
    return a


def _absApprovals12():
    return [
        {"id": "A1", "worker": "M1", "von": _iso_vor(-10),
         "bis": _iso_vor(-6), "type": "urlaub", "status": "offen",
         "tage": 5, "eingereicht": _iso_vor(2)},
        {"id": "A2", "worker": "M2", "von": _iso_vor(-30),
         "bis": _iso_vor(-28), "type": "zeitausgleich", "status": "offen",
         "tage": 3, "eingereicht": _iso_vor(1)},
    ]


def _stundenzettel12():
    return [
        {"id": "SZ1", "worker": "M1", "monat": "2026-08", "status": "offen",
         "stundenApp": 168.5, "stundenFink": 168.5},
        {"id": "SZ2", "worker": "M2", "monat": "2026-08",
         "status": "freigegeben", "stundenApp": 172.0, "stundenFink": 170.0},
    ]


def _urlaubskontingent12():
    return {"M1": {"jahr": 2026, "anspruch": 25, "verbraucht": 8},
            "M2": {"jahr": 2026, "anspruch": 25, "verbraucht": 12},
            "M3": {"jahr": 2026, "anspruch": 25, "verbraucht": 3}}


def _saat12():
    return {"monteure": MONTEURE,
            "arbeitsscheine": _scheine12(),
            "projects": B.PROJEKTE,
            "entries": _eintraege12(),
            "werkzeuge": B.WERKZEUGE,
            "planData": S._plandaten(),
            "forms": S._formulare(),
            "fahrzeuge": _fahrzeuge12(),
            "abs": _abs12(),
            "absApprovals": _absApprovals12(),
            "stundenzettel": _stundenzettel12(),
            "urlaubskontingent": _urlaubskontingent12()}


# ══════════════════════════════════════════════════════════════════════════
# K14: Ehemalige. Die reinen Funktionen werden NICHT angefasst, nur gelesen.
# ══════════════════════════════════════════════════════════════════════════
KOEDER_EHEMALIG_JS = r"""(liste) => {
  const f = window._maIstEhemalig, w = window._maWaehlbar;
  if (typeof f !== 'function')
    return {ok: false, grund: '_maIstEhemalig ist nicht am window - der '
            + 'Koeder kann nicht schlagen, die Frage ist NICHT gemessen'};
  const urteil = {};
  liste.forEach(m => { urteil[m.id] = !!f(m); });
  let waehlbar = null, waehlbar_mit = null;
  if (typeof w === 'function') {
    waehlbar = w(liste, null).map(m => m.id);
    waehlbar_mit = w(liste, 'M5').map(m => m.id);
  }
  return {ok: true, urteil: urteil, waehlbar: waehlbar,
          waehlbar_mit_getragenem_M5: waehlbar_mit,
          funktionen_da: {ehemalig: true, waehlbar: typeof w === 'function'}};
}"""


# ══════════════════════════════════════════════════════════════════════════
# Navigation in die dreizehn Hauptansichten
# ══════════════════════════════════════════════════════════════════════════
# Unter 600 px: Fussleiste oeffnen ("Mehr"), dort waehlen, Menue SCHLIESSEN
# und das Schliessen belegen. Ueber 600 px: obere Reiterleiste. In BEIDEN
# Faellen wird `.bottom-nav` ausgeschlossen - der Gruppenknopf der Fussleiste
# oeffnet den zuletzt aktiven Reiter SEINER Gruppe und damit die falsche
# Seite.
ANSICHTEN = {
    # Stufe 12
    "chef":       {"nav": "Chef", "titel": "Chef-Dashboard", "stufe": 12},
    "zeit":       {"nav": "Zeiterfassung", "titel": "Zeiterfassung",
                   "stufe": 12},
    "abwesend":   {"nav": "Abwesenheiten", "titel": "Abwesenheiten",
                   "stufe": 12},
    # Stufe 13
    "monatsabr":  {"nav": "Monatsabrechnung", "titel": "Monatsabrechnung",
                   "stufe": 13},
    "fahrzeuge":  {"nav": "Fahrzeuge", "titel": "Fahrzeuge", "stufe": 13},
    "flotte":     {"nav": "Flotte", "titel": "Flotte / Fuhrpark-GPS",
                   "stufe": 13},
    # Stufe 14
    "mitarbeiter": {"nav": "Mitarbeiter", "titel": "Mitarbeiter",
                    "stufe": 14},
    "auswertungen": {"nav": "Auswertungen", "titel": "Auswertungen",
                     "stufe": 14},
    "buero":      {"nav": "Büro-Portal", "titel": "Büro-Portal",
                   "stufe": 14},
    # Stufe 15
    "admin":      {"nav": "Admin", "titel": "Admin", "stufe": 15},
    "einstell":   {"nav": "Einstellungen", "titel": "Einstellungen",
                   "stufe": 15},
    "gefahr":     {"nav": "Gefahrenstoffe", "titel": "Gefahrenstoffe",
                   "stufe": 15},
    "baupro":     {"nav": "Bauprovisorien", "titel": "Bauprovisorien",
                   "stufe": 15},
}

# INHALTLICHE Nachweise. Jeder nennt ein Merkmal, das NUR diese Ansicht hat,
# und - wo Verwechslungsgefahr besteht - die ABWESENHEIT des Nachbarmerkmals.
# Der Klick allein beweist die Seite nicht (Messfehler 4 aus Stufe 4-7).
ANSICHT_DA_JS = r"""(art) => {
  const wz = document.querySelector('.main-pad') || document.getElementById('root');
  const t = ((wz && wz.innerText) || '');
  const h2 = Array.from(document.querySelectorAll('h1,h2,h3'))
    .map(e => (e.textContent || '').replace(/\s+/g, ' ').trim())
    .filter(x => x).slice(0, 4);
  // Jede Marke ist ein Merkmal, das NUR diese Ansicht traegt, und wo zwei
  // Ansichten dieselben Woerter fuehren (Fahrzeuge/Flotte,
  // Admin/Einstellungen, Abwesenheiten/Buero-Portal-Reiter), steht dazu die
  // ABWESENHEIT des Nachbarmerkmals. Alle dreizehn Marken sind aus einem
  // Erkundungslauf an DIESER Datei abgelesen, nicht geraten.
  const M = {
    chef:        [/Chef-Portal/, null],
    zeit:        [/Arbeitsstunden pro Monteur/, /Wochenbericht/],
    abwesend:    [/Urlaubstage, Krankenstand|Urlaubskontingent/,
                  /Büro-Export/],
    monatsabr:   [/Monatszettel aus FinkZeit|Monatsabrechnung/, null],
    fahrzeuge:   [/Fahrzeugverwaltung/, null],
    flotte:      [/Tracker|Fahrtenbuch/, /Fahrzeugverwaltung/],
    mitarbeiter: [/Mitarbeiter & Zuweisungen/, null],
    auswertungen:[/Auswertungen & Dashboards/, null],
    buero:       [/Büro-Export|Bauwochenberichte/, null],
    admin:       [/Administration|Benutzer anlegen\/sperren/,
                  /Supabase-Verbindung/],
    einstell:    [/Supabase-Verbindung|Passwort ändern/, /Administration/],
    gefahr:      [/Sicherheitsdatenblätter/, null],
    baupro:      [/Bauprovisorien/, /Fahrzeugverwaltung/]
  };
  const p = M[art];
  if (!p) return {marke: '?', da: false, ueberschriften: h2};
  const eigen = p[0].test(t) || h2.some(x => p[0].test(x));
  const fremd = p[1] ? (p[1].test(t) || h2.some(x => p[1].test(x))) : false;
  return {marke: String(p[0]) + (p[1] ? ' UND NICHT ' + String(p[1]) : ''),
          da: eigen && !fremd, eigen: eigen, fremd_merkmal: fremd,
          ueberschriften: h2};
}"""

# Inventar: was steht ueberhaupt drin? Fuer den Mengengeruest-Teil und fuer
# die Aufnahme der Ansichten, die der Grundstand NICHT kennt.
INVENTAR_JS = r"""() => {
  const sicht = e => {
    const r = e.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return false;
    const c = getComputedStyle(e);
    return c.visibility !== 'hidden' && c.display !== 'none';
  };
  const raus = e => !!e.closest('.bottom-nav, .top-tabs, #__k_zone, #__kz_zone, #__kb_zone');
  const txt = e => (e.textContent || '').replace(/\s+/g, ' ').trim();
  const wz = document.querySelector('.main-pad') || document.getElementById('root');
  const knoepfe = Array.from((wz || document).querySelectorAll('button, [role="button"]'))
    .filter(sicht).filter(e => !raus(e))
    .map(e => ({t: txt(e).slice(0, 40),
                title: e.getAttribute('title'),
                aria: e.getAttribute('aria-label'),
                h: Math.round(e.getBoundingClientRect().height)}));
  const felder = Array.from((wz || document).querySelectorAll('input:not([type=hidden]), textarea'))
    .filter(sicht).map(e => ({typ: e.type || e.tagName.toLowerCase(),
                              ph: e.getAttribute('placeholder')}));
  const auswahl = Array.from((wz || document).querySelectorAll('select'))
    .filter(sicht).map(e => ({n: e.options.length,
                              opt: Array.from(e.options).map(o => txt(o).slice(0, 28)).slice(0, 14)}));
  const kopf = Array.from((wz || document).querySelectorAll('h1,h2,h3'))
    .filter(sicht).map(e => txt(e).slice(0, 70));
  const thead = Array.from((wz || document).querySelectorAll('th'))
    .filter(sicht).map(e => txt(e).slice(0, 28));
  return {knoepfe: knoepfe, anzahl_knoepfe: knoepfe.length,
          felder: felder, anzahl_felder: felder.length,
          auswahl: auswahl, anzahl_auswahl: auswahl.length,
          ueberschriften: kopf, spalten: thead,
          text_kopf: ((wz && wz.innerText) || '').slice(0, 900)};
}"""

# Bestandsschutz nach BENANNTEN STUECKEN. Verglichen wird nach Abzug aller
# Nicht-Buchstaben (Messfehler N-1: "📋 aufgenommen" ist nicht gleich
# "aufgenommen"), und gesucht wird NUR in Knoepfen/Reitern/Ueberschriften/
# Spaltenkoepfen - NICHT in <option> (Messfehler N-2: die Woerter standen
# auch in Auswahlfeldern, und eine fehlende Kachel waere dadurch
# "vorhanden" gewesen).
MENGEN_BENANNT_JS = r"""(cfg) => {
  const norm = s => (s || '').toLowerCase().replace(/[^a-zäöüß]/g, '');
  const sicht = e => {
    const r = e.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return false;
    const c = getComputedStyle(e);
    return c.visibility !== 'hidden' && c.display !== 'none';
  };
  const wz = document.querySelector('.main-pad') || document.getElementById('root');
  const quellen = Array.from((wz || document)
      .querySelectorAll('button, [role="button"], th, h1, h2, h3, label, a'))
    .filter(sicht)
    .filter(e => !e.closest('.bottom-nav, .top-tabs'))
    .map(e => norm(e.textContent) + '|' + norm(e.getAttribute('title'))
              + '|' + norm(e.getAttribute('aria-label')));
  const erg = {};
  (cfg.stuecke || []).forEach(s => {
    const n = norm(s);
    erg[s] = quellen.some(q => q.indexOf(n) >= 0 && n.length > 2);
  });
  // K15: ein Wort, das es hier mit Sicherheit NICHT gibt. Findet der
  // Zaehler es, zaehlt er nicht, was er behauptet.
  const koeder = norm(cfg.koeder || 'Kalibrierungsintervallpruefung');
  const koeder_gefunden = quellen.some(q => q.indexOf(koeder) >= 0);
  return {treffer: erg,
          da: Object.values(erg).filter(Boolean).length,
          gesamt: (cfg.stuecke || []).length,
          fehlt: Object.keys(erg).filter(k => !erg[k]),
          k15_falschtreffer: koeder_gefunden,
          quellen_gezaehlt: quellen.length};
}"""

# Spezifitaet: welche CSS-Regel schlaegt die 44-px-Hausregel?
# Gemeldet wird nur, was GEMESSEN ist: die Regel, ihr Selektor und die
# ausgerechnete Spezifitaet (a,b,c). `!important` entscheidet nach
# Spezifitaet - zwei !important schlagen sich gegenseitig ueber a,b,c.
SPEZIFITAET_JS = r"""() => {
  const spez = sel => {
    let s = sel.replace(/\[[^\]]*\]/g, '\u0001')
               .replace(/::[a-z-]+/g, '')
               .replace(/:not\(([^)]*)\)/g, '$1');
    const a = (s.match(/#[\w-]+/g) || []).length;
    const b = (s.match(/\.[\w-]+/g) || []).length
            + (s.match(/\u0001/g) || []).length
            + (s.match(/:[a-z-]+/g) || []).length;
    const c = (s.replace(/[#.][\w-]+/g, ' ').replace(/\u0001/g, ' ')
                .match(/\b[a-z][\w-]*/gi) || []).length;
    return [a, b, c];
  };
  const treffer = [];
  for (const bl of Array.from(document.styleSheets)) {
    let regeln;
    try { regeln = bl.cssRules; } catch (e) { continue; }
    if (!regeln) continue;
    const gehe = (liste, medium) => {
      for (const r of Array.from(liste)) {
        if (r.cssRules && r.conditionText !== undefined) {
          gehe(r.cssRules, (medium ? medium + ' && ' : '') + r.conditionText);
          continue;
        }
        if (!r.style || !r.selectorText) continue;
        const txt = r.cssText;
        // Regeln, die Hoehe/Breite/Polster von Bedienelementen setzen
        if (!/\b(min-height|height|min-width|width|padding)\b/.test(txt)) continue;
        if (!/button|\[role|input|select|a\b/.test(r.selectorText)) continue;
        const sp = r.selectorText.split(',').map(x => x.trim());
        sp.forEach(one => {
          const s = spez(one);
          const mh = r.style.getPropertyValue('min-height')
                   || r.style.getPropertyValue('height');
          if (!mh) return;
          treffer.push({selektor: one, spezifitaet: s,
                        medium: medium || null,
                        wert: mh,
                        wichtig: !!(r.style.getPropertyPriority('min-height')
                                 || r.style.getPropertyPriority('height'))});
        });
      }
    };
    gehe(regeln, null);
  }
  return {regeln: treffer, anzahl: treffer.length};
}"""

# Welche Regel gewinnt WIRKLICH an einem zu kleinen Knopf? Nicht geraten,
# sondern am Element nachgefragt.
WER_GEWINNT_JS = r"""() => {
  const sicht = e => {
    const r = e.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return false;
    const c = getComputedStyle(e);
    return c.visibility !== 'hidden' && c.display !== 'none';
  };
  const spez = sel => {
    let s = sel.replace(/\[[^\]]*\]/g, '\u0001').replace(/::[a-z-]+/g, '')
               .replace(/:not\(([^)]*)\)/g, '$1');
    const a = (s.match(/#[\w-]+/g) || []).length;
    const b = (s.match(/\.[\w-]+/g) || []).length
            + (s.match(/\u0001/g) || []).length
            + (s.match(/:[a-z-]+/g) || []).length;
    const c = (s.replace(/[#.][\w-]+/g, ' ').replace(/\u0001/g, ' ')
                .match(/\b[a-z][\w-]*/gi) || []).length;
    return a + ',' + b + ',' + c;
  };
  const passt = (e, sel) => {
    try { return e.matches(sel); } catch (x) { return false; }
  };
  const klein = Array.from(document.querySelectorAll('button, [role="button"]'))
    .filter(sicht)
    .filter(e => !e.closest('.bottom-nav, .top-tabs, #__k_zone, #__kz_zone, #__kb_zone'))
    .filter(e => { const r = e.getBoundingClientRect();
                   return r.height < 44 || r.width < 44; });
  const erg = [];
  klein.slice(0, 14).forEach(e => {
    const r = e.getBoundingClientRect();
    const kandidaten = [];
    for (const bl of Array.from(document.styleSheets)) {
      let regeln; try { regeln = bl.cssRules; } catch (x) { continue; }
      if (!regeln) continue;
      const gehe = (liste, medium) => {
        for (const rr of Array.from(liste)) {
          if (rr.cssRules && rr.conditionText !== undefined) {
            let gilt = true;
            try { gilt = window.matchMedia(rr.conditionText).matches; }
            catch (x) { gilt = true; }
            if (gilt) gehe(rr.cssRules, rr.conditionText);
            continue;
          }
          if (!rr.style || !rr.selectorText) continue;
          const mh = rr.style.getPropertyValue('min-height')
                   || rr.style.getPropertyValue('height');
          if (!mh) continue;
          rr.selectorText.split(',').map(x => x.trim()).forEach(one => {
            if (!passt(e, one)) return;
            kandidaten.push({sel: one, spez: spez(one), wert: mh,
                             medium: medium || null,
                             wichtig: !!(rr.style.getPropertyPriority('min-height')
                                      || rr.style.getPropertyPriority('height'))});
          });
        }
      };
      gehe(regeln, null);
    }
    erg.push({text: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 26),
              h: Math.round(r.height), w: Math.round(r.width),
              inline_h: e.style.height || e.style.minHeight || null,
              regeln: kandidaten});
  });
  return {anzahl_klein: klein.length, proben: erg};
}"""

# Stufe 14, Sonderauftrag: die gerenderten Diagramme mit ihren Balken.
# Die Diagrammkarten tragen ihren Titel in einem Element; die Balken tragen
# Beschriftung und Wert. Gesucht wird ueber den TITEL (er steht im Quelltext
# als `charts[].title`), nicht ueber eine Bauform.
CHARTS_JS = r"""(titel) => {
  const sicht = e => {
    const r = e.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return false;
    const c = getComputedStyle(e);
    return c.visibility !== 'hidden' && c.display !== 'none';
  };
  const txt = e => (e.textContent || '').replace(/\s+/g, ' ').trim();
  const alle = [];
  titel.forEach(ti => {
    // Der kleinste sichtbare Behaelter, der den Titel UND mindestens einen
    // weiteren Text enthaelt - das ist die Diagrammkarte.
    const k = Array.from(document.querySelectorAll('div'))
      .filter(sicht)
      .filter(e => txt(e).indexOf(ti) >= 0);
    if (!k.length) { alle.push({titel: ti, da: false}); return; }
    k.sort((a, b) => txt(a).length - txt(b).length);
    const karte = k[0];
    const ganz = txt(karte);
    alle.push({titel: ti, da: true, inhalt: ganz.slice(0, 500),
               hoehe: Math.round(karte.getBoundingClientRect().height)});
  });
  return {karten: alle,
          gefunden: alle.filter(x => x.da).length,
          gesucht: titel.length};
}"""

# Welche Namen erscheinen ueberhaupt im Bild?
# EIGENER MESSFEHLER, hier behoben: die erste Fassung las NUR `innerText`.
# SVG-`<text>` steht dort NICHT drin - und die Diagramme dieser App sind SVG.
# Alle fuenf Namen galten in den Auswertungen als "nicht im Bild", obwohl
# sie als Balkenbeschriftung dastanden. Das waere eine saubere, falsche Null
# im Kernpunkt des Auftrags gewesen. Gelesen wird jetzt BEIDES, und die
# Antwort sagt, in welchem der beiden der Name steht.
NAMEN_IM_BILD_JS = r"""(namen) => {
  const wz = document.querySelector('.main-pad') || document.getElementById('root');
  const t = ((wz && wz.innerText) || '');
  const tc = ((wz && wz.textContent) || '');
  const svgTexte = Array.from((wz || document).querySelectorAll('svg text'))
    .map(e => (e.textContent || '').trim()).filter(x => x);
  const erg = {};
  namen.forEach(n => {
    const i = t.indexOf(n);
    const j = tc.indexOf(n);
    // Die Balkenbeschriftung wird bei 14 Zeichen gekappt
    // (`lbl.slice(0,maxChars)+"…"` in SvgHBar) - der GANZE Name steht dort
    // also nie. Deshalb wird auch der gekappte Anfang gesucht.
    const kurz = n.slice(0, 14);
    const imSvg = svgTexte.filter(x => x === n || x === kurz + '…'
                                    || x.indexOf(kurz) === 0);
    erg[n] = {da: i >= 0 || j >= 0 || imSvg.length > 0,
              in_innertext: i >= 0, in_textcontent: j >= 0, in_svg: imSvg,
              umgebung: i >= 0 ? t.slice(Math.max(0, i - 70), i + 90)
                                   .replace(/\n/g, ' ⏎ ')
                       : (j >= 0 ? tc.slice(Math.max(0, j - 70), j + 90)
                                 : null)};
  });
  return erg;
}"""

# Die Diagrammkarten mit ihren BALKEN. Eine Karte ist der kleinste sichtbare
# Behaelter, der den Titel UND ein `<svg>` fuehrt - der Titel allein ist nur
# seine eigene Zeile, und genau die hat die erste Fassung zurueckgegeben
# ("Inhalt: 'Scheine pro Monteur'" und sonst nichts).
CHART_SVG_JS = r"""(titel) => {
  const sicht = e => {
    const r = e.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return false;
    const c = getComputedStyle(e);
    return c.visibility !== 'hidden' && c.display !== 'none';
  };
  const txt = e => (e.textContent || '').replace(/\s+/g, ' ').trim();
  const alle = [];
  titel.forEach(ti => {
    const k = Array.from(document.querySelectorAll('div'))
      .filter(sicht)
      .filter(e => txt(e).indexOf(ti) >= 0 && e.querySelector('svg'));
    if (!k.length) { alle.push({titel: ti, da: false, svg: false}); return; }
    k.sort((a, b) => txt(a).length - txt(b).length);
    const karte = k[0];
    const svg = karte.querySelector('svg');
    const zeilen = Array.from(svg.querySelectorAll('text')).map(e => ({
      t: txt(e),
      px: Math.round(parseFloat(getComputedStyle(e).fontSize) * 10) / 10}));
    alle.push({titel: ti, da: true, svg: true, zeilen: zeilen,
               anzahl_zeilen: zeilen.length,
               leer_hinweis: /Keine Daten/i.test(txt(karte)),
               hoehe: Math.round(karte.getBoundingClientRect().height)});
  });
  return {karten: alle, gefunden: alle.filter(x => x.da).length,
          gesucht: titel.length};
}"""

# Zuweisungs-Auswahl gegen Filter-Auswahl: steht M5 (ausgetreten, ohne
# Beitrag) in einem <select>, und in welchem?
SELECTS_JS = r"""(name) => {
  const sicht = e => {
    const r = e.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return false;
    const c = getComputedStyle(e);
    return c.visibility !== 'hidden' && c.display !== 'none';
  };
  const erg = [];
  Array.from(document.querySelectorAll('select')).filter(sicht).forEach(s => {
    const opt = Array.from(s.options).map(o => (o.textContent || '').trim());
    erg.push({n: opt.length,
              hat_namen: opt.some(o => o.indexOf(name) >= 0),
              erste: opt.slice(0, 8),
              label: (s.getAttribute('aria-label') || s.getAttribute('title')
                      || (s.previousElementSibling
                          && (s.previousElementSibling.textContent || '').trim())
                      || '').slice(0, 40)});
  });
  return {auswahlfelder: erg, anzahl: erg.length,
          mit_namen: erg.filter(x => x.hat_namen).length};
}"""


# ══════════════════════════════════════════════════════════════════════════
# Lauf
# ══════════════════════════════════════════════════════════════════════════
# Bestandsschutz: die BENANNTEN Stuecke aus docs/GRUNDSTAND_UI_v3.9.930.md.
# Was hier NICHT steht, kennt der Grundstand nicht - diese Ansichten werden
# als NEU und NICHT ABGENOMMEN aufgenommen.
GRUNDSTAND = {}   # wird in main() aus der Doku gefuellt/geprueft


def _saeen12(seite):
    daten = _saat12()
    erg = seite.evaluate(S.SEED2_JS, {"db": M.DB_NAME, "daten": daten})
    if erg.get("fehlend"):
        print("   HINWEIS: diese Speicher gibt es nicht: %s"
              % ", ".join(erg["fehlend"]))
    for k, v in sorted(erg.get("gelesen", {}).items()):
        print("   zurueckgelesen  %-18s %s" % (k, v))
    schlecht = [k for k, v in erg["gelesen"].items()
                if str(v) in ("array:0", "FEHLT", "LESEFEHLER")
                or str(v).startswith("leer")]
    if schlecht:
        raise SystemExit("ABBRUCH: die Saat ist nicht angekommen (%s)."
                         % ", ".join(schlecht))
    seite.evaluate("() => { try { localStorage.setItem("
                   "'epk_last_juprowa_pull', String(Date.now())); } "
                   "catch(e){} }")
    seite.reload(wait_until="domcontentloaded")
    seite.wait_for_timeout(6800)
    t = seite.evaluate("() => document.body.innerText")
    treffer = len(B.SAATWORT.findall(t or ""))
    print("   K6 Saat in der Ansicht sichtbar: %d Treffer" % treffer)
    if not treffer:
        raise SystemExit("ABBRUCH (K6): die Saat liegt in der Datenbank, "
                         "erscheint aber in KEINER Ansicht.")
    return treffer


def _navigieren12(seite, kuerzel, breite, protokoll):
    ziel = ANSICHTEN[kuerzel]["nav"]
    if breite < 600:
        seite.evaluate(M.NAV_OEFFNEN_JS)
        seite.wait_for_timeout(450)
        weg = seite.evaluate(B.NAV_MEHR_JS, ziel)
        seite.wait_for_timeout(2600)
        zu = seite.evaluate(B.MEHR_ZU_JS)
        seite.wait_for_timeout(700)
        rest = seite.evaluate(B.MEHR_OFFEN_JS)
        if rest:
            protokoll.append("Mehr-Menue noch offen (%d) - Verdeckungs- und "
                             "Tippzielzahlen dieses Laufs sind NICHT "
                             "belastbar" % rest)
        print("   Mehr-Menue: %s" % zu)
    else:
        weg = seite.evaluate(B.NAV_TOP_JS, ziel)
        seite.wait_for_timeout(2600)
    return weg


def _messen(seite, d, kuerzel):
    """Die sieben Regeln plus die drei aus Stufe 8-11."""
    d["schrift"] = seite.evaluate(B.SCHRIFT_JS)
    d["tipp"] = seite.evaluate(B.TIPP_JS)
    d["emoji"] = seite.evaluate(B.EMOJI_JS)
    d["emoji_zahl"] = seite.evaluate(S.EMOJI_ZAHL_JS)
    d["quer"] = seite.evaluate(B.QUER_JS)
    d["beschnitt"] = seite.evaluate(B.BESCHNITT_JS)
    d["beschnitt_echt"] = seite.evaluate(S.BESCHNITT_ECHT_JS)
    d["tabellen"] = seite.evaluate(B.TABELLE_JS)
    d["mengen"] = seite.evaluate(B.MENGEN_JS)
    d["inventar"] = seite.evaluate(INVENTAR_JS)
    return d


def _lauf(pw, url, kuerzel, breite, hoehe, thema="dark", erkunden=False):
    marke = "%s @ %dx%d %s" % (kuerzel, breite, hoehe, thema)
    print("\n── %s ─────────────────────────────" % marke)
    d = {"ansicht": kuerzel, "stufe": ANSICHTEN[kuerzel]["stufe"],
         "titel": ANSICHTEN[kuerzel]["titel"],
         "breite": breite, "hoehe": hoehe, "thema": thema}
    offen, fehler, protokoll = [], [], []
    ctx = pw.new_context(viewport={"width": breite, "height": hoehe},
                         is_mobile=breite < 600, has_touch=breite < 600,
                         device_scale_factor=2 if breite < 600 else 1,
                         color_scheme="dark")
    ctx.add_init_script(M.INIT)
    ctx.add_init_script(
        "try{var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
        "u.monteurId='M1';u.name='Gerhard Steinbichler';u.role='admin';"
        "u.rolle='Geschaeftsfuehrer';"
        "localStorage.setItem('epkolar_user',JSON.stringify(u));"
        "localStorage.setItem('epk_theme','%s');}catch(e){}" % thema)
    ctx.route("**/rest/v1/**", lambda r: r.abort())
    ctx.route("**/auth/v1/**", lambda r: r.abort())
    seite = ctx.new_page()
    seite.on("pageerror", lambda x: fehler.append(str(x)[:170]))
    try:
        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(3800)
        _saeen12(seite)
        # K14 vor der Navigation - die Funktionen haengen am window.
        k14 = seite.evaluate(KOEDER_EHEMALIG_JS, MONTEURE)
        d["k14"] = k14
        erwartet = {"M1": False, "M2": False, "M3": False,
                    "M4": True, "M5": True}
        k14ok = bool(k14.get("ok")) and k14.get("urteil") == erwartet
        w = k14.get("waehlbar") or []
        k14ok = k14ok and ("M5" not in w) and ("M1" in w)
        k14ok = k14ok and ("M5" in (k14.get("waehlbar_mit_getragenem_M5") or []))
        print("   K14 Ehemalige  %s  (Urteil %s | _maWaehlbar ohne M5: %s | "
              "mit getragenem M5: %s)"
              % ("ANGESCHLAGEN" if k14ok else "STUMM", k14.get("urteil"),
                 w, k14.get("waehlbar_mit_getragenem_M5")))
        if not k14ok:
            offen.append("%s: K14 - _maIstEhemalig/_maWaehlbar haben nicht "
                         "das erwartete Urteil geliefert (%s). Die Frage "
                         "'Ehemalige nur mit Beitrag' ist in diesem Lauf "
                         "NICHT gemessen." % (marke, k14))

        weg = _navigieren12(seite, kuerzel, breite, protokoll)
        print("   Navigation: %s" % weg)
        if weg in (None, "nicht-gefunden"):
            d["nicht_erreichbar"] = True
            offen.append("%s: Ansicht nicht erreichbar (%s) - das ist KEIN "
                         "bestandener Fall." % (marke, weg))
            ctx.close()
            return d, offen, fehler
        nw = seite.evaluate(ANSICHT_DA_JS, kuerzel)
        d["nachweis"] = nw
        print("   Ansicht belegt: %s  (Ueberschriften: %s)"
              % (nw["da"], nw.get("ueberschriften")))
        if not nw["da"]:
            d["nicht_erreichbar"] = True
            d["inventar"] = seite.evaluate(INVENTAR_JS)
            print("   WAS STATT DESSEN DA IST: %d Knoepfe, Text %r"
                  % (d["inventar"]["anzahl_knoepfe"],
                     d["inventar"]["text_kopf"][:500]))
            offen.append("%s: INHALTLICHER Nachweis fehlgeschlagen (%s) - der "
                         "Klick allein beweist die Seite nicht." % (marke, nw))
            ctx.close()
            return d, offen, fehler

        if erkunden:
            d["inventar"] = seite.evaluate(INVENTAR_JS)
            print("   Inventar: %d Knoepfe / %d Felder / %d Auswahlfelder"
                  % (d["inventar"]["anzahl_knoepfe"],
                     d["inventar"]["anzahl_felder"],
                     d["inventar"]["anzahl_auswahl"]))
            print("   Ueberschriften: %s" % d["inventar"]["ueberschriften"][:6])
            print("   Knopftexte: %s"
                  % [k["t"] for k in d["inventar"]["knoepfe"][:40]])
            print("   Spalten: %s" % d["inventar"]["spalten"][:20])
            print("   Text: %r" % d["inventar"]["text_kopf"][:600])
            ctx.close()
            return d, offen, fehler

        if thema == "light":
            d["dunkel"] = seite.evaluate(S.DUNKEL_JS)
            seite.evaluate(B.BIS_UNTEN_JS)
            seite.wait_for_timeout(1100)
            d["dunkel_gerollt"] = seite.evaluate(S.DUNKEL_JS)
            for wo, dd in (("oben", d["dunkel"]),
                           ("gerollt", d["dunkel_gerollt"])):
                print("   Hellmodus %-8s %d dunkle Flaechen ab 8000 px2, "
                      "tragend (>=25 %% Schirm): %d | feste dunkle Farben "
                      "im Bild: %d   Huelle %s"
                      % (wo, dd["anzahl"], len(dd["tragend"]),
                         dd["anzahl_feste"], dd["huelle"]))
                for g in dd["dunkel"][:4]:
                    print("      %-26s %s  H=%.3f  %dx%d  %.1f %% des Schirms"
                          % ((g["tag"] + "." + g["klasse"])[:26], g["farbe"],
                             g["helligkeit"], g["breit"], g["hoch"],
                             g["anteil"] * 100))
                for f in dd["feste_farben"][:8]:
                    print("      FEST %s  %-18s %dx%d = %.1f %% des Schirms, "
                          "sichtbar=%s"
                          % (f["farbe"], (f["tag"] + "." + f["klasse"])[:18],
                             f["breit"], f["hoch"], f["anteil"] * 100,
                             f["sichtbar"]))
            ziel = os.path.join(WURZEL, "screenshots")
            os.makedirs(ziel, exist_ok=True)
            seite.screenshot(path=os.path.join(
                ziel, "b3_%s_%d_hell.png" % (kuerzel, breite)))
            d["seitenfehler"] = [f for f in fehler
                                 if not any(w.lower() in f.lower()
                                            for w in M.IGNORIEREN)][:5]
            ctx.close()
            return d, offen, fehler

        # ── K1-K8 ──────────────────────────────────────────────────────
        d["querrollen_selbstprobe"] = {}
        d["koeder_ok"] = B._koeder(seite, marke, offen,
                                   d["querrollen_selbstprobe"])
        # ── K9 ─────────────────────────────────────────────────────────
        kb = seite.evaluate(S.KOEDER_BESCH2_EIN)
        be = seite.evaluate(S.BESCHNITT_ECHT_JS)
        hart = [x for x in be["gekuerzt"] if x["text"].startswith("HART")]
        weich = [x for x in be["nur_ueberlauf"] if x["text"].startswith("WEICH")]
        falsch = ([x for x in be["nur_ueberlauf"] if x["text"].startswith("HART")]
                  + [x for x in be["gekuerzt"] if x["text"].startswith("WEICH")])
        k9 = bool(hart) and bool(weich) and not falsch
        print("   K9 Beschnitt   %s  (hart %s/%s; weich %s/%s; falsch "
              "eingeordnet: %d)"
              % ("ANGESCHLAGEN" if k9 else "STUMM",
                 kb["hart"]["scroll"], kb["hart"]["sicht"],
                 kb["weich"]["scroll"], kb["weich"]["sicht"], len(falsch)))
        if not k9:
            offen.append("%s: K9 hat nicht angeschlagen - gekuerzt gegen "
                         "nur-ueberlaufen ist NICHT gemessen." % marke)
        seite.evaluate(S.KOEDER_BESCH2_AUS)
        seite.wait_for_timeout(250)

        # ── K13 ────────────────────────────────────────────────────────
        seite.evaluate(S.KOEDER_EMOJIZAHL_EIN)
        alt = seite.evaluate(B.EMOJI_JS)
        neu = seite.evaluate(S.EMOJI_ZAHL_JS)
        alt_hat = any(x["zeichen"] == "\U0001f529" + "7"
                      for x in alt["ohne_hilfe"])
        neu_hat = any(x["zeichen"] == "\U0001f529" + "7"
                      for x in neu["ohne_hilfe"])
        k13 = neu_hat and not alt_hat
        print("   K13 Symbol+Zahl %s (alt %s / neu %s)"
              % ("ANGESCHLAGEN" if k13 else "STUMM", alt_hat, neu_hat))
        if not k13:
            offen.append("%s: K13 - 'nur Symbol + Zahl' ist NICHT gemessen "
                         "(alt=%s neu=%s)." % (marke, alt_hat, neu_hat))
        seite.evaluate(S.KOEDER_EMOJIZAHL_AUS)
        seite.wait_for_timeout(200)

        # ── K12 ────────────────────────────────────────────────────────
        d["dunkel_dunkelmodus"] = seite.evaluate(S.DUNKEL_JS)
        k12 = len(d["dunkel_dunkelmodus"]["tragend"]) > 0
        print("   K12 Flaeche     %s  (%d dunkle, %d tragend, Huelle %s)"
              % ("ANGESCHLAGEN" if k12 else "STUMM",
                 d["dunkel_dunkelmodus"]["anzahl"],
                 len(d["dunkel_dunkelmodus"]["tragend"]),
                 d["dunkel_dunkelmodus"]["huelle"]))
        if not k12:
            offen.append("%s: K12 - der Flaechenmelder sieht keine Farbe; "
                         "die Hellmodus-Aussage dieser Ansicht ist NICHT "
                         "gemessen." % marke)

        # ── Die Regeln ─────────────────────────────────────────────────
        _messen(seite, d, kuerzel)
        d["verdeckung_oben"] = seite.evaluate(B.VERDECKUNG_JS)
        d["wer_gewinnt"] = seite.evaluate(WER_GEWINNT_JS)

        # ── Bestandsschutz, nach BENANNTEN Stuecken ────────────────────
        stuecke = GRUNDSTAND.get(kuerzel)
        if stuecke:
            bs = seite.evaluate(MENGEN_BENANNT_JS,
                                {"stuecke": stuecke,
                                 "koeder": "Kalibrierungsintervallpruefung"})
            d["bestand"] = bs
            print("   BESTANDSSCHUTZ  %d/%d benannte Stuecke%s   "
                  "(K15 Falschtreffer: %s, %d Quellen)"
                  % (bs["da"], bs["gesamt"],
                     ("  FEHLT: %s" % bs["fehlt"]) if bs["fehlt"] else "",
                     bs["k15_falschtreffer"], bs["quellen_gezaehlt"]))
            if bs["k15_falschtreffer"]:
                offen.append("%s: K15 - der Bestandsschutz-Zaehler findet ein "
                             "Wort, das es nicht gibt. Er zaehlt nicht, was "
                             "er behauptet; das Mengengeruest dieser Ansicht "
                             "ist NICHT gemessen." % marke)
        else:
            d["bestand"] = {"hinweis": "GRUNDSTAND kennt diese Ansicht nicht "
                                       "- IST-Aufnahme ist NEU und NICHT "
                                       "ABGENOMMEN"}

        # ── Stufe 14: die Diagramme ────────────────────────────────────
        if kuerzel == "auswertungen":
            d["charts"] = seite.evaluate(CHART_SVG_JS, CHART_TITEL)
            d["namen"] = seite.evaluate(NAMEN_IM_BILD_JS,
                                        [m["n"] for m in MONTEURE])
            d["selects"] = seite.evaluate(SELECTS_JS, "Puchleitner")
            print("   DIAGRAMME: %d von %d Karten mit SVG gefunden"
                  % (d["charts"]["gefunden"], d["charts"]["gesucht"]))
            for k in d["charts"]["karten"]:
                print("      %-34s %s  %d SVG-Zeilen  %s"
                      % (k["titel"], k["da"], k.get("anzahl_zeilen") or 0,
                         [(z["t"], z["px"])
                          for z in (k.get("zeilen") or [])][:24]))
            # K16: der Melder MUSS mindestens einen Namen im SVG finden.
            # Findet er keinen, misst er die Frage dieses Auftrags nicht.
            k16 = any(v["in_svg"] for v in d["namen"].values())
            print("   K16 Namen im SVG %s"
                  % ("ANGESCHLAGEN" if k16 else "STUMM"))
            if not k16:
                offen.append("%s: K16 - in KEINEM Diagramm steht ein "
                             "Monteursname als SVG-Text. Die Frage "
                             "'erscheinen Ausgetretene mit Null' ist damit "
                             "NICHT gemessen." % marke)
            for n, v in d["namen"].items():
                print("      Name %-32s im Bild: %s (innerText %s, SVG %s)"
                      % (n, v["da"], v["in_innertext"], v["in_svg"]))
        # Ehemalige: in JEDER Ansicht, nicht nur in den vermuteten. Eine
        # Ansicht, in der man NICHT nachgesehen hat, ist kein Nachweis.
        if kuerzel != "auswertungen":
            d["namen"] = seite.evaluate(NAMEN_IM_BILD_JS,
                                        [m["n"] for m in MONTEURE])
            d["selects"] = seite.evaluate(SELECTS_JS, "Puchleitner")
        print("   Ausgetretene im Bild: M4(mit Beitrag)=%s  "
              "M5(ohne Beitrag)=%s | Auswahlfelder mit M5: %d von %d"
              % (d["namen"]["Ferdinand Aschenbrenner"]["da"],
                 d["namen"]["Roswitha Puchleitner"]["da"],
                 d["selects"]["mit_namen"], d["selects"]["anzahl"]))
        for n in ("Ferdinand Aschenbrenner", "Roswitha Puchleitner"):
            if d["namen"][n]["da"]:
                print("      %-24s steht bei: %r"
                      % (n, (d["namen"][n]["umgebung"] or "")[:150]))

        seite.evaluate(B.BIS_UNTEN_JS)
        seite.wait_for_timeout(900)
        d["roller"] = seite.evaluate(B.BIS_UNTEN_JS)
        seite.wait_for_timeout(700)
        d["verdeckung_unten"] = seite.evaluate(B.VERDECKUNG_JS)
        print("   Roller bis ans Ende: %s" % [
            "%s %d/%d %s" % (r["weg"], r["oben"], r["hoehe"],
                             "am Ende" if r["am_ende"] else "NICHT am Ende")
            for r in d["roller"]["roller"]])
        ziel = os.path.join(WURZEL, "screenshots")
        os.makedirs(ziel, exist_ok=True)
        seite.screenshot(path=os.path.join(
            ziel, "b3_%s_%d.png" % (kuerzel, breite)))
    finally:
        echte = [f for f in fehler
                 if not any(w.lower() in f.lower() for w in M.IGNORIEREN)]
        d["seitenfehler"] = echte[:5]
        d["protokoll"] = protokoll
        ctx.close()

    if d.get("nicht_erreichbar") or erkunden or thema == "light":
        return d, offen, fehler
    print("   Schrift < 12 px: %d von %d gemessenen Textstellen"
          % (d["schrift"]["anzahl_klein"], d["schrift"]["gemessen"]))
    print("   kleinste Werte: %s" % d["schrift"].get("kleinste", [])[:6])
    print("   Tippziele (Knoepfe) < 44 px: %d   |   Felder/Beschriftungen "
          "< 44 px: %d (getrennt, KEIN Knopfbefund)"
          % (d["tipp"]["anzahl_klein"], d["tipp"]["anzahl_felder_klein"]))
    print("   nur-Symbol ohne title/aria: %d  (mit: %d)"
          % (d["emoji"]["anzahl_ohne"], d["emoji"]["anzahl_mit"]))
    ez = d["emoji_zahl"]
    print("   OHNE BUCHSTABEN ohne title/aria: %d, davon nur Symbol+Zaehler: "
          "%d   ->   %s"
          % (ez["anzahl_ohne"], ez["nur_mit_zaehler"],
             [x["zeichen"] for x in ez["ohne_hilfe"][:10]]))
    print("   quer, Regelwortlaut: %s gegen %s -> %s"
          % (d["quer"]["scrollWidth"], d["quer"]["innerWidth"],
             "ROLLT" if d["quer"]["rollt"] else "rollt nicht"))
    for r in d["quer"]["waagrechte_roller"]:
        bk = r["breitestes_kind"] or {}
        print("   quer, TATSAECHLICH: %s rollt %s px quer (%s von %s), "
              "breitestes Kind %s px: %s"
              % (r["weg"], r["ueberschuss"], r["clientWidth"],
                 r["scrollWidth"], bk.get("breite"),
                 (bk.get("text") or bk.get("weg") or "")[:46]))
    if not d["quer"]["waagrechte_roller"]:
        print("   quer, TATSAECHLICH: kein waagrechter Roller ueberhaupt")
    be = d["beschnitt_echt"]
    print("   Beschnitt: %d WIRKLICH gekuerzt | %d nur Kastenueberlauf "
          "(nichts verloren) | %d in gewollt rollbaren Behaeltern"
          % (be["anzahl_gekuerzt"], be["anzahl_nur_ueberlauf"],
             be["anzahl_rollbar"]))
    for x in be["gekuerzt"][:8]:
        print("      %5s px verloren an %-28s  %r"
              % (x["verloren_px"], x["verloren_an"][:28], x["text"][:40]))
    vu = d["verdeckung_unten"]
    print("   Verdeckung am Ende: %s"
          % (vu.get("hinweis") or "%d Bedienelemente in der Leistenzone "
             "(%s, Ueberstand %s px)"
             % (vu.get("anzahl", -1), vu.get("leiste"), vu.get("ueberstand"))))
    print("   Tabellen: %d, davon breiter als der Schirm: %d"
          % (len(d["tabellen"]), sum(1 for t in d["tabellen"] if t["ueber"])))
    for t in d["tabellen"]:
        if t["ueber"]:
            print("      Tabelle %s von %s, breiteste Spalte: %s"
                  % (t.get("breite"), t.get("innerWidth"),
                     t.get("breiteste_spalte")))
    print("   Mengen: %d Knoepfe, %d Felder, %d Auswahlfelder"
          % (d["mengen"]["knoepfe"], d["mengen"]["felder"],
             d["mengen"]["auswahl"]))
    wg = d.get("wer_gewinnt") or {}
    if wg.get("anzahl_klein"):
        print("   zu kleine Bedienelemente: %d; die Regeln, die an den "
              "ersten greifen:" % wg["anzahl_klein"])
        for p in wg["proben"][:6]:
            print("      %-26r %dx%d inline=%s  %s"
                  % (p["text"], p["w"], p["h"], p["inline_h"],
                     [(r["sel"], r["spez"], r["wert"],
                       "!" if r["wichtig"] else "") for r in p["regeln"][:4]]))
    return d, offen, fehler


CHART_TITEL = [
    "Arbeitsscheine nach Status", "Arbeitsscheine nach Art",
    "Scheine pro Monteur", "Projekte Status", "Projektfortschritt (aktiv)",
    "Abwesenheiten nach Typ", "Abwesenheit pro Person",
    "Werkzeuge nach Status", "Werkzeuge nach Kategorie",
    "Werkzeugwert (€) pro Kategorie", "Stunden letzte 7 Tage",
    "Tankkosten pro Fahrzeug (€)", "Liter pro Fahrzeug",
    "km-Stand Fahrzeuge", "Offene Schäden pro Fahrzeug",
]


def main(argv):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt.")
        return 2
    nur = argv[argv.index("--nur") + 1] if "--nur" in argv else None
    ziel_json = argv[argv.index("--json") + 1] if "--json" in argv else None
    nur_hell = "--hell" in argv
    nur_dunkel = "--dunkel" in argv
    erkunden = "--erkunden" in argv

    datei = os.environ.get("EPK_INDEX", "index.html")
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port, datei)
    print("Gemessen wird: %s" % url)
    import hashlib
    h = hashlib.md5(io.open(os.path.join(WURZEL, datei), "rb").read()).hexdigest()
    print("md5 der gemessenen Datei: %s" % h)

    # Bestandsschutz aus der Doku holen - NICHT abtippen.
    _grundstand_lesen()

    alles, offen = [], []
    listen = [nur] if nur else list(ANSICHTEN)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for kuerzel in listen:
            for breite, hoehe in BREITEN:
                if erkunden:
                    dd, o, _ = _lauf(browser, url, kuerzel, breite, hoehe,
                                     "dark", True)
                    alles.append(dd)
                    offen += o
                    continue
                if not nur_hell:
                    dd, o, _ = _lauf(browser, url, kuerzel, breite, hoehe,
                                     "dark")
                    alles.append(dd)
                    offen += o
                if not nur_dunkel:
                    dd, o, _ = _lauf(browser, url, kuerzel, breite, hoehe,
                                     "light")
                    alles.append(dd)
                    offen += o
        browser.close()

    if ziel_json:
        io.open(ziel_json, "w", encoding="utf-8", newline="\n").write(
            json.dumps({"md5": h, "datei": datei, "laeufe": alles,
                        "offen": offen}, indent=1, ensure_ascii=False))
        print("\nJSON: %s" % ziel_json)

    print("\n" + "=" * 78)
    print("ZUSAMMENFASSUNG")
    print("=" * 78)
    for d in alles:
        if d.get("nicht_erreichbar"):
            print("  %-13s %5d %-5s NICHT ERREICHBAR" % (d["ansicht"],
                                                         d["breite"],
                                                         d["thema"]))
            continue
        if erkunden:
            iv = d.get("inventar") or {}
            print("  %-13s %5d  %3d Knoepfe / %2d Felder / %2d Auswahl | %s"
                  % (d["ansicht"], d["breite"], iv.get("anzahl_knoepfe", -1),
                     iv.get("anzahl_felder", -1), iv.get("anzahl_auswahl", -1),
                     (iv.get("ueberschriften") or [""])[0][:44]))
            continue
        if d["thema"] == "light":
            print("  %-13s %5d hell   dunkle Flaechen %2d, tragend %d, feste "
                  "Farben %d"
                  % (d["ansicht"], d["breite"], d["dunkel"]["anzahl"],
                     len(d["dunkel"]["tragend"]),
                     d["dunkel"]["anzahl_feste"]))
            continue
        vu = d["verdeckung_unten"]
        print("  %-13s %5d dunkel Schrift<12 %3d/%3d | Tipp<44 %3d | "
              "Symbol %2d/%2d | quer %-9s | gekuerzt %2d | ueberlauf %2d | "
              "verdeckt %s | Tab>Schirm %d"
              % (d["ansicht"], d["breite"], d["schrift"]["anzahl_klein"],
                 d["schrift"]["gemessen"], d["tipp"]["anzahl_klein"],
                 d["emoji"]["anzahl_ohne"], d["emoji_zahl"]["anzahl_ohne"],
                 ("%d>%d" % (d["quer"]["scrollWidth"], d["quer"]["innerWidth"]))
                 if d["quer"]["rollt"] else "nein",
                 d["beschnitt_echt"]["anzahl_gekuerzt"],
                 d["beschnitt_echt"]["anzahl_nur_ueberlauf"],
                 ("-" if vu.get("leiste") is None else vu.get("anzahl")),
                 sum(1 for t in d["tabellen"] if t["ueber"])))
    if offen:
        print("\nNICHT GEMESSEN (das sind KEINE bestandenen Faelle):")
        for z in offen:
            print("   " + z)
        return 1
    print("\nAlle Koeder haben angeschlagen - die Zahlen oben sind Messwerte.")
    return 0


def _grundstand_lesen():
    """Die BENANNTEN Stuecke aus docs/GRUNDSTAND_UI_v3.9.930.md.

    Es wird NICHT abgetippt: die Abschnitte werden aus der Datei gelesen.
    Steht dort nichts zu einer Ansicht, bleibt sie leer - und der Bericht
    sagt dann ausdruecklich "NEU, nicht abgenommen".
    """
    pfad = os.path.join(WURZEL, "docs", "GRUNDSTAND_UI_v3.9.930.md")
    if not os.path.exists(pfad):
        print("HINWEIS: %s gibt es nicht - Bestandsschutz entfaellt." % pfad)
        return
    txt = io.open(pfad, encoding="utf-8", newline="").read()
    GRUNDSTAND.update(_grundstand_zerlegen(txt))
    for k, v in sorted(GRUNDSTAND.items()):
        print("   Grundstand %-13s %d benannte Stuecke" % (k, len(v)))


def _grundstand_zerlegen(txt):
    """Aus dem Grundstand die benannten Knopf-/Reiter-Woerter je Ansicht.

    Gesucht wird in den Abschnitten zu Mitarbeiter, Fahrzeuge und
    Abwesenheiten nach in Backticks oder Anfuehrungszeichen gesetzten
    Stuecken. Die ROHEN Knopfzahlen des Grundstands werden bewusst NICHT
    verglichen (die Zaehlvorschrift ist nirgends festgelegt, und der
    Datenbestand ist ein anderer).
    """
    import re
    erg = {}
    # Die drei Abschnitte, die der Grundstand fuer DIESE Stufen fuehrt.
    # Ueberschrift ist `## <Name> (<n> Knoepfe…)`; darunter stehen die
    # benannten Stuecke, durch `·` getrennt. Gelesen wird der erste Absatz -
    # die Kontingentliste darunter ist eine DATEN-Liste, kein Stueck.
    zuordnung = {"mitarbeiter": r"^## Mitarbeiter \(",
                 "fahrzeuge": r"^## Fahrzeuge \(",
                 "abwesend": r"^## Abwesenheiten \("}
    for kuerzel, muster in zuordnung.items():
        m = re.search(muster, txt, re.M)
        if not m:
            continue
        rest = txt[m.end():]
        rest = rest.split("\n\n", 2)
        absatz = rest[1] if len(rest) > 1 else ""
        stuecke = []
        for teil in re.split(r"[·\n]", absatz):
            s = re.sub(r"\s*\(.*?\)\s*$", "", teil.strip())
            s = s.strip().strip("*_ ").rstrip(".").strip()
            if len(s) < 3 or len(s) > 42:
                continue
            if not re.search(r"[A-Za-zÄÖÜäöüß]", s):
                continue
            stuecke.append(s)
        gesehen, rein = set(), []
        for s in stuecke:
            if s.lower() in gesehen:
                continue
            gesehen.add(s.lower())
            rein.append(s)
        if rein:
            erg[kuerzel] = rein
    return erg


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
