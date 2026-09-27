# -*- coding: utf-8 -*-
"""Alle 22 Ansichten bei 390 UND 1440 px an REALITAETSNAHEN Mengen messen.

WAS GEMESSEN WIRD - je Ansicht und je Breite
────────────────────────────────────────────
  1. Elemente unter 12 px            (B.SCHRIFT_JS, unveraendert benutzt)
  2. Tippziele unter 44 px           (B.TIPP_JS, Topf „knopf")
  3. horizontaler Ueberlauf          (B.QUER_JS) - und je Fund getrennt:
       * rollt der Behaelter?  -> `in_rollbar` gesetzt / eigener Roller
       * geht etwas verloren?  -> ueber innerWidth hinaus UND kein rollbarer
                                  Vorfahr: der Inhalt wird still abgeschnitten
  4. Emoji in KNOPFTEXTEN            (PIKTO_JS, neu - siehe unten)
  5. Icon-Knoepfe ohne aria-label UND ohne title  (B.EMOJI_JS, `ohne_hilfe`)

WARUM 4 NEU IST UND 5 NICHT
───────────────────────────
`B.EMOJI_JS` faengt nur Bedienelemente, deren GANZER Text zeichenlos ist
(kein Buchstabe, keine Ziffer) - also den Icon-Knopf. Ein Knopf
„🔧 Werkzeug ausgeben" traegt Buchstaben und faellt dort per Vorschrift heraus.
Punkt 4 des Auftrags fragt aber nach Emoji IN Knopftexten. Das ist eine andere
Grundgesamtheit, also ein eigener Melder - mit eigenen Koedern.

🔴 KEINE AUFGEZAEHLTE ZEICHENLISTE. Genau daran ist der erste Emoji-Melder
gescheitert (die Geometrischen Formen ▲▼◀▶ standen in keinem Bereich, also
galt so ein Knopf als „traegt Text"). PIKTO_JS fragt statt einer Liste nach
der Unicode-KATEGORIE: ein Piktogramm ist ein Zeichen aus \\p{S} (Symbol),
das kein Waehrungszeichen (\\p{Sc}) und nicht ASCII ist. Damit sind
🔧 (So, astral), ▲ (So, BMP), ✏️ (So + Variantenselektor) und → (Sm, aber
nicht ASCII) alle erfasst, ohne dass ein Bereich aufgezaehlt wird.

  Was dieser Melder BEWUSST nicht meldet und was das kostet:
    * ASCII-Symbole (+ - < = ~ ^ |): sonst waere jeder Knopf „Preis + Zuschlag"
      ein Befund.
    * Waehrungszeichen (€ $ £): „1.250,00 €" ist kein Emoji.
    * Hochgestellte Ziffern (m²): Kategorie No, kein Symbol.
  Was er mitzaehlt, obwohl es kein Emoji ist: mathematische Nicht-ASCII-Zeichen
  wie × ± ≥ ÷. Ein Knopf „5 × 3" wuerde gemeldet. Diese Unschaerfe steht im
  Bericht, sie ist nicht wegmessbar - und sie faellt zur SICHEREN Seite, weil
  sie zu VIEL meldet und nicht zu wenig.

DIE MINDESTMENGE
────────────────
Zwei Tore, und beide koennen einen Lauf als NICHT AUSSAGEKRAEFTIG stempeln -
niemals als bestanden:

  Tor A (Saat, einmal je Lauf). `echtmengen_saat.mindestmenge_pruefen` gegen
     das, was aus der Datenbank ZURUECKGELESEN wurde - nicht gegen das, was
     hineingeschrieben werden sollte.
  Tor B (Ansicht, je Aufnahme). Die Ansicht muss mindestens
     MINDEST_MARKEN_IN_ANSICHT verschiedene Saatmarken zeigen. Zeigt sie
     weniger, sind ihre Zahlen die eines leeren Blatts.

🔴 EIN ZAEHLENDER MELDER BRAUCHT EINEN KOEDER, UND ZWAR EINEN JE FORM.
Tor A hat zwei: die LEERE Saat und die ALTE, duenne Saat aus v3.9.954. Die
zweite ist die wichtigere - faengt der Melder nur die leere, dann prueft er
auf „ueberhaupt Daten" statt auf „genug Daten", und das ist ein anderer Melder
als der behauptete. Tor B hat einen eigenen Lauf mit leerer Saat.

AUFRUF
──────
    python scripts/echtmengen_messen.py --koeder     # nur die Selbstproben
    python scripts/echtmengen_messen.py             # alle 22 x 2
    python scripts/echtmengen_messen.py --nur fahrzeuge
"""
import io
import json
import os
import sys
import time

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import mob_ansicht_messen as M           # noqa: E402
import b3_vier_ansichten_messen as B     # noqa: E402
import b3_stufen_8_11_messen as S        # noqa: E402
import b3_stufen_12_15_messen as B12     # noqa: E402
import echtmengen_saat as SAAT           # noqa: E402

