# -*- coding: utf-8 -*-
"""Liegt der Dokumente-Reiter eines Projekts OHNE NETZ vor oder ist er leer?

WORUM ES GEHT (offener Punkt 33)
--------------------------------
Der Dokumentexplorer legt seine Listen so ab:

    ODB.save("docs_"+p.id, docs)      und    ODB.load("docs_"+p.id)

Dasselbe fuer "folders_", "fotos_" und "bt_". Diese Namen koennen in STORES
nie stehen, weil sie die Projektkennung tragen. _odbHasStore ist deshalb
falsch, ODB.set/ODB.get warnen und tun NICHTS. Auf der Baustelle ohne Netz war
der Reiter damit immer leer.

Dieses Skript misst das im echten Browser, nicht am Quelltext:

  Runde 1  (mit Netz)   Server antwortet ueber playwright-route mit zwei
                        Dokumenten und einem Ordner -> die Liste steht.
  Runde 1b (mit Netz)   Projekt verlassen und wieder oeffnen.
  Runde 2  (ohne Netz)  Dieselbe Sitzung, dieselbe IndexedDB, aber jede
                        Anfrage an /rest/v1/ wird ABGEBROCHEN. Neu laden,
                        wieder zum Reiter. Was jetzt zu sehen ist, ist genau
                        das, was der Monteur im Keller sieht.
  Runde 2b (ohne Netz)  Und nochmal raus aus dem Projekt und wieder rein -
                        OHNE neu zu laden.
  Runde 3               Ein Dokument hochladen und nachsehen, was es in der
                        IndexedDB kostet (nur mit Groessenangabe, s.u.).

RUNDE 2b IST DIE WICHTIGSTE UND KAM ZULETZT DAZU. Die zweite Fassung des
Umbaus vom 31.08. war in Runde 1, 1b und 2 gruen und fiel erst hier um: ohne
Netz gibt es beim zweiten Aufschlagen keinen Server, der den leeren Erstlauf
des Reiters hinterher wieder wegraeumt. Ein Messgeraet, das ein Projekt nur
EINMAL oeffnet, haette den Umbau durchgewinkt.

Zusaetzlich wird die ECHTE IndexedDB gelesen: welche Speicher es gibt, und ob
eine Transaktion auf "docs_<projekt>" ueberhaupt aufgeht.

BENUTZUNG
---------
    python scripts/doku_offline_messen.py                  # gegen index.html
    python scripts/doku_offline_messen.py index_v927.html  # gegen eine Fassung
    python scripts/doku_offline_messen.py index_v927.html projektCache 300
                                             # dazu Runde 3 mit 300 KiB Datei

Gemessen wird gegen die GENANNTE DATEI im Arbeitsbaum - nicht gegen eine ins
Fenster eingespielte Fassung. Der Unterschied hat am 30.08. einen Umbau vor
dem Gegenteil bewahrt.

VORAUSSETZUNG
-------------
    pip install playwright && playwright install chromium
"""
import json
import os
import sys
import threading

for _strom in (sys.stdout, sys.stderr):
    try:
        _strom.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)

from tab_sweep import DB_NAME  # noqa: E402
from select_wert_messen import KLICK_TAB_JS, TABS_JS  # noqa: E402
from select_breite_messen import (  # noqa: E402
    KARTE_JS, KLICK_PROJ_NAV_JS, PID, PROJ_NAV_JS,
)
from select_breite_messen import ZURUECK_JS as ZURUECK2_JS  # noqa: E402

