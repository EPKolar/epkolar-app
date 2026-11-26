# -*- coding: utf-8 -*-
"""Wochenplanung am Handy: Namen in den Tageszellen lesbar (v3.9.1122) - im ECHTEN Browser.

Befund 26.11.2026 (390x844, alle fuenf Rollen): in der Planungskarte standen die sechs Tageszellen
Mo..Sa nebeneinander, je rund 50 px. Der Name (nowrap + ellipsis, Kurzform maKurz) stand als
"Monte..." - zwei Monteure in derselben Zelle waren nicht zu unterscheiden, das Kennzeichen brach
in "XX-" / "101AA". maKurz kann das nicht loesen: "Monteur 1"/"Monteur 2" oder "Steinbach"/
"Steinbichler" haben erst ab dem 8. Zeichen ein eindeutiges Praefix.

Kur: am Handy (Stufe schmal = isMob) zwei Reihen zu je drei Tageszellen. Kein Umbruch mitten im
Wort (PL2/v1004 bleibt: nowrap + maKurz), Tablet/PC (Tabelle) unveraendert.

Gemessen wird die ganze App (Chromium, Playwright), Supabase abgefangen, nichts wird geschrieben:
  * 390x844: jedes Namens-Element der Tageszellen ist NICHT abgeschnitten (scrollWidth <= clientWidth+1),
    mindestens eine Zelle traegt zwei Namen, die sichtbaren Texte einer Zelle sind verschieden.
  * 1280x800: Zellbreiten und Namensstil der Planungstabelle sind gleich wie in 1f3791c.
Umkehrprobe: dieselbe Messung gegen `git show 1f3791c:index.html` findet die abgeschnittenen Namen.
Mit EPK_PLAN_ALT=1 laeuft test_handy_namen_nicht_abgeschnitten gegen den Altstand (muss ROT sein).
"""
import functools
import http.server
import json
import os
import socketserver
import subprocess
import threading
import urllib.parse

import pytest

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALT_REF = "1f3791c"
sync_api = pytest.importorskip("playwright.sync_api")

UHR = "2026-11-26T09:00:00"
JAHR, KW = 2026, 48

# Namen mit LANGEM gemeinsamen Anfang - genau die Faelle, an denen maKurz nichts kuerzen kann.
WORKERS = [
    {"id": "w1", "name": "Monteur 1", "role": "Monteur", "eintritt": "2020-01-01"},
    {"id": "w2", "name": "Monteur 2", "role": "Monteur", "eintritt": "2020-01-01"},
    {"id": "w3", "name": "Steinbach", "role": "Techniker", "eintritt": "2020-01-01"},
    {"id": "w4", "name": "Steinbichler", "role": "Monteur", "eintritt": "2020-01-01"},
]
FAHRZEUGE = [{"id": "fz1", "kennzeichen": "XX-101AA", "bezeichnung": "Testwagen", "aktiv": True}]
PROJECTS = [{"id": "p1", "name": "Muster Wohnhausanlage Nord", "status": "aktiv"},
            {"id": "p2", "name": "Muster Buero Mitte", "status": "aktiv"}]


def _rows():
    out = []
    for i, (pid, bvh, ma) in enumerate([("p1", "Muster Wohnhausanlage Nord", ["w1", "w2"]),
                                         ("p2", "Muster Buero Mitte", ["w3", "w4"])]):
        z = {d: {"ma": (ma if d != "Sa" else []), "fz": (["fz1"] if d != "Sa" else [])}
             for d in ["Mo", "Di", "Mi", "Do", "Fr", "Sa"]}
        out.append({"row_id": "wpr%d" % (i + 1), "year": JAHR, "week": KW, "sort_order": i, "bvh": bvh,
                    "proj_id": pid, "bem": "", "z": z, "updated_at": "2026-11-23T07:00:00Z", "updated_by": "Test"})
    return out


USER = {"id": "1", "name": "Test Admin", "username": "admin", "email": "t@x", "role": "admin", "active": True,
        "monteur_id": None, "permissions": [], "perms_override": {}, "locked": False}

INIT = """
try{
  var b=function(s){return btoa(s).replace(/=+$/,'');};
  var jwt=b(JSON.stringify({alg:"HS256",typ:"JWT"}))+"."+b(JSON.stringify({sub:"1",role:"authenticated",exp:Math.floor(Date.now()/1000)+86400}))+".sig";
  localStorage.setItem('epkolar_auth',JSON.stringify({at:jwt,rt:"r",exp:Date.now()+86400000}));
  localStorage.setItem('epkolar_user',JSON.stringify({id:"1",username:"admin",name:"Test Admin",role:"admin",permissions:[],perms_override:{}}));
}catch(e){}
"""

