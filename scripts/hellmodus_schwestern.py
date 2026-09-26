# -*- coding: utf-8 -*-
"""Die vier Schwestern-Flaechen des Plan-Befunds - und die Vollbild-Tore.

WARUM ES DIESE DATEI GIBT
─────────────────────────
scripts/hellmodus_ansichten.py hat den Nutzerbefund gefunden: die Plan-Flaeche
mit fest eingetragenem #1a1a1a. Im selben Quelltext stehen weitere fest
eingetragene dunkle Hintergruende. Die habe ich damals GELISTET und
ausdruecklich als NICHT GEMESSEN bezeichnet - eine Zeile im Quelltext ist kein
Befund. Diese Datei misst sie.

  #0a0c14 (rgb(10,12,20))   Zeilen 17154, 18439, 19191, 19207
  #0f172a (rgb(15,23,42))   Zeilen 7640, 7693, 9481, height:100dvh width:100vw
  #525659 (rgb(82,86,89))   Zeile 29019

WAS DER ERSTE LAUF NICHT SEHEN KONNTE
─────────────────────────────────────
Alle vier #0a0c14-Stellen brauchen DATEN: einen Plan oder ein Foto. Der Lauf
vom 26.09. hat jede Anfrage abgebrochen und nichts gesaet ausser Monteuren,
Arbeitsscheinen, Projekten und Zeiteintraegen. In der Ansicht Plaene stand
deshalb "Noch keine Plaene", und die vier Flaechen waren GAR NICHT IM BAUM.
Sie als "nicht gefunden" zu fuehren waere die Auskunft eines leeren
Renderpfads gewesen. Hier wird darum ein Plan und werden Fotos gesaet, und die
Saat wird ZURUECKGELESEN - erscheint sie nicht in der Ansicht, bricht der Lauf
fuer diese Stelle ab und meldet NICHT GEMESSEN.

WIE GEMESSEN WIRD
─────────────────
Mit demselben Rastermass wie in hellmodus_ansichten.py (SCHIRM_JS, dort
importiert): 24 x 40 Punkte, je Punkt elementFromPoint, Farbstapel gemischt,
Helligkeit. Es zaehlt, was man SIEHT, nicht das Rechteck im Baum. Zusaetzlich
wird je Stelle GEZIELT nachgesehen, ob ein Element mit genau dieser Farbe im
Baum steht und wie gross es ist - damit "nicht auf dem Schirm" von "gar nicht
da" unterschieden werden kann. Das sind zwei verschiedene Auskuenfte.

DER KOEDER
──────────
Je Ansicht wird auch im Dunkelmodus gemessen. Schlaegt das Rastermass dort
nicht an, misst es auch im Hellmodus nichts, und die Stelle ist NICHT
GEMESSEN. Zusaetzlich ist die Saat selbst ein Koeder: wird der gesaete Plan
bzw. das gesaete Foto in der Ansicht nicht sichtbar, ist die Stelle nicht
erreicht worden.

AUFRUF
──────
    python scripts/hellmodus_schwestern.py
    (misst index.html; EPK_INDEX setzt eine andere Datei)

Ergebnis: screenshots/hellmodus_schwestern.json
          Bilder in screenshots/schwestern_*.png
"""
import io
import json
import os
import sys
import time

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)

import mob_ansicht_messen as M  # noqa: E402
from hellmodus_ansichten import (SCHIRM_JS, ROLLEN_JS, WAEHLEN_JS,  # noqa: E402
                                 SHELL_WAEHLEN_JS, PROJEKT_OEFFNEN_JS,
                                 _nutzer, _saat)
from tab_sweep import INIT, DB_NAME  # noqa: E402

BREITEN = (390, 1440)
THEMEN = ("light", "dark")
TRAGEND_AB = 0.25

# Die gesuchten Farben, als rgb-Zeichenkette wie getComputedStyle sie liefert.
ZIELE = {
    "#0a0c14": "rgb(10, 12, 20)",
    "#0f172a": "rgb(15, 23, 42)",
    "#525659": "rgb(82, 86, 89)",
    "#1a1a1a": "rgb(26, 26, 26)",   # die behobene Stelle, zur Gegenprobe
}