WURZEL = os.path.dirname(HIER)

# (Kuerzel der Gruppe, Modul, Navigator, Argumentzahl) - dieselbe Tabelle wie
# in grundstand_erheben.py, damit die Wege dieselben sind.
GRUPPEN = [
    ("4-7",   B,   "_navigieren",   3),
    ("8-11",  S,   "_navigieren8",  4),
    ("12-15", B12, "_navigieren12", 4),
]


# ══════════════════════════════════════════════════════════════════════════
# Der neue Melder: Piktogramme IM Text eines Bedienelements
# ══════════════════════════════════════════════════════════════════════════
PIKTO_JS = r"""() => {
  // Ein Piktogramm: Unicode-Kategorie Symbol, kein Waehrungszeichen,
  // nicht ASCII. Keine aufgezaehlte Bereichsliste - eine Liste ist genau die
  // Fehlerform, an der der erste Emoji-Melder blind war.
  const PIKTO = /[^\x00-\x7F]/u;
  const istPikto = (ch) => {
    if (ch.codePointAt(0) < 128) return false;
    if (/\p{Sc}/u.test(ch)) return false;
    return /\p{S}/u.test(ch);
  };
  const BUCHSTABE = /[\p{L}\p{N}]/u;
  const sicht = e => {
    const r = e.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return false;
    const c = getComputedStyle(e);
    return c.visibility !== 'hidden' && c.display !== 'none'
           && parseFloat(c.opacity || '1') >= 0.05;
  };
  const weg = e => {
    const t = []; let x = e;
    while (x && x.nodeType === 1 && t.length < 4) {
      let s = x.tagName.toLowerCase();
      if (x.id) { s += '#' + x.id; t.unshift(s); break; }
      const k = (x.className && typeof x.className === 'string')
        ? x.className.trim().split(/\s+/)[0] : '';
      if (k) s += '.' + k;
      t.unshift(s); x = x.parentElement;
    }
    return t.join(' > ');
  };
  const mitText = [], nurZeichen = [];
  document.querySelectorAll('button, [role="button"], a, summary')
    .forEach(e => {
      if (!sicht(e)) return;
      const roh = (e.textContent || '').replace(/\s+/g, ' ').trim();
      if (!roh) return;
      if (!PIKTO.test(roh)) return;
      const zeichen = [];
      for (const ch of roh) if (istPikto(ch)) zeichen.push(ch);
      if (!zeichen.length) return;
      const x = {text: roh.slice(0, 44), zeichen: zeichen.join(''),
                 anzahl_zeichen: zeichen.length, weg: weg(e),
                 title: e.getAttribute('title'),
                 aria: e.getAttribute('aria-label')};
      // Getrennt gefuehrt: ein Knopf, der NEBEN dem Piktogramm Text traegt
      // (das ist Punkt 4 des Auftrags), und einer, der nur aus Zeichen
      // besteht (das ist Punkt 5 und wird von B.EMOJI_JS gezaehlt).
      if (BUCHSTABE.test(roh)) mitText.push(x); else nurZeichen.push(x);
    });
  return {mit_text: mitText, anzahl_mit_text: mitText.length,
          nur_zeichen: nurZeichen, anzahl_nur_zeichen: nurZeichen.length};
}"""

