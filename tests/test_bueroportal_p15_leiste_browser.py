# -*- coding: utf-8 -*-
"""Paket 15 Nachbau (GF 24.11.2026): Buero-Portal Mitarbeiter-Monat im ECHTEN Browser (Chromium, Playwright).

Offline-Sitzung wie tests/test_dispo_mobil_browser.py (Schein-JWT + epkolar_user im localStorage, /auth/v1 abgebrochen,
/rest/v1 aus erfundenen Testdaten beantwortet, JEDE schreibende Anfrage abgebrochen und mitgeschrieben). Uhr: 24.11.2026,
der Kopf steht damit auf Oktober 2026.

Gemessen wird:
  * Exporte: jeder Abschnitt (Stunden, Zulagen, Stempelzeiten) hat genau EINE Leiste "Exporte" mit allen Knoepfen.
  * Jeder Exportweg liefert dieselbe Datei wie vorher: gleiche Knopf-Beschriftung, gleicher Dateiname, gleicher Inhalt
    (Excel/HTML byte-gleich, PDF ohne Erstell-Zeitstempel/ID gleich, Druck = window.print). Vergleich gegen den Stand
    VOR dem Nachbau (bb45370 = Paket 15 erster Teil, Erzeuger byte-gleich zu 37d4d59).
  * Leerzustand: Abschnitte ohne Daten fuer die Person zeigen denselben Text "Keine Eintraege".
  * Zulagen und Stempelzeiten folgen dem Kopf-Monat: im Mitarbeiter-Monat keine eigenen Monats-Pfeile/Datumsfelder.
Gegenprobe: EPK_P15_INDEX=<Datei> laesst die Seite aus einer anderen index.html laufen (z. B. git show 37d4d59:index.html).
"""
import functools
import http.server
import json
import os
import re
import socketserver
import subprocess
import threading
import urllib.parse

import pytest

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIT = os.environ.get("EPK_P15_GIT", WURZEL)
VORHER = "803a6ce"  # Stapel-Stand direkt vor Paket 15 (3.9.1117); vorher bb45370 = verworfener alter Zweig
UHR = "2026-11-24T10:00:00"

sync_api = pytest.importorskip("playwright.sync_api")

WORKERS = [{"id": "t1", "name": "Anna Testmonteur", "role": "Monteur", "eintritt": "2020-03-01", "austritt": None, "active": True},
           {"id": "t2", "name": "Bert Ohnedaten", "role": "Monteur", "eintritt": "2021-01-01", "austritt": None, "active": True},
           {"id": "t3", "name": "Cora Buero", "role": "Backoffice", "eintritt": "2019-01-01", "austritt": None, "active": True}]
PROJ = [{"id": "p1", "nr": "PA100", "name": "Testbaustelle Krems", "kunde": "Testkunde", "status": "aktiv", "type": "projekt"}]


def _te():
    out = []
    for i, tag in enumerate(["2026-09-28", "2026-09-30", "2026-10-01", "2026-10-02", "2026-10-06", "2026-10-07", "2026-10-14", "2026-10-21"]):
        out.append({"id": "e%d" % i, "worker_id": "t1", "project_id": "p1", "date": tag, "hours": 8.5 if i % 2 else 7.75,
                    "von": "07:00", "bis": "16:00", "taetigkeit": "Montage %d" % i, "gewerk": "elektro", "pause": 60, "bemerkung": ""})
    return out


def _stempel():
    out = []
    for i, tag in enumerate(["2026-10-01", "2026-10-02", "2026-10-06", "2026-10-07", "2026-10-14"]):
        out.append({"id": "s%da" % i, "worker_id": "t1", "ts": tag + "T05:00:00Z", "direction": "kommen", "device": "kiosk"})
        out.append({"id": "s%db" % i, "worker_id": "t1", "ts": tag + "T14:30:00Z", "direction": "gehen", "device": "kiosk"})
    return out


DATEN = {
    "workers": WORKERS, "projects": PROJ, "time_entries": _te(), "stempel_log": _stempel(),
    "entfernungszulage_tage": [{"worker_id": "t1", "datum": "2026-10-06", "aktiv": True, "stufe": "mittel"}],
    "absences": [{"id": "a1", "worker_id": "t1", "worker_name": "Anna Testmonteur", "type": "urlaub", "from_date": "2026-10-20",
                  "to_date": "2026-10-20", "von": "2026-10-20", "bis": "2026-10-20", "status": "genehmigt", "tage": 1}],
    "users": [{"id": "1", "name": "Test Buero", "username": "admin", "email": "t@x", "role": "admin", "active": True,
               "monteur_id": None, "permissions": [], "perms_override": {}, "locked": False}],
}