# Zwei Bilder mit ECHTEM SEITENVERHAELTNIS, und das ist keine Feinheit.
#
# Der erste Anlauf saete ein 1x1-Bild. Bei `objectFit:"contain"` - so haengen
# die Planvorschauen - malt ein 1x1-Bild GENAU EINEN Bildpunkt aus; der Rest
# der Mulde bleibt frei. Die Messung meldete daraufhin 30,3 Prozent freie
# dunkle Flaeche bei 390 px, und das war eine Eigenschaft der SAAT, nicht der
# Anwendung. Ein Planblatt ist 1200 zu 850; das Bild hier hat dasselbe
# Verhaeltnis, damit der gemessene Rand der Rand ist, den ein Nutzer sieht.
# Fuer die Fotokacheln (`objectFit:"cover"`) ist das Verhaeltnis gleichgueltig,
# weil ein deckendes Bild die Mulde immer ganz fuellt - gemessen wird es
# trotzdem, statt es zu behaupten.
# Die Bilder werden GERECHNET statt abgeschrieben. Ein erster Anlauf hat die
# Base64-Zeichenkette von Hand umbrochen und dabei zerstoert; `b64decode`
# warf "Incorrect padding". Ein kaputtes Bild laedt nicht, `naturalWidth`
# bleibt 0, und die Mulde erscheint zu 100 Prozent frei - die Messung haette
# eine Eigenschaft der Saat als Befund gemeldet. Gerechnet ist es nachpruefbar.
def _png(breit, hoch, rgb):
    """Ein einfarbiges PNG als Datenadresse, ohne fremde Bibliothek."""
    import base64
    import struct
    import zlib
    roh = b"".join(b"\x00" + bytes(rgb) * breit for _ in range(hoch))

    def block(art, inhalt):
        return (struct.pack(">I", len(inhalt)) + art + inhalt
                + struct.pack(">I", zlib.crc32(art + inhalt) & 0xffffffff))

    daten = (b"\x89PNG\r\n\x1a\n"
             + block(b"IHDR", struct.pack(">IIBBBBB", breit, hoch, 8, 2, 0, 0, 0))
             + block(b"IDAT", zlib.compress(roh, 9))
             + block(b"IEND", b""))
    return "data:image/png;base64," + base64.b64encode(daten).decode()


# Ein Planblatt: 1200 zu 850, also 240 x 170, fast weiss.
PNG_PLAN = _png(240, 170, (246, 246, 244))
# Ein Foto: 4 zu 3, mittelgrau.
PNG_FOTO = _png(160, 120, (120, 130, 140))

# ── Saat: ein Plan und drei Fotos ─────────────────────────────────────────
# planData liegt im Speicher `planData` unter dem Schluessel "data",
# Projektfotos im Speicher `projektCache` unter "fotos_<Projekt-Id>".
SAAT_JS = r"""(cfg) => new Promise((fertig) => {
  const auf = indexedDB.open(cfg.db);
  auf.onsuccess = () => {
    const db = auf.result;
    const hat = Array.from(db.objectStoreNames);
    const fehlt = [];
    const schreiben = (store, key, wert) => new Promise((res) => {
      if (hat.indexOf(store) < 0) { fehlt.push(store); return res(); }
      const tx = db.transaction(store, 'readwrite');
      tx.objectStore(store).put(wert, key);
      tx.oncomplete = res; tx.onerror = res; tx.onabort = res;
    });
    const lesen = (store, key) => new Promise((res) => {
      if (hat.indexOf(store) < 0) return res(-1);
      const tx = db.transaction(store, 'readonly');
      const r = tx.objectStore(store).get(key);
      r.onsuccess = () => res(r.result);
      r.onerror = () => res(-2);
    });
    (async () => {
      await schreiben('planData', 'data', cfg.planData);
      await schreiben('projektCache', 'fotos_' + cfg.pid, cfg.fotos);
      // ZURUECKLESEN - die Eingabe zu melden waere keine Messung.
      const pd = await lesen('planData', 'data');
      const ft = await lesen('projektCache', 'fotos_' + cfg.pid);
      fertig({fehlt: fehlt,
              plaene: (pd && pd.plans) ? pd.plans.length : -3,
              fotos: Array.isArray(ft) ? ft.length : -3});
    })();
  };
  auf.onerror = () => fertig({fehler: String(auf.error)});
})"""

