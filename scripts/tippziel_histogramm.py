# -*- coding: utf-8 -*-
"""Wie gross sind die Tippziele WIRKLICH - Hoehe UND Breite, ungekappt.

🔴 WARUM ES DIESES WERKZEUG GIBT: DAS ALTE WAR BLIND FUER BREITE.

`B.TIPP_JS` sammelt jedes Bedienelement mit `h < 44 || w < 44` und gibt
zurueck:

    knopf.sort((a, b) => a.h - b.h);
    return {klein: knopf.slice(0, 60), anzahl_klein: knopf.length, ...}

und `echtmengen_messen._kuerzen` schneidet davon noch einmal auf ZWOELF.
Sortiert wird nach HOEHE, aufsteigend. Ein Ziel, das 60 px hoch und 20 px
BREIT ist, steht damit am ENDE der Liste - und faellt heraus.

Aus dieser Liste habe ich am 28.09. geschlossen, es gebe keine Ziele unter
24 px Breite. Fuer die HOEHE traegt dieser Schluss (die Liste ist nach Hoehe
aufsteigend sortiert, die kleinsten stehen also drin). Fuer die BREITE traegt
er NICHT - die Grundgesamtheit der Beispiele ist nach dem falschen Merkmal
ausgewaehlt. Die Zahl `anzahl_klein` half auch nicht: sie zaehlt `h<44 ODER
w<44` in EINEM Topf und kann Hoehe und Breite nicht trennen.

🔴 Das ist kein falscher Riegel, sondern ein blindes MESSGERAET: es misst
einwandfrei - nur eine andere Grundgesamtheit als die, ueber die ich geredet
habe. Eine ABWESENHEIT darin belegt nichts.

WAS DIESES WERKZEUG ANDERS MACHT
Es zaehlt im Browser ueber die GANZE Menge und gibt nur ZAHLEN zurueck -
je 4-px-Klasse, fuer Hoehe und Breite GETRENNT, dazu die Kreuztabelle
"zu niedrig / zu schmal / beides". Nichts wird sortiert, nichts geschnitten.
Die Beispielliste bleibt eine Beispielliste und heisst auch so.

🔴 DREI KOEDER, UND DAS IST DER GANZE PUNKT
Ein einziger kleiner Koeder wuerde von BEIDEN Zaehlern gesehen und koennte
nicht zeigen, dass sie unabhaengig sind - genau der Fehler, der dieses
Werkzeug noetig gemacht hat.

    A   20 px hoch, 200 px breit  -> NUR der Hoehenzaehler darf ihn sehen
    B  200 px hoch,  20 px breit  -> NUR der Breitenzaehler darf ihn sehen
    C  200 px hoch, 200 px breit  -> KEINER darf ihn sehen (Gegenprobe)

Koeder B ist die Form, die das alte Werkzeug nachweislich verloren hat.
Findet der Breitenzaehler ihn nicht, ist der Lauf wertlos und bricht ab.

GRUNDGESAMTHEIT (und sie wird genannt, nicht vorausgesetzt)
Derselbe Waehler wie in `B.TIPP_JS`, damit die Zahlen mit der alten Aussage
vergleichbar sind: button, [role="button"], a, summary, .clickable und die
klickbaren input-Arten. Sichtbar heisst: Flaeche, nicht `display:none`,
nicht `visibility:hidden`, nicht durchsichtig.

Aufruf:
    python scripts/tippziel_histogramm.py                 # alle Ansichten
    python scripts/tippziel_histogramm.py zeit fahrzeuge  # nur diese
    python scripts/tippziel_histogramm.py --breite 390 zeit

Ergebnis: docs/befunde/TIPPZIEL_HISTOGRAMM.json und .md
"""
import io
import json
import os
import sys
import time

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
WURZEL = os.path.dirname(HIER)

import mob_ansicht_messen as M           # noqa: E402
import b3_vier_ansichten_messen as B     # noqa: E402
import b3_stufen_8_11_messen as S        # noqa: E402
import b3_stufen_12_15_messen as B12     # noqa: E402
import echtmengen_saat as SAAT           # noqa: E402
import echtmengen_messen as EM           # noqa: E402

GRUPPEN = [(B, "_navigieren", 3), (S, "_navigieren8", 4), (B12, "_navigieren12", 4)]

