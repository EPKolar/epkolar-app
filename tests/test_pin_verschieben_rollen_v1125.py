# -*- coding: utf-8 -*-
"""Plaene: ein GESETZTER Pin wird nur von Admin und Projektleiter verschoben (v3.9.1125) - im ECHTEN Browser.

Regel Sebastian 26.11.2026: "ein gesetzter pin im plan darf der monteur oder buero nicht verrutschen nur admin und
projektleiter" und "nach erstellung darf er nicht mehr geschoben werden". Also: Monteur, Buero, Techniker,
Obermonteur (und alle anderen Rollen) verschieben einen gespeicherten Pin NIE - auch nicht den eigenen, auch nicht
direkt nach dem Speichern. Einen neuen Pin setzen bleibt fuer alle, und die Stelle VOR dem ersten Speichern
(nochmal tippen / "Pin aendern") zu korrigieren ist kein Verschieben. Status, Text, Zuweisung bleiben aenderbar.

Gemessen wird die ganze App (Chromium, Playwright), Supabase abgefangen - nichts verlaesst den Rechner. Jede
Messung zaehlt die abgefangenen Schreib-Auftraege, die eine Lage tragen (x, y, plan_id, page). Die Umkehrprobe baut
den Fehler in eine KOPIE der Datei ein (Buero darf ziehen) und verlangt, dass die Messung ihn findet.
"""
import base64
import functools
import http.server
import io
import json
import os
import socketserver
import struct
import sys
import threading
import urllib.parse
import zlib

import pytest

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WURZEL, "tests"))
from conftest import _extract_fn, run_node_snippet  # noqa: E402

sync_api = pytest.importorskip("playwright.sync_api")

HINWEIS = "Pin verschieben nur Admin/Projektleitung"
LAGE = ("x", "y", "plan_id", "page")


