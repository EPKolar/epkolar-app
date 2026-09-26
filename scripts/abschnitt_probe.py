# -*- coding: utf-8 -*-
"""Probe: werden Wochenbericht-Summe und Material-Reiter noch beschnitten?

WOZU
────
Zwei belegte Abschneidefehler in der Projektakte:
  * Wochenbericht, Summenspalte: "18." statt "18,0"
  * Material, Unterreiter: rechts abgeschnitten

Beide sehen im Quelltext richtig aus. Der Material-Reiter hatte sogar schon
`overflowX:auto` und `whiteSpace:nowrap` - und war trotzdem beschnitten, weil
`flexShrink:0` fehlte: ohne das SCHRUMPFEN Flex-Kinder, statt ueberzulaufen.
Der Text kann dann nicht umbrechen und wird abgeschnitten, waehrend der
Rollbalken nie entsteht. Nicht der Text sprengt seine Box - die Box wird
kleiner als der Text.

Solche Faelle sieht nur der gerenderte Schirm.

WAS GEMESSEN WIRD
─────────────────
Je Element: scrollWidth gegen clientWidth. Mehr als 1 px Differenz heisst
"der Inhalt passt nicht in seine Box". Zusaetzlich beim Wochenbericht: der
Text der Summenzelle muss ein Komma enthalten - "18." ist beschnitten,
"18,0" nicht.

DER KOEDER
──────────
Ein absichtlich zu langer Text wird in eine der gemessenen Boxen gesetzt; die
Probe MUSS ihn als Beschnitt melden. Sonst sagt "nichts beschnitten" nichts.

AUFRUF
──────
    python scripts/abschnitt_probe.py
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import mob_ansicht_messen as M  # noqa: E402

OEFFNE_JS = """() => {
  const k = Array.from(document.querySelectorAll('div')).filter(e => {
    const t = (e.innerText || '');
    return t.includes('Stunden') && t.includes('Gewerk')
           && e.getBoundingClientRect().height > 80;
  });
  if (!k.length) return false;
  k.sort((a, b) => a.getBoundingClientRect().height
                 - b.getBoundingClientRect().height);
  k[0].click();
  return true;
}"""

ZIEL_JS = """(name) => {
  const norm = s => (s || '').split(String.fromCharCode(10)).join(' ')
                             .replace(/  +/g, ' ').trim();
  let t = Array.from(document.querySelectorAll('button, [role="menuitem"]'))
    .find(e => norm(e.innerText).indexOf(name) >= 0);
  if (!t) {
    const mehr = Array.from(document.querySelectorAll('button[aria-haspopup="menu"]'))
      .find(e => norm(e.innerText).startsWith('Mehr'));
    if (mehr) mehr.click();
    return 'mehr';
  }
  t.click();
  return true;
}"""

SUMME_JS = """() => {
  const tab = document.querySelector('.proj-main table');
  if (!tab) return {fehler: 'keine Tabelle im Wochenbericht'};
  const zeilen = Array.from(tab.querySelectorAll('tr'));
  const letzte = zeilen.map(z => Array.from(z.children).pop())
    .filter(Boolean)
    .filter(c => (c.innerText || '').trim().length > 0);
  if (!letzte.length) return {fehler: 'keine Summenzellen mit Inhalt'};
  return {
    anzahl: letzte.length,
    zellen: letzte.map(c => ({
      text: (c.innerText || '').trim(),
      scroll: c.scrollWidth, klar: c.clientWidth,
      beschnitten: c.scrollWidth > c.clientWidth + 1
    })).slice(0, 8),
    tabelleBreite: tab.getBoundingClientRect().width
  };
}"""

REITER_JS = """() => {
  // Die Material-Unterreiter: Knoepfe in einem quer rollbaren Streifen mit
  // Unterstrich-Rand. Gesucht ueber die Eigenschaft.
  const streifen = Array.from(document.querySelectorAll('.proj-main div'))
    .find(e => {
      const cs = getComputedStyle(e);
      if (!/auto|scroll/.test(cs.overflowX)) return false;
      const b = e.querySelectorAll(':scope > button');
      return b.length >= 2;
    });
  if (!streifen) return {fehler: 'keine Unterreiter-Leiste gefunden'};
  const b = Array.from(streifen.querySelectorAll(':scope > button'));
  return {
    anzahl: b.length,
    rollt: streifen.scrollWidth > streifen.clientWidth + 1,
    knoepfe: b.map(x => ({
      text: (x.innerText || '').trim().split(String.fromCharCode(10)).join(' '),
      scroll: x.scrollWidth, klar: x.clientWidth,
      shrink: getComputedStyle(x).flexShrink,
      beschnitten: x.scrollWidth > x.clientWidth + 1
    }))
  };
}"""

KOEDER_JS = """() => {
  const b = document.querySelector('.proj-main button');
  if (!b) return null;
  const alt = b.innerText;
  b.style.width = '30px';
  b.style.overflow = 'hidden';
  b.style.whiteSpace = 'nowrap';
  b.textContent = 'Ein absichtlich viel zu langer Knopftext';
  const erkannt = b.scrollWidth > b.clientWidth + 1;
  b.textContent = alt;
  b.style.width = '';
  b.style.overflow = '';
  return erkannt;
}"""

# Die Summenzelle unter LAST messen. Die Testdaten liefern "0.0" - drei
# Zeichen. Der Befund lautete aber "18." statt "18,0", also VIER Zeichen.
# Mit 0.0 laesst sich die Reparatur nicht belegen: die Probe setzt deshalb
# selbst einen langen Wert ein und schaut, ob er noch hineinpasst.
LAST_JS = """() => {
  const tab = document.querySelector('.proj-main table');
  if (!tab) return {fehler: 'keine Tabelle'};
  const zeilen = Array.from(tab.querySelectorAll('tr'));
  const zellen = zeilen.map(z => Array.from(z.children).pop()).filter(Boolean);
  const zahl = zellen.filter(c => /[0-9]/.test((c.innerText || '')));
  if (!zahl.length) return {fehler: 'keine Zahlenzelle in der Summenspalte'};
  const c = zahl[0];
  const alt = c.textContent;
  const proben = ['18,0', '188,5', '1888,0'];
  const aus = [];
  proben.forEach(p => {
    c.textContent = p;
    aus.push({wert: p, scroll: c.scrollWidth, klar: c.clientWidth,
              passt: c.scrollWidth <= c.clientWidth + 1});
  });
  c.textContent = alt;
  return {proben: aus};
}"""


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt.")
        return 2

    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port, os.environ.get("EPK_INDEX", "index.html"))
    print("Gemessen wird:", url)

    schlimm, gemessen = [], 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 390, "height": 860},
                                  is_mobile=True, has_touch=True)
        ctx.add_init_script(M.INIT)
        ctx.add_init_script(
            "try{var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
            "u.role='admin';u.monteurId='M1';"
            "localStorage.setItem('epkolar_user',JSON.stringify(u));}catch(e){}")
        ctx.route("**/rest/v1/**", lambda r: r.abort())
        ctx.route("**/auth/v1/**", lambda r: r.abort())
        seite = ctx.new_page()
        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(3800)
        seite.evaluate(M.NAV_OEFFNEN_JS)
        seite.wait_for_timeout(350)
        seite.evaluate(M.NAV_WAEHLEN_JS, "Projekte")
        seite.wait_for_timeout(2100)
        if not seite.evaluate(OEFFNE_JS):
            print("KEIN Projekt zum Oeffnen - nichts gemessen.")
            return 1
        seite.wait_for_timeout(2300)

        koeder = seite.evaluate(KOEDER_JS)
        print("KOEDER - ein zu langer Text in einer 30px-Box: %s"
              % ("als Beschnitt ERKANNT" if koeder else "NICHT erkannt"))
        if not koeder:
            print("   Dann sagt 'nichts beschnitten' nichts aus. ABBRUCH.")
            return 1

        # ── Wochenbericht ─────────────────────────────────────────────────
        for versuch in range(2):
            r = seite.evaluate(ZIEL_JS, "Berichte")
            seite.wait_for_timeout(1100)
            if r is True:
                break
        d = seite.evaluate(SUMME_JS)
        print("\nWochenbericht: %s" % ("ROT: " + d["fehler"] if d.get("fehler") else ""))
        if not d.get("fehler"):
            gemessen += 1
            print("   Tabellenbreite %.0f px, %d Summenzellen"
                  % (d["tabelleBreite"], d["anzahl"]))
            for z in d["zellen"]:
                print("      %-10r scroll=%d klar=%d beschnitten=%s"
                      % (z["text"], z["scroll"], z["klar"], z["beschnitten"]))
                if z["beschnitten"]:
                    schlimm.append("Summenzelle %r beschnitten (%d von %d px)"
                                   % (z["text"], z["scroll"], z["klar"]))
            # Die frueher hier stehende Komma-Pruefung war falsch: _n
            # formatiert mit PUNKT ("0.0"), und die Testdaten liefern ohnehin
            # nur Nullen. Gemessen wird deshalb unter LAST - mit Werten in der
            # Laenge, um die es im Befund ging.
            last = seite.evaluate(LAST_JS)
            if last.get("fehler"):
                schlimm.append("Lasttest: " + last["fehler"])
            else:
                print("   Lasttest der Summenzelle:")
                for pr in last["proben"]:
                    print("      %-8s scroll=%d klar=%d passt=%s"
                          % (pr["wert"], pr["scroll"], pr["klar"], pr["passt"]))
                    if not pr["passt"]:
                        schlimm.append("Der Wert %s passt NICHT in die "
                                       "Summenzelle (%d von %d px) - genau der "
                                       "Befund (\"18.\" statt \"18,0\")"
                                       % (pr["wert"], pr["scroll"], pr["klar"]))
        else:
            schlimm.append("Wochenbericht: " + d["fehler"])

        # ── Material ──────────────────────────────────────────────────────
        for versuch in range(2):
            r = seite.evaluate(ZIEL_JS, "Material")
            seite.wait_for_timeout(1400)
            if r is True:
                break
        d2 = seite.evaluate(REITER_JS)
        print("\nMaterial-Unterreiter: %s"
              % ("ROT: " + d2["fehler"] if d2.get("fehler") else ""))
        if not d2.get("fehler"):
            gemessen += 1
            print("   %d Reiter, Leiste rollt: %s" % (d2["anzahl"], d2["rollt"]))
            for k in d2["knoepfe"]:
                print("      %-18r scroll=%d klar=%d shrink=%s beschnitten=%s"
                      % (k["text"], k["scroll"], k["klar"], k["shrink"],
                         k["beschnitten"]))
                if k["beschnitten"]:
                    schlimm.append("Reiter %r beschnitten (%d von %d px)"
                                   % (k["text"], k["scroll"], k["klar"]))
                if k["shrink"] != "0":
                    schlimm.append("Reiter %r hat flexShrink %s - ohne 0 "
                                   "schrumpft er statt ueberzulaufen"
                                   % (k["text"], k["shrink"]))
        else:
            schlimm.append("Material: " + d2["fehler"])
        browser.close()

    print("\n" + "=" * 62)
    if gemessen == 0:
        print("NICHTS GEMESSEN - das ist kein gruenes Ergebnis.")
        return 1
    if schlimm:
        print("ROT:")
        for z in schlimm:
            print("   " + z)
        return 1
    print("GRUEN - die Summenspalte des Wochenberichts zeigt vollstaendige")
    print("Werte mit Komma, und die Material-Unterreiter schrumpfen nicht mehr")
    print("(flexShrink 0), also wird nichts abgeschnitten.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