# ── Koeder fuer PIKTO_JS: EIN KOEDER JE FORM ──────────────────────────────
# Vier Formen, und keine teilt die Luecke einer anderen:
#   F1  astrales Piktogramm            U+1F527      (So, ausserhalb der BMP)
#   F2  geometrische Form              U+25B2       (So, in der BMP - genau
#                                      die Form, an der die erste Fassung des
#                                      Emoji-Melders blind war)
#   F3  Piktogramm mit Variantenwahl   U+270F U+FE0F (So + Cf)
#   F4  Pfeil                          U+2192       (Sm, NICHT So - eine
#                                      Regel „nur So" waere hier blind)
# Jeder Koeder traegt NEBEN dem Zeichen ein Wort. Ein Koeder, der nur aus dem
# Zeichen besteht, wuerde auch von B.EMOJI_JS gefangen und wuerde nicht
# belegen, dass dieser Melder etwas Eigenes findet.
KOEDER_PIKTO_EIN = r"""() => {
  const w = document.getElementById('root') || document.body;
  let z = document.getElementById('__pk_zone');
  if (!z) { z = document.createElement('div'); z.id = '__pk_zone'; w.appendChild(z); }
  z.innerHTML = '';
  const mach = (id, txt) => {
    const b = document.createElement('button');
    b.id = id; b.textContent = txt; z.appendChild(b); return b.textContent;
  };
  const treffer = {
    F1_astral:   mach('__pk_f1', '\u{1F527} Werkzeug ausgeben'),
    F2_geo:      mach('__pk_f2', '▲ Sortierung aufsteigend'),
    F3_variante: mach('__pk_f3', '✏️ Schein bearbeiten'),
    F4_pfeil:    mach('__pk_f4', 'Weiter → Schritt 2')
  };
  // Gegenproben: keiner davon darf gemeldet werden.
  const gegen = {
    G1_waehrung: mach('__pk_g1', 'Summe 1.250,00 € uebernehmen'),
    G2_ascii:    mach('__pk_g2', 'Preis + Zuschlag = Endsumme'),
    G3_hoch:     mach('__pk_g3', 'Flaeche 12 m² erfassen'),
    G4_wort:     mach('__pk_g4', 'Speichern')
  };
  return {treffer: treffer, gegen: gegen};
}"""

KOEDER_PIKTO_MESSEN = r"""() => {
  const z = document.getElementById('__pk_zone');
  if (!z) return null;
  const PIKTO_ID = ['__pk_f1', '__pk_f2', '__pk_f3', '__pk_f4'];
  const GEGEN_ID = ['__pk_g1', '__pk_g2', '__pk_g3', '__pk_g4'];
  const istPikto = (ch) => {
    if (ch.codePointAt(0) < 128) return false;
    if (/\p{Sc}/u.test(ch)) return false;
    return /\p{S}/u.test(ch);
  };
  const urteil = {};
  PIKTO_ID.concat(GEGEN_ID).forEach(id => {
    const b = document.getElementById(id);
    if (!b) { urteil[id] = 'FEHLT'; return; }
    const roh = (b.textContent || '').trim();
    let n = 0;
    for (const ch of roh) if (istPikto(ch)) n++;
    urteil[id] = n;
  });
  return urteil;
}"""

KOEDER_PIKTO_AUS = r"""() => {
  const z = document.getElementById('__pk_zone');
  if (z && z.parentElement) z.parentElement.removeChild(z);
  return !document.getElementById('__pk_zone');
}"""

# Kreuzprobe: der Icon-Melder (B.EMOJI_JS) und der Text-Melder (PIKTO_JS)
# duerfen NICHT dieselbe Menge messen. Ein Knopf nur aus Zeichen gehoert dem
# einen, einer mit Wort daneben dem anderen.
KOEDER_ICON_EIN = r"""() => {
  const w = document.getElementById('root') || document.body;
  let z = document.getElementById('__ik_zone');
  if (!z) { z = document.createElement('div'); z.id = '__ik_zone'; w.appendChild(z); }
  z.innerHTML = '';
  const mach = (id, txt, titel) => {
    const b = document.createElement('button');
    b.id = id; b.textContent = txt;
    if (titel) b.setAttribute('title', titel);
    z.appendChild(b); return b.textContent;
  };
  return {
    I1_ohne_namen: mach('__ik_1', '\u{1F5D1}', null),   // MUSS Befund sein
    I2_geo_ohne:   mach('__ik_2', '▼', null),      // MUSS Befund sein
    I3_mit_title:  mach('__ik_3', '⚙', 'Einstellungen')  // darf NICHT
  };
}"""

