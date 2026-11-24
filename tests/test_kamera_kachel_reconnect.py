# -*- coding: utf-8 -*-
"""Kamera-Kachel: MJPEG-Anlauf und Wiederaufbau ohne "Neu laden" (Owner 24.11.2026, Mobotix ueber go2rtc).

Befund vorher: MJPEG-Kachel ging nach dem Token SOFORT auf "live" (schwarz bis zum ersten Bild) und der ERSTE
Bildfehler des img-Elements setzte "Kamera nicht erreichbar" - go2rtc startet den Mobotix-Strom aber erst auf Abruf
(ffmpeg braucht Sekunden), ein Abbruch wurde nie selbst neu aufgebaut. Ein haengender Strom ohne Ereignis blieb
dauerhaft schwarz auf "live".

Jetzt (echter Code aus index.html in Node, Attrappen aus test_kamera_client_v1083, Zeiten verkuerzt):
A  langsamer Anlauf -> erst "verbindet", dann Bild, nie "nicht erreichbar"
B  erster Versuch scheitert (Aufwaermen), zweiter liefert -> Bild ohne Klick
C  erstes Bild ohne onload-Ereignis (Bild hat aber Masse) -> gilt als da
D  Strom bricht ab -> letztes Bild bleibt, Kachel baut selbst neu auf (neues Token), Tausch erst mit erstem Bild
E  Kamera dauerhaft tot (jeder Versuch Fehler) -> nach Anlauf + 3 Wiederholungen sauber "Kamera nicht erreichbar"
F  Kamera haengt (kein Ereignis) -> ebenso nach allen Zeitfenstern
G  UniFi/WebRTC unveraendert sofort live (Waechter: gruen auch auf dem alten Stand, Umkehrprobe belegt die Zaehne)
"""
import pytest

from test_kameras_phase1_v1055 import _block
from test_kamera_client_v1083 import _kachel, _mut