INIT = """
try{
  var b=function(s){return btoa(s).replace(/=+$/,'');};
  var jwt=b(JSON.stringify({alg:"HS256",typ:"JWT"}))+"."+b(JSON.stringify({sub:"1",role:"authenticated",exp:Math.floor(Date.now()/1000)+86400}))+".sig";
  localStorage.setItem('epkolar_auth',JSON.stringify({at:jwt,rt:"r",exp:Date.now()+86400000}));
  localStorage.setItem('epkolar_user',JSON.stringify({id:"1",username:"admin",name:"Test Buero",role:"admin",rolle:"Geschaeftsfuehrer",permissions:[],perms_override:{}}));
  localStorage.setItem('epk_bueroportal_neu_tab','abschluss');
}catch(e){}
window.__exp=[];
(function(){
  var oc=URL.createObjectURL;
  URL.createObjectURL=function(bl){try{if(bl&&bl.text){var rec={typ:bl.type};window.__exp.push(rec);bl.text().then(function(t){rec.text=t;});}}catch(e){}return oc.apply(this,arguments);};
  var merk=function(a){if(a&&a.download)window.__exp.push({datei:a.download});};
  var ac=HTMLAnchorElement.prototype.click;HTMLAnchorElement.prototype.click=function(){merk(this);if(this.download)return;return ac.apply(this,arguments);};
  var ad=HTMLAnchorElement.prototype.dispatchEvent;HTMLAnchorElement.prototype.dispatchEvent=function(ev){if(this.download&&ev&&ev.type==='click'){merk(this);return true;}return ad.apply(this,arguments);};
  window.print=function(){window.__exp.push({druck:1});};
})();
"""


def _cmp(v, op, arg):
    if v is None:
        return False
    sv = str(v)
    return {"eq": sv == arg, "gte": sv >= arg, "gt": sv > arg, "lte": sv <= arg, "lt": sv < arg}.get(op, True)


def _filtern(rows, query):
    out = rows
    for k, val in urllib.parse.parse_qsl(query, keep_blank_values=True):
        if k in ("select", "order", "limit", "offset", "or", "and"):
            continue
        m = re.match(r"^(eq|gte|gt|lte|lt)\.(.*)$", val)
        if m:
            out = [r for r in out if _cmp(r.get(k), m.group(1), m.group(2))]
    return out


class _Still(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


@pytest.fixture(scope="module")
def server():
    srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(_Still, directory=WURZEL))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield "http://127.0.0.1:%d/index.html" % srv.server_address[1]
    srv.shutdown()


@pytest.fixture(scope="module")
def browser():
    with sync_api.sync_playwright() as pw:
        try:
            br = pw.chromium.launch()
        except Exception as e:  # pragma: no cover
            pytest.skip("Chromium nicht startbar: %s" % e)
        yield br
        br.close()


def _neu_index():
    p = os.environ.get("EPK_P15_INDEX")
    with open(p or os.path.join(WURZEL, "index.html"), "rb") as f:
        return f.read()


def _vorher_index():
    r = subprocess.run(["git", "-C", GIT, "show", VORHER + ":index.html"], capture_output=True)
    if r.returncode != 0:
        pytest.skip("Vorher-Stand nicht im Repo")
    return r.stdout


def _seite(browser, url, body, breite=1366, hoehe=900):
    log = {"schreib": [], "fehler": []}

    def weiter(route):
        req = route.request
        u = req.url
        if u.startswith("http://127.0.0.1"):
            return route.continue_()
        if "/rest/v1/" in u:
            teil = u.split("/rest/v1/")[-1]
            tab = teil.split("?")[0]
            if req.method == "GET":
                rows = _filtern(DATEN.get(tab, []), teil.split("?", 1)[1] if "?" in teil else "")
                return route.fulfill(status=200, content_type="application/json", body=json.dumps(rows))
            log["schreib"].append(req.method + " " + tab)
            return route.abort()
        if "supabase.co" in u:
            return route.abort()
        return route.continue_()

    ctx = browser.new_context(viewport={"width": breite, "height": hoehe}, service_workers="block", locale="de-AT", timezone_id="Europe/Vienna")
    ctx.add_init_script(INIT)
    ctx.route("**/*", weiter)
    ctx.route("**/index.html", lambda r: r.fulfill(status=200, content_type="text/html; charset=utf-8", body=body))
    s = ctx.new_page()
    s.clock.install(time=UHR)
    s.clock.resume()
    s.on("pageerror", lambda e: log["fehler"].append(str(e)[:200]))
    s.goto(url, wait_until="domcontentloaded")
    s.wait_for_timeout(5000)
    return ctx, s, log