# Gezielt nachsehen: steht ein Element mit dieser Farbe im Baum, wie gross ist
# es, und liegt es im sichtbaren Ausschnitt? "Nicht auf dem Schirm" und "gar
# nicht da" sind zwei verschiedene Auskuenfte, und beide muessen benennbar sein.
SUCHE_JS = r"""(farben) => {
  const aus = {};
  Object.keys(farben).forEach(k => { aus[k] = []; });
  document.querySelectorAll('*').forEach(el => {
    const c = getComputedStyle(el).backgroundColor;
    for (const k of Object.keys(farben)) {
      if (c !== farben[k]) continue;
      const r = el.getBoundingClientRect();
      // Der Teil des Rechtecks, der wirklich im Fenster liegt.
      const bx = Math.max(0, Math.min(r.right, innerWidth) - Math.max(r.left, 0));
      const by = Math.max(0, Math.min(r.bottom, innerHeight) - Math.max(r.top, 0));
      aus[k].push({
        tag: el.tagName.toLowerCase(),
        klasse: String(el.className || '').slice(0, 40),
        voll: Math.round(r.width * r.height),
        sichtbar: Math.round(bx * by),
        anteil_sichtbar: (bx * by) / Math.max(1, innerWidth * innerHeight),
        oben: Math.round(r.top), links: Math.round(r.left),
        breit: Math.round(r.width), hoch: Math.round(r.height),
        text: String(el.innerText || '').replace(/\s+/g, ' ').slice(0, 50)});
      break;
    }
  });
  return aus;
}"""

TEXT_KLICK_JS = r"""(txt) => {
  const sichtbar = (b) => {
    const cs = getComputedStyle(b);
    if (cs.visibility === 'hidden' || cs.display === 'none') return false;
    const r = b.getBoundingClientRect();
    return r.width > 1 && r.height > 1;
  };
  const k = [...document.querySelectorAll('button, [role=button], div')]
    .filter(b => sichtbar(b)
                 && (b.innerText || '').replace(/\s+/g, ' ').trim() === txt);
  if (!k.length) return 'nicht-gefunden';
  k.sort((a, b) => {
    const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
    return (ra.width * ra.height) - (rb.width * rb.height);
  });
  k[0].click();
  return 'geklickt';
}"""

ENTHAELT_KLICK_JS = r"""(txt) => {
  const sichtbar = (b) => {
    const cs = getComputedStyle(b);
    if (cs.visibility === 'hidden' || cs.display === 'none') return false;
    const r = b.getBoundingClientRect();
    return r.width > 1 && r.height > 1;
  };
  const k = [...document.querySelectorAll('button, [role=button], div, span')]
    .filter(b => sichtbar(b) && (b.textContent || '').indexOf(txt) >= 0
                 && b.children.length <= 6);
  if (!k.length) return 'nicht-gefunden';
  k.sort((a, b) => {
    const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
    return (ra.width * ra.height) - (rb.width * rb.height);
  });
  k[0].click();
  return 'geklickt';
}"""

SICHTBAR_TEXT_JS = r"""(txt) => (document.body.innerText || '').indexOf(txt) >= 0"""

# KOEDER DER FOTO-SAAT, zweiter Anlauf.
# Der erste hat nach der Bildunterschrift im Text gesucht - die Ansicht
# rendert sie nicht, und die Messung meldete daraufhin "Fotos erscheinen
# NICHT" fuer alle vier Laeufe. Die Fotos WAREN da: sechs Zeilen lagen im
# Speicher projektCache, und die Ansicht zeigte sieben Bilder statt einem.
# Ein Koeder, der am falschen Merkmal haengt, macht eine gemessene Stelle zu
# einer ungemessenen - dieselbe Krankheit wie ein Riegel, der zu wenig findet.
# Jetzt zwei unabhaengige Merkmale: der LEERTEXT darf nicht stehen, UND es
# muessen mehr Bilder im Baum sein als ohne Saat.
FOTO_KOEDER_JS = r"""() => {
  const t = (document.body.innerText || '').replace(/\s+/g, ' ');
  return {leerText: t.indexOf('Noch keine Fotos in diesem Projekt') >= 0,
          bilder: document.querySelectorAll('img').length,
          datenBilder: document.querySelectorAll('img[src^="data:image"]').length};
}"""