# WCAG 2.5.8 AA ist 24x24, 2.5.5 AAA ist 44x44. Beide Schwellen werden
# gezaehlt, damit die Aussage nicht von der gewaehlten Norm abhaengt.
SCHWELLEN = (24, 44)
KLASSENBREITE = 4
OBERGRENZE = 48          # alles darueber faellt in einen Sammeltopf

# Der Zaehler laeuft ueber die ganze Menge und gibt NUR Zahlen zurueck.
# Die Beispiele sind ausdruecklich Beispiele und stehen getrennt.
HISTOGRAMM_JS = r"""(cfg) => {
""" + B.HILFEN + r"""
  const sel = cfg.wahl;
  const kb = cfg.klassenbreite, og = cfg.obergrenze;
  const klasse = v => (v >= og ? og : Math.floor(v / kb) * kb);

  const hoehe = {}, breite = {}, arten = {};
  let gesamt = 0;
  const kreuz = {};
  cfg.schwellen.forEach(s => {
    kreuz[s] = {nur_hoch: 0, nur_breit: 0, beides: 0, keins: 0};
  });
  const beispiele = {};
  cfg.schwellen.forEach(s => { beispiele[s] = []; });

  const wurzel = cfg.zone
    ? document.getElementById('__hist_koeder')
    : (document.getElementById('root') || document.body);
  if (!wurzel) return null;

  wurzel.querySelectorAll(sel).forEach(e => {
    if (!cfg.zone && e.closest('#__hist_koeder')) return;
    if (!_sicht(e)) return;
    const r = e.getBoundingClientRect();
    const h = Math.round(r.height * 10) / 10;
    const w = Math.round(r.width * 10) / 10;
    gesamt++;
    const kh = klasse(h), kw = klasse(w);
    hoehe[kh] = (hoehe[kh] || 0) + 1;
    breite[kw] = (breite[kw] || 0) + 1;
    const art = e.tagName.toLowerCase() +
      (e.getAttribute('role') ? '[role=' + e.getAttribute('role') + ']' : '');
    arten[art] = (arten[art] || 0) + 1;
    cfg.schwellen.forEach(s => {
      const zh = h < s, zw = w < s;
      if (zh && zw) kreuz[s].beides++;
      else if (zh) kreuz[s].nur_hoch++;
      else if (zw) kreuz[s].nur_breit++;
      else kreuz[s].keins++;
      // Die Beispiele dienen dem LESEN, nicht dem Zaehlen. Sie sind
      // gedeckelt, die Zahlen darueber sind es NICHT.
      if ((zh || zw) && beispiele[s].length < 25) {
        beispiele[s].push({art: art, h: h, w: w,
                           text: _txt(e, 30),
                           aria: e.getAttribute('aria-label'),
                           titel: e.getAttribute('title'),
                           weg: _weg(e)});
      }
    });
  });
  return {gesamt: gesamt, hoehe: hoehe, breite: breite, arten: arten,
          kreuz: kreuz, beispiele: beispiele};
}"""

# Die drei Koeder. Jeder traegt !important, weil die Hausregel
# `min-height:44px !important` sonst gewinnt - ein Koeder, der von der
# eigenen App auf Normmass gezogen wird, beweist gar nichts.
KOEDER_EIN_JS = r"""() => {
  let z = document.getElementById('__hist_koeder');
  if (z) z.remove();
  z = document.createElement('div');
  z.id = '__hist_koeder';
  z.style.setProperty('position', 'fixed', 'important');
  z.style.setProperty('left', '0', 'important');
  z.style.setProperty('top', '0', 'important');
  z.style.setProperty('z-index', '2147483000', 'important');
  const masse = [['A', 20, 200], ['B', 200, 20], ['C', 200, 200]];
  const gemessen = {};
  masse.forEach(m => {
    const b = document.createElement('button');
    b.id = '__koeder_' + m[0];
    b.textContent = 'K' + m[0];
    [['min-height', m[1]], ['height', m[1]], ['max-height', m[1]],
     ['min-width', m[2]], ['width', m[2]], ['max-width', m[2]]]
      .forEach(p => b.style.setProperty(p[0], p[1] + 'px', 'important'));
    b.style.setProperty('padding', '0', 'important');
    b.style.setProperty('box-sizing', 'border-box', 'important');
    z.appendChild(b);
  });
  (document.getElementById('root') || document.body).appendChild(z);
  masse.forEach(m => {
    const r = document.getElementById('__koeder_' + m[0])
      .getBoundingClientRect();
    gemessen[m[0]] = {h: Math.round(r.height), w: Math.round(r.width),
                      soll_h: m[1], soll_w: m[2]};
  });
  return gemessen;
}"""

