# -*- coding: utf-8 -*-
"""Was zeigt die Prioritaets-Auswahl bei einem Schein OHNE Prioritaet?

DER VERDACHT (30.08.2026, beim ersten Blick auf die AS-Zeile im Browser)
-----------------------------------------------------------------------
    value: a.prioritaet||"keine"
    ...
    Object.entries(AS_PRIO).filter(([k]) => k!=="keine" || a.prioritaet==="keine")

`AS_PRIO` beginnt mit  keine, aufgeschoben, niedrig, normal, hoch, ...

Traegt ein Schein GAR KEINE Prioritaet, ist `a.prioritaet` undefined:
  * der Wert wird "keine"
  * der Filter wirft "keine" aber HERAUS, denn `undefined === "keine"` ist falsch
  * ein select, dessen value zu keiner Option passt, zeigt die ERSTE Option

Die erste Option ist "aufgeschoben". Ein Schein ohne Prioritaet saehe also aus
wie ein AUFGESCHOBENER - und das ist eine Aussage ueber die Planung, keine
Formalie. Grau eingefaerbt wirkt sie zudem gewollt.

Der Fall ist im Code BEDACHT (v3.9.798: "keine" nur sichtbar, wenn der Schein
ihn noch traegt) - aber nur fuer die wortwoertliche Zeichenkette, nicht fuer
undefined, null oder "".

WARUM ES EINE MESSUNG BRAUCHT
-----------------------------
Dass ein select ohne passende Option die erste zeigt, ist Browserverhalten und
steht in keiner Datei dieses Repos. Behaupten reicht nicht.

Gemessen werden vier Scheine nebeneinander: ohne Feld, null, leerer Text, und
einer mit "normal" als Gegenprobe.
"""
import os
import sys
import threading

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)

from tab_sweep import INIT, DB_NAME, SEED_JS  # noqa: E402

FAELLE = [
    ("ohne Feld", {}),
    ("null", {"prioritaet": None}),
    ("leerer Text", {"prioritaet": ""}),
    ("keine (woertlich)", {"prioritaet": "keine"}),
    ("normal (Gegenprobe)", {"prioritaet": "normal"}),
]

LIES_JS = """() => {
  const zeilen = Array.from(document.querySelectorAll('tr'))
    .filter(r => r.querySelectorAll('select').length >= 3);
  return zeilen.map(r => {
    const nr = (r.querySelector('td') || {}).textContent || '';
    // Die Prioritaets-Auswahl ist die, deren Optionen 'FIXTERMIN' enthalten.
    const sel = Array.from(r.querySelectorAll('select')).find(s =>
      Array.from(s.options).some(o => o.value === 'FIXTERMIN'));
    if (!sel) return {nr: nr.trim(), gefunden: false};
    return {
      nr: nr.trim(),
      gefunden: true,
      wert: sel.value,
      angezeigt: (sel.options[sel.selectedIndex] || {}).text || '(nichts)',
      index: sel.selectedIndex,
      optionen: Array.from(sel.options).map(o => o.value),
    };
  });
}"""


def _server():
    import http.server
    import socketserver
    os.chdir(WURZEL)
    class Still(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = socketserver.TCPServer(("127.0.0.1", 0), Still)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv.server_address[1]


def main():
    from playwright.sync_api import sync_playwright

    scheine = []
    for k, (name, extra) in enumerate(FAELLE, start=1):
        s = {"id": "P%d" % k, "nummer": "AS-%d" % (2000 + k),
             "kundName": name, "arbeitsort": "Krems",
             "scheinstatus": "freigegeben"}
        s.update(extra)
        scheine.append(s)

    port = _server()
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        c = b.new_context(viewport={"width": 1440, "height": 900})
        c.add_init_script(INIT)
        p = c.new_page()
        p.goto("http://127.0.0.1:%d/index.html" % port, wait_until="domcontentloaded")
        p.wait_for_timeout(4000)
        erg = p.evaluate(SEED_JS, {"db": DB_NAME,
                                   "daten": {"arbeitsscheine": scheine,
                                             "monteure": [{"id": "M1", "n": "A",
                                                           "r": "Monteur", "austritt": ""}]}})
        print("gesaet:", erg.get("gelesen"))
        p.reload(wait_until="domcontentloaded")
        p.wait_for_timeout(4000)
        p.get_by_text("Arbeitsscheine", exact=False).first.click()
        p.wait_for_timeout(2500)

        zeilen = p.evaluate(LIES_JS)
        if not zeilen:
            print("KEINE Zeilen gefunden - hier wird nichts behauptet.")
            b.close()
            return 1

        print()
        print("%-14s %-14s %-16s %s" % ("Nummer", "value", "ANGEZEIGT", "Index"))
        for z in zeilen:
            if not z.get("gefunden"):
                print("%-14s (keine Prio-Auswahl in dieser Zeile)" % z["nr"][:13])
                continue
            print("%-14s %-14s %-16s %s"
                  % (z["nr"][:13], repr(z["wert"]), z["angezeigt"], z["index"]))
        erste = next((z for z in zeilen if z.get("gefunden")), None)
        if erste:
            print()
            print("Optionen der Auswahl:", ", ".join(erste["optionen"]))
        b.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