# Der Unterreiter heisst am Rechner "📁 Planverwaltung 2" und am Telefon nur
# "📁 2" - dort steht die Reiterzeile eng und traegt nur das Zeichen. Der
# erste Lauf suchte nach dem Wort, fand am Telefon nichts, und 18439 blieb
# bei 390 px UNGEMESSEN, ohne dass es im Ergebnis aufgefallen waere.
# Der Umschalter auf die Listenansicht der Fotos traegt das Zeichen "☰" -
# und GENAU DASSELBE Zeichen traegt am Telefon der Hamburger, der die
# Seitenleiste der Projekt-Huelle aufklappt. Der legt eine halbdurchsichtige
# SCHWARZE Flaeche ueber den ganzen Schirm (`rgba(0,0,0,.5)`, `inset:0`).
# Ein Klick auf den falschen der beiden haette also 100 Prozent dunklen Schirm
# gemessen und als Befund gemeldet - eine Dunkelheit, die die Messung selbst
# erzeugt. Der Hamburger traegt ein aria-label, der Umschalter nicht.
LISTE_JS = r"""() => {
  const sichtbar = (b) => {
    const cs = getComputedStyle(b);
    if (cs.visibility === 'hidden' || cs.display === 'none') return false;
    const r = b.getBoundingClientRect();
    return r.width > 1 && r.height > 1;
  };
  const k = [...document.querySelectorAll('button')]
    .filter(b => sichtbar(b) && !b.getAttribute('aria-label')
                 && (b.innerText || '').trim() === '☰');
  if (!k.length) return 'nicht-gefunden';
  k[0].click();
  return 'geklickt/' + k.length;
}"""

# ZWEITER Fehler an derselben Stelle: am Rechner traegt die SEITENLEISTE der
# Projekt-Huelle den Eintrag "📁 Dokumente", und der steht im Baum VOR der
# Unterreiterzeile. Ein Griff nach dem ersten sichtbaren Knopf mit "📁" ging
# deshalb bei 1440 px auf DOKUMENTE - die Messung landete in einer ganz
# anderen Ansicht und meldete dort folgerichtig "keine Zielfarbe". Das sah aus
# wie ein sauberes Ergebnis und war eine verfehlte Ansicht. Gesucht wird
# darum ausdruecklich AUSSERHALB der Seitenleiste.
UNTERREITER_JS = r"""(zeichen) => {
  const sichtbar = (b) => {
    const cs = getComputedStyle(b);
    if (cs.visibility === 'hidden' || cs.display === 'none') return false;
    const r = b.getBoundingClientRect();
    return r.width > 1 && r.height > 1;
  };
  const k = [...document.querySelectorAll('button')]
    .filter(b => sichtbar(b) && !b.closest('.sidebar')
                 && (b.innerText || '').replace(/\s+/g, ' ').trim()
                    .indexOf(zeichen) === 0);
  if (!k.length) return 'nicht-gefunden';
  k[0].click();
  return 'geklickt/' + (k[0].innerText || '').replace(/\s+/g, ' ').trim();
}"""

# Gegenprobe NACH dem Klick: steht die Kachelwand der Planverwaltung wirklich
# da? Ohne sie waere jede Zahl von dort die Zahl irgendeiner Ansicht.
VERWALTUNG_DA_JS = r"""() => {
  const t = (document.body.innerText || '').replace(/\s+/g, ' ');
  return t.indexOf('Plan hochladen') >= 0
         && t.indexOf('Grundriss Erdgeschoss') >= 0;
}"""


def _plan_saat(pid):
    return {
        "plans": [
            {"id": "PL1", "pid": pid, "name": "Grundriss Erdgeschoss Bauteil B",
             "dataUrl": PNG_PLAN, "width": 1200, "height": 850, "isPdf": False,
             "geschoss": "EG", "uploadedAt": "2026-09-20",
             "uploadedBy": "Gerhard Steinbichler",
             "takenAt": "2026-09-20T08:00:00.000Z"},
            {"id": "PL2", "pid": pid, "name": "Strangschema Heizung OG2",
             "dataUrl": PNG_PLAN, "width": 1200, "height": 850, "isPdf": False,
             "geschoss": "OG2", "uploadedAt": "2026-09-21",
             "uploadedBy": "Gerhard Steinbichler",
             "takenAt": "2026-09-21T08:00:00.000Z"},
        ],
        "tickets": [],
        "layers": [],
    }


