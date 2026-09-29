# -*- coding: utf-8 -*-
"""Steht ein AUSGETRETENER Mitarbeiter noch auf der Kiosk-Wochenplantafel?

🔴 DER MANGEL (Frage 27, gemessen am 28.09., gefixt erst jetzt). `WeekPlan`
prueft den Austritt an vier Stellen ueber `_wpMaSichtbarAmTag(m, isoTag)`.
`WochenplanTafel` - die Tafel am Wandbildschirm - prueft ihn an KEINER:

    const maName = id => { const m = monteure.find(x=>x.id===id);
                           return m ? (m.n||'') : ''; };

Kein Tag, keine Pruefung. Ein ausgetretener Mitarbeiter steht damit weiter in
allen sechs Tagesspalten - und zwar auf dem Bildschirm, den die halbe Firma
sieht.

WARUM EIN QUELLTEXT-RIEGEL DAS NICHT ENTSCHEIDET. Dass `_wpMaSichtbarAmTag`
im Bauteil vorkommt, ist Anwesenheit. Gemessen wird hier die WIRKUNG: die
Tafel wird mit zwei erfundenen Mitarbeitern gerendert - einem aktiven und
einem, der vorige Woche ausgetreten ist - und dann wird im gerenderten Text
nachgesehen, wer dasteht.

🔴 SELBSTPROBE, ohne die der Lauf nichts belegt: der AKTIVE Mitarbeiter MUSS
erscheinen. Tut er das nicht, hat der Aufbau nicht gerendert, und die
Abwesenheit des Ausgetretenen waere von „es wurde gar nichts gezeichnet"
nicht zu unterscheiden.

🔴 UND EINE ZWEITE, die leicht vergessen wird: ein Mitarbeiter, der ERST IN
ZUKUNFT austritt, muss diese Woche noch dastehen. Ein Riegel, der nur
„Ausgetretene weg" prueft, waere auch bei „alle weg" gruen.
"""
import io
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
WURZEL = os.path.dirname(HIER)

import mob_ansicht_messen as M           # noqa: E402

PROBE_JS = r"""(cfg) => {
  const T = (typeof WochenplanTafel === 'function') ? WochenplanTafel
          : (window.WochenplanTafel || null);
  if (typeof T !== 'function') return {fehler: 'WochenplanTafel nicht erreichbar'};
  if (!window.React || !window.ReactDOM) return {fehler: 'React fehlt'};

  const topf = document.createElement('div');
  topf.style.position = 'fixed';
  topf.style.left = '-10000px';
  topf.style.width = '1920px';
  document.body.appendChild(topf);
  try {
    const el = window.React.createElement(T, {
      wpHistory: cfg.wpHistory, monteure: cfg.monteure,
      fahrzeuge: [], abs: [], onLogout: function(){}
    });
    const wurzel = window.ReactDOM.createRoot
      ? window.ReactDOM.createRoot(topf) : null;
    if (wurzel) wurzel.render(el);
    else window.ReactDOM.render(el, topf);
    return {gestartet: true, id: (topf.id = '__tafelprobe')};
  } catch (e) {
    topf.remove();
    return {fehler: String(e && e.message || e)};
  }
}"""

LESEN_JS = r"""() => {
  const t = document.getElementById('__tafelprobe');
  if (!t) return {fehler: 'Probetopf weg'};
  const text = (t.innerText || '').replace(/\s+/g, ' ');
  return {text: text.slice(0, 1200), laenge: text.length};
}"""

AUFRAEUMEN_JS = r"""() => {
  const t = document.getElementById('__tafelprobe');
  if (t) t.remove();
  return true;
}"""


