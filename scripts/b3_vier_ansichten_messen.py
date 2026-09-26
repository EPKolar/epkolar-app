# -*- coding: utf-8 -*-
"""B3 Stufen 4-7: vier Ansichten am GERENDERTEN Schirm messen, je 390 UND 1440.

WOZU
────
Die Regeln der Stufen 1-3 (12 px Mindestschrift, 44 px Tippziel, kein Emoji
als einziger Bedeutungstraeger, kein Querrollen, keine Verdeckung durch die
Fussleiste, kein Beschnitt bei vorhandenem Platz, keine Tabelle breiter als
der Schirm) wurden bisher je Einzelansicht mit einer eigenen Sonde geprueft.
Diese Sonde wendet ALLE SIEBEN auf die vier verbleibenden Ansichten an:

    Werkzeuge · Planung/Wochenplanung · Home · Arbeitsschein bearbeiten

WAS GEMESSEN WIRD
─────────────────
  schrift      getComputedStyle(...).fontSize JEDES Elements mit eigenem
               Textknoten. Gemessen wird der BERECHNETE Wert, nicht der im
               Quelltext: eine CSS-Regel kann eine Inline-Angabe schlagen und
               umgekehrt. Befund: < 12 px.
  tippziel     button / [role=button] / a / select / input / textarea /
               label: Rechteckhoehe. Befund bei 390 px: < 44 px.
  emoji        Bedienelemente, deren sichtbarer Text NUR aus Emoji/Symbolen
               besteht - und dabei weder title noch aria-label tragen.
  querrollen   document.scrollingElement.scrollWidth > innerWidth, mit dem
               VERURSACHENDEN Element (breitestes Rechteck rechts ausserhalb,
               das nicht in einem overflow-x:auto-Behaelter sitzt).
  verdeckung   die feste Fussleiste (.bottom-nav / .pf-hauptnav /
               .mob-shell-nav). Das Rechteck der Leiste ENTHAELT den Sync-
               Streifen nicht (top:-24px, ragt heraus) - gemessen wird
               deshalb die VEREINIGUNG von Leiste und allen Kindrechtecken.
               Danach wird bis zum Dokumentende gerollt und geprueft, welche
               Bedienelemente in dieser Vereinigung liegen.
  beschnitt    scrollWidth > clientWidth bei Elementen mit Text; Behaelter
               mit overflow-x auto/scroll werden getrennt als GEWOLLT gefuehrt.
  tabellen     jede sichtbare Tabelle: Breite gegen innerWidth, mit der
               breitesten Spalte als Verursacher.
  mengen       Knopf-/Feld-/Auswahlfeldzahl und die BENANNTEN Stuecke aus
               docs/GRUNDSTAND_UI_v3.9.930.md je Ansicht.

WAS NICHT GEMESSEN WIRD
───────────────────────
  * Farbkontrast, Hellmodus (dafuer scripts/hellmodus_messen.py).
  * Der Hochformat-/Querformat-Wechsel eines echten Geraets; gemessen wird
    ein Chromium-Viewport mit is_mobile/has_touch unter 600 px.
  * Die Zahl "erkannte Zahlen" aus dem Grundstand. Deren Zaehlvorschrift ist
    nicht dokumentiert; diese Sonde zaehlt nach EIGENER Vorschrift (siehe
    ZAHL_JS) und meldet das als eigene Groesse, NICHT als Vergleich. Der
    Vergleich laeuft ueber die BENANNTEN Werte, nicht ueber die Summe.
  * Die Rollen-Gatter. Gefahren wird mit role=admin; ein Monteur sieht in
    Werkzeuge drei statt fuenf Reiter (docs/WERKZEUG_REITER_VORARBEIT.md §4).
  * Echte Serverdaten. REST/Auth werden abgebrochen; die Amber-/Orange-
    Warnbaender sind Aufbau-Artefakt und KEIN Befund.

DIE KOEDER (Regel: ein suchender Riegel braucht einen KOEDER)
─────────────────────────────────────────────────────────────
Jeder ZAEHLENDE Melder bekommt vor der Messung einen Fall untergeschoben, von
dem sicher ist, dass er gefunden werden MUSS. Schlaegt der Koeder nicht an,
wird die Ansicht als NICHT GEMESSEN gefuehrt - nicht als "keine Befunde".

  K1 Schrift     ein Textknoten mit font-size:9px !important
  K2 Tippziel    ein Knopf mit height/min-height 20px !important (die
                 Hausregel @media(pointer:coarse){min-height:44px!important}
                 muss uebersteuert werden, sonst ist der Koeder selbst 44 px)
  K3 Emoji       ein Knopf, dessen ganzer Text "\U0001f527" ist, ohne title/aria
  K4 Beschnitt   ein 80 px breites overflow:hidden-Feld mit 240 Zeichen
  K5 Querrollen  ein 3000 px breites Element (nur zur PROBE des Melders,
                 sofort wieder entfernt)
  K6 Saat        die Daten werden ZURUECKGELESEN und in der Ansicht GESUCHT
  K7 Reitertext  in Werkzeuge muss bei 1440 px mindestens ein Reiter Text
                 tragen - sonst kann "am Telefon nur Ikonen" nichts belegen

AUFRUF
──────
    set EPK_INDEX=_mess_stand_939.html
    python scripts/b3_vier_ansichten_messen.py
    python scripts/b3_vier_ansichten_messen.py --nur werkzeuge
    python scripts/b3_vier_ansichten_messen.py --json befund.json

index.html wird NICHT angefasst. Gemessen wird die Datei aus EPK_INDEX.
"""
import io
import json
import os
import re
import sys

for _strom in (sys.stdout, sys.stderr):
    try:
        _strom.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)

import mob_ansicht_messen as M  # noqa: E402

import os as _os
# v3.9.942: die Breiten sind jetzt setzbar (EPK_BREITEN="375,390,1440").
# Grund: drei CSS-Regeln brechen die 44-px-Hausregel, und eine davon
# greift erst bei <=380 px - die hatte niemand gemessen. Ohne 375 im
# Lauf waere sie wieder nur behauptet.
BREITEN = [(int(_b), 900 if int(_b) >= 600 else 844)
           for _b in _os.environ.get("EPK_BREITEN", "390,1440").split(",")
           if _b.strip()]

# ── Saat ──────────────────────────────────────────────────────────────────
# Feldformen abgelesen, nicht geraten: Monteur aus dem feld-Filter,
# Arbeitsschein aus dem fixMap-Aufbau, Werkzeug aus `const defWz=()=>({...})`.
# Der Scheinstatus MUSS in AS_GRP_OFFEN stehen (aufgenommen/freigegeben/
# in_bearbeitung/aufgeschoben), sonst bleibt die Dispo-Schleife kalt.
MONTEURE = [
    {"id": "M1", "n": "Gerhard Steinbichler", "r": "Monteur", "austritt": ""},
    {"id": "M2", "n": "Johannes Hinterleitner", "r": "Obermonteur",
     "austritt": ""},
    {"id": "M3", "n": "Bernadette Wieshofer-Prandtner", "r": "Monteur",
     "austritt": ""},
]

PROJEKTE = [
    {"id": "P1", "nr": "PA241923", "name": "DR.-GSCHMEIDLERSTRASSE 10",
     "kunde": "GEDESAG", "ort": "Krems an der Donau", "status": "aktiv",
     "fortschritt": 48},
    {"id": "P2", "nr": "PA242467", "name": "BVH Sparkasse Ravelsbach",
     "kunde": "Sparkasse", "ort": "Ravelsbach", "status": "aktiv",
     "fortschritt": 12},
]


def _tage(ab=0, n=6):
    import datetime
    heute = datetime.date.today()
    montag = heute - datetime.timedelta(days=heute.weekday())
    return [(montag + datetime.timedelta(days=ab + k)).isoformat()
            for k in range(n)]


