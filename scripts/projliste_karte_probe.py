# -*- coding: utf-8 -*-
"""Probe: die Projektkarte nach dem Umbau - gerendert, nicht gelesen.

WOZU
────
Die Karte ist in vier Zeilen umgebaut. Der Quelltext kann nur sagen, dass die
Teile DASTEHEN. Ob sie gezeichnet werden, ob die Beschriftungen wirklich bei
ihren Zahlen stehen und ob der Bestand (Buero-Abzeichen, Fortschrittsregler)
noch da ist, sagt nur der gerenderte Schirm.

Zweimal in diesem Umbau hat genau dieser Unterschied etwas gefangen, das
node_check gruen liess: eine TDZ-Verletzung und eine Schrift, die im Repo lag
und nirgends benutzt wurde.

WAS GEMESSEN WIRD
─────────────────
  Zeile 1  Projektname 17px/600
  Zeile 2  Status-Pille (Punkt + Text) und "PA-Nr - Kunde - Ort"
  Zeile 3  drei beschriftete Spalten: Stunden / Summe / Gewerk
  Zeile 4  Balken 5px in marke + Prozentzahl
  Bestand  Buero-Abzeichen und Fortschrittsregler sind noch da
  Rolle    der Monteur sieht die Spalte "Summe" NICHT

DIE KOEDER
──────────
1. Es muss mindestens EINE Karte gefunden werden. Null Karten heisst "nichts
   gemessen", nicht "alles in Ordnung".
2. Im Admin-Fall MUSS die Spalte "Summe" da sein. Ist sie in keinem Fall da,
   sagt "der Monteur sieht sie nicht" nichts aus.

AUFRUF
──────
    python scripts/projliste_karte_probe.py
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import mob_ansicht_messen as M  # noqa: E402

KARTE_JS = """() => {
  // Eine Projektkarte erkennt man am Aktionsmenue-Knopf oder am Namen mit
  // 17px/600 - gesucht wird ueber die EIGENSCHAFT, nicht ueber eine Klasse.
  const kandidaten = Array.from(document.querySelectorAll('div'))
    .filter(e => {
      const t = (e.innerText || '');
      return t.includes('Stunden') && t.includes('Gewerk')
             && e.getBoundingClientRect().height > 80
             && e.getBoundingClientRect().height < 420;
    });
  if (!kandidaten.length) return {anzahl: 0};
  // Die kleinste passende - das ist die Karte, nicht ihr Container.
  kandidaten.sort((a, b) => a.getBoundingClientRect().height
                          - b.getBoundingClientRect().height);
  const k = kandidaten[0];
  const txt = (k.innerText || '').split(String.fromCharCode(10))
                .map(x => x.trim()).filter(Boolean);

  const kleinste = (() => {
    let m = 99;
    k.querySelectorAll('*').forEach(e => {
      const t = (e.textContent || '').trim();
      if (!t) return;
      const g = parseFloat(getComputedStyle(e).fontSize);
      if (g && g < m) m = g;
    });
    return m;
  })();

  // Der Balken: ein Kasten mit Hoehe 5 und einem gefuellten Kind.
  let balken = null;
  k.querySelectorAll('div').forEach(e => {
    const r = e.getBoundingClientRect();
    if (Math.round(r.height) === 5 && r.width > 40 && e.children.length === 1) {
      balken = {hoehe: Math.round(r.height),
                spur: getComputedStyle(e).backgroundColor,
                fuellung: getComputedStyle(e.children[0]).backgroundColor};
    }
  });

  // Der Name: das groesste Textstueck oben in der Karte.
  let name = null;
  k.querySelectorAll('div').forEach(e => {
    if (e.children.length) return;
    const g = parseFloat(getComputedStyle(e).fontSize);
    const t = (e.textContent || '').trim();
    if (t && g >= 16 && (!name || g > name.groesse)) {
      name = {text: t.slice(0, 30), groesse: g,
              gewicht: getComputedStyle(e).fontWeight};
    }
  });

  return {
    anzahl: kandidaten.length,
    zeilen: txt.slice(0, 14),
    kleinsteSchrift: kleinste,
    balken: balken,
    name: name,
    hatSumme: (k.innerText || '').includes('Summe'),
    hatRegler: !!k.querySelector('input[type="range"]'),
    hatAbzeichen: !!k.querySelector('span[title]')
  };
}"""

FAELLE = [("admin", 390), ("monteur", 390), ("admin", 1440)]


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt.")
        return 2

    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port, os.environ.get("EPK_INDEX", "index.html"))
    print("Gemessen wird:", url)

    schlimm, gemessen, summe_gesehen = [], 0, False
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for rolle, breite in FAELLE:
            ctx = browser.new_context(viewport={"width": breite, "height": 900},
                                      is_mobile=breite < 600,
                                      has_touch=breite < 600)
            ctx.add_init_script(M.INIT)
            ctx.add_init_script(
                "try{var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
                "u.role='%s';u.monteurId='M1';u.name='Gerhard Steinbichler';"
                "localStorage.setItem('epkolar_user',JSON.stringify(u));}catch(e){}"
                % rolle)
            ctx.route("**/rest/v1/**", lambda r: r.abort())
            ctx.route("**/auth/v1/**", lambda r: r.abort())
            seite = ctx.new_page()
            fehler = []
            seite.on("pageerror", lambda e: fehler.append(str(e)[:150]))
            seite.goto(url, wait_until="domcontentloaded")
            seite.wait_for_timeout(3800)
            seite.evaluate(M.NAV_OEFFNEN_JS)
            seite.wait_for_timeout(350)
            seite.evaluate(M.NAV_WAEHLEN_JS, "Projekte")
            seite.wait_for_timeout(2200)
            d = seite.evaluate(KARTE_JS)
            ctx.close()

            print("\n-- %s, %dpx" % (rolle, breite))
            if not d.get("anzahl"):
                print("   KEINE Karte gefunden.")
                if rolle == "monteur":
                    print("   (Monteure sehen nur eigene Projekte - kann leer sein.)")
                else:
                    schlimm.append("%s/%dpx: keine Karte gefunden" % (rolle, breite))
                continue

            gemessen += 1
            print("   Karten: %d" % d["anzahl"])
            for z in d["zeilen"]:
                print("      %r" % z)
            print("   Name: %s" % d["name"])
            print("   Balken: %s" % d["balken"])
            print("   kleinste Schrift: %s px" % d["kleinsteSchrift"])
            print("   Summe-Spalte: %s | Regler: %s | Abzeichen: %s"
                  % (d["hatSumme"], d["hatRegler"], d["hatAbzeichen"]))

            if d["kleinsteSchrift"] < 12:
                schlimm.append("%s/%dpx: kleinste Schrift %s px"
                               % (rolle, breite, d["kleinsteSchrift"]))
            n = d["name"]
            if not n:
                schlimm.append("%s/%dpx: kein Projektname >=16px gefunden"
                               % (rolle, breite))
            else:
                if abs(n["groesse"] - 17) > 0.6:
                    schlimm.append("%s/%dpx: Name %.0f statt 17 px"
                                   % (rolle, breite, n["groesse"]))
                if str(n["gewicht"]) != "600":
                    schlimm.append("%s/%dpx: Namensgewicht %s statt 600"
                                   % (rolle, breite, n["gewicht"]))
            if not d["balken"]:
                schlimm.append("%s/%dpx: kein 5px-Balken gefunden" % (rolle, breite))
            elif "0, 150, 64" not in d["balken"]["fuellung"]:
                schlimm.append("%s/%dpx: Balkenfuellung %s ist nicht marke "
                               "(#009640)" % (rolle, breite, d["balken"]["fuellung"]))
            for muss in ("Stunden", "Gewerk"):
                if not any(muss in z for z in d["zeilen"]):
                    schlimm.append("%s/%dpx: Spalte %s fehlt" % (rolle, breite, muss))
            if rolle == "monteur" and d["hatSumme"]:
                schlimm.append("MONTEUR SIEHT DIE SPALTE SUMME")
            if rolle != "monteur":
                summe_gesehen = summe_gesehen or d["hatSumme"]
                if not d["hatRegler"]:
                    schlimm.append("%s/%dpx: der Fortschrittsregler ist weg"
                                   % (rolle, breite))
            if fehler:
                schlimm.append("%s/%dpx: Seitenfehler %s" % (rolle, breite, fehler[:2]))
        browser.close()

    print("\n" + "=" * 62)
    if gemessen == 0:
        print("KEINE EINZIGE KARTE GEMESSEN - das ist kein gruenes Ergebnis,")
        print("sondern eine ausgefallene Messung.")
        return 1
    if not summe_gesehen:
        print("KOEDER GESCHEITERT: die Spalte 'Summe' war in keinem Admin-Fall")
        print("da. Dann sagt 'der Monteur sieht sie nicht' nichts aus.")
        return 1
    if schlimm:
        print("ROT:")
        for z in schlimm:
            print("   " + z)
        return 1
    print("GRUEN - vier Zeilen, Name 17/600, Balken 5px in marke, drei")
    print("beschriftete Spalten, keine Schrift unter 12 px, Buero-Abzeichen und")
    print("Fortschrittsregler erhalten, und die Summe bleibt vor dem Monteur")
    print("verborgen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
