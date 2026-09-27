# -*- coding: utf-8 -*-
"""Pixelneutralitaet v3.9.959 - drei Behauptungen am GERENDERTEN Schirm pruefen.

WOZU
────
Drei Aussagen sind am QUELLTEXT begruendet und am Schirm NICHT nachgemessen
worden. Diese Sonde messt sie:

  Fall 1  v3.9.956 D9   "der Umbau von div auf h2 kostet kein Pixel"
          BauprovisorienView, LISTE (fontSize 20) und FORMULAR (fontSize 18).
          Breiten 340 / 375 / 390 / 1440. Die 340 ist der Sonderfall: dort
          greift `.header-row h2{font-size:16px!important}` - WENN der Kopf
          `header-row` truege.
          Vergleichsstand: v3.9.955 = 11e365a (dort ein div).

  Fall 2  v3.9.957/958 S-1  "title und aria-label kosten kein Pixel"
          Die Umschalter ☰/⊞ in FahrzeugView (Hauptreiter "Fahrzeuge") und in
          VFotos (Projektakte/Fotos). Breiten 390 / 1440.
          Vergleichsstand: v3.9.956 = a4b50e5 (dort ohne title/aria-label).

  Fall 3  v3.9.955  "die Verhaltensaenderung im Bautagebuch ist noch da"
          VBautag haengt an BP_MOB (600) statt an 768; bei 640 px muss die
          DESKTOP-Fassung erscheinen. Gemessen wird mit GEOEFFNETEM
          Bearbeitungsformular und mit Eintragskarten - alle isMob-Stellen in
          VBautag liegen dort. Breiten 390 / 640 / 767 / 1440.
          Vergleichsstand: v3.9.954 = a34d535 (dort ww<768).

🔴 Der vom Auftrag genannte Stand 84b8e72 ist ein DOKU-Commit; sein
   index.html ist byteidentisch mit v3.9.957 (09d0153) und traegt den h2
   sowie die title/aria-label bereits. Als Vergleichsstand fuer Fall 1 und 2
   ist er untauglich. Deshalb die drei Staende oben, jeweils der Commit
   DIREKT VOR der Aenderung.

WIE GEMESSEN WIRD
─────────────────
  RASTER_JS   nimmt fuer JEDES Element der Ansicht mit sichtbarem Kasten und
              Text bis 90 Zeichen eine Zeile auf: Schluessel = normierter
              Text + "#" + laufende Nummer dieses Textes in Dokumentordnung,
              Wert = tag, x, y, w, h. Der Schluessel ueberlebt den Umbau
              div→h2 (der Text bleibt, die Position in der Ordnung bleibt),
              das TAG wird daneben mitgefuehrt. So faellt jede Verschiebung
              der GANZEN Ansicht auf, nicht nur die des Titels.
  TITEL_JS    dazu die Feinmessung am Titelelement selbst: tag, Kasten,
              berechnete Schriftgroesse/-dicke, Zeilenhoehe, Aussenabstand.
  NAMEN_JS    zugaenglicher Name jedes Knopfes der Ansicht: aria-label, sonst
              title, sonst Text mit mindestens einem Buchstaben. Ein Knopf,
              dessen ganzer Inhalt ein Symbol ist, hat keinen.
  SCHRIFT_JS  aus b3_vier_ansichten_messen (Textstellen unter 12 px).

DIE KOEDER - ohne sie ist das Ergebnis "nicht gemessen"
───────────────────────────────────────────────────────
  K-A  Saat sichtbar (uebernommen aus B/S: SAATWORT muss in der Ansicht
       stehen). Eine leere Ansicht ist keine bestandene Probe.
  K-B  Ansichtsnachweis: ein Merkmal, das NUR diese Ansicht traegt.
  K-C  Der Titeltext MUSS gefunden werden, in BEIDEN Staenden. Fehlt er in
       einem, ist der Vergleich nicht gemessen.
  K-D  Gegenprobe zum Textsucher: ein Wort, das es sicher nicht gibt
       ("Kalibrierungsintervallpruefung"), darf NICHT gefunden werden.
  K-E  Nur Fall 1, nur 340 px: dem Kopfbehaelter wird voruebergehend die
       Klasse `header-row` angehaengt. Die berechnete Schriftgroesse MUSS
       dann auf 16px fallen. Faellt sie nicht, kann diese Messung die Regel
       prinzipiell nicht sehen, und die Aussage "die Regel greift hier
       nicht" ist NICHT gemessen. Danach wird die Klasse entfernt und die
       Rueckkehr auf den Altwert belegt.
  K-F  Nur Fall 2: ein Kunstknopf mit ausschliesslich "⊗" und ohne title
       wird eingehaengt; NAMEN_JS MUSS ihn als namenlos zaehlen. Danach raus.
  K-G  Nur Fall 3: ein Kunst-span mit font-size 9px wird eingehaengt; die
       Zahl der Stellen unter 12 px MUSS um genau 1 steigen. Danach raus.
  K-H  Nur Fall 3: das Formular MUSS offen sein - Datumsfeld im DOM UND ein
       Knopf "Speichern" UND ein Knopf "Abbrechen". Ausserdem muessen
       Eintragskarten da sein (mindestens eine), sonst fehlen die
       isMob-Stellen der Karte.

WAS DIESE SONDE NICHT MESSEN KANN
─────────────────────────────────
  * Alle 33+32 Knoepfe aus S-1. Gemessen werden die Knoepfe der ANGEFAHRENEN
    Ansichten. Der Umfang wird je Lauf genannt.
  * Echte Serverdaten. REST/Auth werden abgebrochen; gesaet wird in die
    IndexedDB. Bauprovisorien bleibt in der LISTE leer - der Titel und der
    Kopf sind davon unabhaengig, die Kartenliste NICHT.
  * Rollen. Gefahren wird role=admin, monteurId=M1.
  * Der Tooltip selbst (er erscheint erst beim Verweilen und liegt in der
    Browser-Oberflaeche, nicht im Baum).

AUFRUF
──────
    python scripts/pixelneutralitaet_959_messen.py --fall 1 --json a.json
    EPK_INDEX=_mess_pn_v955_11e365a.html python scripts/... --fall 1 --json b.json
    python scripts/pixelneutralitaet_959_messen.py --vergleich a.json b.json

index.html wird NICHT angefasst.
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

import mob_ansicht_messen as M           # noqa: E402
import b3_vier_ansichten_messen as B     # noqa: E402
import b3_stufen_8_11_messen as S        # noqa: E402
import b3_stufen_12_15_messen as Z       # noqa: E402

NIE = "Kalibrierungsintervallpruefung"

FAELLE = {
    "1": {"breiten": [340, 375, 390, 1440],
          "vergleich": "_mess_pn_v955_11e365a.html",
          "was": "D9 div->h2 in BauprovisorienView (Liste + Formular)"},
    "2": {"breiten": [390, 1440],
          "vergleich": "_mess_pn_v956_a4b50e5.html",
          "was": "S-1 title/aria-label an den Umschaltern (Fahrzeuge + Fotos)"},
    "3": {"breiten": [390, 640, 767, 1440],
          "vergleich": "_mess_pn_v954_a34d535.html",
          "was": "v3.9.955 VBautag an BP_MOB statt 768"},
    # Fall 4 ist eine UMFANGS-Erweiterung zu Fall 2: derselbe Namenszaehler,
    # aber ueber mehrere Hauptansichten, damit die Aussage "jeder Knopf hat
    # einen Namen" nicht nur fuer zwei Leisten gilt. Eine Breite genuegt -
    # ein zugaenglicher Name ist nicht breitenabhaengig; die ANZAHL der
    # gerenderten Knoepfe ist es sehr wohl, deshalb steht sie im Bericht.
    "4": {"breiten": [1440],
          "vergleich": "_mess_pn_v956_a4b50e5.html",
          "was": "S-1 Umfang: namenlose Knoepfe in elf Hauptansichten"},
}

# Fall 4: die Reiterbeschriftungen aus b3_stufens ANSICHTEN plus Home.
SWEEP = ["Projekte", "Arbeitsscheine", "Zeiterfassung", "Abwesenheiten",
         "Fahrzeuge", "Werkzeuge", "Mitarbeiter", "Auswertungen",
         "Einstellungen", "Gefahrenstoffe", "Bauprovisorien"]


# ══════════════════════════════════════════════════════════════════════════
# Messgeraete
# ══════════════════════════════════════════════════════════════════════════
# Schluessel = normierter Text + '#' + laufende Nummer dieses Textes in
# DOKUMENTORDNUNG. Der Text ueberlebt den Umbau div->h2, die Nummer haelt
# Huelle und Kind auseinander (beide tragen denselben Text). Das TAG steht
# im Wert, nicht im Schluessel - sonst waere gerade der gemessene Fall
# unvergleichbar.
RASTER_JS = r"""(wurzelWahl) => {
  const wz = document.querySelector(wurzelWahl) || document.getElementById('root');
  if (!wz) return {ok: false, grund: 'Wurzel ' + wurzelWahl + ' fehlt'};
  const norm = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const zaehler = {};
  const zeilen = {};
  let uebergangen = 0;
  Array.from(wz.querySelectorAll('*')).forEach((e) => {
    const t = norm(e.textContent);
    if (!t || t.length > 90) { uebergangen++; return; }
    const r = e.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) { uebergangen++; return; }
    const n = (zaehler[t] = (zaehler[t] || 0) + 1) - 1;
    zeilen[t + '#' + n] = {
      tag: e.tagName,
      x: Math.round(r.x * 100) / 100, y: Math.round(r.y * 100) / 100,
      w: Math.round(r.width * 100) / 100, h: Math.round(r.height * 100) / 100
    };
  });
  return {ok: true, anzahl: Object.keys(zeilen).length,
          uebergangen: uebergangen, zeilen: zeilen,
          wurzel: wurzelWahl,
          wurzelKasten: (() => { const r = wz.getBoundingClientRect();
            return {x: Math.round(r.x * 100) / 100, w: Math.round(r.width * 100) / 100,
                    h: Math.round(r.height * 100) / 100}; })()};
}"""

# Feinmessung an EINEM Element, gefunden ueber seinen genauen Text. Genommen
# wird das TIEFSTE passende Element (die wenigsten Nachfahren) - sonst misst
# man die Huelle statt der Ueberschrift.
TITEL_JS = r"""(cfg) => {
  const norm = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const wz = document.querySelector(cfg.wurzel) || document.getElementById('root');
  if (!wz) return {gefunden: false, grund: 'Wurzel fehlt'};
  const info = (e) => {
    if (!e) return null;
    const r = e.getBoundingClientRect(), c = getComputedStyle(e);
    return {tag: e.tagName, klassen: String(e.className || ''),
            x: Math.round(r.x * 100) / 100, y: Math.round(r.y * 100) / 100,
            w: Math.round(r.width * 100) / 100, h: Math.round(r.height * 100) / 100,
            unten: Math.round(r.bottom * 100) / 100,
            fontSize: c.fontSize, fontWeight: c.fontWeight,
            lineHeight: c.lineHeight, display: c.display,
            marginTop: c.marginTop, marginBottom: c.marginBottom,
            marginLeft: c.marginLeft, marginRight: c.marginRight,
            paddingTop: c.paddingTop, paddingBottom: c.paddingBottom,
            title: e.getAttribute('title'), aria: e.getAttribute('aria-label'),
            text: norm(e.textContent).slice(0, 60)};
  };
  const treffer = Array.from(wz.querySelectorAll('*'))
    .filter(e => norm(e.textContent) === cfg.text);
  if (!treffer.length) return {gefunden: false, text: cfg.text};
  treffer.sort((a, b) => a.querySelectorAll('*').length
                       - b.querySelectorAll('*').length);
  const el = treffer[0];
  const kopf = el.parentElement;
  let dar = kopf ? kopf.nextElementSibling : null;
  while (dar && dar.getBoundingClientRect().height === 0
         && dar.getBoundingClientRect().width === 0) {
    dar = dar.nextElementSibling;
  }
  return {gefunden: true, treffer: treffer.length, titel: info(el),
          kopfzeile: info(kopf), darunter: info(dar),
          geschwister: kopf ? kopf.children.length : null};
}"""

# Zugaenglicher Name je Knopf. Reihenfolge wie im Baum: aria-label, sonst
# title, sonst Text MIT mindestens einem Buchstaben. Ein Knopf, dessen ganzer
# Inhalt ein Symbol oder eine Zahl ist, hat keinen Namen.
NAMEN_JS = r"""(wurzelWahl) => {
  const wz = document.querySelector(wurzelWahl) || document.getElementById('root');
  if (!wz) return {ok: false, grund: 'Wurzel fehlt'};
  const norm = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const hatBuchstabe = (s) => /[A-Za-zÄÖÜäöüß]/.test(s || '');
  const knoepfe = Array.from(wz.querySelectorAll('button,[role=button]'));
  const ohne = [], mit = [];
  knoepfe.forEach((b) => {
    const r = b.getBoundingClientRect();
    const txt = norm(b.textContent);
    const aria = b.getAttribute('aria-label');
    const tit = b.getAttribute('title');
    const name = (aria && norm(aria)) || (tit && norm(tit))
               || (hatBuchstabe(txt) ? txt : '');
    const z = {text: txt.slice(0, 26), aria: aria, title: tit,
               sichtbar: !!(r.width || r.height),
               x: Math.round(r.x), y: Math.round(r.y),
               w: Math.round(r.width * 100) / 100,
               h: Math.round(r.height * 100) / 100};
    if (name) { z.name = name.slice(0, 40); mit.push(z); } else { ohne.push(z); }
  });
  return {ok: true, gesamt: knoepfe.length, anzahl_ohne: ohne.length,
          ohne: ohne, anzahl_mit: mit.length, mit: mit};
}"""

# Die Umschalter selbst, gefunden ueber ihren Inhalt - nicht ueber eine
# Klasse und nicht ueber eine Reihenfolge.
UMSCHALTER_JS = r"""(cfg) => {
  const wz = document.querySelector(cfg.wurzel) || document.getElementById('root');
  if (!wz) return {ok: false, grund: 'Wurzel fehlt'};
  const norm = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const info = (e, rolle) => {
    const r = e.getBoundingClientRect(), c = getComputedStyle(e);
    return {rolle: rolle, tag: e.tagName, text: norm(e.textContent),
            x: Math.round(r.x * 100) / 100, y: Math.round(r.y * 100) / 100,
            w: Math.round(r.width * 100) / 100, h: Math.round(r.height * 100) / 100,
            fontSize: c.fontSize, padding: c.paddingTop + ' ' + c.paddingRight,
            title: e.getAttribute('title'), aria: e.getAttribute('aria-label')};
  };
  const funde = [];
  cfg.zeichen.forEach((zch) => {
    Array.from(wz.querySelectorAll('button'))
      .filter(b => norm(b.textContent) === zch)
      .forEach(b => funde.push(info(b, zch)));
  });
  let leiste = null;
  const erster = Array.from(wz.querySelectorAll('button'))
    .filter(b => cfg.zeichen.indexOf(norm(b.textContent)) >= 0)[0];
  if (erster && erster.parentElement) leiste = info(erster.parentElement, 'LEISTE');
  return {ok: true, anzahl: funde.length, knoepfe: funde, leiste: leiste};
}"""

# Fall 3: die isMob-abhaengigen Stellen, als BERECHNETE Werte statt als
# Quelltext. Gesucht wird ueber Eigenschaften, nicht ueber Klassen.
ISMOB_SPUREN_JS = r"""(wurzelWahl) => {
  const wz = document.querySelector(wurzelWahl) || document.getElementById('root');
  if (!wz) return {ok: false, grund: 'Wurzel fehlt'};
  const norm = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const alle = Array.from(wz.querySelectorAll('div'));
  // 1) Das 3-spaltige Formularraster (isMob ? "1fr" : "1fr 1fr 1fr")
  const raster3 = alle
    .map(e => ({e: e, c: getComputedStyle(e)}))
    .filter(o => o.c.display === 'grid'
                 && /Datum/.test(norm(o.e.textContent))
                 && /Temperatur/.test(norm(o.e.textContent))
                 && norm(o.e.textContent).length < 400)
    .map(o => ({spalten: o.c.gridTemplateColumns,
                anzahl_spalten: o.c.gridTemplateColumns.split(' ').length,
                text: norm(o.e.textContent).slice(0, 60)}));
  // 2) Die Speichern/Abbrechen-Zeile (isMob ? column : row)
  const speicherZeile = alle
    .map(e => ({e: e, c: getComputedStyle(e)}))
    .filter(o => o.c.display === 'flex'
                 && /[Ss]peichern/.test(norm(o.e.textContent))
                 && /Abbrechen/.test(norm(o.e.textContent))
                 && o.e.querySelectorAll('button').length === 2)
    .map(o => ({richtung: o.c.flexDirection,
                knopfbreiten: Array.from(o.e.querySelectorAll('button'))
                  .map(b => Math.round(b.getBoundingClientRect().width * 100) / 100)}));
  // 3) Die Kartenkopfzeile (isMob ? column/flex-start : row/center)
  const kartenKopf = alle
    .map(e => ({e: e, c: getComputedStyle(e)}))
    .filter(o => o.c.display === 'flex' && o.c.justifyContent === 'space-between'
                 && o.e.querySelector('span')
                 && /°C|Sonnig|Bewölkt|Regen|Schnee|Wechselhaft|—/
                      .test(norm(o.e.textContent))
                 && norm(o.e.textContent).length < 160)
    .map(o => ({richtung: o.c.flexDirection, ausrichtung: o.c.alignItems,
                luecke: o.c.rowGap + '/' + o.c.columnGap,
                text: norm(o.e.textContent).slice(0, 50)}));
  // 4) Die Chips (isMob ? "4px 8px" : "5px 10px")
  const chips = Array.from(wz.querySelectorAll('button'))
    .filter(b => getComputedStyle(b).borderRadius === '14px')
    .slice(0, 6)
    .map(b => ({text: norm(b.textContent).slice(0, 18),
                padding: getComputedStyle(b).paddingTop + ' '
                       + getComputedStyle(b).paddingRight}));
  return {ok: true, raster3: raster3, speicherZeile: speicherZeile,
          kartenKopf: kartenKopf, chips: chips};
}"""

FORM_OFFEN_JS = r"""(wurzelWahl) => {
  const wz = document.querySelector(wurzelWahl) || document.getElementById('root');
  if (!wz) return {ok: false, grund: 'Wurzel fehlt'};
  const norm = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const datum = Array.from(wz.querySelectorAll('input'))
    .filter(i => i.type === 'date')
    .map(i => ({typ: i.type, wert: i.value}));
  const kn = Array.from(wz.querySelectorAll('button')).map(b => norm(b.textContent));
  const h2 = Array.from(wz.querySelectorAll('h1,h2,h3'))
    .map(e => norm(e.textContent)).filter(x => x);
  return {ok: true, datumsfelder: datum, anzahl_datum: datum.length,
          speichern: kn.filter(t => /[Ss]peichern/.test(t)),
          abbrechen: kn.filter(t => /Abbrechen/.test(t)),
          ueberschriften: h2.slice(0, 5),
          textareas: wz.querySelectorAll('textarea').length,
          knoepfe: kn.length};
}"""

NIE_JS = r"""(cfg) => {
  const wz = document.querySelector(cfg.wurzel) || document.getElementById('root');
  const t = ((wz && wz.innerText) || '');
  return {gefunden: t.indexOf(cfg.wort) >= 0, laenge: t.length};
}"""

# K-E: dem Kopfbehaelter die Klasse header-row anhaengen und die berechnete
# Schriftgroesse vorher/nachher/wieder-vorher lesen.
KOEDER_HEADERROW_JS = r"""(cfg) => {
  const norm = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const wz = document.querySelector(cfg.wurzel) || document.getElementById('root');
  const tr = Array.from(wz.querySelectorAll('*'))
    .filter(e => norm(e.textContent) === cfg.text);
  if (!tr.length) return {ok: false, grund: 'Titel nicht gefunden'};
  tr.sort((a, b) => a.querySelectorAll('*').length - b.querySelectorAll('*').length);
  const el = tr[0], kopf = el.parentElement;
  if (!kopf) return {ok: false, grund: 'kein Elternelement'};
  const vorher = getComputedStyle(el).fontSize;
  const vorherH = Math.round(el.getBoundingClientRect().height * 100) / 100;
  kopf.classList.add('header-row');
  const mit = getComputedStyle(el).fontSize;
  const mitH = Math.round(el.getBoundingClientRect().height * 100) / 100;
  kopf.classList.remove('header-row');
  const nachher = getComputedStyle(el).fontSize;
  return {ok: true, tag: el.tagName, vorher: vorher, mit_header_row: mit,
          nachher: nachher, hoehe_vorher: vorherH, hoehe_mit: mitH,
          medienregel_greift: window.matchMedia('(max-width:340px)').matches,
          schlaegt_an: mit !== vorher, zurueck: nachher === vorher};
}"""

# K-F: Kunstknopf mit ausschliesslich einem Symbol, ohne title/aria.
KOEDER_NAMENLOS_JS = r"""(wurzelWahl) => {
  const wz = document.querySelector(wurzelWahl) || document.getElementById('root');
  if (!wz) return {ok: false, grund: 'Wurzel fehlt'};
  const b = document.createElement('button');
  b.id = '__koeder_namenlos';
  b.textContent = '⊗';
  wz.appendChild(b);
  return {ok: true, eingehaengt: !!document.getElementById('__koeder_namenlos')};
}"""

KOEDER_NAMENLOS_WEG_JS = r"""() => {
  const b = document.getElementById('__koeder_namenlos');
  if (b) b.remove();
  return {weg: !document.getElementById('__koeder_namenlos')};
}"""

# K-G: Kunst-span mit 9px.
KOEDER_KLEIN_JS = r"""(wurzelWahl) => {
  const wz = document.querySelector(wurzelWahl) || document.getElementById('root');
  if (!wz) return {ok: false, grund: 'Wurzel fehlt'};
  const s = document.createElement('div');
  s.id = '__koeder_klein';
  s.style.fontSize = '9px';
  s.textContent = 'Koederzeile neun Pixel';
  wz.appendChild(s);
  return {ok: true, eingehaengt: !!document.getElementById('__koeder_klein')};
}"""

KOEDER_KLEIN_WEG_JS = r"""() => {
  const s = document.getElementById('__koeder_klein');
  if (s) s.remove();
  return {weg: !document.getElementById('__koeder_klein')};
}"""

KLICK_TEXT_JS = r"""(cfg) => {
  const wz = document.querySelector(cfg.wurzel) || document.getElementById('root');
  if (!wz) return {ok: false, grund: 'Wurzel fehlt'};
  const norm = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const k = Array.from(wz.querySelectorAll('button'))
    .filter(b => norm(b.textContent) === cfg.text
                 || (cfg.teil && norm(b.textContent).indexOf(cfg.text) >= 0));
  if (!k.length) return {ok: false, grund: 'kein Knopf "' + cfg.text + '"',
                         vorhanden: Array.from(wz.querySelectorAll('button'))
                           .map(b => norm(b.textContent).slice(0, 22)).slice(0, 40)};
  k[0].click();
  return {ok: true, treffer: k.length};
}"""


# ══════════════════════════════════════════════════════════════════════════
# Saat: die Bautagebuch-Eintraege liegen im projektCache, Schluessel bt_<pid>
# (index.html: `ODB.loadProj("bt_"+p.id)`, PROJ_CACHE_STORE="projektCache").
# SEED2_JS schreibt nur unter dem Schluessel 'data' - dafuer braucht es eine
# eigene Einspielung.
# ══════════════════════════════════════════════════════════════════════════
PROJCACHE_JS = r"""
(async (cfg) => {
  const oeffnen = (name) => new Promise((res, rej) => {
    const r = indexedDB.open(name);
    r.onsuccess = () => res(r.result);
    r.onerror = () => rej(r.error);
  });
  const db = await oeffnen(cfg.db);
  if (Array.from(db.objectStoreNames).indexOf(cfg.store) < 0)
    return {ok: false, grund: 'Store ' + cfg.store + ' fehlt',
            stores: Array.from(db.objectStoreNames)};
  for (const k of Object.keys(cfg.paare)) {
    await new Promise((res) => {
      const tx = db.transaction(cfg.store, 'readwrite');
      tx.objectStore(cfg.store).put(cfg.paare[k], k);
      tx.oncomplete = res; tx.onerror = res; tx.onabort = res;
    });
  }
  const gelesen = {};
  for (const k of Object.keys(cfg.paare)) {
    gelesen[k] = await new Promise((res) => {
      const tx = db.transaction(cfg.store, 'readonly');
      const rq = tx.objectStore(cfg.store).get(k);
      rq.onsuccess = () => res(Array.isArray(rq.result)
        ? 'array:' + rq.result.length : String(rq.result));
      rq.onerror = () => res('LESEFEHLER');
    });
  }
  return {ok: true, gelesen: gelesen};
})
"""


def _bt_eintraege(pid):
    import datetime
    heute = datetime.date.today()
    raus = []
    wetter = ["sonnig", "bewoelkt", "regen"]
    for k in range(3):
        d = (heute - datetime.timedelta(days=k)).isoformat()
        raus.append({
            "id": "BT%d" % (k + 1), "pid": pid, "datum": d,
            "wetter": wetter[k], "temperatur": 14 + k,
            "anwesende": ["M1", "M2"],
            "taetigkeiten": "Steigleitung Heizung im Stiegenhaus 2 "
                            "verlegt, Pressfittinge gesetzt und abgedrueckt.",
            "besonderheiten": "Bauaufzug ab 13 Uhr belegt."
                              if k == 0 else "",
            "material": "Pressfitting 22 mm, 14 Stueck" if k == 1 else "",
            "erstelltVon": "M1", "createdAt": d})
    return raus


def _saat_projcache(seite, pid="P1"):
    erg = seite.evaluate(PROJCACHE_JS, {
        "db": M.DB_NAME, "store": "projektCache",
        "paare": {"bt_" + pid: _bt_eintraege(pid)}})
    print("   projektCache: %s" % erg)
    if not erg.get("ok"):
        raise SystemExit("ABBRUCH: projektCache nicht beschreibbar (%s)" % erg)
    if erg["gelesen"].get("bt_" + pid) != "array:3":
        raise SystemExit("ABBRUCH: bt_%s nicht zurueckgelesen (%s)"
                         % (pid, erg["gelesen"]))
    return erg


# ══════════════════════════════════════════════════════════════════════════
# Laeufe
# ══════════════════════════════════════════════════════════════════════════
def _kontext(pw, breite, hoehe):
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
        "localStorage.setItem('epk_theme','dark');}catch(e){}")
    ctx.route("**/rest/v1/**", lambda r: r.abort())
    ctx.route("**/auth/v1/**", lambda r: r.abort())
    return ctx


def _nav_haupt(seite, label, breite, protokoll):
    if breite < 600:
        seite.evaluate(M.NAV_OEFFNEN_JS)
        seite.wait_for_timeout(450)
        weg = seite.evaluate(B.NAV_MEHR_JS, label)
        seite.wait_for_timeout(2600)
        zu = seite.evaluate(B.MEHR_ZU_JS)
        seite.wait_for_timeout(700)
        rest = seite.evaluate(B.MEHR_OFFEN_JS)
        if rest:
            protokoll.append("Mehr-Menue noch offen (%d)" % rest)
        print("   Mehr-Menue zu: %s" % zu)
    else:
        weg = seite.evaluate(B.NAV_TOP_JS, label)
        seite.wait_for_timeout(2600)
    return weg


def _nav_projekt(seite, label):
    weg = seite.evaluate(S.PROJ_OEFFNEN_JS)
    print("   Projekt geoeffnet: %s" % weg)
    if not weg.get("ok"):
        return weg
    seite.wait_for_timeout(2400)
    w2 = seite.evaluate(S.PROJ_NAV_JS, label)
    print("   Unterseite %s: %s" % (label, w2))
    seite.wait_for_timeout(2400)
    return w2


def _marke(seite, wurzel, regex, gegen=None):
    t = seite.evaluate("(w) => { const e = document.querySelector(w)"
                       " || document.getElementById('root');"
                       " return (e && e.innerText) || ''; }", wurzel)
    da = bool(re.search(regex, t))
    weg = (gegen is None) or (not re.search(gegen, t))
    return {"marke": regex, "gegenmarke": gegen, "da": da and weg,
            "treffer": da, "gegenmarke_frei": weg, "textlaenge": len(t)}


def _fall1(seite, breite, d, offen, marke):
    """Bauprovisorien: Liste und Formular."""
    wurzel = ".main-pad"
    weg = _nav_haupt(seite, "Bauprovisorien", breite, d["protokoll"])
    print("   Navigation: %s" % weg)
    if weg in (None, "nicht-gefunden"):
        offen.append("%s: Bauprovisorien nicht erreichbar (%s)" % (marke, weg))
        d["nicht_erreichbar"] = True
        return
    nw = _marke(seite, wurzel, r"Bauprovisorien", r"Fahrzeugverwaltung")
    d["nachweis_liste"] = nw
    print("   K-B Ansichtsnachweis Liste: %s" % nw)
    if not nw["da"]:
        offen.append("%s: K-B - die Liste ist nicht belegt (%s)" % (marke, nw))
        return
    d["nie"] = seite.evaluate(NIE_JS, {"wurzel": wurzel, "wort": NIE})
    if d["nie"]["gefunden"]:
        offen.append("%s: K-D - das Nie-Wort wurde GEFUNDEN, der Textsucher "
                     "misst nicht, was er behauptet" % marke)
        return

    d["liste"] = {
        "titel": seite.evaluate(TITEL_JS, {"wurzel": wurzel,
                                           "text": "🚧 Bauprovisorien"}),
        "raster": seite.evaluate(RASTER_JS, wurzel),
    }
    if not d["liste"]["titel"].get("gefunden"):
        offen.append("%s: K-C - der Listentitel wurde nicht gefunden" % marke)
        return
    print("   Liste: %s %s h=%s y=%s | darunter y=%s"
          % (d["liste"]["titel"]["titel"]["tag"],
             d["liste"]["titel"]["titel"]["fontSize"],
             d["liste"]["titel"]["titel"]["h"],
             d["liste"]["titel"]["titel"]["y"],
             (d["liste"]["titel"]["darunter"] or {}).get("y")))

    if breite == 340:
        k = seite.evaluate(KOEDER_HEADERROW_JS,
                           {"wurzel": wurzel, "text": "🚧 Bauprovisorien"})
        d["koeder_headerrow_liste"] = k
        print("   K-E header-row (Liste): %s" % k)
        if not (k.get("ok") and k.get("medienregel_greift")
                and k.get("schlaegt_an") and k.get("zurueck")):
            offen.append("%s: K-E - die 340-px-Regel .header-row h2 konnte "
                         "nicht als wirksam belegt werden (%s). Die Aussage "
                         "'sie greift hier nicht' ist NICHT gemessen."
                         % (marke, k))

    # ── Formular ──
    kl = seite.evaluate(KLICK_TEXT_JS, {"wurzel": wurzel, "text": "+ Neu"})
    print("   Klick '+ Neu': %s" % (kl if kl.get("ok")
                                    else {k2: v for k2, v in kl.items()
                                          if k2 != "vorhanden"}))
    if not kl.get("ok"):
        offen.append("%s: der Knopf '+ Neu' wurde nicht gefunden - das "
                     "FORMULAR ist NICHT gemessen (vorhandene Knoepfe: %s)"
                     % (marke, (kl.get("vorhanden") or [])[:14]))
        return
    seite.wait_for_timeout(1800)
    nf = _marke(seite, wurzel, r"Neues Bauprovisorium", r"🚧 Bauprovisorien")
    d["nachweis_form"] = nf
    print("   K-B Ansichtsnachweis Formular: %s" % nf)
    if not nf["da"]:
        offen.append("%s: K-B - das Formular ist nicht belegt (%s)"
                     % (marke, nf))
        return
    d["form"] = {
        "titel": seite.evaluate(TITEL_JS, {"wurzel": wurzel,
                                           "text": "Neues Bauprovisorium"}),
        "raster": seite.evaluate(RASTER_JS, wurzel),
        "offen": seite.evaluate(FORM_OFFEN_JS, wurzel),
    }
    if not d["form"]["titel"].get("gefunden"):
        offen.append("%s: K-C - der Formulartitel wurde nicht gefunden"
                     % marke)
        return
    print("   Formular: %s %s h=%s y=%s | darunter y=%s"
          % (d["form"]["titel"]["titel"]["tag"],
             d["form"]["titel"]["titel"]["fontSize"],
             d["form"]["titel"]["titel"]["h"],
             d["form"]["titel"]["titel"]["y"],
             (d["form"]["titel"]["darunter"] or {}).get("y")))
    if breite == 340:
        k = seite.evaluate(KOEDER_HEADERROW_JS,
                           {"wurzel": wurzel, "text": "Neues Bauprovisorium"})
        d["koeder_headerrow_form"] = k
        print("   K-E header-row (Formular): %s" % k)
        if not (k.get("ok") and k.get("medienregel_greift")
                and k.get("schlaegt_an") and k.get("zurueck")):
            offen.append("%s: K-E (Formular) - die 340-px-Regel konnte nicht "
                         "als wirksam belegt werden (%s)" % (marke, k))


def _fall2(seite, breite, d, offen, marke):
    """Umschalter in Fahrzeuge (Hauptreiter) und Fotos (Projektakte)."""
    # ── Fahrzeuge ──
    wurzel = ".main-pad"
    weg = _nav_haupt(seite, "Fahrzeuge", breite, d["protokoll"])
    print("   Navigation Fahrzeuge: %s" % weg)
    if weg in (None, "nicht-gefunden"):
        offen.append("%s: Fahrzeuge nicht erreichbar (%s)" % (marke, weg))
    else:
        nw = _marke(seite, wurzel, r"Fahrzeugverwaltung", r"Tracker")
        d["fahrzeuge_nachweis"] = nw
        print("   K-B Fahrzeuge: %s" % nw)
        if not nw["da"]:
            offen.append("%s: K-B - Fahrzeugverwaltung nicht belegt (%s)"
                         % (marke, nw))
        else:
            d["fahrzeuge"] = {
                "umschalter": seite.evaluate(UMSCHALTER_JS,
                                             {"wurzel": wurzel,
                                              "zeichen": ["☰", "⊞"]}),
                "namen": seite.evaluate(NAMEN_JS, wurzel),
                "raster": seite.evaluate(RASTER_JS, wurzel),
            }
            u = d["fahrzeuge"]["umschalter"]
            print("   Fahrzeuge Umschalter: %d gefunden" % u["anzahl"])
            for z in u["knoepfe"]:
                print("      %s  %sx%s @%s,%s  title=%r aria=%r"
                      % (z["rolle"], z["w"], z["h"], z["x"], z["y"],
                         z["title"], z["aria"]))
            if u["leiste"]:
                print("      LEISTE %sx%s @%s,%s"
                      % (u["leiste"]["w"], u["leiste"]["h"],
                         u["leiste"]["x"], u["leiste"]["y"]))
            if u["anzahl"] != 2:
                offen.append("%s: in Fahrzeuge wurden %d Umschalter gefunden, "
                             "nicht 2 - NICHT gemessen" % (marke, u["anzahl"]))
            # K-F
            seite.evaluate(KOEDER_NAMENLOS_JS, wurzel)
            nk = seite.evaluate(NAMEN_JS, wurzel)
            weg2 = seite.evaluate(KOEDER_NAMENLOS_WEG_JS)
            fand = any(z["text"] == "⊗" for z in nk["ohne"])
            d["koeder_namenlos_fahrzeuge"] = {
                "gefunden": fand, "ohne_mit_koeder": nk["anzahl_ohne"],
                "ohne_ohne_koeder": d["fahrzeuge"]["namen"]["anzahl_ohne"],
                "entfernt": weg2}
            print("   K-F Kunstknopf ohne Namen: %s (namenlos %d -> %d)"
                  % ("ANGESCHLAGEN" if fand else "STUMM",
                     d["fahrzeuge"]["namen"]["anzahl_ohne"],
                     nk["anzahl_ohne"]))
            if not fand:
                offen.append("%s: K-F - der Namenszaehler hat den Kunstknopf "
                             "NICHT gefunden. Die Namenszahlen dieses Laufs "
                             "sind NICHT gemessen." % marke)

    # ── Fotos in der Projektakte ──
    seite.evaluate("() => { try { localStorage.setItem('__x','1'); } "
                   "catch(e){} }")
    weg = _nav_haupt(seite, "Projekte", breite, d["protokoll"])
    print("   Navigation Projekte: %s" % weg)
    if weg in (None, "nicht-gefunden"):
        offen.append("%s: Projektliste nicht erreichbar (%s)" % (marke, weg))
        return
    seite.wait_for_timeout(1600)
    w2 = _nav_projekt(seite, "Fotos")
    if not w2.get("ok"):
        offen.append("%s: Projektakte/Fotos nicht erreichbar (%s)"
                     % (marke, {k: v for k, v in w2.items()
                                if k != "vorhanden"}))
        return
    wurzel = ".proj-main"
    nw = _marke(seite, wurzel, r"Fotos|Mängel-Fotos|GPS-markiert",
                r"Fahrzeugverwaltung")
    d["fotos_nachweis"] = nw
    print("   K-B Fotos: %s" % nw)
    if not nw["da"]:
        offen.append("%s: K-B - Fotos nicht belegt (%s)" % (marke, nw))
        return
    d["fotos"] = {
        "umschalter": seite.evaluate(UMSCHALTER_JS,
                                     {"wurzel": wurzel,
                                      "zeichen": ["☰", "⊞"]}),
        "namen": seite.evaluate(NAMEN_JS, wurzel),
        "raster": seite.evaluate(RASTER_JS, wurzel),
    }
    u = d["fotos"]["umschalter"]
    print("   Fotos Umschalter: %d gefunden" % u["anzahl"])
    for z in u["knoepfe"]:
        print("      %s  %sx%s @%s,%s  title=%r aria=%r"
              % (z["rolle"], z["w"], z["h"], z["x"], z["y"],
                 z["title"], z["aria"]))
    if u["leiste"]:
        print("      LEISTE %sx%s @%s,%s"
              % (u["leiste"]["w"], u["leiste"]["h"],
                 u["leiste"]["x"], u["leiste"]["y"]))
    if u["anzahl"] != 2:
        offen.append("%s: in Fotos wurden %d Umschalter gefunden, nicht 2 - "
                     "NICHT gemessen" % (marke, u["anzahl"]))
    seite.evaluate(KOEDER_NAMENLOS_JS, wurzel)
    nk = seite.evaluate(NAMEN_JS, wurzel)
    weg2 = seite.evaluate(KOEDER_NAMENLOS_WEG_JS)
    fand = any(z["text"] == "⊗" for z in nk["ohne"])
    d["koeder_namenlos_fotos"] = {
        "gefunden": fand, "ohne_mit_koeder": nk["anzahl_ohne"],
        "ohne_ohne_koeder": d["fotos"]["namen"]["anzahl_ohne"],
        "entfernt": weg2}
    print("   K-F (Fotos): %s (namenlos %d -> %d)"
          % ("ANGESCHLAGEN" if fand else "STUMM",
             d["fotos"]["namen"]["anzahl_ohne"], nk["anzahl_ohne"]))
    if not fand:
        offen.append("%s: K-F (Fotos) - der Namenszaehler hat den Kunstknopf "
                     "NICHT gefunden." % marke)


def _fall3(seite, breite, d, offen, marke):
    """VBautag mit GEOEFFNETEM Formular und mit Eintragskarten."""
    wurzel = ".proj-main"
    weg = _nav_haupt(seite, "Projekte", breite, d["protokoll"])
    print("   Navigation Projekte: %s" % weg)
    if weg in (None, "nicht-gefunden"):
        offen.append("%s: Projektliste nicht erreichbar (%s)" % (marke, weg))
        return
    seite.wait_for_timeout(1600)
    w2 = _nav_projekt(seite, "Bautagebuch")
    if not w2.get("ok"):
        offen.append("%s: Projektakte/Bautagebuch nicht erreichbar (%s)"
                     % (marke, {k: v for k, v in w2.items()
                                if k != "vorhanden"}))
        return
    nw = _marke(seite, wurzel, r"Bautagebuch", r"Warenkorb")
    d["nachweis"] = nw
    print("   K-B Bautagebuch: %s" % nw)
    if not nw["da"]:
        offen.append("%s: K-B - Bautagebuch nicht belegt (%s)" % (marke, nw))
        return
    # Eintragskarten (K-H, zweiter Teil)
    liste = seite.evaluate(FORM_OFFEN_JS, wurzel)
    karten = seite.evaluate(
        "(w) => { const wz = document.querySelector(w); const n = (s) => "
        "(s||'').replace(/\\s+/g,' ').trim();"
        " return {erstellt_von: Array.from(wz.querySelectorAll('div'))"
        ".filter(e => n(e.textContent).indexOf('Erstellt von:') === 0).length,"
        " zeilen: (wz.innerText.match(/Erstellt von:/g) || []).length}; }",
        wurzel)
    d["karten"] = karten
    print("   Eintragskarten: %s" % karten)
    if not karten.get("zeilen"):
        offen.append("%s: K-H - es ist KEINE Eintragskarte gerendert. Die "
                     "isMob-Stellen der Karte sind NICHT gemessen (leere "
                     "Grundgesamtheit)." % marke)
    d["liste_vor_form"] = liste
    d["liste_ismob"] = seite.evaluate(ISMOB_SPUREN_JS, wurzel)
    # Nebenbefund-Messung: die Knopfnamen der EINTRAGSKARTE haengen an
    # isMob (der Text "Bearbeiten"/"Loeschen" faellt in der
    # Desktop-Fassung weg). Ob damit ein Knopf namenlos wird, ist eine
    # Frage an den gerenderten Baum, nicht an den Quelltext.
    d["liste_namen"] = seite.evaluate(NAMEN_JS, wurzel)
    seite.evaluate(KOEDER_NAMENLOS_JS, wurzel)
    _nk = seite.evaluate(NAMEN_JS, wurzel)
    seite.evaluate(KOEDER_NAMENLOS_WEG_JS)
    _fand = any(z["text"] == "⊗" for z in _nk["ohne"])
    d["liste_namen_koeder"] = _fand
    print("   Knopfnamen in der Liste: %d von %d ohne Namen %s "
          "| K-F %s"
          % (d["liste_namen"]["anzahl_ohne"],
             d["liste_namen"]["gesamt"],
             [z["text"] for z in d["liste_namen"]["ohne"]],
             "ok" if _fand else "STUMM"))
    if not _fand:
        offen.append("%s: K-F in der Bautagebuch-Liste STUMM - die "
                     "Namenszahl dieses Laufs ist NICHT gemessen."
                     % marke)
    d["liste_raster"] = seite.evaluate(RASTER_JS, wurzel)
    d["liste_schrift"] = seite.evaluate(B.SCHRIFT_JS)

    # ── Formular oeffnen ──
    kl = seite.evaluate(KLICK_TEXT_JS, {"wurzel": wurzel,
                                        "text": "➕ Neuer Eintrag"})
    if not kl.get("ok"):
        kl = seite.evaluate(KLICK_TEXT_JS, {"wurzel": wurzel,
                                            "text": "Neuer Eintrag",
                                            "teil": True})
    print("   Klick 'Neuer Eintrag': %s"
          % (kl if kl.get("ok") else {k: v for k, v in kl.items()
                                      if k != "vorhanden"}))
    if not kl.get("ok"):
        offen.append("%s: der Knopf 'Neuer Eintrag' wurde nicht gefunden - "
                     "das Formular ist NICHT gemessen (%s)"
                     % (marke, (kl.get("vorhanden") or [])[:14]))
        return
    seite.wait_for_timeout(3200)
    fo = seite.evaluate(FORM_OFFEN_JS, wurzel)
    d["form_offen"] = fo
    print("   K-H Formular offen: %d Datumsfelder, Speichern=%s, "
          "Abbrechen=%s, Ueberschriften=%s"
          % (fo["anzahl_datum"], fo["speichern"], fo["abbrechen"],
             fo["ueberschriften"][:2]))
    if not (fo["anzahl_datum"] and fo["speichern"] and fo["abbrechen"]):
        offen.append("%s: K-H - das Formular ist NICHT offen (Datum %d, "
                     "Speichern %s, Abbrechen %s). Die isMob-Stellen liegen "
                     "im Formular; dieser Lauf misst sie NICHT."
                     % (marke, fo["anzahl_datum"], fo["speichern"],
                        fo["abbrechen"]))
        return
    d["form_ismob"] = seite.evaluate(ISMOB_SPUREN_JS, wurzel)
    d["form_raster"] = seite.evaluate(RASTER_JS, wurzel)
    d["form_schrift"] = seite.evaluate(B.SCHRIFT_JS)
    print("   isMob-Spuren: Raster3 %s | Speicherzeile %s | Chips %s"
          % ([r["spalten"] for r in d["form_ismob"]["raster3"]],
             [(s["richtung"], s["knopfbreiten"])
              for s in d["form_ismob"]["speicherZeile"]],
             [c["padding"] for c in d["form_ismob"]["chips"][:2]]))
    print("   Schrift unter 12 px: %d von %d"
          % (d["form_schrift"]["anzahl_klein"],
             d["form_schrift"]["gemessen"]))
    # K-G
    seite.evaluate(KOEDER_KLEIN_JS, wurzel)
    sk = seite.evaluate(B.SCHRIFT_JS)
    wg = seite.evaluate(KOEDER_KLEIN_WEG_JS)
    delta = sk["anzahl_klein"] - d["form_schrift"]["anzahl_klein"]
    d["koeder_klein"] = {"vorher": d["form_schrift"]["anzahl_klein"],
                         "mit": sk["anzahl_klein"], "delta": delta,
                         "entfernt": wg}
    print("   K-G 9-px-Koeder: %d -> %d (delta %d) %s"
          % (d["form_schrift"]["anzahl_klein"], sk["anzahl_klein"], delta,
             "ANGESCHLAGEN" if delta == 1 else "STUMM"))
    if delta != 1:
        offen.append("%s: K-G - der 12-px-Zaehler hat den 9-px-Koeder nicht "
                     "um genau 1 mitgezaehlt (delta %d). Die Schriftzahlen "
                     "dieses Laufs sind NICHT gemessen." % (marke, delta))


def _fall4(seite, breite, d, offen, marke):
    """Namenszaehler ueber mehrere Hauptansichten - der UMFANG zu Fall 2."""
    wurzel = ".main-pad"
    d["sweep"] = {}
    for label in SWEEP:
        weg = _nav_haupt(seite, label, breite, d["protokoll"])
        if weg in (None, "nicht-gefunden"):
            d["sweep"][label] = {"erreichbar": False, "weg": weg}
            offen.append("%s: Ansicht %s nicht erreichbar (%s) - ihre "
                         "Knoepfe sind NICHT gemessen" % (marke, label, weg))
            continue
        seite.wait_for_timeout(900)
        n = seite.evaluate(NAMEN_JS, wurzel)
        # K-F je Ansicht: ohne den Koeder waere eine 0 nicht belegbar.
        seite.evaluate(KOEDER_NAMENLOS_JS, wurzel)
        nk = seite.evaluate(NAMEN_JS, wurzel)
        seite.evaluate(KOEDER_NAMENLOS_WEG_JS)
        fand = any(z["text"] == "⊗" for z in nk["ohne"])
        d["sweep"][label] = {"erreichbar": True, "gesamt": n["gesamt"],
                             "anzahl_ohne": n["anzahl_ohne"],
                             "ohne": [z["text"] for z in n["ohne"]],
                             "koeder": fand}
        print("   %-16s %3d Knoepfe, %2d ohne Namen %-28s K-F %s"
              % (label, n["gesamt"], n["anzahl_ohne"],
                 str([z["text"] for z in n["ohne"]])[:28],
                 "ok" if fand else "STUMM"))
        if not fand:
            offen.append("%s: K-F in %s STUMM - die Null dieser Ansicht ist "
                         "NICHT gemessen" % (marke, label))


def _lauf(pw, url, fall, breite, hoehe):
    marke = "Fall %s @ %d" % (fall, breite)
    print("\n── %s ───────────────────────────────" % marke)
    d = {"fall": fall, "breite": breite, "hoehe": hoehe, "protokoll": []}
    offen, fehler = [], []
    ctx = _kontext(pw, breite, hoehe)
    seite = ctx.new_page()
    seite.on("pageerror", lambda x: fehler.append(str(x)[:170]))
    try:
        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(3800)
        # Saat: Hauptspeicher (Projekte, Monteure, Fahrzeuge ...) ...
        erg = seite.evaluate(S.SEED2_JS, {"db": M.DB_NAME,
                                          "daten": Z._saat12()})
        if erg.get("fehlend"):
            print("   HINWEIS fehlende Speicher: %s" % erg["fehlend"])
        schlecht = [k for k, v in erg["gelesen"].items()
                    if str(v) in ("array:0", "FEHLT", "LESEFEHLER")
                    or str(v).startswith("leer")]
        if schlecht:
            raise SystemExit("ABBRUCH: Saat nicht angekommen (%s)" % schlecht)
        # ... und der projektCache fuer die Bautagebuch-Eintraege.
        _saat_projcache(seite, "P1")
        seite.evaluate("() => { try { localStorage.setItem("
                       "'epk_last_juprowa_pull', String(Date.now())); } "
                       "catch(e){} }")
        seite.reload(wait_until="domcontentloaded")
        seite.wait_for_timeout(6800)
        t = seite.evaluate("() => document.body.innerText")
        saat = len(B.SAATWORT.findall(t or ""))
        d["koeder_saat"] = saat
        print("   K-A Saat sichtbar: %d Treffer" % saat)
        if not saat:
            offen.append("%s: K-A - die Saat erscheint in KEINER Ansicht."
                         % marke)
            ctx.close()
            return d, offen, fehler

        if fall == "1":
            _fall1(seite, breite, d, offen, marke)
        elif fall == "2":
            _fall2(seite, breite, d, offen, marke)
        elif fall == "4":
            _fall4(seite, breite, d, offen, marke)
        else:
            _fall3(seite, breite, d, offen, marke)
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        offen.append("%s: ABBRUCH im Lauf: %s" % (marke, str(e)[:220]))
    finally:
        d["seitenfehler"] = [f for f in fehler
                             if not any(i in f for i in M.IGNORIEREN)]
        try:
            ctx.close()
        except Exception:
            pass
    if d.get("seitenfehler"):
        print("   Seitenfehler: %s" % d["seitenfehler"][:3])
    return d, offen, fehler


# ══════════════════════════════════════════════════════════════════════════
# Vergleich zweier JSON-Ergebnisse
# ══════════════════════════════════════════════════════════════════════════
def _raster_vergleich(a, b, schwelle=1.0):
    """a, b = die 'zeilen'-Woerterbuecher aus RASTER_JS."""
    gem = sorted(set(a) & set(b))
    nur_a = sorted(set(a) - set(b))
    nur_b = sorted(set(b) - set(a))
    abw = []
    for k in gem:
        for feld in ("x", "y", "w", "h"):
            dv = round(a[k][feld] - b[k][feld], 2)
            if abs(dv) > schwelle:
                abw.append({"schluessel": k, "feld": feld,
                            "neu": a[k][feld], "alt": b[k][feld],
                            "delta": dv,
                            "tag_neu": a[k]["tag"], "tag_alt": b[k]["tag"]})
    maxd = {}
    for feld in ("x", "y", "w", "h"):
        if gem:
            maxd[feld] = max(abs(round(a[k][feld] - b[k][feld], 2))
                             for k in gem)
        else:
            maxd[feld] = None
    tagwechsel = [{"schluessel": k, "neu": a[k]["tag"], "alt": b[k]["tag"]}
                  for k in gem if a[k]["tag"] != b[k]["tag"]]
    return {"gemeinsam": len(gem), "nur_neu": nur_a, "nur_alt": nur_b,
            "abweichungen": abw, "anzahl_abweichungen": len(abw),
            "max_delta": maxd, "tagwechsel": tagwechsel}


def _vergleich(pfad_neu, pfad_alt):
    neu = json.loads(io.open(pfad_neu, encoding="utf-8").read())
    alt = json.loads(io.open(pfad_alt, encoding="utf-8").read())
    print("=" * 78)
    print("VERGLEICH  neu=%s (%s)  gegen  alt=%s (%s)"
          % (neu["datei"], neu["md5"][:10], alt["datei"], alt["md5"][:10]))
    print("=" * 78)
    if neu["md5"] == alt["md5"]:
        print("🔴 BEIDE STAENDE SIND BYTEIDENTISCH - der Vergleich kann "
              "nichts zeigen.")
    nach_breite_alt = {(d["breite"]): d for d in alt["laeufe"]}
    raus = []
    for dn in neu["laeufe"]:
        da = nach_breite_alt.get(dn["breite"])
        if not da:
            print("  %d px: kein Gegenstueck im Altstand" % dn["breite"])
            continue
        for stelle in ("liste", "form", "fahrzeuge", "fotos"):
            if stelle in dn and stelle in da:
                rn = (dn[stelle].get("raster") or {}).get("zeilen") or {}
                ra = (da[stelle].get("raster") or {}).get("zeilen") or {}
                if not rn or not ra:
                    print("  %d px %s: leeres Raster (neu %d, alt %d) - "
                          "NICHT gemessen"
                          % (dn["breite"], stelle, len(rn), len(ra)))
                    continue
                v = _raster_vergleich(rn, ra)
                v.update({"breite": dn["breite"], "stelle": stelle})
                raus.append(v)
                print("\n  %d px  %s  %d gemeinsame Stellen, "
                      "max |delta| x=%s y=%s w=%s h=%s, %d > 1 px"
                      % (dn["breite"], stelle, v["gemeinsam"],
                         v["max_delta"]["x"], v["max_delta"]["y"],
                         v["max_delta"]["w"], v["max_delta"]["h"],
                         v["anzahl_abweichungen"]))
                if v["tagwechsel"]:
                    print("     Tagwechsel: %s" % v["tagwechsel"][:5])
                for z in v["abweichungen"][:14]:
                    print("     %-46s %s  %s -> %s  (%+g)"
                          % (z["schluessel"][:46], z["feld"], z["alt"],
                             z["neu"], z["delta"]))
                if len(v["abweichungen"]) > 14:
                    print("     ... und %d weitere"
                          % (len(v["abweichungen"]) - 14))
                if v["nur_neu"]:
                    print("     nur im NEUEN Stand (%d): %s"
                          % (len(v["nur_neu"]), v["nur_neu"][:6]))
                if v["nur_alt"]:
                    print("     nur im ALTEN Stand (%d): %s"
                          % (len(v["nur_alt"]), v["nur_alt"][:6]))
        for stelle in ("liste_raster", "form_raster"):
            if stelle in dn and stelle in da:
                rn = (dn[stelle] or {}).get("zeilen") or {}
                ra = (da[stelle] or {}).get("zeilen") or {}
                if not rn or not ra:
                    print("  %d px %s: leeres Raster - NICHT gemessen"
                          % (dn["breite"], stelle))
                    continue
                v = _raster_vergleich(rn, ra)
                v.update({"breite": dn["breite"], "stelle": stelle})
                raus.append(v)
                print("\n  %d px  %s  %d gemeinsame Stellen, %d > 1 px"
                      % (dn["breite"], stelle, v["gemeinsam"],
                         v["anzahl_abweichungen"]))
                for z in v["abweichungen"][:10]:
                    print("     %-46s %s  %s -> %s  (%+g)"
                          % (z["schluessel"][:46], z["feld"], z["alt"],
                             z["neu"], z["delta"]))
                if v["nur_neu"] or v["nur_alt"]:
                    print("     nur neu %d / nur alt %d"
                          % (len(v["nur_neu"]), len(v["nur_alt"])))
        # Feinmessungen im Klartext
        for stelle in ("liste", "form"):
            if stelle in dn and stelle in da:
                tn = dn[stelle]["titel"].get("titel")
                ta = da[stelle]["titel"].get("titel")
                if tn and ta:
                    print("\n  %d px  %s  TITEL  alt %s %s h=%s y=%s m=%s/%s"
                          % (dn["breite"], stelle, ta["tag"], ta["fontSize"],
                             ta["h"], ta["y"], ta["marginTop"],
                             ta["marginBottom"]))
                    print("                        neu %s %s h=%s y=%s m=%s/%s"
                          % (tn["tag"], tn["fontSize"], tn["h"], tn["y"],
                             tn["marginTop"], tn["marginBottom"]))
                dnn = dn[stelle]["titel"].get("darunter")
                daa = da[stelle]["titel"].get("darunter")
                if dnn and daa:
                    print("                        DARUNTER alt y=%s h=%s | "
                          "neu y=%s h=%s  (dy %+g)"
                          % (daa["y"], daa["h"], dnn["y"], dnn["h"],
                             round(dnn["y"] - daa["y"], 2)))
        for stelle in ("fahrzeuge", "fotos"):
            if stelle in dn and stelle in da:
                un = dn[stelle]["umschalter"]
                ua = da[stelle]["umschalter"]
                print("\n  %d px  %s  UMSCHALTER" % (dn["breite"], stelle))
                for kn, ka in zip(un["knoepfe"], ua["knoepfe"]):
                    print("     %s  alt %sx%s  neu %sx%s  (dw %+g dh %+g)  "
                          "title alt=%r neu=%r"
                          % (kn["rolle"], ka["w"], ka["h"], kn["w"], kn["h"],
                             round(kn["w"] - ka["w"], 2),
                             round(kn["h"] - ka["h"], 2),
                             ka["title"], kn["title"]))
                if un["leiste"] and ua["leiste"]:
                    print("     LEISTE alt %sx%s  neu %sx%s  (dw %+g dh %+g)"
                          % (ua["leiste"]["w"], ua["leiste"]["h"],
                             un["leiste"]["w"], un["leiste"]["h"],
                             round(un["leiste"]["w"] - ua["leiste"]["w"], 2),
                             round(un["leiste"]["h"] - ua["leiste"]["h"], 2)))
                print("     namenlose Knoepfe  alt %d  neu %d"
                      % (ua and da[stelle]["namen"]["anzahl_ohne"],
                         dn[stelle]["namen"]["anzahl_ohne"]))
                print("       alt ohne Namen: %s"
                      % [z["text"] for z in da[stelle]["namen"]["ohne"]][:12])
                print("       neu ohne Namen: %s"
                      % [z["text"] for z in dn[stelle]["namen"]["ohne"]][:12])
        for schl in ("form_ismob", "liste_ismob"):
            if schl in dn and schl in da:
                print("\n  %d px  %s" % (dn["breite"], schl))
                print("     Raster3   alt %s | neu %s"
                      % ([r["spalten"] for r in da[schl]["raster3"]],
                         [r["spalten"] for r in dn[schl]["raster3"]]))
                print("     Speicher  alt %s | neu %s"
                      % ([(s["richtung"], s["knopfbreiten"])
                          for s in da[schl]["speicherZeile"]],
                         [(s["richtung"], s["knopfbreiten"])
                          for s in dn[schl]["speicherZeile"]]))
                print("     Karten    alt %s | neu %s"
                      % ([(k["richtung"], k["ausrichtung"])
                          for k in da[schl]["kartenKopf"]][:3],
                         [(k["richtung"], k["ausrichtung"])
                          for k in dn[schl]["kartenKopf"]][:3]))
                print("     Chips     alt %s | neu %s"
                      % ([c["padding"] for c in da[schl]["chips"][:3]],
                         [c["padding"] for c in dn[schl]["chips"][:3]]))
        if "sweep" in dn and "sweep" in da:
            print("\n  %d px  NAMENS-SWEEP" % dn["breite"])
            print("     %-16s %-22s %-22s" % ("Ansicht", "alt", "neu"))
            for label in sorted(set(dn["sweep"]) | set(da["sweep"])):
                sa = da["sweep"].get(label) or {}
                sn = dn["sweep"].get(label) or {}
                if not sa.get("erreichbar") or not sn.get("erreichbar"):
                    print("     %-16s NICHT ERREICHBAR (alt %s / neu %s)"
                          % (label, sa.get("erreichbar"),
                             sn.get("erreichbar")))
                    continue
                print("     %-16s %2d/%3d ohne Namen %-8s %2d/%3d ohne Namen "
                      "%s"
                      % (label, sa["anzahl_ohne"], sa["gesamt"],
                         str(sa["ohne"])[:8], sn["anzahl_ohne"], sn["gesamt"],
                         str(sn["ohne"])[:30]))
        for schl in ("form_schrift", "liste_schrift"):
            if schl in dn and schl in da:
                print("     Schrift<12  alt %d/%d | neu %d/%d"
                      % (da[schl]["anzahl_klein"], da[schl]["gemessen"],
                         dn[schl]["anzahl_klein"], dn[schl]["gemessen"]))
    if neu.get("offen") or alt.get("offen"):
        print("\nNICHT GEMESSEN (keine bestandenen Faelle):")
        for z in (neu.get("offen") or []):
            print("   NEU " + z)
        for z in (alt.get("offen") or []):
            print("   ALT " + z)
    return raus


def main(argv):
    if "--vergleich" in argv:
        i = argv.index("--vergleich")
        _vergleich(argv[i + 1], argv[i + 2])
        return 0
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt.")
        return 2
    fall = argv[argv.index("--fall") + 1] if "--fall" in argv else "1"
    if fall not in FAELLE:
        print("--fall 1|2|3")
        return 2
    ziel = argv[argv.index("--json") + 1] if "--json" in argv else None
    breiten = FAELLE[fall]["breiten"]
    if "--breiten" in argv:
        breiten = [int(x) for x in argv[argv.index("--breiten") + 1].split(",")]

    datei = os.environ.get("EPK_INDEX", "index.html")
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port, datei)
    import hashlib
    h = hashlib.md5(io.open(os.path.join(WURZEL, datei), "rb").read()
                    ).hexdigest()
    print("Fall %s: %s" % (fall, FAELLE[fall]["was"]))
    print("Gemessen wird: %s" % url)
    print("md5 der gemessenen Datei: %s" % h)
    print("Breiten: %s" % breiten)

    alles, offen = [], []
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for breite in breiten:
            hoehe = 900 if breite >= 600 else 844
            d, o, _f = _lauf(br, url, fall, breite, hoehe)
            alles.append(d)
            offen += o
        br.close()

    if ziel:
        io.open(ziel, "w", encoding="utf-8", newline="\n").write(
            json.dumps({"md5": h, "datei": datei, "fall": fall,
                        "laeufe": alles, "offen": offen},
                       indent=1, ensure_ascii=False))
        print("\nJSON: %s" % ziel)
    if offen:
        print("\nNICHT GEMESSEN (das sind KEINE bestandenen Faelle):")
        for z in offen:
            print("   " + z)
        return 1
    print("\nAlle Koeder haben angeschlagen.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
