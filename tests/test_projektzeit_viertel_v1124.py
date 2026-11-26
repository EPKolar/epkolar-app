# -*- coding: utf-8 -*-
"""Projektzeit Von/Bis nur in Viertelstunden waehlbar (v3.9.1124) - im ECHTEN Browser.

Befund GF 26.11.2026 (Handy, Monteur, "Eintrag bearbeiten"): Von/Bis waren <input type=time step=900>. step ist auf
Android/iOS nur ein Hinweis - die Geraete-Uhr bot jede Minute (06:27), "Von nur in Viertelstunden" kam erst beim
Speichern. GF: "Uhr unpraktisch, besser machen". Entscheidung 24.11. gilt weiter: nur 15-min-EINGABE, KEINE Rundung,
keine Vorschlaege, keine Vorbelegung.

Kur: app-eigene Auswahl ViertelZeitWahl (Handy: Blatt von unten; Tablet/PC: Klappfeld am Feld; PC zusaetzlich
Tastatur, die nur 00/15/30/45 annimmt). Stunde antippen, Minute antippen -> Wert steht im Feld, kein "Festlegen".
Alte krumme Werte (07:25) bleiben sichtbar mit "Bitte Viertelstunde wählen" und werden nie still geaendert.
Stempelzeiten und die Stundenrechnung sind nicht beruehrt.

Gemessen wird die ganze App (Chromium, Playwright), Supabase abgefangen - nichts verlaesst den Rechner.
Jede Messung liefert eine Liste von Maengeln (leer = gruen). Die Umkehrproben am Ende bauen den Fehler gezielt in
eine KOPIE der Datei ein (Minute 25 waehlbar / still runden / Geraete-Uhr zurueck) und verlangen, dass die
Messung ihn findet - ein Test, der nie rot werden kann, schuetzt nichts.
"""
import functools
import http.server
import io
import json
import os
import re
import socketserver
import threading
import urllib.parse

import pytest

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sync_api = pytest.importorskip("playwright.sync_api")

UHR = "2026-11-26T09:00:00"
WORKERS = [{"id": "w1", "name": "Monteur Eins", "role": "Monteur", "eintritt": "2020-01-01"}]
PROJECTS = [{"id": "p1", "name": "Muster Wohnhausanlage Nord", "nr": "2026-014", "status": "aktiv"}]
# Alter Eintrag mit krummer Von-Zeit (vor der 15-min-Regel gebucht).
ENTRIES = [{"id": "te1", "worker_id": "w1", "project_id": "p1", "date": "2026-11-26", "hours": 8.33,
            "taetigkeit": "Montage", "von": "07:25", "bis": "16:15", "pause": 0.5, "gewerk": "elektro", "bemerkung": ""}]
USER = {"id": "7", "name": "Monteur Eins", "username": "m1", "email": "m@x", "role": "monteur", "active": True,
        "monteur_id": "w1", "permissions": [], "perms_override": {}, "locked": False}
TABELLEN = {"workers": WORKERS, "users": [USER], "projects": PROJECTS, "time_entries": ENTRIES}