# ═══ DIE SAAT ═════════════════════════════════════════════════════════════
# EIGENE Zeilen statt der aus select_breite_messen geerbten - und zwar wegen
# eines Fehlalarms im ersten Lauf: der dortige Ordner heisst "Fotos", und
# "Fotos" steht in der Projekt-Navigationsleiste als Knopf. Der Ordner galt
# damit auch OHNE Netz als sichtbar, obwohl von ihm nichts geladen war. Die
# Namen hier sind deshalb so gewaehlt, dass sie in der ganzen App sonst
# nirgends vorkommen koennen.
DOK_ROWS = [
    {"id": "d1", "name": "Bauplan ZZQ1", "category": "plaene",
     "folder_id": "fzz", "note": "", "file_url": "", "file_name": "eg.pdf",
     "file_type": "application/pdf", "file_size": 1234,
     "uploaded_at": "2026-01-02T00:00:00", "kunde_freigabe": 0},
    {"id": "d2", "name": "Abnahme ZZQ2", "category": "baubesprechung",
     "folder_id": "fzz", "note": "", "file_url": "", "file_name": "prot.pdf",
     "file_type": "application/pdf", "file_size": 2345,
     "uploaded_at": "2026-01-03T00:00:00", "kunde_freigabe": 0},
]
ORDNER_ROWS = [
    {"id": "fzz", "name": "Ordner ZZQ3", "color": "#888888", "parent_id": "",
     "created_at": "2026-01-01T00:00:00"},
]

PROJ_NR = "PA241923"   # DR.-GSCHMEIDLERSTRASSE 10, das ist Projekt p4.

NUTZER = {"id": "1", "username": "admin", "name": "Sweep Admin",
          "role": "admin", "rolle": "Geschaeftsfuehrer",
          "monteurId": "", "permissions": [], "perms_override": {}}

INIT = """
try{
  var b=function(s){return btoa(s).replace(/=+$/,'');};
  var jwt=b(JSON.stringify({alg:"HS256",typ:"JWT"}))+"."+
          b(JSON.stringify({sub:"1",role:"authenticated",
                            exp:Math.floor(Date.now()/1000)+86400}))+".sig";
  localStorage.setItem('epkolar_auth',JSON.stringify({at:jwt,rt:"r",exp:Date.now()+86400000}));
  localStorage.setItem('epkolar_user',JSON.stringify(__NUTZER__));
}catch(e){}
""".replace("__NUTZER__", json.dumps(NUTZER))


# Gezaehlt werden die NAMEN der gesaeten Dokumente und des gesaeten Ordners.
# Nicht die Zahl der Zeilen: eine leere Liste hat auch Zeilen (Kopf, Hinweis).
SICHTBAR_JS = r"""(namen) => {
  const txt = document.body.innerText || '';
  const raus = {};
  namen.forEach(n => { raus[n] = txt.indexOf(n) >= 0; });
  return raus;
}"""

# Die App oeffnet die DB selbst; hier wird sie ein zweites Mal geoeffnet - OHNE
# Versionsangabe, damit dieser Lauf niemals selbst ein onupgradeneeded ausloest
# und den Zustand erzeugt, den er messen will.
DB_LESEN_JS = r"""(cfg) => new Promise((res) => {
  const r = indexedDB.open(cfg.db);
  r.onerror = () => res({fehler: 'open: ' + (r.error && r.error.name)});
  r.onsuccess = () => {
    const db = r.result;
    const stores = Array.from(db.objectStoreNames);
    const antwort = {stores: stores, version: db.version};
    // Genau der Griff, den ODB tut - und genau die Stelle, an der er scheitert.
    antwort.hat_docs_store = stores.indexOf('docs_' + cfg.pid) >= 0;
    try { db.transaction('docs_' + cfg.pid, 'readonly'); antwort.tx_docs = 'geht'; }
    catch (e) { antwort.tx_docs = 'wirft: ' + (e && e.name || e); }
    try { db.transaction('projects', 'readonly'); antwort.tx_projects = 'geht'; }
    catch (e) { antwort.tx_projects = 'wirft: ' + (e && e.name || e); }
    if (stores.indexOf(cfg.cache) < 0) { antwort.cache_inhalt = null; res(antwort); return; }
    const rq = db.transaction(cfg.cache, 'readonly')
                 .objectStore(cfg.cache).getAllKeys();
    rq.onsuccess = () => {
      antwort.cache_schluessel = rq.result;
      const rq2 = db.transaction(cfg.cache, 'readonly')
                    .objectStore(cfg.cache).get('docs_' + cfg.pid);
      rq2.onsuccess = () => {
        const w = rq2.result;
        antwort.cache_inhalt = Array.isArray(w) ? w.length : (w === undefined ? -1 : -2);
        // Traegt der Zwischenspeicher base64-Nutzlast? Das ist die Frage aus
        // offenem Punkt 19 eine Etage tiefer.
        let gross = 0;
        (Array.isArray(w) ? w : []).forEach(z => {
          Object.keys(z || {}).forEach(k => {
            const v = z[k];
            if (typeof v === 'string' && v.slice(0, 5) === 'data:') gross += v.length;
          });
        });
        antwort.cache_base64_zeichen = gross;
        antwort.cache_bytes = JSON.stringify(w === undefined ? null : w).length;
        res(antwort);
      };
      rq2.onerror = () => { antwort.cache_inhalt = -3; res(antwort); };
    };
    rq.onerror = () => { antwort.cache_schluessel = null; res(antwort); };
  };
})"""


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