def _scheine():
    tage = _tage(0, 6)
    status = ["freigegeben", "in_bearbeitung", "aufgenommen",
              "freigegeben", "aufgeschoben", "in_bearbeitung"]
    kunden = [
        ("Marktgemeinde Sankt Leonhard am Hornerwald", "K-10441",
         "Steiner Landstrasse 44", "3572"),
        ("Hinterleitner Gebaeudetechnik GmbH", "K-20887",
         "Wachaustrasse 118a", "3620"),
        ("GEDESAG Gemeinnuetzige Donau-Ennstaler Siedlungs-AG", "K-30012",
         "Dr.-Gschmeidlerstrasse 10", "3500"),
        ("Weingut Gerald Waltner", "K-40119", "Kellergasse 7", "3491"),
        ("Sparkasse Ravelsbach Zweigstelle", "K-50220",
         "Hauptplatz 2", "3720"),
        ("Pfarre Sankt Michael Oberoesterreich", "K-60331",
         "Kirchenplatz 1", "4362"),
    ]
    arbeiten = [
        "Zaehlerkasten tauschen, Hauptleitung neu ziehen, FI-Schutzschalter "
        "nachruesten und Endpruefung samt Protokoll",
        "Stoerung Aussenbeleuchtung Stiegenhaus 2 - Bewegungsmelder "
        "defekt, Ersatz mitbringen",
        "Wartung Notlichtanlage, 24 Leuchten, Batterietest und "
        "Pruefbuch nachtragen",
        "Neuinstallation Weinkeller: 14 Steckdosen, 6 Leuchten, "
        "Verteiler erweitern",
        "Netzwerkverkabelung Schalterhalle, 18 Datendosen Cat.7",
        "Blitzschutz Pruefung nach OeVE/OeNORM E 8049 mit Befund",
    ]
    out = []
    for k in range(6):
        kd = kunden[k]
        out.append({
            "id": "S%d" % (k + 1), "nummer": "AS-%d" % (2401 + k),
            "kundName": kd[0], "kundNr": kd[1], "arbeitsort": kd[2],
            "plz": kd[3], "arbeitsanweisungen": arbeiten[k],
            "monteur": MONTEURE[k % 3]["id"], "aufgenommen": tage[0],
            "terminBestaetigt": tage[min(k, 5)], "terminVorschlag": "",
            "terminZeit": "07:30", "scheinstatus": status[k],
            "prioritaet": ["hoch", "normal", "keine", "dringend", "normal",
                           "hoch"][k],
            "scheinart": ["stoerung", "wartung", "montage", "stoerung",
                          "montage", "kein"][k],
            "sachbearbeiter": "Bernadette Wieshofer-Prandtner",
            "projektnr": PROJEKTE[k % 2]["nr"], "dauer": "4h",
        })
    return out


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
     "notizen": "Auf der Baustelle verschwunden", "zustandBewertung": 2},
    {"id": "W5", "name": "Bosch GBH 18V-26 F Akku-Bohrhammer",
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


def _eintraege():
    tage = _tage(0, 5)
    out = []
    for k in range(5):
        out.append({
            "id": "E%d" % (k + 1), "worker": "M1", "datum": tage[k],
            "project_id": PROJEKTE[k % 2]["id"] if k % 3 else "",
            "arbeitsschein_id": "" if k % 3 else "S1",
            "taetigkeit": "Zaehlerkasten tauschen und Endpruefung",
            "hours": 8 if k < 4 else 6.5, "von": "07:00", "bis": "16:00",
            "pause": 1, "gewerk": "elektro",
            "bemerkung": "Anfahrt Krems - Zwettl gemeinsam",
        })
    return out


# SAATWORT: muss nach dem Neuladen in IRGENDEINER Ansicht auftauchen.
SAATWORT = re.compile(r"Steinbichler|Hinterleitner|Steiner Landstra|Hilti")


# ══════════════════════════════════════════════════════════════════════════
# Die Messungen im Browser
# ══════════════════════════════════════════════════════════════════════════

# Gemeinsame Hilfen, jedem Block vorangestellt.
HILFEN = r"""
  const _cs = e => getComputedStyle(e);
  const _sicht = e => {
    const r = e.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return false;
    const c = _cs(e);
    if (c.visibility === 'hidden' || c.display === 'none') return false;
    if (parseFloat(c.opacity || '1') < 0.05) return false;
    return true;
  };
  const _weg = e => {
    const t = [];
    let x = e;
    while (x && x.nodeType === 1 && t.length < 5) {
      let s = x.tagName.toLowerCase();
      if (x.id) { s += '#' + x.id; t.unshift(s); break; }
      const k = (x.className && typeof x.className === 'string')
        ? x.className.trim().split(/\s+/).slice(0, 2).join('.') : '';
      if (k) s += '.' + k;
      t.unshift(s);
      x = x.parentElement;
    }
    return t.join(' > ');
  };
  const _txt = (e, n) => (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, n || 44);
  const _rollbarUeber = e => {
    let x = e.parentElement;
    while (x && x !== document.body) {
      const ox = _cs(x).overflowX;
      if (ox === 'auto' || ox === 'scroll') return _weg(x);
      x = x.parentElement;
    }
    return null;
  };
"""

# ── Schrift ───────────────────────────────────────────────────────────────
# Gemessen wird nur an Elementen mit EIGENEM Textknoten. Wer an jedem Element
# misst, zaehlt jede Schachtel mit und bekommt dieselbe Stelle achtmal.
SCHRIFT_JS = r"""() => {
""" + HILFEN + r"""
  const wurzel = document.getElementById('root') || document.body;
  const klein = [], alle = [];
  wurzel.querySelectorAll('*').forEach(e => {
    let eigen = '';
    for (const k of e.childNodes)
      if (k.nodeType === 3) eigen += k.nodeValue;
    eigen = eigen.replace(/\s+/g, ' ').trim();
    if (!eigen) return;
    if (!_sicht(e)) return;
    const px = Math.round(parseFloat(_cs(e).fontSize) * 10) / 10;
    alle.push(px);
    if (px < 12) klein.push({px: px, tag: e.tagName.toLowerCase(),
                             text: eigen.slice(0, 44), weg: _weg(e)});
  });
  klein.sort((a, b) => a.px - b.px);
  const zahl = {};
  alle.forEach(p => { zahl[p] = (zahl[p] || 0) + 1; });
  return {klein: klein.slice(0, 60), anzahl_klein: klein.length,
          gemessen: alle.length, verteilung: zahl};
}"""

KOEDER_SCHRIFT_EIN = r"""() => {
  const w = document.getElementById('root') || document.body;
  const d = document.createElement('div');
  d.id = '__k_schrift';
  d.style.setProperty('font-size', '9px', 'important');
  d.textContent = 'KOEDER Schrift neun Pixel';
  w.appendChild(d);
  return Math.round(parseFloat(getComputedStyle(d).fontSize) * 10) / 10;
}"""

# ── Tippziele ─────────────────────────────────────────────────────────────
# Die Hausregel @media(pointer:coarse),(max-width:768px) setzt
# min-height/min-width 44px !important auf button, [role=button], .clickable,
# a.btn und input[type=checkbox|radio|submit|button]. NICHT erfasst sind:
# select, input[type=text|date|...], textarea, label, a ohne .btn und jedes
# div mit onClick ohne role=button. Genau die sind hier der interessante Teil.
# ZWEI TOEPFE, und das ist der Unterschied zwischen einer Zahl und Laerm.
#   knopf   was man DRUECKT: button, [role=button], a, summary, .clickable und
#           input[checkbox|radio|submit|button]. Nur hier gilt die 44-px-Regel.
#   feld    select / input-Text / textarea / label. Die erste Fassung warf
#           alles in einen Topf und meldete im Arbeitsschein-Formular 22
#           Befunde, die alle BESCHRIFTUNGEN waren (19,5 px hohe Textzeilen
#           ueber einem 44 px hohen Eingabefeld). Eine Regel ueber Tippziele,
#           die an Beschriftungen anschlaegt, misst nicht das, was sie behauptet.
TIPP_JS = r"""() => {
""" + HILFEN + r"""
  const knopfSel = 'button, [role="button"], a, summary, .clickable, ' +
    'input[type="checkbox"], input[type="radio"], input[type="submit"], ' +
    'input[type="button"]';
  const feldSel = 'select, textarea, ' +
    'input:not([type="hidden"]):not([type="checkbox"]):not([type="radio"])' +
    ':not([type="submit"]):not([type="button"]), label';
  const nimm = e => {
    const r = e.getBoundingClientRect();
    return {art: e.tagName.toLowerCase() +
              (e.getAttribute('type') ? '[' + e.getAttribute('type') + ']' : '') +
              (e.getAttribute('role') ? '[role=' + e.getAttribute('role') + ']' : ''),
            h: Math.round(r.height * 10) / 10,
            w: Math.round(r.width * 10) / 10,
            text: _txt(e, 34), title: e.getAttribute('title'),
            aria: e.getAttribute('aria-label'),
            minH: _cs(e).minHeight, weg: _weg(e)};
  };
  const knopf = [], feld = [], arten = {};
  document.querySelectorAll(knopfSel).forEach(e => {
    if (e.closest('#__koeder_zone')) return;
    if (!_sicht(e)) return;
    const x = nimm(e);
    arten[x.art] = (arten[x.art] || 0) + 1;
    if (x.h < 44 || x.w < 44) knopf.push(x);
  });
  document.querySelectorAll(feldSel).forEach(e => {
    if (e.closest('#__koeder_zone')) return;
    if (!_sicht(e)) return;
    const x = nimm(e);
    // Eine Beschriftung, die ein Feld UMSCHLIESST, ist selbst das Tippziel -
    // eine, die nur darueber steht, nicht. Das wird getrennt gefuehrt.
    x.umschliesst_feld = !!e.querySelector('input, select, textarea');
    if (x.h < 44) feld.push(x);
  });
  knopf.sort((a, b) => a.h - b.h);
  feld.sort((a, b) => a.h - b.h);
  return {klein: knopf.slice(0, 60), anzahl_klein: knopf.length,
          felder_klein: feld.slice(0, 40), anzahl_felder_klein: feld.length,
          arten: arten};
}"""

KOEDER_TIPP_EIN = r"""() => {
  const w = document.getElementById('root') || document.body;
  let z = document.getElementById('__koeder_zone');
  if (!z) { z = document.createElement('div'); z.id = '__koeder_zone'; w.appendChild(z); }
  const b = document.createElement('button');
  b.id = '__k_tipp';
  b.textContent = 'KOEDER Tippziel';
  // Die Hausregel traegt !important - der Koeder muss sie uebersteuern,
  // sonst ist er selbst 44 px hoch und der Melder findet zu Recht nichts.
  b.style.setProperty('min-height', '20px', 'important');
  b.style.setProperty('height', '20px', 'important');
  b.style.setProperty('min-width', '30px', 'important');
  b.style.setProperty('width', '30px', 'important');
  b.style.setProperty('padding', '0', 'important');
  b.style.setProperty('font-size', '13px', 'important');
  z.appendChild(b);
  const r = b.getBoundingClientRect();
  return {h: Math.round(r.height), w: Math.round(r.width)};
}"""

# Der Koeder-Melder laeuft gegen die Zone, die der Hauptmelder ausblendet.
KOEDER_TIPP_MESSEN = r"""() => {
""" + HILFEN + r"""
  const z = document.getElementById('__koeder_zone');
  if (!z) return -1;
  let n = 0;
  z.querySelectorAll('button, [role="button"]').forEach(e => {
    if (!_sicht(e)) return;
    const r = e.getBoundingClientRect();
    if (r.height < 44 || r.width < 44) n++;
  });
  return n;
}"""

# ── Emoji als einziger Bedeutungstraeger ──────────────────────────────────
# Ein Bedienelement ist "nur Emoji", wenn sein sichtbarer Text nach Abzug
# aller Emoji-/Symbol-/Piktogramm-Bereiche und der Variantenselektoren LEER
# ist. Gezaehlt wird zusaetzlich, ob title oder aria-label eine Bedeutung
# nachliefern - erst OHNE beides ist es ein Befund.
#
# DIE ERSTE FASSUNG ZAEHLTE EINE AUFGEZAEHLTE LISTE VON CODEPOINT-BEREICHEN
# und hat damit weniger gefunden, als es gibt: die Pfeile und Zeichen aus dem
# Block "Geometrische Formen" (U+25A0-25FF: ▲ ▼ ◀ ▶) und Zeichen wie ⊘ standen
# in keinem Bereich, also galt so ein Knopf als "traegt Text" - und fiel aus
# der Liste. Ein Melder, der zu wenig findet, meldet gruen.
#
# Jetzt die umgekehrte Vorschrift, die keine Liste braucht: ein Bedienelement
# traegt nur dann Text, wenn in seiner Beschriftung ein BUCHSTABE oder eine
# ZIFFER steht. Bleibt nach Abzug aller Buchstaben und Ziffern die ganze
# Beschriftung uebrig, ist sie ein reines Zeichen - egal aus welchem Block.
EMOJI_JS = r"""() => {
""" + HILFEN + r"""
  const TEXTZEICHEN = /[\p{L}\p{N}]/u;
  const out = [], mitHilfe = [];
  document.querySelectorAll('button, [role="button"], a, summary').forEach(e => {
    if (!_sicht(e)) return;
    const roh = (e.textContent || '').replace(/\s+/g, ' ').trim();
    if (!roh) return;
    if (TEXTZEICHEN.test(roh)) return;    // traegt Text -> kein Befund
    const t = e.getAttribute('title'), a = e.getAttribute('aria-label');
    const e2 = {zeichen: roh, title: t, aria: a, weg: _weg(e),
                h: Math.round(e.getBoundingClientRect().height)};
    if (t || a) mitHilfe.push(e2); else out.push(e2);
  });
  return {ohne_hilfe: out, mit_hilfe: mitHilfe,
          anzahl_ohne: out.length, anzahl_mit: mitHilfe.length};
}"""

# ZWEI Koeder, nicht einer. Der erste (\U0001f527) haette die Fehlfassung
# oben NICHT entlarvt - er lag mitten im erfassten Bereich. Der zweite ist
# genau der Fall, der durchfiel: ein Dreieck aus "Geometrische Formen".
KOEDER_EMOJI_EIN = r"""() => {
  const w = document.getElementById('root') || document.body;
  const mach = (id, zeichen) => {
    const b = document.createElement('button');
    b.id = id; b.textContent = zeichen; w.appendChild(b);
    return b.textContent;
  };
  return {a: mach('__k_emoji', '\u{1F527}'),
          b: mach('__k_emoji2', '▲')};
}"""

# ── Querrollen ────────────────────────────────────────────────────────────
QUER_JS = r"""() => {
""" + HILFEN + r"""
  const se = document.scrollingElement || document.documentElement;
  const W = window.innerWidth;
  const ueber = [];
  // Auch hier KEINE Koeder-Ausnahme, siehe BESCHNITT_JS.
  (document.getElementById('root') || document.body)
    .querySelectorAll('*').forEach(e => {
      if (!_sicht(e)) return;
      const r = e.getBoundingClientRect();
      const rechts = Math.round(r.right + (se.scrollLeft || 0));
      if (rechts <= W + 1) return;
      ueber.push({rechts: rechts, breite: Math.round(r.width),
                  tag: e.tagName.toLowerCase(), text: _txt(e, 40),
                  in_rollbar: _rollbarUeber(e), weg: _weg(e)});
    });
  ueber.sort((a, b) => b.rechts - a.rechts);
  // Der aeusserste, der NICHT in einem gewollt rollbaren Behaelter sitzt.
  const echt = ueber.filter(x => !x.in_rollbar);

  // ══ DER TEIL, DER IM ERSTEN ENTWURF FEHLTE ══════════════════════════════
  // Die Regel lautet "document.scrollingElement.scrollWidth > innerWidth".
  // In dieser App kann dieser Vergleich NIE zutreffen: body traegt
  // overflow-x:hidden, und bis 1199 px scrollt ohnehin nicht die Seite,
  // sondern .main-pad (@media(max-width:1199px){.main-pad{overflow-y:auto}}).
  // Der erste Entwurf meldete deshalb in allen acht Laeufen "rollt nicht" -
  // waehrend .main-pad auf Home bei 390 px scrollWidth 460 gegen clientWidth
  // 390 hat. Die Seite ROLLT quer, nur nicht dort, wo die Regel hinsieht.
  // Gemessen wird jetzt JEDER waagrechte Roller, samt dem breitesten Kind,
  // das ihn aufspannt.
  const roller = [];
  (document.getElementById('root') || document.body)
    .querySelectorAll('*').forEach(e => {
      if (e.scrollWidth <= e.clientWidth + 1) return;
      const ox = _cs(e).overflowX;
      if (ox !== 'auto' && ox !== 'scroll') return;
      let breitestes = null;
      e.querySelectorAll('*').forEach(k => {
        const r = k.getBoundingClientRect();
        if (!breitestes || r.width > breitestes.breite)
          breitestes = {breite: Math.round(r.width), tag: k.tagName.toLowerCase(),
                        text: _txt(k, 40), stil: (k.getAttribute('style') || '').slice(0, 150),
                        klasse: (typeof k.className === 'string') ? k.className : '',
                        weg: _weg(k)};
      });
      roller.push({weg: _weg(e), scrollWidth: e.scrollWidth,
                   clientWidth: e.clientWidth,
                   ueberschuss: e.scrollWidth - e.clientWidth,
                   breitestes_kind: breitestes});
    });
  roller.sort((a, b) => b.ueberschuss - a.ueberschuss);

  return {scrollWidth: Math.round(se.scrollWidth), innerWidth: W,
          rollt: se.scrollWidth > W + 1,
          body_scroll: Math.round(document.body.scrollWidth),
          ursache: echt.slice(0, 6), in_rollbaren: ueber.length - echt.length,
          alle_ueber: ueber.length,
          waagrechte_roller: roller.slice(0, 6),
          rollt_irgendwo: roller.length > 0};
}"""

# KOEDER K5. ERSTE FASSUNG WAR FALSCH GEBAUT und das ist selbst ein Befund:
# sie legte ein 3000 px breites Element in #root und erwartete, dass
# document.scrollingElement.scrollWidth waechst. Es wuchs NICHT - weil ein
# Vorfahr overflow-x nicht auf visible hat. Die Folge fuer die Regel
# "bei 390 px darf die Seite nicht quer rollen": sie kann ueber scrollWidth
# GAR NICHT rot werden. Zu breiter Inhalt wird hier nicht gerollt, sondern
# still ABGESCHNITTEN. Gemessen wird deshalb ueber die Rechtecke (QUER_JS),
# und dieser Koeder belegt genau das, samt dem abschneidenden Vorfahren.
KOEDER_QUER_EIN = r"""() => {
""" + HILFEN + r"""
  const se = document.scrollingElement || document.documentElement;
  const vorher = se.scrollWidth;
  const d = document.createElement('div');
  d.id = '__k_quer';
  d.style.cssText = 'width:3000px;height:3px;background:red';
  (document.getElementById('root') || document.body).appendChild(d);
  let klipper = null;
  let x = d.parentElement;
  while (x && x !== document.documentElement) {
    const ox = _cs(x).overflowX;
    if (ox !== 'visible') { klipper = _weg(x) + '  overflow-x:' + ox; break; }
    x = x.parentElement;
  }
  return {vorher: Math.round(vorher),
          mit_koeder: Math.round((document.scrollingElement ||
                                  document.documentElement).scrollWidth),
          koeder_breite: Math.round(d.getBoundingClientRect().width),
          koeder_rechts: Math.round(d.getBoundingClientRect().right),
          abschneidender_vorfahr: klipper};
}"""

# ── Verdeckung durch die feste Fussleiste ─────────────────────────────────
# Das Rechteck der Leiste enthaelt den Sync-/Offline-Streifen NICHT: der sitzt
# als position:absolute mit top:-24px IN der Leiste und ragt darueber hinaus.
# Ein Kind, das aus seinem Elter herausragt, zaehlt in getBoundingClientRect()
# des Elters nicht mit. Gemessen wird deshalb die VEREINIGUNG.
VERDECKUNG_JS = r"""() => {
""" + HILFEN + r"""
  const kandidaten = ['.bottom-nav', '.pf-hauptnav', '.mob-shell-nav'];
  let leiste = null;
  for (const s of kandidaten) {
    for (const e of document.querySelectorAll(s)) {
      const c = _cs(e);
      if (c.position !== 'fixed' || c.display === 'none') continue;
      const r = e.getBoundingClientRect();
      if (r.height < 5) continue;
      leiste = e; break;
    }
    if (leiste) break;
  }
  if (!leiste) return {leiste: null, hinweis: 'keine feste Fussleiste sichtbar'};
  let oben = leiste.getBoundingClientRect().top;
  leiste.querySelectorAll('*').forEach(k => {
    const r = k.getBoundingClientRect();
    if (r.height > 0 && r.top < oben) oben = r.top;
  });
  const lr = leiste.getBoundingClientRect();
  const sel = 'button, [role="button"], a, select, textarea, ' +
    'input:not([type="hidden"]), label, .clickable';
  const verdeckt = [];
  document.querySelectorAll(sel).forEach(e => {
    if (leiste.contains(e)) return;
    if (e.closest('#__koeder_zone')) return;
    if (!_sicht(e)) return;
    const r = e.getBoundingClientRect();
    if (r.bottom <= oben + 0.5) return;          // ganz oberhalb -> frei
    if (r.top >= window.innerHeight) return;      // gar nicht im Bild
    verdeckt.push({text: _txt(e, 34), aria: e.getAttribute('aria-label'),
                   id: e.id || null,
                   top: Math.round(r.top), bottom: Math.round(r.bottom),
                   weg: _weg(e)});
  });
  // Das LETZTE Bedienelement im Inhalt - es muss vollstaendig sichtbar sein.
  const inhalt = Array.from(document.querySelectorAll(sel))
    .filter(e => !leiste.contains(e) && !e.closest('#__koeder_zone')
                 && e.id !== '__k_verdeckt' && _sicht(e));
  const letztes = inhalt.length ? inhalt[inhalt.length - 1] : null;
  const lr2 = letztes ? letztes.getBoundingClientRect() : null;
  return {letztes_bedienelement: letztes ? {
            text: _txt(letztes, 34), aria: letztes.getAttribute('aria-label'),
            unten: Math.round(lr2.bottom), weg: _weg(letztes),
            luft_bis_leiste: Math.round(oben - lr2.bottom)} : null,
          leiste: leiste.className || leiste.tagName,
          leiste_hoehe: Math.round(lr.height),
          leiste_oben: Math.round(lr.top),
          vereinigung_oben: Math.round(oben),
          ueberstand: Math.round(lr.top - oben),
          fensterhoehe: window.innerHeight,
          dokument: Math.round((document.scrollingElement ||
                                document.documentElement).scrollHeight),
          rollstand: Math.round(window.scrollY),
          verdeckt: verdeckt.slice(0, 20), anzahl: verdeckt.length};
}"""

# ── Beschnitt ─────────────────────────────────────────────────────────────
BESCHNITT_JS = r"""() => {
""" + HILFEN + r"""
  const wurzel = document.getElementById('root') || document.body;
  const schlimm = [], gewollt = [];
  // KEINE Ausnahme fuer die Koeder-Kennungen: dieser Melder MUSS den Koeder
  // sehen. Der erste Entwurf blendete '__k*' aus und meldete den eigenen
  // Koeder deshalb als nicht gefunden - ein Melder, der seinen Koeder
  // wegfiltert, ist genau der Fall, gegen den der Koeder da ist.
  wurzel.querySelectorAll('*').forEach(e => {
    if (e.scrollWidth <= e.clientWidth + 1) return;
    const t = _txt(e, 44);
    if (!t) return;
    const c = _cs(e);
    const eintrag = {tag: e.tagName.toLowerCase(), text: t,
                     scroll: e.scrollWidth, sicht: e.clientWidth,
                     overflowX: c.overflowX, ellipsis: c.textOverflow,
                     weg: _weg(e)};
    if (c.overflowX === 'auto' || c.overflowX === 'scroll') gewollt.push(eintrag);
    else schlimm.push(eintrag);
  });
  return {schlimm: schlimm.slice(0, 25), gewollt: gewollt.slice(0, 15),
          anzahl_schlimm: schlimm.length, anzahl_gewollt: gewollt.length};
}"""

KOEDER_BESCHNITT_EIN = r"""() => {
  const w = document.getElementById('root') || document.body;
  const d = document.createElement('div');
  d.id = '__k_beschnitt';
  d.style.cssText = 'width:80px;overflow:hidden;white-space:nowrap';
  d.textContent = 'K'.repeat(240);
  w.appendChild(d);
  return d.scrollWidth > d.clientWidth + 1;
}"""

# KOEDER K7 zum Tabellenmelder. Ohne ihn heisst "keine Tabelle breiter als der
# Schirm" nur "keine Tabelle gesehen" - und bei 390 px zeigen drei der vier
# Ansichten tatsaechlich KEINE Tabelle (Kartenansicht). Genau da wird ein
# zaehlender Melder beim eigenen Ausfall gruen.
# KOEDER K8 zum Verdeckungsmelder. "0 verdeckte Bedienelemente" ist die
# Aussage, die dieser Melder in allen vier Ansichten liefert - und genau eine
# solche Null ist wertlos, solange der Melder nicht bewiesen hat, dass er eine
# Verdeckung ueberhaupt sehen wuerde. Der Koeder ist ein Knopf, der fest ueber
# der Leiste klebt; er MUSS in der Liste erscheinen.
KOEDER_VERDECKT_EIN = r"""() => {
  const b = document.createElement('button');
  b.id = '__k_verdeckt';
  b.textContent = 'KOEDER verdeckt';
  b.style.cssText = 'position:fixed;left:8px;bottom:6px;z-index:10;' +
    'height:30px;min-height:30px';
  document.body.appendChild(b);
  const r = b.getBoundingClientRect();
  return {unten: Math.round(r.bottom), oben: Math.round(r.top)};
}"""

KOEDER_VERDECKT_AUS = r"""() => {
  const b = document.getElementById('__k_verdeckt');
  if (b) b.remove();
  return !document.getElementById('__k_verdeckt');
}"""

KOEDER_TABELLE_EIN = r"""() => {
  const w = document.getElementById('root') || document.body;
  const t = document.createElement('table');
  t.id = '__k_tabelle';
  t.innerHTML = '<thead><tr><th style="width:2200px">KOEDER breite Spalte</th>' +
    '<th style="width:800px">zweite</th></tr></thead>' +
    '<tbody><tr><td>x</td><td>y</td></tr></tbody>';
  t.style.cssText = 'width:3000px;table-layout:fixed';
  w.appendChild(t);
  return Math.round(t.getBoundingClientRect().width);
}"""

KOEDER_AUS = r"""() => {
  ['__k_schrift', '__k_tipp', '__k_emoji', '__k_emoji2', '__k_beschnitt',
   '__k_quer', '__k_tabelle', '__koeder_zone'].forEach(i => {
    const e = document.getElementById(i);
    if (e && e.parentElement) e.parentElement.removeChild(e);
  });
  return ['__k_schrift', '__k_tipp', '__k_emoji', '__k_emoji2',
          '__k_beschnitt', '__k_tabelle',
          '__koeder_zone'].filter(i => document.getElementById(i));
}"""

# ── Tabellen ──────────────────────────────────────────────────────────────
TABELLE_JS = r"""() => {
""" + HILFEN + r"""
  const W = window.innerWidth;
  const out = [];
  document.querySelectorAll('table').forEach(t => {
    if (!_sicht(t)) return;
    const r = t.getBoundingClientRect();
    const kopf = t.querySelector('thead tr') || t.querySelector('tr');
    const spalten = kopf ? Array.from(kopf.children).map(c => ({
      text: _txt(c, 22), breite: Math.round(c.getBoundingClientRect().width)
    })) : [];
    spalten.sort((a, b) => b.breite - a.breite);
    const beh = t.parentElement;
    const bc = beh ? _cs(beh) : null;
    out.push({
      breite: Math.round(r.width), scrollWidth: Math.round(t.scrollWidth),
      innerWidth: W, ueber: Math.round(r.width) > W + 1,
      behaelter: beh ? _weg(beh) : null,
      behaelter_overflowX: bc ? bc.overflowX : null,
      behaelter_sicht: beh ? beh.clientWidth : null,
      behaelter_rollt: beh ? beh.scrollWidth > beh.clientWidth + 1 : null,
      spalten_breiteste: spalten.slice(0, 4),
      zeilen: t.querySelectorAll('tr').length, weg: _weg(t)});
  });
  return out;
}"""

# ── Mengen ────────────────────────────────────────────────────────────────
# "erkannte Zahlen" nach EIGENER Vorschrift (siehe Dateikopf): jede Zahl im
# sichtbaren Text, die eine Einheit (%, h, EUR) traegt oder alleinstehend in
# einer Klammer/Kachel steht. Diese Zahl ist NICHT mit dem Grundstand
# vergleichbar, dessen Vorschrift nicht dokumentiert ist.
MENGEN_JS = r"""() => {
""" + HILFEN + r"""
  const sichtbar = e => _sicht(e);
  const knoepfe = Array.from(document.querySelectorAll('button, [role="button"]'))
    .filter(sichtbar);
  const felder = Array.from(document.querySelectorAll(
    'input:not([type="hidden"]):not([type="checkbox"]):not([type="radio"]):not([type="file"]), textarea'))
    .filter(sichtbar);
  const auswahl = Array.from(document.querySelectorAll('select')).filter(sichtbar);
  const txt = ((document.getElementById('root') || document.body).innerText || '')
    .replace(/ /g, ' ');
  const zahlen = Array.from(new Set(
    (txt.match(/\d[\d\s.,]*\s*(?:%|h\b|€|EUR)/g) || []).map(s => s.trim())));
  return {
    knoepfe: knoepfe.length,
    knopf_texte: knoepfe.map(b => _txt(b, 40) || ('[aria] ' + (b.getAttribute('aria-label') || '') ) || '[leer]'),
    felder: felder.length,
    feld_platzhalter: felder.map(f => f.getAttribute('placeholder') || ('[' + (f.getAttribute('type') || f.tagName.toLowerCase()) + ']')),
    auswahl: auswahl.length,
    auswahl_optionen: auswahl.map(s => Array.from(s.options).map(o => (o.textContent || '').trim())),
    zahlen: zahlen,
    kacheln: Array.from(document.querySelectorAll('[role="button"][aria-label]'))
      .filter(sichtbar).map(e => e.getAttribute('aria-label'))
  };
}"""

# Rollen bis ans Ende - erst dort kann die Fussleiste das letzte Element
# verdecken.
#
# ERSTE FASSUNG MASS DEN FALSCHEN ROLLER, und die Zahl sah trotzdem sauber
# aus. Bis 1199 px scrollt nicht die SEITE, sondern der Behaelter:
#   @media(max-width:1199px){ .app-shell{height:100dvh;overflow:hidden}
#                             .main-pad{flex:1;overflow-y:auto} }
# window.scrollTo() bewegte damit nur die 70 px, die das Dokument ausserhalb
# der Spalte noch hergab - der Inhalt selbst blieb oben stehen. Gemeldet
# wurden dann Bedienelemente "in der Leistenzone", die in Wahrheit gar nicht
# am Ende der Liste standen. Jetzt wird JEDER Roller bis an sein Ende
# gefahren und BELEGT, dass er dort angekommen ist.
BIS_UNTEN_JS = r"""() => {
  const se = document.scrollingElement || document.documentElement;
  const roller = [];
  const kandidaten = [se, document.body].concat(
    Array.from(document.querySelectorAll('*')));
  const gesehen = new Set();
  kandidaten.forEach(e => {
    if (!e || gesehen.has(e)) return;
    gesehen.add(e);
    if (e.scrollHeight <= e.clientHeight + 4) return;
    const oy = getComputedStyle(e).overflowY;
    if (e !== se && e !== document.body && oy !== 'auto' && oy !== 'scroll')
      return;
    e.scrollTop = e.scrollHeight;
    roller.push({
      weg: (e === se ? 'scrollingElement'
            : (e.className && typeof e.className === 'string'
               ? e.tagName.toLowerCase() + '.' + e.className.trim().split(/\s+/)[0]
               : e.tagName.toLowerCase())),
      hoehe: Math.round(e.scrollHeight), sicht: Math.round(e.clientHeight),
      oben: Math.round(e.scrollTop),
      am_ende: e.scrollTop + e.clientHeight >= e.scrollHeight - 2});
  });
  window.scrollTo(0, se.scrollHeight);
  return {roller: roller, fenster_y: Math.round(window.scrollY),
          anzahl: roller.length};
}"""


# ══════════════════════════════════════════════════════════════════════════
# Navigation in die vier Ansichten
# ══════════════════════════════════════════════════════════════════════════
# Unter 600 px gibt es die Fussleiste mit "Mehr"; darueber die obere
# Reiterleiste (.top-tabs). NAV_WAEHLEN_JS aus mob_ansicht_messen nimmt den
# LETZTEN Knopf mit dem aria-label - am Rechner gibt es nur einen.
NAV_TOP_JS = r"""(label) => {
  const k = Array.from(document.querySelectorAll('button[aria-label]'))
    .filter(b => b.getAttribute('aria-label') === label)
    .filter(b => b.getBoundingClientRect().height > 0);
  if (!k.length) return 'nicht-gefunden';
  k[0].click();
  return 'geklickt/' + k.length;
}"""

# DAS MEHR-MENUE BLEIBT OFFEN. Erster Lauf, 390 px, Home: nach dem Klick lag
# noch die Vollbild-Auffangflaeche (aria-label "Mehr-Menü schließen") ueber der
# Seite, und zwei Menueeintraege (Werkzeuge, Bauprovisorien) sassen genau in
# der Leistenzone. Der Verdeckungsmelder hat sie brav gemeldet - als Befund an
# der App, obwohl es der Aufbau der Sonde war. Deshalb wird das Menue nach
# jeder Navigation GESCHLOSSEN und das Schliessen BELEGT.
MEHR_ZU_JS = r"""() => {
  const zu = Array.from(document.querySelectorAll('[aria-label]'))
    .filter(e => (e.getAttribute('aria-label') || '').indexOf('Mehr-Men') === 0);
  if (!zu.length) return 'kein-menue-offen';
  zu[0].click();
  return 'geschlossen/' + zu.length;
}"""

MEHR_OFFEN_JS = r"""() => Array.from(document.querySelectorAll('[aria-label]'))
  .filter(e => (e.getAttribute('aria-label') || '').indexOf('Mehr-Men') === 0)
  .length"""

# Ein Nachweis je Ansicht: ohne ihn misst die Sonde irgendeine Seite und
# meldet saubere Zahlen dafuer.
ANSICHT_DA_JS = r"""(art) => {
""" + HILFEN + r"""
  const t = ((document.getElementById('root') || document.body).innerText || '');
  const knopf = s => Array.from(document.querySelectorAll('button'))
    .some(b => (b.textContent || '').indexOf(s) >= 0);
  if (art === 'werkzeuge')
    return {marke: 'Reiterzeile mit \u{1F4F7}',
            da: Array.from(document.querySelectorAll('.tab-bar')).some(e => {
              const b = Array.from(e.querySelectorAll(':scope > button'));
              return b.length >= 3 &&
                b.some(x => (x.textContent || '').indexOf('\u{1F4F7}') >= 0);
            }) && /Kalibrierung|Inventar|Seriennr/.test(t)};
  if (art === 'planung')
    return {marke: '"+ Zeile" und "Vorwoche"',
            da: knopf('+ Zeile') && knopf('Vorwoche')};
  // HOME BRAUCHT EINEN MARKER, DER NUR HOME HAT.
  // Die erste Fassung fragte "mindestens vier [role=button][aria-label] und
  // irgendwo das Wort Projekt" - das trifft auf das CHEF-DASHBOARD genauso zu,
  // und genau dort ist der Lauf bei 390 px gelandet: der Klick auf den
  // Gruppenknopf der Fussleiste oeffnete den zuletzt aktiven Reiter der
  // Gruppe 0, und das war Chef. Die Sonde hat dann das Chef-Dashboard
  // vermessen und "Home" darueber geschrieben. Merkmale, die TRENNEN:
  // "Ueberblick" gibt es nur in ChefDashboard, die Kachel-aria-labels
  // "Werkzeugwert"/"Bautagebuch"/"Monatsabrechnung" und "Tanken" nur in
  // HomeView.
  if (art === 'home') {
    const aria = Array.from(document.querySelectorAll('[aria-label]'))
      .map(e => e.getAttribute('aria-label'));
    const eigen = aria.some(a => /Werkzeugwert|Bautagebuch|Monatsabrechnung/.test(a))
      || /Tanken|Urlaub beantragen/.test(t);
    const chef = /Überblick/.test(t);
    return {marke: 'HomeView-Kacheln (Werkzeugwert/Bautagebuch/Tanken) UND '
                   + 'kein Chef-Merkmal "Ueberblick"',
            da: eigen && !chef, eigen: eigen, chef_merkmal: chef};
  }
  if (art === 'as_form')
    return {marke: '.as-form-grid bzw. Speichern-Knopf',
            da: !!document.querySelector('.as-form-grid') ||
                Array.from(document.querySelectorAll('button'))
                  .some(b => /Speichern/i.test(b.textContent || ''))};
  return {marke: '?', da: false};
}"""

# NAVIGATION IM MEHR-MENUE, aber NICHT ueber die Fussleiste.
# NAV_WAEHLEN_JS aus mob_ansicht_messen nimmt den LETZTEN Knopf mit dem
# aria-label. Bei "Home" sind das drei Knoepfe, und der letzte ist der
# GRUPPENKNOPF der Fussleiste - der oeffnet den zuletzt aktiven Reiter seiner
# Gruppe, und in Gruppe 0 liegt neben Home auch Chef. Ergebnis war ein
# vollstaendig vermessenes Chef-Dashboard unter der Ueberschrift "Home".
# Deshalb hier: nur Knoepfe, die NICHT in der Fussleiste sitzen.
NAV_MEHR_JS = r"""(label) => {
  const k = Array.from(document.querySelectorAll('button[aria-label]'))
    .filter(b => b.getAttribute('aria-label') === label)
    .filter(b => !b.closest('.bottom-nav'))
    .filter(b => b.getBoundingClientRect().height > 0);
  if (!k.length) return 'nicht-gefunden';
  k[k.length - 1].click();
  return 'geklickt/' + k.length + ' (ohne Fussleiste)';
}"""

# Arbeitsschein bearbeiten: der Deep-Link, den das Chef-Portal benutzt
# (`window.__asOpenId`, v3.9.489). Der useEffect haengt an [arbeitsscheine]
# und laeuft beim Aufbau der Ansicht - die Marke muss also VOR der
# Navigation gesetzt werden.
AS_MARKE_JS = r"""(id) => { window.__asOpenId = id; return window.__asOpenId; }"""

# Belegen, dass wirklich das Formular offen ist und nicht die Liste.
AS_FORM_DA_JS = r"""() => {
""" + HILFEN + r"""
  const t = ((document.getElementById('root') || document.body).innerText || '');
  return {
    nummer_im_text: /AS-2401/.test(t),
    felder: document.querySelectorAll('input:not([type=hidden]), textarea, select').length,
    gitter: !!document.querySelector('.as-form-grid'),
    speichern: Array.from(document.querySelectorAll('button'))
      .filter(b => /Speichern|Sichern/i.test(b.textContent || '')).length
  };
}"""

# Fallback: den Stift in der Liste antippen.
AS_STIFT_JS = r"""() => {
  const k = Array.from(document.querySelectorAll('button'))
    .filter(b => (b.textContent || '').indexOf('✏') >= 0)
    .filter(b => b.getBoundingClientRect().height > 0);
  if (!k.length) return 'kein-stift';
  k[0].click();
  return 'geklickt/' + k.length;
}"""

ANSICHTEN = {
    "werkzeuge": {"nav": "Werkzeuge", "titel": "Werkzeuge"},
    "planung": {"nav": "Planung", "titel": "Planung / Wochenplanung"},
    "home": {"nav": "Home", "titel": "Home / Startseite"},
    "as_form": {"nav": "Arbeitsscheine", "titel": "Arbeitsschein bearbeiten"},
}


def _saeen(seite):
    cfg = {"db": M.DB_NAME, "daten": {
        "monteure": MONTEURE, "arbeitsscheine": _scheine(),
        "projects": PROJEKTE, "entries": _eintraege(),
        "werkzeuge": WERKZEUGE}}
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
    seite.wait_for_timeout(6500)
    t = seite.evaluate("() => document.body.innerText")
    treffer = len(SAATWORT.findall(t or ""))
    print("   K6 Saat in der Ansicht sichtbar: %d Treffer" % treffer)
    if not treffer:
        raise SystemExit(
            "ABBRUCH (K6): die Saat liegt in der Datenbank, erscheint aber in "
            "KEINER Ansicht. Ein Lauf darueber misst leere Renderpfade.")
    return treffer


def _navigieren(seite, kuerzel, breite):
    """In die Ansicht gehen. Gibt die Meldung zurueck oder None bei Fehlschlag."""
    ziel = ANSICHTEN[kuerzel]["nav"]
    if kuerzel == "as_form":
        seite.evaluate(AS_MARKE_JS, "S1")
    if breite < 600:
        seite.evaluate(M.NAV_OEFFNEN_JS)
        seite.wait_for_timeout(400)
        weg = seite.evaluate(NAV_MEHR_JS, ziel)
    else:
        weg = seite.evaluate(NAV_TOP_JS, ziel)
    seite.wait_for_timeout(2600)
    if breite < 600:
        print("   Mehr-Menue: %s" % seite.evaluate(MEHR_ZU_JS))
        seite.wait_for_timeout(700)
        rest = seite.evaluate(MEHR_OFFEN_JS)
        if rest:
            print("   WARNUNG: Mehr-Menue noch offen (%d Auffangflaechen)"
                  % rest)
    if kuerzel == "as_form":
        da = seite.evaluate(AS_FORM_DA_JS)
        if not (da.get("gitter") or da.get("speichern")):
            weg2 = seite.evaluate(AS_STIFT_JS)
            seite.wait_for_timeout(2200)
            da = seite.evaluate(AS_FORM_DA_JS)
            print("   Deep-Link griff nicht, Stift: %s" % weg2)
        print("   Formular belegt: %s" % da)
        if not (da.get("gitter") or da.get("speichern")):
            return None
    nw = seite.evaluate(ANSICHT_DA_JS, kuerzel)
    print("   Ansicht belegt ueber %s: %s" % (nw["marke"], nw["da"]))
    if not nw["da"]:
        return None
    return weg


def _koeder(seite, marke, offen, self_quer):
    """Alle Melder gegen einen bekannten Fall fahren. Gibt True, wenn alle
    angeschlagen haben."""
    ok = True
    px = seite.evaluate(KOEDER_SCHRIFT_EIN)
    seite.evaluate(KOEDER_EMOJI_EIN)
    tipp = seite.evaluate(KOEDER_TIPP_EIN)
    besch = seite.evaluate(KOEDER_BESCHNITT_EIN)
    quer = seite.evaluate(KOEDER_QUER_EIN)

    s = seite.evaluate(SCHRIFT_JS)
    gefunden_schrift = any(x["text"].startswith("KOEDER Schrift")
                           for x in s["klein"])
    e = seite.evaluate(EMOJI_JS)
    gefunden_emoji = (
        any(x["zeichen"] == "\U0001f527" for x in e["ohne_hilfe"])
        and any(x["zeichen"] == "▲" for x in e["ohne_hilfe"]))
    n_tipp = seite.evaluate(KOEDER_TIPP_MESSEN)
    b = seite.evaluate(BESCHNITT_JS)
    gefunden_besch = any(x["text"].startswith("KKK") for x in b["schlimm"])
    kv = seite.evaluate(KOEDER_VERDECKT_EIN)
    vd = seite.evaluate(VERDECKUNG_JS)
    if vd.get("leiste") is None:
        # Kein Befund und kein Fehler: unter der Regel gibt es hier keine
        # feste Fussleiste (die .bottom-nav lebt in @media(max-width:600px)).
        gefunden_verdeckt = None
    else:
        gefunden_verdeckt = any(x.get("id") == "__k_verdeckt"
                                for x in vd.get("verdeckt", []))
    seite.evaluate(KOEDER_VERDECKT_AUS)

    tb = seite.evaluate(KOEDER_TABELLE_EIN)
    tlist = seite.evaluate(TABELLE_JS)
    gefunden_tab = any(t["ueber"] and t["breite"] >= 2900 for t in tlist)
    q = seite.evaluate(QUER_JS)
    gefunden_quer = any(x["breite"] >= 2900 for x in q["ursache"])
    self_quer["klipper"] = quer.get("abschneidender_vorfahr")
    self_quer["scrollWidth_mit_3000px_kind"] = quer["mit_koeder"]
    self_quer["scrollWidth_vorher"] = quer["vorher"]

    proben = [
        ("K1 Schrift", gefunden_schrift, "9px-Text gemessen als %s px" % px),
        ("K2 Tippziel", n_tipp == 1,
         "Koeder-Knopf %sx%s, Melder fand %s" % (tipp.get("w"), tipp.get("h"),
                                                 n_tipp)),
        ("K3 Emoji", gefunden_emoji,
         "zwei Knoepfe: einer nur \U0001f527, einer nur ▲ - letzterer ist "
         "genau der Fall, den die erste Fassung des Melders durchliess"),
        ("K4 Beschnitt", gefunden_besch and besch,
         "240 Zeichen in 80 px"),
        ("K5 Querrollen", gefunden_quer,
         "3000px-Kind: Rechteck %s px, scrollWidth %s -> %s, abgeschnitten "
         "von %s" % (quer["koeder_breite"], quer["vorher"],
                     quer["mit_koeder"], quer["abschneidender_vorfahr"])),
        ("K7 Tabelle", gefunden_tab,
         "3000px-Tabelle gemessen als %s px, %d Tabellen im Bild"
         % (tb, len(tlist))),
    ]
    if gefunden_verdeckt is None:
        print("   K8 Verdeckung  ENTFAELLT (keine feste Fussleiste bei dieser "
              "Breite - die .bottom-nav lebt in @media(max-width:600px))")
    else:
        proben.append(("K8 Verdeckung", gefunden_verdeckt,
                       "Knopf fest ueber der Leiste, unten %s"
                       % kv.get("unten")))
    for name, traf, wie in proben:
        print("   %-13s %s  (%s)" % (name, "ANGESCHLAGEN" if traf else "STUMM",
                                     wie))
        if not traf:
            ok = False
            offen.append("%s: %s hat seinen Koeder NICHT gefangen (%s) - "
                         "dieser Melder misst nichts." % (marke, name, wie))
    rest = seite.evaluate(KOEDER_AUS)
    if rest:
        offen.append("%s: Koeder nicht restlos entfernt: %s" % (marke, rest))
        ok = False
    seite.wait_for_timeout(250)
    return ok


def _lauf(pw, url, kuerzel, breite, hoehe):
    marke = "%s @ %dx%d" % (kuerzel, breite, hoehe)
    print("\n── %s ─────────────────────────────" % marke)
    d = {"ansicht": kuerzel, "breite": breite, "hoehe": hoehe}
    offen, fehler = [], []
    ctx = pw.new_context(viewport={"width": breite, "height": hoehe},
                         is_mobile=breite < 600, has_touch=breite < 600,
                         device_scale_factor=2 if breite < 600 else 1)
    ctx.add_init_script(M.INIT)
    # Ohne monteurId bleibt `_wzQuickBtn` stumm und die Zeiterfassung leer -
    # ein nicht angeschalteter Zweig sieht wie ein Ist-Zustand aus.
    ctx.add_init_script(
        "try{var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
        "u.monteurId='M1';u.name='Gerhard Steinbichler';u.role='admin';"
        "localStorage.setItem('epkolar_user',JSON.stringify(u));}catch(e){}")
    ctx.route("**/rest/v1/**", lambda r: r.abort())
    ctx.route("**/auth/v1/**", lambda r: r.abort())
    seite = ctx.new_page()
    seite.on("pageerror", lambda x: fehler.append(str(x)[:170]))
    try:
        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(3800)
        _saeen(seite)
        weg = _navigieren(seite, kuerzel, breite)
        print("   Navigation: %s" % weg)
        if weg in (None, "nicht-gefunden"):
            d["nicht_erreichbar"] = True
            offen.append("%s: Ansicht nicht erreichbar (%s)" % (marke, weg))
            ctx.close()
            return d, offen, fehler

        d["querrollen_selbstprobe"] = {}
        d["koeder_ok"] = _koeder(seite, marke, offen,
                                 d["querrollen_selbstprobe"])

        d["schrift"] = seite.evaluate(SCHRIFT_JS)
        d["tipp"] = seite.evaluate(TIPP_JS)
        d["emoji"] = seite.evaluate(EMOJI_JS)
        d["quer"] = seite.evaluate(QUER_JS)
        d["beschnitt"] = seite.evaluate(BESCHNITT_JS)
        d["tabellen"] = seite.evaluate(TABELLE_JS)
        d["mengen"] = seite.evaluate(MENGEN_JS)
        d["verdeckung_oben"] = seite.evaluate(VERDECKUNG_JS)
        seite.evaluate(BIS_UNTEN_JS)
        seite.wait_for_timeout(900)
        d["roller"] = seite.evaluate(BIS_UNTEN_JS)
        seite.wait_for_timeout(700)
        d["verdeckung_unten"] = seite.evaluate(VERDECKUNG_JS)
        print("   Roller bis ans Ende: %s" % [
            "%s %d/%d %s" % (r["weg"], r["oben"], r["hoehe"],
                             "am Ende" if r["am_ende"] else "NICHT am Ende")
            for r in d["roller"]["roller"]])

        ziel = os.path.join(WURZEL, "screenshots")
        os.makedirs(ziel, exist_ok=True)
        seite.screenshot(path=os.path.join(
            ziel, "b3_%s_%d.png" % (kuerzel, breite)), full_page=False)
    finally:
        echte = [f for f in fehler
                 if not any(w.lower() in f.lower() for w in M.IGNORIEREN)]
        d["seitenfehler"] = echte[:5]
        ctx.close()

    print("   Schrift < 12 px: %d von %d gemessenen Textstellen"
          % (d["schrift"]["anzahl_klein"], d["schrift"]["gemessen"]))
    print("   Tippziele (Knoepfe) < 44 px: %d   |   Felder/Beschriftungen "
          "< 44 px: %d (getrennt gefuehrt, KEIN Knopfbefund)"
          % (d["tipp"]["anzahl_klein"], d["tipp"]["anzahl_felder_klein"]))
    print("   nur-Emoji ohne title/aria: %d  (mit title/aria: %d)"
          % (d["emoji"]["anzahl_ohne"], d["emoji"]["anzahl_mit"]))
    print("   quer, Regelwortlaut (scrollingElement): %s gegen %s -> %s"
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
    print("   Beschnitt ungewollt: %d  (gewollt rollbar: %d)"
          % (d["beschnitt"]["anzahl_schlimm"], d["beschnitt"]["anzahl_gewollt"]))
    vu = d["verdeckung_unten"]
    print("   Verdeckung am Dokumentende: %s"
          % (vu.get("hinweis") or "%d Bedienelemente in der Leistenzone (%s, "
             "Ueberstand %s px)" % (vu.get("anzahl", -1), vu.get("leiste"),
                                    vu.get("ueberstand"))))
    print("   Tabellen: %d, davon breiter als der Schirm: %d"
          % (len(d["tabellen"]), sum(1 for t in d["tabellen"] if t["ueber"])))
    print("   Mengen: %d Knoepfe, %d Felder, %d Auswahlfelder"
          % (d["mengen"]["knoepfe"], d["mengen"]["felder"],
             d["mengen"]["auswahl"]))
    return d, offen, fehler


def main(argv):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt - pip install playwright && "
              "playwright install chromium")
        return 2

    nur = None
    if "--nur" in argv:
        nur = argv[argv.index("--nur") + 1]
    ziel_json = None
    if "--json" in argv:
        ziel_json = argv[argv.index("--json") + 1]

    datei = os.environ.get("EPK_INDEX", "index.html")
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port, datei)
    print("Gemessen wird: %s" % url)
    try:
        import hashlib
        h = hashlib.md5(io.open(os.path.join(WURZEL, datei), "rb").read()
                        ).hexdigest()
        print("md5 der gemessenen Datei: %s" % h)
    except Exception as e:
        print("md5 nicht bestimmbar: %s" % e)

    alles, offen = [], []
    listen = [nur] if nur else list(ANSICHTEN)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for kuerzel in listen:
            for breite, hoehe in BREITEN:
                d, o, _ = _lauf(browser, url, kuerzel, breite, hoehe)
                alles.append(d)
                offen += o
        browser.close()

    if ziel_json:
        io.open(ziel_json, "w", encoding="utf-8", newline="\n").write(
            json.dumps({"md5": h, "datei": datei, "laeufe": alles,
                        "offen": offen}, indent=1, ensure_ascii=False))
        print("\nJSON: %s" % ziel_json)

    print("\n" + "=" * 70)
    print("ZUSAMMENFASSUNG")
    print("=" * 70)
    for d in alles:
        if d.get("nicht_erreichbar"):
            print("  %-10s %5d  NICHT ERREICHBAR" % (d["ansicht"], d["breite"]))
            continue
        vu = d["verdeckung_unten"]
        print("  %-10s %5d  Schrift<12 %3d | Tipp<44 %3d | Emoji %2d | "
              "quer %-11s | Beschnitt %2d | Verdeckt %s | Tab>Schirm %d"
              % (d["ansicht"], d["breite"], d["schrift"]["anzahl_klein"],
                 d["tipp"]["anzahl_klein"], d["emoji"]["anzahl_ohne"],
                 "%d>%d" % (d["quer"]["scrollWidth"], d["quer"]["innerWidth"])
                 if d["quer"]["rollt"] else "nein",
                 d["beschnitt"]["anzahl_schlimm"],
                 ("-" if vu.get("leiste") is None else vu.get("anzahl")),
                 sum(1 for t in d["tabellen"] if t["ueber"])))

    if offen:
        print("\nNICHT GEMESSEN (das sind KEINE bestandenen Faelle):")
        for z in offen:
            print("   " + z)
        return 1
    print("\nAlle Koeder haben angeschlagen - die Zahlen oben sind Messwerte.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