KOEDER_ICON_AUS = r"""() => {
  const z = document.getElementById('__ik_zone');
  if (z && z.parentElement) z.parentElement.removeChild(z);
  return !document.getElementById('__ik_zone');
}"""

# Der Text der Ansicht, fuer Tor B.
TEXT_JS = r"""() => ((document.getElementById('root') || document.body)
                     .innerText || '')"""

# Wieviele Zeilen/Karten stehen wirklich da? Ohne diese Zahl ist „die Saat ist
# groesser" eine Behauptung ueber die Datenbank, nicht ueber die Ansicht.
ZEILEN_JS = r"""() => {
  const sicht = e => {
    const r = e.getBoundingClientRect();
    return r.width > 1 && r.height > 1;
  };
  const z = Array.from(document.querySelectorAll('tbody tr')).filter(sicht);
  const alle = Array.from(document.querySelectorAll('tr')).filter(sicht);
  return {tbody_zeilen: z.length, alle_zeilen: alle.length,
          tabellen: document.querySelectorAll('table').length,
          knoepfe: Array.from(document.querySelectorAll('button'))
                        .filter(sicht).length,
          textlaenge: ((document.getElementById('root') || document.body)
                       .innerText || '').length};
}"""

# Die Saat zurueckLESEN - nicht das, was hineingeschrieben werden sollte.
ZURUECK_JS = r"""
(async (cfg) => {
  const oeffnen = (name) => new Promise((res, rej) => {
    const r = indexedDB.open(name);
    r.onsuccess = () => res(r.result);
    r.onerror = () => rej(r.error);
  });
  const db = await oeffnen(cfg.db);
  const vorhanden = Array.from(db.objectStoreNames);
  const aus = {};
  for (const store of cfg.stores) {
    if (vorhanden.indexOf(store) < 0) { aus[store] = -1; continue; }
    aus[store] = await new Promise((res) => {
      const tx = db.transaction(store, 'readonly');
      const rq = tx.objectStore(store).get('data');
      rq.onsuccess = () => {
        const v = rq.result;
        if (Array.isArray(v)) return res(v.length);
        if (v && typeof v === 'object') return res(Object.keys(v).length);
        return res(-2);
      };
      rq.onerror = () => res(-3);
    });
  }
  let aktiv = 0, weg = 0;
  if (vorhanden.indexOf('monteure') >= 0) {
    const liste = await new Promise((res) => {
      const tx = db.transaction('monteure', 'readonly');
      const rq = tx.objectStore('monteure').get('data');
      rq.onsuccess = () => res(Array.isArray(rq.result) ? rq.result : []);
      rq.onerror = () => res([]);
    });
    liste.forEach(m => { if (m && m.austritt) weg++; else aktiv++; });
  }
  return {mengen: aus, monteure_aktiv: aktiv, monteure_ausgetreten: weg};
})
"""

STORES = ["monteure", "arbeitsscheine", "projects", "entries", "werkzeuge",
          "fahrzeuge"]


# ══════════════════════════════════════════════════════════════════════════
# Saat und Tore
# ══════════════════════════════════════════════════════════════════════════
def _saeen(seite, daten, still=False):
    """Saeen mit S.SEED2_JS (dem Rueckleser, der auch Objekte kennt)."""
    erg = seite.evaluate(S.SEED2_JS, {"db": M.DB_NAME, "daten": daten})
    if erg.get("fehlend") and not still:
        print("   HINWEIS: diese Speicher gibt es nicht: %s"
              % ", ".join(erg["fehlend"]))
    seite.evaluate("() => { try { localStorage.setItem("
                   "'epk_last_juprowa_pull', String(Date.now())); } "
                   "catch(e){} }")
    seite.reload(wait_until="domcontentloaded")
    seite.wait_for_timeout(7200)
    return erg


def _tor_a(seite):
    """Tor A: die Mindestmenge gegen die ZURUECKGELESENE Saat."""
    zu = seite.evaluate(ZURUECK_JS, {"db": M.DB_NAME, "stores": STORES})
    ist = dict(zu["mengen"])
    ist["monteure_aktiv"] = zu["monteure_aktiv"]
    ist["monteure_ausgetreten"] = zu["monteure_ausgetreten"]
    return SAAT.mindestmenge_pruefen(ist), ist


