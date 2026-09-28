# -*- coding: utf-8 -*-
"""Die BERECHNETE Schriftgroesse, nicht die geschriebene.

🔴 WARUM ES DIESES WERKZEUG GIBT
`tests/test_css_boden_12px_v966.py` liest den Quelltext. Das reicht nicht, und
zwar in BEIDE Richtungen - beides am 28.09.2026 gemessen:

  * Zu WENIG: was inline auf 12 px steht, kann der Browser auf 10 px
    ausrechnen, wenn eine Regel mit `!important` daruebersteht. Genau so war
    die Arbeitsscheinliste nach v3.9.965 noch voller 10-px-Texte, waehrend ihr
    Quelltext NULL Werte unter 12 px fuehrte.
  * Zu VIEL: drei der neun in v3.9.966 gehobenen Regeln treffen ueberhaupt
    kein Bauteil. `.ber-table` kommt als Klasse nirgends vor, `.badge` nur in
    Druck-HTML mit eigenem Stilblock, und beide Arme des Sync-Banner-Musters
    gehen ins Leere. Der Quelltextriegel ist an ihnen gruen - und war es auch,
    als sie noch 11 px trugen.

Dieses Werkzeug fragt den gerenderten Baum: `getComputedStyle(el).fontSize`.
Es schreibt sein Ergebnis samt der VERSION, an der gemessen wurde, nach
`docs/befunde/WIRKUNG_SCHRIFT.json`. Der Riegel
`tests/test_wirkung_frisch_v968.py` geht rot, sobald die Datei aelter ist als
der Code - damit eine Kur nicht gruen gemeldet werden kann, deren Wirkung nie
nachgemessen wurde.

Aufruf:
    python scripts/schriftgroesse_wirkung.py            # die Standardauswahl
    python scripts/schriftgroesse_wirkung.py as_liste fahrzeuge
"""
import io
import json
import os
import re
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

GRUPPEN = [("4-7", B, "_navigieren", 3),
           ("8-11", S, "_navigieren8", 4),
           ("12-15", B12, "_navigieren12", 4)]

# Die Auswahl ist klein und benannt: dieses Werkzeug soll in Minuten laufen,
# nicht in einer Viertelstunde. Der volle Lauf ueber 22 Ansichten steht in
# `echtmengen_messen.py`.
STANDARD = ["as_liste", "fahrzeuge", "planung", "home"]
BREITEN = [390, 1440]

# 🔴 Gemessen wird die BERECHNETE Groesse. Zusaetzlich wird je Fundstelle
# festgehalten, was INLINE dransteht - nur so ist der Unterschied sichtbar,
# um den es geht.
# 🔴 DER KOEDER DER MESSUNG SELBST. Bis v3.9.971 galt als Beleg, dass der
# Melder etwas GEFUNDEN hat - die App-Huelle trug ja in jeder Ansicht Stellen
# unter 12 px. Mit v3.9.972 sind es NULL, und damit war der Beleg weg, obwohl
# der Melder einwandfrei arbeitet. Ein Nachweis, der vom Fortbestehen des
# Mangels lebt, wird bei der naechsten Kur entweder rot oder blind.
# Der Melder beweist seine Empfindlichkeit jetzt SELBST: ein eingesetztes
# 9-px-Element muss gefunden und danach restlos entfernt werden.
KOEDER_JS = r"""() => {
  const d = document.createElement('div');
  d.id = '_koeder_schrift';
  d.textContent = 'Koeder';
  d.style.fontSize = '9px';
  document.body.appendChild(d);
  return true;
}"""

KOEDER_WEG_JS = r"""() => {
  const d = document.getElementById('_koeder_schrift');
  if (d) d.remove();
  return !document.getElementById('_koeder_schrift');
}"""

JS = r"""() => {
  const aus = [];
  for (const el of document.querySelectorAll('*')) {
    if (el.children.length) continue;
    const t = (el.innerText || '').trim();
    if (!t) continue;
    const berechnet = parseFloat(getComputedStyle(el).fontSize);
    if (!(berechnet < 12)) continue;
    const st = el.getAttribute('style') || '';
    const m = st.match(/font-size:\s*([^;]+)/);
    aus.push({px: berechnet, inline: m ? m[1].trim() : null,
              tag: el.tagName.toLowerCase(), text: t.slice(0, 26)});
  }
  const abweichung = aus.filter(x => x.inline
      && parseFloat(x.inline) >= 12 && x.px < 12);
  return {anzahl: aus.length, stellen: aus.slice(0, 40),
          uebersteuert: abweichung.length,
          uebersteuert_beispiele: abweichung.slice(0, 8)};
}"""


def _gruppe(kuerzel):
    for name, modul, navi, argzahl in GRUPPEN:
        if kuerzel in getattr(modul, "ANSICHTEN", {}):
            return modul, navi, argzahl
    return None, None, None


