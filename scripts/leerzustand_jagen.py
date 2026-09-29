# -*- coding: utf-8 -*-
"""Was zeigt die App, wenn NICHTS da ist?

🔴 WARUM DIESER ZUSTAND SELTEN GEPRUEFT WIRD: alle Messreihen dieses Hauses
saeen zuerst Daten ein - sonst waere die Ansicht leer und man koennte nichts
messen. Genau deshalb hat den LEEREN Zustand kaum je jemand gesehen. Ein
Monteur auf einer neuen Baustelle sieht ihn als erstes.

GESUCHT WIRD, was der Nutzer NIE sehen darf:
    NaN            eine Rechnung mit einem fehlenden Wert
    undefined      ein Feld, das es nicht gibt, als Text gerendert
    Invalid Date   ein Datum, das nicht gelesen werden konnte
    [object Object] ein Objekt, das als Text ausgegeben wurde
    null           dasselbe in Gruen
und dazu jeder Fehler in der Konsole und jeder unbehandelte Absturz.

🔴 SELBSTPROBE: in dieselbe Seite wird ein Text mit genau diesen Formen
EINGESETZT und muss gefunden werden. Ein Sucher, der auch den eingesetzten
Koeder nicht sieht, meldet fuer jede Seite der Welt "sauber".

🔴 UND EINE GEGENPROBE IN DIE ANDERE RICHTUNG: derselbe Lauf faehrt einmal
MIT Daten. Findet er dort dieselben Formen, sind sie kein Befund des leeren
Zustands, sondern ein allgemeiner - das gehoert unterschieden.

Aufruf:  python scripts/leerzustand_jagen.py [breite]
"""
import io
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
WURZEL = os.path.dirname(HIER)

import mob_ansicht_messen as M           # noqa: E402
import b3_vier_ansichten_messen as B     # noqa: E402
import b3_stufen_8_11_messen as S        # noqa: E402
import b3_stufen_12_15_messen as B12     # noqa: E402
import echtmengen_saat as SAAT           # noqa: E402
import echtmengen_messen as EM           # noqa: E402

GRUPPEN = [(B, "_navigieren", 3), (S, "_navigieren8", 4),
           (B12, "_navigieren12", 4)]
ANSICHTEN = ["home", "as_liste", "werkzeuge", "fahrzeuge", "mitarbeiter",
             "zeit", "planung", "auswertungen", "monatsabr", "chef",
             "einstell", "abwesend", "flotte", "buero", "gefahr"]

# Die Formen, die der Nutzer nie sehen darf. Als WORT gesucht, damit
# "undefiniert" oder ein Nachname wie "Nanninga" nicht mitzaehlt.
VERBOTEN = ["NaN", "undefined", "Invalid Date", "[object Object]",
            "null", "NULL"]

LESEN_JS = r"""(formen) => {
  const wurzel = document.getElementById('root') || document.body;
  const text = (wurzel.innerText || '');
  const aus = {};
  for (const f of formen) {
    // Wortgrenzen, damit "undefiniert" oder "Nanninga" nicht mitzaehlen.
    const roh = f.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const re = new RegExp('(^|[^\\p{L}\\p{N}_])' + roh
                          + '([^\\p{L}\\p{N}_]|$)', 'gu');
    const t = text.match(re);
    if (t && t.length) {
      aus[f] = {anzahl: t.length, umgebung: []};
      let i = text.indexOf(f);
      while (i >= 0 && aus[f].umgebung.length < 3) {
        aus[f].umgebung.push(
          text.slice(Math.max(0, i - 45), i + 45).replace(/\s+/g, ' '));
        i = text.indexOf(f, i + 1);
      }
    }
  }
  return {gefunden: aus, textlaenge: text.length};
}"""

KOEDER_EIN_JS = r"""() => {
  let z = document.getElementById('__leerprobe');
  if (z) z.remove();
  z = document.createElement('div');
  z.id = '__leerprobe';
  // 🔴 JE GESUCHTER FORM EIN KOEDER. Der erste Entwurf nannte `null`, aber
  //    nicht `NULL` - und der Lauf brach zu Recht ab, weil dieser eine
  //    Zaehler ungeeicht war. Genau so entsteht sonst eine Null, die von
  //    "sauber" nicht zu unterscheiden ist.
  z.textContent = 'Summe NaN Stunden, Datum Invalid Date, Wert undefined, '
                + 'Objekt [object Object], Rest null, Spalte NULL.';
  (document.getElementById('root') || document.body).appendChild(z);
  return true;
}"""

KOEDER_AUS_JS = r"""() => {
  const z = document.getElementById('__leerprobe');
  if (z) z.remove();
  return !document.getElementById('__leerprobe');
}"""


def _navi(seite, kuerzel, breite):
    for modul, name, argzahl in GRUPPEN:
        if kuerzel in getattr(modul, "ANSICHTEN", {}):
            f = getattr(modul, name)
            return (f(seite, kuerzel, breite, []) if argzahl == 4
                    else f(seite, kuerzel, breite))
    raise SystemExit("unbekannte Ansicht: %s" % kuerzel)


