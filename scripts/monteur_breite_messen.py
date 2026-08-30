# -*- coding: utf-8 -*-
"""Passt der Monteursname in die Spalte? Gemessen, nicht geschaetzt.

DER VERDACHT (30.08.2026, aus dem ersten Bild der AS-Zeile am Rechner-Schirm)
-----------------------------------------------------------------------------
Die Saat trug "Testmonteur A" und "Testmonteur B". Im Bild stand in BEIDEN
Zeilen nur "Testmonteur" - das unterscheidende Zeichen war weg. Das Auswahlfeld
traegt `maxWidth:90` (das Sachbearbeiter-Feld `maxWidth:80`).

WARUM DAS MEHR IST ALS EIN SCHOENHEITSFEHLER
--------------------------------------------
Der Monteur ist eines der ZWEI Felder, die v3.9.918 bewusst "laut" gelassen hat
- weil das Dispo-Brett Termin und Monteur in EINEM Aufruf schreibt und der Code
damit WER+WANN als einen Vorgang kennt. Ein Feld, das man nicht lesen kann,
laut zu lassen, waere die falsche Haelfte der Arbeit.

WAS GEMESSEN WIRD
-----------------
Nicht "sieht abgeschnitten aus", sondern `scrollWidth > clientWidth` am echten
Element - das ist die Frage, ob der Inhalt in seinen Kasten passt. Dazu die
Zahl der Zeichen, die tatsaechlich sichtbar bleiben.

Gepruefte Namen sind echte oesterreichische Namensformen unterschiedlicher
Laenge, nicht "Test A"/"Test B" - eine Messung mit lauter kurzen Faellen ist
gruen und nutzlos.
"""
import os
import sys
import threading

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)

from tab_sweep import INIT, DB_NAME, SEED_JS  # noqa: E402

NAMEN = [
    "Ali",
    "Franz Huber",
    "Michael Hofbauer",
    "Sebastian Guenther",
    "Alexander Steinberger",
    "Maximilian Gruber-Wallner",
]

# ERSTER VERSUCH MASS DAS FALSCHE FELD und meldete sauber '0 von 6
# abgeschnitten'. Der Selektor suchte ein select mit einem Leerzeichen in
# irgendeiner Option - das trifft auch das STATUS-Feld ('in bearbeitung').
# Eine Entwarnung aus der falschen Spalte ist schlimmer als keine Messung.
# Jetzt wird ueber die gesaeten Namen gesucht: nur das Feld, das sie
# wirklich anbietet, ist das Monteur-Feld.
MESS_JS = """(namen) => {
  const zeilen = Array.from(document.querySelectorAll('tr'))
    .filter(r => r.querySelectorAll('select').length >= 3);
  const aus = [];
  for (const r of zeilen) {
    const sel = Array.from(r.querySelectorAll('select')).find(s =>
      Array.from(s.options).some(o => namen.indexOf((o.text || '').trim()) >= 0));
    if (!sel) continue;
    const cs = getComputedStyle(sel);
    const gewaehlt = (sel.options[sel.selectedIndex] || {}).text || '';
    /* ZWEITER FEHLVERSUCH: scrollWidth > clientWidth ist bei einem select
       IMMER falsch - ein select laeuft nicht ueber, es schneidet. Die Zahlen
       waren fuer jeden Namen gleich (88 = 88), auch fuer einen mit 25
       Zeichen, und die Ausgabe meldete brav 'passt: ja'. Zwei saubere,
       falsche Entwarnungen hintereinander aus demselben Messgeraet.
       Richtig ist: die NATUERLICHE Textbreite mit der echten Schrift des
       Feldes ausmessen und gegen den verfuegbaren Platz halten. Der Pfeil
       des Auswahlfeldes braucht rund 14 px, die kann der Text nicht nutzen. */
    const mess = document.createElement('canvas').getContext('2d');
    mess.font = cs.fontWeight + ' ' + cs.fontSize + ' ' + cs.fontFamily;
    const textbreite = mess.measureText(gewaehlt).width;
    const platz = sel.clientWidth
                - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight) - 14;
    aus.push({
      name: gewaehlt,
      zeichen: gewaehlt.length,
      kastenbreite: Math.round(sel.clientWidth),
      platz: Math.round(platz),
      inhaltsbreite: Math.round(textbreite),
      maxWidth: cs.maxWidth,
      passt: textbreite <= platz + 0.5,
      titel: sel.getAttribute('title') || '',
    });
  }
  return aus;
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

    monteure = [{"id": "M%d" % k, "n": n, "r": "Monteur", "austritt": ""}
                for k, n in enumerate(NAMEN, start=1)]
    scheine = [{"id": "S%d" % k, "nummer": "AS-%d" % (3000 + k),
                "kundName": "Kunde %d" % k, "arbeitsort": "Krems",
                "scheinstatus": "freigegeben", "prioritaet": "normal",
                "monteur": "M%d" % k}
               for k in range(1, len(NAMEN) + 1)]

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
                                             "monteure": monteure}})
        print("gesaet:", erg.get("gelesen"))
        p.reload(wait_until="domcontentloaded")
        p.wait_for_timeout(4000)
        p.get_by_text("Arbeitsscheine", exact=False).first.click()
        p.wait_for_timeout(2500)

        zeilen = p.evaluate(MESS_JS, NAMEN)
        b.close()

    if not zeilen:
        print("KEIN Monteur-Feld gefunden - hier wird nichts behauptet.")
        return 1

    print()
    print("%-28s %-8s %-7s %-8s %s"
          % ("Name", "Zeichen", "Platz", "braucht", "passt"))
    zu_eng = 0
    for z in zeilen:
        if not z["passt"]:
            zu_eng += 1
        print("%-28s %-8d %-7d %-8d %s"
              % (z["name"][:27], z["zeichen"], z["platz"],
                 z["inhaltsbreite"], "ja" if z["passt"] else "NEIN"))
    print()
    print("Abgeschnitten (gerechnet): %d von %d" % (zu_eng, len(zeilen)))
    ohne = [z for z in zeilen if not z["titel"]]
    print("Ohne Titel (Name waere unwiederbringlich): %d von %d"
          % (len(ohne), len(zeilen)))
    stimmt = [z for z in zeilen if z["titel"] == z["name"]]
    print("Titel nennt den vollen Namen: %d von %d" % (len(stimmt), len(zeilen)))
    if zeilen:
        print("maxWidth des Feldes:", zeilen[0]["maxWidth"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
