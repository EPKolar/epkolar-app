# -*- coding: utf-8 -*-
"""Welche zerstoerenden Knoepfe sieht ein MONTEUR, die er nicht sehen sollte?

🔴 WARUM DAS EIN EIGENES GEBIET IST. Die Datenbank hat Zeilenschutz (RLS).
Die Oberflaeche weiss davon nichts von selbst - sie zeigt, was ihr Code
zeigt. Wo beides auseinanderlaeuft, drueckt ein Monteur auf „Loeschen", die
Datenbank weist ihn mit 403 ab, und was er dann sieht, haengt davon ab, ob
jemand den Fehler anzeigt. Im besten Fall eine Meldung, im schlechtesten
nichts.

Gemessen wird die FLAECHE: welche Bedienelemente eine Rolle sieht. Ob die
Datenbank sie erlaubt, kann von hier aus niemand sagen - dafuer braeuchte es
einen Zugang. Das ist die Grenze dieser Messung, und sie steht im Bericht.

🔴 DIE SELBSTPROBE IST HIER DER GANZE PUNKT: wenn der Rollenwechsel gar
nicht greift, sehen alle Laeufe gleich aus, und der Bericht meldet
einträchtig „kein Unterschied" - das waere von einem echten Ergebnis nicht
zu unterscheiden. Deshalb muss sich mindestens EINE Ansicht zwischen `admin`
und `monteur` messbar unterscheiden, sonst bricht der Lauf ab.

Aufruf:  python scripts/rollenflaeche_jagen.py [breite]
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
             "zeit", "planung", "einstell"]

ROLLEN = [
    ("admin", {"role": "admin", "rolle": "Geschäftsführer"}),
    ("monteur", {"role": "monteur", "rolle": "Monteur"}),
]

# Wortstaemme, die eine zerstoerende oder freigebende Handlung anzeigen.
# 🔴 Stamm, nicht ganzes Wort: die Beschriftungen wechseln, die Absicht nicht.
ZERSTOEREND = ["lösch", "entfern", "verwerf", "zurücksetz",
               "storn", "freigeb", "abschliess", "abschließen",
               "genehmig", "bestätig", "archivier", "übertrag"]

KNOEPFE_JS = r"""() => {
  // 🔴 Der WEG gehoert dazu. Der erste Lauf nahm nur die Beschriftung mit,
  //    und "Zeile loeschen" gibt es an DREI Quellstellen - welche gerendert
  //    war, liess sich hinterher nicht mehr sagen. Ein Befund ohne Ort ist
  //    ein halber.
  const weg = e => {
    const t = [];
    let x = e;
    while (x && x.nodeType === 1 && t.length < 6) {
      let s = x.tagName.toLowerCase();
      if (x.id) { t.unshift(s + '#' + x.id); break; }
      const k = (x.className && typeof x.className === 'string')
        ? x.className.trim().split(/\s+/).slice(0, 2).join('.') : '';
      if (k) s += '.' + k;
      t.unshift(s);
      x = x.parentElement;
    }
    return t.join('>');
  };
  const aus = [];
  document.querySelectorAll('button,[role="button"]').forEach(b => {
    const r = b.getBoundingClientRect();
    if (!r.width || !r.height) return;
    const t = ((b.getAttribute('aria-label') || '')
               + ' ' + (b.getAttribute('title') || '')
               + ' ' + (b.innerText || '')).replace(/\s+/g, ' ').trim();
    if (t) aus.push(t.slice(0, 48) + ' │ ' + weg(b));
  });
  return aus;
}"""


def _init(rolle):
    return ("try{var u=JSON.parse(localStorage.getItem('epkolar_user')"
            "||'{}');u.monteurId='M1';u.name='Probe Person';"
            "u.role=%s;u.rolle=%s;"
            "localStorage.setItem('epkolar_user',JSON.stringify(u));}"
            "catch(e){}" % (json.dumps(rolle["role"]),
                            json.dumps(rolle["rolle"])))


def _ctx_rolle(browser, breite, rolle):
    ctx = browser.new_context(viewport={"width": breite, "height": 880},
                              is_mobile=breite < 600, has_touch=breite < 600,
                              color_scheme="dark")
    ctx.add_init_script(M.INIT)
    ctx.add_init_script(_init(rolle))
    ctx.route("**/rest/v1/**", lambda r: r.abort())
    ctx.route("**/auth/v1/**", lambda r: r.abort())
    return ctx


def _navi(seite, kuerzel, breite):
    for modul, name, argzahl in GRUPPEN:
        if kuerzel in getattr(modul, "ANSICHTEN", {}):
            f = getattr(modul, name)
            return (f(seite, kuerzel, breite, []) if argzahl == 4
                    else f(seite, kuerzel, breite))
    raise SystemExit("unbekannte Ansicht: %s" % kuerzel)


def _lauf(browser, url, breite, saat, name, rolle):
    aus = {}
    for kuerzel in ANSICHTEN:
        ctx = _ctx_rolle(browser, breite, rolle)
        seite = ctx.new_page()
        try:
            seite.goto(url, wait_until="domcontentloaded")
            seite.wait_for_timeout(3500)
            EM._saeen(seite, saat, still=True)
            seite.wait_for_timeout(1100)
            try:
                _navi(seite, kuerzel, breite)
            except Exception:          # noqa: BLE001
                pass                    # die Rolle kann die Ansicht sperren
            seite.wait_for_timeout(1300)
            aus[kuerzel] = sorted(set(seite.evaluate(KNOEPFE_JS)))
            print("   %-8s %-12s %3d Bedienelemente"
                  % (name, kuerzel, len(aus[kuerzel])))
        except Exception as e:         # noqa: BLE001
            aus[kuerzel] = []
            print("   %-8s %-12s \U0001F534 %s"
                  % (name, kuerzel, type(e).__name__))
        finally:
            ctx.close()
    return aus


def _zerstoerend(text):
    t = text.lower()
    return [w for w in ZERSTOEREND if w in t]


def main(argv):
    from playwright.sync_api import sync_playwright
    breite = int(argv[0]) if argv else 1440
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port,
                                      os.environ.get("EPK_INDEX", "index.html"))
    saat = SAAT.saat()
    bericht = {"breite": breite, "rollen": {}}

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for name, rolle in ROLLEN:
            print("Rolle %s:" % name)
            bericht["rollen"][name] = _lauf(browser, url, breite, saat,
                                            name, rolle)
        browser.close()

    a = bericht["rollen"]["admin"]
    m = bericht["rollen"]["monteur"]

    # 🔴 SELBSTPROBE: hat der Rollenwechsel ueberhaupt gegriffen?
    unterschiede = {k: (len(a.get(k, [])), len(m.get(k, [])))
                    for k in ANSICHTEN
                    if set(a.get(k, [])) != set(m.get(k, []))}
    print("\nSelbstprobe: %d von %d Ansichten unterscheiden sich zwischen "
          "admin und monteur" % (len(unterschiede), len(ANSICHTEN)))
    for k, (na, nm) in sorted(unterschiede.items()):
        print("   %-12s admin %3d  monteur %3d" % (k, na, nm))
    if not unterschiede:
        print("\U0001F534 KEIN Unterschied zwischen den Rollen. Entweder "
              "greift der Rollenwechsel\n   im Pruefstand nicht, oder die "
              "Oberflaeche kennt keine Rollen. Beides macht\n   den "
              "Vergleich unten wertlos. NICHT GEMESSEN.")
        return 2
    print("   \U0001F7E2 der Rollenwechsel greift.\n")

    print("=" * 62)
    treffer = []
    for k in ANSICHTEN:
        for t in m.get(k, []):
            w = _zerstoerend(t)
            if w:
                nur_monteur = t not in a.get(k, [])
                treffer.append((k, t, w, nur_monteur))
    if not treffer:
        print("\U0001F7E2 Ein Monteur sieht in %d Ansichten KEIN "
              "zerstoerendes oder freigebendes Bedienelement." % len(ANSICHTEN))
    else:
        print("Ein Monteur sieht %d zerstoerende/freigebende Bedienelemente:"
              % len(treffer))
        for k, t, w, nur in sorted(treffer):
            print("   %-12s %-46r %s%s"
                  % (k, t, ",".join(w), "  [sieht der ADMIN NICHT]"
                     if nur else ""))

    ziel = os.path.join(WURZEL, "docs", "befunde", "ROLLENFLAECHE.json")
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps(bericht, ensure_ascii=False, indent=1))
    print("\nGRENZE DIESER MESSUNG: sie sagt, WAS ein Monteur sieht - nicht,"
          "\nob die Datenbank es ihm erlaubt. Dafuer braeuchte es einen "
          "Zugang zur DB.")
    print("geschrieben:", ziel)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