def _tor_b(text):
    """Tor B: genug verschiedene Saatmarken in DIESER Ansicht?"""
    marken = SAAT.marken_im_text(text)
    if len(marken) < SAAT.MINDEST_MARKEN_IN_ANSICHT:
        return (["nur %d von mindestens %d verschiedenen Saatmarken in der "
                 "Ansicht: %s" % (len(marken), SAAT.MINDEST_MARKEN_IN_ANSICHT,
                                  marken or "keine")], marken)
    return [], marken


# ══════════════════════════════════════════════════════════════════════════
# Die Koeder aller fuenf Messungen
# ══════════════════════════════════════════════════════════════════════════
def _koeder(seite):
    """Je Messung ein Koeder, je FORM einer. Gibt (alles_gruen, Protokoll)."""
    zeilen, ok = [], True

    def sag(name, traf, wie):
        nonlocal ok
        zeilen.append((name, bool(traf), wie))
        if not traf:
            ok = False

    # ── 1. Elemente unter 12 px ───────────────────────────────────────────
    px = seite.evaluate(B.KOEDER_SCHRIFT_EIN)
    s = seite.evaluate(B.SCHRIFT_JS)
    sag("M1 Schrift <12px", any(x["text"].startswith("KOEDER Schrift")
                                for x in s["klein"]),
        "9-px-Text, gemessen als %s px" % px)

    # ── 2. Tippziele unter 44 px ──────────────────────────────────────────
    tipp = seite.evaluate(B.KOEDER_TIPP_EIN)
    n_tipp = seite.evaluate(B.KOEDER_TIPP_MESSEN)
    sag("M2 Tippziel <44px", n_tipp == 1,
        "Koederknopf %sx%s px (die Hausregel traegt !important und wird "
        "uebersteuert), Melder fand %s" % (tipp.get("w"), tipp.get("h"),
                                           n_tipp))

    # ── 3. Querueberlauf ──────────────────────────────────────────────────
    quer = seite.evaluate(B.KOEDER_QUER_EIN)
    q = seite.evaluate(B.QUER_JS)
    sag("M3 Ueberlauf", any(x["breite"] >= 2900 for x in q["ursache"]),
        "3000-px-Kind: Rechteck %s px, scrollWidth %s -> %s (waechst NICHT, "
        "der Inhalt wird abgeschnitten von %s) - darum wird ueber die "
        "Rechtecke gemessen und nicht ueber scrollWidth"
        % (quer["koeder_breite"], quer["vorher"], quer["mit_koeder"],
           quer["abschneidender_vorfahr"]))

    # ── 4. Piktogramm IM Knopftext: vier Formen, vier Gegenproben ─────────
    seite.evaluate(KOEDER_PIKTO_EIN)
    urteil = seite.evaluate(KOEDER_PIKTO_MESSEN)
    p = seite.evaluate(PIKTO_JS)
    wege = {x["weg"]: x for x in p["mit_text"]}
    for kurz, form in (("f1", "F1 astral \U0001F527"),
                       ("f2", "F2 geometrisch ▲"),
                       ("f3", "F3 Variantenwahl ✏️"),
                       ("f4", "F4 Pfeil → (Kategorie Sm, nicht So)")):
        gefunden = any(("#__pk_" + kurz) in w for w in wege)
        sag("M4 Pikto %s" % form, gefunden,
            "Zeichenzahl im Koeder: %s, im Melder gefunden: %s"
            % (urteil.get("__pk_" + kurz), gefunden))
    for kurz, was in (("g1", "Waehrung €"), ("g2", "ASCII +="),
                      ("g3", "hochgestellt m²"), ("g4", "reines Wort")):
        gemeldet = any(("#__pk_" + kurz) in w for w in wege)
        sag("M4 GEGENPROBE %s" % was, not gemeldet,
            "darf NICHT gemeldet werden; gemeldet: %s (Zeichenzahl %s)"
            % (gemeldet, urteil.get("__pk_" + kurz)))

    # ── 5. Icon-Knopf ohne aria-label UND ohne title ──────────────────────
    seite.evaluate(KOEDER_ICON_EIN)
    e = seite.evaluate(B.EMOJI_JS)
    ohne = {x["weg"]: x for x in e["ohne_hilfe"]}
    mit = {x["weg"]: x for x in e["mit_hilfe"]}
    sag("M5 Icon astral \U0001F5D1", any("#__ik_1" in w for w in ohne),
        "Knopf nur \U0001F5D1, kein title, kein aria-label")
    sag("M5 Icon geometrisch ▼", any("#__ik_2" in w for w in ohne),
        "Knopf nur ▼ - genau die Form, an der die erste Fassung des "
        "Melders blind war")
    sag("M5 GEGENPROBE mit title", (not any("#__ik_3" in w for w in ohne))
        and any("#__ik_3" in w for w in mit),
        "Knopf ⚙ MIT title gehoert nach `mit_hilfe`, nicht in den Befund")

    # ── Kreuzprobe: die beiden Emoji-Melder messen NICHT dasselbe ─────────
    p2 = seite.evaluate(PIKTO_JS)
    icon_in_pikto_text = any("#__ik_1" in x["weg"] for x in p2["mit_text"])
    pikto_in_icon = any("#__pk_f1" in w for w in ohne)
    sag("Kreuzprobe M4/M5", (not icon_in_pikto_text) and (not pikto_in_icon),
        "der reine Icon-Knopf darf NICHT in `mit_text` stehen (%s) und der "
        "Knopf mit Wort NICHT im Icon-Befund (%s) - messen sie dasselbe, ist "
        "einer der beiden ueberfluessig"
        % (icon_in_pikto_text, pikto_in_icon))

    # ── Aufraeumen und belegen, dass aufgeraeumt ist ──────────────────────
    weg1 = seite.evaluate(KOEDER_PIKTO_AUS)
    weg2 = seite.evaluate(KOEDER_ICON_AUS)
    rest = seite.evaluate(B.KOEDER_AUS)
    sag("Koeder restlos entfernt", weg1 and weg2 and not rest,
        "pikto=%s icon=%s rest=%s" % (weg1, weg2, rest))
    return ok, zeilen


