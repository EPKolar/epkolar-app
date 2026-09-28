# -*- coding: utf-8 -*-
"""Die aufgeklappten Bereiche der Ansichten messen - der grosse Rest.

🔴 DAS IST DIE GROESSERE HAELFTE DES BLINDEN FLECKS. `dialoge_erkunden.py` hat
gezeigt: die App benutzt fast keine Modalen. Was anderswo ein Dialog waere -
ein Formular, eine Detailansicht, eine Auswahl - schiebt sich hier INLINE in
den Fluss der Seite. Die Messreihe misst Ansichten im RUHEZUSTAND, also
zugeklappt. Alles, was erst nach einem Klick erscheint, war nie gemessen.

WIE ERKANNT WIRD, DASS SICH ETWAS GEOEFFNET HAT
───────────────────────────────────────────────
Nicht an `position: fixed` - das war das Merkmal fuer Ueberlagerungen und
findet hier nichts. Gemessen wird der SICHTBARE BAUM: die Zahl der sichtbaren
Bedienelemente und Eingabefelder. Waechst sie nach einem Klick deutlich, ist
etwas aufgegangen.

🔴 EINE SCHWELLE IST NOETIG, UND SIE MUSS BEGRUENDET SEIN. Ein Klick, der
einen einzigen Knopf umschaltet, aendert den Baum auch - das ist kein
aufgeklappter Bereich. Die Schwelle steht auf **5 neuen Elementen**: weniger
ist ein Zustandswechsel, mehr ist ein Bereich. Sie ist willkuerlich gewaehlt
und darum HIER benannt; der Bericht fuehrt je Fund die tatsaechliche Zahl mit,
damit man sie nachrechnen kann.

🔴 ZERSTOERENDE KNOEPFE WERDEN NICHT GEKLICKT. Die Saat ist eine Attrappe,
aber ein Loeschklick macht die naechste Messung wertlos - und ein Exportklick
oeffnet ein Download-Fenster, das den Browser anhaelt. Die Sperrliste steht
unten als NAMEN, nicht als Zahl. Sie faellt zur sicheren Seite: lieber ein
Bereich ungemessen als eine Messreihe, die sich selbst zerstoert.

🔴 NACH JEDEM KLICK WIRD DIE ANSICHT NEU AUFGEBAUT. Sonst misst der zweite
Klick den Zustand, den der erste hinterlassen hat, und der Bericht nennt
Bereiche, die es so nie gab.
"""
import io
import json
import os
import re
import sys
import time

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)

import mob_ansicht_messen as M           # noqa: E402
import b3_vier_ansichten_messen as B     # noqa: E402
import b3_stufen_8_11_messen as S        # noqa: E402
import b3_stufen_12_15_messen as B12     # noqa: E402
import echtmengen_saat as SAAT           # noqa: E402
import echtmengen_messen as EM           # noqa: E402

GRUPPEN = [(B, "_navigieren", 3), (S, "_navigieren8", 4), (B12, "_navigieren12", 4)]

SCHWELLE = 5          # ab so vielen neuen Elementen gilt es als Bereich
# Anteil der Knopf-Beschriftungen des Ruhezustands, die nach dem Klick NOCH
# DA sein muessen. Darunter ist es keine Aufklappung, sondern ein Wechsel der
# Ansicht. 0.8 laesst Raum fuer die paar Knoepfe, die ein Bereich verdraengt
# (ein „Bearbeiten" wird zu „Abbrechen"), und schliesst eine Navigation aus,
# bei der praktisch der ganze Inhalt getauscht wird.
ERHALT_MINDESTENS = 0.8
HOECHSTENS_KNOEPFE = 30

# Knoepfe, die NICHT geklickt werden - als Wortstaemme, nicht als ganze Texte:
# die Beschriftungen wechseln, die Absicht nicht.
GESPERRT = ("lösch", "loesch", "entfern", "verwerf", "papierkorb", "reset",
            "zurücksetz", "zuruecksetz", "abmeld", "logout", "senden",
            "absenden", "versend", "mail", "export", "download", "herunterlad",
            "drucken", "pdf", "excel", "xls", "csv", "speicher", "anlegen",
            "erstellen", "buchen", "genehmig", "ablehn", "archiv",
            "synchronis", "hochlad", "upload", "kamera", "foto")

