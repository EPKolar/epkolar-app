# -*- coding: utf-8 -*-
"""Ist der Hellmodus in IRGENDEINER Ansicht dunkel?

WOHER DIE FRAGE KOMMT
─────────────────────
Der Nutzer meldet "mobil hell ist auch sehr dunkel". scripts/hellmodus_messen.py
hat das auf der STARTANSICHT gemessen und NICHT nachgestellt: App-Huelle
rgb(240,242,245) mit Helligkeit 0,886, Fussleiste weiss, bei 390 px und bei
1440 px, keine tragende dunkle Flaeche. Damit war genau eine Frage offen: gilt
das auch fuer die ANDEREN Ansichten? Eine Messung auf einer von neunzehn
Ansichten sagt ueber die uebrigen achtzehn nichts.

WAS GEMESSEN WIRD
─────────────────
Jede Ansicht, die die Navigation FUEHRT - nicht eine Liste, die ich mir
ausgedacht habe. Die Reiter werden zur Laufzeit aus dem Baum gelesen
(`.top-tabs` traegt alle Eintraege aus _allTabs, auch die am Telefon
eingeklappten), und zusaetzlich die Unterseiten der Projekt-Huelle, die
_allNav fuehrt. Je Ansicht bei 390 px UND 1440 px, mit epk_theme='light' und
dem BETRIEBSSYSTEM auf dunkel (color_scheme="dark"): die App-Wahl muss die
OS-Einstellung schlagen, und nur so ist der Fall gemessen, um den es geht.

Gemessen wird ZWEIMAL je Ansicht - oben und nach dem Rollen. Die Projekt-
Huelle ist `height:100dvh; overflow:hidden`; das FENSTER rollt dort nicht,
sondern ein Behaelter im Inneren (`.proj-main`). Wer nur oben misst, sieht am
Telefon die halbe Ansicht nie. Genau daran haette diese Messung den Befund
verloren: bei 390 px liegt die schwarze Planflaeche beim Oeffnen KNAPP unter
der Kante und kommt erst beim Rollen auf den Schirm.

ZWEI MASSE, WEIL EINES NICHT REICHT
───────────────────────────────────
(A) Die FLAECHENSUCHE aus hellmodus_messen.py: jedes Element ab 8000 px2, die
    gemischte Farbe, die Flaeche. Sie findet Flaechen, die es GIBT.
(B) Eine RASTER-ABTASTUNG des Schirms: 24 x 40 Punkte, je Punkt
    elementFromPoint, die Farbstapel gemischt, Helligkeit. Sie misst, was man
    SIEHT.
Das ist kein Beiwerk, sondern ein behobener Messfehler: (A) rechnet mit dem
vollen Rechteck eines Elements, auch wenn es unter der Kante liegt. Bei 390 px
meldete (A) fuer die Planflaeche 78 Prozent "Anteil am Schirm", waehrend (B)
7,6 Prozent mass - die Flaeche war gar nicht auf dem Schirm. Beide Zahlen
stehen im Bericht; geurteilt wird nach (B), und eine Flaeche, die (A) findet
und (B) nicht sieht, bekommt eine EIGENE Zeile statt stillschweigend zu
verschwinden.

Die Flaechensuche (A) wird aus hellmodus_messen.py IMPORTIERT und nicht
nachgebaut. Dort stecken drei bereits behobene Messfehler, und ein Nachbau
holt sie sich zurueck:
  1. rgba(0,0,0,0) ist Durchsichtigkeit, nicht Schwarz. <html> hat keinen
     Hintergrund und keinen Vorfahren - es faellt aus der Wertung.
  2. Eine halbdurchsichtige Farbe ist nicht die Farbe, die man sieht.
     rgba(234,179,8,0.067) ueber Weiss ist nahezu weiss. Es wird gegen den
     ersten deckenden Vorfahren GEMISCHT.
  3. Fuenf benannte Flaechen verfehlen den Befund, wenn er woanders liegt.
     Darum wird JEDES sichtbare Element ab 8000 px2 abgetastet und nach
     ANTEIL AM SCHIRM geurteilt (ab 25 % = tragende Flaeche), nicht nach
     Farbe. Nach Farbe zu filtern waere Blindheit auf Bestellung.

DER KOEDER - die wichtigste Regel dieser Datei
──────────────────────────────────────────────
Derselbe Lauf mit epk_theme='dark' MUSS in JEDER Ansicht eine tragende dunkle
Flaeche finden - und zwar in BEIDEN Massen: die Flaechensuche muss etwas ab
25 Prozent melden UND die Raster-Abtastung muss einen dunklen Schirm ab
25 Prozent messen. Versagt eines der beiden, hat das Werkzeug dort nichts
gemessen, und die Aussage ueber den Hellmodus dieser Ansicht ist wertlos. Das
Urteil lautet dann "NICHT GEMESSEN", niemals "gruen". Ein Werkzeug, das zu
wenig findet, meldet gruen.

Derselbe Grundsatz fuer das Erreichen: eine Ansicht, die nicht geoeffnet
werden konnte - Reiter nicht sichtbar, Rolle fehlt, Zeitgrenze, Ausnahme -
erscheint als "NICHT GEMESSEN" mit Grund und nicht stillschweigend als
"keine Befunde".

WAS KEIN BEFUND IST
───────────────────
Dieser Aufbau bricht jede REST-Anfrage ab. Dadurch erscheinen Warnbaender in
Amber und Orange ("Mitarbeiterliste konnte nicht aktualisiert werden",
"SERVER"). Sie sind rund 6 Prozent des Schirms, sind Akzentfarben und KEIN
Themenfehler. Sie werden gelistet, aber nicht als Befund gezaehlt - die
Trennlinie ist der Anteil am Schirm, nicht die Farbe.

AUFRUF
──────
    set EPK_INDEX=_mess_stand_939.html
    python scripts/hellmodus_ansichten.py

Ergebnis: docs/befunde/HELLMODUS_ANSICHTEN.md und
          screenshots/hellmodus_ansichten.json
Rueckgabe: 0 = in jeder GEMESSENEN Ansicht keine tragende dunkle Flaeche im
           Hellmodus; 1 = Befund ODER eine Ansicht ohne Koeder/unerreichbar.
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
from hellmodus_messen import FLAECHEN_JS  # noqa: E402  - NICHT nachbauen
from tab_sweep import INIT, DB_NAME, SEED_JS  # noqa: E402

BREITEN = (390, 1440)
THEMEN = ("light", "dark")
TRAGEND_AB = 0.25          # Anteil am Schirm, ab dem eine Flaeche traegt
HELL_GRENZE = 0.5          # relative Helligkeit, unter der es dunkel ist

# ── Die Navigation AUFZAEHLEN, nicht raten ────────────────────────────────
# _allTabs steht im Quelltext (v3.9.939 ab Zeile 9374), aber gemessen wird
# der BAUM: `.top-tabs` traegt alle Reiter, die der angemeldete Nutzer
# tatsaechlich bekommt, samt der am Telefon eingeklappten. Wer die Liste
# abschreibt, misst eine Ansicht, die es fuer diese Rolle nicht gibt, und
# verfehlt eine, die dazukam.
TABS_JS = r"""() => {
  const aus = [];
  const gesehen = {};
  const sammeln = (wurzel) => {
    if (!wurzel) return;
    wurzel.querySelectorAll('button[aria-label]').forEach(b => {
      const l = b.getAttribute('aria-label');
      if (!l || gesehen[l]) return;
      gesehen[l] = 1; aus.push(l);
    });
  };
  sammeln(document.querySelector('.top-tabs'));
  // Am Telefon ist die obere Reiterzeile per CSS ausgeblendet, steht aber im
  // Baum. Die Fussleiste fuehrt eigene Kurznamen (Home/Baustelle/Zeit/
  // Fuhrpark/Mehr) - die sind KEINE Ansichten und werden ausgelassen.
  return {reiter: aus,
          fussleiste: [...(document.querySelector('.bottom-nav')
                        || {querySelectorAll: () => []}).querySelectorAll('button')]
                      .map(b => b.getAttribute('aria-label') || ''),
          topTabsDa: !!document.querySelector('.top-tabs')};
}"""

# Am Telefon liegen die Reiter im Mehr-Menue der Fussleiste, am Rechner in der
# oberen Zeile. In beiden Faellen gibt es mehrere Knoepfe mit demselben
# aria-label. Geklickt wird der LETZTE SICHTBARE AUSSERHALB DER FUSSLEISTE -
# und dieser Zusatz ist ein behobener Messfehler, nicht Kosmetik:
#
# Die Fussleiste fuehrt GRUPPEN-Knoepfe, deren aria-label mit einem Reiternamen
# zusammenfaellt ("Home" heisst beides). Der erste Lauf klickte den letzten
# sichtbaren Knopf ueberhaupt, und das war der Gruppenknopf der Fussleiste - er
# oeffnete GRUPPE 0 und damit 'Chef'. Ergebnis: "Home" fiel mit "Klick ging auf
# 'Home', offen ist 'Chef'" aus der Messung, und 'Chef' fand danach keinen
# eigenen Knopf mehr. Zwei von achtzehn Ansichten waren bei 390 px nicht
# gemessen; nur die Gegenprobe ueber aria-current hat verhindert, dass
# stattdessen zweimal dieselbe Ansicht als zwei gemessene gezaehlt wurde.
# Ein Knopf in einem per CSS ausgeblendeten Behaelter nimmt den Klick ebenso an
# und tut nichts - beides waere eine Ansicht, die als gemessen gilt und nie kam.
WAEHLEN_JS = r"""(label) => {
  const sichtbar = (b) => {
    const cs = getComputedStyle(b);
    if (cs.visibility === 'hidden' || cs.display === 'none') return false;
    const r = b.getBoundingClientRect();
    return r.width > 1 && r.height > 1;
  };
  const k = [...document.querySelectorAll('button[aria-label]')]
    .filter(b => b.getAttribute('aria-label') === label && sichtbar(b)
                 && !b.closest('.bottom-nav'));
  if (!k.length) return 'kein-sichtbarer-knopf';
  k[k.length - 1].click();
  return 'geklickt/' + k.length;
}"""

# ── Mass (B): was bedeckt den SCHIRM? ─────────────────────────────────────
# Die Flaechensuche rechnet mit dem vollen Rechteck eines Elements. Ein
# Element, das knapp unter der Kante beginnt, hat dieselbe Flaeche wie eines
# mitten im Bild - und wird als "78 Prozent des Schirms" gemeldet, obwohl es
# nicht auf dem Schirm ist. Genau das ist bei 390 px in der Ansicht Plaene
# passiert. Diese Abtastung fragt stattdessen fuer 24 x 40 Punkte, WAS an
# dieser Stelle oben liegt, und mischt den Farbstapel von aussen nach innen -
# also dieselbe Rechnung wie in `gemischt`, nur am Punkt statt am Element.
SCHIRM_JS = r"""() => {
  const kanaele = (c) => {
    const m = /rgba?\((\d+), ?(\d+), ?(\d+)(?:, ?([\d.]+))?/.exec(c || '');
    if (!m) return null;
    return {r:+m[1], g:+m[2], b:+m[3], a: m[4] === undefined ? 1 : parseFloat(m[4])};
  };
  const hell = (k) => {
    const f = [k.r, k.g, k.b].map(v => {
      v = v / 255;
      return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4);
    });
    return 0.2126*f[0] + 0.7152*f[1] + 0.0722*f[2];
  };
  // Alle Hintergruende vom Punkt bis zur Wurzel sammeln, dann von HINTEN
  // nach vorne uebereinanderlegen. Ein Element mit Alpha 0 traegt nichts bei;
  // der Standard-Untergrund des Browsers ist Weiss.
  const farbeAn = (el) => {
    let e = el; const oben = [];
    while (e) {
      const k = kanaele(getComputedStyle(e).backgroundColor);
      if (k && k.a > 0.004) { oben.push({k:k, el:e}); if (k.a >= 0.999) break; }
      e = e.parentElement;
    }
    if (!oben.length) return null;
    let u = {r:255, g:255, b:255};
    for (let i = oben.length - 1; i >= 0; i--) {
      const k = oben[i].k;
      u = {r: Math.round(k.a*k.r + (1-k.a)*u.r),
           g: Math.round(k.a*k.g + (1-k.a)*u.g),
           b: Math.round(k.a*k.b + (1-k.a)*u.b)};
    }
    return {k:u, traeger: oben[0].el};
  };
  const NX = 24, NY = 40;
  let dunkel = 0, gesamt = 0;
  const zaehler = {};
  for (let ix = 0; ix < NX; ix++) {
    for (let iy = 0; iy < NY; iy++) {
      const el = document.elementFromPoint((ix + 0.5) * innerWidth / NX,
                                           (iy + 0.5) * innerHeight / NY);
      if (!el) continue;
      gesamt++;
      const f = farbeAn(el);
      if (!f) continue;
      if (hell(f.k) >= 0.5) continue;
      dunkel++;
      const t = f.traeger;
      const s = t.tagName.toLowerCase() + '.'
              + String(t.className || '').slice(0, 34)
              + '  rgb(' + f.k.r + ',' + f.k.g + ',' + f.k.b + ')';
      zaehler[s] = (zaehler[s] || 0) + 1;
    }
  }
  return {punkte: gesamt, dunkel: dunkel,
          anteil: gesamt ? dunkel / gesamt : null,
          traeger: Object.keys(zaehler).map(s => [s, zaehler[s]])
                     .sort((a, b) => b[1] - a[1]).slice(0, 8)};
}"""

# Jeden rollbaren Behaelter ans Ende rollen. `window.scrollTo` genuegt NICHT:
# die Projekt-Huelle ist 100dvh mit overflow:hidden, gerollt wird `.proj-main`
# im Inneren. Ohne diesen Schritt bleibt die schwarze Planflaeche bei 390 px
# unter der Kante und der Befund faellt aus der Messung.
ROLLEN_JS = r"""() => {
  const aus = [];
  document.querySelectorAll('*').forEach(e => {
    if (e.scrollHeight - e.clientHeight > 40 && e.clientHeight > 80) {
      e.scrollTop = e.scrollHeight;
      aus.push({tag: e.tagName.toLowerCase(),
                klasse: String(e.className || '').slice(0, 36),
                sh: e.scrollHeight, ch: e.clientHeight, nach: e.scrollTop});
    }
  });
  try { window.scrollTo(0, document.scrollingElement.scrollHeight); } catch (x) {}
  return aus;
}"""

ROLLEN_ZURUECK_JS = r"""() => {
  document.querySelectorAll('*').forEach(e => {
    if (e.scrollTop) e.scrollTop = 0;
  });
  try { window.scrollTo(0, 0); } catch (x) {}
  return true;
}"""

# Welche Ansicht ist gerade offen? Der Reiter mit aria-current="page" ist die
# Selbstaussage der App. Ohne diese Gegenprobe wuerde ein fehlgeschlagener
# Klick die VORIGE Ansicht ein zweites Mal messen und als neue ausgeben.
OFFEN_JS = r"""() => {
  const a = document.querySelector('button[aria-current="page"]');
  return {aktiv: a ? a.getAttribute('aria-label') : null,
          projShell: !!document.querySelector('.proj-shell'),
          zeichen: String(document.body.innerText || '')
                   .replace(/\s+/g, ' ').slice(0, 90)};
}"""

# ── Projekt-Huelle (_allNav) ──────────────────────────────────────────────
# Die dreizehn Unterseiten aus _allNav (v3.9.937, Zeile 15751 der gemessenen
# Fassung) sind nur INNERHALB eines Projekts erreichbar. Ihre Knoepfe tragen
# `title`, nicht aria-label - wer nur nach aria-label sucht, findet sie nicht
# und haelt sie fuer nicht vorhanden.
#
# Die Projektkarte ist ein nackter <div> ohne Klasse, ohne role und ohne
# onclick-Attribut: React haengt den Horcher an, das Markup verraet ihn nicht.
# Der erste Lauf suchte nach `[role=button], .epk-card-hover, div[onclick]`,
# fand nichts und meldete "keine Projektkarte im Baum" - dreizehn Unterseiten
# standen als nicht erreichbar da, obwohl sie da waren. Geklickt wird deshalb
# das BLATT, das den Projektnamen traegt; der Klick steigt zur Karte auf.
PROJEKT_OEFFNEN_JS = r"""() => {
  const blatt = [...document.querySelectorAll('div, span, b, strong')]
    .filter(e => e.children.length === 0
                 && /Steiner Landstra|Landesklinikum Zwettl/.test(e.textContent || ''));
  if (!blatt.length) return 'keine-projektkarte';
  blatt[0].click();
  return 'geklickt';
}"""

# NUR die Seitenleiste der Projekt-Huelle. `.proj-shell button[title]` liefert
# auch die Hauptreiter der App mit (Home, Chef, Projekte, ...) - die stehen
# innerhalb der Huelle und sind KEINE Unterseiten. Der erste Lauf nahm sie mit,
# klickte bei 'Zeiterfassung' den HAUPTREITER, verliess damit das Projekt, und
# ab da fand jede weitere Unterseite keinen Knopf mehr: acht von dreizehn
# Unterseiten fielen an einem einzigen Namenszusammenfall aus.
SHELL_NAV_JS = r"""() => {
  const sb = document.querySelector('.proj-shell .sidebar');
  if (!sb) return {da: !!document.querySelector('.proj-shell'), eintraege: []};
  const t = [...sb.querySelectorAll('button[title]')]
    .map(b => b.getAttribute('title'))
    .filter(x => x && x !== 'Menue');
  const ein = [];
  t.forEach(x => { if (ein.indexOf(x) < 0) ein.push(x); });
  return {da: true, eintraege: ein};
}"""

SHELL_WAEHLEN_JS = r"""(titel) => {
  const sichtbar = (b) => {
    const cs = getComputedStyle(b);
    if (cs.visibility === 'hidden' || cs.display === 'none') return false;
    const r = b.getBoundingClientRect();
    return r.width > 1 && r.height > 1;
  };
  let k = [...document.querySelectorAll('.proj-shell .sidebar button[title]')]
    .filter(b => b.getAttribute('title') === titel && sichtbar(b));
  if (!k.length) {
    // Am Telefon liegt die Seitenleiste hinter dem Hamburger.
    const h = [...document.querySelectorAll('button[aria-label]')]
      .find(b => b.getAttribute('aria-label') === 'Menue oeffnen');
    if (h) { h.click(); return 'menue-geoeffnet'; }
    return 'kein-sichtbarer-knopf';
  }
  k[0].click();
  return 'geklickt/' + k.length;
}"""


def _nutzer(rolle, thema):
    """localStorage-Vorbelegung. Ohne monteurId bleibt selWorker leer und die
    Zeiterfassung zeigt einen LEEREN Renderpfad - jede Farbe daraus waere
    die Farbe von nichts."""
    return (
        "try{localStorage.setItem('epk_theme',%s);"
        "var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
        "u.role=%s;u.monteurId='M1';u.name='Gerhard Steinbichler';"
        "u.rolle=%s;"
        "localStorage.setItem('epkolar_user',JSON.stringify(u));}catch(e){}"
        % (json.dumps(thema), json.dumps(rolle),
           json.dumps("Monteur" if rolle == "monteur" else "Geschaeftsfuehrer")))


def _saat(seite):
    """Dieselbe Saat wie mob_ansicht_messen, aber OHNE Abbruch: hier ist die
    Saat Beiwerk, nicht Gegenstand. Gemeldet wird, was zurueckgelesen wurde,
    damit eine leere Ansicht nicht als 'nichts gefunden' durchgeht."""
    scheine, eintraege = M._daten()
    cfg = {"db": DB_NAME, "daten": {
        "monteure": M.MONTEURE, "arbeitsscheine": scheine,
        "projects": M.PROJEKTE, "entries": eintraege}}
    try:
        erg = seite.evaluate(SEED_JS, cfg)
    except Exception as e:
        return {"fehler": str(e)[:120]}
    return erg.get("gelesen", {})


def _kurz(e):
    """Eine Zeile fuer den Lauf-Mitschrieb: BEIDE Masse, nicht eines."""
    if "tragend" not in e:
        return "NICHT GEMESSEN"
    return "Schirm %5.1f %% dunkel | %d tragend" % (
        100 * (e["schirm"] or 0), len(e["tragend"]))


def _einmal(seite):
    """Eine Aufnahme: Flaechensuche (A) und Raster-Abtastung (B) am selben
    Zustand."""
    d = seite.evaluate(FLAECHEN_JS)
    gross = d.get("dunkelGross", [])
    s = seite.evaluate(SCHIRM_JS)
    return {
        "tragend": [g for g in gross if g["anteil"] >= TRAGEND_AB],
        "dunkelGross": gross,
        "dunkelGrossAnzahl": d.get("dunkelGrossAnzahl", 0),
        "schirm": s["anteil"],
        "schirm_punkte": s["punkte"],
        "schirm_traeger": s["traeger"],
        "colorScheme": d.get("colorScheme"),
        "htmlKlasse": d.get("htmlKlasse"),
        "textfarbe": d.get("textfarbe"),
        "elemente": d.get("elemente"),
    }


def _messen(seite):
    """Zwei Aufnahmen: oben und nach dem Rollen. Die Projekt-Huelle rollt
    NICHT am Fenster - `height:100dvh; overflow:hidden`, gerollt wird ein
    Behaelter im Inneren. Eine Messung nur am oberen Rand sieht am Telefon die
    halbe Ansicht nie."""
    oben = _einmal(seite)
    behaelter = seite.evaluate(ROLLEN_JS)
    seite.wait_for_timeout(900)
    gerollt = _einmal(seite)
    seite.evaluate(ROLLEN_ZURUECK_JS)
    seite.wait_for_timeout(300)
    # Fuer die Auswertung wird der SCHLECHTERE der beiden Zustaende gefuehrt:
    # eine Flaeche, die erst beim Rollen erscheint, ist keine Flaeche weniger.
    schirm = max(x for x in (oben["schirm"], gerollt["schirm"])
                 if x is not None) if (oben["schirm"] is not None
                                       or gerollt["schirm"] is not None) else None
    tragend = list(oben["tragend"])
    schon = {(g["tag"], g["klasse"], g["farbe"], g["flaeche"]) for g in tragend}
    for g in gerollt["tragend"]:
        if (g["tag"], g["klasse"], g["farbe"], g["flaeche"]) not in schon:
            tragend.append(g)
    return {
        "tragend": tragend,
        "schirm": schirm,
        "oben": oben,
        "gerollt": gerollt,
        "rollbehaelter": behaelter,
        "dunkelGrossAnzahl": max(oben["dunkelGrossAnzahl"],
                                 gerollt["dunkelGrossAnzahl"]),
        "dunkelGross": (oben["dunkelGross"]
                        if oben["dunkelGrossAnzahl"] >= gerollt["dunkelGrossAnzahl"]
                        else gerollt["dunkelGross"]),
        "colorScheme": oben["colorScheme"],
        "htmlKlasse": oben["htmlKlasse"],
        "textfarbe": oben["textfarbe"],
        "elemente": oben["elemente"],
    }


def _lauf(browser, url, thema, breite, rolle, ergebnis, protokoll):
    """Ein Kontext: eine Rolle, ein Thema, eine Breite. Alle Ansichten
    hintereinander in derselben Seite - ein frischer Kontext je Ansicht waere
    neunzehnmal Ladezeit und misst dieselbe Sache."""
    schluessel = (rolle, thema, breite)
    ctx = browser.new_context(
        viewport={"width": breite, "height": 880},
        is_mobile=breite < 600, has_touch=breite < 600,
        device_scale_factor=1,
        # Das Betriebssystem bewusst auf DUNKEL. Die App-Wahl muss gewinnen
        # (v3.9.711). Ohne das ist der gemeldete Fall nicht gemessen.
        color_scheme="dark")
    ctx.add_init_script(INIT)
    ctx.add_init_script(_nutzer(rolle, thema))
    ctx.route("**/rest/v1/**", lambda r: r.abort())
    ctx.route("**/auth/v1/**", lambda r: r.abort())
    seite = ctx.new_page()
    seiten_fehler = []
    seite.on("pageerror", lambda e: seiten_fehler.append(str(e)[:120]))

    try:
        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(4000)
        saat = _saat(seite)
        seite.reload(wait_until="domcontentloaded")
        seite.wait_for_timeout(5000)
    except Exception as e:
        protokoll.append("%s: Laden fehlgeschlagen: %s"
                         % (schluessel, str(e)[:120]))
        ergebnis[schluessel] = {"_laden": "FEHLER: " + str(e)[:120]}
        ctx.close()
        return

    tabs = seite.evaluate(TABS_JS)
    protokoll.append("%s: Saat %s | Reiter aus dem Baum: %s"
                     % (schluessel, saat, tabs["reiter"]))
    aus = {"_saat": saat, "_reiter": tabs["reiter"],
           "_fussleiste": tabs["fussleiste"]}

    for label in tabs["reiter"]:
        eintrag = {"art": "reiter"}
        try:
            if breite < 600:
                # Am Telefon stehen die Reiter im Mehr-Menue der Fussleiste.
                seite.evaluate(M.NAV_OEFFNEN_JS)
                seite.wait_for_timeout(400)
            eintrag["klick"] = seite.evaluate(WAEHLEN_JS, label)
            if eintrag["klick"] == "kein-sichtbarer-knopf":
                eintrag["nicht_gemessen"] = "kein sichtbarer Reiter-Knopf"
                aus[label] = eintrag
                continue
            seite.wait_for_timeout(2600)
            seite.evaluate("() => window.scrollTo(0,0)")
            seite.wait_for_timeout(300)
            offen = seite.evaluate(OFFEN_JS)
            eintrag["aktiv"] = offen["aktiv"]
            if offen["aktiv"] and offen["aktiv"] != label:
                # Die App sagt selbst, dass eine ANDERE Ansicht offen ist.
                eintrag["nicht_gemessen"] = (
                    "Klick ging auf %r, offen ist %r" % (label, offen["aktiv"]))
                aus[label] = eintrag
                continue
            eintrag.update(_messen(seite))
            eintrag["zeichen"] = offen["zeichen"]
        except Exception as e:
            eintrag["nicht_gemessen"] = "Ausnahme: " + str(e)[:110]
        aus[label] = eintrag
        print("   %-18s %-28s %s" % (label, _kurz(eintrag),
                                     eintrag.get("nicht_gemessen", "")))

    # ── Die Unterseiten der Projekt-Huelle (_allNav) ──────────────────────
    aus["_shell"] = _shell(seite, breite, aus)
    aus["_seitenfehler"] = seiten_fehler[:6]
    ergebnis[schluessel] = aus
    ctx.close()


def _projekt_auf(seite, breite):
    """Ein Projekt oeffnen. Gibt None zurueck, wenn es geklappt hat, sonst den
    GRUND - der gehoert in den Bericht und nicht in ein leeres Ergebnis."""
    if breite < 600:
        seite.evaluate(M.NAV_OEFFNEN_JS)
        seite.wait_for_timeout(400)
    k = seite.evaluate(WAEHLEN_JS, "Projekte")
    if k == "kein-sichtbarer-knopf":
        return "Reiter 'Projekte' nicht sichtbar (Rolle?)"
    seite.wait_for_timeout(2600)
    r = seite.evaluate(PROJEKT_OEFFNEN_JS)
    if r != "geklickt":
        return "keine Projektkarte im Baum (%s)" % r
    seite.wait_for_timeout(3000)
    if not seite.evaluate("() => !!document.querySelector('.proj-shell')"):
        return "Projekt-Huelle (.proj-shell) nicht geoeffnet"
    return None


def _shell(seite, breite, aus):
    """Die dreizehn Unterseiten aus _allNav. Sie hangen an einem PROJEKT -
    ohne geoeffnetes Projekt gibt es sie nicht, und das ist ein Grund, nicht
    ein leeres Ergebnis."""
    erg = {}
    try:
        grund = _projekt_auf(seite, breite)
        if grund:
            return {"_grund": grund}
        nav = seite.evaluate(SHELL_NAV_JS)
        if not nav["eintraege"]:
            return {"_grund": "Seitenleiste der Projekt-Huelle fuehrt keine "
                              "Eintraege (da=%s)" % nav["da"]}
        erg["_eintraege"] = nav["eintraege"]
        for titel in nav["eintraege"]:
            e = {"art": "projekt-unterseite"}
            try:
                # Eine Unterseite kann die Huelle verlassen (Hauptreiter mit
                # gleichem Namen, Ruecksprung). Dann wird das Projekt WIEDER
                # geoeffnet, statt die restlichen Unterseiten als
                # "kein Knopf" durchfallen zu lassen - genau so hat der erste
                # Lauf acht Unterseiten verloren.
                if not seite.evaluate(
                        "() => !!document.querySelector('.proj-shell')"):
                    g2 = _projekt_auf(seite, breite)
                    e["wieder_geoeffnet"] = g2 or "ja"
                    if g2:
                        e["nicht_gemessen"] = "Projekt nicht wieder auf: " + g2
                        erg[titel] = e
                        continue
                r2 = seite.evaluate(SHELL_WAEHLEN_JS, titel)
                if r2 == "menue-geoeffnet":
                    seite.wait_for_timeout(500)
                    r2 = seite.evaluate(SHELL_WAEHLEN_JS, titel)
                e["klick"] = r2
                if r2 == "kein-sichtbarer-knopf":
                    e["nicht_gemessen"] = "kein sichtbarer Knopf"
                    erg[titel] = e
                    continue
                seite.wait_for_timeout(2400)
                seite.evaluate("() => window.scrollTo(0,0)")
                seite.wait_for_timeout(300)
                if not seite.evaluate(
                        "() => !!document.querySelector('.proj-shell')"):
                    e["nicht_gemessen"] = "Projekt-Huelle verlassen"
                    erg[titel] = e
                    continue
                e.update(_messen(seite))
            except Exception as ex:
                e["nicht_gemessen"] = "Ausnahme: " + str(ex)[:110]
            erg[titel] = e
            print("   P/%-16s %-28s %s" % (titel, _kurz(e),
                                            e.get("nicht_gemessen", "")))
    except Exception as ex:
        erg["_grund"] = "Ausnahme beim Oeffnen: " + str(ex)[:110]
    return erg


def _ansichten(aus):
    """Die Namen der Ansichten in einem Lauf, Reiter und Unterseiten."""
    namen = [k for k in aus if not k.startswith("_")]
    for k in aus.get("_shell", {}):
        if not k.startswith("_"):
            namen.append("Projekt/" + k)
    return namen


def _holen(ergebnis, rolle, thema, breite, name):
    aus = ergebnis.get((rolle, thema, breite))
    if aus is None:
        return None
    if name.startswith("Projekt/"):
        return aus.get("_shell", {}).get(name[len("Projekt/"):])
    return aus.get(name)


def _zelle(e):
    """Die Zelle einer Breite: BEIDE Masse, in Zahlen. Der Schirmanteil steht
    vorn, weil er die Frage beantwortet ("sieht es dunkel aus"); die
    Flaechensuche steht daneben, weil sie auch findet, was gerade unter der
    Kante liegt."""
    if e is None:
        return "NICHT GEMESSEN (Ansicht in diesem Lauf nicht aufgetaucht)"
    if "tragend" not in e:
        return "NICHT GEMESSEN (%s)" % e.get("nicht_gemessen", "ohne Grund")
    schirm = 100 * (e["schirm"] or 0)
    txt = "Schirm %.1f %% dunkel (oben %.1f, gerollt %.1f)" % (
        schirm, 100 * (e["oben"]["schirm"] or 0),
        100 * (e["gerollt"]["schirm"] or 0))
    if schirm >= 100 * TRAGEND_AB:
        txt = "**" + txt + "**"
    txt += "; %d tragend im Baum, %d dunkel ab 8000 px2" % (
        len(e["tragend"]), e["dunkelGrossAnzahl"])
    return txt


def _fest_verdrahtet(pfad):
    """Gegenprobe im QUELLTEXT: welche Hintergruende sind als feste Farbe
    geschrieben statt aus THEMES zu kommen? Eine solche Flaeche kann der
    Hellmodus gar nicht erreichen - sie ist in beiden Themen gleich dunkel.

    Das ist eine LEITLISTE, kein Urteil: Druck- und Exportvorlagen stehen als
    HTML-Zeichenketten in derselben Datei und tauchen hier mit auf, obwohl sie
    nie eine Bildschirmflaeche der App sind. Welche Zeile wirklich am Schirm
    haengt, sagt die Messung oben, nicht diese Liste.
    """
    import re
    try:
        s = io.open(pfad, encoding="utf-8", errors="replace").read()
    except Exception as e:
        return [{"fehler": str(e)[:120]}]
    aus = []
    muster = re.compile(
        r"""background(?:Color)?\s*:\s*["']#([0-9a-fA-F]{6})["']""")
    for m in muster.finditer(s):
        r, g, b = (int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4))
        f = []
        for v in (r, g, b):
            v = v / 255.0
            f.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
        h = 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2]
        if h >= HELL_GRENZE:
            continue
        aus.append({
            "zeile": s.count(chr(10), 0, m.start()) + 1,
            "farbe": "#" + m.group(1).lower(),
            "helligkeit": round(h, 3),
            "umfeld": s[max(0, m.start() - 90):m.start() + 50]
                      .replace(chr(10), " ").replace("|", "/")})
    return aus