# ══════════════════════════════════════════════════════════════════════════
# Ein Lauf
# ══════════════════════════════════════════════════════════════════════════
def _ctx(browser, breite):
    ctx = browser.new_context(viewport={"width": breite, "height": 880},
                              is_mobile=breite < 600, has_touch=breite < 600,
                              color_scheme="dark")
    ctx.add_init_script(M.INIT)
    ctx.add_init_script(
        "try{var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
        "u.monteurId='M1';u.name='Gerhard Steinbichler';u.role='admin';"
        "u.rolle='Geschaeftsfuehrer';"
        "localStorage.setItem('epkolar_user',JSON.stringify(u));}catch(e){}")
    ctx.route("**/rest/v1/**", lambda r: r.abort())
    ctx.route("**/auth/v1/**", lambda r: r.abort())
    return ctx


def _messen(seite):
    d = {}
    d["schrift"] = seite.evaluate(B.SCHRIFT_JS)
    d["tipp"] = seite.evaluate(B.TIPP_JS)
    d["quer"] = seite.evaluate(B.QUER_JS)
    d["pikto"] = seite.evaluate(PIKTO_JS)
    d["icon"] = seite.evaluate(B.EMOJI_JS)
    d["zeilen"] = seite.evaluate(ZEILEN_JS)
    return d


def _eine(browser, url, gruppe, modul, navi, argzahl, kuerzel, breite,
          daten, mit_koeder=False):
    ctx = _ctx(browser, breite)
    seite = ctx.new_page()
    fehler = []
    seite.on("pageerror", lambda x: fehler.append(str(x)[:170]))
    aus = {"gruppe": gruppe, "kuerzel": kuerzel, "breite": breite,
           "titel": modul.ANSICHTEN[kuerzel].get("titel", kuerzel)}
    try:
        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(3800)
        _saeen(seite, daten, still=True)
        aus["tor_a"], aus["saat_ist"] = _tor_a(seite)
        f = getattr(modul, navi)
        try:
            weg = (f(seite, kuerzel, breite, []) if argzahl == 4
                   else f(seite, kuerzel, breite))
        except Exception as e:
            weg, aus["navi_fehler"] = None, str(e)[:160]
        seite.wait_for_timeout(1800)
        aus["weg"] = str(weg)[:120]
        if weg in (None, "nicht-gefunden"):
            aus["nicht_erreicht"] = True
        text = seite.evaluate(TEXT_JS)
        aus["tor_b"], aus["marken"] = _tor_b(text)
        aus.update(_messen(seite))
        if mit_koeder:
            aus["koeder_ok"], aus["koeder"] = _koeder(seite)
        aus["seitenfehler"] = fehler[:3]
        return aus
    finally:
        ctx.close()