MESSEN_JS = r"""() => {
  // 🔴 GEMESSEN WIRD NUR DER INHALTSBEREICH, NICHT DIE GANZE SEITE.
  //    Der erste Lauf mass das ganze Dokument - und die HUELLE (Reiterzeile,
  //    Seitenleiste, Kopf) ueberwiegt: ein Klick auf „🔧 Werkzeuge" wechselte
  //    die Ansicht und kam trotzdem auf einen Erhalt von 0.97, weil fast alle
  //    Beschriftungen der Huelle stehen blieben. Der Unterscheider war damit
  //    blind fuer genau den Fall, fuer den er gebaut wurde.
  const wurzel = document.querySelector('.main-pad')
               || document.querySelector('main')
               || document.body;
  const sicht = e => {
    const r = e.getBoundingClientRect();
    if (!r.width || !r.height) return false;
    const s = getComputedStyle(e);
    return s.display !== 'none' && s.visibility !== 'hidden' && s.opacity !== '0';
  };
  const knopfSel = 'button,[role="button"],a,summary,input[type="checkbox"]';
  const feldSel = 'select,textarea,input:not([type="hidden"])';
  let knoepfe = 0, felder = 0;
  const klein = [], tipp = [], namenlos = [];
  for (const e of wurzel.querySelectorAll(knopfSel)) {
    if (!sicht(e)) continue;
    knoepfe++;
    const r = e.getBoundingClientRect();
    if (Math.min(r.width, r.height) < 24) {
      tipp.push({w: Math.round(r.width * 10) / 10,
                 h: Math.round(r.height * 10) / 10,
                 text: (e.innerText || '').trim().slice(0, 18),
                 aria: e.getAttribute('aria-label')});
    }
    if (e.matches('button,[role="button"]')) {
      const t = (e.innerText || '').trim();
      // Ein Icon-Knopf: sein ganzer Text traegt keinen Buchstaben und keine
      // Ziffer. Ohne aria-label und ohne title ist er fuer eine Vorlesehilfe
      // namenlos.
      const wort = /[\p{L}\p{N}]/u.test(t);
      if (!wort && !e.getAttribute('aria-label') && !e.getAttribute('title')) {
        namenlos.push({text: t.slice(0, 8),
                       w: Math.round(r.width), h: Math.round(r.height)});
      }
    }
  }
  for (const e of wurzel.querySelectorAll(feldSel)) {
    if (sicht(e)) felder++;
  }
  for (const e of wurzel.querySelectorAll('*')) {
    if (e.children.length || !(e.innerText || '').trim()) continue;
    if (!sicht(e)) continue;
    const px = parseFloat(getComputedStyle(e).fontSize);
    if (px < 12) klein.push({px: px, text: (e.innerText || '').trim().slice(0, 20)});
  }
  const marken = [...wurzel.querySelectorAll('button,[role="button"]')]
      .filter(sicht)
      .map(e => ((e.innerText || '') + '|' + (e.getAttribute('aria-label') || '')
                 + '|' + (e.getAttribute('title') || ''))
                .replace(/\s+/g, ' ').trim())
      .filter(s => s.length > 2);
  return {knoepfe: knoepfe, felder: felder, marken: marken,
          unter12: klein.length, unter12_bsp: klein.slice(0, 5),
          unter24: tipp.length, unter24_bsp: tipp.slice(0, 6),
          namenlos: namenlos.length, namenlos_bsp: namenlos.slice(0, 5)};
}"""