KOEDER_AUS_JS = r"""() => {
  const z = document.getElementById('__hist_koeder');
  if (z) z.remove();
  return !document.getElementById('__hist_koeder');
}"""


def _cfg(zone=False):
    return {"wahl": ('button, [role="button"], a, summary, .clickable, '
                     'input[type="checkbox"], input[type="radio"], '
                     'input[type="submit"], input[type="button"]'),
            "klassenbreite": KLASSENBREITE, "obergrenze": OBERGRENZE,
            "schwellen": list(SCHWELLEN), "zone": zone}


def eichen(seite):
    """🔴 Drei Koeder, drei verschiedene Fragen. Fehlt einer, ist alles hin.

    Der Rueckgabewert ist die Liste der MISSLUNGENEN Proben; leer heisst
    geeicht. Ein Lauf ohne diese Probe wuerde eine Null melden, die von
    "es gibt keine" nicht zu unterscheiden ist.
    """
    gemessen = seite.evaluate(KOEDER_EIN_JS)
    schief = []
    for name, g in sorted(gemessen.items()):
        if abs(g["h"] - g["soll_h"]) > 2 or abs(g["w"] - g["soll_w"]) > 2:
            schief.append(
                "Koeder %s wollte %dx%d px sein, ist aber %dx%d - die App "
                "uebersteuert ihn, er kann nichts beweisen."
                % (name, g["soll_h"], g["soll_w"], g["h"], g["w"]))
    h = seite.evaluate(HISTOGRAMM_JS, _cfg(zone=True))
    seite.evaluate(KOEDER_AUS_JS)
    if not h:
        return ["Die Koederzone war beim Messen nicht da."], gemessen
    k24 = _k(h["kreuz"], 24)
    if h["gesamt"] != 3:
        schief.append("Der Zaehler sieht %d der 3 Koeder." % h["gesamt"])
    if k24["nur_hoch"] != 1:
        schief.append(
            "Der HOEHEN-Zaehler findet Koeder A (20 px hoch, 200 px breit) "
            "nicht genau einmal, sondern %d mal." % k24["nur_hoch"])
    if k24["nur_breit"] != 1:
        schief.append(
            "Der BREITEN-Zaehler findet Koeder B (200 px hoch, 20 px BREIT) "
            "nicht genau einmal, sondern %d mal.\n     Genau diese Form hat "
            "das alte Werkzeug verloren - ohne sie misst auch dieses nichts."
            % k24["nur_breit"])
    if k24["keins"] != 1:
        schief.append(
            "Die Gegenprobe schlaegt fehl: Koeder C (200x200) faellt %d mal "
            "in einen der Zu-klein-Toepfe, erwartet war 0." % (3 - k24["keins"]))
    return schief, gemessen


def _navi(seite, kuerzel, breite):
    for modul, name, argzahl in GRUPPEN:
        if kuerzel in getattr(modul, "ANSICHTEN", {}):
            f = getattr(modul, name)
            return (f(seite, kuerzel, breite, []) if argzahl == 4
                    else f(seite, kuerzel, breite))
    raise SystemExit("unbekannte Ansicht: %s" % kuerzel)


def alle_ansichten():
    aus = []
    for modul, _, _ in GRUPPEN:
        aus.extend(sorted(getattr(modul, "ANSICHTEN", {})))
    return aus


def _k(kreuz, s):
    """Die Schluessel kommen als Zeichenkette aus JSON zurueck, als Zahl
    aus `evaluate`. Beides annehmen statt raten."""
    return kreuz.get(str(s)) or kreuz.get(s) or {}


def _summe(hist, grenze):
    """Wieviele Elemente liegen UNTER `grenze`? Aus den Klassen, nicht aus
    einer Beispielliste - das ist der ganze Unterschied."""
    n = 0
    for k, v in hist.items():
        if int(k) + KLASSENBREITE <= grenze:
            n += v
    return n