TABELLEN = {"workers": WORKERS, "users": [USER], "fahrzeuge": FAHRZEUGE, "projects": PROJECTS, "weekplan_rows": _rows()}


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
def alt_index():
    r = subprocess.run(["git", "-C", WURZEL, "show", ALT_REF + ":index.html"], capture_output=True)
    if r.returncode != 0:
        pytest.skip("Altstand %s nicht im Repo" % ALT_REF)
    return r.stdout


def _seite(browser, url, breite, hoehe, index_body=None):
    schreib = []

    def rest(route):
        req = route.request
        if req.method == "OPTIONS":
            return route.fulfill(status=204, headers={"Access-Control-Allow-Origin": "*"})
        pu = urllib.parse.urlparse(req.url)
        if req.method in ("GET", "HEAD"):
            tab = pu.path.split("/rest/v1/")[-1]
            return route.fulfill(status=200, content_type="application/json", body=json.dumps(TABELLEN.get(tab, [])))
        schreib.append(req.method + " " + pu.path)
        return route.fulfill(status=200, content_type="application/json", body="[]")

    ctx = browser.new_context(viewport={"width": breite, "height": hoehe}, service_workers="block")
    ctx.add_init_script(INIT)
    ctx.route("**/auth/v1/**", lambda r: r.abort())
    ctx.route("**/functions/v1/**", lambda r: r.abort())
    ctx.route("**/rest/v1/**", rest)
    if index_body is not None:
        ctx.route("**/index.html", lambda r: r.fulfill(status=200, content_type="text/html; charset=utf-8", body=index_body))
    s = ctx.new_page()
    s.clock.set_fixed_time(UHR)
    fehler = []
    s.on("pageerror", lambda e: fehler.append(str(e)[:200]))
    s.goto(url, wait_until="domcontentloaded")
    s.wait_for_function("() => [...document.querySelectorAll('.bottom-nav button, .tab-bar button')].some(b => b.getBoundingClientRect().height > 0)", timeout=40000)
    return ctx, s, schreib, fehler


# Planung oeffnen: am Handy ueber die Gruppe "Zeit" (Klick wechselt innerhalb der Gruppe), am PC ueber die Seitenleiste.
ZUR_PLANUNG = r"""() => {
  const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const t = b => (b.getAttribute('title') || b.getAttribute('aria-label') || b.innerText || '').replace(/\s+/g, ' ').trim();
  const kn = [...document.querySelectorAll('button, a')].filter(vis);
  const p = kn.find(b => b.closest('.tab-bar') && b.getAttribute('aria-label') === 'Planung');
  if (p) { p.click(); return 'planung'; }
  const z = kn.find(b => b.closest('.bottom-nav') && b.getAttribute('title') === 'Zeit');
  if (z) { z.click(); return 'zeit'; }
  return '';
}"""

IST_PLANUNG = r"""() => /KW\s*48\s*\/\s*2026/.test(document.body.innerText) && /Monteure, Baustellen/.test(document.body.innerText)"""


def _planung(s):
    for _ in range(8):
        if s.evaluate(IST_PLANUNG):
            break
        s.evaluate(ZUR_PLANUNG)
        try:
            s.wait_for_function(IST_PLANUNG, timeout=1500)
        except Exception:
            pass
    assert s.evaluate(IST_PLANUNG), "Wochenplanung KW 48 nicht erreicht"


# Namens-Elemente der Handy-Tageszellen: die Spanne mit title == aria-label == voller Name.
NAMEN = """(namen) => [...document.querySelectorAll('span[title][aria-label]')]
  .filter(e => namen.includes(e.getAttribute('title')) && e.getAttribute('aria-label') === e.getAttribute('title') && e.getBoundingClientRect().width > 0)
  .map(e => { const zelle = e.parentElement.closest('div[style*="min-height: 42px"]') || e.parentElement;
    return {voll: e.getAttribute('title'), text: e.textContent, sw: e.scrollWidth, cw: e.clientWidth,
            w: Math.round(e.getBoundingClientRect().width), zelle: [...(zelle.parentElement ? zelle.parentElement.children : [])].indexOf(zelle),
            karte: (e.closest('div[style*="border-radius: 10px"]') || {}).textContent ? e.closest('div[style*="border-radius: 10px"]').textContent.slice(0, 30) : ''}; })"""


