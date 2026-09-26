# -*- coding: utf-8 -*-
"""Wird am Sync-/Offline-Knopf im Kopf wirklich etwas ABGESCHNITTEN?

DER GEMELDETE BEFUND (B3_STUFEN_4_7.md, B7)
───────────────────────────────────────────
In allen acht Laeufen genau eine Beschnittstelle, immer dieselbe:
`header > div > button`, Inhalt `Offline4` bei 390 px mit scrollWidth 48 gegen
clientWidth 44, und `Offline4Server ❌` bei 1440 px mit 85/81. Die Sonde
schloss auf "wird stumm abgeschnitten, ohne Auslassungspunkte".

WARUM DAS NICHT GESICHERT IST
─────────────────────────────
Dieselbe Sonde meldet fuer diesen Knopf `overflow: visible`. Bei sichtbarem
Ueberlauf wird nichts abgeschnitten - der Inhalt wird AUSSERHALB des Kastens
gezeichnet und ist zu sehen. `text-overflow` greift ueberhaupt nur bei
`overflow: hidden`; die Angabe `clip` sagt hier also nichts. Das Kriterium
scrollWidth > clientWidth findet einen KASTENUEBERLAUF und kann nicht
unterscheiden, ob dabei ein Pixel verloren geht.

Bei den anderen vier Beschnittstellen auf Home ist es umgekehrt eindeutig:
dort steht `overflow: hidden` mit `text-overflow: ellipsis`, und es wird
tatsaechlich gekuerzt (lange Kundennamen).

WAS HIER GEMESSEN WIRD
──────────────────────
Fuer jeden Textknoten IM Knopf das eigene Rechteck (Range.getClientRects) und
die Frage, ob es von einem Vorfahren mit `overflow: hidden` beschnitten wird
oder ueber den Rand des Fensters hinausragt. Also: wird der Text GEZEICHNET
und liegt er im Bild?

Zusaetzlich wird der Kette der Vorfahren nachgegangen, bis der erste mit
`overflow: hidden` kommt - genau der entscheidet, ob ein Ueberlauf sichtbar
bleibt.

DER KOEDER
──────────
In dieselbe Kopfzeile wird ein Knopf eingesetzt, dessen Text sicher
abgeschnitten WIRD (feste Breite, overflow:hidden, langer Text). Findet die
Messung den nicht, sagt sie ueber den echten Knopf nichts.

AUFRUF
──────
    python scripts/b7_syncknopf_messen.py
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import mob_ansicht_messen as M  # noqa: E402

MESS_JS = r"""() => {
  // Der erste Vorfahr, der einen Ueberlauf tatsaechlich beschneidet.
  // Beim Element SELBST anfangen, nicht beim Elternteil. Mein erster Lauf
  // fing beim Elternteil an - dadurch meldete der KOEDER "0 px verloren",
  // obwohl er genau dafuer gebaut ist, sich selbst zu beschneiden
  // (width:40px; overflow:hidden). Ein Werkzeug, das seinen eigenen Koeder
  // nicht findet, sagt ueber den Messgegenstand nichts.
  const beschneider = (el) => {
    let e = el;
    while (e) {
      const cs = getComputedStyle(e);
      if (cs.overflowX === 'hidden' || cs.overflowX === 'clip' ||
          cs.overflowY === 'hidden' || cs.overflowY === 'clip' ||
          cs.overflowX === 'auto' || cs.overflowX === 'scroll') {
        return {tag: e.tagName.toLowerCase(),
                klasse: String(e.className || '').slice(0, 30),
                ox: cs.overflowX, oy: cs.overflowY,
                r: e.getBoundingClientRect()};
      }
      e = e.parentElement;
    }
    return null;
  };

  // Das Rechteck, das der TEXT wirklich einnimmt - nicht das des Kastens.
  const textRechteck = (el) => {
    let l = Infinity, r = -Infinity, o = Infinity, u = -Infinity, n = 0;
    const lauf = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    let k;
    while ((k = lauf.nextNode())) {
      if (!String(k.nodeValue || '').trim()) continue;
      const rg = document.createRange();
      rg.selectNodeContents(k);
      for (const re of rg.getClientRects()) {
        if (re.width <= 0 && re.height <= 0) continue;
        l = Math.min(l, re.left); r = Math.max(r, re.right);
        o = Math.min(o, re.top);  u = Math.max(u, re.bottom); n++;
      }
    }
    return n ? {left: l, right: r, top: o, bottom: u} : null;
  };

  const urteil = (el, name) => {
    const cs = getComputedStyle(el);
    const kr = el.getBoundingClientRect();
    const tr = textRechteck(el);
    const b = beschneider(el);
    let verloren = 0, wo = '-';
    if (tr) {
      // Vom Beschneider abgeschnitten?
      if (b) {
        const ueber = Math.max(0, tr.right - b.r.right) + Math.max(0, b.r.left - tr.left);
        if (ueber > 0.5) { verloren = ueber; wo = b.tag + '.' + b.klasse; }
      }
      // Oder aus dem Fenster heraus?
      const raus = Math.max(0, tr.right - innerWidth) + Math.max(0, 0 - tr.left);
      if (raus > verloren) { verloren = raus; wo = 'Fensterrand'; }
    }
    return {name: name,
            text: String(el.innerText || '').replace(/\s+/g, ' ').slice(0, 40),
            kasten: Math.round(kr.width),
            scrollWidth: el.scrollWidth, clientWidth: el.clientWidth,
            kastenUeberlauf: el.scrollWidth - el.clientWidth,
            eigenOverflow: cs.overflowX,
            textBreite: tr ? Math.round(tr.right - tr.left) : null,
            textRechts: tr ? Math.round(tr.right) : null,
            beschneider: b ? (b.tag + '.' + b.klasse + ' ' + b.ox) : 'KEINER',
            beschneiderRechts: b ? Math.round(b.r.right) : null,
            wirklichVerloren: Math.round(verloren * 10) / 10,
            verlorenAn: wo};
  };

  const aus = [];
  const kopf = document.querySelector('header');
  if (!kopf) return {fehler: 'kein header'};
  [...kopf.querySelectorAll('button')].forEach((b, i) => {
    if (b.scrollWidth - b.clientWidth > 0.5)
      aus.push(urteil(b, 'kopfknopf#' + i));
  });

  // KOEDER: ein Knopf, dessen Text WIRKLICH abgeschnitten wird.
  const kk = document.createElement('button');
  kk.textContent = 'KOEDER ein sehr langer Text der nicht passt';
  kk.style.cssText = 'width:40px;overflow:hidden;display:block;white-space:nowrap;font-size:12px';
  kopf.appendChild(kk);
  const koeder = urteil(kk, 'KOEDER');
  kk.remove();

  return {knoepfe: aus, koeder: koeder, innerWidth: innerWidth};
}"""


ZIEL_JS = """(namen) => {
  const k = [...document.querySelectorAll('button, a, [role="button"]')]
    .filter(b => !b.closest('.bottom-nav'));
  for (const n of namen) {
    const t = k.find(b => (b.innerText || '').trim() === n
                          || (b.getAttribute('aria-label') || '') === n);
    if (t) { t.click(); return n; }
  }
  return null;
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

    ergebnis = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for breite in (390, 1440):
            ctx = browser.new_context(viewport={"width": breite, "height": 880},
                                      is_mobile=breite < 600,
                                      has_touch=breite < 600)
            ctx.add_init_script(M.INIT)
            ctx.add_init_script(
                "try{var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
                "u.role='admin';u.monteurId='M1';"
                "localStorage.setItem('epkolar_user',JSON.stringify(u));}catch(e){}")
            ctx.route("**/rest/v1/**", lambda r: r.abort())
            ctx.route("**/auth/v1/**", lambda r: r.abort())
            seite = ctx.new_page()
            seite.goto(url, wait_until="domcontentloaded")
            seite.wait_for_timeout(4500)
            # Erst in eine Ansicht wechseln. Mein erster Lauf mass die
            # Startansicht und meldete "kein Kopfknopf mit Kastenueberlauf" -
            # der Sync-Knopf existiert dort naemlich noch nicht. Das haette
            # als "behoben" durchgehen koennen.
            seite.evaluate(ZIEL_JS, ["Auswertungen", "Fahrzeuge", "Werkzeuge"])
            seite.wait_for_timeout(2000)
            d = seite.evaluate(MESS_JS)
            ctx.close()
            ergebnis[breite] = d

            print("\n-- %d px" % breite)
            if d.get("fehler"):
                print("   %s" % d["fehler"])
                continue
            k = d["koeder"]
            print("   KOEDER: Text %d px breit, Beschneider %s, WIRKLICH "
                  "verloren %s px an %s"
                  % (k["textBreite"] or 0, k["beschneider"],
                     k["wirklichVerloren"], k["verlorenAn"]))
            if not d["knoepfe"]:
                print("   Kein Kopfknopf mit Kastenueberlauf.")
            for b in d["knoepfe"]:
                print("   %s  %r" % (b["name"], b["text"]))
                print("      Kasten %d px, scrollWidth %d / clientWidth %d "
                      "(Ueberlauf %d), eigenes overflow-x: %s"
                      % (b["kasten"], b["scrollWidth"], b["clientWidth"],
                         b["kastenUeberlauf"], b["eigenOverflow"]))
                print("      Text %s px breit, rechte Kante %s; Beschneider %s "
                      "(rechte Kante %s)"
                      % (b["textBreite"], b["textRechts"], b["beschneider"],
                         b["beschneiderRechts"]))
                print("      WIRKLICH VERLOREN: %s px an %s"
                      % (b["wirklichVerloren"], b["verlorenAn"]))
        browser.close()

    print("\n" + "=" * 68)
    kk = [ergebnis[b]["koeder"] for b in ergebnis if not ergebnis[b].get("fehler")]
    if not kk or not all(k["wirklichVerloren"] > 1 for k in kk):
        print("KOEDER STUMM: die Messung findet nicht einmal einen Text, der")
        print("sicher abgeschnitten wird. Dann sagt sie ueber den Sync-Knopf")
        print("nichts. ABBRUCH.")
        return 1
    print("KOEDER ANGESCHLAGEN in beiden Breiten (Text wirklich beschnitten).")

    # LEERE GRUNDGESAMTHEIT. Hat kein einziger Kopfknopf einen Kastenueberlauf,
    # gibt es hier nichts zu beurteilen - und "kein Textverlust" waere eine
    # Aussage ueber eine leere Menge. Genau dieser Fehler hat in diesem Lauf
    # schon zweimal ein falsches Gruen erzeugt, und mein erster Durchlauf hier
    # hat ihn wieder gemacht: er meldete "die Kopfknoepfe haben einen
    # Kastenueberlauf, aber sichtbar", waehrend die Liste leer war.
    kandidaten = sum(len(ergebnis[b].get("knoepfe", [])) for b in ergebnis)
    if kandidaten == 0:
        print("\nNICHT GEMESSEN. In diesem Aufbau hat KEIN Kopfknopf einen")
        print("Kastenueberlauf - der gemeldete Fall ('Offline4', scrollWidth 48")
        print("gegen clientWidth 44) ist hier gar nicht aufgetreten. Der Knopf")
        print("zeigt einen Zustand samt Ausstehend-Zaehler; ohne genau diesen")
        print("Zustand gibt es den Ueberlauf nicht. Der Koeder belegt, dass die")
        print("Messung einen echten Beschnitt FINDEN wuerde - sie hatte nur")
        print("nichts zu messen. Das ist kein 'behoben' und kein 'kein Befund'.")
        print("Was fehlt: derselbe Zustand, also offline UND vier ausstehende")
        print("Auftraege in der Warteschlange.")
        return 2

    verlust = []
    for breite in sorted(ergebnis):
        d = ergebnis[breite]
        if d.get("fehler"):
            continue
        for b in d["knoepfe"]:
            if b["wirklichVerloren"] > 1:
                verlust.append((breite, b["name"], b["text"],
                                b["wirklichVerloren"], b["verlorenAn"]))
    if verlust:
        print("\nBEFUND BESTAETIGT - hier geht wirklich Text verloren:")
        for v in verlust:
            print("   %d px  %s %r  %s px an %s" % v)
        return 1
    print("\nKEIN TEXTVERLUST. Die Kopfknoepfe haben einen KASTENUEBERLAUF")
    print("(scrollWidth > clientWidth), aber ihr overflow ist sichtbar und kein")
    print("Vorfahr beschneidet an dieser Stelle - der Text wird also vollstaendig")
    print("gezeichnet und liegt im Bild. Das Kriterium scrollWidth > clientWidth")
    print("allein ist damit KEIN Beschnittbefund. Bleibt als Schoenheitsfrage:")
    print("der Inhalt ragt aus seinem Kasten.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