def _saat():
    """Zwei erfundene Mitarbeiter und eine Wochenplanzeile, die beide nennt.

    Die Namen sind absichtlich unverwechselbar: ein Name, der auch sonst in
    der App vorkaeme, waere im gerenderten Text nicht von einem Zufallstreffer
    zu unterscheiden.
    """
    import datetime
    heute = datetime.date.today()
    montag = heute - datetime.timedelta(days=heute.weekday())
    vorige_woche = (montag - datetime.timedelta(days=3)).isoformat()
    naechstes_jahr = (heute + datetime.timedelta(days=400)).isoformat()
    iso = heute.isocalendar()
    monteure = [
        {"id": "PROBE_AKTIV", "n": "Zzaktiv Probemann", "r": "Monteur"},
        {"id": "PROBE_WEG", "n": "Zzweg Probemann", "r": "Monteur",
         "austritt": vorige_woche},
        {"id": "PROBE_SPAETER", "n": "Zzspaeter Probemann", "r": "Monteur",
         "austritt": naechstes_jahr},
    ]
    tage = ["Mo", "Di", "Mi", "Do", "Fr", "Sa"]
    z = {}
    for t in tage:
        z[t] = {"ma": ["PROBE_AKTIV", "PROBE_WEG", "PROBE_SPAETER"], "fz": []}
    zeile = {"id": "PROBEZEILE", "bvh": "PROBE-BAUSTELLE", "bem": "",
             "z": z, "_sortOrder": 0}
    return {"monteure": monteure,
            "wpHistory": {"%d-%d" % (iso[0], iso[1]): [zeile],
                          str(iso[1]): [zeile]},
            "kw": iso[1], "jahr": iso[0]}


def main(argv):
    from playwright.sync_api import sync_playwright
    cfg = _saat()
    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port,
                                      os.environ.get("EPK_INDEX", "index.html"))
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
        ctx.add_init_script(M.INIT)
        ctx.route("**/rest/v1/**", lambda r: r.abort())
        ctx.route("**/auth/v1/**", lambda r: r.abort())
        seite = ctx.new_page()
        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(5000)
        start = seite.evaluate(PROBE_JS, cfg)
        if start.get("fehler"):
            print("\U0001F534 NICHT GEMESSEN: %s" % start["fehler"])
            ctx.close()
            browser.close()
            return 2
        seite.wait_for_timeout(1500)
        gelesen = seite.evaluate(LESEN_JS)
        seite.evaluate(AUFRAEUMEN_JS)
        ctx.close()
        browser.close()

    if gelesen.get("fehler"):
        print("\U0001F534 NICHT GEMESSEN: %s" % gelesen["fehler"])
        return 2
    text = gelesen["text"]
    aktiv = "Zzaktiv" in text
    weg = "Zzweg" in text
    spaeter = "Zzspaeter" in text
    print("KW %d/%d, Tafel gerendert (%d Zeichen Text)"
          % (cfg["kw"], cfg["jahr"], gelesen["laenge"]))
    print("   aktiv   (kein Austritt)        : %s"
          % ("steht da" if aktiv else "\U0001F534 FEHLT"))
    print("   spaeter (Austritt in 400 Tagen): %s"
          % ("steht da" if spaeter else "\U0001F534 FEHLT"))
    print("   WEG     (Austritt vorige Woche): %s"
          % ("\U0001F534 STEHT NOCH DA" if weg else "weg"))

    if not aktiv:
        print("\n\U0001F534 Die Selbstprobe schlaegt fehl: schon der AKTIVE "
              "Mitarbeiter steht nicht\n   auf der Tafel. Dann hat der "
              "Aufbau nichts gezeichnet, und die Abwesenheit\n   des "
              "Ausgetretenen belegt NICHTS.")
        print("\n   Gerenderter Text: %r" % text[:400])
        return 2
    if not spaeter:
        print("\n\U0001F534 Ein Mitarbeiter, der ERST IN 400 TAGEN austritt, "
              "fehlt schon jetzt.\n   Die Pruefung ist dann nicht zu eng, "
              "sondern falsch.")
        return 1
    if weg:
        print("\n\U0001F534 BEFUND: der vorige Woche Ausgetretene steht auf "
              "der Wandtafel -\n   in allen sechs Tagesspalten. `maName` "
              "kennt den Tag nicht und fragt\n   `_wpMaSichtbarAmTag` nicht.")
        return 1
    print("\n\U0001F7E2 Die Tafel zeigt den Ausgetretenen nicht mehr, und die "
          "beiden anderen\n   stehen weiterhin da.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
