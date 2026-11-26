# -*- coding: utf-8 -*-
"""v3.9.1126 Arbeitsscheine: Sicht der Feldrollen auf erledigte und abgerechnete Scheine - EIN Schalter.

GF 26.11. abends (woertlich): "erledigte und abgerechnete as soll der monteur nicht mehr sehen".
GF-Nachtrag: das WIE entscheidet er selbst. Darum ein Schalter AS_FELD_SICHT={modus,tage}:
  "alle"        Standard, bisheriges Verhalten (nichts versteckt) - der Commit aendert ohne Umstellen nichts Sichtbares
  "sofort"      erledigt + abgerechnet sofort weg
  "nach_tagen"  abgerechnet sofort weg, erledigt erst nach `tage` Tagen (Stichtag abschlussDatum,
                sonst juprowa_sync_at, sonst local_updated_at - Ersatzwert)
  "eingeklappt" erledigt + abgerechnet in einem zugeklappten Abschnitt "Erledigt" am Ende der Liste
Feldrollen = monteur, helfer, techniker, obermonteur. Admin, Buero, Projektleitung sehen immer alles.

Geprueft wird ECHTER Code: node (Helfer aus index.html ausgeschnitten) und Chromium (Playwright,
Offline-Sitzung, /rest/v1 abgefangen, Testnamen). Die Varianten werden ueber den Schalter in einer
Kopie von index.html gesetzt - genau die eine Zeile, die der GF spaeter aendert.
Umkehrproben: Helfer neutralisiert -> rot; Beschriftung ueber gefilterte Liste -> rot.
"""
import functools
import http.server
import io
import json
import os
import socketserver
import subprocess
import threading

import pytest

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(WURZEL, "index.html")
SCHALTER = 'const AS_FELD_SICHT={modus:"alle",tage:7};'

ROLLEN_ALLE = ["admin", "buero", "projektleiter"]
ROLLEN_FELD = ["monteur", "techniker", "helfer", "obermonteur"]
STATUS = ["aufgenommen", "freigegeben", "in_bearbeitung", "aufgeschoben", "erledigt", "abgerechnet", "bar_bezahlt", "storniert"]


def _html():
    return io.open(HTML, encoding="utf-8", newline="").read()


def _mit_modus(s, modus, tage=7):
    assert s.count(SCHALTER) == 1, "Schalter-Zeile nicht genau einmal da"
    return s.replace(SCHALTER, 'const AS_FELD_SICHT={modus:"%s",tage:%d};' % (modus, tage))


def _neutralisiert(s):
    """Altverhalten: Helfer bleibt aufrufbar, filtert aber nichts."""
    alt = 'function _asFuerRolle(list,role){var l=Array.isArray(list)?list:[];return (_asIstFeldrolle(role)&&AS_FELD_SICHT.modus!=="alle")?l.filter(function(a){return !_asFeldVerborgen(a,role);}):l;}'
    assert s.count(alt) == 1
    s = s.replace(alt, 'function _asFuerRolle(list,role){return Array.isArray(list)?list:[];}')
    alt2 = 'function _asFeldSichtbar(a,role){return !_asFeldVerborgen(a,role);}'
    assert s.count(alt2) == 1
    return s.replace(alt2, 'function _asFeldSichtbar(a,role){return true;}')


def test_standard_ist_alle():
    assert _html().count(SCHALTER) == 1


# ---------------------------------------------------------------- node: Helfer je Modus x Rolle x Status