# 🔴 DIE AUSWAHL DER KLICKBAREN IST DER GANZE MELDER. Der erste Lauf nahm nur
#    `button,[role="button"]` und fand in fahrzeuge NULL Bereiche - und meldete
#    das brav als misslungenen Griff. Der Grund: was eine Detailansicht
#    oeffnet, ist hier meistens ein `div` mit `tabIndex` OHNE `role="button"`
#    (acht dieser Flaechen enthalten selbst einen Knopf, und ein Knopf im Knopf
#    ist ungueltiges ARIA - siehe v3.9.975). Wer die Klasse nicht mitnimmt,
#    misst die Karten nicht, die er messen will.
KLICKBAR_SEL = ('button,[role="button"],summary,'
                '[tabindex]:not([tabindex="-1"])')

KNOEPFE_JS = r"""(sel) => {
  // 🔴 NUR KLICKBARE IM INHALTSBEREICH. Das ist der Unterscheider, und er ist
  //    STRUKTURELL statt heuristisch: ein Klick INNERHALB des Inhalts kann
  //    keine Ansichtsnavigation sein - die Navigation steht in der Huelle.
  //    Vorher klickte der Melder die Reiterzeile, die Seitenleiste, Sync und
  //    Kamera mit und mass dann den Inhalt: entweder +0 (die Ueberlagerungen
  //    liegen ausserhalb) oder ein vollstaendiger Austausch (Navigation).
  //    Beides sah aus wie ein Befund und war keiner.
  const wurzel = document.querySelector('.main-pad')
               || document.querySelector('main')
               || document.body;
  return [...wurzel.querySelectorAll(sel)]
    .map((e, i) => {
      const r = e.getBoundingClientRect();
      return {i: i, sichtbar: !!(r.width && r.height) && !e.disabled,
              tag: e.tagName.toLowerCase(),
              text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40),
              titel: e.getAttribute('title'),
              aria: e.getAttribute('aria-label')};
    })
    .filter(x => x.sichtbar);
}"""

# 🔴 GEKLICKT WIRD UEBER DIE BESCHRIFTUNG, NICHT UEBER DIE POSITION.
#    Der dritte Lauf meldete fuer VIERZEHN verschiedene Knoepfe hintereinander
#    exakt +0 in jeder Spalte. Vierzehn identische Nullen sind keine
#    Eigenschaft der App, sondern die Signatur eines Messfehlers: die Liste der
#    Klickbaren wurde EINMAL am Anfang erhoben, und nach jedem Neuaufbau der
#    Ansicht zeigte derselbe Index auf ein anderes Element. Am Ende klickte der
#    Melder irgendwohin und meldete brav „nichts passiert".
#    Eine Beschriftung ueberlebt den Neuaufbau, eine Position nicht.
KLICK_JS = r"""([sel, text, aria, titel, tag]) => {
  const wurzel = document.querySelector('.main-pad')
               || document.querySelector('main')
               || document.body;
  const passt = e => {
    if (e.tagName.toLowerCase() !== tag) return false;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40);
    return t === text
        && (e.getAttribute('aria-label') || null) === aria
        && (e.getAttribute('title') || null) === titel;
  };
  const e = [...wurzel.querySelectorAll(sel)].find(x => {
    const r = x.getBoundingClientRect();
    return r.width && r.height && !x.disabled && passt(x);
  });
  if (!e) return false;
  e.click();
  return true;
}"""


def _gesperrt(k):
    wort = " ".join(x for x in (k.get("text"), k.get("titel"), k.get("aria"))
                    if x).lower()
    return next((g for g in GESPERRT if g in wort), None)


def eichen():
    """🔴 Selbstprobe der Sperrliste. Ohne sie waere sie eine Attrappe:
    eine Liste, die nie greift, sieht aus wie eine Liste, die schuetzt."""
    faelle = [({"text": "🗑 Löschen"}, True),
              ({"aria": "Eintrag löschen"}, True),
              ({"titel": "Als PDF exportieren"}, True),
              ({"text": "Speichern"}, True),
              ({"text": "Filter"}, False),
              ({"text": "Details"}, False),
              ({"aria": "Zeile nach oben"}, False)]
    schief = []
    for k, soll in faelle:
        if bool(_gesperrt(k)) != soll:
            schief.append((k, soll))
    return schief