def _png(w, h):
    roh = b"".join(b"\x00" + b"\xee\xee\xee" * w for _ in range(h))

    def ch(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return "data:image/png;base64," + base64.b64encode(
        b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + ch(b"IDAT", zlib.compress(roh)) + ch(b"IEND", b"")).decode()


def _tabellen(rolle):
    return {
        "workers": [{"id": "w1", "name": "Monteur Eins", "role": "Monteur"}],
        "users": [{"id": "7", "name": "Test Person", "username": "u7", "role": rolle, "active": True,
                   "monteur_id": "w1", "permissions": [], "perms_override": {}}],
        "projects": [{"id": "p1", "name": "Muster Wohnhausanlage Nord", "nr": "2026-014", "status": "aktiv"}],
        "worker_projects": [{"worker_id": "w1", "project_id": "p1"}],
        "plans": [{"id": "pl1", "project_id": "p1", "name": "EG Grundriss", "data_url": _png(120, 85),
                   "width": 1200, "height": 850, "page_count": 1, "version": 1}],
        "tickets": [{"id": "t1", "plan_id": "pl1", "project_id": "p1", "x": 40, "y": 50, "page": 1,
                     "title": "Steckdose fehlt", "status": "offen", "priority": "mittel", "type": "mangel",
                     "layer": "l1", "assignee": "w1", "photos": "[]", "comments": "[]", "created_at": "2026-11-20"}],
        "defects": [{"id": "t1", "project_id": "p1", "title": "Steckdose fehlt", "status": "offen", "prio": "mittel",
                     "x": 40.0000003, "y": 50.0000002, "plan_id": "pl1", "page": 1, "zugewiesen": "w1"}],
    }


def _init(rolle):
    return """
try{
  var b=function(s){return btoa(s).replace(/=+$/,'');};
  var jwt=b(JSON.stringify({alg:"HS256",typ:"JWT"}))+"."+b(JSON.stringify({sub:"7",role:"authenticated",exp:Math.floor(Date.now()/1000)+86400}))+".sig";
  localStorage.setItem('epkolar_auth',JSON.stringify({at:jwt,rt:"r",exp:Date.now()+86400000}));
  localStorage.setItem('epkolar_user',JSON.stringify({id:"7",username:"u7",name:"Test Person",role:"%s",monteur_id:"w1",permissions:[],perms_override:{}}));
}catch(e){}
""" % rolle


class _Still(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


@pytest.fixture(scope="module")
def server():
    srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(_Still, directory=WURZEL))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield "http://127.0.0.1:%d/index.html" % srv.server_address[1]
    srv.shutdown()
    srv.server_close()


@pytest.fixture(scope="module")
def browser():
    with sync_api.sync_playwright() as pw:
        try:
            br = pw.chromium.launch()
        except Exception as e:  # pragma: no cover
            pytest.skip("Chromium nicht startbar: %s" % e)
        yield br
        br.close()


@pytest.fixture(scope="module")
def quelle():
    return io.open(os.path.join(WURZEL, "index.html"), encoding="utf-8", newline="").read()


def _app(browser, url, rolle, reiter="Pläne", breite=1280, hoehe=800, index_body=None):
    """App als <rolle> laden, Projekt oeffnen, Reiter waehlen. Liefert ctx, Seite, Schreibliste, JS-Fehler."""
    schreib = []
    tab = _tabellen(rolle)

    def rest(route):
        req = route.request
        if req.method == "OPTIONS":
            return route.fulfill(status=204, headers={"Access-Control-Allow-Origin": "*"})
        pu = urllib.parse.urlparse(req.url)
        if req.method in ("GET", "HEAD"):
            t = pu.path.split("/rest/v1/")[-1]
            return route.fulfill(status=200, content_type="application/json", body=json.dumps(tab.get(t, [])))
        try:
            body = json.loads(req.post_data or "{}")
        except ValueError:
            body = {}
        schreib.append({"m": req.method, "tab": pu.path.split("/rest/v1/")[-1], "body": body})
        return route.fulfill(status=200, content_type="application/json", body="[]")

    ctx = browser.new_context(viewport={"width": breite, "height": hoehe}, service_workers="block")
    ctx.add_init_script(_init(rolle))
    ctx.route("**/auth/v1/**", lambda r: r.abort())
    ctx.route("**/functions/v1/**", lambda r: r.abort())
    ctx.route("**/rest/v1/**", rest)
    if index_body is not None:
        ctx.route("**/index.html", lambda r: r.fulfill(status=200, content_type="text/html; charset=utf-8", body=index_body))
    s = ctx.new_page()
    fehler = []
    s.on("pageerror", lambda e: fehler.append(str(e)[:200]))
    s.goto(url, wait_until="domcontentloaded")
    # PC/Tablet: Reiter "Projekte"; Handy-Leiste: "Baustelle"
    s.wait_for_function("() => [...document.querySelectorAll('button')].some(b => ['Projekte','Baustelle'].includes((b.innerText||'').trim()) && b.getBoundingClientRect().height>0)", timeout=40000)
    s.wait_for_timeout(1500)
    s.evaluate("() => { const b=[...document.querySelectorAll('button')].find(b => ['Projekte','Baustelle'].includes((b.innerText||'').trim()) && b.getBoundingClientRect().height>0); b.click(); }")
    s.get_by_text("Muster Wohnhausanlage Nord").first.click(timeout=15000)
    s.get_by_role("button", name=reiter, exact=True).first.click(timeout=15000)
    s.wait_for_timeout(2000)
    return ctx, s, schreib, fehler


def _pin(s, titel):
    for p in s.query_selector_all('[aria-label^="Pin "]'):
        bb = p.bounding_box()
        if titel in (p.get_attribute("aria-label") or "") and bb and bb["width"] < 60:
            return p, bb
    return None, None


def _ziehe(s, titel, dx=90, dy=40):
    p, bb = _pin(s, titel)
    assert p, "Pin '%s' nicht auf dem Plan" % titel
    cx, cy = bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] - 8
    s.mouse.move(cx, cy)
    s.mouse.down()
    s.mouse.move(cx + dx / 3, cy + dy / 3, steps=4)
    s.mouse.move(cx + dx, cy + dy, steps=6)
    s.wait_for_timeout(150)
    hinweis_beim_ziehen = s.get_by_text(HINWEIS).count() > 0
    s.mouse.up()
    s.wait_for_timeout(3000)
    return hinweis_beim_ziehen or s.get_by_text(HINWEIS).count() > 0