JETZT = "2026-11-23T09:00:00Z"
FAELLE = [  # (id, status, Stichtag-Felder)
    ("auf", "aufgenommen", {}),
    ("frei", "freigegeben", {}),
    ("bearb", "in_bearbeitung", {}),
    ("aufg", "aufgeschoben", {}),
    ("erl_neu", "erledigt", {"juprowa_sync_at": "2026-11-20T10:00:00Z"}),       # 3 Tage
    ("erl_alt", "erledigt", {"juprowa_sync_at": "2026-11-01T10:00:00Z"}),       # 22 Tage
    ("erl_absch", "erledigt", {"abschlussDatum": "2026-11-22", "juprowa_sync_at": "2026-10-01T00:00:00Z"}),  # abschlussDatum gewinnt
    ("erl_ohne", "erledigt", {}),                                                # kein Datum -> versteckt
    ("abger", "abgerechnet", {"juprowa_sync_at": "2026-11-22T10:00:00Z"}),
    ("bar", "bar_bezahlt", {}),
    ("storno", "storniert", {}),
]
ALLE_IDS = [f[0] for f in FAELLE]
ERWARTET_FELD = {
    "alle": ALLE_IDS,
    "sofort": ["auf", "frei", "bearb", "aufg", "bar", "storno"],
    "eingeklappt": ["auf", "frei", "bearb", "aufg", "bar", "storno"],
    "nach_tagen": ["auf", "frei", "bearb", "aufg", "erl_neu", "erl_absch", "bar", "storno"],
}
ERWARTET_EKL = {"alle": [], "sofort": [], "nach_tagen": [], "eingeklappt": ["erl_neu", "erl_alt", "erl_absch", "erl_ohne", "abger"]}


def _helfer_js(s):
    i = s.index('const AS_FELD_SICHT=')
    j = s.index('if(typeof window!=="undefined"){window._asFuerRolle=', i)
    return s[i:j]


def _node(s):
    liste = [dict({"id": i, "scheinstatus": st}, **x) for i, st, x in FAELLE]
    js = "var TIME_DAY=24*60*60*1000;" + _helfer_js(s) + """
var ROL=%s, L=%s, ST=%s; Date.now=function(){return Date.parse("%s");}; var out={};
ROL.forEach(function(r){out[r]={sicht:_asFuerRolle(L,r).map(function(a){return a.id;}),
  einzel:L.filter(function(a){return _asFeldSichtbar(a,r);}).map(function(a){return a.id;}),
  ekl:_asEingeklappt(L,r).map(function(a){return a.id;}),
  status:ST.filter(function(st){return !_asFeldStatusVerborgen(st,r);})};});
out._leer=_asFuerRolle(null,"monteur").length+_asEingeklappt(undefined,"monteur").length;
process.stdout.write(JSON.stringify(out));
""" % (json.dumps(ROLLEN_ALLE + ROLLEN_FELD + ["", "viewer"]), json.dumps(liste), json.dumps(STATUS), JETZT)
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr[:500]
    return json.loads(r.stdout)


def _pruefe(m, modus):
    for r in ROLLEN_ALLE + ["", "viewer"]:
        assert m[r]["sicht"] == ALLE_IDS and m[r]["einzel"] == ALLE_IDS, (modus, r, m[r])
        assert m[r]["ekl"] == [] and m[r]["status"] == STATUS, (modus, r, m[r])
    for r in ROLLEN_FELD:
        assert m[r]["sicht"] == ERWARTET_FELD[modus], (modus, r, m[r])
        if modus == "alle":
            assert m[r]["einzel"] == ALLE_IDS, (modus, r, m[r])
        else:
            assert m[r]["einzel"] == ERWARTET_FELD[modus], (modus, r, m[r])
        assert m[r]["ekl"] == ERWARTET_EKL[modus], (modus, r, m[r])
        verb = {"alle": set(), "sofort": {"erledigt", "abgerechnet"}, "eingeklappt": {"erledigt", "abgerechnet"},
                "nach_tagen": {"abgerechnet"}}[modus]
        assert m[r]["status"] == [st for st in STATUS if st not in verb], (modus, r, m[r])
    assert m["_leer"] == 0


@pytest.mark.parametrize("modus", ["alle", "sofort", "nach_tagen", "eingeklappt"])
def test_helfer_je_modus_rolle_status(modus):
    _pruefe(_node(_mit_modus(_html(), modus)), modus)


def test_nach_tagen_grenze_und_tage_einstellbar():
    m = _node(_mit_modus(_html(), "nach_tagen", 2))  # erl_neu ist 3 Tage alt -> jetzt weg, erl_absch (1 Tag) bleibt
    assert m["monteur"]["sicht"] == ["auf", "frei", "bearb", "aufg", "erl_absch", "bar", "storno"], m["monteur"]
    m = _node(_mit_modus(_html(), "nach_tagen", 30))  # alle datierten erledigten bleiben, nur ohne Datum weg
    assert m["monteur"]["sicht"] == ["auf", "frei", "bearb", "aufg", "erl_neu", "erl_alt", "erl_absch", "bar", "storno"], m["monteur"]