def _foto_saat(pid):
    return [
        {"id": "FO%d" % i, "project_id": pid, "data_url": PNG_FOTO,
         "taken_at": "2026-09-2%dT09:1%d:00.000Z" % (i % 10, i),
         "entity_type": "schnellfoto",
         "caption": "Baufortschritt Aufnahme %d" % i,
         "uploaded_by": "Gerhard Steinbichler"}
        for i in range(1, 7)
    ]


def _messen(seite):
    s = seite.evaluate(SCHIRM_JS)
    f = seite.evaluate(SUCHE_JS, ZIELE)
    return {"schirm": s["anteil"], "punkte": s["punkte"],
            "traeger": s["traeger"], "funde": f}


def _stelle(erg, name, seite, bild=None):
    d = _messen(seite)
    erg[name] = d
    if bild:
        try:
            seite.screenshot(path=bild)
            d["bild"] = os.path.basename(bild)
        except Exception as e:
            d["bild_fehler"] = str(e)[:80]
    treffer = ", ".join(
        "%s x%d (groesste sichtbar %.1f %%)"
        % (k, len(v), 100 * max([x["anteil_sichtbar"] for x in v] or [0]))
        for k, v in d["funde"].items() if v)
    print("      %-26s Schirm %5.1f %% dunkel | %s"
          % (name, 100 * (d["schirm"] or 0), treffer or "keine Zielfarbe im Baum"))
    return d