def messen(kuerzel_liste):
    from playwright.sync_api import sync_playwright
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port,
                                      os.environ.get("EPK_INDEX", "index.html"))
    saat = SAAT.saat()
    aufnahmen = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for kuerzel in kuerzel_liste:
            modul, navi, argzahl = _gruppe(kuerzel)
            if modul is None:
                print("   \U0001F534 unbekannte Ansicht: %s" % kuerzel)
                continue
            for breite in BREITEN:
                ctx = EM._ctx(browser, breite)
                seite = ctx.new_page()
                try:
                    seite.goto(url, wait_until="domcontentloaded")
                    seite.wait_for_timeout(3800)
                    EM._saeen(seite, saat, still=True)
                    f = getattr(modul, navi)
                    (f(seite, kuerzel, breite, []) if argzahl == 4
                     else f(seite, kuerzel, breite))
                    seite.wait_for_timeout(1600)
                    # 🔴 Erst die Selbstprobe: ein eingesetztes 9-px-Element
                    # MUSS gefunden werden. Ohne sie waere eine Null nicht von
                    # einem blinden Melder zu unterscheiden.
                    seite.evaluate(KOEDER_JS)
                    mit = seite.evaluate(JS)
                    seite.evaluate(KOEDER_WEG_JS)
                    erg = seite.evaluate(JS)
                    erg["koeder_gefunden"] = any(
                        x.get("text") == "Koeder" and x.get("px") == 9
                        for x in (mit.get("stellen") or []))
                    erg["koeder_restlos_weg"] = not any(
                        x.get("text") == "Koeder"
                        for x in (erg.get("stellen") or []))
                finally:
                    ctx.close()
                erg.update({"kuerzel": kuerzel, "breite": breite})
                aufnahmen.append(erg)
                print("  %-12s %5d px   unter 12 px: %3d   uebersteuert: %d"
                      "   Koeder: %s"
                      % (kuerzel, breite, erg["anzahl"], erg["uebersteuert"],
                         "gefunden+weg" if (erg["koeder_gefunden"]
                                            and erg["koeder_restlos_weg"])
                         else "🔴 ROT"))
        browser.close()
    return aufnahmen


def version():
    t = io.open(os.path.join(WURZEL, "index.html"),
                encoding="utf-8", newline="").read(200000)
    m = re.search(r'APP_VERSION\s*=\s*"([\d.]+)', t)
    return m.group(1) if m else "unbekannt"


def fingerabdruck():
    """Ein Abdruck der SCHRIFTQUELLEN, nicht der ganzen Datei.

    🔴 Die Frische-Klinke haengt absichtlich NICHT an der Versionsnummer.
    Sonst muesste nach jeder unbeteiligten Aenderung ein Browserlauf von
    Minuten gefahren werden, und ein Riegel, der die Kette messbar bremst,
    wird irgendwann uebersprungen - ein uebersprungener Riegel meldet gruen,
    ohne zu messen.

    Der Abdruck deckt genau das ab, was die berechnete Schriftgroesse
    veraendern kann: alle CSS-Quellen und jede Inline-Schriftangabe.
    """
    import hashlib
    sys.path.insert(0, os.path.join(WURZEL, "tests"))
    import importlib.util
    sp = importlib.util.spec_from_file_location(
        "_cssriegel", os.path.join(WURZEL, "tests",
                                   "test_css_boden_12px_v966.py"))
    mod = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(mod)
    text = io.open(os.path.join(WURZEL, "index.html"),
                   encoding="utf-8", newline="").read()
    css = mod.stilbloecke(text)
    inline = re.findall(r"fontSize\s*:\s*[^,}]{1,40}", text)
    h = hashlib.md5()
    h.update(css.encode("utf-8"))
    h.update(("\n".join(inline)).encode("utf-8"))
    return {"md5": h.hexdigest(), "css_zeichen": len(css),
            "inline_angaben": len(inline)}


def main(argv):
    ziel = os.path.join(WURZEL, "docs", "befunde", "WIRKUNG_SCHRIFT.json")
    ansichten = argv or STANDARD
    v = version()
    print("Wirkungsmessung an v%s, Ansichten: %s"
          % (v, ", ".join(ansichten)))
    a = messen(ansichten)
    if not a:
        print("\U0001F534 Keine Aufnahme zustande gekommen - KEINE Datei "
              "geschrieben.")
        return 2
    erg = {"version": v,
           "gemessen_am": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "abdruck": fingerabdruck(),
           "breiten": BREITEN,
           "aufnahmen": a,
           "summe_unter_12px": sum(x["anzahl"] for x in a),
           "summe_uebersteuert": sum(x["uebersteuert"] for x in a)}
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps(erg, ensure_ascii=False, indent=1))
    print("\nSumme unter 12 px: %d | davon uebersteuert (inline >= 12, "
          "berechnet < 12): %d"
          % (erg["summe_unter_12px"], erg["summe_uebersteuert"]))
    print("geschrieben:", ziel)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