def test_umkehrprobe_helfer_neutralisiert_ist_rot():
    with pytest.raises(AssertionError):
        _pruefe(_node(_neutralisiert(_mit_modus(_html(), "sofort"))), "sofort")


def test_helfer_wird_an_allen_anzeigestellen_benutzt():
    s = _html()
    assert s.count("_asFuerRolle(arbeitsscheine,curUser.role)") == 2  # ArbeitsscheinView + Home
    assert s.count("_asFuerRolle(arbeitsscheine,curUser&&curUser.role)") == 1  # globale Suche
    assert "const filtered=_react.useMemo.call(void 0, ()=>_asSicht.filter(" in s
    assert "const calAs=_react.useMemo.call(void 0, ()=>_asSicht.filter(" in s
    assert "a.id===addId||_asFeldSichtbar(a,curUser&&curUser.role)" in s
    # Beschriftung der Stundeneintraege + Speichern lesen die VOLLE Liste
    assert "const schein=asId?arbeitsscheine.find(s=>s.id===asId):null;" in s
    assert 'const s=arbeitsscheine.find(x=>x.id===addId);if(s){label=s.nummer+" — "+(s.kundName||"");asId=s.id;}' in s


# ---------------------------------------------------------------- Browser

sync_api = pytest.importorskip("playwright.sync_api")

UHR = "2026-11-23T09:00:00"  # Montag
ST_DATEN = ["aufgenommen", "freigegeben", "in_bearbeitung", "aufgeschoben", "erledigt", "abgerechnet", "erledigt", "abgerechnet", "storniert", "in_bearbeitung"]
SYNC = {4: "2026-11-21T10:00:00Z", 6: "2026-10-20T10:00:00Z"}  # S079004 frisch erledigt, S079006 alt erledigt
SCHEINE = [{"id": "A%d" % k, "nummer": "S0790%02d" % k, "kund_name": "Testkunde %d" % k, "arbeitsort": "Musterweg %d, 3500 Krems" % k,
            "monteur": "w1", "scheinstatus": st, "prioritaet": "normal", "push_pending": False, "juprowa_id": 500 + k,
            "juprowa_sync_at": SYNC.get(k, "2026-11-22T10:00:00Z"),
            "termin_bestaetigt": "2026-11-%02d" % (20 + k % 6), "arbeitsanweisungen": "Arbeit %d" % k, "scheinart": "kein"}
           for k, st in enumerate(ST_DATEN)]
NR_ALLE = sorted(x["nummer"] for x in SCHEINE)
NR_FERTIG = sorted(x["nummer"] for x in SCHEINE if x["scheinstatus"] in ("erledigt", "abgerechnet"))
NR_SOFORT = sorted(x["nummer"] for x in SCHEINE if x["scheinstatus"] not in ("erledigt", "abgerechnet"))
NR_NACH_TAGEN = sorted(NR_SOFORT + ["S079004"])
WORKERS = [{"id": "w1", "name": "Max Mustermann", "role": "Monteur"}]
EINTRAG = {"id": "e1", "worker_id": "w1", "date": "2026-11-23", "arbeitsschein_id": "A5", "hours": 2,
           "von": "07:00", "bis": "09:00", "pause": 0, "taetigkeit": "Montage"}  # auf einem ABGERECHNETEN Schein

