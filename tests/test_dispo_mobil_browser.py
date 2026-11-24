# -*- coding: utf-8 -*-
"""Dispo mobil im ECHTEN Browser (Chromium, Playwright) - die ganze App, nicht ein Ausschnitt.

Offline-Sitzung wie in scripts/tab_sweep.py: localStorage epkolar_auth {at,rt,exp} mit Schein-JWT +
epkolar_user (Rolle buero), /auth/v1 abgebrochen, /rest/v1 abgefangen (Testdaten fuer arbeitsscheine,
workers, users; jede schreibende Anfrage wird MITGESCHRIEBEN). Die Uhr steht auf Mo 23.11.2026 09:00.

Gemessen wird:
  * Handy 360/390/430 hochkant und 915x412 quer: Dispo = Tageskarten, Kalender Tag/Monat am Handy -
    kein Querrollen, Inhaltsschrift >= 13 px, Tippziele >= 44 px, Monatszahl = Zahl der Tageskarten.
  * Tablet hochkant 800x1280: Wochenuebersicht nur lesen (kein [data-dispocell], nichts ziehbar).
  * PC 1440x900: Finger- und Stift-Zeiger auf einer Kachel schreiben NICHTS; die Maus zieht eine Kachel
    auf einen anderen Tag und es geht genau EIN PATCH mit NUR dispo_*-Feldern hinaus, kein Push.
  * Termin bestaetigen: genau EIN Schreibvorgang mit termin_bestaetigt + push_pending, genau EIN Push.
Gegenprobe: derselbe Fingerlauf gegen den Stand vor dem Umbau (f0c1c86) schreibt - dort rot.
"""
import datetime
import functools
import http.server
import json
import os
import socketserver
import subprocess
import threading

import pytest

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALT_REF = "f0c1c86"

sync_api = pytest.importorskip("playwright.sync_api")

UHR = "2026-11-23T09:00:00"
MO = datetime.date(2026, 11, 23)


def _iso(t):
    return (MO + datetime.timedelta(days=t)).isoformat()


WORKERS = [{"id": "w1", "name": "Anna Steinbichler", "role": "Monteur"},
           {"id": "w2", "name": "Bert Hinterleitner", "role": "Monteur"},
           {"id": "w3", "name": "Cora Wieshofer-Prandtner", "role": "Monteur"}]


def _scheine():
    a = []
    for k in range(8):
        a.append({"id": "A%d" % k, "nummer": "S07%04d" % k, "kund_name": "Kunde mit langem Namen %d GmbH & Co KG" % k,
                  "arbeitsort": "Lange Strasse %d, 3500 Krems an der Donau" % k, "monteur": ["w1", "w2", "w3"][k % 3],
                  "termin_bestaetigt": _iso(1 + k % 4), "termin_zeit": "08:00", "dauer": "02:00", "scheinstatus": "freigegeben",
                  "juprowa_id": 100 + k, "arbeitsanweisungen": "Arbeit %d" % k, "projektnr": "PA1" if k == 2 else "",
                  "scheinart": "stoerung" if k == 3 else "kein"})
    # geplant (ohne bestaetigten Termin) und Wunsch
    a.append({"id": "G1", "nummer": "S079001", "kund_name": "Geplant", "arbeitsort": "Krems", "monteur": "w2", "termin_bestaetigt": "",
              "termin_vorschlag": _iso(3), "dispo_datum": _iso(2), "dispo_zeit": "10:00", "dispo_dauer": "01:30",
              "scheinstatus": "freigegeben", "juprowa_id": 901})
    a.append({"id": "W1", "nummer": "S079002", "kund_name": "Wunsch", "arbeitsort": "Krems", "monteur": "", "termin_bestaetigt": "",
              "termin_vorschlag": _iso(1), "scheinstatus": "aufgenommen", "juprowa_id": 902})
    for x in a:
        x.setdefault("prioritaet", "normal")
        x.setdefault("push_pending", False)
    return a


USER = {"id": "1", "name": "Test Buero", "username": "admin", "email": "t@x", "role": "buero", "active": True,
        "monteur_id": None, "permissions": [], "perms_override": {}, "locked": False}

INIT = """
try{
  var b=function(s){return btoa(s).replace(/=+$/,'');};
  var jwt=b(JSON.stringify({alg:"HS256",typ:"JWT"}))+"."+b(JSON.stringify({sub:"1",role:"authenticated",exp:Math.floor(Date.now()/1000)+86400}))+".sig";
  localStorage.setItem('epkolar_auth',JSON.stringify({at:jwt,rt:"r",exp:Date.now()+86400000}));
  localStorage.setItem('epkolar_user',JSON.stringify({id:"1",username:"admin",name:"Test Buero",role:"buero",rolle:"Backoffice",permissions:[],perms_override:{}}));
}catch(e){}
"""


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


