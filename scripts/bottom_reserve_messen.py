# -*- coding: utf-8 -*-
"""Misst, WAS die Fussleiste verdeckt - und WELCHER Kasten dafuer rollt.

WOZU
────
Befund: "nach Scrollen bis ganz unten stehen die Aktionen der letzten Karte
28 px UNTER der Leiste, dauerhaft unerreichbar". Die Reparatur ist eine
Endreserve am rollenden Kasten - aber WELCHER Kasten rollt? Die Datei traegt
bereits an einer Stelle `padding: 0 0 calc(80px + env(safe-area-inset-bottom))`
fuer Mobil. Wenn trotzdem etwas verdeckt ist, sitzt die Reserve am falschen
Kasten. Das laesst sich nicht lesen, nur messen.

WAS GEMESSEN WIRD
─────────────────
Je Ansicht, nach dem Rollen bis ganz unten:
  * die Fussleiste: Oberkante und Hoehe (GEMESSEN, nicht aus dem CSS gelesen -
    `.bottom-nav` hat gar keine Hoehenangabe, die 58 px sind ein Messwert)
  * jedes bedienbare Element, dessen MITTE unter der Leistenoberkante liegt
  * der tatsaechlich rollende Kasten (scrollHeight > clientHeight)

DER KOEDER
──────────
Vor der eigentlichen Messung wird ein Knopf fest an den unteren Rand gesetzt.
Er MUSS als verdeckt gemeldet werden. Tut er das nicht, sieht das Werkzeug
nichts - und ein leerer Fundhaufen waere dann von "nichts verdeckt" nicht zu
unterscheiden. Genau dieser Fehler ist mir am 24.09. unterlaufen: ich meldete
"alle Flaechen wechseln", gemessen worden war nichts.

Ausserdem: eine Ansicht, in der KEIN einziges bedienbares Element gefunden
wurde, gilt als NICHT GEMESSEN und wird als solche gemeldet, nicht als
"nichts verdeckt".

AUFRUF
──────
    python scripts/bottom_reserve_messen.py
    python scripts/bottom_reserve_messen.py --nachher   (nach der Reparatur)
"""
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import mob_ansicht_messen as M  # noqa: E402  (Server, INIT, Navigation)

ANSICHTEN = ["Projekte", "Arbeitsscheine", "Planung", "Werkzeuge",
             "Abwesenheiten", "Fahrzeuge"]

MESS_JS = """() => {
  const bar = document.querySelector('.bottom-nav');
  if (!bar) return {fehler: 'keine .bottom-nav'};
  const br = bar.getBoundingClientRect();
  if (br.height < 1) return {fehler: 'bottom-nav ist nicht sichtbar'};

  // DIE DECKKANTE IST NICHT DIE LEISTENOBERKANTE.
  // In der Leiste sitzt ein Streifen mit `position:absolute; top:-24px`
  // (Sync-/Offline-Warnung). Der ragt UEBER die Leiste hinaus und verdeckt
  // Inhalt, aber das Rechteck der Leiste enthaelt ihn nicht - ein Kind, das
  // aus seinem Elter herausragt, zaehlt in getBoundingClientRect() des
  // Elters nicht mit. Wer nur die Leiste misst, sieht diese Verdeckung nie.
  // Gesucht wird deshalb die oberste Kante ALLER Dinge, die unten kleben.
  let deckTop = br.top;
  const decker = [];
  document.querySelectorAll('*').forEach(e => {
    const cs = getComputedStyle(e);
    if (cs.position !== 'fixed' && cs.position !== 'absolute') return;
    const r = e.getBoundingClientRect();
    if (r.height < 4 || r.width < 40) return;
    if (r.bottom < window.innerHeight - 90) return;   // klebt nicht unten
    if (r.top > window.innerHeight - 4) return;       // ausserhalb
    if (cs.visibility === 'hidden' || cs.display === 'none') return;
    if (parseFloat(cs.opacity || '1') < 0.05) return;
    decker.push({cls: (e.className||'').toString().slice(0,40),
                 top: Math.round(r.top), h: Math.round(r.height),
                 pos: cs.position});
    if (r.top < deckTop) deckTop = r.top;
  });


  // Der Kasten, der tatsaechlich rollt. Nicht geraten - gesucht.
  const roller = [];
  document.querySelectorAll('*').forEach(e => {
    if (e.scrollHeight > e.clientHeight + 8 && e.clientHeight > 100) {
      const cs = getComputedStyle(e);
      if (/auto|scroll/.test(cs.overflowY)) {
        const r = e.getBoundingClientRect();
        roller.push({tag: e.tagName, cls: (e.className||'').toString().slice(0,60),
                     h: Math.round(r.height), scrollH: e.scrollHeight,
                     padB: cs.paddingBottom});
      }
    }
  });
  const docRollt = document.documentElement.scrollHeight >
                   document.documentElement.clientHeight + 8;

  const wahl = 'button, a[href], input, select, textarea, [role="button"], [onclick]';
  const alle = Array.from(document.querySelectorAll(wahl)).filter(e => {
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    return r.width > 4 && r.height > 4 && cs.visibility !== 'hidden'
           && cs.display !== 'none' && r.top < window.innerHeight && r.bottom > 0;
  });

  const verdeckt = alle.filter(e => {
    if (bar.contains(e)) return false;              // die Leiste selbst zaehlt nicht
    const r = e.getBoundingClientRect();
    return (r.top + r.height / 2) > deckTop;         // Mitte unter der DECKKANTE
  }).map(e => {
    const r = e.getBoundingClientRect();
    return {
      tag: e.tagName,
      txt: (e.innerText || e.value || e.getAttribute('aria-label') || '').trim().slice(0, 34),
      y: Math.round(r.top),
      h: Math.round(r.height),
      tief: Math.round(r.top + r.height / 2 - deckTop)
    };
  });

  return {barTop: Math.round(br.top), barHoehe: Math.round(br.height),
          deckTop: Math.round(deckTop), decker: decker,
          fensterH: window.innerHeight, bedienbar: alle.length,
          verdeckt: verdeckt, docRollt: docRollt, roller: roller.slice(0, 6)};
}"""

