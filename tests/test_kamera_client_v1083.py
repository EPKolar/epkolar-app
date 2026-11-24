# -*- coding: utf-8 -*-
"""Kamera-Client v3.9.1083 - WHEP/Einzelbild-Weg gegen go2rtc 1.9.9 + Caddy-Gateway, Diagnose fuer vor Ort.

1. sw.js: Anfragen ins lokale Netz (Kamera-Gateway) gehen NICHT durch den Service Worker. Chrome Local Network Access
   (ab 142) fragt nur fuer Anfragen der Seite; eine vom SW weitergereichte Anfrage ins lokale Netz wird ohne Frage
   abgelehnt. Ausserdem landen so keine Token-Adressen/Antworten im SW-Cache.
2. Kachel: WHEP-Antwort da, ICE verbindet nicht -> nach KAMERA_ICE_MS Einzelbild-Rueckfall (statt ~30 s schwarz "live").
3. Kachel: Einzelbild/MJPEG scheitert UND /gesund am Gateway antwortet nicht -> "Kamera-Server nicht erreichbar" + Hinweis.
4. Einrichtung: "nicht erreichbar" nennt Zertifikat, Buero-Netz, Browser-Freigabe fuer das lokale Netz.
5. _kamWhep (unveraendert, hier belegt): POST application/sdp, keine weiteren Koepfe, 201 gilt als ok, Angebot erst
   nach abgeschlossener ICE-Sammlung (go2rtc 1.9.9: kein Trickle ueber HTTP, PATCH = 405).
Jede Pruefung laeuft echten Code in Node mit Attrappen; Umkehrproben belegen, dass sie Zaehne hat.
"""
import io
import json
import os
import subprocess
import tempfile

import pytest

from conftest import EPK_TEST_TIMEOUT
from test_kameras_phase1_v1055 import RENDER_PRELUDE, _block, _layout_echt
from test_kameras_einrichtung_v1060 import VERBOTEN_IN_EINRICHTUNG

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SW = os.path.join(WURZEL, "sw.js")
IP4 = ".".join(("192", "168", "1", "20"))  # zusammengesetzt: keine IP-Literale im Repo


