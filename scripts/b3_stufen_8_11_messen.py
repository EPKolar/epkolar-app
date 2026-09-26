# -*- coding: utf-8 -*-
"""B3 Stufen 8-11: vier Ansichten am GERENDERTEN Schirm messen, je 390 UND 1440.

WOZU
────
Fortsetzung von `b3_vier_ansichten_messen.py` (Stufen 4-7). Dieselben SIEBEN
Regeln, dieselben acht Koeder, dieselbe Saat - nur andere Ansichten:

    Projektakte/Berichte · Projektakte/Bautagebuch · Projektakte/Material ·
    Projektakte/Plaene · Arbeitsscheine-LISTE

WAS HIER ZUSAETZLICH GEMESSEN WIRD (und in Stufe 4-7 fehlte)
────────────────────────────────────────────────────────────
  beschnitt_echt  Der Melder aus Stufe 4-7 kennt nur `scrollWidth >
                  clientWidth`. Das trennt NICHT zwischen
                  (a) `overflow:hidden` + gekuerztem Text - da geht ein
                      Pixel verloren -, und
                  (b) einem KASTENUEBERLAUF bei `overflow:visible`, wo der
                      Text ausserhalb des Kastens GEZEICHNET wird und nichts
                      verloren geht.
                  Gemessen wird deshalb das Rechteck des TEXTES ueber
                  Range.getClientRects gegen den ersten wirklich
                  beschneidenden Vorfahren (Vorbild: b7_syncknopf_messen.py).
                  ZWEI Koeder: einer, der wirklich kuerzt, und einer, der nur
                  ueberlaeuft. Der Melder muss BEIDE richtig einordnen -
                  ein Melder, der alles "abgeschnitten" nennt, hat recht,
                  ohne zu messen.
  dunkelflaeche   Im HELLMODUS: jede Flaeche mit gesetztem Hintergrund, deren
                  gegen den Untergrund GEMISCHTE Helligkeit unter 0,5 liegt,
                  ab 8000 px2, mit ihrem ANTEIL am Schirm. Urteil ab 25 %
                  (Vorbild: hellmodus_messen.py, samt dessen drei behobenen
                  Messfehlern: durchsichtig ist nicht schwarz; Alpha muss
                  gemischt werden; geurteilt wird nach Anteil, nicht Farbe).
  bestandsschutz  Fuer die Arbeitsschein-Liste die HARTE Pruefliste aus
                  docs/GRUNDSTAND_UI_v3.9.930.md: ELF Statuswerte, SIEBEN
                  Sortierkriterien, ACHT Schnellfilter-Chips, Suchfeld,
                  vier Unterreiter, OFFA-Excel.
  offa            Der OFFA-Hinweis in der Liste: Wortlaut, Schriftgroesse,
                  Bedingung, und ob man von ihm aus zu den betroffenen
                  Scheinen GELANGEN kann (Klickhorcher, role, tabIndex,
                  Knoepfe im Band).

WAS NICHT GEMESSEN WIRD
───────────────────────
  * Rollen-Gatter. Gefahren wird role=admin, monteurId=M1. Ein Monteur sieht
    in der Projektakte weniger Unterseiten (_allNav traegt pm-Rechte) und in
    VMaterial/VPlan/VBautag weniger Knoepfe.
  * Echte Serverdaten. REST/Auth werden abgebrochen. VBautag (btEntries),
    VMaterial (orders) und VDoku laden ihre Zeilen vom SERVER - sie sind in
    diesem Aufbau LEER. Das wird als leere Grundgesamtheit AUSGEWIESEN und
    nicht als "in Ordnung" gemeldet.
  * Der zweite Reiter von VMaterial (Warenkorb/Lager) wird nur dann
    mitgemessen, wenn --mat-tab gesetzt ist.
  * Farbkontrast von TEXT. Gemessen wird nur die Flaeche (siehe oben).
  * Die Tastaturbedienung.

DIE KOEDER
──────────
K1-K8 kommen unveraendert aus b3_vier_ansichten_messen.py (dort im Kopf
beschrieben und in `_koeder()` gefahren). Dazu hier:

  K9  Beschnitt-Einordnung  zwei Baits: (a) 80 px `overflow:hidden` mit
      240 Zeichen MUSS als "gekuerzt" gelten, (b) ein 60 px breiter
      `overflow:visible`-Kasten mit langem Text MUSS als "nur
      Kastenueberlauf, nichts verloren" gelten. Beide Urteile muessen
      stimmen, sonst ist der Melder stumm oder ueberempfindlich.
  K10 OFFA-Hinweis  die Saat enthaelt GENAU ZWEI Scheine, die
      `_isOffaVerwaist` erfuellen (juprowa_id + juprowa_sync_at 30 Tage alt +
      Status in AS_GRP_OFFEN + `epk_last_juprowa_pull` neuer als der sync).
      Das Band MUSS erscheinen und die Zahl 2 nennen. Erscheint es nicht,
      ist der IST-Stand des Hinweises NICHT GEMESSEN.
  K11 Projektakte erreicht  die Huelle `.proj-shell` muss nach jedem
      Navigationsschritt noch stehen, und die Ansicht wird ueber ein
      INHALTLICHES Merkmal belegt, nicht ueber den Klick (Messfehler 4 aus
      B3_STUFEN_4_7.md: der Klick bewies die falsche Seite).
  K12 Dunkelflaeche  derselbe Lauf mit epk_theme='dark' MUSS eine tragende
      dunkle Flaeche melden. Tut er das nicht, misst der Melder keine Farbe.

AUFRUF
──────
    set EPK_INDEX=_mess_stand_942.html
    python scripts/b3_stufen_8_11_messen.py --json b3_8_11.json
    python scripts/b3_stufen_8_11_messen.py --nur as_liste
    EPK_BREITEN="390,1440" python scripts/b3_stufen_8_11_messen.py

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

BREITEN = B.BREITEN

# ══════════════════════════════════════════════════════════════════════════
# Saat: die aus Stufe 4-7, erweitert um das, was die Projekt-Unterseiten und
# der OFFA-Hinweis brauchen.
# ══════════════════════════════════════════════════════════════════════════

# Ein 4x4-PNG als Planblatt. Ein echtes Bild, damit PlanViewerCanvas seine
# Flaeche wirklich aufspannt - mit einem leeren dataUrl bliebe der Zweig kalt.
_PNG = ("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABAAQMAAACQp+OdAAAA"
        "BlBMVEX///+/v7+jQ3Y5AAAAKklEQVQoz2NgQAX8/xkYGBgY/jMwMDAwMPxnYGBgYGD4"
        "z8DAwMDA8B8AFQwCASsCUbEAAAAASUVORK5CYII=")


def _iso_vor(tage):
    import datetime
    return (datetime.datetime.now()
            - datetime.timedelta(days=tage)).isoformat(timespec="seconds") + "Z"


def _scheine8():
    """Die sechs Scheine aus Stufe 4-7, aber ZWEI davon OFFA-verwaist.

    Verwaist heisst laut _isOffaVerwaist: juprowa_id gesetzt,
    juprowa_sync_at gesetzt und aelter als OFFA_VERWAIST_TAGE (7),
    scheinstatus in AS_GRP_OFFEN, und der letzte Pull liegt NACH dem sync.
    Der letzte Pull wird ueber localStorage epk_last_juprowa_pull gesetzt.
    """
    s = B._scheine()
    for k in (0, 1):                      # S1 freigegeben, S2 in_bearbeitung
        s[k]["juprowa_id"] = "JUP-%04d" % (7700 + k)
        s[k]["juprowa_sync_at"] = _iso_vor(30)
    # Gegenprobe im Datensatz selbst: S3 ist juprowa-gebunden, aber FRISCH -
    # er darf NICHT mitzaehlen. Ohne diesen Fall wuerde ein Melder, der
    # einfach alle juprowa-Scheine zaehlt, dieselbe 2 liefern wie der richtige.
    s[2]["juprowa_id"] = "JUP-7702"
    s[2]["juprowa_sync_at"] = _iso_vor(1)
    return s


def _eintraege8():
    """Wie in Stufe 4-7, aber mit pid/p - sonst findet VBer keine Zeile.

    Der ODB-Mapper in der App liest `x.pid||x.p`; die Saat aus Stufe 4-7
    fuehrte nur `project_id`. Ein VBer ueber eine leere Menge sieht wie ein
    Ist-Zustand aus und ist keiner.
    """
    aus = B._eintraege()
    for k, e in enumerate(aus):
        pid = B.PROJEKTE[k % 2]["id"]
        e["pid"] = pid
        e["p"] = pid
        e["project_id"] = pid
        e["w"] = e.get("worker", "M1")
        e["date"] = e.get("datum", "")
        e["stunden"] = e.get("hours", 8)
        e["gw"] = "elektro"
    return aus


def _plandaten():
    return {
        "plans": [
            {"id": "PL1", "pid": "P1", "name": "Erdgeschoss Elektro Rev. B",
             "geschoss": "Erdgeschoss", "dataUrl": _PNG, "isPdf": False,
             "archived": False, "hochgeladen": _iso_vor(20), "rev": 2},
            {"id": "PL2", "pid": "P1", "name": "1. Obergeschoss Datennetz",
             "geschoss": "1. Obergeschoss", "dataUrl": _PNG, "isPdf": False,
             "archived": False, "hochgeladen": _iso_vor(11), "rev": 1},
        ],
        "tickets": [
            {"id": "T1", "pid": "P1", "planId": "PL1", "x": 22, "y": 40,
             "titel": "Steckdose fehlt neben Verteiler",
             "beschreibung": "Doppelsteckdose 30 cm rechts vom Verteiler "
                             "nachruesten, Zuleitung liegt bereits",
             "status": "offen", "assignee": "M1", "layer": "elektro",
             "erstellt": _iso_vor(6), "prio": "hoch"},
            {"id": "T2", "pid": "P1", "planId": "PL1", "x": 71, "y": 63,
             "titel": "Leuchte falsch positioniert",
             "beschreibung": "Abhaengung 40 cm nach Sueden",
             "status": "erledigt", "assignee": "M2", "layer": "elektro",
             "erstellt": _iso_vor(13), "prio": "normal"},
            {"id": "T3", "pid": "P1", "planId": "PL2", "x": 50, "y": 50,
             "titel": "Datendose Cat.7 statt Cat.6",
             "beschreibung": "Ausschreibung verlangt Cat.7",
             "status": "offen", "assignee": "M3", "layer": "daten",
             "erstellt": _iso_vor(3), "prio": "sehr hoch"},
        ],
    }


def _formulare():
    return {
        "maengel": [
            {"id": "MG1", "pid": "P1", "titel": "Brandschott offen",
             "status": "offen", "prio": "hoch", "erstellt": _iso_vor(9),
             "melder": "M1", "beschreibung": "Durchbruch Steigschacht 2. OG"},
            {"id": "MG2", "pid": "P1", "titel": "Verteilerdeckel fehlt",
             "status": "behoben", "prio": "normal", "erstellt": _iso_vor(22),
             "melder": "M2", "beschreibung": ""},
        ],
    }


# SEED2: eigener Saat-Melder, weil SEED_JS nur ARRAYS zurueckliest (-2 bei
# einem Objekt). planData und forms sind Objekte; ihre Saat waere mit dem
# alten Rueckleser ununterscheidbar von einem Fehlschlag, und "die Saat kam
# nicht an" waere dann eine Eigenschaft des Werkzeugs.
SEED2_JS = r"""
(async (cfg) => {
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
  const gelesen = {};
  for (const store of Object.keys(cfg.daten)) {
    if (vorhanden.indexOf(store) < 0) { gelesen[store] = 'FEHLT'; continue; }
    gelesen[store] = await new Promise((res) => {
      const tx = db.transaction(store, 'readonly');
      const rq = tx.objectStore(store).get('data');
      rq.onsuccess = () => {
        const v = rq.result;
        if (Array.isArray(v)) return res('array:' + v.length);
        if (v && typeof v === 'object') {
          const t = {};
          Object.keys(v).forEach(k => {
            t[k] = Array.isArray(v[k]) ? v[k].length : typeof v[k];
          });
          return res('objekt:' + JSON.stringify(t));
        }
        return res('leer:' + String(v));
      };
      rq.onerror = () => res('LESEFEHLER');
    });
  }
  return {gelesen: gelesen, fehlend: fehlend, stores: vorhanden.length};
})
"""


# ══════════════════════════════════════════════════════════════════════════
# Navigation
# ══════════════════════════════════════════════════════════════════════════

# Die Projektkarte ist ein NACKTER div - React haengt den Horcher an, das
# Markup verraet ihn nicht. Es gibt kein [role=button] und kein onclick-
# Attribut. Gesucht wird darum ueber die EIGENSCHAFT (die Karte traegt
# "Stunden" und "Gewerk"), und geklickt wird das kleinste passende Blatt;
# der Klick steigt auf.
PROJ_OEFFNEN_JS = r"""() => {
  const k = Array.from(document.querySelectorAll('div')).filter(e => {
    const t = (e.innerText || '');
    const r = e.getBoundingClientRect();
    return t.includes('Stunden') && t.includes('Gewerk')
           && r.height > 80 && r.height < 460;
  });
  if (!k.length) return {ok: false, grund: 'keine Projektkarte gefunden'};
  k.sort((a, b) => a.getBoundingClientRect().height
                 - b.getBoundingClientRect().height);
  const txt = (k[0].innerText || '').split(String.fromCharCode(10))[0].trim();
  k[0].click();
  return {ok: true, karten: k.length, geklickt: txt.slice(0, 40)};
}"""

# NUR .sidebar. `.proj-shell button[title]` faengt auch die HAUPTREITER der
# unteren Leiste (.tab-bar.pf-hauptnav) - ein Klick darauf verlaesst das
# Projekt, und danach findet man in den Unterseiten keinen Knopf mehr.
# Die .sidebar ist unter 601 px `display:none !important`; ihre Knoepfe
# existieren aber im Baum, und .click() loest den React-Horcher aus. Das ist
# hier gewollt: gemessen wird die ANSICHT, nicht der Weg dorthin - fuer den
# Weg gibt es scripts/projektakte_nav_probe.py.
PROJ_NAV_JS = r"""(label) => {
  const sb = document.querySelector('.proj-shell .sidebar');
  if (!sb) return {ok: false, grund: 'keine .proj-shell .sidebar'};
  const k = Array.from(sb.querySelectorAll('button[title]'))
    .filter(b => b.getAttribute('title') === label);
  if (!k.length) {
    return {ok: false, grund: 'kein Sidebar-Knopf mit title=' + label,
            vorhanden: Array.from(sb.querySelectorAll('button[title]'))
              .map(b => b.getAttribute('title'))};
  }
  k[0].click();
  return {ok: true, treffer: k.length};
}"""

HUELLE_JS = r"""() => ({
  shell: !!document.querySelector('.proj-shell'),
  main: !!document.querySelector('.proj-main'),
  sidebarKnoepfe: document.querySelectorAll('.proj-shell .sidebar button[title]').length
})"""

# INHALTLICHE Nachweise. Messfehler 4 aus B3_STUFEN_4_7.md: der Klick bewies
# die falsche Seite, und der Nachweis war gruen, weil er nur etwas pruefte,
# was auf mehrere Seiten zutrifft. Jeder Nachweis hier nennt ein Merkmal, das
# NUR diese Unterseite hat - und zusaetzlich die Abwesenheit des Merkmals der
# Nachbarseite, wo Verwechslungsgefahr besteht.
ANSICHT_DA8_JS = r"""(art) => {
  const wz = document.querySelector('.proj-main') || document.getElementById('root');
  const t = ((wz && wz.innerText) || '');
  const knopf = s => Array.from(document.querySelectorAll('button'))
    .some(b => (b.textContent || '').indexOf(s) >= 0);
  if (art === 'berichte')
    return {marke: 'H2 "Wochenbericht" + KW-Untertitel, und KEIN Bautagebuch-Merkmal',
            da: /Wochenbericht/.test(t) && /KW/.test(t) && !/Bautagebuch/.test(t)};
  if (art === 'bautagebuch')
    return {marke: 'Wortmarke "Bautagebuch" in der Unterseite',
            da: /Bautagebuch/.test(t)};
  if (art === 'material')
    return {marke: 'Material-Reiter (Warenkorb/Lager) bzw. Wortmarke Anforderung',
            da: /Warenkorb|Anforderung|Material/.test(t)
                && !/Wochenbericht/.test(t)};
  if (art === 'plaene')
    return {marke: 'Plan-Wortmarke + Geschoss-Auswahl bzw. Plan-Kachel',
            da: (/Plan|Pläne|Geschoss/.test(t)) && !/Wochenbericht/.test(t)};
  if (art === 'as_liste') {
    // Die Liste, NICHT das Formular: .as-form-grid darf es nicht geben.
    const kacheln = Array.from(document.querySelectorAll('*'))
      .filter(e => e.children.length === 0
                && /^(Gesamt|Offen \(alle\)|Fertig \(alle\))$/
                     .test((e.textContent || '').trim())).length;
    return {marke: '11 Statuskacheln + Sortier-Auswahlfeld, und KEIN .as-form-grid',
            da: kacheln >= 2 && !document.querySelector('.as-form-grid')
                && /Suche Nr, Kunde, Arbeit/.test(
                     Array.from(document.querySelectorAll('input'))
                       .map(i => i.getAttribute('placeholder') || '').join('|')),
            kopfkacheln: kacheln};
  }
  return {marke: '?', da: false};
}"""

# Der AS-Unterreiter "Liste" - er ist die Voreinstellung, wird aber sicher
# angetippt, damit ein stehengebliebener Reiter (Dispo/Kalender aus einem
# frueheren Schritt) die Messung nicht verschiebt.
# Die vier Unterzustaende von VPlan (viewer / tickets / layers / upload).
# Sie sind bei 390 px eine Reihe von Ikonen-Knoepfen. Eine Ansicht, die nur
# in ihrem Startzustand gemessen wird, ist zu einem Viertel gemessen - und
# genau in einem der anderen drei steht die fest eingetragene Farbe
# `#0a0c14` (Plan-Kachel, 140 px hoch) aus dem Quelltext.
_VPLAN_REIHE = r"""
  const _reihe = () => {
    // Erster Anlauf nahm "die flachste Reihe aus 3-6 Geschwister-Knoepfen"
    // und traf damit die STATUS-Chips (Alle/Offen/Erledigt) - drei Reiter
    // wurden gemessen, die keine sind, und die Unterzustaende blieben
    // unbesucht. Gesucht wird jetzt ueber ein Merkmal, das NUR diese Reihe
    // hat: der erste Eintrag traegt die Karten-Ikone U+1F5FA.
    const alle = Array.from(document.querySelectorAll('.proj-main div'))
      .filter(e => {
        const b = Array.from(e.children).filter(k => k.tagName === 'BUTTON');
        if (b.length < 3 || b.length > 6) return false;
        return b.some(x => (x.textContent || '').indexOf('\u{1F5FA}') >= 0);
      });
    if (!alle.length) return null;
    alle.sort((a, b) => a.getBoundingClientRect().height
                      - b.getBoundingClientRect().height);
    return alle[0];
  };