SZENEN = r"""
function reset(s) { SZENE = s; store.clear(); _kamBackend.fehlt = false; FPC.length = 0; WHEP.length = 0;
  ['get','post','upsert','del','fetch','pruef'].forEach(function (k) { ZAEHL[k].length = 0; }); }
const KAMS = [{id: 'mob32', name: 'Mobotix 32', standort: 'Hof', aktiv: true, aufbewahrung_tage: 3}];
const G = 'https://g.example.test:8443';
function MJ(t) { return {status: 200, json: {typ: 'mjpeg', mjpegUrl: G + '/live/mob32/mjpeg?token=' + t, exp: 1e12, ttl: 90}}; }
function wurzel() { return React.createElement(KameraView, {curUser: {id: 'x', role: 'projektleiter'}, ww: 1440, users: []}); }
function bilder() { return alle(baum, function (n) { return n.tag === 'img'; }); }
function anlauf() { return bilder().filter(function (n) { return n.props['data-kam-mjpeg'] === 'anlauf'; }); }
function chips() { return alle(baum, function (n) { return n.props && n.props['data-kam-status']; }).map(function (n) { return n.props['data-kam-status']; }); }
function warte(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
function erstes(l, was) { if (!l.length) return; if (typeof was === "function") was(l[0].props); else l[0].props[was]({}); }
async function bisAnlauf(w, n) { const t = Date.now(); for (let j = 0; Date.now() - t < 3000 && !(anlauf().length && ZAEHL.fetch.length >= n); j++) { await warte(5); await ruhe(w); } }
function bild() { return {n: bilder().length, chips: chips(), text: text(baum), fetch: ZAEHL.fetch.length,
  img: bilder().map(function (b) { return {src: b.props.src, art: b.props['data-kam-mjpeg'], op: b.props.style.opacity, ref: b.props.referrerPolicy}; }),
  neu: knopfHat(baum, 'Neu laden')}; }
globalThis.RTCPeerConnection = FakePC;
KAMERA_MJPEG_START_MS = 1500;  // lang genug, dass die Renderschleife (ruhe) das Fenster nicht selbst verbraucht
KAMERA_MJPEG_RETRY_MS = [20, 20, 20];

// A) langsamer Anlauf
reset({db: {kameras: KAMS}, fein: true, fetch: MJ('T1')});
let w = wurzel(); await ruhe(w);
OUT.a0 = bild();
await warte(300); await ruhe(w);
OUT.a1 = bild();
erstes(anlauf(), "onLoad"); await ruhe(w);
OUT.a2 = bild();

// B) erster Versuch scheitert beim Aufwaermen, zweiter liefert
reset({db: {kameras: KAMS}, fein: true, fetch: MJ('T1')});
w = wurzel(); await ruhe(w);
SZENE.fetch = MJ('T2');
erstes(anlauf(), "onError"); await ruhe(w);
OUT.b0 = bild();
await bisAnlauf(w, 2);
OUT.b1 = bild();
erstes(anlauf(), "onLoad"); await ruhe(w);
OUT.b2 = bild();

// C) erstes Bild ohne onload-Ereignis, das Bild hat aber Masse
reset({db: {kameras: KAMS}, fein: true, fetch: MJ('T1')});
w = wurzel(); await ruhe(w);
OUT.c0 = bild();
erstes(anlauf(), function (p) { p.ref.current.naturalWidth = 640; });
for (let j = 0; j < 100 && chips()[0] !== 'live'; j++) { await warte(10); await ruhe(w); }
OUT.c1 = bild();

// D) Strom bricht im Betrieb ab
reset({db: {kameras: KAMS}, fein: true, fetch: MJ('T1')});
w = wurzel(); await ruhe(w);
erstes(anlauf(), function (p) { p.ref.current.naturalWidth = 0; });
erstes(anlauf(), "onLoad"); await ruhe(w);
OUT.d0 = bild();
SZENE.fetch = MJ('T2');
erstes(bilder(), "onError"); await ruhe(w);
OUT.d1 = bild();
await bisAnlauf(w, 2);
OUT.d2 = bild();
erstes(anlauf(), "onLoad"); await ruhe(w);
OUT.d3 = bild();

// E) Kamera dauerhaft tot: jeder Versuch scheitert sofort
reset({db: {kameras: KAMS}, fein: true, fetch: MJ('T1')});
w = wurzel(); await ruhe(w);
erstes(anlauf(), "onError"); await ruhe(w);
OUT.e0 = bild();
for (let i = 0; i < 3; i++) { await bisAnlauf(w, i + 2); const a = anlauf(); if (a.length) { a[0].props.onError({}); await ruhe(w); } }
await warte(5); await ruhe(w); await warte(5); await ruhe(w);
OUT.e1 = bild();
if (knopfHat(baum, 'Neu laden')) await klick(w, 'Neu laden');
OUT.e2 = bild();
erstes(anlauf(), "onLoad"); await ruhe(w);
OUT.e3 = bild();

// F) Kamera haengt: kein Bild, kein Fehler
reset({db: {kameras: KAMS}, fein: true, fetch: MJ('T1')});
w = wurzel(); await ruhe(w);
OUT.f0 = bild();
const tF = Date.now();
for (let j = 0; Date.now() - tF < 15000 && text(baum).indexOf('nicht erreichbar') < 0; j++) { await warte(10); await ruhe(w); }
await warte(5); await ruhe(w);
OUT.f1 = bild();

// G) UniFi/WebRTC: sofort live, Anlauf-Fenster spielt keine Rolle
KAMERA_MJPEG_START_MS = 10000;
const LIVE = {status: 200, json: {typ: 'webrtc', liveUrl: G + '/live/cam1/index.m3u8?token=T', webrtcUrl: G + '/live/cam1/whep?token=T',
              snapshotUrl: G + '/live/cam1/snapshot.jpg?token=T', exp: 1e12}};
reset({db: {kameras: KAMS}, fein: true, fetch: LIVE, whep: {status: 201}, ice: 'connected'});
const t0 = Date.now();
w = wurzel(); await ruhe(w); await warte(30); await ruhe(w);
OUT.g = Object.assign(bild(), {ms: Date.now() - t0, whep: WHEP.length,
  video: alle(baum, function (n) { return n.tag === 'video'; }).map(function (v) { return v.props.style.display; })});
"""


def _lauf(node_exe, block=None):
    return _kachel(node_exe, block if block is not None else _block(), SZENEN)


@pytest.fixture(scope="module")
def R(node_exe):
    return _lauf(node_exe)


def _kein_fehler(z):
    assert "nicht erreichbar" not in z["text"] and z["neu"] is False, z["text"]


def test_langsamer_anlauf_erst_verbindet_dann_bild(R):
    for z in (R["a0"], R["a1"]):
        assert z["chips"] == ["verbindet"] and "Verbinde" in z["text"], z
        _kein_fehler(z)
        # der Strom laeuft schon (img im Dokument), bleibt aber unsichtbar bis zum ersten Bild
        assert z["img"] == [{"src": "https://g.example.test:8443/live/mob32/mjpeg?token=T1", "art": "anlauf", "op": 0, "ref": "no-referrer"}]
    a = R["a2"]
    assert a["chips"] == ["live"] and "Verbinde" not in a["text"] and a["fetch"] == 1
    assert a["img"] == [{"src": "https://g.example.test:8443/live/mob32/mjpeg?token=T1", "art": "an", "op": 1, "ref": "no-referrer"}]
    _kein_fehler(a)


def test_aufwaermfehler_wird_selbst_wiederholt(R):
    _kein_fehler(R["b0"])
    assert R["b0"]["chips"] == ["verbindet"]
    b1 = R["b1"]
    assert b1["fetch"] == 2, "neues Token fuer den zweiten Versuch"
    assert [i["src"] for i in b1["img"]] == ["https://g.example.test:8443/live/mob32/mjpeg?token=T2"]
    _kein_fehler(b1)
    assert R["b2"]["chips"] == ["live"] and R["b2"]["img"][0]["op"] == 1
    _kein_fehler(R["b2"])