def _lauf(browser, url, breite, thema, erg, protokoll):
    ctx = browser.new_context(
        viewport={"width": breite, "height": 880},
        is_mobile=breite < 600, has_touch=breite < 600,
        device_scale_factor=1, color_scheme="dark")
    ctx.add_init_script(INIT)
    ctx.add_init_script(_nutzer("admin", thema))
    ctx.route("**/rest/v1/**", lambda r: r.abort())
    ctx.route("**/auth/v1/**", lambda r: r.abort())
    seite = ctx.new_page()
    schl = "%s/%d" % (thema, breite)
    print("\n== %s" % schl)
    seite.goto(url, wait_until="domcontentloaded")
    seite.wait_for_timeout(4000)
    grund = _saat(seite)
    # Die Speicher werden beim ersten Oeffnen der Datenbank angelegt. Laeuft
    # die App gerade noch hoch, sind sie noch nicht da - im zweiten Anlauf
    # meldete die Saat fuer BEIDE Dunkel-Laeufe
    # fehlt: ['planData','projektCache'], und die Messung haette ohne diese
    # Wiederholung zwei leere Renderpfade als Ergebnis ausgegeben.
    zusatz = None
    for versuch in range(3):
        zusatz = seite.evaluate(SAAT_JS, {"db": DB_NAME, "pid": "P1",
                                          "planData": _plan_saat("P1"),
                                          "fotos": _foto_saat("P1")})
        if not zusatz.get("fehlt"):
            break
        seite.wait_for_timeout(2500)
    protokoll.append("%s: Grundsaat %s | Plan/Foto-Saat zurueckgelesen: %s"
                     % (schl, grund, zusatz))
    print("   Saat zurueckgelesen: %s" % zusatz)

    aus = {}
    erg[schl] = aus
    if zusatz.get("fehlt") or zusatz.get("plaene", 0) < 1:
        aus["_grund"] = ("Saat kam nicht an (%s) - ohne Plan und Foto gibt es "
                         "die gesuchten Flaechen nicht. NICHT GEMESSEN."
                         % zusatz)
        ctx.close()
        return
    seite.reload(wait_until="domcontentloaded")
    seite.wait_for_timeout(5000)

    # ── Projekt oeffnen ───────────────────────────────────────────────────
    if breite < 600:
        seite.evaluate(M.NAV_OEFFNEN_JS)
        seite.wait_for_timeout(400)
    if seite.evaluate(WAEHLEN_JS, "Projekte") == "kein-sichtbarer-knopf":
        aus["_grund"] = "Reiter Projekte nicht sichtbar"
        ctx.close()
        return
    seite.wait_for_timeout(2600)
    if seite.evaluate(PROJEKT_OEFFNEN_JS) != "geklickt":
        aus["_grund"] = "keine Projektkarte"
        ctx.close()
        return
    seite.wait_for_timeout(3000)

    bild = lambda n: os.path.join(WURZEL, "screenshots",
                                  "schwestern_%s_%d_%s.png" % (thema, breite, n))

    # ── Ansicht Plaene ────────────────────────────────────────────────────
    r = seite.evaluate(SHELL_WAEHLEN_JS, "Pläne")
    if r == "menue-geoeffnet":
        seite.wait_for_timeout(500)
        r = seite.evaluate(SHELL_WAEHLEN_JS, "Pläne")
    seite.wait_for_timeout(2800)
    # KOEDER DER SAAT: steht der gesaete Plan in der Ansicht? Wenn nicht, ist
    # jede Zahl von hier die Zahl eines leeren Renderpfads.
    da = seite.evaluate(SICHTBAR_TEXT_JS, "Grundriss Erdgeschoss")
    aus["_plan_sichtbar"] = bool(da)
    print("   Plan-Saat in der Ansicht sichtbar: %s" % da)
    if not da:
        aus["_grund_plaene"] = ("gesaeter Plan erscheint in der Ansicht NICHT "
                                "- leerer Renderpfad, nicht gemessen")
    else:
        seite.evaluate(ROLLEN_JS)
        seite.wait_for_timeout(900)
        _stelle(aus, "Plaene/Viewer (Zeile 17154)", seite, bild("viewer"))
        # Planverwaltung: die Kachelwand mit den Vorschaubildern (18439).
        # Ueber das ZEICHEN, nicht ueber das Wort - am Telefon heisst der
        # Reiter nur "📁 2".
        k = seite.evaluate(UNTERREITER_JS, "📁")
        aus["_klick_verwaltung"] = k
        seite.wait_for_timeout(2200)
        da2 = seite.evaluate(VERWALTUNG_DA_JS)
        aus["_verwaltung_da"] = bool(da2)
        if not da2:
            aus["_grund_verwaltung"] = (
                "Kachelwand der Planverwaltung nicht erreicht (Klick: %s) - "
                "NICHT GEMESSEN" % k)
            print("      Planverwaltung NICHT erreicht (%s)" % k)
        else:
            seite.evaluate(ROLLEN_JS)
            seite.wait_for_timeout(900)
            _stelle(aus, "Plaene/Planverwaltung (Zeile 18439)", seite,
                    bild("verwaltung"))

    # ── Ansicht Fotos ─────────────────────────────────────────────────────
    r = seite.evaluate(SHELL_WAEHLEN_JS, "Fotos")
    if r == "menue-geoeffnet":
        seite.wait_for_timeout(500)
        r = seite.evaluate(SHELL_WAEHLEN_JS, "Fotos")
    seite.wait_for_timeout(3000)
    kf = seite.evaluate(FOTO_KOEDER_JS)
    aus["_foto_koeder"] = kf
    da = (not kf["leerText"]) and kf["bilder"] >= 6
    aus["_fotos_sichtbar"] = bool(da)
    print("   Foto-Saat sichtbar: %s  (Leertext %s, %d Bilder, %d davon Daten)"
          % (da, kf["leerText"], kf["bilder"], kf["datenBilder"]))
    if not da:
        aus["_grund_fotos"] = (
            "gesaete Fotos erscheinen in der Ansicht NICHT (Leertext=%s, "
            "%d Bilder) - leerer Renderpfad, nicht gemessen"
            % (kf["leerText"], kf["bilder"]))
    else:
        seite.evaluate(ROLLEN_JS)
        seite.wait_for_timeout(900)
        _stelle(aus, "Fotos/Kachelwand (Zeile 19191)", seite, bild("fotos_grid"))
        aus["_klick_liste"] = seite.evaluate(LISTE_JS)
        seite.wait_for_timeout(1600)
        seite.evaluate(ROLLEN_JS)
        seite.wait_for_timeout(900)
        _stelle(aus, "Fotos/Liste (Zeile 19207)", seite, bild("fotos_liste"))

    ctx.close()