def _kurz(a):
    """Die fuenf Zahlen einer Aufnahme."""
    q = a.get("quer") or {}
    verloren = len([x for x in (q.get("ursache") or []) if not x["in_rollbar"]])
    roller = len(q.get("waagrechte_roller") or [])
    return {
        "klein12": (a.get("schrift") or {}).get("anzahl_klein"),
        "tipp44": (a.get("tipp") or {}).get("anzahl_klein"),
        "ueberlauf_verloren": verloren,
        "ueberlauf_roller": roller,
        "pikto_im_text": (a.get("pikto") or {}).get("anzahl_mit_text"),
        "icon_ohne_namen": (a.get("icon") or {}).get("anzahl_ohne"),
        "zeilen": (a.get("zeilen") or {}).get("tbody_zeilen"),
        "knoepfe": (a.get("zeilen") or {}).get("knoepfe"),
    }


def main(argv):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt.")
        return 2
    nur = argv[argv.index("--nur") + 1] if "--nur" in argv else None
    nur_koeder = "--koeder" in argv
    # --saat alt: dieselben Melder, dieselbe Fassung von index.html, aber die
    # DUENNE Saat aus v3.9.954. Nur so laesst sich „die Saat war zu duenn" von
    # „der Umbau hat nichts geaendert" trennen - ein Vergleich gegen die
    # Zahlen eines ANDEREN Messskripts vergleicht zwei Dinge auf einmal.
    alte_saat = "--saat" in argv and argv[argv.index("--saat") + 1] == "alt"

    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port,
                                      os.environ.get("EPK_INDEX", "index.html"))
    voll = SAAT.saat_duenn() if alte_saat else SAAT.saat()
    if alte_saat:
        print("🔴 LAUF MIT DER ALTEN, DUENNEN SAAT (v3.9.954-Stand).")
        print("   Er ist per Tor A NICHT AUSSAGEKRAEFTIG und dient nur dem "
              "Vergleich: %s" % "; ".join(SAAT.mindestmenge_pruefen(voll)))
    t0 = time.time()
    ergebnis = {"saat_soll": SAAT.mengen_aus_saat(voll), "aufnahmen": [],
                "koeder": None, "tor_b_koeder": None,
                "saat_art": "alt-duenn" if alte_saat else "echtmengen"}

    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ── Selbstproben zuerst. Ein Lauf vor der Selbstprobe ist eine
        #    Zahl ohne Belegung.
        print("\n═══ KOEDER (alle fuenf Messungen, 1440 px, Ansicht fahrzeuge)")
        k = _eine(browser, url, "12-15", B12, "_navigieren12", 4,
                  "fahrzeuge", 1440, voll, mit_koeder=True)
        for name, traf, wie in k.get("koeder", []):
            print("   %-28s %s  (%s)"
                  % (name, "ANGESCHLAGEN" if traf else "STUMM", wie))
        ergebnis["koeder"] = {"ok": k.get("koeder_ok"),
                              "zeilen": k.get("koeder"),
                              "tor_a": k.get("tor_a"),
                              "saat_ist": k.get("saat_ist")}
        print("   Tor A an der vollen Saat: %s"
              % (k["tor_a"] or "keine Verletzung (richtig)"))

        # ── Koeder fuer Tor B: LEERE Saat in derselben Ansicht.
        print("\n═══ KOEDER Tor B: dieselbe Ansicht mit LEERER Saat")
        leer = _eine(browser, url, "12-15", B12, "_navigieren12", 4,
                     "fahrzeuge", 1440, SAAT.saat_leer())
        print("   Tor A meldet: %s" % (leer["tor_a"] or "NICHTS - STUMM"))
        print("   Tor B meldet: %s" % (leer["tor_b"] or "NICHTS - STUMM"))
        print("   Gegenprobe volle Saat, Tor B: %s"
              % (k["tor_b"] or "nichts (richtig)"))
        ergebnis["tor_b_koeder"] = {
            "leer_tor_a": leer["tor_a"], "leer_tor_b": leer["tor_b"],
            "voll_tor_b": k["tor_b"], "leer_marken": leer["marken"],
            "voll_marken": k["marken"],
            "leer_zahlen": _kurz(leer), "voll_zahlen": _kurz(k)}
        tor_b_ok = bool(leer["tor_a"]) and bool(leer["tor_b"]) \
            and not k["tor_b"]
        print("   -> Tor B %s" % ("TRAEGT" if tor_b_ok else "TRAEGT NICHT"))

        if nur_koeder:
            browser.close()
            _schreiben(ergebnis)
            return 0 if (k.get("koeder_ok") and tor_b_ok) else 1

        # ── Alle 22 Ansichten, beide Breiten ─────────────────────────────
        print("\n═══ ALLE ANSICHTEN, 390 und 1440 px")
        for gruppe, modul, navi, argzahl in GRUPPEN:
            for kuerzel in modul.ANSICHTEN:
                if nur and kuerzel != nur:
                    continue
                for breite in (390, 1440):
                    try:
                        a = _eine(browser, url, gruppe, modul, navi, argzahl,
                                  kuerzel, breite, voll)
                    except Exception as e:
                        a = {"gruppe": gruppe, "kuerzel": kuerzel,
                             "breite": breite, "abbruch": str(e)[:200],
                             "titel": modul.ANSICHTEN[kuerzel].get("titel")}
                    ergebnis["aufnahmen"].append(a)
                    z = _kurz(a)
                    stempel = ("ABBRUCH" if a.get("abbruch") else
                               ("NICHT ERREICHT" if a.get("nicht_erreicht")
                                else ("NICHT AUSSAGEKRAEFTIG"
                                      if (a.get("tor_a") or a.get("tor_b"))
                                      else "gemessen")))
                    print("  %-13s %-5d %-22s <12px=%s tipp<44=%s "
                          "verl=%s roll=%s pikto=%s icon=%s zeilen=%s"
                          % (kuerzel, breite, stempel, z["klein12"],
                             z["tipp44"], z["ueberlauf_verloren"],
                             z["ueberlauf_roller"], z["pikto_im_text"],
                             z["icon_ohne_namen"], z["zeilen"]))
        browser.close()

    print("\n%d Aufnahmen in %.0f s" % (len(ergebnis["aufnahmen"]),
                                        time.time() - t0))
    _schreiben(ergebnis)
    return 0