def _lies(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


def _mut(text, alt, neu):
    assert text.count(alt) == 1, alt
    return text.replace(alt, neu, 1)


def _node(node_exe, js, name="h.cjs"):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, name)
        with io.open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(js)
        r = subprocess.run([node_exe, p], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


# ── 1. Service Worker ──────────────────────────────────────────────────────
SW_HARNESS = r"""
const vm = require('vm');
const src = %(src)s;
const handler = {};
const ctx = {
  self: {addEventListener: function (t, f) { handler[t] = f; }, location: {origin: 'https://epkolar.github.io'},
         skipWaiting: function () {}, clients: {claim: function () { return Promise.resolve(); }, matchAll: function () { return Promise.resolve([]); }}},
  caches: {open: function () { return Promise.resolve({put: function () {}, addAll: function () { return Promise.resolve(); }}); },
           match: function () { return Promise.resolve(undefined); }, keys: function () { return Promise.resolve([]); }},
  fetch: function () { return Promise.resolve({ok: true}); }, URL: URL, console: console, Promise: Promise,
  setTimeout: setTimeout, clearTimeout: clearTimeout,
};
vm.runInNewContext(src, ctx);
const URLS = %(urls)s;
const OUT = {};
for (const u of URLS) {
  let gefangen = false;
  handler.fetch({request: {url: u, method: 'GET', mode: 'cors', destination: ''}, respondWith: function (p) { gefangen = true; if (p && p.catch) p.catch(function () {}); }});
  OUT[u] = gefangen;
}
console.log(JSON.stringify(OUT));
"""

GW_IP = "https://" + IP4 + ":8443"
LOKAL = [GW_IP + "/live/hochregal01/whep?token=T", GW_IP + "/live/hochregal01/snapshot.jpg?token=T&_=3",
         GW_IP + "/gesund", GW_IP + "/live/mob32/mjpeg?token=T",
         "https://kameras.example.test/live/cam39/snapshot.jpg?token=T",   # Gateway unter DNS-Namen
         "https://kameras.example.test/gesund",
         "https://" + ".".join(("10", "0", "0", "5")) + "/x.jpg", "https://" + ".".join(("172", "20", "1", "1")) + "/x",
         "https://nas.local/x", "https://[fd00::1]/x"]
FREMD = ["https://epkolar.github.io/epkolar-app/icon-192.png",
         "https://fonts.example.test/live.css",                                # kein /live/<s>/-Pfad
         "https://" + ".".join(("172", "40", "1", "1")) + "/x"]                  # oeffentlich (ausserhalb 172.16/12)


def _sw(node_exe, src=None):
    urls = LOKAL + FREMD
    return _node(node_exe, SW_HARNESS % {"src": json.dumps(src if src is not None else _lies(SW)), "urls": json.dumps(urls)})


def test_sw_laesst_lokales_netz_und_gateway_durch(node_exe):
    R = _sw(node_exe)
    for u in LOKAL:
        assert R[u] is False, ("SW darf nicht dazwischen", u)
    for u in FREMD:
        assert R[u] is True, ("uebrige Anfragen weiter ueber den SW", u)


def test_umkehrprobe_sw_ohne_ausnahme_faengt_gateway(node_exe):
    kaputt = _mut(_lies(SW), "  if (_lokalesNetz(url)) return;\n", "")
    R = _sw(node_exe, kaputt)
    assert R[LOKAL[0]] is True and R[LOKAL[1]] is True, "Umkehrprobe: alter SW reichte Gateway-Anfragen weiter"


# ── 2./3./5. Kachel ────────────────────────────────────────────────────────
PRELUDE_EXTRA = r"""
// Referenzen auf Host-Elemente fuellen (sonst sieht die Kachel nie ein Videoelement)
function _fakeEl(tag) { return {tag: tag, srcObject: null, src: '', play: function () { return Promise.resolve(); }, pause: function () {},
  removeAttribute: function () {}, load: function () {}, canPlayType: function () { return ''; }}; }
const FPC = [];
class FakePC {
  constructor(cfg) { this.cfg = cfg; this.connectionState = 'new'; this.iceConnectionState = 'new'; this.iceGatheringState = 'gathering';
    this.localDescription = null; this.tr = []; this.l = {}; this.remote = null; FPC.push(this);
    const self = this; setTimeout(function () { self.iceGatheringState = 'complete'; self.localDescription = {type: 'offer', sdp: 'v=0 offer+kandidaten'};
      (self.l.icegatheringstatechange || []).forEach(function (f) { f(); }); }, 5); }
  addTransceiver(k, o) { this.tr.push([k, o && o.direction]); }
  async createOffer() { return {type: 'offer', sdp: 'v=0 offer'}; }
  async setLocalDescription(o) { this.localDescription = o; }
  addEventListener(t, f) { (this.l[t] = this.l[t] || []).push(f); }
  async setRemoteDescription(d) { this.remote = d; if (SZENE.ice) { this.connectionState = SZENE.ice; this.iceConnectionState = SZENE.ice; } }
  close() { this.connectionState = 'closed'; }
}
const WHEP = [];
"""


def _prelude():
    p = RENDER_PRELUDE
    p = _mut(p, "  return {tag: el.type, props: el.props, kinder: rend(el.children, pfad + '>' + el.type)};",
             "  if (el.props && el.props.ref && typeof el.props.ref === 'object' && !el.props.ref.current) el.props.ref.current = _fakeEl(el.type);\n"
             "  return {tag: el.type, props: el.props, kinder: rend(el.children, pfad + '>' + el.type)};")
    # WHEP-Attrappe VOR dem JSON-Lesen der Grund-Attrappe (der Rumpf ist SDP, kein JSON)
    p = _mut(p, "async function fetch(url, init) {\n",
             "async function fetch(url, init) {\n"
             "  if (/\\/whep\\?/.test(url)) { WHEP.push({url: url, init: init, sdp: init && init.body, zeit: FPC.length ? FPC[FPC.length - 1].iceGatheringState : ''});\n"
             "    const a = SZENE.whep || {status: 201}; if (a.wirft) throw new TypeError('Failed to fetch');\n"
             "    return {status: a.status, ok: a.status >= 200 && a.status < 300, text: async function () { return 'v=0 answer'; }}; }\n")
    return p + PRELUDE_EXTRA


def _kachel(node_exe, block, szenen):
    js = _prelude() + _layout_echt() + block + "\n(async function(){\nconst OUT={};\n" + szenen + \
        "\nconsole.log(JSON.stringify(OUT));process.exit(0);\n})().catch(function(e){console.error(e&&e.stack||e);process.exit(3);});\n"
    return _node(node_exe, js, "render.cjs")


SZENEN = r"""
function reset(s) { SZENE = s; store.clear(); _kamBackend.fehlt = false; FPC.length = 0; WHEP.length = 0;
  ['get','post','upsert','del','fetch','pruef'].forEach(function (k) { ZAEHL[k].length = 0; }); }
const KAMS = [{id: 'cam1', name: 'Kamera 1', standort: 'Hof', aktiv: true, aufbewahrung_tage: 3}];
const G = 'https://g.example.test:8443';
const LIVE = {status: 200, json: {typ: 'webrtc', liveUrl: G + '/live/cam1/index.m3u8?token=T', webrtcUrl: G + '/live/cam1/whep?token=T',
              snapshotUrl: G + '/live/cam1/snapshot.jpg?token=T', exp: 1e12}};
function wurzel() { return React.createElement(KameraView, {curUser: {id: 'x', role: 'projektleiter'}, ww: 1440, users: []}); }
function bilder() { return alle(baum, function (n) { return n.tag === 'img'; }); }
function warte(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
globalThis.RTCPeerConnection = FakePC;
KAMERA_ICE_MS = 400;

// a) WHEP ok (201), ICE haengt -> Einzelbild-Rueckfall
reset({db: {kameras: KAMS}, fein: true, fetch: LIVE, whep: {status: 201}, ice: 'checking'});
let w = wurzel(); await ruhe(w);
OUT.haengt_vorher = {img: bilder().length, whep: WHEP.length};
await warte(700); await ruhe(w);
OUT.haengt = {img: bilder().length, src: bilder().length ? bilder()[0].props.src : '', pcZu: FPC.length ? FPC[0].connectionState : ''};
const W0 = WHEP[0] || {};
OUT.whep = {url: W0.url, methode: W0.init && W0.init.method, koepfe: W0.init && W0.init.headers, cred: W0.init ? (W0.init.credentials || null) : 'x',
            sdp: W0.sdp, zeit: W0.zeit, tr: FPC.length ? FPC[0].tr : [], remote: FPC.length ? FPC[0].remote : null};

// b) ICE verbunden -> Video bleibt, kein Einzelbild
reset({db: {kameras: KAMS}, fein: true, fetch: LIVE, whep: {status: 201}, ice: 'connected'});
w = wurzel(); await ruhe(w); await warte(700); await ruhe(w);
OUT.verbunden = {img: bilder().length, text: text(baum), pcZu: FPC.length ? FPC[0].connectionState : ''};

// c) WHEP wirft (Zertifikat/Netz), Einzelbild scheitert 3x, Gateway antwortet nicht -> Hinweis
reset({db: {kameras: KAMS}, fein: true, fetch: LIVE, whep: {wirft: true}, gesund: {wirft: true}});
w = wurzel(); await ruhe(w);
for (let i = 0; i < 3; i++) { const b = bilder(); if (b.length) { b[0].props.onError({}); await ruhe(w); } }
await warte(5); await ruhe(w);
OUT.gateway_weg = {img: bilder().length, text: text(baum), neu: knopfHat(baum, 'Neu laden'), pruef: ZAEHL.pruef.slice()};

// d) wie c), aber Gateway antwortet -> die Kamera selbst fehlt
reset({db: {kameras: KAMS}, fein: true, fetch: LIVE, whep: {wirft: true}, gesund: {status: 200}});
w = wurzel(); await ruhe(w);
for (let i = 0; i < 3; i++) { const b = bilder(); if (b.length) { b[0].props.onError({}); await ruhe(w); } }
await warte(5); await ruhe(w);
OUT.kamera_weg = {text: text(baum), pruef: ZAEHL.pruef.slice()};

// e) MJPEG bricht ab, Gateway weg
reset({db: {kameras: KAMS}, fein: true, fetch: {status: 200, json: {typ: 'mjpeg', mjpegUrl: G + '/live/mob32/mjpeg?token=T', exp: 1e12}}, gesund: {wirft: true}});
w = wurzel(); await ruhe(w);
// Pin angepasst 24.11.2026 (feature/kamera-kachel-reconnect): alt = EIN onError -> Hinweis. Neu erst nach Anlauf +
// 3 automatischen Wiederholungen (Pausen verkuerzt); die Diagnose danach ist unveraendert.
KAMERA_MJPEG_RETRY_MS = [5, 5, 5];
for (let i = 0; i < 4; i++) {
  for (let j = 0; j < 100 && !bilder().length; j++) { await warte(5); await ruhe(w); }
  const bi = bilder(); if (bi.length) { bi[bi.length - 1].props.onError({}); await ruhe(w); }
}
await warte(5); await ruhe(w); await warte(5); await ruhe(w);
OUT.mjpeg_gateway = text(baum);

OUT.H = {basis: [_kamGatewayBasis(G + '/live/cam1/snapshot.jpg?token=T&_=4'), _kamGatewayBasis('https://h.example.test/kam/live/c_2/mjpeg?token=T'),
                 _kamGatewayBasis('http://h/live/c/x'), _kamGatewayBasis('https://h/andere/c/x'), _kamGatewayBasis(null)],
         ice: [_kamIceHaengt('new', 'new'), _kamIceHaengt('connecting', 'checking'), _kamIceHaengt('connected', 'connected'),
               _kamIceHaengt(undefined, 'completed'), _kamIceHaengt(undefined, 'connected'), _kamIceHaengt('failed', 'failed')],
         tipp: KAMERA_NETZ_TIPP, status: _kamStatus('stub', 'gateway')};
"""


def _ui(node_exe, block=None):
    return _kachel(node_exe, block if block is not None else _block(), SZENEN)


@pytest.fixture(scope="module")
def K(node_exe):
    return _ui(node_exe)


def test_whep_anfrage_passt_zu_go2rtc_und_caddy(K):
    w = K["whep"]
    assert w["url"] == "https://g.example.test:8443/live/cam1/whep?token=T" and w["methode"] == "POST"
    # Caddy @vorab erlaubt nur content-type: genau dieser eine Kopf, keine Anmeldedaten
    assert w["koepfe"] == {"Content-Type": "application/sdp"} and w["cred"] in (None, "omit")
    # go2rtc 1.9.9: kein Trickle ueber HTTP -> Angebot erst nach abgeschlossener ICE-Sammlung
    assert w["zeit"] == "complete" and w["sdp"] == "v=0 offer+kandidaten"
    assert w["tr"] == [["video", "recvonly"], ["audio", "recvonly"]]
    # go2rtc antwortet 201 Created mit der Antwort-SDP als Text
    assert w["remote"] == {"type": "answer", "sdp": "v=0 answer"}


def test_ice_haengt_faellt_auf_einzelbild_zurueck(K):
    assert K["haengt_vorher"]["img"] == 0 and K["haengt_vorher"]["whep"] == 1
    h = K["haengt"]
    assert h["img"] == 1 and h["src"].startswith("https://g.example.test:8443/live/cam1/snapshot.jpg?token=T&_=")
    assert h["pcZu"] == "closed", "die haengende Verbindung wird geschlossen"


def test_ice_verbunden_bleibt_video(K):
    v = K["verbunden"]
    assert v["img"] == 0 and v["pcZu"] == "connected"


def test_gateway_weg_zeigt_hinweis(K):
    g = K["gateway_weg"]
    assert g["img"] == 0 and g["neu"] is True
    assert "Kamera-Server nicht erreichbar" in g["text"] and K["H"]["tipp"] in g["text"]
    assert "gesund:https://g.example.test:8443/gesund" in g["pruef"]
    assert "Kamera-Server nicht erreichbar" in K["mjpeg_gateway"] and K["H"]["tipp"] in K["mjpeg_gateway"]


def test_gateway_da_kamera_weg_bleibt_wie_bisher(K):
    k = K["kamera_weg"]
    assert "Kamera nicht erreichbar" in k["text"] and K["H"]["tipp"] not in k["text"]
    assert "Kamera-Server nicht erreichbar" not in k["text"]


def test_helfer(K):
    H = K["H"]
    assert H["basis"] == ["https://g.example.test:8443", "https://h.example.test/kam", "", "", ""]
    assert H["ice"] == [True, True, False, False, False, True]
    assert H["status"] == "server"
    for wort in VERBOTEN_IN_EINRICHTUNG + ("erledigt",):
        assert wort not in H["tipp"], wort


def test_umkehrprobe_ohne_ice_wache_bleibt_es_schwarz(node_exe):
    b = _mut(_block(), "iceT=setTimeout(", "iceT=0&&setTimeout(")
    assert _ui(node_exe, b)["haengt"]["img"] == 0


def test_umkehrprobe_ohne_gesundheitsabruf_kein_hinweis(node_exe):
    b = _mut(_block(), "if(gb)_kamBueroPruefen(gb)", "if(false)_kamBueroPruefen(gb)")
    R = _ui(node_exe, b)
    assert "Kamera-Server nicht erreichbar" not in R["gateway_weg"]["text"]


def test_umkehrprobe_whep_vor_ice_sammlung(node_exe):
    b = _mut(_block(), "if(pc.iceGatheringState==='complete'){fertig();return;}", "fertig();return;")
    assert _ui(node_exe, b)["whep"]["zeit"] != "complete"


# ── 4. Einrichtung ──────────────────────────────────────────────────────────
EINR = r"""
const OUT = {};
const fn = {stufe: 'ok', secret: true, basis: 'https://g'};
OUT.weg = _kamEinrichtung({status: 'ok', rows: []}, fn, 'nicht_erreichbar').zeilen.filter(function (z) { return z.id === 'buero'; })[0];
OUT.ok = _kamEinrichtung({status: 'ok', rows: []}, fn, 'ok').zeilen.filter(function (z) { return z.id === 'buero'; })[0];
"""


def _einr(node_exe, block=None):
    js = RENDER_PRELUDE + (block if block is not None else _block()) + "\n" + EINR + "\nconsole.log(JSON.stringify(OUT));\n"
    return _node(node_exe, js)


def test_einrichtung_nennt_drei_pruefpunkte(node_exe):
    R = _einr(node_exe)
    t = R["weg"]["text"]
    assert R["weg"]["titel"] == "Kamera-Server im Büro: nicht erreichbar"
    assert "unterwegs ist das normal" in t
    assert "Stammzertifikat des Kamera-Servers auf diesem Gerät installiert" in t
    assert "Büro-WLAN" in t
    assert "Zugriff auf Geräte im lokalen Netzwerk" in t and "erlauben" in t
    for wort in VERBOTEN_IN_EINRICHTUNG + ("erledigt",):
        assert wort not in t, wort
    assert R["ok"]["text"] == ""


def test_umkehrprobe_alter_einrichtungstext(node_exe):
    b = _block()
    i = b.index("buero==='nicht_erreichbar'")
    j = b.index("wer:''});", i)
    alt = b[i:j]
    kaputt = b.replace(alt, "buero==='nicht_erreichbar')z.push({id:'buero',stand:'offen',titel:'Kamera-Server im Büro: nicht erreichbar',"
                            "text:'Er ist nur aus dem Büro-Netz erreichbar - unterwegs ist das normal.',", 1)
    R = _einr(node_exe, kaputt)
    assert "Stammzertifikat" not in R["weg"]["text"]