def _kiosk(browser, url, breite, thema, erg, protokoll):
    """Die Stempeluhr-Tafel hinter ?screen=stempel. Die Vermutung war, das
    seien Tore VOR dem Anmelden. Gemessen wird, ob das stimmt."""
    ctx = browser.new_context(
        viewport={"width": breite, "height": 880},
        is_mobile=breite < 600, has_touch=breite < 600,
        color_scheme="dark")
    ctx.add_init_script(INIT)
    ctx.add_init_script(_nutzer("admin", thema))
    ctx.route("**/rest/v1/**", lambda r: r.abort())
    ctx.route("**/auth/v1/**", lambda r: r.abort())
    seite = ctx.new_page()
    schl = "kiosk/%s/%d" % (thema, breite)
    print("\n== %s" % schl)
    try:
        seite.goto(url + "?screen=stempel", wait_until="domcontentloaded")
        seite.wait_for_timeout(6000)
        aus = {}
        erg[schl] = aus
        aus["_text"] = seite.evaluate(
            "() => (document.body.innerText||'').replace(/\\s+/g,' ').slice(0,120)")
        _stelle(aus, "Stempeluhr-Kiosk (Zeilen 7640/7693/9481)", seite,
                os.path.join(WURZEL, "screenshots",
                             "schwestern_kiosk_%s_%d.png" % (thema, breite)))
    except Exception as e:
        erg[schl] = {"_grund": "Ausnahme: " + str(e)[:120]}
        protokoll.append("%s: %s" % (schl, str(e)[:120]))
    ctx.close()


def _ohne_anmeldung(browser, url, erg):
    """Erscheint das Tor #0f172a OHNE Anmeldung? Das war die Vermutung, und
    sie laesst sich mit einem LEEREN Speicher pruefen: kein INIT, kein Nutzer."""
    ctx = browser.new_context(viewport={"width": 390, "height": 880},
                              is_mobile=True, has_touch=True,
                              color_scheme="dark")
    ctx.add_init_script("try{localStorage.setItem('epk_theme','light');}catch(e){}")
    ctx.route("**/rest/v1/**", lambda r: r.abort())
    ctx.route("**/auth/v1/**", lambda r: r.abort())
    seite = ctx.new_page()
    print("\n== ohne Anmeldung, 390 px, epk_theme=light")
    seite.goto(url, wait_until="domcontentloaded")
    seite.wait_for_timeout(6000)
    aus = {}
    erg["ohne_anmeldung/light/390"] = aus
    aus["_text"] = seite.evaluate(
        "() => (document.body.innerText||'').replace(/\\s+/g,' ').slice(0,140)")
    _stelle(aus, "Anmeldeschirm", seite,
            os.path.join(WURZEL, "screenshots", "schwestern_anmeldung.png"))
    ctx.close()


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt.")
        return 2
    import hashlib
    datei = os.environ.get("EPK_INDEX", "index.html")
    pfad = os.path.join(WURZEL, datei)

    def md5():
        with open(pfad, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    md5_vor = md5()
    print("Gemessen wird %s  (md5 %s)" % (datei, md5_vor))
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port, datei)
    print("Quelle:", url)
    os.makedirs(os.path.join(WURZEL, "screenshots"), exist_ok=True)

    erg, protokoll = {}, []
    t0 = time.time()
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for thema in THEMEN:
            for breite in BREITEN:
                _lauf(b, url, breite, thema, erg, protokoll)
        for thema in THEMEN:
            for breite in BREITEN:
                _kiosk(b, url, breite, thema, erg, protokoll)
        _ohne_anmeldung(b, url, erg)
        b.close()
    md5_nach = md5()

    ziel = os.path.join(WURZEL, "screenshots", "hellmodus_schwestern.json")
    with io.open(ziel, "w", encoding="utf-8") as f:
        f.write(json.dumps({"md5_vor": md5_vor, "md5_nach": md5_nach,
                            "datei": datei, "protokoll": protokoll,
                            "sekunden": round(time.time() - t0),
                            "stellen": erg},
                           ensure_ascii=False, indent=1))
    print("\n" + "=" * 70)
    print("md5 %s: vor %s, nach %s" % (datei, md5_vor, md5_nach))
    if md5_vor != md5_nach:
        print("ACHTUNG: die Datei hat sich waehrend des Laufs geaendert.")
    print("Rohwerte:", ziel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