"""

VPLAN_REITER_JS = r"""() => {
""" + _VPLAN_REIHE + r"""
  const reihe = _reihe();
  if (!reihe) return {ok: false, grund: 'keine VPlan-Unterreiter-Reihe '
                      + '(Merkmal: Karten-Ikone im ersten Eintrag)'};
  const b = Array.from(reihe.children).filter(k => k.tagName === 'BUTTON');
  return {ok: true, anzahl: b.length,
          knoepfe: b.map(x => ({
            text: (x.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 24),
            title: x.getAttribute('title'),
            aria: x.getAttribute('aria-label'),
            h: Math.round(x.getBoundingClientRect().height),
            w: Math.round(x.getBoundingClientRect().width)}))};
}"""

VPLAN_TIPPEN_JS = r"""(i) => {
""" + _VPLAN_REIHE + r"""
  const reihe = _reihe();
  if (!reihe) return false;
  const b = Array.from(reihe.children).filter(k => k.tagName === 'BUTTON');
  if (!b[i]) return false;
  b[i].click();
  return true;
}"""

# ══════════════════════════════════════════════════════════════════════════
# Bedeutung nur im Symbol - die ZWEITE Form, die der Melder aus Stufe 4-7
# nicht sehen kann
# ══════════════════════════════════════════════════════════════════════════
# EMOJI_JS fragt: "steht in der Beschriftung ein Buchstabe ODER eine ZIFFER?"
# Damit gilt ein Knopf, dessen ganze Beschriftung `🎫3` ist, als beschriftet -
# er traegt ja eine Ziffer. Eine ZAHL ist aber keine Bedeutung: `🎫3` sagt
# "drei wovon?" und beantwortet es nicht. Genau so stehen die vier
# Unterreiter der Plan-Ansicht bei 390 px da (`!isMob&&...t.l` blendet die
# Beschriftung aus, title und aria-label gibt es nicht), und drei von vier
# rutschen am alten Melder vorbei, weil ihr Zaehler-Abzeichen eine Ziffer ist.
# Gemessen wird hier nach BUCHSTABEN.
EMOJI_ZAHL_JS = r"""() => {
  const BUCHSTABE = /\p{L}/u;
  const sicht = e => {
    const r = e.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return false;
    const c = getComputedStyle(e);
    return c.visibility !== 'hidden' && c.display !== 'none';
  };
  const weg = e => {
    const t = []; let x = e;
    while (x && x.nodeType === 1 && t.length < 4) {
      let s = x.tagName.toLowerCase();
      const k = (x.className && typeof x.className === 'string')
        ? x.className.trim().split(/\s+/)[0] : '';
      if (k) s += '.' + k;
      t.unshift(s); x = x.parentElement;
    }
    return t.join(' > ');
  };
  const ohne = [], mit = [];
  document.querySelectorAll('button, [role="button"], a, summary')
    .forEach(e => {
      if (!sicht(e)) return;
      const roh = (e.textContent || '').replace(/\s+/g, ' ').trim();
      if (!roh) return;
      if (BUCHSTABE.test(roh)) return;      // traegt ein Wort -> kein Befund
      const t = e.getAttribute('title'), a = e.getAttribute('aria-label');
      const x = {zeichen: roh, title: t, aria: a, weg: weg(e),
                 hat_ziffer: /\p{N}/u.test(roh),
                 h: Math.round(e.getBoundingClientRect().height),
                 w: Math.round(e.getBoundingClientRect().width)};
      if (t || a) mit.push(x); else ohne.push(x);
    });
  return {ohne_hilfe: ohne, anzahl_ohne: ohne.length,
          nur_mit_zaehler: ohne.filter(x => x.hat_ziffer).length,
          mit_hilfe: mit, anzahl_mit: mit.length};
}"""

# Der Koeder dazu: ein Knopf, dessen ganze Beschriftung `🔩7` ist. Der alte
# Melder MUSS ihn durchlassen (Ziffer = Text), der neue MUSS ihn fangen.
# Faengt der neue ihn nicht, misst er dieselbe Menge wie der alte und ist
# ueberfluessig; faengt der ALTE ihn, dann hat der alte Melder die Luecke
# nicht, die hier behauptet wird.
KOEDER_EMOJIZAHL_EIN = r"""() => {
  const w = document.getElementById('root') || document.body;
  let z = document.getElementById('__kz_zone');
  if (!z) { z = document.createElement('div'); z.id = '__kz_zone'; w.appendChild(z); }
  z.innerHTML = '';
  const b = document.createElement('button');
  b.id = '__k_zahl';
  b.textContent = '\u{1F529}7';
  z.appendChild(b);
  return b.textContent;
}"""

KOEDER_EMOJIZAHL_AUS = r"""() => {
  const z = document.getElementById('__kz_zone');
  if (z && z.parentElement) z.parentElement.removeChild(z);
  return !document.getElementById('__kz_zone');
}"""

# VMaterial oeffnet fuer einen Admin auf dem Reiter "Lager" - und der laedt
# seine Zeilen vom SERVER, der in diesem Aufbau abgebrochen wird. Die Ansicht
# ist dort LEER ("Keine offenen Anforderungen"). Eine leere Grundgesamtheit
# ist kein Bestehen: gemessen wird darum zusaetzlich der Reiter "Warenkorb",
# der seinen Inhalt aus einem eingebauten Katalog nimmt und nichts vom
# Server braucht.
REITER_TIPPEN_JS = r"""(name) => {
  const wz = document.querySelector('.proj-main') || document.body;
  const k = Array.from(wz.querySelectorAll('button'))
    .filter(b => (b.textContent || '').indexOf(name) >= 0)
    .filter(b => b.getBoundingClientRect().height > 4);
  if (!k.length) return false;
  k[0].click();
  return true;
}"""

AS_LISTE_JS = r"""() => {
  const k = Array.from(document.querySelectorAll('.tab-bar button'))
    .filter(b => /Liste/.test(b.textContent || ''));
  if (!k.length) return 'kein-Liste-Reiter';
  k[0].click();
  return 'geklickt/' + k.length;
}"""


# ══════════════════════════════════════════════════════════════════════════
# Beschnitt: (a) wirklich gekuerzt gegen (b) nur Kastenueberlauf
# ══════════════════════════════════════════════════════════════════════════
BESCHNITT_ECHT_JS = r"""() => {
  const _cs = e => getComputedStyle(e);
  const _weg = e => {
    const t = []; let x = e;
    while (x && x.nodeType === 1 && t.length < 5) {
      let s = x.tagName.toLowerCase();
      if (x.id) { s += '#' + x.id; t.unshift(s); break; }
      const k = (x.className && typeof x.className === 'string')
        ? x.className.trim().split(/\s+/).slice(0, 2).join('.') : '';
      if (k) s += '.' + k;
      t.unshift(s); x = x.parentElement;
    }
    return t.join(' > ');
  };
  // Der erste Vorfahr (das Element SELBST eingeschlossen), der einen
  // Ueberlauf tatsaechlich beschneidet. Beim Elternteil anzufangen war in
  // b7_syncknopf_messen.py der erste Fehler: der Koeder, der sich SELBST
  // beschneidet, galt dann als "0 px verloren".
  const beschneider = (el) => {
    let e = el;
    while (e && e !== document.documentElement) {
      const cs = _cs(e);
      const ox = cs.overflowX, oy = cs.overflowY;
      if (['hidden', 'clip', 'auto', 'scroll'].indexOf(ox) >= 0 ||
          ['hidden', 'clip', 'auto', 'scroll'].indexOf(oy) >= 0)
        return {el: e, ox: ox, oy: oy, r: e.getBoundingClientRect(),
                weg: _weg(e)};
      e = e.parentElement;
    }
    return null;
  };
  // Das Rechteck, das der TEXT einnimmt - nicht das des Kastens.
  const textRechteck = (el) => {
    let l = Infinity, r = -Infinity, n = 0;
    const lauf = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    let k;
    while ((k = lauf.nextNode())) {
      if (!String(k.nodeValue || '').trim()) continue;
      const rg = document.createRange();
      rg.selectNodeContents(k);
      for (const re of rg.getClientRects()) {
        if (re.width <= 0 && re.height <= 0) continue;
        l = Math.min(l, re.left); r = Math.max(r, re.right); n++;
      }
    }
    return n ? {left: l, right: r} : null;
  };
  const wurzel = document.getElementById('root') || document.body;
  const gekuerzt = [], nur_ueberlauf = [], rollbar = [];
  wurzel.querySelectorAll('*').forEach(e => {
    if (e.scrollWidth <= e.clientWidth + 1) return;
    const roh = (e.textContent || '').replace(/\s+/g, ' ').trim();
    if (!roh) return;
    const cs = _cs(e);
    const b = beschneider(e);
    const tr = textRechteck(e);
    let verloren = 0, wo = '-';
    if (tr && b) {
      const ueber = Math.max(0, tr.right - b.r.right)
                  + Math.max(0, b.r.left - tr.left);
      if (ueber > 0.5) { verloren = Math.round(ueber * 10) / 10; wo = b.weg; }
    }
    if (tr) {
      const raus = Math.max(0, tr.right - innerWidth) + Math.max(0, -tr.left);
      if (raus > verloren) { verloren = Math.round(raus * 10) / 10; wo = 'Fensterrand'; }
    }
    const eintrag = {tag: e.tagName.toLowerCase(), text: roh.slice(0, 50),
                     scroll: e.scrollWidth, sicht: e.clientWidth,
                     eigen_overflowX: cs.overflowX,
                     textOverflow: cs.textOverflow,
                     beschneider: b ? (b.weg + ' overflow-x:' + b.ox) : 'KEINER',
                     verloren_px: verloren, verloren_an: wo, weg: _weg(e)};
    if (['auto', 'scroll'].indexOf(cs.overflowX) >= 0) rollbar.push(eintrag);
    else if (verloren > 0.5) gekuerzt.push(eintrag);
    else nur_ueberlauf.push(eintrag);
  });
  gekuerzt.sort((a, b) => b.verloren_px - a.verloren_px);
  return {gekuerzt: gekuerzt.slice(0, 25), anzahl_gekuerzt: gekuerzt.length,
          nur_ueberlauf: nur_ueberlauf.slice(0, 20),
          anzahl_nur_ueberlauf: nur_ueberlauf.length,
          rollbar: rollbar.slice(0, 10), anzahl_rollbar: rollbar.length};
}"""

# K9: ZWEI Baits. Der erste MUSS als gekuerzt gelten, der zweite MUSS als
# blosser Kastenueberlauf gelten. Ein Melder, der beide "abgeschnitten" nennt,
# waere bei jedem Kastenueberlauf rot und damit unbrauchbar.
KOEDER_BESCH2_EIN = r"""() => {
  const w = document.getElementById('root') || document.body;
  let z = document.getElementById('__kb_zone');
  if (!z) { z = document.createElement('div'); z.id = '__kb_zone'; w.appendChild(z); }
  z.innerHTML = '';
  const a = document.createElement('div');
  a.id = '__kb_hart';
  a.style.cssText = 'width:80px;overflow:hidden;white-space:nowrap;' +
    'text-overflow:clip;font-size:13px';
  a.textContent = 'HART' + 'x'.repeat(240);
  z.appendChild(a);
  const b = document.createElement('div');
  b.id = '__kb_weich';
  b.style.cssText = 'width:60px;overflow:visible;white-space:nowrap;' +
    'font-size:13px';
  b.textContent = 'WEICH' + 'y'.repeat(40);
  z.appendChild(b);
  return {hart: {scroll: a.scrollWidth, sicht: a.clientWidth},
          weich: {scroll: b.scrollWidth, sicht: b.clientWidth}};
}"""

KOEDER_BESCH2_AUS = r"""() => {
  const z = document.getElementById('__kb_zone');
  if (z && z.parentElement) z.parentElement.removeChild(z);
  return !document.getElementById('__kb_zone');
}"""


# ══════════════════════════════════════════════════════════════════════════
# Feste dunkle Flaechen im HELLMODUS
# ══════════════════════════════════════════════════════════════════════════
DUNKEL_JS = r"""() => {
  const kanaele = (c) => {
    const m = /rgba?\((\d+), ?(\d+), ?(\d+)(?:, ?([\d.]+))?/.exec(c || '');
    if (!m) return null;
    return {r: +m[1], g: +m[2], b: +m[3],
            a: m[4] === undefined ? 1 : parseFloat(m[4])};
  };
  const hell = (c) => {
    const k = kanaele(c);
    if (!k) return null;
    if (k.a === 0) return null;          // durchsichtig ist nicht schwarz
    const f = [k.r, k.g, k.b].map(v => {
      const x = v / 255;
      return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2];
  };
  const untergrund = (el) => {
    let e = el.parentElement;
    while (e) {
      const k = kanaele(getComputedStyle(e).backgroundColor);
      if (k && k.a >= 0.999) return k;
      e = e.parentElement;
    }
    return {r: 255, g: 255, b: 255, a: 1};
  };
  const gemischt = (el, c) => {
    const k = kanaele(c);
    if (!k) return null;
    if (k.a >= 0.999) return c;
    const u = untergrund(el);
    const f = (x, y) => Math.round(k.a * x + (1 - k.a) * y);
    return 'rgb(' + f(k.r, u.r) + ', ' + f(k.g, u.g) + ', ' + f(k.b, u.b) + ')';
  };
  const gross = [];
  const schirm = Math.max(1, innerWidth * innerHeight);
  document.querySelectorAll('*').forEach(el => {
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none') return;
    if (parseFloat(cs.opacity || '1') < 0.1) return;
    const roh = cs.backgroundColor;
    if (!roh || roh === 'rgba(0, 0, 0, 0)' || roh === 'transparent') return;
    const c = gemischt(el, roh);
    const h = hell(c);
    if (h === null || h >= 0.5) return;
    const r = el.getBoundingClientRect();
    const fl = Math.round(r.width * r.height);
    if (fl < 8000) return;
    gross.push({tag: el.tagName.toLowerCase(),
                klasse: String(el.className || '').slice(0, 50),
                farbe: c, roh: roh,
                helligkeit: Math.round(h * 1000) / 1000,
                flaeche: fl, anteil: Math.round(fl / schirm * 1000) / 1000,
                breit: Math.round(r.width), hoch: Math.round(r.height),
                oben: Math.round(r.top),
                text: String(el.innerText || '').replace(/\s+/g, ' ').slice(0, 50)});
  });
  gross.sort((a, b) => b.flaeche - a.flaeche);
  // Zusaetzlich, und OHNE Flaechenschwelle: jede FEST eingetragene dunkle
  // Farbe der Datei, die im Bild wirklich vorkommt. Die Schwelle 8000 px2
  // beantwortet "traegt sie den Schirm"; diese Liste beantwortet "gibt es
  // sie ueberhaupt". Ohne sie waere eine feste Farbe, die gerade klein
  // gerendert wird, unsichtbar - und "keine feste dunkle Farbe gefunden"
  // waere eine Aussage ueber den Zeitpunkt, nicht ueber die Datei.
  const FEST = ['rgb(10, 12, 20)', 'rgb(26, 26, 26)', 'rgb(15, 15, 15)'];
  const feste = [];
  document.querySelectorAll('*').forEach(el => {
    const cs = getComputedStyle(el);
    if (FEST.indexOf(cs.backgroundColor) < 0) return;
    const r = el.getBoundingClientRect();
    feste.push({farbe: cs.backgroundColor, tag: el.tagName.toLowerCase(),
                klasse: String(el.className || '').slice(0, 40),
                breit: Math.round(r.width), hoch: Math.round(r.height),
                flaeche: Math.round(r.width * r.height),
                anteil: Math.round(r.width * r.height / schirm * 1000) / 1000,
                sichtbar: cs.display !== 'none' && cs.visibility !== 'hidden',
                display: cs.display, oben: Math.round(r.top)});
  });
  return {dunkel: gross.slice(0, 12), anzahl: gross.length,
          feste_farben: feste, anzahl_feste: feste.length,
          tragend: gross.filter(g => g.anteil >= 0.25),
          theme: (localStorage.getItem('epk_theme') || '?'),
          textfarbe: getComputedStyle(document.body).color,
          huelle: (document.querySelector('.app-shell')
                   ? getComputedStyle(document.querySelector('.app-shell')).backgroundColor
                   : null)};
}"""


# ══════════════════════════════════════════════════════════════════════════
# Bestandsschutz Arbeitsschein-Liste + der OFFA-Hinweis
# ══════════════════════════════════════════════════════════════════════════
AS_BESTAND_JS = r"""() => {
  const sicht = e => {
    const r = e.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return false;
    const c = getComputedStyle(e);
    return c.visibility !== 'hidden' && c.display !== 'none';
  };
  const wurzel = document.getElementById('root') || document.body;
  const txt = (wurzel.innerText || '');
  // Die ELF Statuskacheln. Sie sind keine <button>, sondern Kpi-Karten;
  // gesucht wird nach ihrer BESCHRIFTUNG, weil die im Grundstand steht.
  const NAMEN = ['Gesamt', 'Offen (alle)', 'aufgenommen', 'freigegeben',
                 'in Bearbeitung', 'aufgeschoben', 'erledigt', 'abgerechnet',
                 'bar bezahlt', 'storniert', 'Fertig (alle)'];
  // NEUN der elf Kacheln tragen ihre Beschriftung als `v.i+" "+v.l`, also
  // EMOJI PLUS Wort ("📋 aufgenommen"). Ein Gleichheitsvergleich auf das
  // reine Wort fand deshalb im ersten Lauf nur 4 von 11 und haette SIEBEN
  // Regressionsfehler gemeldet, die keine sind. Verglichen wird jetzt der
  // Text nach Abzug aller Zeichen, die keine Buchstaben, Ziffern, Klammern
  // oder Leerzeichen sind.
  const norm = s => String(s || '').replace(/[^\p{L}\p{N}() .-]/gu, '')
                                   .replace(/\s+/g, ' ').trim().toLowerCase();
  // Gesucht wird IM Kachelband, nicht irgendwo auf der Seite: dieselben
  // Woerter stehen auch in den Optionen des Status-Auswahlfelds und im
  // OFFA-Excel-Menue. Eine Kachel, die es nicht gibt, waere sonst durch eine
  // Option "vorhanden" - und der Bestandsschutz waere blind.
  const band = wurzel.querySelector('.kpi-grid') || wurzel;
  const kacheln = {};
  NAMEN.forEach(n => { kacheln[n] = false; });
  Array.from(band.querySelectorAll('*')).forEach(e => {
    if (e.children.length) return;
    if (!sicht(e)) return;
    const t = norm(e.textContent);
    NAMEN.forEach(n => { if (norm(n) === t) kacheln[n] = true; });
  });
  // Die SIEBEN Sortierkriterien: am Telefon ein <select>, am Rechner
  // klickbare Tabellenkoepfe. BEIDE Wege werden erfasst - sonst meldet die
  // Messung bei 1440 px "vier von sieben fehlen", weil sie nur nach dem
  // Auswahlfeld gesehen hat.
  const SORT = ['Nummer', 'Erf.-Datum', 'Termin (best.)', 'Termin (vorg.)',
                'Status', 'Kunde', 'Monteur'];
  let sortSelect = null;
  Array.from(document.querySelectorAll('select')).forEach(s => {
    const o = Array.from(s.options).map(x => (x.textContent || '').trim());
    if (o.indexOf('Nummer') >= 0 && o.indexOf('Erf.-Datum') >= 0)
      sortSelect = {optionen: o, sichtbar: sicht(s), wert: s.value};
  });
  const kopfSort = Array.from(document.querySelectorAll('th'))
    .filter(sicht)
    .map(th => (th.textContent || '').replace(/[▲▼↕]/g, '').trim());
  // Bei 1440 px gibt es das Auswahlfeld NICHT - dort wird ueber die
  // klickbaren Tabellenkoepfe sortiert (toggleSort). Ein Zaehler, der nur
  // das Auswahlfeld kennt, meldete im ersten Lauf "0 von 7" und damit SIEBEN
  // Regressionsfehler, die keine sind. Die sieben Kriterien des Grundstands
  // heissen in der Kopfzeile teils anders; die Gleichsetzung steht hier
  // ausgeschrieben, damit sie nachlesbar ist und nicht geraten wird.
  const KOPF_GLEICH = {'Nummer': 'Nummer', 'Erf.-Datum': 'Erf.-Datum',
                       'Termin (best.)': 'Bestätigt',
                       'Termin (vorg.)': 'Vorgeschl.', 'Status': 'Status',
                       'Kunde': 'Kundenname', 'Monteur': 'Monteur'};
  const ueberKopf = SORT.filter(n => kopfSort.indexOf(KOPF_GLEICH[n]) >= 0);
  // Die ACHT Schnellfilter-Chips.
  const CHIPS = ['Alle', 'Offen', 'In Arbeit', 'Erledigt', 'Meine', 'Heute',
                 'Überfällig', 'Kein Monteur'];
  const chipTexte = Array.from(document.querySelectorAll('button'))
    .filter(sicht)
    .map(b => (b.textContent || '').replace(/[^\p{L}\p{N} .()\-]/gu, '').trim())
    .filter(Boolean);
  const chips = {};
  CHIPS.forEach(c => {
    chips[c] = chipTexte.some(t => t === c || t === c + ' ' || t.endsWith(c));
  });
  // Unterreiter und OFFA-Excel.
  const REITER = ['Liste', 'QR Scan', 'Kalender', 'Dispo'];
  const reiter = {};
  REITER.forEach(r => {
    reiter[r] = Array.from(document.querySelectorAll('.tab-bar button'))
      .filter(sicht).some(b => (b.textContent || '').indexOf(r) >= 0);
  });
  const suchfeld = Array.from(document.querySelectorAll('input'))
    .filter(sicht)
    .map(i => i.getAttribute('placeholder') || '')
    .filter(p => /Suche Nr, Kunde, Arbeit/.test(p));
  const alleSelects = Array.from(document.querySelectorAll('select'))
    .filter(sicht).map(s => ({
      wert: s.value, n: s.options.length,
      erste: Array.from(s.options).slice(0, 3)
        .map(o => (o.textContent || '').trim())}));
  return {
    statuskacheln: kacheln,
    statuskacheln_da: Object.keys(kacheln).filter(k => kacheln[k]).length,
    sort_select: sortSelect,
    sort_kopfzeile: kopfSort,
    sort_erfuellt: SORT.filter(n =>
      (sortSelect && sortSelect.optionen.indexOf(n) >= 0)
      || kopfSort.indexOf(KOPF_GLEICH[n]) >= 0).length,
    sort_ueber_auswahlfeld: sortSelect
      ? SORT.filter(n => sortSelect.optionen.indexOf(n) >= 0).length : 0,
    sort_ueber_kopfzeile: ueberKopf.length,
    chips: chips,
    chips_da: Object.keys(chips).filter(k => chips[k]).length,
    unterreiter: reiter,
    suchfeld: suchfeld,
    offa_excel: Array.from(document.querySelectorAll('button')).filter(sicht)
      .some(b => /OFFA Excel/.test(b.textContent || '')),
    auswahlfelder: alleSelects,
    zeilen_in_liste: document.querySelectorAll('tbody tr').length,
    text_laenge: txt.length
  };
}"""

# Der OFFA-Hinweis: wo steht er, was sagt er, und kommt man von ihm aus zu
# den betroffenen Scheinen? Die letzte Frage ist die eigentliche: ein Band,
# das eine ZAHL nennt, aber keinen Weg, ist eine Warnung ohne Ziel.
OFFA_JS = r"""() => {
  const wurzel = document.getElementById('root') || document.body;
  const treffer = [];
  wurzel.querySelectorAll('*').forEach(e => {
    const t = (e.textContent || '');
    if (!/in OFFA (prüfen|pruefen)/.test(t)) return;
    // nur das INNERSTE Element, das den Satz traegt
    if (Array.from(e.children).some(k => /in OFFA (prüfen|pruefen)/
        .test(k.textContent || ''))) return;
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    treffer.push({
      tag: e.tagName.toLowerCase(),
      wortlaut: t.replace(/\s+/g, ' ').trim(),
      fontSize: Math.round(parseFloat(cs.fontSize) * 10) / 10,
      farbe: cs.color, hintergrund: cs.backgroundColor, rahmen: cs.border,
      oben: Math.round(r.top), hoehe: Math.round(r.height),
      breite: Math.round(r.width),
      sichtbar: r.width > 1 && r.height > 1 && cs.display !== 'none',
      // Kommt man weiter? Drei Wege: eigener Horcher, role/tabIndex, Knopf
      // oder Verweis IM Band.
      role: e.getAttribute('role'),
      tabindex: e.getAttribute('tabindex'),
      cursor: cs.cursor,
      onclick_attr: e.getAttribute('onclick') ? 'ja' : 'nein',
      knoepfe_im_band: Array.from(e.querySelectorAll('button, a, [role="button"]'))
        .map(b => (b.textContent || '').trim().slice(0, 30)),
      eltern_knopf: !!e.closest('button, a, [role="button"]'),
      // React-Horcher sind im Markup unsichtbar. Die einzige Spur, die von
      // aussen messbar ist, ist der React-Props-Schluessel am DOM-Knoten.
      react_onclick: (() => {
        for (const k of Object.keys(e)) {
          if (k.indexOf('__reactProps') === 0) {
            const p = e[k];
            return !!(p && (p.onClick || p.onKeyDown));
          }
        }
        return null;
      })()
    });
  });
  // Und: welche Scheine sind es ueberhaupt? Die Funktion ist window-exportiert.
  let verwaiste = null;
  try {
    const pull = (window.__lastJuprowaPull
                  || parseInt(localStorage.getItem('epk_last_juprowa_pull'), 10)) || 0;
    verwaiste = {letzter_pull: pull, funktion_da: !!window._isOffaVerwaist};
  } catch (e) { verwaiste = {fehler: String(e).slice(0, 60)}; }
  return {treffer: treffer, anzahl: treffer.length, pull: verwaiste};
}"""


# ══════════════════════════════════════════════════════════════════════════
# Lauf
# ══════════════════════════════════════════════════════════════════════════
ANSICHTEN = {
    "berichte":    {"titel": "Projektakte / Berichte (Wochenbericht)",
                    "nav": "Berichte", "stufe": 8},
    "bautagebuch": {"titel": "Projektakte / Bautagebuch",
                    "nav": "Bautagebuch", "stufe": 8},
    "material":    {"titel": "Projektakte / Material",
                    "nav": "Material", "stufe": 9},
    "plaene":      {"titel": "Projektakte / Pläne",
                    "nav": "Pläne", "stufe": 10},
    "as_liste":    {"titel": "Arbeitsscheine / LISTE",
                    "nav": "Arbeitsscheine", "stufe": 11},
}


def _saeen8(seite):
    """Saat, zurueckgelesen und in der Ansicht nachgewiesen."""
    daten = {"monteure": B.MONTEURE, "arbeitsscheine": _scheine8(),
             "projects": B.PROJEKTE, "entries": _eintraege8(),
             "werkzeuge": B.WERKZEUGE,
             "planData": _plandaten(), "forms": _formulare()}
    erg = seite.evaluate(SEED2_JS, {"db": M.DB_NAME, "daten": daten})
    if erg.get("fehlend"):
        raise SystemExit("ABBRUCH: diese Speicher gibt es nicht: %s"
                         % ", ".join(erg["fehlend"]))
    for k, v in sorted(erg.get("gelesen", {}).items()):
        print("   zurueckgelesen  %-14s %s" % (k, v))
    schlecht = [k for k, v in erg["gelesen"].items()
                if str(v) in ("array:0", "FEHLT", "LESEFEHLER")
                or str(v).startswith("leer")]
    if schlecht:
        raise SystemExit("ABBRUCH: die Saat ist nicht angekommen (%s)."
                         % ", ".join(schlecht))
    # Der letzte Juprowa-Pull: OHNE ihn kann _isOffaVerwaist nie wahr werden
    # (letzte Zeile der Funktion: return !!(lastPullMs && lastPullMs>syncMs)).
    seite.evaluate("() => { try { localStorage.setItem("
                   "'epk_last_juprowa_pull', String(Date.now())); } "
                   "catch(e){} return localStorage.getItem("
                   "'epk_last_juprowa_pull'); }")
    seite.reload(wait_until="domcontentloaded")
    seite.wait_for_timeout(6800)
    t = seite.evaluate("() => document.body.innerText")
    treffer = len(B.SAATWORT.findall(t or ""))
    print("   K6 Saat in der Ansicht sichtbar: %d Treffer" % treffer)
    if not treffer:
        raise SystemExit("ABBRUCH (K6): die Saat liegt in der Datenbank, "
                         "erscheint aber in KEINER Ansicht.")
    return treffer


def _navigieren8(seite, kuerzel, breite, protokoll):
    ziel = ANSICHTEN[kuerzel]["nav"]
    if kuerzel == "as_liste":
        if breite < 600:
            seite.evaluate(M.NAV_OEFFNEN_JS)
            seite.wait_for_timeout(420)
            weg = seite.evaluate(B.NAV_MEHR_JS, ziel)
        else:
            weg = seite.evaluate(B.NAV_TOP_JS, ziel)
        seite.wait_for_timeout(2600)
        if breite < 600:
            print("   Mehr-Menue: %s" % seite.evaluate(B.MEHR_ZU_JS))
            seite.wait_for_timeout(700)
            rest = seite.evaluate(B.MEHR_OFFEN_JS)
            if rest:
                protokoll.append("Mehr-Menue noch offen (%d)" % rest)
        print("   Unterreiter Liste: %s" % seite.evaluate(AS_LISTE_JS))
        seite.wait_for_timeout(1400)
        return weg
    # ── Projektakte ────────────────────────────────────────────────────
    if breite < 600:
        seite.evaluate(M.NAV_OEFFNEN_JS)
        seite.wait_for_timeout(420)
        weg = seite.evaluate(B.NAV_MEHR_JS, "Projekte")
    else:
        weg = seite.evaluate(B.NAV_TOP_JS, "Projekte")
    seite.wait_for_timeout(2400)
    if breite < 600:
        seite.evaluate(B.MEHR_ZU_JS)
        seite.wait_for_timeout(600)
    auf = seite.evaluate(PROJ_OEFFNEN_JS)
    print("   Projekt oeffnen: %s" % auf)
    if not auf.get("ok"):
        return None
    seite.wait_for_timeout(2600)
    h = seite.evaluate(HUELLE_JS)
    print("   Huelle nach dem Eintreten: %s" % h)
    if not h["shell"]:
        return None
    nav = seite.evaluate(PROJ_NAV_JS, ziel)
    print("   Sidebar-Navigation nach '%s': %s" % (ziel, nav))
    if not nav.get("ok"):
        return None
    seite.wait_for_timeout(2600)
    h2 = seite.evaluate(HUELLE_JS)
    if not h2["shell"]:
        protokoll.append("Die Huelle .proj-shell ist nach dem Klick auf "
                         "'%s' verschwunden - das Projekt wurde verlassen."
                         % ziel)
        return None
    return "%s / %s" % (weg, ziel)


def _lauf(pw, url, kuerzel, breite, hoehe, thema="dark"):
    marke = "%s @ %dx%d %s" % (kuerzel, breite, hoehe, thema)
    print("\n── %s ─────────────────────────────" % marke)
    d = {"ansicht": kuerzel, "stufe": ANSICHTEN[kuerzel]["stufe"],
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
        "localStorage.setItem('epkolar_user',JSON.stringify(u));"
        "localStorage.setItem('epk_theme','%s');}catch(e){}" % thema)
    ctx.route("**/rest/v1/**", lambda r: r.abort())
    ctx.route("**/auth/v1/**", lambda r: r.abort())
    seite = ctx.new_page()
    seite.on("pageerror", lambda x: fehler.append(str(x)[:170]))
    try:
        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(3800)
        _saeen8(seite)
        weg = _navigieren8(seite, kuerzel, breite, protokoll)
        print("   Navigation: %s" % weg)
        if weg in (None, "nicht-gefunden"):
            d["nicht_erreichbar"] = True
            offen.append("%s: Ansicht nicht erreichbar (%s)" % (marke, weg))
            ctx.close()
            return d, offen, fehler
        nw = seite.evaluate(ANSICHT_DA8_JS, kuerzel)
        d["nachweis"] = nw
        print("   Ansicht belegt ueber %s: %s" % (nw["marke"], nw["da"]))
        if not nw["da"]:
            d["nicht_erreichbar"] = True
            offen.append("%s: INHALTLICHER Nachweis fehlgeschlagen (%s) - der "
                         "Klick allein beweist die Seite nicht." % (marke, nw))
            ctx.close()
            return d, offen, fehler

        if thema == "light":
            # Im Hellmodus wird NUR die Flaechenfarbe gemessen. Die sieben
            # Regeln haengen nicht am Thema; sie zweimal zu fahren waere
            # doppelte Zeit fuer dieselbe Zahl.
            d["dunkel"] = seite.evaluate(DUNKEL_JS)
            # ZWEIMAL messen: oben und am Ende jedes Rollers. Die
            # Hellmodus-Messreihe vom 26.09. hat genau hier ihren groessten
            # Wert gefunden (Projekt/Plaene: oben 7,6 %, gerollt 57,5 %) -
            # eine Flaeche, die erst nach dem Rollen gezeichnet wird, ist
            # oben nicht vorhanden und waere sonst "nicht da".
            seite.evaluate(B.BIS_UNTEN_JS)
            seite.wait_for_timeout(1100)
            d["dunkel_gerollt"] = seite.evaluate(DUNKEL_JS)
            for wo, dd in (("oben", d["dunkel"]),
                           ("gerollt", d["dunkel_gerollt"])):
                print("   Hellmodus %-8s %d dunkle Flaechen ab 8000 px2, "
                      "tragend (>=25 %% Schirm): %d | feste dunkle Farben "
                      "im Bild: %d   Huelle %s"
                      % (wo, dd["anzahl"], len(dd["tragend"]),
                         dd["anzahl_feste"], dd["huelle"]))
                for g in dd["dunkel"][:5]:
                    print("      %-26s %s  H=%.3f  %dx%d  %.1f %% des Schirms"
                          % ((g["tag"] + "." + g["klasse"])[:26], g["farbe"],
                             g["helligkeit"], g["breit"], g["hoch"],
                             g["anteil"] * 100))
                for f in dd["feste_farben"][:6]:
                    print("      FEST %s  %-18s %dx%d = %.1f %% des Schirms, "
                          "sichtbar=%s"
                          % (f["farbe"], (f["tag"] + "." + f["klasse"])[:18],
                             f["breit"], f["hoch"], f["anteil"] * 100,
                             f["sichtbar"]))
            if kuerzel == "plaene":
                # Die drei uebrigen Unterzustaende von VPlan. Nur ihren
                # Startzustand zu messen hiesse, ein Viertel der Ansicht zu
                # messen und drei Viertel unerwaehnt zu lassen.
                r = seite.evaluate(VPLAN_REITER_JS)
                d["vplan_reiter"] = r
                print("   VPlan-Unterreiter: %s" % r)
                d["vplan_zustaende"] = []
                if r.get("ok"):
                    for i in range(r["anzahl"]):
                        if not seite.evaluate(VPLAN_TIPPEN_JS, i):
                            continue
                        seite.wait_for_timeout(1300)
                        dz = seite.evaluate(DUNKEL_JS)
                        eintrag = {
                            "reiter": r["knoepfe"][i],
                            "dunkel_anzahl": dz["anzahl"],
                            "tragend": dz["tragend"],
                            "feste_farben": dz["feste_farben"]}
                        d["vplan_zustaende"].append(eintrag)
                        print("      Reiter %d %-18r: %d dunkle Flaechen, "
                              "%d tragend, feste dunkle Farben: %s"
                              % (i, r["knoepfe"][i]["text"], dz["anzahl"],
                                 len(dz["tragend"]),
                                 ["%s %dx%d = %.1f%%"
                                  % (f["farbe"], f["breit"], f["hoch"],
                                     f["anteil"] * 100)
                                  for f in dz["feste_farben"][:4]]))
            ziel = os.path.join(WURZEL, "screenshots")
            os.makedirs(ziel, exist_ok=True)
            seite.screenshot(path=os.path.join(
                ziel, "b3_%s_%d_hell.png" % (kuerzel, breite)))
            d["seitenfehler"] = [f for f in fehler
                                 if not any(w.lower() in f.lower()
                                            for w in M.IGNORIEREN)][:5]
            ctx.close()
            return d, offen, fehler

        # ── Die Koeder K1-K8 aus Stufe 4-7, unveraendert ───────────────
        d["querrollen_selbstprobe"] = {}
        d["koeder_ok"] = B._koeder(seite, marke, offen,
                                   d["querrollen_selbstprobe"])
        # ── K9: die Beschnitt-Einordnung ───────────────────────────────
        kb = seite.evaluate(KOEDER_BESCH2_EIN)
        be = seite.evaluate(BESCHNITT_ECHT_JS)
        hart = [x for x in be["gekuerzt"] if x["text"].startswith("HART")]
        weich = [x for x in be["nur_ueberlauf"] if x["text"].startswith("WEICH")]
        falsch = ([x for x in be["nur_ueberlauf"] if x["text"].startswith("HART")]
                  + [x for x in be["gekuerzt"] if x["text"].startswith("WEICH")])
        k9 = bool(hart) and bool(weich) and not falsch
        print("   K9 Beschnitt   %s  (hart %s/%s als gekuerzt: %s; weich "
              "%s/%s als blosser Ueberlauf: %s; falsch eingeordnet: %d)"
              % ("ANGESCHLAGEN" if k9 else "STUMM",
                 kb["hart"]["scroll"], kb["hart"]["sicht"], bool(hart),
                 kb["weich"]["scroll"], kb["weich"]["sicht"], bool(weich),
                 len(falsch)))
        if not k9:
            offen.append("%s: K9 (Beschnitt-Einordnung) hat nicht "
                         "angeschlagen - gekuerzt gegen nur-ueberlaufen ist "
                         "in diesem Lauf NICHT gemessen." % marke)
        seite.evaluate(KOEDER_BESCH2_AUS)
        seite.wait_for_timeout(250)

        # ── K13: "nur Symbol + Zahl" - die Luecke des alten Melders ────
        seite.evaluate(KOEDER_EMOJIZAHL_EIN)
        alt = seite.evaluate(B.EMOJI_JS)
        neu = seite.evaluate(EMOJI_ZAHL_JS)
        alt_hat = any(x["zeichen"] == "\U0001f529" + "7"
                      for x in alt["ohne_hilfe"])
        neu_hat = any(x["zeichen"] == "\U0001f529" + "7"
                      for x in neu["ohne_hilfe"])
        k13 = neu_hat and not alt_hat
        print("   K13 Symbol+Zahl %s  (Koeder-Knopf '\U0001f5297': alter "
              "Melder faengt ihn: %s, neuer: %s)"
              % ("ANGESCHLAGEN" if k13 else "STUMM", alt_hat, neu_hat))
        if not k13:
            offen.append("%s: K13 - der Melder 'nur Symbol + Zahl' hat "
                         "seinen Koeder nicht gefangen (alt=%s neu=%s). "
                         "Diese Form ist in diesem Lauf NICHT gemessen."
                         % (marke, alt_hat, neu_hat))
        seite.evaluate(KOEDER_EMOJIZAHL_AUS)
        seite.wait_for_timeout(200)

        # ── K12: der Flaechenmelder im DUNKELMODUS ─────────────────────
        # Positivkontrolle. Findet er hier keine tragende dunkle Flaeche,
        # misst er keine Farbe - und "im Hellmodus nichts dunkel" waere die
        # Aussage eines Melders, der nichts sehen kann.
        d["dunkel_dunkelmodus"] = seite.evaluate(DUNKEL_JS)
        k12 = len(d["dunkel_dunkelmodus"]["tragend"]) > 0
        print("   K12 Flaeche     %s  (Dunkelmodus: %d dunkle Flaechen, "
              "%d tragend, Huelle %s)"
              % ("ANGESCHLAGEN" if k12 else "STUMM",
                 d["dunkel_dunkelmodus"]["anzahl"],
                 len(d["dunkel_dunkelmodus"]["tragend"]),
                 d["dunkel_dunkelmodus"]["huelle"]))
        if not k12:
            offen.append("%s: K12 (Flaechenmelder) hat im DUNKELMODUS keine "
                         "tragende dunkle Flaeche gefunden - die "
                         "Hellmodus-Aussage dieser Ansicht ist NICHT "
                         "gemessen." % marke)

        # ── Die sieben Regeln ──────────────────────────────────────────
        d["schrift"] = seite.evaluate(B.SCHRIFT_JS)
        d["tipp"] = seite.evaluate(B.TIPP_JS)
        d["emoji"] = seite.evaluate(B.EMOJI_JS)
        d["emoji_zahl"] = seite.evaluate(EMOJI_ZAHL_JS)
        d["quer"] = seite.evaluate(B.QUER_JS)
        d["beschnitt"] = seite.evaluate(B.BESCHNITT_JS)
        d["beschnitt_echt"] = seite.evaluate(BESCHNITT_ECHT_JS)
        d["tabellen"] = seite.evaluate(B.TABELLE_JS)
        d["mengen"] = seite.evaluate(B.MENGEN_JS)
        d["verdeckung_oben"] = seite.evaluate(B.VERDECKUNG_JS)
        if kuerzel == "as_liste":
            d["bestand"] = seite.evaluate(AS_BESTAND_JS)
            d["offa"] = seite.evaluate(OFFA_JS)
            # ── K10: der OFFA-Hinweis MUSS erscheinen und die 2 nennen ──
            # Die Saat setzt GENAU ZWEI verwaiste Scheine (S1, S2) und einen
            # dritten, der juprowa-gebunden aber FRISCH ist (S3). Nennt das
            # Band nicht die 2, ist der Hinweis nicht gemessen - und "der
            # Hinweis warnt nur" waere die Aussage eines Melders, der das
            # Band nie gesehen hat.
            band = [t for t in d["offa"]["treffer"] if t["sichtbar"]]
            k10 = bool(band) and any("2 offene" in t["wortlaut"]
                                     for t in band)
            print("   K10 OFFA-Hinweis %s  (%d sichtbare Stellen; Saat setzt "
                  "2 verwaiste + 1 frischen juprowa-Schein)"
                  % ("ANGESCHLAGEN" if k10 else "STUMM", len(band)))
            d["k10"] = k10
            if not k10:
                offen.append("%s: K10 - das OFFA-Hinweisband erschien NICHT "
                             "oder nannte nicht die 2. Der IST-Stand des "
                             "Hinweises ist damit NICHT gemessen." % marke)
        if kuerzel == "material":
            # Der zweite Zustand: Warenkorb. Ohne ihn ist die Ansicht mit
            # einer LEEREN Liste gemessen und drei Viertel unbesucht.
            if seite.evaluate(REITER_TIPPEN_JS, "Warenkorb"):
                seite.wait_for_timeout(2000)
                zw = {"schrift": seite.evaluate(B.SCHRIFT_JS),
                      "tipp": seite.evaluate(B.TIPP_JS),
                      "emoji": seite.evaluate(B.EMOJI_JS),
                      "emoji_zahl": seite.evaluate(EMOJI_ZAHL_JS),
                      "quer": seite.evaluate(B.QUER_JS),
                      "beschnitt_echt": seite.evaluate(BESCHNITT_ECHT_JS),
                      "mengen": seite.evaluate(B.MENGEN_JS),
                      "tabellen": seite.evaluate(B.TABELLE_JS)}
                d["warenkorb"] = zw
                print("   WARENKORB (zweiter Zustand): Schrift<12 %d von %d | "
                      "Tipp<44 %d | Symbol %d (ohne Buchstaben %d) | "
                      "gekuerzt %d | %d Knoepfe / %d Felder"
                      % (zw["schrift"]["anzahl_klein"],
                         zw["schrift"]["gemessen"], zw["tipp"]["anzahl_klein"],
                         zw["emoji"]["anzahl_ohne"],
                         zw["emoji_zahl"]["anzahl_ohne"],
                         zw["beschnitt_echt"]["anzahl_gekuerzt"],
                         zw["mengen"]["knoepfe"], zw["mengen"]["felder"]))
                for r in zw["quer"]["waagrechte_roller"][:3]:
                    bk = r["breitestes_kind"] or {}
                    print("      quer: %s rollt %s px (%s von %s), "
                          "breitestes Kind %s px"
                          % (r["weg"][-42:], r["ueberschuss"],
                             r["clientWidth"], r["scrollWidth"],
                             bk.get("breite")))
                seite.evaluate(REITER_TIPPEN_JS, "Lager")
                seite.wait_for_timeout(1400)
            else:
                d["warenkorb"] = {"fehler": "Reiter Warenkorb nicht gefunden"}
                offen.append("%s: der Reiter 'Warenkorb' war nicht antippbar "
                             "- drei Viertel der Material-Ansicht sind NICHT "
                             "gemessen." % marke)
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

    print("   Schrift < 12 px: %d von %d gemessenen Textstellen"
          % (d["schrift"]["anzahl_klein"], d["schrift"]["gemessen"]))
    print("   Tippziele (Knoepfe) < 44 px: %d   |   Felder/Beschriftungen "
          "< 44 px: %d (getrennt, KEIN Knopfbefund)"
          % (d["tipp"]["anzahl_klein"], d["tipp"]["anzahl_felder_klein"]))
    print("   nur-Symbol ohne title/aria: %d  (mit title/aria: %d)"
          % (d["emoji"]["anzahl_ohne"], d["emoji"]["anzahl_mit"]))
    ez = d["emoji_zahl"]
    print("   OHNE BUCHSTABEN ohne title/aria: %d, davon nur Symbol+Zaehler: "
          "%d   ->   %s"
          % (ez["anzahl_ohne"], ez["nur_mit_zaehler"],
             [x["zeichen"] for x in ez["ohne_hilfe"][:8]]))
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
    for x in be["gekuerzt"][:6]:
        print("      %5s px verloren an %-28s  %r"
              % (x["verloren_px"], x["verloren_an"][:28], x["text"][:40]))
    vu = d["verdeckung_unten"]
    print("   Verdeckung am Ende: %s"
          % (vu.get("hinweis") or "%d Bedienelemente in der Leistenzone "
             "(%s, Ueberstand %s px)"
             % (vu.get("anzahl", -1), vu.get("leiste"), vu.get("ueberstand"))))
    print("   Tabellen: %d, davon breiter als der Schirm: %d"
          % (len(d["tabellen"]), sum(1 for t in d["tabellen"] if t["ueber"])))
    print("   Mengen: %d Knoepfe, %d Felder, %d Auswahlfelder"
          % (d["mengen"]["knoepfe"], d["mengen"]["felder"],
             d["mengen"]["auswahl"]))
    if kuerzel == "as_liste":
        bs = d["bestand"]
        fehlt_k = [k for k, v in bs["statuskacheln"].items() if not v]
        fehlt_c = [k for k, v in bs["chips"].items() if not v]
        print("   BESTANDSSCHUTZ  Statuskacheln %d/11%s | Sortierkriterien "
              "%d/7 (Auswahlfeld %d, Kopfzeile %d) | Chips %d/8%s | "
              "Suchfeld %s | OFFA-Excel %s | Unterreiter %s"
              % (bs["statuskacheln_da"],
                 (" FEHLT: %s" % fehlt_k) if fehlt_k else "",
                 bs["sort_erfuellt"], bs["sort_ueber_auswahlfeld"],
                 bs["sort_ueber_kopfzeile"], bs["chips_da"],
                 (" FEHLT: %s" % fehlt_c) if fehlt_c else "",
                 bool(bs["suchfeld"]), bs["offa_excel"],
                 [r for r, v in bs["unterreiter"].items() if v]))
        of = d["offa"]
        print("   OFFA-HINWEIS    %d Stellen gefunden" % of["anzahl"])
        for t in of["treffer"]:
            print("      <%s> %d px, y=%d, %dx%d, role=%s tabindex=%s "
                  "cursor=%s react-onClick=%s Knoepfe im Band=%s"
                  % (t["tag"], t["fontSize"], t["oben"], t["breite"],
                     t["hoehe"], t["role"], t["tabindex"], t["cursor"],
                     t["react_onclick"], t["knoepfe_im_band"]))
            print("      Wortlaut: %r" % t["wortlaut"][:200])
    return d, offen, fehler


def main(argv):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt.")
        return 2
    nur = argv[argv.index("--nur") + 1] if "--nur" in argv else None
    ziel_json = argv[argv.index("--json") + 1] if "--json" in argv else None
    nur_hell = "--hell" in argv

    datei = os.environ.get("EPK_INDEX", "index.html")
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port, datei)
    print("Gemessen wird: %s" % url)
    import hashlib
    h = hashlib.md5(io.open(os.path.join(WURZEL, datei), "rb").read()).hexdigest()
    print("md5 der gemessenen Datei: %s" % h)

    alles, offen = [], []
    listen = [nur] if nur else list(ANSICHTEN)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for kuerzel in listen:
            for breite, hoehe in BREITEN:
                if not nur_hell:
                    dd, o, _ = _lauf(browser, url, kuerzel, breite, hoehe, "dark")
                    alles.append(dd)
                    offen += o
                dd, o, _ = _lauf(browser, url, kuerzel, breite, hoehe, "light")
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
            print("  %-12s %5d %-5s NICHT ERREICHBAR" % (d["ansicht"],
                                                         d["breite"],
                                                         d["thema"]))
            continue
        if d["thema"] == "light":
            print("  %-12s %5d hell   dunkle Flaechen %2d, tragend %d"
                  % (d["ansicht"], d["breite"], d["dunkel"]["anzahl"],
                     len(d["dunkel"]["tragend"])))
            continue
        vu = d["verdeckung_unten"]
        print("  %-12s %5d dunkel Schrift<12 %3d/%3d | Tipp<44 %3d | "
              "Symbol %2d | quer %-9s | gekuerzt %2d | ueberlauf %2d | "
              "verdeckt %s | Tab>Schirm %d"
              % (d["ansicht"], d["breite"], d["schrift"]["anzahl_klein"],
                 d["schrift"]["gemessen"], d["tipp"]["anzahl_klein"],
                 d["emoji"]["anzahl_ohne"],
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


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