class Netz(object):
    """Der Server. Ab `aus=True` kommt keine Antwort mehr - das ist der Keller."""

    def __init__(self):
        self.aus = False
        self.abgebrochen = 0
        self.beantwortet = 0

    def __call__(self, auftrag):
        if self.aus:
            self.abgebrochen += 1
            try:
                auftrag.abort()
            except Exception:
                pass
            return
        u = auftrag.request.url
        koerper = "[]"
        if "project_documents" in u:
            koerper = json.dumps(DOK_ROWS)
        elif "project_folders" in u:
            koerper = json.dumps(ORDNER_ROWS)
        self.beantwortet += 1
        try:
            auftrag.fulfill(status=200, content_type="application/json",
                            body=koerper)
        except Exception:
            pass


# ═══ DIE DATENMENGE ═══════════════════════════════════════════════════════
# addDoc legt die hochgeladene Datei als vollstaendige base64-data-URL in den
# Zustand (reader.readAsDataURL) - ohne jede Groessengrenze, das ist offener
# Punkt 19. Genau dieser Zustand ist es, den die Speicher-Wirkung in den
# Zwischenspeicher schreiben WUERDE. Hier wird gemessen, wieviel davon
# tatsaechlich in der IndexedDB landet - im Zwischenspeicher UND in der
# syncQueue, die dieselben Bytes ohnehin schon traegt.
MENGE_JS = r"""(cfg) => new Promise((res) => {
  const r = indexedDB.open(cfg.db);
  r.onerror = () => res({fehler: 'open'});
  r.onsuccess = () => {
    const db = r.result;
    const stores = Array.from(db.objectStoreNames);
    const lies = (store, key) => new Promise((ok) => {
      if (stores.indexOf(store) < 0) { ok(null); return; }
      const rq = db.transaction(store, 'readonly').objectStore(store).get(key);
      rq.onsuccess = () => ok(rq.result);
      rq.onerror = () => ok(null);
    });
    Promise.all([lies(cfg.cache, 'docs_' + cfg.pid), lies('syncQueue', 'data')])
      .then(([cache, q]) => {
        const zaehl = (w) => {
          let b64 = 0;
          JSON.stringify(w === undefined ? null : w)
            .replace(/data:[^"]{200,}/g, (m) => { b64 += m.length; return ''; });
          return b64;
        };
        res({
          cache_zeilen: Array.isArray(cache) ? cache.length : -1,
          cache_bytes: JSON.stringify(cache === undefined ? null : cache).length,
          cache_base64: zaehl(cache),
          queue_eintraege: Array.isArray(q) ? q.length : -1,
          queue_bytes: JSON.stringify(q === undefined ? null : q).length,
          queue_base64: zaehl(q)
        });
      });
  };
})"""

# Ein Knopf oder ein verstecktes Feld - die Datei geht direkt an das
# input[type=file] des Reiters. Der Dialog wird vorher aufgeklappt, sonst
# gibt es das Feld noch gar nicht.
HOCHLADEN_AUF_JS = r"""() => {
  const t = e => (e.textContent||'').trim().replace(/\s+/g,' ');
  for (const b of document.querySelectorAll('button')) {
    if (b.closest('.tab-bar')) continue;
    if (/Hochladen|Datei|Upload|\+ Dokument/i.test(t(b)) && !b.disabled) {
      b.click(); return t(b);
    }
  }
  return null;
}"""