def _navi(seite, kuerzel, breite):
    for modul, name, argzahl in GRUPPEN:
        if kuerzel in getattr(modul, "ANSICHTEN", {}):
            f = getattr(modul, name)
            return (f(seite, kuerzel, breite, []) if argzahl == 4
                    else f(seite, kuerzel, breite))
    raise SystemExit("unbekannte Ansicht: %s" % kuerzel)


def _frisch(browser, ctx, url, saat, kuerzel, breite):
    """🔴 WEDER NEU NAVIGIEREN NOCH NEU LADEN IST EIN ZURUECKSETZEN.

    Der fuenfte Lauf fand 21 von 27 Knoepfen „nach dem Neuaufbau nicht mehr" -
    und der Vergleich war nachweislich in Ordnung (44 Kandidaten, alle im
    selben Aufruf wiedergefunden). Die Ursache: die ersten beiden Knoepfe der
    Fahrzeugansicht sind `☰` und `⊞`, Listen- gegen Kachelansicht. Diese Wahl
    wird GESPEICHERT. Ab dem dritten Klick mass der Melder eine andere
    Darstellung und meldete lauter Fehlschlaege - die wie „der Knopf oeffnet
    nichts" aussehen.

    Der sechste Lauf lud die Seite darum vollstaendig neu - und fand
    NEUNZEHN weiterhin nicht. Denn `localStorage` ueberlebt ein Neuladen; nur
    ein neuer Browser-Kontext raeumt es weg.

    Deshalb bekommt JEDER Klick einen eigenen Kontext. Das kostet rund zehn
    Sekunden und ist der Preis dafuer, dass zwei Messungen ueberhaupt
    vergleichbar sind.
    """
    ctx.close()
    neu = EM._ctx(browser, breite)
    seite = neu.new_page()
    seite.goto(url, wait_until="domcontentloaded")
    seite.wait_for_timeout(3800)
    EM._saeen(seite, saat, still=True)
    _navi(seite, kuerzel, breite)
    seite.wait_for_timeout(1600)
    return neu, seite