def test_erstes_bild_ohne_onload_gilt_als_da(R):
    assert R["c0"]["chips"] == ["verbindet"]
    c = R["c1"]
    assert c["chips"] == ["live"] and c["fetch"] == 1 and c["img"][0]["art"] == "an" and c["img"][0]["op"] == 1
    _kein_fehler(c)


def test_abbruch_baut_selbst_neu_auf_letztes_bild_bleibt(R):
    assert R["d0"]["chips"] == ["live"]
    d1 = R["d1"]
    _kein_fehler(d1)
    assert d1["chips"] == ["verbindet"], "Wiederaufbau sichtbar im Statuschip"
    assert d1["img"][0] == {"src": "https://g.example.test:8443/live/mob32/mjpeg?token=T1", "art": "an", "op": 1, "ref": "no-referrer"}, \
        "letztes gutes Bild bleibt stehen"
    assert all(i["op"] == 0 and i["art"] == "anlauf" for i in d1["img"][1:]), "ein neuer Strom laeuft hoechstens unsichtbar an"
    d2 = R["d2"]
    assert d2["fetch"] == 2
    assert [(i["art"], i["src"][-2:], i["op"]) for i in d2["img"]] == [("an", "T1", 1), ("anlauf", "T2", 0)], "neuer Strom laedt unsichtbar"
    d3 = R["d3"]
    assert d3["chips"] == ["live"] and [(i["art"], i["src"][-2:], i["op"]) for i in d3["img"]] == [("an", "T2", 1)]
    _kein_fehler(d3)


def test_tote_kamera_nach_allen_versuchen_sauber_nicht_erreichbar(R):
    _kein_fehler(R["e0"])
    assert R["e0"]["chips"] == ["verbindet"]
    e = R["e1"]
    assert e["fetch"] == 4, "Anlauf + 3 Wiederholungen"
    assert e["n"] == 0 and "Kamera nicht erreichbar" in e["text"] and e["neu"] is True and e["chips"] == ["offline"]
    # Neu laden bleibt als Handgriff und startet frisch
    assert R["e2"]["fetch"] == 5 and R["e2"]["chips"] == ["verbindet"]
    assert R["e3"]["chips"] == ["live"]


def test_haengende_kamera_nach_allen_zeitfenstern_nicht_erreichbar(R):
    assert R["f0"]["chips"] == ["verbindet"]
    f = R["f1"]
    assert f["fetch"] == 4 and f["n"] == 0 and "Kamera nicht erreichbar" in f["text"] and f["neu"] is True


def test_unifi_webrtc_unveraendert_sofort_live(R):
    g = R["g"]
    assert g["chips"] == ["live"] and g["n"] == 0 and g["whep"] == 1 and g["fetch"] == 1
    assert g["video"] == ["block"] and "Verbinde" not in g["text"]
    assert g["ms"] < 5000, "kein Warten auf das MJPEG-Anlauffenster"


def test_konstanten_im_block():
    b = _block()
    assert "var KAMERA_MJPEG_START_MS=10000;" in b and "var KAMERA_MJPEG_RETRY_MS=[2000,5000,10000];" in b
    assert "`" not in b


# ── Umkehrproben ─────────────────────────────────────────────────────────────
def test_umkehrprobe_ohne_wiederholung_sofort_fehler(node_exe):
    b = _mut(_block(), "function _kamMjpegPause(n){return (n>=0&&n<KAMERA_MJPEG_RETRY_MS.length)?KAMERA_MJPEG_RETRY_MS[n]:null;}",
             "function _kamMjpegPause(n){return null;}")
    R2 = _lauf(node_exe, b)
    assert "nicht erreichbar" in R2["b0"]["text"] and "nicht erreichbar" in R2["d1"]["text"]


def test_umkehrprobe_ohne_anlauffenster_haengt_es_ewig(node_exe):
    b = _mut(_block(), "else mjFehl(e.k,e.u);},KAMERA_MJPEG_START_MS);", "else mjFehl(e.k,e.u);},1e9);")
    R2 = _lauf(node_exe, b)
    assert "nicht erreichbar" not in R2["f1"]["text"] and R2["f1"]["fetch"] == 1


def test_umkehrprobe_ohne_doppelpuffer_verschwindet_das_letzte_bild(node_exe):
    b = _mut(_block(), "[mj.an,mj.neu].filter(Boolean)", "[mj.neu].filter(Boolean)")
    R2 = _lauf(node_exe, b)
    assert R2["d1"]["n"] == 0


def test_umkehrprobe_webrtc_waechter_hat_zaehne(node_exe):
    # wuerde WebRTC wie MJPEG erst im Anlauf stehen, saehe G kein "live"
    b = _mut(_block(), "        try{await v.play();}catch(_p){}\r\n        setSt({phase:'live',grund:''});",
             "        try{await v.play();}catch(_p){}\r\n        setSt({phase:'laedt',grund:'laedt'});")
    R2 = _lauf(node_exe, b)
    assert R2["g"]["chips"] == ["verbindet"]