INIT = """
try{
  var b=function(s){return btoa(s).replace(/=+$/,'');};
  var jwt=b(JSON.stringify({alg:"HS256",typ:"JWT"}))+"."+b(JSON.stringify({sub:"7",role:"authenticated",exp:Math.floor(Date.now()/1000)+86400}))+".sig";
  localStorage.setItem('epkolar_auth',JSON.stringify({at:jwt,rt:"r",exp:Date.now()+86400000}));
  localStorage.setItem('epkolar_user',JSON.stringify({id:"7",username:"m1",name:"Monteur Eins",role:"monteur",monteur_id:"w1",permissions:[],perms_override:{}}));
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


def _dialog(browser, url, breite, hoehe, beruehrung, index_body=None):
    """App als Monteur laden, Zeiterfassung oeffnen, den alten Eintrag (07:25) bearbeiten."""
    schreib = []

    def rest(route):
        req = route.request
        if req.method == "OPTIONS":
            return route.fulfill(status=204, headers={"Access-Control-Allow-Origin": "*"})
        pu = urllib.parse.urlparse(req.url)
        if req.method in ("GET", "HEAD"):
            tab = pu.path.split("/rest/v1/")[-1]
            return route.fulfill(status=200, content_type="application/json", body=json.dumps(TABELLEN.get(tab, [])))
        schreib.append({"m": req.method, "pfad": pu.path, "body": req.post_data or ""})
        return route.fulfill(status=200, content_type="application/json", body="[]")

    ctx = browser.new_context(viewport={"width": breite, "height": hoehe}, service_workers="block",
                              has_touch=beruehrung, is_mobile=beruehrung)
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
    for _ in range(8):
        if s.evaluate("() => !!document.querySelector('[aria-label=\"Eintrag bearbeiten\"]')"):
            break
        s.evaluate(r"""() => { const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
          const t = b => (b.getAttribute('title') || b.getAttribute('aria-label') || b.innerText || '').trim();
          const kn = [...document.querySelectorAll('button, a, [role=tab]')].filter(vis);
          const z = kn.find(b => t(b) === 'Zeiterfassung') || kn.find(b => t(b) === 'Zeit'); if (z) z.click(); }""")
        s.wait_for_timeout(1500)
    s.click('[aria-label="Eintrag bearbeiten"]')
    s.wait_for_selector('[data-vzw="Von"], input[type="time"]', timeout=10000)
    return ctx, s, schreib, fehler


def _oeffne(s, feld):
    knopf = s.query_selector('button[data-vzw-feld="%s"]' % feld) or s.query_selector('[aria-label="%s auswählen"]' % feld)
    assert knopf, "Auswahl-Knopf fuer %s fehlt" % feld
    knopf.click()
    s.wait_for_selector('[data-vzw-panel="%s"]' % feld, timeout=5000)


PANEL = r"""(feld) => { const p = document.querySelector('[data-vzw-panel="' + feld + '"]'); if (!p) return null;
  const r = p.getBoundingClientRect();
  const opt = sel => [...p.querySelectorAll(sel)].map(o => ({t: o.textContent.trim(), sel: o.getAttribute('aria-selected'),
     h: Math.round(o.getBoundingClientRect().height), lb: (o.closest('[role=listbox]') || {getAttribute: () => ''}).getAttribute('aria-label')}));
  return {rolle: p.getAttribute('role'), name: p.getAttribute('aria-label'), unten: Math.round(window.innerHeight - r.bottom),
          breite: Math.round(r.width), links: Math.round(r.left), minuten: opt('[data-vzw-minute]'), stunden: opt('[data-vzw-stunde]'),
          listen: [...p.querySelectorAll('[role=listbox]')].map(l => l.getAttribute('aria-label'))}; }"""

ZEIT_FELDER = r"""() => [...document.querySelectorAll('input[type="time"]')].filter(i => i.getBoundingClientRect().width > 0).length"""
FELD = r"""(feld) => { const w = document.querySelector('[data-vzw="' + feld + '"]'); if (!w) return null;
  const k = w.querySelector('[data-vzw-feld]'); const h = [...w.querySelectorAll('[data-vzw-hinweis]')].map(x => x.getAttribute('data-vzw-hinweis') + ':' + x.textContent.trim());
  return {text: k ? (k.tagName === 'INPUT' ? k.value : k.textContent.trim()) : '', hinweise: h}; }"""
STUNDEN = r"""() => { const e = [...document.querySelectorAll('input')].find(i => i.readOnly && /Von\/Bis/.test(i.title || '')); return e ? e.value : null; }"""


# ── Messungen: jede liefert eine Maengelliste ────────────────────────────────
def _messe_auswahl(browser, url, index_body=None):
    """(i) Handy 390x844: es gibt nur die Minuten 00/15/30/45, keine Geraete-Uhr, Tippziele >= 44 px."""
    ctx, s, schreib, fehler = _dialog(browser, url, 390, 844, True, index_body)
    m = []
    try:
        n_uhr = s.evaluate(ZEIT_FELDER)
        if n_uhr:
            m.append("Geraete-Uhr: %d sichtbare input[type=time] im Dialog" % n_uhr)
            return m
        _oeffne(s, "Von")
        p = s.evaluate(PANEL, "Von")
        minuten = [o["t"] for o in p["minuten"]]
        if minuten != ["00", "15", "30", "45"]:
            m.append("Minuten waehlbar: %s" % minuten)
        if p["rolle"] != "dialog" or not p["name"]:
            m.append("Blatt ohne role=dialog/aria-label")
        if p["unten"] > 2:
            m.append("Handy: kein Blatt von unten (Abstand unten %d px)" % p["unten"])
        if sorted(set(p["listen"])) != ["Minute", "Stunde"]:
            m.append("Auswahllisten ohne Namen: %s" % p["listen"])
        tag = [o["t"] for o in p["stunden"]]
        if tag != ["%02d" % h for h in range(5, 20)]:
            m.append("Stunden ohne Wischen nicht 05-19: %s" % tag)
        if [o["t"] for o in p["stunden"] if o["sel"] == "true"] != ["07"]:
            m.append("aktuelle Stunde nicht hervorgehoben")
        klein = [o["t"] for o in p["stunden"] + p["minuten"] if o["h"] < 44]
        if klein:
            m.append("Tippziele unter 44 px: %s" % klein)
        s.click('[data-vzw-nacht]')
        nacht = [o["t"] for o in s.evaluate(PANEL, "Von")["stunden"]]
        if sorted(nacht) != ["%02d" % h for h in range(24)]:
            m.append("Nachtstunden nicht erreichbar: %s" % nacht)
        if fehler:
            m.append("JS-Fehler: %s" % fehler[:2])
    finally:
        ctx.close()
    return m


def _messe_alter_wert(browser, url, index_body=None):
    """(ii) Alter Eintrag 07:25: bleibt ohne Zutun sichtbar und unveraendert (Anzeige UND gespeicherte Nutzlast);
    erst die bewusste Wahl 07 + 30 aendert ihn - das Blatt schliesst ohne 'Festlegen'. Bis vor Von meldet sich am Feld."""
    ctx, s, schreib, fehler = _dialog(browser, url, 390, 844, True, index_body)
    m = []
    try:
        if s.evaluate(ZEIT_FELDER):
            m.append("Geraete-Uhr im Dialog")
            return m
        s.wait_for_timeout(500)
        f = s.evaluate(FELD, "Von")
        if f["text"] != "07:25":
            m.append("alter Wert still geaendert: Feld zeigt %r statt '07:25'" % f["text"])
        if not any(h.startswith("krumm:") and "Viertelstunde" in h for h in f["hinweise"]):
            m.append("kein Hinweis 'bitte Viertelstunde wählen' am alten Wert")
        # Blatt oeffnen und ohne Wahl schliessen -> nichts geaendert
        _oeffne(s, "Von")
        s.keyboard.press("Escape")
        s.wait_for_timeout(300)
        if s.query_selector('[data-vzw-panel]'):
            m.append("Escape schliesst das Blatt nicht")
        if s.evaluate(FELD, "Von")["text"] != "07:25":
            m.append("Oeffnen/Schliessen hat den Wert geaendert")
        if not s.query_selector('[data-vzw-panel]') and s.query_selector('[data-vzw="Von"]'):
            if s.evaluate("() => document.activeElement && document.activeElement.getAttribute('data-vzw-feld')") != "Von":
                m.append("Fokus nach Escape nicht zurueck am Feld")
        # Unveraendert speichern: Nutzlast traegt 07:25 (die Speicherpruefung laesst alte Werte unveraendert durch)
        s.click("text=Änderungen speichern")
        for _ in range(20):
            if any("time_entries" in w["pfad"] for w in schreib):
                break
            s.wait_for_timeout(250)
        te = [w for w in schreib if "time_entries" in w["pfad"]]
        if not te:
            m.append("Speichern ohne Aenderung schrieb nichts - Messung ohne Aussage")
        else:
            body = te[-1]["body"]
            if '"von":"07:25"' not in body.replace(" ", ""):
                m.append("gespeicherte Nutzlast hat Von veraendert: %s" % body[:160])
        if fehler:
            m.append("JS-Fehler: %s" % fehler[:2])
    finally:
        ctx.close()
    return m


def _messe_bewusste_wahl(browser, url, index_body=None):
    ctx, s, schreib, fehler = _dialog(browser, url, 390, 844, True, index_body)
    m = []
    try:
        if s.evaluate(ZEIT_FELDER):
            return ["Geraete-Uhr im Dialog"]
        _oeffne(s, "Von")
        s.click('[data-vzw-panel="Von"] [data-vzw-stunde="07"]')
        if not s.query_selector('[data-vzw-panel="Von"]'):
            m.append("Blatt schliesst schon nach der Stunde")
        s.click('[data-vzw-panel="Von"] [data-vzw-minute="30"]')
        s.wait_for_timeout(300)
        if s.query_selector('[data-vzw-panel]'):
            m.append("Blatt schliesst nach Stunde+Minute nicht (braucht 'Festlegen')")
        f = s.evaluate(FELD, "Von")
        if f["text"] != "07:30":
            m.append("Wahl 07+30 ergab %r" % f["text"])
        if any(h.startswith("krumm:") for h in f["hinweise"]):
            m.append("Hinweis bleibt nach gueltiger Wahl")
        std = s.evaluate(STUNDEN)
        if std not in ("8,25", "8.25"):
            m.append("Stunden nicht aus Von/Bis/Pause gerechnet: %r" % std)
        # Bis vor Von: Meldung sofort am Bis-Feld
        _oeffne(s, "Bis")
        s.click('[data-vzw-panel="Bis"] [data-vzw-stunde="06"]')
        s.click('[data-vzw-panel="Bis"] [data-vzw-minute="00"]')
        s.wait_for_timeout(300)
        if not any(h.startswith("bisvorvon:") for h in s.evaluate(FELD, "Bis")["hinweise"]):
            m.append("Bis vor Von wird nicht am Feld gemeldet")
        if schreib:
            m.append("Auswahl hat geschrieben: %s" % schreib[:1])
    finally:
        ctx.close()
    return m


def _messe_tablet_pc(browser, url, index_body=None):
    """Tablet 1280x800 (Beruehrung): Klappfeld am Feld, gleiche Minuten. PC (Maus): Tastatur nimmt nur 00/15/30/45."""
    m = []
    ctx, s, schreib, fehler = _dialog(browser, url, 1280, 800, True, index_body)
    try:
        if s.evaluate(ZEIT_FELDER):
            return ["Geraete-Uhr im Tablet-Dialog"]
        _oeffne(s, "Von")
        p = s.evaluate(PANEL, "Von")
        if [o["t"] for o in p["minuten"]] != ["00", "15", "30", "45"]:
            m.append("Tablet-Minuten: %s" % [o["t"] for o in p["minuten"]])
        if p["breite"] > 400 or p["unten"] < 4:
            m.append("Tablet: kein Klappfeld am Feld (Breite %d, unten %d)" % (p["breite"], p["unten"]))
    finally:
        ctx.close()
    ctx, s, schreib, fehler = _dialog(browser, url, 1280, 800, False, index_body)
    try:
        if s.evaluate(ZEIT_FELDER):
            return m + ["Geraete-Uhr im PC-Dialog"]
        feld = s.query_selector('input[data-vzw-feld="Von"]')
        if not feld:
            return m + ["PC: kein Tastaturfeld"]
        feld.fill("07:20")
        feld.press("Enter")
        s.wait_for_timeout(200)
        f = s.evaluate(FELD, "Von")
        if f["text"] != "07:25" or not any(h.startswith("tipp:") for h in f["hinweise"]):
            m.append("PC: 07:20 nicht abgewiesen (Feld %r, Hinweise %s)" % (f["text"], f["hinweise"]))
        feld.fill("0745")
        feld.press("Enter")
        s.wait_for_timeout(200)
        f = s.evaluate(FELD, "Von")
        if f["text"] != "07:45" or f["hinweise"]:
            m.append("PC: 0745 nicht als 07:45 angenommen (Feld %r, Hinweise %s)" % (f["text"], f["hinweise"]))
        # Tastatur in der Auswahl: Fokus im Klappfeld, Pfeil rechts, Enter waehlt die Stunde
        s.click('[aria-label="Von auswählen"]')
        s.wait_for_selector('[data-vzw-panel="Von"]')
        if s.evaluate("() => document.activeElement && document.activeElement.getAttribute('data-vzw-stunde')") != "07":
            m.append("PC: Fokus nicht auf der aktuellen Stunde")
        s.keyboard.press("ArrowRight")
        s.keyboard.press("Enter")
        s.keyboard.press("Tab")
        s.wait_for_timeout(100)
        s.evaluate("() => { const b = document.querySelector('[data-vzw-panel] [data-vzw-minute=\"15\"]'); if (b) b.focus(); }")
        s.keyboard.press("Enter")
        s.wait_for_timeout(200)
        if s.evaluate(FELD, "Von")["text"] != "08:15":
            m.append("PC: Tastaturwahl 08:15 ergab %r" % s.evaluate(FELD, "Von")["text"])
    finally:
        ctx.close()
    return m


# ── Tests ────────────────────────────────────────────────────────────────────
def test_nur_viertelstunden_waehlbar_handy(browser, server):
    assert _messe_auswahl(browser, server) == []


def test_alter_krummer_wert_bleibt_ohne_zutun(browser, server):
    assert _messe_alter_wert(browser, server) == []


def test_bewusste_wahl_schliesst_und_rechnet(browser, server):
    assert _messe_bewusste_wahl(browser, server) == []


def test_tablet_klappfeld_und_pc_tastatur(browser, server):
    assert _messe_tablet_pc(browser, server) == []


def test_keine_geraete_uhr_an_projektzeit(quelle):
    """Quelltext: in beiden Erfassungsdialogen (VZeit, ZeiterfassungView) haengen Von/Bis an ViertelZeitWahl,
    kein type=time und kein showPicker. Stempelzeiten bleiben eigene Regel (5 min)."""
    assert quelle.count('React.createElement(ViertelZeitWahl,{feld:"Von",isMob:isMob,value:addVon,') == 2
    assert quelle.count('React.createElement(ViertelZeitWahl,{feld:"Bis",gegenVon:addVon,isMob:isMob,value:addBis,') == 2
    assert not re.search(r"type:\s*['\"]time['\"][^)]{0,40}value:\s*add(Von|Bis)", quelle)
    assert "showPicker" not in quelle
    assert 'var VZW_MINUTEN=["00","15","30","45"];' in quelle
    assert "const STEMPEL_ROUND_MIN=5;" in quelle
    assert "const ZEIT_RASTER_MIN=1;" in quelle  # keine Auto-Rundung (GF 24.11.)


# ── Umkehrproben: der eingebaute Fehler MUSS gefunden werden ────────────────
def _kaputt(quelle, alt, neu):
    assert quelle.count(alt) >= 1, alt
    return quelle.replace(alt, neu).encode("utf-8")


def test_umkehr_minute_25_waehlbar(browser, server, quelle):
    k = _kaputt(quelle, 'var VZW_MINUTEN=["00","15","30","45"];', 'var VZW_MINUTEN=["00","15","25","30","45"];')
    assert any(x.startswith("Minuten waehlbar") for x in _messe_auswahl(browser, server, k))


def test_umkehr_geraete_uhr_zurueck(browser, server, quelle):
    k = _kaputt(quelle, 'React.createElement(ViertelZeitWahl,{feld:"Von",isMob:isMob,value:addVon,',
                'React.createElement(\'input\',{type:"time",step:900,value:addVon,')
    assert any(x.startswith("Geraete-Uhr") for x in _messe_auswahl(browser, server, k))


def test_umkehr_still_gerundet(browser, server, quelle):
    # Auto-Rundung beim Anzeigen: 07:25 -> 07:30 ohne Zutun. Muss als "still geaendert" auffallen.
    k = _kaputt(quelle, "function melde(v){var ev={target:{value:v}};if(props.onChange)props.onChange(ev);if(props.onBlur)props.onBlur(ev);}",
                "function melde(v){var ev={target:{value:v}};if(props.onChange)props.onChange(ev);if(props.onBlur)props.onBlur(ev);}"
                "React.useEffect(function(){if(krumm)melde(_vzw2(hAkt)+':'+_vzw2(Math.round((wv%60)/15)*15%60));},[wert]);")
    m = _messe_alter_wert(browser, server, k)
    assert any("still geaendert" in x for x in m) and any("Nutzlast" in x for x in m), m