KLICK = """([t, idx]) => { const wurzel=document.querySelector('[data-bx-mamonat]')||document;
  const k=[...wurzel.querySelectorAll('button,[role=tab]')].filter(b=>(b.textContent||'').replace(/\\s+/g,' ').trim()===t && b.getBoundingClientRect().height>0);
  const b=idx<0?k[k.length+idx]:k[idx]; if(!b) return 'fehlt'; if(b.disabled) return 'gesperrt'; b.click(); return 'ok'; }"""

NAV = """(t) => { const k=[...document.querySelectorAll('button,[role=tab]')].filter(b=>(b.textContent||'').replace(/\\s+/g,' ').trim().indexOf(t)>=0 && b.getBoundingClientRect().height>0); if(k.length){k[0].click();return true;} return false; }"""

WAHL = """(nm) => { const sel=document.querySelector('[data-bx-kopfleiste] select'); const o=[...sel.options].find(x=>x.textContent.indexOf(nm)===0);
  const st=Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value').set; st.call(sel,o.value); sel.dispatchEvent(new Event('change',{bubbles:true})); return o.value; }"""


MENUE = """() => { const b=[...document.querySelectorAll('button[aria-label]')].find(x=>/Menü|Menu|Mehr/i.test(x.getAttribute('aria-label')) && x.getBoundingClientRect().height>0); if(b){b.click();return true;} return false; }"""


def _mamonat(s, name):
    if not s.evaluate(NAV, "Büro-Portal"):
        s.evaluate(MENUE)  # Handy: Buero-Portal steht im Menue
        s.wait_for_timeout(800)
        assert s.evaluate(NAV, "Büro-Portal"), "Buero-Portal nicht erreichbar"
    s.wait_for_timeout(2000)
    s.evaluate(WAHL, name)
    s.wait_for_timeout(300)
    s.evaluate(NAV, "Mitarbeiter-Monat")
    s.wait_for_timeout(5000)


# Exportwege im Mitarbeiter-Monat: (Beschriftung, Index unter gleich beschrifteten Knoepfen im Abschnitt)
EXPORTWEGE = [("Monat Excel", 0), ("Monat PDF", 0), ("Wochen-Stundenbestätigung", 0), ("Übersicht Excel", 0),
              ("PDF", 0), ("Mo 28.09.", 0), ("PZE-PDF (Lohnverrechner)", 0), ("Excel", -1), ("PDF", -1)]


def _norm(t):
    t = re.sub(r"/(CreationDate|ModDate) \(D:[^)]*\)", "", t or "")
    return re.sub(r"/ID \[[^\]]*\]", "", t)


BESTAETIGEN = """() => { const b=[...document.querySelectorAll('button')].find(x=>/Excel exportieren|exportieren$/.test((x.textContent||'').trim()) && x.getBoundingClientRect().height>0 && !x.closest('[data-bx-mamonat]'));
  if(b){b.click();return true;} return false; }"""


def _ernte(s):
    s.wait_for_timeout(1000)
    s.evaluate(BESTAETIGEN)  # Vorschau-Dialog (Uebersicht Excel): unveraendert bestaetigen
    s.wait_for_timeout(2500)
    return s.evaluate("() => window.__exp.map(x=>({datei:x.datei||null, druck:x.druck||0, typ:x.typ||null, text:x.text==null?null:x.text}))")


def _exporte_ausloesen(browser, url, body):
    ctx, s, log = _seite(browser, url, body)
    try:
        _mamonat(s, "Anna Testmonteur")
        out = {}
        for t, idx in EXPORTWEGE:
            s.evaluate("() => { window.__exp.length = 0; }")
            st = s.evaluate(KLICK, [t, idx])
            out["%s#%d" % (t, idx)] = {"status": st, "ernte": [dict(x, text=_norm(x["text"])) for x in _ernte(s)] if st == "ok" else []}
        return out, log
    finally:
        ctx.close()