def bericht_schreiben(bericht):
    z = ["# Tippziele - Histogramm ueber die GANZE Menge", "",
         "Erzeugt von `scripts/tippziel_histogramm.py` am %s."
         % time.strftime("%Y-%m-%d %H:%M"),
         "Breite des Fensters: %d px." % bericht["breite"], "",
         "🔴 Dieses Werkzeug ersetzt eine Aussage, die auf einer nach HOEHE",
         "sortierten und auf zwoelf gekappten Beispielliste beruhte. Fuer die",
         "BREITE war diese Liste blind: ein hohes, schmales Ziel sortiert ans",
         "Ende und faellt heraus. Hier wird gezaehlt, nicht ausgewaehlt.", "",
         "Grundgesamtheit je Ansicht: `%s`" % bericht["wahl"], "",
         "## Zusammenzug", ""]
    kopf = ("| Ansicht | Ziele | <24 nur hoch | <24 nur BREIT | <24 beides "
            "| <44 nur hoch | <44 nur BREIT | <44 beides |")
    z += [kopf, "|---|---:|---:|---:|---:|---:|---:|---:|"]
    gesamt = {"gesamt": 0}
    for s in SCHWELLEN:
        for f in ("nur_hoch", "nur_breit", "beides"):
            gesamt["%s_%s" % (s, f)] = 0
    for name in sorted(bericht["ansichten"]):
        a = bericht["ansichten"][name]
        if a.get("fehler"):
            z.append("| %s | — | — nicht gemessen: %s |||||||"
                     % (name, a["fehler"]))
            continue
        k24, k44 = _k(a["kreuz"], 24), _k(a["kreuz"], 44)
        gesamt["gesamt"] += a["gesamt"]
        for s, kk in ((24, k24), (44, k44)):
            for f in ("nur_hoch", "nur_breit", "beides"):
                gesamt["%s_%s" % (s, f)] += kk.get(f, 0)
        z.append("| %s | %d | %d | %d | %d | %d | %d | %d |"
                 % (name, a["gesamt"],
                    k24.get("nur_hoch", 0), k24.get("nur_breit", 0),
                    k24.get("beides", 0),
                    k44.get("nur_hoch", 0), k44.get("nur_breit", 0),
                    k44.get("beides", 0)))
    z.append("| **Summe** | **%d** | **%d** | **%d** | **%d** | **%d** | "
             "**%d** | **%d** |"
             % (gesamt["gesamt"],
                gesamt["24_nur_hoch"], gesamt["24_nur_breit"],
                gesamt["24_beides"], gesamt["44_nur_hoch"],
                gesamt["44_nur_breit"], gesamt["44_beides"]))
    z += ["", "Dieselbe Stelle kann in mehreren Ansichten vorkommen (Kopf-",
          "und Fussleiste). Die Summe ist eine Summe von VORKOMMEN, nicht von",
          "verschiedenen Stellen - das steht hier, statt verschwiegen zu",
          "werden.", ""]

    for name in sorted(bericht["ansichten"]):
        a = bericht["ansichten"][name]
        if a.get("fehler"):
            continue
        z += ["## %s" % name, "",
              "%d Ziele. Klassen zu %d px, `%d` ist der Sammeltopf "
              "„%d px und mehr“." % (a["gesamt"], KLASSENBREITE,
                                               OBERGRENZE, OBERGRENZE), ""]
        for feld, wort in (("hoehe", "Hoehe"), ("breite", "Breite")):
            teile = ["%s px: %d" % (k, a[feld][k])
                     for k in sorted(a[feld], key=lambda x: int(x))]
            z.append("- **%s** — %s" % (wort, ", ".join(teile)))
        for s in SCHWELLEN:
            bsp = (a.get("beispiele") or {}).get(str(s)) or \
                  (a.get("beispiele") or {}).get(s) or []
            schmal = [b for b in bsp if b["w"] < s]
            if not schmal:
                continue
            z += ["", "  Beispiele unter %d px BREIT (Auszug aus %d):"
                  % (s, _k(a["kreuz"], s).get("nur_breit", 0)
                     + _k(a["kreuz"], s).get("beides", 0))]
            for b in schmal[:8]:
                z.append("  - `%s` %sx%s px — %r"
                         % (b["art"], b["h"], b["w"],
                            b["aria"] or b["titel"] or b["text"] or b["weg"]))
        z.append("")

    ziel = os.path.join(WURZEL, "docs", "befunde")
    if not os.path.isdir(ziel):
        os.makedirs(ziel)
    # Die Breite gehoert IN den Dateinamen. Ein Lauf bei 390 px, der den
    # Bericht von 1440 px ueberschreibt, sieht aus wie eine Korrektur und ist
    # ein Verlust - und beim Lesen ist nicht mehr zu sehen, welche Breite
    # gemeint war.
    md = os.path.join(ziel, "TIPPZIEL_HISTOGRAMM_%d.md" % bericht["breite"])
    js = os.path.join(ziel, "TIPPZIEL_HISTOGRAMM_%d.json" % bericht["breite"])
    io.open(md, "w", encoding="utf-8", newline="").write("\n".join(z) + "\n")
    io.open(js, "w", encoding="utf-8", newline="").write(
        json.dumps(bericht, ensure_ascii=False, indent=1))
    return md, js, gesamt