DATEIFELDER_JS = "() => document.querySelectorAll('input[type=file]').length"


def _zum_reiter(seite):
    """Startseite -> Projekte -> Projekt PA241923 -> Dokumente."""
    tabs = seite.evaluate(TABS_JS)
    ziel = [i for i, n in enumerate(tabs) if "Projekte" in n]
    if not ziel:
        return "keine Ansicht 'Projekte' (Reiter: %s)" % tabs
    seite.evaluate(KLICK_TAB_JS, ziel[0])
    seite.wait_for_timeout(1200)
    if not seite.evaluate(KARTE_JS, PROJ_NR):
        return "Projektkarte %s nicht gefunden" % PROJ_NR
    seite.wait_for_timeout(1500)
    nav = seite.evaluate(PROJ_NAV_JS)
    name = [n for n in nav if "Dokumente" in n]
    if not name:
        return "kein Knopf 'Dokumente' (Untermasken: %s)" % nav
    seite.evaluate(KLICK_PROJ_NAV_JS, name[0])
    seite.wait_for_timeout(2000)
    return None


NAMEN = [d["name"] for d in DOK_ROWS] + [f["name"] for f in ORDNER_ROWS]


def _lauf(pw, url, cache_store, sichtbar, gross_kb=0,
          zurueck_und_wieder=True):
    netz = Netz()
    b = pw.chromium.launch()
    c = b.new_context(viewport={"width": 1600, "height": 1000})
    c.add_init_script(INIT)
    c.route("**/rest/v1/**", netz)
    warnungen = []
    p = c.new_page()

    def _konsole(m):
        t = m.text
        if "Store missing" in t or "saveProj" in t:
            warnungen.append(t)
    p.on("console", _konsole)
    if sichtbar:
        p.on("pageerror", lambda e: print("   Seitenfehler:", str(e)[:120]))
    p.goto(url, wait_until="domcontentloaded")
    p.wait_for_timeout(5000)

    fehler = _zum_reiter(p)
    if fehler:
        b.close()
        return {"fehler": "Runde 1: " + fehler}
    mit = p.evaluate(SICHTBAR_JS, NAMEN)
    p.wait_for_timeout(1500)   # den Schreibvorgang zu Ende kommen lassen
    db = p.evaluate(DB_LESEN_JS, {"db": DB_NAME, "pid": PID, "cache": cache_store})

    # ═══ RUNDE 1b: DAS PROJEKT VERLASSEN UND WIEDERKOMMEN ═══
    # Das ist keine Kuer, sondern der Alltag: Projekt auf, Reiter durch,
    # zurueck zur Liste, anderes Projekt, wieder her. Beim Wiederkommen
    # haengt sich der Reiter mit einer LEEREN Liste ein - und wenn diese leere
    # Liste in den Zwischenspeicher darf, ist er beim naechsten Start ohne
    # Netz leer. Die erste Fassung dieses Umbaus hatte genau dort ein Loch,
    # und ohne diese Runde waere es nicht aufgefallen: Runde 2 laedt die Seite
    # neu und faengt bei einem sauberen Zustand an.
    if zurueck_und_wieder:
        seite_zurueck = p.evaluate(ZURUECK2_JS)
        p.wait_for_timeout(1200)
        fehler = _zum_reiter(p)
        if fehler:
            b.close()
            return {"fehler": "Runde 1b: " + fehler + " (Zurueck: %s)" % seite_zurueck,
                    "mit_netz": mit, "db": db}
        p.wait_for_timeout(2000)
        if sichtbar:
            print("   Runde 1b: Projekt verlassen und wieder geoeffnet")

    # ═══ UND JETZT DER KELLER ═══
    netz.aus = True
    p.reload(wait_until="domcontentloaded")
    p.wait_for_timeout(5000)
    fehler = _zum_reiter(p)
    if fehler:
        b.close()
        return {"fehler": "Runde 2: " + fehler, "mit_netz": mit, "db": db}
    ohne = p.evaluate(SICHTBAR_JS, NAMEN)
    db2 = p.evaluate(DB_LESEN_JS, {"db": DB_NAME, "pid": PID, "cache": cache_store})

    # ═══ RUNDE 2b: OHNE NETZ ZUM ZWEITEN MAL IN DASSELBE PROJEKT ═══
    # Das ist der Tag auf der Baustelle: kein Empfang, und man geht zwischen
    # Projekt, Liste und Projekt hin und her. Beim zweiten Aufschlagen haengt
    # sich der Reiter wieder mit einer LEEREN Liste ein - und diesmal kommt
    # kein Server, der sie hinterher fuellt. Darf diese leere Liste in den
    # Zwischenspeicher, ist er danach leer, und zwar dauerhaft.
    # Runde 1b sieht das NICHT: dort antwortet der Server noch und raeumt den
    # Schaden im selben Atemzug wieder weg.
    ohne2 = None
    if zurueck_und_wieder:
        p.evaluate(ZURUECK2_JS)
        p.wait_for_timeout(1500)
        fehler = _zum_reiter(p)
        if fehler:
            b.close()
            return {"fehler": "Runde 2b: " + fehler, "mit_netz": mit,
                    "ohne_netz": ohne, "db": db}
        p.wait_for_timeout(2000)
        ohne2 = p.evaluate(SICHTBAR_JS, NAMEN)

    # ═══ RUNDE 3: WAS KOSTET EIN HOCHGELADENES DOKUMENT? ═══
    menge = None
    if gross_kb:
        vorher = p.evaluate(MENGE_JS, {"db": DB_NAME, "pid": PID, "cache": cache_store})
        knopf = p.evaluate(HOCHLADEN_AUF_JS)
        p.wait_for_timeout(800)
        felder = p.evaluate(DATEIFELDER_JS)
        if sichtbar:
            print("   Runde 3: Knopf %r, Dateifelder %s" % (knopf, felder))
        if felder:
            # Der Reiter hat MEHRERE input[type=file] (Foto, Kamera, Dokument).
            # Das erste ist nicht das richtige - im ersten Lauf ging die Datei
            # ins Leere, die Messung meldete "keine Aenderung", und das haette
            # wie ein bestandener Deckel ausgesehen. Deshalb wird jedes Feld
            # probiert, bis der Dateiname im Reiter steht.
            datei = {"name": "grosse_datei_zzq.pdf",
                     "mimeType": "application/pdf",
                     "buffer": b"%PDF-1.4\n" + (b"Z" * (gross_kb * 1024))}
            try:
                for _i in range(felder):
                    p.locator("input[type=file]").nth(_i).set_input_files(datei)
                    p.wait_for_timeout(2500)
                    if p.evaluate("() => (document.body.innerText||'')"
                                  ".indexOf('grosse_datei_zzq') >= 0"):
                        if sichtbar:
                            print("   Runde 3: Feld %d war das richtige" % _i)
                        break
                p.wait_for_timeout(2500)
                if sichtbar:
                    print("   Runde 3: Reiter-Text enthaelt den Namen: %s"
                          % p.evaluate("() => (document.body.innerText||'')"
                                       ".indexOf('grosse_datei_zzq') >= 0"))
            except Exception as e:
                menge = {"fehler": "Datei setzen: " + str(e)[:120]}
        else:
            menge = {"fehler": "kein input[type=file] (Knopf: %s)" % knopf}
        if menge is None:
            nachher = p.evaluate(MENGE_JS, {"db": DB_NAME, "pid": PID, "cache": cache_store})
            menge = {"knopf": knopf, "vorher": vorher, "nachher": nachher,
                     "datei_kb": gross_kb}
    b.close()
    return {"mit_netz": mit, "ohne_netz": ohne, "ohne_netz_2": ohne2,
            "db": db, "db_nachher": db2, "menge": menge,
            "abgebrochen": netz.abgebrochen, "warnungen": warnungen[:12]}