def _alt_index():
    r = subprocess.run(["git", "-C", WURZEL, "show", ALT_REF + ":index.html"], capture_output=True)
    if r.returncode != 0:
        pytest.skip("Altstand nicht im Repo")
    return r.stdout


def _seite(browser, url, breite, hoehe, scheine=None, index_body=None, touch=False):
    log = {"schreib": [], "push": []}
    daten = scheine if scheine is not None else _scheine()

    def rest(route):
        req = route.request
        u = req.url
        if req.method == "GET":
            if "/rest/v1/arbeitsscheine" in u:
                # Filter, die die App wirklich stellt, ehrlich beantworten (die Nachsende-Abfrage fragt push_pending=eq.true)
                zeilen = [x for x in daten if x.get("push_pending")] if "push_pending=eq.true" in u else daten
                return route.fulfill(status=200, content_type="application/json", body=json.dumps(zeilen))
            if "/rest/v1/users" in u:
                return route.fulfill(status=200, content_type="application/json", body=json.dumps([USER]))
            if "/rest/v1/workers" in u:
                return route.fulfill(status=200, content_type="application/json", body=json.dumps(WORKERS))
            return route.fulfill(status=200, content_type="application/json", body="[]")
        teil = u.split("/rest/v1/")[-1]
        if teil.startswith("rpc/juprowa_push"):
            log["push"].append(teil)
            return route.fulfill(status=200, content_type="application/json", body="{}")
        if teil.startswith("rpc/") and "juprowa" in teil:
            # Abruf aus OFFA: im Test nicht erreichbar (kein Feed, kein Abgleich)
            return route.abort()
        if teil.startswith("arbeitsscheine"):
            try:
                body = json.loads(req.post_data or "{}")
            except Exception:
                body = {"_roh": req.post_data}
            log["schreib"].append({"methode": req.method, "pfad": teil, "body": body})
        return route.fulfill(status=200, content_type="application/json", body="[{\"id\":\"x\"}]")

    ctx = browser.new_context(viewport={"width": breite, "height": hoehe}, has_touch=touch, is_mobile=touch)
    ctx.add_init_script(INIT)
    ctx.route("**/auth/v1/**", lambda r: r.abort())
    ctx.route("**/rest/v1/**", rest)
    if index_body is not None:
        ctx.route("**/index.html", lambda r: r.fulfill(status=200, content_type="text/html; charset=utf-8", body=index_body))
    seite = ctx.new_page()
    seite.clock.set_fixed_time(UHR)
    fehler = []
    seite.on("pageerror", lambda e: fehler.append(str(e)[:200]))
    seite.goto(url, wait_until="domcontentloaded")
    seite.wait_for_timeout(4500)
    return ctx, seite, log, fehler


NAV_AS = """() => { const sicht = b => b.getBoundingClientRect().height > 0;
  const k = [...document.querySelectorAll('button[aria-label]')].filter(b => b.getAttribute('aria-label') === 'Arbeitsscheine' && sicht(b));
  if (k.length) { k[0].click(); return 'aria'; }
  const t = [...document.querySelectorAll('button')].filter(b => (b.textContent || '').trim() === 'Arbeitsscheine' && sicht(b));
  if (t.length) { t[0].click(); return 'text'; } return 'nicht-gefunden'; }"""

SUB = """(w) => { const k = [...document.querySelectorAll('button,[role=tab]')].filter(b => (b.textContent || '').trim() === w && b.getBoundingClientRect().height > 0);
  if (k.length) { k[0].click(); return k.length; } return 0; }"""

MESSEN = """() => {
  const W = innerWidth; const root = document.querySelector('[data-dispo-mobil]');
  if (!root) return {da: false};
  const klein = [], tipp = [], rechts = [];
  root.querySelectorAll('*').forEach(e => {
    const r = e.getBoundingClientRect(); if (!r.width || !r.height) return;
    if (r.right > W + 1) rechts.push((e.tagName + ' ' + (e.textContent || '').trim()).slice(0, 50) + ' ' + Math.round(r.right));
    const direkt = [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (direkt) { const fs = parseFloat(getComputedStyle(e).fontSize); if (fs < 13) klein.push(e.tagName + ':' + fs + ':' + e.textContent.trim().slice(0, 30)); }
    if (e.matches('button,[role=button]') && (r.height < 44 || r.width < 44)) tipp.push(e.tagName + ':' + Math.round(r.width) + 'x' + Math.round(r.height) + ':' + (e.textContent || '').trim().slice(0, 30));
  });
  return {da: true, art: root.getAttribute('data-dispo-mobil'), scrollW: document.documentElement.scrollWidth, W: W,
          klein: klein, tipp: tipp, rechts: rechts, jobs: root.querySelectorAll('[data-dk-job]').length,
          zellen: document.querySelectorAll('[data-dispocell]').length};
}"""