def _warte(s, pruef, ms=8000):
    """Die Warteschlange schreibt verzoegert: bis pruef() wahr ist oder die Zeit um ist."""
    for _ in range(ms // 250):
        if pruef():
            return True
        s.wait_for_timeout(250)
    return pruef()


def _lage_auftraege(schreib, nur_update=True):
    return [w for w in schreib if w["tab"] in ("tickets", "defects")
            and (w["m"] in ("PATCH", "PUT") or not nur_update) and any(k in w["body"] for k in LAGE)]


def _messe_ziehen(browser, url, rolle, index_body=None):
    ctx, s, schreib, fehler = _app(browser, url, rolle, index_body=index_body)
    try:
        hinweis = _ziehe(s, "Steckdose fehlt")
        return {"lage": _lage_auftraege(schreib), "hinweis": hinweis, "fehler": fehler}
    finally:
        ctx.close()


# ── Wer darf ziehen ─────────────────────────────────────────────────────────
@pytest.mark.parametrize("rolle", ["admin", "projektleiter"])
def test_admin_und_projektleiter_verschieben(browser, server, rolle):
    r = _messe_ziehen(browser, server, rolle)
    assert not r["fehler"], r["fehler"]
    tk = [w for w in r["lage"] if w["tab"] == "tickets"]
    assert tk and "x" in tk[0]["body"] and abs(tk[0]["body"]["x"] - 40) > 1, \
        "%s: Ziehen schrieb keine neue Lage: %s" % (rolle, r["lage"])
    assert not r["hinweis"], "%s bekommt den Sperr-Hinweis" % rolle


@pytest.mark.parametrize("rolle", ["buero", "monteur", "techniker", "obermonteur"])
def test_andere_rollen_verschieben_nicht(browser, server, rolle):
    r = _messe_ziehen(browser, server, rolle)
    assert not r["fehler"], r["fehler"]
    assert r["lage"] == [], "%s hat einen gesetzten Pin verschoben: %s" % (rolle, r["lage"])
    assert r["hinweis"], "%s: kein Hinweis '%s' beim Zieh-Versuch" % (rolle, HINWEIS)


# ── Nach dem Speichern sofort gesperrt; vorher frei ─────────────────────────
def test_monteur_setzt_neuen_pin_und_kann_ihn_danach_nicht_schieben(browser, server):
    ctx, s, schreib, fehler = _app(browser, server, "monteur")
    try:
        s.get_by_role("button", name="Ticket platzieren").first.click()
        s.wait_for_timeout(600)
        s.mouse.click(650, 600)
        s.wait_for_timeout(1200)
        s.fill('input[placeholder="z.B. Steckdose fehlt"]', "Neuer Pin")
        s.get_by_role("button", name="Erstellen", exact=True).click()
        _warte(s, lambda: any(w["m"] == "POST" and w["tab"] == "tickets" for w in schreib))
        post = [w for w in schreib if w["m"] == "POST" and w["tab"] == "tickets"]
        assert post and post[0]["body"].get("x") not in (None, 0) and post[0]["body"].get("title") == "Neuer Pin", \
            "Monteur kann keinen neuen Pin setzen: %s" % schreib
        vorher = len(schreib)
        hinweis = _ziehe(s, "Neuer Pin")  # gleiche Sitzung, direkt nach dem Speichern
        neu = _lage_auftraege(schreib[vorher:])
        assert neu == [], "eigener Pin direkt nach dem Speichern verschoben: %s" % neu
        assert hinweis, "kein Hinweis beim Zieh-Versuch auf den eigenen neuen Pin"
        assert not fehler, fehler
    finally:
        ctx.close()


def test_monteur_korrigiert_stelle_vor_dem_ersten_speichern(browser, server):
    """Maengel-Reiter: + Mangel -> Auf Plan setzen -> Tipp A -> nochmal Tipp B -> Hier setzen -> 'Pin ändern' ->
    Tipp C -> Hier setzen -> Hinzufuegen. Der POST traegt die LETZTE Stelle, kein UPDATE noetig."""
    ctx, s, schreib, fehler = _app(browser, server, "monteur", reiter="Mängel")
    try:
        s.get_by_role("button", name="+ Mangel", exact=True).click()
        s.get_by_role("button", name="Auf Plan setzen").first.click()
        dlg = s.locator('[role=dialog][aria-label="Mangel auf Plan setzen"]')
        dlg.wait_for(timeout=10000)
        s.wait_for_timeout(1500)
        bb = dlg.bounding_box()
        mx, my = bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] * 0.6
        s.mouse.click(mx - 120, my)
        s.wait_for_timeout(400)
        s.mouse.click(mx - 60, my)  # "Sonst nochmal tippen"
        s.wait_for_timeout(400)
        s.get_by_role("button", name="✓ Hier setzen").click()
        s.wait_for_timeout(500)
        s.get_by_role("button", name="Pin ändern").first.click()
        dlg.wait_for(timeout=10000)
        s.wait_for_timeout(1500)
        s.mouse.click(mx + 80, my - 40)
        s.wait_for_timeout(400)
        s.get_by_role("button", name="✓ Hier setzen").click()
        s.wait_for_timeout(500)
        s.locator('xpath=//span[normalize-space()="Mangel"]/following-sibling::*//input | //span[normalize-space()="Mangel"]/following-sibling::input').first.fill("Probe vor Speichern")
        s.get_by_role("button", name="Hinzufügen").click()
        _warte(s, lambda: any(w["m"] == "POST" and w["tab"] == "defects" for w in schreib))
        s.wait_for_timeout(1000)
        post = [w for w in schreib if w["m"] == "POST" and w["tab"] == "defects"]
        upd = _lage_auftraege(schreib)
        assert post, "Mangel nicht angelegt: %s" % schreib
        assert post[0]["body"].get("x") is not None and post[0]["body"].get("x") > 50, \
            "POST traegt nicht die zuletzt gewaehlte Stelle (rechts der Mitte): %s" % post[0]["body"]
        assert upd == [], "Anlegen brauchte ein UPDATE der Lage (der DB-Riegel wuerde es abweisen): %s" % upd
        assert not fehler, fehler
    finally:
        ctx.close()