def _bericht(ergebnis, protokoll, md5_vor, md5_nach, url, dauer):
    zeilen = []
    p = zeilen.append
    p("# Hellmodus in ALLEN Ansichten - Messung 26.09.2026")
    p("")
    p("Gemessen mit `scripts/hellmodus_ansichten.py` gegen die EINGEFRORENE")
    p("Kopie `_mess_stand_939.html` (md5 vor dem Lauf `%s`, danach `%s`)."
      % (md5_vor, md5_nach))
    p("`index.html` wurde nicht angefasst. Quelle: `%s`. Laufzeit %.0f s."
      % (url, dauer))
    p("")
    p("Aufbau je Ansicht: `epk_theme='light'`, Betriebssystem auf DUNKEL")
    p("(`color_scheme=\"dark\"`), 390 px und 1440 px, Rolle `admin` mit")
    p("`monteurId='M1'`, alle `/rest/v1/`- und `/auth/v1/`-Anfragen abgebrochen.")
    p("Eine Farbe gilt als dunkel bei relativer Helligkeit unter %.1f, eine"
      % HELL_GRENZE)
    p("Flaeche als TRAGEND ab %d %% des Schirms. Halbdurchsichtige Farben"
      % int(TRAGEND_AB * 100))
    p("werden gegen den Untergrund gemischt, `rgba(0,0,0,0)` faellt aus der")
    p("Wertung - beides sind behobene Messfehler der Vorgaengerfassung.")
    p("")
    p("**Zwei Masse, je Ansicht zweimal aufgenommen (oben und nach dem")
    p("Rollen):**")
    p("")
    p("- **(A) Flaechensuche** (aus `scripts/hellmodus_messen.py` importiert):")
    p("  jedes Element ab 8000 px2, gemischte Farbe, Flaeche. Sie findet")
    p("  Flaechen, die es GIBT - auch solche, die gerade unter der Kante")
    p("  liegen, denn sie rechnet mit dem vollen Rechteck.")
    p("- **(B) Raster-Abtastung** des Schirms, 24 x 40 Punkte: je Punkt")
    p("  `elementFromPoint`, Farbstapel gemischt, Helligkeit. Sie misst, was")
    p("  man SIEHT.")
    p("")
    p("Geurteilt wird nach (B). Der Unterschied ist kein Feinschliff: in der")
    p("Ansicht `Projekt/Plaene` meldete (A) bei 390 px 78 % Anteil fuer die")
    p("schwarze Planflaeche, waehrend (B) 7,6 % mass - die Flaeche lag knapp")
    p("unter der Kante. Erst nach dem Rollen des INNEREN Behaelters")
    p("(`.proj-main`; das Fenster rollt in der Projekt-Huelle nicht, sie ist")
    p("`100dvh` mit `overflow:hidden`) sind es 57,5 %. Eine Ansicht, in der")
    p("(A) etwas findet und (B) nichts sieht, bekommt das Urteil")
    p("\"Flaeche im Baum, nicht auf dem Schirm\" - weder gruen noch Befund.")
    p("")

    # ── Der Koeder zuerst: ohne ihn ist der Rest wertlos ──────────────────
    p("## Der Koeder")
    p("")
    p("Derselbe Lauf mit `epk_theme='dark'` MUSS in jeder Ansicht in BEIDEN")
    p("Massen anschlagen: (A) mindestens eine tragende Flaeche UND (B) ein")
    p("Schirm ab %d %% dunkel. Wo eines der beiden versagt, hat das Werkzeug"
      % int(TRAGEND_AB * 100))
    p("dort nichts gemessen, und die Aussage ueber den Hellmodus dieser")
    p("Ansicht ist wertlos - Urteil dann NICHT GEMESSEN, nicht gruen.")
    p("")
    p("Die Prozentzahl in Klammern ist das Mass (A) der groessten Flaeche. Sie")
    p("kann ueber 100 % liegen: (A) teilt das VOLLE Rechteck eines Elements")
    p("durch die Schirmflaeche, und ein Element kann laenger sein als der")
    p("Schirm. Genau deshalb steht der Schirmanteil (B) davor.")
    p("")
    p("| Ansicht | Koeder 390 px | Koeder 1440 px |")
    p("| --- | --- | --- |")

    namen = []
    for (rolle, thema, breite), aus in sorted(
            ergebnis.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2])):
        for n in _ansichten(aus):
            if n not in namen:
                namen.append(n)

    rollen = sorted({k[0] for k in ergebnis})
    for rolle in rollen:
        for n in namen:
            zellen = []
            for b in BREITEN:
                e = _holen(ergebnis, rolle, "dark", b, n)
                if e is None or "tragend" not in e:
                    zellen.append("nicht erreicht")
                elif e["tragend"] and (e["schirm"] or 0) >= TRAGEND_AB:
                    zellen.append("Schirm %.1f %% dunkel, %d tragend (%.0f %% groesste)"
                                  % (100 * e["schirm"], len(e["tragend"]),
                                     100 * max(x["anteil"] for x in e["tragend"])))
                else:
                    zellen.append("**VERSAGT - Schirm %.1f %%, %d tragend**"
                                  % (100 * (e["schirm"] or 0), len(e["tragend"])))
            if any("nicht erreicht" != z for z in zellen):
                p("| %s%s | %s | %s |"
                  % (n, "" if rolle == "admin" else " (%s)" % rolle,
                     zellen[0], zellen[1]))
    p("")

    # ── Die Haupttabelle ─────────────────────────────────────────────────
    p("## Hellmodus je Ansicht")
    p("")
    p("| Ansicht | 390 px | 1440 px | Urteil |")
    p("| --- | --- | --- | --- |")
    urteile = {}
    nur_baum = []
    for rolle in rollen:
        for n in namen:
            hell = [_holen(ergebnis, rolle, "light", b, n) for b in BREITEN]
            dunkel = [_holen(ergebnis, rolle, "dark", b, n) for b in BREITEN]
            if all(x is None for x in hell) and all(x is None for x in dunkel):
                continue
            gruende = []
            befund = False
            gemessen = 0
            for i, b in enumerate(BREITEN):
                h, d = hell[i], dunkel[i]
                if h is None or "tragend" not in h:
                    gruende.append("%d px: %s" % (
                        b, (h or {}).get("nicht_gemessen",
                                         "Ansicht nicht aufgetaucht")))
                    continue
                if (d is None or "tragend" not in d or not d["tragend"]
                        or (d["schirm"] or 0) < TRAGEND_AB):
                    gruende.append(
                        "%d px: Koeder schlaegt nicht an (dunkel: Schirm "
                        "%.1f %%, %d tragend)"
                        % (b, 100 * ((d or {}).get("schirm") or 0),
                           len((d or {}).get("tragend", []))))
                    continue
                gemessen += 1
                if (h["schirm"] or 0) >= TRAGEND_AB:
                    befund = True
                elif h["tragend"]:
                    # Die Flaechensuche findet eine tragende dunkle Flaeche,
                    # die Abtastung sieht sie nicht: sie liegt unter der Kante
                    # oder ist verdeckt. Das ist KEIN gruen und kein Befund -
                    # es bekommt eine eigene Zeile, damit es niemand wegliest.
                    nur_baum.append((rolle, n, b, h))
            if befund:
                urteil = "BEFUND"
            elif [x for x in nur_baum if x[0] == rolle and x[1] == n]:
                urteil = "Flaeche im Baum, nicht auf dem Schirm"
            elif gemessen == len(BREITEN):
                urteil = "gruen"
            elif gemessen:
                urteil = "teils NICHT GEMESSEN"
            else:
                urteil = "NICHT GEMESSEN"
            urteile[(rolle, n)] = (urteil, gruende)
            p("| %s%s | %s | %s | %s%s |" % (
                n, "" if rolle == "admin" else " (%s)" % rolle,
                _zelle(hell[0]), _zelle(hell[1]), urteil,
                (" - " + "; ".join(gruende)) if gruende else ""))
    p("")

    # ── Weder gruen noch Befund ──────────────────────────────────────────
    p("## Tragende dunkle Flaeche im Baum, aber nicht auf dem Schirm")
    p("")
    if not nur_baum:
        p("Keine. In jeder Ansicht stimmten beide Masse ueberein.")
    else:
        p("Diese Flaechen FINDET die Flaechensuche als tragend, die")
        p("Raster-Abtastung SIEHT sie aber nicht - sie liegen unter der Kante")
        p("oder sind verdeckt. Das ist kein gruen: wer rollt, kann sie sehen.")
        p("")
        p("| Ansicht | Breite | Schirm dunkel | Flaeche | Farbe | Anteil (A) |")
        p("| --- | --- | --- | --- | --- | --- |")
        for rolle, n, b, h in nur_baum:
            for g in h["tragend"]:
                p("| %s%s | %d px | %.1f %% | %d px2 `%s.%s` | %s | %.1f %% |"
                  % (n, "" if rolle == "admin" else " (%s)" % rolle, b,
                     100 * (h["schirm"] or 0), g["flaeche"], g["tag"],
                     g["klasse"] or "-", g["farbe"], 100 * g["anteil"]))
    p("")

    # ── Was die Abtastung als dunkel sieht ───────────────────────────────
    p("## Was die Raster-Abtastung im Hellmodus als dunkel sieht")
    p("")
    p("Die Traeger je Ansicht, nach Punkten. Der orange Streifen")
    p("`rgb(249,115,22)` ist das Sync-Warnband, das es nur gibt, weil dieser")
    p("Aufbau jede Anfrage abbricht - Akzentfarbe, kein Themenfehler.")
    p("")
    for rolle in rollen:
        for b in BREITEN:
            zeilen_da = False
            for n in namen:
                e = _holen(ergebnis, rolle, "light", b, n)
                if e is None or "tragend" not in e:
                    continue
                for wann in ("oben", "gerollt"):
                    t = e[wann]["schirm_traeger"]
                    if not t:
                        continue
                    if not zeilen_da:
                        p("### Rolle %s, %d px, epk_theme=light" % (rolle, b))
                        p("")
                        p("| Ansicht | Zustand | Schirm dunkel | Traeger (Punkte von %d) |"
                          % e[wann]["schirm_punkte"])
                        p("| --- | --- | --- | --- |")
                        zeilen_da = True
                    p("| %s | %s | %.1f %% | %s |"
                      % (n, wann, 100 * (e[wann]["schirm"] or 0),
                         "; ".join("`%s` x%d" % (x[0], x[1]) for x in t)))
            if zeilen_da:
                p("")

    # ── Jede dunkle Flaeche, auch die kleinen ────────────────────────────
    p("## Jede dunkle Flaeche im Hellmodus, ab 8000 px2")
    p("")
    p("Vollstaendig, nicht nur die tragenden. Die Warnbaender in Amber und")
    p("Orange entstehen erst dadurch, dass dieser Aufbau jede Anfrage")
    p("abbricht - sie sind Akzente und kein Themenfehler; der Text steht")
    p("dabei, damit das nachpruefbar ist.")
    p("")
    for rolle in rollen:
        for b in BREITEN:
            p("### Rolle %s, %d px, epk_theme=light" % (rolle, b))
            p("")
            leer = True
            for n in namen:
                e = _holen(ergebnis, rolle, "light", b, n)
                if e is None or "tragend" not in e:
                    continue
                if not e["dunkelGross"]:
                    continue
                leer = False
                p("**%s** - %d dunkle Flaechen ab 8000 px2:" % (n, e["dunkelGrossAnzahl"]))
                p("")
                p("| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |")
                p("| --- | --- | --- | --- | --- | --- |")
                for g in e["dunkelGross"]:
                    p("| `%s.%s` | %s%s | %.3f | %d | %.1f %% | %s |" % (
                        g["tag"], g["klasse"] or "-", g["farbe"],
                        "" if g["roh"] == g["farbe"] else " (roh %s)" % g["roh"],
                        g["helligkeit"], g["flaeche"], 100 * g["anteil"],
                        (g["text"] or "-").replace("|", "/")))
                p("")
            if leer:
                p("Keine Ansicht mit einer dunklen Flaeche ab 8000 px2.")
                p("")

    # ── Gegenprobe im Quelltext ──────────────────────────────────────────
    p("## Fest verdrahtete dunkle Hintergruende im Quelltext")
    p("")
    p("Eine Flaeche, deren Hintergrund als feste Farbe geschrieben ist, kann")
    p("der Hellmodus nicht erreichen - sie ist in beiden Themen gleich dunkel.")
    p("Diese Liste ist eine LEITLISTE und kein Urteil: Druck- und")
    p("Exportvorlagen stehen als HTML-Zeichenketten in derselben Datei und")
    p("tauchen hier mit auf, obwohl sie nie am Schirm haengen. Was wirklich am")
    p("Schirm haengt, sagt die Messung oben.")
    p("")
    fest = _fest_verdrahtet(os.path.join(WURZEL, os.environ.get(
        "EPK_INDEX", "index.html")))
    if fest and fest[0].get("fehler"):
        p("Die Datei konnte nicht gelesen werden: `%s`" % fest[0]["fehler"])
    elif not fest:
        p("Keine gefunden.")
    else:
        geordnet = sorted(fest, key=lambda f: f["helligkeit"])
        p("**%d** fest geschriebene Hintergruende mit Helligkeit unter %.1f."
          % (len(fest), HELL_GRENZE))
        p("Gezeigt sind die %d DUNKELSTEN; die vollstaendige Liste steht in"
          % min(25, len(geordnet)))
        p("`screenshots/hellmodus_ansichten.json` unter `fest_verdrahtet`.")
        p("Gekappt wird nach Helligkeit, nicht nach Farbe - die uebrigen sind")
        p("heller, nicht anders gefaerbt (das Markengruen `#009640` mit 0,222")
        p("ist als Knopfflaeche unter weisser Schrift gewollt).")
        p("")
        p("| Zeile | Farbe | Helligkeit | Umfeld |")
        p("| --- | --- | --- | --- |")
        for f in geordnet[:25]:
            p("| %d | `%s` | %.3f | `%s` |"
              % (f["zeile"], f["farbe"], f["helligkeit"],
                 f["umfeld"].replace("`", "'")))
    p("")

    # ── Gesamturteil ─────────────────────────────────────────────────────
    befunde = [k for k, v in urteile.items() if v[0] == "BEFUND"]
    offen = [k for k, v in urteile.items()
             if v[0] in ("NICHT GEMESSEN", "teils NICHT GEMESSEN")]
    p("## Gesamturteil")
    p("")
    p("- Ansichten, deren Schirm im Hellmodus ab %d %% dunkel ist: **%d**%s"
      % (int(TRAGEND_AB * 100), len(befunde),
         (" - " + ", ".join("%s/%s" % k for k in befunde))
         if befunde else ""))
    p("- Ansichten NICHT GEMESSEN (Koeder versagt oder nicht erreicht): **%d**%s"
      % (len(offen), (" - " + ", ".join("%s/%s" % k for k in offen))
         if offen else ""))
    p("- Ansichten mit tragender Flaeche im Baum, die die Abtastung nicht")
    p("  sieht: **%d**%s"
      % (len([1 for v in urteile.values()
              if v[0] == "Flaeche im Baum, nicht auf dem Schirm"]),
         (" - " + ", ".join(sorted({"%s/%s" % (r, n)
                                    for r, n, _b, _h in nur_baum})))
         if nur_baum else ""))
    p("- Ansichten gruen (Koeder schlug in beiden Massen an, Schirm unter")
    p("  %d %% dunkel): **%d**"
      % (int(TRAGEND_AB * 100),
         len([1 for v in urteile.values() if v[0] == "gruen"])))
    p("")

    p("## WAS DIESER AUFBAU NICHT ABDECKT")
    p("")
    p("- **Ein echtes Geraet.** Hier laeuft Chromium mit gesetzter Breite und")
    p("  `is_mobile`, aber ohne Geraeteprofil: kein iOS-Safari, kein")
    p("  Android-WebView, keine Systemleiste, keine Hoch/Quer-Drehung, kein")
    p("  `prefers-contrast`, keine Bedienungshilfe, die Farben ersetzt.")
    p("- **Ein gespeicherter Dienstarbeiter mit einer aelteren Fassung.** Der")
    p("  Nutzer kann eine Fassung vor v3.9.711 im Zwischenspeicher haben, in")
    p("  der die OS-Einstellung die App-Wahl noch schlug. Dieser Lauf laedt")
    p("  die Datei frisch und sieht das nicht.")
    p("- **Ansichten hinter Rollen, die hier nicht gemessen wurden.** Gemessen")
    p("  wurde %s. Was ein anderer Zuschnitt (Buero, Projektleiter, ein"
      % " und ".join("`%s`" % r for r in rollen))
    p("  eigener `perms_override`) zeigt, steht hier nicht.")
    p("- **Ansichten hinter Daten, die dieser Aufbau nicht hat.** Alle")
    p("  REST-Anfragen sind abgebrochen. Was erst mit echten Zeilen erscheint")
    p("  - eine Tabelle, ein Diagramm, eine Karte - ist hier leer oder ein")
    p("  Warnband. Eine dunkle Flaeche, die nur bei gefuellter Liste")
    p("  entsteht, kann dieser Lauf nicht finden.")
    p("- **Ansichten, die einen Absturz voraussetzen.** Die Auffangflaeche der")
    p("  Fehlergrenze (`#0f0f0f` mit `#1a1a1a`-Karte, `minHeight:100dvh`) ist")
    p("  fest verdrahtet dunkel und erscheint nur, wenn die App wirft. In")
    p("  diesem Lauf ist sie nie erschienen - sie steht in der Quelltextliste")
    p("  oben und ist NICHT gemessen.")
    p("- **Zustaende innerhalb einer Ansicht.** Gemessen sind zwei Zustaende:")
    p("  beim Oeffnen und nach dem Rollen aller rollbaren Behaelter ans Ende.")
    p("  Was DAZWISCHEN liegt, wird nicht abgetastet, ebensowenig")
    p("  Ueberlagerungen, Dialoge, aufgeklappte Karten, quer gerollte Bereiche")
    p("  und alles, was erst nach einer Eingabe erscheint.")
    p("- **Die Liste je Ansicht zeigt die 12 GROESSTEN dunklen Flaechen.** Die")
    p("  Zahl daneben (`... dunkel ab 8000 px2`) ist die vollstaendige Anzahl.")
    p("  Fuer das Urteil ist die Kappung ohne Folge, weil nach Flaeche")
    p("  sortiert wird und eine tragende Flaeche damit immer in den ersten")
    p("  zwoelf steht; fuer die Durchsicht der kleinen Flaechen ist sie eine")
    p("  Grenze.")
    p("- **Die Messung urteilt nach ANTEIL, nicht nach Farbe.** Eine dunkle")
    p("  Flaeche unter %d %% des Schirms erscheint in der vollen Liste, gilt"
      % int(TRAGEND_AB * 100))
    p("  aber nicht als Befund. Wer die Grenze anders zieht, bekommt ein")
    p("  anderes Urteil - die Rohwerte dafuer stehen in der JSON.")
    p("- **Die Abtastung hat %d Punkte.** Eine dunkle Flaeche, die schmaler"
      % (24 * 40))
    p("  ist als ein Rasterabstand (%d px bei 390, %d px bei 1440 Breite),"
      % (390 // 24, 1440 // 24))
    p("  kann zwischen den Punkten hindurchfallen. Die Flaechensuche (A)")
    p("  faengt diesen Fall ab, deshalb stehen beide Masse nebeneinander.")
    p("")
    p("## Protokoll")
    p("")
    for z in protokoll:
        p("- `%s`" % z.replace("`", "'"))
    p("")
    return "\n".join(zeilen) + "\n", len(befunde), len(offen)


def _schreiben(text, ergebnis, md5_vor, md5_nach, pfad, protokoll):
    ziel = os.path.join(WURZEL, "docs", "befunde")
    os.makedirs(ziel, exist_ok=True)
    with io.open(os.path.join(ziel, "HELLMODUS_ANSICHTEN.md"), "w",
                 encoding="utf-8", newline="\r\n") as f:
        f.write(text)
    roh = {"/".join(map(str, k)): v for k, v in ergebnis.items()}
    os.makedirs(os.path.join(WURZEL, "screenshots"), exist_ok=True)
    with io.open(os.path.join(WURZEL, "screenshots",
                              "hellmodus_ansichten.json"), "w",
                 encoding="utf-8") as f:
        f.write(json.dumps({"md5_vor": md5_vor, "md5_nach": md5_nach,
                            "laeufe": roh, "protokoll": protokoll,
                            "fest_verdrahtet": _fest_verdrahtet(pfad)},
                           ensure_ascii=False, indent=1))


def nur_bericht():
    """Den Bericht aus der vorhandenen JSON neu schreiben, ohne zu messen.
    Fuer eine Aenderung AM BERICHT - nicht an der Messung. Der Lauf dauert
    zehn Minuten; wer dafuer neu misst, misst einen anderen Baum."""
    q = os.path.join(WURZEL, "screenshots", "hellmodus_ansichten.json")
    d = json.loads(io.open(q, encoding="utf-8").read())
    ergebnis = {}
    for k, v in d["laeufe"].items():
        rolle, thema, breite = k.split("/")
        ergebnis[(rolle, thema, int(breite))] = v
    # Das Protokoll des MESSLAUFS mitnehmen. Ohne das verliert ein neu
    # geschriebener Bericht genau die Zeilen, die belegen, was gemessen wurde
    # (Saat, Reiterliste, Rollenvergleich) - und der Bericht saehe aus, als
    # waere er aus dem Nichts entstanden.
    prot = list(d.get("protokoll") or [])
    if not prot:
        prot = ["Die JSON fuehrt KEIN Protokoll des Messlaufs. Diese Fassung "
                "wurde aus ihr neu geschrieben; was der Lauf ueber Saat, "
                "Reiterliste und Rollen gemeldet hat, ist nicht mehr da."]
    prot.append("Bericht aus %s neu geschrieben, NICHT neu gemessen." % q)
    text, nb, no = _bericht(ergebnis, prot,
                            d["md5_vor"], d["md5_nach"], "(aus der JSON)", 0.0)
    _schreiben(text, ergebnis, d["md5_vor"], d["md5_nach"],
               os.path.join(WURZEL, os.environ.get("EPK_INDEX", "index.html")),
               prot)
    print("Bericht neu geschrieben. Befunde %d, NICHT GEMESSEN %d." % (nb, no))
    return 1 if (nb or no) else 0


def main():
    if "--nur-bericht" in sys.argv:
        return nur_bericht()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt.  pip install playwright && playwright install chromium")
        return 2

    import hashlib
    datei = os.environ.get("EPK_INDEX", "index.html")
    pfad = os.path.join(WURZEL, datei)

    def md5():
        with open(pfad, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    md5_vor = md5()
    print("Gemessen wird %s  (md5 %s)" % (datei, md5_vor))
    if datei == "index.html":
        print("WARNUNG: index.html wandert unter der Messung. Fuer ein")
        print("belastbares Ergebnis EPK_INDEX auf die eingefrorene Kopie setzen.")

    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port, datei)
    print("Quelle:", url)

    t0 = time.time()
    ergebnis = {}
    protokoll = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for rolle in ("admin",):
            for thema in THEMEN:
                for breite in BREITEN:
                    print("\n== Rolle %s, epk_theme=%s, %d px  (OS steht auf dunkel)"
                          % (rolle, thema, breite))
                    _lauf(browser, url, thema, breite, rolle, ergebnis, protokoll)

        # ── Rolle monteur: nur, wenn sie ANDERE Ansichten oeffnet ─────────
        # Ein zweiter vollstaendiger Lauf ueber dieselben Ansichten messe
        # dasselbe Thema zweimal. Gemessen wird also erst die Reiterliste;
        # gibt es keine neue Ansicht, wird das GESAGT und nicht gemessen.
        ctx = browser.new_context(viewport={"width": 390, "height": 880},
                                  is_mobile=True, has_touch=True,
                                  color_scheme="dark")
        ctx.add_init_script(INIT)
        ctx.add_init_script(_nutzer("monteur", "light"))
        ctx.route("**/rest/v1/**", lambda r: r.abort())
        ctx.route("**/auth/v1/**", lambda r: r.abort())
        s = ctx.new_page()
        s.goto(url, wait_until="domcontentloaded")
        s.wait_for_timeout(4500)
        mont = s.evaluate(TABS_JS)["reiter"]
        ctx.close()
        admin_reiter = ergebnis.get(("admin", "light", 390), {}).get("_reiter", [])
        neu = [x for x in mont if x not in admin_reiter]
        protokoll.append("Rolle monteur fuehrt %d Reiter: %s" % (len(mont), mont))
        protokoll.append("davon NICHT in der Admin-Liste: %s"
                         % (neu or "keine - kein zweiter Lauf noetig"))
        print("\n== Rolle monteur: %d Reiter, davon neu: %s" % (len(mont), neu or "keine"))
        if neu:
            for thema in THEMEN:
                for breite in BREITEN:
                    print("\n== Rolle monteur, epk_theme=%s, %d px" % (thema, breite))
                    _lauf(browser, url, thema, breite, "monteur", ergebnis, protokoll)
        browser.close()

    md5_nach = md5()
    if md5_nach != md5_vor:
        print("ABBRUCH DES URTEILS: die gemessene Datei hat sich waehrend des")
        print("Laufs geaendert (%s -> %s). Die Zahlen gehoeren damit zu zwei"
              % (md5_vor, md5_nach))
        print("verschiedenen Baeumen.")

    text, n_befunde, n_offen = _bericht(
        ergebnis, protokoll, md5_vor, md5_nach, url, time.time() - t0)

    _schreiben(text, ergebnis, md5_vor, md5_nach, pfad, protokoll)

    print("\n" + "=" * 70)
    print("Ansichten mit dunklem SCHIRM (ab %d %%) im HELLMODUS: %d"
          % (int(TRAGEND_AB * 100), n_befunde))
    print("Ansichten NICHT GEMESSEN (Koeder versagt / nicht erreicht): %d" % n_offen)
    print("Bericht: docs/befunde/HELLMODUS_ANSICHTEN.md")
    print("Rohwerte: screenshots/hellmodus_ansichten.json")
    print("md5 der gemessenen Datei: vor %s, nach %s" % (md5_vor, md5_nach))
    if md5_nach != md5_vor:
        return 1
    return 1 if (n_befunde or n_offen) else 0


if __name__ == "__main__":
    sys.exit(main())