def main(argv):
    datei = argv[1] if len(argv) > 1 else "index.html"
    cache_store = argv[2] if len(argv) > 2 else "projektCache"
    gross_kb = int(argv[3]) if len(argv) > 3 else 0
    if not os.path.exists(os.path.join(WURZEL, datei)):
        print("Datei gibt es nicht:", datei)
        return 2
    port = _server()
    url = "http://127.0.0.1:%d/%s" % (port, datei)
    print("gemessen wird:", datei, "->", url)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        erg = _lauf(pw, url, cache_store, True, gross_kb)

    if erg.get("fehler"):
        print("ABBRUCH:", erg["fehler"])
        for k in ("mit_netz", "db"):
            if k in erg:
                print("  %s: %s" % (k, erg[k]))
        return 1

    print()
    print("  IndexedDB: Fassung %s, %d Speicher"
          % (erg["db"].get("version"), len(erg["db"].get("stores") or [])))
    print("  Speicher 'docs_%s' vorhanden: %s" % (PID, erg["db"].get("hat_docs_store")))
    print("  transaction('docs_%s'): %s" % (PID, erg["db"].get("tx_docs")))
    print("  transaction('projects'): %s   <- Gegenprobe" % erg["db"].get("tx_projects"))
    if erg["db"].get("cache_inhalt") is not None:
        print("  Speicher '%s': Schluessel %s" % (cache_store, erg["db"].get("cache_schluessel")))
        print("     docs_-Eintraege %s, %s Bytes, davon base64 %s Zeichen"
              % (erg["db"].get("cache_inhalt"), erg["db"].get("cache_bytes"),
                 erg["db"].get("cache_base64_zeichen")))
    print()
    z2 = erg.get("ohne_netz_2") or {}
    print("  %-28s %-12s %-12s %s"
          % ("gesucht im Reiter", "MIT Netz", "OHNE Netz", "OHNE, 2. Besuch"))
    for n in NAMEN:
        print("  %-28s %-12s %-12s %s"
              % (n[:28], "sichtbar" if erg["mit_netz"].get(n) else "FEHLT",
                 "sichtbar" if erg["ohne_netz"].get(n) else "FEHLT",
                 ("sichtbar" if z2.get(n) else "FEHLT") if z2 else "-"))
    m = erg.get("menge")
    if m and not m.get("fehler"):
        v, n = m["vorher"], m["nachher"]
        print()
        print("  EIN HOCHGELADENES DOKUMENT VON %d KiB (Runde 3):" % m["datei_kb"])
        print("    %-22s %12s %12s" % ("", "vorher", "nachher"))
        print("    %-22s %12d %12d" % ("Zwischenspeicher Byte", v["cache_bytes"], n["cache_bytes"]))
        print("    %-22s %12d %12d" % ("davon base64", v["cache_base64"], n["cache_base64"]))
        print("    %-22s %12d %12d" % ("syncQueue Byte", v["queue_bytes"], n["queue_bytes"]))
        print("    %-22s %12d %12d" % ("davon base64", v["queue_base64"], n["queue_base64"]))
    elif m:
        print()
        print("  Runde 3 nicht gelaufen:", m.get("fehler"))
    print()
    print("  abgebrochene Serveranfragen in Runde 2:", erg["abgebrochen"])
    if erg["warnungen"]:
        print("  Konsole:")
        for w in erg["warnungen"]:
            print("    ", w[:110])

    # Die Gegenprobe des Messgeraets selbst: waere Runde 1 schon leer, saehe
    # ein kaputter und ein heiler Stand gleich aus und der Lauf maesse nichts.
    if not all(erg["mit_netz"].get(n) for n in NAMEN):
        print()
        print("ABBRUCH: schon MIT Netz steht nicht alles im Reiter. Dann kann")
        print("   dieser Lauf ueber den Zustand OHNE Netz nichts aussagen.")
        return 1
    fehlt = [n for n in NAMEN if not erg["ohne_netz"].get(n)]
    fehlt += [n + " (2. Besuch)" for n in NAMEN if z2 and not z2.get(n)]
    print()
    if fehlt:
        print("BEFUND: ohne Netz fehlt im Reiter: %s" % ", ".join(fehlt))
        return 1
    print("BEFUND: der Reiter steht auch ohne Netz vollstaendig.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