def test_jeder_exportweg_liefert_dieselbe_datei_wie_vorher(browser, server):
    vorher, log_v = _exporte_ausloesen(browser, server, _vorher_index())
    nachher, log_n = _exporte_ausloesen(browser, server, _neu_index())
    assert log_v["schreib"] == [] and log_n["schreib"] == [], (log_v["schreib"], log_n["schreib"])
    for weg in vorher:
        assert vorher[weg]["status"] == "ok", (weg, vorher[weg]["status"])
        assert nachher[weg]["status"] == "ok", (weg, nachher[weg]["status"])
        assert vorher[weg]["ernte"], ("Vorher-Stand lieferte nichts", weg)
        assert nachher[weg]["ernte"] == vorher[weg]["ernte"], weg
    # Belege, dass wirklich Dateien entstanden: Dateinamen der Excel-/PDF-Wege
    dateien = [x["datei"] for w in nachher.values() for x in w["ernte"] if x.get("datei")]
    assert any(d.endswith(".xls") for d in dateien) and any(d.endswith(".pdf") for d in dateien), dateien


LEISTEN = """() => { const m=document.querySelector('[data-bx-mamonat]'); if(!m) return null;
  return {leisten:[...m.querySelectorAll('[data-bx-exporte]')].map(e=>[...e.querySelectorAll('button')].map(b=>b.textContent.replace(/\\s+/g,' ').trim())),
          leer:[...m.querySelectorAll('[data-bx-leer]')].map(e=>e.textContent),
          monatsPfeile:m.querySelectorAll('[aria-label="Monat zurück"],[aria-label="Monat vor"],[aria-label="Zeitraum zurück"],[aria-label="Zeitraum vor"],[aria-label="Vorheriger Monat"],[aria-label="Nächster Monat"]').length,
          datumsfelder:m.querySelectorAll('input[type=date]').length,
          monatsWahl:m.querySelectorAll('select[aria-label="Monat"]').length,
          heute:[...m.querySelectorAll('button')].filter(b=>b.textContent.trim()==='Heute' && !b.closest('[data-ze-kw]')).length,
          fest:[...m.querySelectorAll('[data-bx-monat-fest]')].map(e=>e.textContent)}; }"""


@pytest.fixture(scope="module")
def messung(browser, server):
    out = {}
    for breite, hoehe in ((1366, 900), (390, 844)):
        for name in ("Anna Testmonteur", "Bert Ohnedaten"):
            ctx, s, log = _seite(browser, server, _neu_index(), breite, hoehe)
            try:
                _mamonat(s, name)
                out[(breite, name)] = dict(s.evaluate(LEISTEN) or {}, schreib=log["schreib"], fehler=log["fehler"])
            finally:
                ctx.close()
    return out


@pytest.mark.parametrize("breite", [1366, 390])
def test_eine_exportleiste_je_abschnitt(messung, breite):
    m = messung[(breite, "Anna Testmonteur")]
    assert m.get("leisten") is not None, "Mitarbeiter-Monat nicht gerendert"
    assert len(m["leisten"]) == 3, m["leisten"]
    stunden, zulagen, stempel = m["leisten"]
    for k in ("Monat Excel", "Monat PDF", "Wochen-Stundenbestätigung", "Übersicht Excel", "PDF", "Mo 28.09."):
        assert k in stunden, (k, stunden)
    assert zulagen == ["PZE-PDF (Lohnverrechner)"], zulagen
    assert stempel == ["Excel", "PDF"], stempel
    assert m["schreib"] == [] and m["fehler"] == [], (m["schreib"], m["fehler"])


@pytest.mark.parametrize("breite", [1366, 390])
def test_zulagen_und_stempel_folgen_dem_kopfmonat(messung, breite):
    m = messung[(breite, "Anna Testmonteur")]
    assert m.get("leisten") is not None, "Mitarbeiter-Monat nicht gerendert"
    assert m["monatsPfeile"] == 0, "eigene Monats-Pfeile im Mitarbeiter-Monat"
    assert m["datumsfelder"] == 0, "eigene Datumsfelder (Stempelzeiten) im Mitarbeiter-Monat"
    assert m["monatsWahl"] == 0, "eigene Monatswahl (Monatsliste) im Mitarbeiter-Monat"
    assert m["fest"] and all(x == "Oktober 2026" for x in m["fest"]), m["fest"]


@pytest.mark.parametrize("breite", [1366, 390])
def test_leere_abschnitte_zeigen_keine_eintraege(messung, breite):
    leer = messung[(breite, "Bert Ohnedaten")].get("leer")
    assert leer is not None and len(leer) == 3, leer
    assert all(x.startswith("Keine Einträge – Bert Ohnedaten hat im Oktober 2026 keine") for x in leer), leer
    voll = messung[(breite, "Anna Testmonteur")]["leer"]
    assert voll == [], voll  # Gegenfall: wer Stunden, Stempel und Zulagen hat, bekommt keinen Leerhinweis