KOEDER_JS = """() => {
  const b = document.createElement('button');
  b.id = '__koeder__'; b.textContent = 'KOEDER';
  b.style.cssText = 'position:fixed;left:8px;bottom:6px;width:80px;height:30px;z-index:5';
  document.body.appendChild(b);
  return true;
}"""

KOEDER_WEG_JS = """() => {
  const b = document.getElementById('__koeder__');
  if (b) b.remove();
  return true;
}"""


def main(argv):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt.  pip install playwright && playwright install chromium")
        return 2

    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port, os.environ.get("EPK_INDEX", "index.html"))
    print("Gemessen wird:", url)
    print("Geraet: 390x844, is_mobile, has_touch\n")

    EXTRA = ("try{ var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
             " u.role=\"admin\"; u.monteurId=\"M1\"; u.name=\"Gerhard Steinbichler\";"
             " u.rolle=\"Monteur\";"
             " localStorage.setItem('epkolar_user',JSON.stringify(u)); }catch(e){}")

    gemessen, verdeckt_gesamt, koeder_ok = 0, 0, False
    zeilen = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 390, "height": 844},
                                  device_scale_factor=1, is_mobile=True,
                                  has_touch=True)
        ctx.add_init_script(M.INIT)
        ctx.add_init_script(EXTRA)
        ctx.route("**/rest/v1/**", lambda r: r.abort())
        ctx.route("**/auth/v1/**", lambda r: r.abort())
        seite = ctx.new_page()
        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(4000)

        # ── Der Koeder zuerst ──────────────────────────────────────────────
        seite.evaluate(KOEDER_JS)
        probe = seite.evaluate(MESS_JS)
        if probe.get("fehler"):
            print("KOEDER unmoeglich:", probe["fehler"])
            print("Ohne sichtbare Fussleiste ist keine Aussage moeglich.")
            return 1
        koeder_ok = any(v["txt"] == "KOEDER" for v in probe["verdeckt"])
        seite.evaluate(KOEDER_WEG_JS)
        print("KOEDER: ein Knopf fest am unteren Rand wird %s"
              % ("ERKANNT - das Werkzeug sieht etwas." if koeder_ok
                 else "NICHT erkannt. ABBRUCH."))
        if not koeder_ok:
            return 1
        print("Leiste: Oberkante y=%d, Hoehe %d px (gemessen, nicht aus dem CSS)\n"
              % (probe["barTop"], probe["barHoehe"]))

        # ── Die Ansichten ──────────────────────────────────────────────────
        for name in ANSICHTEN:
            seite.evaluate(M.NAV_OEFFNEN_JS)
            seite.wait_for_timeout(400)
            ok = seite.evaluate(M.NAV_WAEHLEN_JS, name)
            seite.wait_for_timeout(2200)
            if not ok:
                zeilen.append((name, None, "nicht erreichbar"))
                continue
            # bis ganz nach unten rollen
            seite.evaluate("()=>{window.scrollTo(0, document.body.scrollHeight);"
                           "document.querySelectorAll('*').forEach(e=>{"
                           "if(e.scrollHeight>e.clientHeight+8)e.scrollTop=e.scrollHeight;});}")
            seite.wait_for_timeout(800)
            d = seite.evaluate(MESS_JS)
            if d.get("fehler") or d.get("bedienbar", 0) == 0:
                zeilen.append((name, None, d.get("fehler") or "0 bedienbare Elemente"))
                continue
            gemessen += 1
            verdeckt_gesamt += len(d["verdeckt"])
            zeilen.append((name, d, None))

        browser.close()

    # ── Urteil ─────────────────────────────────────────────────────────────
    print("=" * 72)
    for name, d, fehler in zeilen:
        if d is None:
            print("%-16s NICHT GEMESSEN - %s" % (name, fehler))
            continue
        print("%-16s %3d bedienbar | %2d verdeckt | Leiste y=%d h=%d | doc rollt %s"
              % (name, d["bedienbar"], len(d["verdeckt"]), d["barTop"],
                 d["barHoehe"], d["docRollt"]))
        for v in d["verdeckt"][:6]:
            print("        %-34r y=%-4d h=%-3d  %d px unter der Kante"
                  % (v["txt"], v["y"], v["h"], v["tief"]))
        for r in d["roller"][:3]:
            print("        roller: %s .%s h=%d scrollH=%d padB=%s"
                  % (r["tag"], r["cls"][:40], r["h"], r["scrollH"], r["padB"]))
    print("=" * 72)

    if gemessen == 0:
        print("KEINE EINZIGE ANSICHT GEMESSEN. Das ist kein gruenes Ergebnis,")
        print("sondern eine ausgefallene Messung.")
        return 1
    print("%d Ansichten gemessen, %d verdeckte Bedienelemente insgesamt."
          % (gemessen, verdeckt_gesamt))
    return 0 if verdeckt_gesamt == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