def _pruefe_mobil(m, art):
    assert m["da"], "keine Mobilansicht"
    assert m["art"] == art, m["art"]
    assert m["scrollW"] <= m["W"] + 1, "Seite rollt quer: %s > %s" % (m["scrollW"], m["W"])
    assert m["rechts"] == [], m["rechts"][:5]
    assert m["klein"] == [], m["klein"][:5]
    assert m["tipp"] == [], m["tipp"][:5]
    assert m["zellen"] == 0, "Raster mit Zieh-Zellen am Handy"


@pytest.mark.parametrize("breite,hoehe", [(360, 780), (390, 844), (430, 932), (915, 412)])
def test_handy_tageskarten_und_kalender(browser, server, breite, hoehe):
    ctx, s, log, fehler = _seite(browser, server, breite, hoehe, touch=True)
    try:
        assert s.evaluate(NAV_AS) != "nicht-gefunden"
        s.wait_for_timeout(1200)
        assert s.evaluate(SUB, "Dispo") >= 1
        s.wait_for_timeout(1500)
        m = s.evaluate(MESSEN)
        _pruefe_mobil(m, "dispo")
        # Dienstag hat Termine: Wochenstreifen antippen
        s.evaluate("""() => { const b=[...document.querySelectorAll('[data-dispo-mobil] button[aria-pressed]')].find(x=>/Dienstag/.test(x.getAttribute('aria-label')||'')); if(b) b.click(); }""")
        s.wait_for_timeout(600)
        m = s.evaluate(MESSEN)
        _pruefe_mobil(m, "dispo")
        assert m["jobs"] >= 3, m["jobs"]
        # Kalender: Monat -> Zahl je Tag, tippen -> Tag mit gleich vielen Karten
        assert s.evaluate(SUB, "Kalender") >= 1
        s.wait_for_timeout(1000)
        assert s.evaluate(SUB, "Monat") >= 1
        s.wait_for_timeout(800)
        m = s.evaluate(MESSEN)
        _pruefe_mobil(m, "monat")
        zahl = s.evaluate("() => +document.querySelector('[data-kal-tag=\"%s\"]').getAttribute('data-anzahl')" % _iso(1))
        assert zahl >= 2
        s.evaluate("() => document.querySelector('[data-kal-tag=\"%s\"]').click()" % _iso(1))
        s.wait_for_timeout(800)
        m = s.evaluate(MESSEN)
        _pruefe_mobil(m, "kalender")
        assert m["jobs"] == zahl, (m["jobs"], zahl)
        assert log["schreib"] == [] and log["push"] == [], log
        assert fehler == [], fehler
    finally:
        ctx.close()


def test_tablet_hochkant_wochenuebersicht_nur_lesen(browser, server):
    ctx, s, log, fehler = _seite(browser, server, 800, 1280, touch=True)
    try:
        s.evaluate(NAV_AS)
        s.wait_for_timeout(1200)
        s.evaluate(SUB, "Dispo")
        s.wait_for_timeout(1500)
        m = s.evaluate(MESSEN)
        assert m["da"] and m["art"] == "woche", m
        assert m["zellen"] == 0 and m["scrollW"] <= m["W"] + 1
        assert m["klein"] == [] and m["tipp"] == [], (m["klein"][:3], m["tipp"][:3])
        assert m["jobs"] >= 8
        assert fehler == []
    finally:
        ctx.close()


ZEIGER_JS = """([pt, von, nach]) => {
  const chip = document.querySelector('[data-dispocell][data-monteur="w1"][data-iso="' + von + '"] [title^="Ziehen"]');
  const ziel = document.querySelector('[data-dispocell][data-monteur="w1"][data-iso="' + nach + '"]');
  if (!chip || !ziel) return 'fehlt ' + !!chip + ' ' + !!ziel;
  const a = chip.getBoundingClientRect(), b = ziel.getBoundingClientRect();
  const x0 = a.left + 20, y0 = a.top + 10, x1 = b.left + b.width / 2, y1 = b.top + 40;
  const o = (x, y) => ({bubbles: true, cancelable: true, pointerType: pt, pointerId: 7, isPrimary: true, clientX: x, clientY: y, button: 0, buttons: 1});
  chip.dispatchEvent(new PointerEvent('pointerdown', o(x0, y0)));
  for (let i = 1; i <= 8; i++) window.dispatchEvent(new PointerEvent('pointermove', o(x0 + (x1 - x0) * i / 8, y0 + (y1 - y0) * i / 8)));
  window.dispatchEvent(new PointerEvent('pointerup', o(x1, y1)));
  return 'ok';
}"""