INIT = """
try{
  var b=function(s){return btoa(s).replace(/=+$/,'');};
  var jwt=b(JSON.stringify({alg:"HS256",typ:"JWT"}))+"."+b(JSON.stringify({sub:"1",role:"authenticated",exp:Math.floor(Date.now()/1000)+86400}))+".sig";
  localStorage.setItem('epkolar_auth',JSON.stringify({at:jwt,rt:"r",exp:Date.now()+86400000}));
  localStorage.setItem('epkolar_user',JSON.stringify({id:"1",username:"mm",name:"Max Mustermann",role:"__ROLLE__",monteurId:"w1",monteur_id:"w1",permissions:[],perms_override:{}}));
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


def _seite(browser, url, rolle, index_body=None):
    user = {"id": "1", "name": "Max Mustermann", "username": "mm", "email": "t@x", "role": rolle, "active": True,
            "monteur_id": "w1", "permissions": [], "perms_override": {}, "locked": False}
    schreib = []

    def rest(route):
        req = route.request
        u = req.url
        if req.method != "GET":
            schreib.append(req.method + " " + u.split("/rest/v1/")[-1])
            return route.fulfill(status=200, content_type="application/json", body="[]")
        if "/rest/v1/arbeitsscheine" in u:
            return route.fulfill(status=200, content_type="application/json",
                                 body=json.dumps([] if "push_pending=eq.true" in u else SCHEINE))
        if "/rest/v1/time_entries" in u:
            return route.fulfill(status=200, content_type="application/json", body=json.dumps([EINTRAG]))
        if "/rest/v1/users" in u:
            return route.fulfill(status=200, content_type="application/json", body=json.dumps([user]))
        if "/rest/v1/workers" in u:
            return route.fulfill(status=200, content_type="application/json", body=json.dumps(WORKERS))
        return route.fulfill(status=200, content_type="application/json", body="[]")

    ctx = browser.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
    ctx.add_init_script(INIT.replace("__ROLLE__", rolle))
    ctx.route("**/auth/v1/**", lambda r: r.abort())
    ctx.route("**/rest/v1/**", rest)
    if index_body is not None:
        ctx.route("**/index.html", lambda r: r.fulfill(status=200, content_type="text/html; charset=utf-8", body=index_body))
    s = ctx.new_page()
    s.clock.set_fixed_time(UHR)
    fehler = []
    s.on("pageerror", lambda e: fehler.append(str(e)[:200]))
    s.goto(url, wait_until="domcontentloaded")
    s.wait_for_timeout(4500)
    return ctx, s, fehler, schreib


NAV = """(w) => { const v = b => b.getBoundingClientRect().height > 0;
  const k = [...document.querySelectorAll('button[aria-label]')].filter(b => b.getAttribute('aria-label') === w && v(b));
  if (k.length) { k[0].click(); return 'aria'; }
  const t = [...document.querySelectorAll('button')].filter(b => (b.textContent || '').trim() === w && v(b));
  if (t.length) { t[0].click(); return 'text'; } return 'nicht-gefunden'; }"""

# "x von y Arbeitsscheine"; Nummern ausserhalb des eingeklappten Abschnitts; Zustand des Abschnitts
LISTE = """() => { const t = document.body.innerText; const m = t.match(/(\\d+) von (\\d+) Arbeitsscheine/);
  const ekl = document.querySelector('[data-as-eingeklappt]');
  const alle = [...new Set((document.body.textContent.match(/S0790\\d\\d/g) || []))];
  const inEkl = ekl ? [...new Set((ekl.textContent.match(/S0790\\d\\d/g) || []))] : [];
  return {von: m ? +m[1] : -1, gesamt: m ? +m[2] : -1, nr: alle.filter(n => inEkl.indexOf(n) < 0).sort(),
          ekl: ekl ? ekl.getAttribute('data-as-eingeklappt') : null, eklText: ekl ? ekl.innerText : '',
          eklNr: [...document.querySelectorAll('[data-as-ekl-nr]')].map(b => b.getAttribute('data-as-ekl-nr')).sort(),
          erledigtChip: [...document.querySelectorAll('button')].some(b => (b.textContent || '').trim() === 'Erledigt')}; }"""


def _liste(browser, server, rolle, index_body=None, aufklappen=False):
    ctx, s, fehler, schreib = _seite(browser, server, rolle, index_body)
    try:
        assert s.evaluate(NAV, "Arbeitsscheine") != "nicht-gefunden"
        s.wait_for_timeout(1500)
        r = s.evaluate(LISTE)
        if aufklappen:
            s.evaluate("() => document.querySelector('[data-as-eingeklappt] button').click()")
            s.wait_for_timeout(500)
            r["auf"] = s.evaluate(LISTE)
            s.evaluate("() => document.querySelector('[data-as-ekl-nr=\"S079005\"]').click()")
            s.wait_for_timeout(800)
            r["formular"] = s.evaluate("() => document.body.innerText.indexOf('abgeschlossen') >= 0")
        r["fehler"] = fehler
        r["schreib"] = schreib
        return r
    finally:
        ctx.close()


def test_standard_monteur_sieht_alles_wie_bisher(browser, server):
    r = _liste(browser, server, "monteur")
    assert r["fehler"] == [] and r["schreib"] == [], r
    assert r["gesamt"] == len(SCHEINE) and r["von"] == len(SCHEINE), r
    assert r["ekl"] is None and r["erledigtChip"] is True, r


@pytest.mark.parametrize("rolle", ROLLEN_FELD)
def test_sofort_feldrolle(browser, server, rolle):
    r = _liste(browser, server, rolle, _mit_modus(_html(), "sofort"))
    assert r["fehler"] == [] and r["schreib"] == [], r
    assert r["gesamt"] == len(NR_SOFORT) and r["von"] == len(NR_SOFORT), r
    assert not (set(r["nr"]) & set(NR_FERTIG)), r["nr"]
    for x in SCHEINE:  # offene / in Bearbeitung bleiben
        if x["scheinstatus"] in ("aufgenommen", "freigegeben", "in_bearbeitung", "aufgeschoben"):
            assert x["nummer"] in r["nr"], (x["nummer"], r["nr"])
    assert r["ekl"] is None and r["erledigtChip"] is False, r


@pytest.mark.parametrize("rolle", ROLLEN_ALLE)
def test_sofort_buero_pl_admin_sehen_alles(browser, server, rolle):
    r = _liste(browser, server, rolle, _mit_modus(_html(), "sofort"))
    assert r["fehler"] == [], r["fehler"]
    assert r["gesamt"] == len(SCHEINE) and r["von"] == len(SCHEINE), r
    assert r["erledigtChip"] is True, r


def test_nach_tagen_monteur(browser, server):
    r = _liste(browser, server, "monteur", _mit_modus(_html(), "nach_tagen", 7))
    assert r["fehler"] == [], r["fehler"]
    assert r["gesamt"] == len(NR_NACH_TAGEN), r
    assert "S079006" not in r["nr"] and "S079005" not in r["nr"] and "S079007" not in r["nr"], r["nr"]
    assert r["erledigtChip"] is True and r["ekl"] is None, r


def test_eingeklappt_monteur(browser, server):
    r = _liste(browser, server, "monteur", _mit_modus(_html(), "eingeklappt"), aufklappen=True)
    assert r["fehler"] == [] and r["schreib"] == [], r
    assert r["gesamt"] == len(NR_SOFORT) and r["von"] == len(NR_SOFORT), r
    assert r["ekl"] == "zu" and "Erledigt (%d)" % len(NR_FERTIG) in r["eklText"] and r["eklNr"] == [], r
    assert r["auf"]["ekl"] == "auf" and r["auf"]["eklNr"] == NR_FERTIG, r["auf"]
    assert r["formular"] is True, "Schein aus dem eingeklappten Abschnitt oeffnet nicht (gesperrte Maske erwartet)"


def test_eingeklappt_buero_ohne_abschnitt(browser, server):
    r = _liste(browser, server, "buero", _mit_modus(_html(), "eingeklappt"))
    assert r["gesamt"] == len(SCHEINE) and r["ekl"] is None, r


def test_umkehrprobe_liste_ohne_filter_zeigt_verborgene(browser, server):
    r = _liste(browser, server, "monteur", index_body=_neutralisiert(_mit_modus(_html(), "sofort")))
    assert r["gesamt"] == len(SCHEINE), r  # Altverhalten: alle zehn


AUSWAHL = """() => { const x = [...document.querySelectorAll('select')].find(s => [...s.options].some(o => o.text === '— Schein wählen —'));
  if (!x) return null; return [...new Set([...x.options].map(o => (o.text.match(/S0790\\d\\d/) || [''])[0]).filter(Boolean))].sort(); }"""


def _zeit_auswahl(browser, server, rolle, index_body=None):
    ctx, s, fehler, schreib = _seite(browser, server, rolle, index_body)
    try:
        assert s.evaluate(NAV, "Zeit") != "nicht-gefunden"
        s.wait_for_timeout(2500)
        s.evaluate("() => [...document.querySelectorAll('button')].find(b => (b.textContent || '').trim() === '+ Eintrag').click()")
        s.wait_for_timeout(600)
        s.evaluate("() => [...document.querySelectorAll('button')].find(b => (b.textContent || '').trim() === 'Schein/Störung').click()")
        s.wait_for_timeout(600)
        nr = s.evaluate(AUSWAHL)
        assert fehler == [], fehler
        return nr
    finally:
        ctx.close()


def test_zeiterfassung_auswahl_standard_unveraendert(browser, server):
    assert _zeit_auswahl(browser, server, "monteur") == NR_ALLE


@pytest.mark.parametrize("rolle", ["monteur", "techniker"])
def test_zeiterfassung_auswahl_sofort_feldrolle(browser, server, rolle):
    assert _zeit_auswahl(browser, server, rolle, _mit_modus(_html(), "sofort")) == NR_SOFORT


def test_zeiterfassung_auswahl_sofort_buero_alle(browser, server):
    assert _zeit_auswahl(browser, server, "buero", _mit_modus(_html(), "sofort")) == NR_ALLE


def test_umkehrprobe_zeiterfassung_auswahl_ohne_filter(browser, server):
    nr = _zeit_auswahl(browser, server, "monteur", index_body=_neutralisiert(_mit_modus(_html(), "sofort")))
    assert set(NR_FERTIG) <= set(nr), nr


ZEIT = """() => { const t = document.body.innerText; return {hat: t.indexOf('S079005 — Testkunde 5') >= 0}; }"""


@pytest.mark.parametrize("modus", ["alle", "sofort", "eingeklappt"])
def test_stundeneintrag_auf_verborgenem_schein_behaelt_beschriftung(browser, server, modus):
    ctx, s, fehler, schreib = _seite(browser, server, "monteur", _mit_modus(_html(), modus))
    try:
        assert s.evaluate(NAV, "Zeit") != "nicht-gefunden"
        s.wait_for_timeout(2500)
        assert s.evaluate(ZEIT)["hat"], ("Beschriftung des Eintrags auf dem abgerechneten Schein fehlt", modus)
        assert fehler == [] and schreib == [], (fehler, schreib)
    finally:
        ctx.close()


def test_bearbeiten_eines_eintrags_auf_verborgenem_schein_behaelt_auswahl(browser, server):
    """Ein alter Eintrag auf einem abgerechneten Schein bleibt bearbeitbar: die Auswahl fuehrt genau
    diesen einen Schein weiter (sonst 'Bitte Eintrag auswaehlen'), die anderen verborgenen nicht."""
    ctx, s, fehler, schreib = _seite(browser, server, "monteur", _mit_modus(_html(), "sofort"))
    try:
        assert s.evaluate(NAV, "Zeit") != "nicht-gefunden"
        s.wait_for_timeout(2500)
        geklickt = s.evaluate("""() => { const k = [...document.querySelectorAll('[aria-label="Eintrag bearbeiten"]')].filter(x => x.getBoundingClientRect().height > 0);
          if (k.length !== 1) return k.length; k[0].click(); return true; }""")
        assert geklickt is True, geklickt
        s.wait_for_timeout(800)
        nr = s.evaluate(AUSWAHL)
        assert nr is not None, "Bearbeitungsmaske nicht offen"
        wert = s.evaluate("""() => { const x = [...document.querySelectorAll('select')].find(s => [...s.options].some(o => o.text === '— Schein wählen —')); return x.value; }""")
        assert wert == "A5", wert
        assert "S079005" in nr and not ({"S079004", "S079006", "S079007"} & set(nr)), nr
        assert fehler == [], fehler
    finally:
        ctx.close()


def test_umkehrprobe_beschriftung_ueber_gefilterte_liste_waere_leer(browser, server):
    """Wuerde die Beschriftung die gefilterte Liste lesen, verschwaende die Scheinnummer am Eintrag."""
    alt = "const schein=asId?arbeitsscheine.find(s=>s.id===asId):null;"
    s0 = _mit_modus(_html(), "sofort")
    assert s0.count(alt) == 1
    kaputt = s0.replace(alt, "const schein=asId?_asFuerRolle(arbeitsscheine,curUser.role).find(s=>s.id===asId):null;")
    ctx, s, fehler, schreib = _seite(browser, server, "monteur", index_body=kaputt)
    try:
        s.evaluate(NAV, "Zeit")
        s.wait_for_timeout(2500)
        assert s.evaluate(ZEIT)["hat"] is False
    finally:
        ctx.close()