def _messe_handy(browser, url, index_body=None):
    ctx, s, schreib, fehler = _seite(browser, url, 390, 844, index_body)
    try:
        _planung(s)
        voll = [w["name"] for w in WORKERS]
        s.wait_for_function("(n) => document.querySelectorAll('span[title][aria-label]').length && [...document.querySelectorAll('span[title][aria-label]')].some(e => n.includes(e.getAttribute('title')))", arg=voll, timeout=15000)
        m = s.evaluate(NAMEN, voll)
        return m, schreib, fehler
    finally:
        ctx.close()


def _abgeschnitten(m):
    return [x for x in m if x["sw"] > x["cw"] + 1]


def _pruefe_handy(m):
    assert len(m) >= 4, "zu wenige Namens-Elemente gefunden (%d) - die Messung misst sonst nichts" % len(m)
    zellen = {}
    for x in m:
        zellen.setdefault((x["karte"], x["zelle"]), []).append(x)
    assert any(len(v) >= 2 for v in zellen.values()), "keine Tageszelle mit zwei Namen - Probe ohne Aussage"
    ab = _abgeschnitten(m)
    assert not ab, ("\U0001F534 %d Namen in den Tageszellen abgeschnitten (390 px), z. B. %s"
                    % (len(ab), ["%s: '%s' %d>%d" % (x["voll"], x["text"], x["sw"], x["cw"]) for x in ab[:4]]))
    for k, v in zellen.items():
        texte = [x["text"] for x in v]
        assert len(set(texte)) == len(texte), "Zelle %s: gleiche sichtbare Namen %s" % (k, texte)


def test_handy_namen_nicht_abgeschnitten(browser, server, alt_index):
    body = alt_index if os.environ.get("EPK_PLAN_ALT") == "1" else None
    m, schreib, fehler = _messe_handy(browser, server, body)
    assert not fehler, "Seitenfehler: %s" % fehler[:3]
    assert not schreib, "Die Ansicht hat geschrieben: %s" % schreib[:3]
    _pruefe_handy(m)


def test_umkehr_altstand_schneidet_ab(browser, server, alt_index):
    """Dieselbe Pruefung gegen 1f3791c muss anschlagen - sonst misst sie nichts."""
    m, _, _ = _messe_handy(browser, server, alt_index)
    with pytest.raises(AssertionError) as e:
        _pruefe_handy(m)
    assert "abgeschnitten" in str(e.value), str(e.value)[:300]


# PC 1280: Planungstabelle - Zellbreiten und Namensstil (darf sich durch die Kur nicht aendern).
PC_MESS = """() => { const t = document.querySelector('[data-wp-plan]'); if (!t) return null;
  const tds = [...t.querySelectorAll('tbody tr')].slice(0, 2).map(tr => [...tr.children].map(td => Math.round(td.getBoundingClientRect().width)));
  const sp = [...t.querySelectorAll('span[title]')].filter(e => e.getBoundingClientRect().width > 0).slice(0, 6).map(e => { const c = getComputedStyle(e);
    return [e.textContent, c.whiteSpace, c.textOverflow, c.fontSize, Math.round(e.getBoundingClientRect().width)]; });
  return {tds: tds, namen: sp, mobil: document.querySelectorAll('[data-wp-tage-mobil]').length}; }"""


def _messe_pc(browser, url, index_body=None):
    ctx, s, _, fehler = _seite(browser, url, 1280, 800, index_body)
    try:
        _planung(s)
        s.wait_for_function("() => { const t = document.querySelector('[data-wp-plan]'); return t && t.querySelectorAll('span[title]').length > 0; }", timeout=15000)
        return s.evaluate(PC_MESS), fehler
    finally:
        ctx.close()


def test_pc_1280_unveraendert(browser, server, alt_index):
    neu, f1 = _messe_pc(browser, server)
    alt, f2 = _messe_pc(browser, server, alt_index)
    assert neu and alt, "Planungstabelle bei 1280 px nicht gefunden"
    assert not f1, f1[:3]
    assert neu["mobil"] == 0, "Handy-Raster erscheint am PC"
    assert neu["namen"], "keine Namen in der Planungstabelle - Vergleich ohne Aussage"
    assert neu["tds"] == alt["tds"], "Zellbreiten 1280 px geaendert: %s gegen %s" % (neu["tds"], alt["tds"])
    assert neu["namen"] == alt["namen"], "Namensstil 1280 px geaendert: %s gegen %s" % (neu["namen"], alt["namen"])