def main(argv):
    from playwright.sync_api import sync_playwright
    schief = eichen()
    if schief:
        for k, soll in schief:
            print("\U0001F534 Sperrliste: %r sollte %s sein" % (k, soll))
        print("Die Sperrliste ist nicht geeicht - der Lauf wuerde entweder\n"
              "zerstoerende Knoepfe klicken oder harmlose auslassen.")
        return 2
    print("Sperrliste: 7 von 7 Eichfaellen richtig (3 Gegenproben)")

    ansichten = argv or ["fahrzeuge", "mitarbeiter", "as_liste", "werkzeuge"]
    breite = 1440
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port,
                                      os.environ.get("EPK_INDEX", "index.html"))
    saat = SAAT.saat()
    bericht = {"schwelle": SCHWELLE, "breite": breite, "ansichten": {}}
    t0 = time.time()

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for kuerzel in ansichten:
            ctx = EM._ctx(browser, breite)
            seite = ctx.new_page()
            bereiche, uebersprungen, gewechselt = [], [], []
            try:
                seite.goto(url, wait_until="domcontentloaded")
                seite.wait_for_timeout(3800)
                EM._saeen(seite, saat, still=True)
                _navi(seite, kuerzel, breite)
                seite.wait_for_timeout(1600)

                ruhe = seite.evaluate(MESSEN_JS)
                # 🔴 Ohne diese Probe ist der ganze Lauf wertlos: findet der
                #    Melder im Ruhezustand nichts, ist jeder Erhalt 0 und
                #    jeder Klick sieht aus wie ein aufgeklappter Bereich.
                if len(set(ruhe["marken"])) < 3:
                    print("   \U0001F534 %s: der Inhaltsbereich traegt im "
                          "Ruhezustand nur %d verschiedene\n"
                          "      Knopf-Beschriftungen. Das ist kein "
                          "Ruhezustand, das ist ein misslungener Griff "
                          "- NICHT gemessen."
                          % (kuerzel, len(set(ruhe["marken"]))))
                    bericht["ansichten"][kuerzel] = {"messbar": False,
                                                     "marken": len(ruhe["marken"])}
                    continue
                alle = seite.evaluate(KNOEPFE_JS, KLICKBAR_SEL)
                # 🔴 JE BESCHRIFTUNG EINER. In fahrzeuge sind 21 der ersten 30
                #    Klickbaren derselbe Favoritenstern; sie fressen das
                #    Klickbudget auf, ohne einen einzigen neuen Bereich zu
                #    oeffnen. Gemessen wird ein Vertreter je Beschriftung -
                #    dadurch reichen 30 Klicks fuer 30 VERSCHIEDENE Knoepfe
                #    statt fuer 30 Karten desselben Knopfs.
                knoepfe, gesehen = [], set()
                for k in alle:
                    schl = (k["text"], k["titel"], k["aria"], k["tag"])
                    if schl in gesehen:
                        continue
                    gesehen.add(schl)
                    knoepfe.append(k)
                print("\n=== %s: %d klickbar, davon %d verschieden | "
                      "Ruhezustand %d Bedienelemente / %d Felder"
                      % (kuerzel, len(alle), len(knoepfe), ruhe["knoepfe"],
                         ruhe["felder"]))
                print("    Ruhezustand: unter 12 px %d | unter 24 px %d | "
                      "namenlos %d"
                      % (ruhe["unter12"], ruhe["unter24"], ruhe["namenlos"]))

                for k in knoepfe[:HOECHSTENS_KNOEPFE]:
                    grund = _gesperrt(k)
                    if grund:
                        uebersprungen.append({"knopf": k["text"] or k["aria"],
                                              "grund": grund})
                        continue
                    try:
                        getroffen = seite.evaluate(
                            KLICK_JS, [KLICKBAR_SEL, k["text"], k["aria"],
                                       k["titel"], k["tag"]])
                        if not getroffen:
                            # 🔴 Kein Treffer ist KEIN Ergebnis. Ohne diese
                            #    Buchung stuende hier eine Null, die aussieht
                            #    wie „der Knopf oeffnet nichts".
                            uebersprungen.append(
                                {"knopf": k["text"] or k["aria"],
                                 "grund": "nach dem Neuaufbau nicht mehr "
                                          "gefunden - NICHT geklickt"})
                            continue
                        seite.wait_for_timeout(1200)
                        jetzt = seite.evaluate(MESSEN_JS)
                    except Exception as e:
                        uebersprungen.append({"knopf": k["text"],
                                              "grund": str(e)[:60]})
                        ctx, seite = _frisch(browser, ctx, url, saat,
                                             kuerzel, breite)
                        continue

                    zuwachs = ((jetzt["knoepfe"] - ruhe["knoepfe"])
                               + (jetzt["felder"] - ruhe["felder"]))
                    # 🔴 ES GIBT ZWEI ARTEN VON BEREICH, UND MEIN ERSTER
                    #    ENTWURF KANNTE NUR EINE. Ich suchte nach ZUWACHS -
                    #    etwas klappt auf und legt Elemente dazu. In dieser
                    #    App ist das die seltenere Form. Die haeufigere ist
                    #    Meister-Detail: die Karte oeffnet die Detailansicht
                    #    AN ORT UND STELLE und ERSETZT die Liste. Der Zuwachs
                    #    ist dabei klein oder negativ - mein Melder sah 18 mal
                    #    genau das und verbuchte es als „Navigation".
                    #
                    #    Dass es keine sein KANN, ist strukturell: geklickt
                    #    wird nur INNERHALB des Inhaltsbereichs, und dort
                    #    steht kein Navigationsknopf. Der Eimer „navigiert"
                    #    hiess also falsch, nicht die Messung.
                    behalten = set(ruhe["marken"]) & set(jetzt["marken"])
                    erhalt = (len(behalten) / len(set(ruhe["marken"]))
                              if ruhe["marken"] else 0.0)
                    ersetzend = erhalt < ERHALT_MINDESTENS
                    if zuwachs >= SCHWELLE or ersetzend:
                        fund = {"knopf": (k["text"] or k["aria"]
                                          or k["titel"] or "")[:40],
                                "art": "ersetzend" if ersetzend
                                       else "ergaenzend",
                                "zuwachs": zuwachs,
                                "erhalt": round(erhalt, 2),
                                "felder_neu": jetzt["felder"] - ruhe["felder"],
                                "unter12": jetzt["unter12"] - ruhe["unter12"],
                                "unter24": jetzt["unter24"] - ruhe["unter24"],
                                "namenlos": jetzt["namenlos"] - ruhe["namenlos"],
                                "unter12_bsp": jetzt["unter12_bsp"],
                                "unter24_bsp": jetzt["unter24_bsp"],
                                "namenlos_bsp": jetzt["namenlos_bsp"]}
                        # 🔴 BEI EINEM ERSETZENDEN BEREICH IST DIE DIFFERENZ
                        #    IRREFUEHREND. Wenn der Ruhezustand verschwindet,
                        #    heisst „unter 12 px: +0" nicht „nichts Kleines
                        #    dazugekommen", sondern „die neue Ansicht hat
                        #    zufaellig gleich viele". Beurteilt wird deshalb
                        #    der ABSOLUTE Stand des geoeffneten Bereichs.
                        fund["abs_unter12"] = jetzt["unter12"]
                        fund["abs_unter24"] = jetzt["unter24"]
                        fund["abs_namenlos"] = jetzt["namenlos"]
                        bereiche.append(fund)
                        marke = ("\U0001F7E2" if not (jetzt["unter12"]
                                                      or jetzt["namenlos"])
                                 else "\U0001F534")
                        print("   %s %-28s %-10s Erhalt %.2f | im Bereich: "
                              "<12px %d, <24px %d, namenlos %d"
                              % (marke, fund["knopf"][:28], fund["art"],
                                 erhalt, jetzt["unter12"], jetzt["unter24"],
                                 jetzt["namenlos"]))
                        for b in fund["unter12_bsp"][:2]:
                            print("          %spx %r" % (b["px"], b["text"]))
                        for b in fund["namenlos_bsp"][:2]:
                            print("          namenlos %dx%d %r"
                                  % (b["w"], b["h"], b["text"]))
                    ctx, seite = _frisch(browser, ctx, url, saat,
                                         kuerzel, breite)
            finally:
                ctx.close()
            bericht["ansichten"][kuerzel] = {
                "ruhe": ruhe, "bereiche": bereiche,
                "uebersprungen": uebersprungen,
                "navigiert": gewechselt}
        browser.close()

    ziel = os.path.join(WURZEL, "docs", "befunde", "INLINE_BEREICHE.json")
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps(bericht, ensure_ascii=False, indent=1))
    ges = sum(len(v["bereiche"]) for v in bericht["ansichten"].values())
    # 🔴 Dieser Eimer MUSS leer bleiben, und das ist eine Strukturprobe, kein
    #    Zierrat: geklickt wird nur im Inhaltsbereich, dort steht kein
    #    Navigationsknopf. Ist er je gefuellt, greift die Einengung nicht mehr
    #    - und dann misst der Melder wieder fremde Ansichten als „Bereiche".
    nav = sum(len(v.get("navigiert") or ())
              for v in bericht["ansichten"].values())
    if nav:
        print("   \U0001F534 %d Klicks haben die ANSICHT gewechselt, obwohl "
              "nur im\n      Inhaltsbereich geklickt wird. Die Einengung "
              "greift nicht - die Zahlen\n      oben sind NICHT belastbar."
              % nav)
    print("\n%d Bereiche in %d Ansichten, %d s" % (ges, len(ansichten),
                                                   int(time.time() - t0)))
    if not ges:
        print("\U0001F534 KEIN einziger Bereich gefunden. Das ist kein "
              "Ergebnis, das ist ein\n   misslungener Griff - entweder ist "
              "die Schwelle zu hoch oder die Knoepfe\n   reagieren nicht.")
    print("geschrieben:", ziel)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