def _kuerzen(a):
    """Die Beispiellisten auf ein handliches Mass bringen.

    Die ZAHLEN bleiben unangetastet - gekuerzt werden nur die Beispiele.
    Eine 40-MB-Rohdatei waere selbst ein Befund: mein Kommentar hat am
    26.09. einen fremden Riegel rot gemacht, weil sein Auszieher 95 000
    Zeichen nahm.
    """
    s = a.get("schrift")
    if s:
        s["klein"] = s.get("klein", [])[:12]
        s.pop("verteilung", None)
    t = a.get("tipp")
    if t:
        t["klein"] = t.get("klein", [])[:12]
        t["felder_klein"] = t.get("felder_klein", [])[:6]
    q = a.get("quer")
    if q:
        q["ursache"] = q.get("ursache", [])[:4]
        q["waagrechte_roller"] = q.get("waagrechte_roller", [])[:4]
    p = a.get("pikto")
    if p:
        p["mit_text"] = p.get("mit_text", [])[:12]
        p["nur_zeichen"] = p.get("nur_zeichen", [])[:6]
    i = a.get("icon")
    if i:
        i["ohne_hilfe"] = i.get("ohne_hilfe", [])[:12]
        i["mit_hilfe"] = i.get("mit_hilfe", [])[:6]
    a["zahlen"] = _kurz(a)
    return a


def _schreiben(ergebnis):
    for a in ergebnis.get("aufnahmen", []):
        _kuerzen(a)
    art = ergebnis.get("saat_art", "echtmengen")
    ziel = os.path.join(WURZEL, "scripts",
                        "_echtmengen_rohdaten%s.json"
                        % ("_alt" if art == "alt-duenn" else ""))
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps(ergebnis, ensure_ascii=False, indent=1))
    print("Rohdaten:", ziel)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