@pytest.mark.parametrize("rolle", ["monteur", "buero"])
def test_status_bleibt_aenderbar_ohne_lage(browser, server, rolle):
    """Status am gesetzten Pin aendern: Ticket- UND Maengel-Spiegel-PUT gehen durch und tragen KEINE Lage
    (defects.x ist double, tickets.x real - der Spiegel schrieb sonst eine minimal andere Zahl, die der DB-Riegel abweist)."""
    ctx, s, schreib, fehler = _app(browser, server, rolle)
    try:
        p, _ = _pin(s, "Steckdose fehlt")
        p.click()
        s.wait_for_timeout(1000)
        s.get_by_role("button", name="In Bearbeitung", exact=True).first.click()
        _warte(s, lambda: any(w["tab"] == "defects" and "status" in w["body"] for w in schreib))
        s.wait_for_timeout(1000)
        st = [w for w in schreib if w["m"] in ("PATCH", "PUT") and w["tab"] == "tickets" and w["body"].get("status") == "in_bearbeitung"]
        assert st, "Status-Aenderung nicht geschrieben: %s" % schreib
        df = [w for w in schreib if w["m"] in ("PATCH", "PUT") and w["tab"] == "defects" and "status" in w["body"]]
        assert df, "Maengel-Spiegel bekam den Status nicht: %s" % schreib
        assert _lage_auftraege(schreib) == [], "Status-PUT traegt eine Lage: %s" % _lage_auftraege(schreib)
        assert not fehler, fehler
    finally:
        ctx.close()


# ── Die Regel selbst (echter Code, node) ────────────────────────────────────
def test_regel_fuer_alle_rollen(node_exe, quelle):
    f1 = _extract_fn(quelle, "_pinVerschiebenErlaubt")
    f2 = _extract_fn(quelle, "_pinPosGeaendert")
    assert f1 and f2
    js = f1 + "\n" + f2 + r"""
const rollen=["admin","projektleiter","buero","monteur","techniker","obermonteur","helfer","viewer","kiosk","lager_display",""];
const darf={};rollen.forEach(r=>darf[r]=_pinVerschiebenErlaubt({role:r}));darf["null"]=_pinVerschiebenErlaubt(null);
const a={x:53.69863640772154,y:57.73568926073938,plan_id:"pl1",page:1};
const fr={x:Math.fround(a.x),y:Math.fround(a.y),planId:"pl1"};
console.log(JSON.stringify({darf,
  realGerundet:_pinPosGeaendert(a,fr),
  verschoben:_pinPosGeaendert(a,{...a,x:a.x+0.5}),
  anderePlan:_pinPosGeaendert(a,{...a,plan_id:"pl2"}),
  andereSeite:_pinPosGeaendert(a,{...a,page:2}),
  vomPlan:_pinPosGeaendert(a,{...a,x:null,y:null}),
  leerGleich:_pinPosGeaendert({x:null,y:null,plan_id:""},{x:null,y:null,planId:"",page:1})}));
"""
    out = json.loads(run_node_snippet(node_exe, js).strip().splitlines()[-1])
    erlaubt = sorted(r for r, v in out["darf"].items() if v)
    assert erlaubt == ["admin", "projektleiter"], erlaubt
    assert out["realGerundet"] is False and out["leerGleich"] is False
    assert out["verschoben"] and out["anderePlan"] and out["andereSeite"] and out["vomPlan"]


# ── Umkehrprobe: die Messung muss ein erlaubtes Buero-Ziehen finden ─────────
def test_umkehrprobe_buero_darf_waere_rot(browser, server, quelle):
    alt = 'function _pinVerschiebenErlaubt(cu){const r=cu&&cu.role;return r==="admin"||r==="projektleiter";}'
    assert quelle.count(alt) == 1
    kaputt = quelle.replace(alt, alt.replace('r==="projektleiter"', 'r==="projektleiter"||r==="buero"'))
    r = _messe_ziehen(browser, server, "buero", index_body=kaputt)
    assert r["lage"], "Umkehrprobe: Buero darf ziehen, aber die Messung findet keinen Lage-Auftrag - sie waere zahnlos"