def _pc_dispo(browser, server, index_body=None, scheine=None):
    ctx, s, log, fehler = _seite(browser, server, 1440, 900, scheine=scheine, index_body=index_body)
    s.evaluate(NAV_AS)
    s.wait_for_timeout(1200)
    assert s.evaluate(SUB, "Dispo") >= 1
    s.wait_for_timeout(2000)
    return ctx, s, log, fehler


def pruefe_finger(browser, server, index_body=None):
    ctx, s, log, fehler = _pc_dispo(browser, server, index_body)
    try:
        assert s.evaluate("() => document.querySelectorAll('[data-dispocell]').length") > 0
        for pt in ("touch", "pen"):
            r = s.evaluate(ZEIGER_JS, [pt, _iso(1), _iso(3)])
            assert r == "ok", r
            s.wait_for_timeout(1500)
        assert log["schreib"] == [], "Finger/Stift hat geschrieben: %s" % log["schreib"]
        assert log["push"] == []
    finally:
        ctx.close()


def test_pc_finger_und_stift_schreiben_nichts(browser, server):
    pruefe_finger(browser, server)


def test_gegenprobe_finger_alt_schreibt(browser, server):
    with pytest.raises(AssertionError):
        pruefe_finger(browser, server, index_body=_alt_index())


def test_pc_maus_zieht_und_schreibt_nur_planung(browser, server):
    ctx, s, log, fehler = _pc_dispo(browser, server)
    try:
        chip = s.locator('[data-dispocell][data-monteur="w1"][data-iso="%s"] [title^="Ziehen"]' % _iso(1)).first
        ziel = s.locator('[data-dispocell][data-monteur="w1"][data-iso="%s"]' % _iso(3)).first
        a = chip.bounding_box()
        b = ziel.bounding_box()
        s.mouse.move(a["x"] + 20, a["y"] + 10)
        s.mouse.down()
        for i in range(1, 11):
            s.mouse.move(a["x"] + 20 + (b["x"] + b["width"] / 2 - a["x"] - 20) * i / 10, a["y"] + 10 + (b["y"] + 40 - a["y"] - 10) * i / 10)
        s.mouse.up()
        s.wait_for_timeout(2500)
        sch = log["schreib"]
        assert len(sch) == 1, sch
        assert sch[0]["methode"] == "PATCH" and set(sch[0]["body"]) == {"dispo_datum", "dispo_zeit", "dispo_dauer"}, sch
        assert sch[0]["body"]["dispo_datum"] == _iso(3)
        assert log["push"] == [], log["push"]
        # die Kachel steht jetzt als "Geplant" bzw. "Weicht ab" am neuen Tag, mit Knopf Termin bestaetigen
        assert s.locator('[data-dispocell][data-monteur="w1"][data-iso="%s"] [data-stand="abweichend"]' % _iso(3)).count() >= 1
        assert fehler == []
    finally:
        ctx.close()


def test_termin_bestaetigen_genau_ein_push(browser, server):
    ctx, s, log, fehler = _pc_dispo(browser, server)
    try:
        knopf = s.locator('[data-dp-bestaetigen="G1"]')
        assert knopf.count() == 1, "Knopf Termin bestaetigen fehlt an der geplanten Kachel"
        knopf.first.click()
        s.wait_for_timeout(9000)
        # geschrieben wird der Termin genau einmal; danach quittiert die Push-Klammer das Ergebnis (last_push_at/push_error)
        sch = [x for x in log["schreib"] if "G1" in x["pfad"] and "termin_bestaetigt" in x["body"]]
        assert len(sch) == 1, log["schreib"]
        assert all(("termin_bestaetigt" in x["body"]) or set(x["body"]) <= {"last_push_at", "push_pending", "push_error"}
                   for x in log["schreib"] if "G1" in x["pfad"]), log["schreib"]
        body = sch[0]["body"]
        assert body.get("termin_bestaetigt") == _iso(2) and body.get("push_pending") is True, body
        assert body.get("dispo_datum", "x") is None, body
        assert len(log["push"]) == 1, log["push"]
        assert fehler == []
    finally:
        ctx.close()