def main(argv):
    from playwright.sync_api import sync_playwright
    breite = 1440
    if "--breite" in argv:
        i = argv.index("--breite")
        breite = int(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    ansichten = argv or alle_ansichten()
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port,
                                      os.environ.get("EPK_INDEX", "index.html"))
    saat = SAAT.saat()
    bericht = {"breite": breite, "wahl": _cfg()["wahl"], "ansichten": {}}
    t0 = time.time()
    geeicht = False

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for nr, kuerzel in enumerate(ansichten, 1):
            ctx = EM._ctx(browser, breite)
            seite = ctx.new_page()
            try:
                seite.goto(url, wait_until="domcontentloaded")
                seite.wait_for_timeout(3800)
                EM._saeen(seite, saat, still=True)
                _navi(seite, kuerzel, breite)
                seite.wait_for_timeout(1600)

                if not geeicht:
                    schief, gemessen = eichen(seite)
                    print("Eichung der drei Koeder (%s):" % kuerzel)
                    for n, g in sorted(gemessen.items()):
                        print("   K%s soll %dx%d, ist %dx%d"
                              % (n, g["soll_h"], g["soll_w"], g["h"], g["w"]))
                    if schief:
                        for m in schief:
                            print("   \U0001F534 " + m)
                        print("\nNICHT GEMESSEN. Ein ungeeichtes Histogramm "
                              "meldet eine Null, die von\n„es gibt "
                              "keine“ nicht zu unterscheiden ist - genau "
                              "der Fehler, den\ndieses Werkzeug beheben "
                              "soll.")
                        return 2
                    print("   \U0001F7E2 A nur in der Hoehe, B nur in der "
                          "BREITE, C in keinem Topf.\n")
                    geeicht = True

                h = seite.evaluate(HISTOGRAMM_JS, _cfg())
                if not h or not h["gesamt"]:
                    bericht["ansichten"][kuerzel] = {
                        "fehler": "kein einziges Bedienelement gefunden"}
                    print("%2d/%d %-12s \U0001F534 KEIN Bedienelement - das "
                          "ist kein Ergebnis." % (nr, len(ansichten), kuerzel))
                    continue
                bericht["ansichten"][kuerzel] = h
                k24 = _k(h["kreuz"], 24)
                print("%2d/%d %-12s %4d Ziele | <24: hoch %d, BREIT %d, "
                      "beides %d"
                      % (nr, len(ansichten), kuerzel, h["gesamt"],
                         k24.get("nur_hoch", 0), k24.get("nur_breit", 0),
                         k24.get("beides", 0)))
            except Exception as e:                       # noqa: BLE001
                bericht["ansichten"][kuerzel] = {
                    "fehler": "%s: %s" % (type(e).__name__, str(e)[:160])}
                print("%2d/%d %-12s \U0001F534 %s: %s"
                      % (nr, len(ansichten), kuerzel, type(e).__name__,
                         str(e)[:110]))
            finally:
                ctx.close()
        browser.close()

    if not geeicht:
        print("\n\U0001F534 Die Eichung ist NIE gelaufen - keine Ansicht kam "
              "so weit.\nDie Zahlen unten sind damit nicht beurteilbar.")
        return 2

    md, js, gesamt = bericht_schreiben(bericht)
    misslungen = [k for k, v in bericht["ansichten"].items() if v.get("fehler")]
    print("\n%d Ansichten, %d Vorkommen, %.0f s"
          % (len(bericht["ansichten"]) - len(misslungen), gesamt["gesamt"],
             time.time() - t0))
    print("unter 24 px:  nur hoch %d | nur BREIT %d | beides %d"
          % (gesamt["24_nur_hoch"], gesamt["24_nur_breit"],
             gesamt["24_beides"]))
    print("unter 44 px:  nur hoch %d | nur BREIT %d | beides %d"
          % (gesamt["44_nur_hoch"], gesamt["44_nur_breit"],
             gesamt["44_beides"]))
    if misslungen:
        print("\U0001F534 NICHT gemessen: %s" % ", ".join(sorted(misslungen)))
    print("geschrieben: %s und %s" % (md, js))
    return 1 if misslungen else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