def _lauf(browser, url, breite, saat, kennung):
    """Ein Durchgang ueber alle Ansichten, je mit frischem Kontext."""
    aus = {}
    for kuerzel in ANSICHTEN:
        ctx = EM._ctx(browser, breite)
        seite = ctx.new_page()
        meldungen = []
        seite.on("console", lambda m: meldungen.append(
            "%s: %s" % (m.type, m.text[:200])) if m.type == "error" else None)
        seite.on("pageerror", lambda e: meldungen.append(
            "ABSTURZ: %s" % str(e)[:200]))
        try:
            seite.goto(url, wait_until="domcontentloaded")
            seite.wait_for_timeout(3500)
            if saat is not None:
                EM._saeen(seite, saat, still=True)
            seite.wait_for_timeout(1200)
            try:
                _navi(seite, kuerzel, breite)
            except Exception:          # noqa: BLE001
                pass                    # die Ansicht kann leer unerreichbar sein
            seite.wait_for_timeout(1400)
            g = seite.evaluate(LESEN_JS, VERBOTEN)
            g["konsole"] = meldungen[:6]
            aus[kuerzel] = g
            n = sum(v["anzahl"] for v in g["gefunden"].values())
            print("   %-8s %-13s %5d Zeichen Text, %d verbotene Formen, "
                  "%d Konsolenfehler"
                  % (kennung, kuerzel, g["textlaenge"], n, len(meldungen)))
        except Exception as e:         # noqa: BLE001
            aus[kuerzel] = {"fehler": "%s: %s" % (type(e).__name__,
                                                  str(e)[:120])}
            print("   %-8s %-13s \U0001F534 %s"
                  % (kennung, kuerzel, type(e).__name__))
        finally:
            ctx.close()
    return aus


def main(argv):
    from playwright.sync_api import sync_playwright
    breite = int(argv[0]) if argv else 1440
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port,
                                      os.environ.get("EPK_INDEX", "index.html"))
    bericht = {"breite": breite}

    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # 🔴 SELBSTPROBE ZUERST.
        ctx = EM._ctx(browser, breite)
        seite = ctx.new_page()
        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(3500)
        ohne = seite.evaluate(LESEN_JS, VERBOTEN)["gefunden"]
        seite.evaluate(KOEDER_EIN_JS)
        mit = seite.evaluate(LESEN_JS, VERBOTEN)["gefunden"]
        seite.evaluate(KOEDER_AUS_JS)
        ctx.close()
        fehlt = [f for f in VERBOTEN
                 if mit.get(f, {}).get("anzahl", 0)
                 <= ohne.get(f, {}).get("anzahl", 0)]
        print("Selbstprobe: ohne Koeder %r" % {k: v["anzahl"]
                                               for k, v in ohne.items()})
        print("             mit  Koeder %r" % {k: v["anzahl"]
                                               for k, v in mit.items()})
        if fehlt:
            print("\U0001F534 Der Sucher findet den EINGESETZTEN Koeder nicht "
                  "fuer: %s.\n   Dann meldet er fuer jede Seite der Welt "
                  "„sauber“. NICHT GEMESSEN." % ", ".join(fehlt))
            browser.close()
            return 2
        print("   \U0001F7E2 alle %d Formen werden gefunden.\n" % len(VERBOTEN))

        print("Durchgang 1: LEER (keine Saat)")
        bericht["leer"] = _lauf(browser, url, breite, None, "leer")
        print("\nDurchgang 2: MIT DATEN (Gegenprobe)")
        bericht["voll"] = _lauf(browser, url, breite, SAAT.saat(), "voll")
        browser.close()

    ziel = os.path.join(WURZEL, "docs", "befunde", "LEERZUSTAND.json")
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps(bericht, ensure_ascii=False, indent=1))

    print("\n" + "=" * 62)
    nur_leer = []
    for k, g in sorted(bericht["leer"].items()):
        if g.get("fehler"):
            continue
        v = bericht["voll"].get(k, {})
        for form, d in (g.get("gefunden") or {}).items():
            auch_voll = (v.get("gefunden") or {}).get(form, {}).get("anzahl", 0)
            nur_leer.append((k, form, d["anzahl"], auch_voll,
                             d["umgebung"][:2]))
    if not nur_leer:
        print("\U0001F7E2 Keine verbotene Form in keiner Ansicht - weder "
              "leer noch voll.")
    else:
        print("\U0001F534 %d Stellen mit verbotenen Formen:" % len(nur_leer))
        for k, form, n_leer, n_voll, umg in nur_leer:
            wo = "NUR LEER" if not n_voll else "leer UND voll"
            print("\n   %-13s %-16s %dx (%s)" % (k, form, n_leer, wo))
            for u in umg:
                print("      ...%s..." % u)
    absturz = [(k, g["konsole"]) for k, g in bericht["leer"].items()
               if g.get("konsole")]
    if absturz:
        print("\n\U0001F534 Konsolenfehler im LEEREN Zustand:")
        for k, ms in absturz:
            print("   %s:" % k)
            for m in ms[:3]:
                print("      " + m)
    print("\ngeschrieben:", ziel)
    return 1 if (nur_leer or absturz) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
