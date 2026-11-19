# -*- coding: utf-8 -*-
"""Kamera-Oberflaeche fuer den Betrieb + Demo-Ansicht (20.11.2026) - echter Code aus index.html in Node.

TEIL A: reine Helfer (Statuschip je HTTP-Status/Fehler, Wiederholung mit Pause, Spalten aus _layoutStufe, Token-Erneuerung).
TEIL B: Kachel - 403 -> "kein Zugriff jetzt", 503 -> "Server nicht erreichbar", Netzfehler -> 3 Wiederholungen dann
        "Neu laden"; Strom erst bei Sichtbarkeit, Stopp bei verborgener Seite; Vollbild auf/zu (Knopf + Esc).
TEIL C: Ansicht - Spalten je Stufe, Aufzeichnungen aus (Hinweis nur fuer Admin), Verwaltungs-Hinweis.
TEIL D: Demo - nur Admin + Schalter, kein einziger Abruf, Banner auf jeder Kachel und im Kopf; Umkehrproben.
"""
import pytest

from test_kameras_phase1_v1055 import _block, _render_lauf

SZENEN = r"""
function reset(s) { SZENE = s; store.clear(); _kamBackend.fehlt = false; window.location.search = s.search || '';
  ['get','post','upsert','del','fetch','pruef'].forEach(function (k) { ZAEHL[k].length = 0; }); delete LS[KAMERA_DEMO_LS]; }
const KAMS = [{id: 'hochregal01', name: 'Hochregal 01', standort: 'Lager', aktiv: true, aufbewahrung_tage: 3}];
const KAMS4 = ['hochregal01', 'verkauf02', 'elektrolager03', 'cam39'].map(function (i) { return {id: i, name: i, standort: 'x', aktiv: true, aufbewahrung_tage: 3}; });
function wurzel(rolle, ww) { return React.createElement(KameraView, {curUser: {id: 'x', role: rolle}, ww: ww || 1440, users: []}); }
function chips() { return alle(baum, function (n) { return n.props && n.props['data-kam-status']; }).map(function (n) { return n.props['data-kam-status']; }); }
function knoepfe() { return alle(baum, function (n) { return n.tag === 'button'; }).map(function (n) { return (text(n).trim() || n.props['aria-label'] || ''); }); }
function raster() { return alle(baum, function (n) { return n.props && n.props.style && n.props.style.gridTemplateColumns; }).map(function (n) { return n.props.style.gridTemplateColumns; }); }
function warte(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
const W = {typ: 'webrtc', liveUrl: 'https://g/live/hochregal01/index.m3u8?token=T', webrtcUrl: 'https://g/live/hochregal01/whep?token=T',
           snapshotUrl: 'https://g/live/hochregal01/snapshot.jpg?token=T', exp: 1e12, ttl: 90};

// ── A: Helfer ──
OUT.A = {
  status: [['live',''],['laedt','laedt'],['laedt','wartet'],['stub','kein_zugriff'],['stub','kein_backend'],['stub','netz_aus'],['stub','offline'],['stub','abbruch'],['stub','fehler']]
    .map(function (x) { return _kamStatus(x[0], x[1]); }),
  ausHttp: [403, 401, 503, 404, 0].map(function (st) { return _kamStatus('stub', _kamStreamAntwort(st, {error: 'x'}, 'live').grund); }),
  backoff: [0, 1, 2, 3, -1].map(_kamBackoff),
  spalten: [['schmal','2x2',4],['schmal','3x3',9],['mittel','3x3',9],['mittel','2x2',1],['breit','2x2',4],['breit','3x3',9],['breit','alle',4],['breit','alle',9],['breit','einzel',1]]
    .map(function (x) { return _kamSpalten(x[0], x[1], x[2]); }),
  stufe: [[390, 800], [800, 1280], [1280, 800], [1440, 900]].map(function (x) { return _layoutStufe(x[0], x[1]); }),
  refresh: [_kamRefreshIn(1000 + 90, 1000 * 1000), _kamRefreshIn(1000 + 10, 1000 * 1000), _kamRefreshIn(1000 + 500, 1000 * 1000)],
  txt: KAMERA_STATUS_TXT
};

// ── B: Kachel ──
reset({db: {kameras: KAMS}, fein: true, fetch: {status: 403, json: {error: 'kein_zugriff'}}});
let w = wurzel('admin'); await ruhe(w);
OUT.k403 = {chips: chips(), fetch: ZAEHL.fetch.length, text: text(baum)};
reset({db: {kameras: KAMS}, fein: true, fetch: {status: 503, json: {error: 'nicht_konfiguriert'}}});
w = wurzel('admin'); await ruhe(w);
OUT.k503 = {chips: chips(), fetch: ZAEHL.fetch.length, neu: knoepfe().indexOf('Neu laden') >= 0};

// Netzfehler: fetch wirft -> 3 Wiederholungen (Pausen fuer den Test verkuerzt), dann "Neu laden"
const echtFetch = _fetchStream;
_fetchStream = async function () { ZAEHL.fetch.push('netz'); throw new Error('netz'); };
KAMERA_RETRY_MS = [1500, 5, 5];  // erste Pause lang genug fuer die Erstmessung auch unter Last
reset({db: {kameras: KAMS}, fein: true});
w = wurzel('admin'); await ruhe(w);
OUT.netz_erst = {chips: chips(), fetch: ZAEHL.fetch.length};
for (let i = 0; i < 400 && ZAEHL.fetch.length < 4; i++) { await warte(25); await ruhe(w); }
for (let i = 0; i < 4; i++) { await warte(25); await ruhe(w); }
OUT.netz_ende = {chips: chips(), fetch: ZAEHL.fetch.length, neu: knoepfe().indexOf('Neu laden') >= 0, text: text(baum)};
_fetchStream = echtFetch;
KAMERA_RETRY_MS = [2000, 5000, 10000];

// Sichtbarkeit: Beobachter + Seite verborgen
let ioCb = null; let sichtLst = null;
globalThis.IntersectionObserver = function (cb) { ioCb = cb; this.observe = function () {}; this.disconnect = function () {}; };
globalThis.document = {hidden: false, addEventListener: function (t, f) { if (t === 'visibilitychange') sichtLst = f; }, removeEventListener: function () {}};
const echtCE = React.createElement;
React.createElement = function (t, p) { if (p && p.ref && typeof p.ref === 'object' && !p.ref.current) p.ref.current = {tag: t}; return echtCE.apply(this, arguments); };
reset({db: {kameras: KAMS}, fein: true, fetch: {status: 200, json: W}});
w = wurzel('admin'); await ruhe(w);
OUT.sicht_vorher = {fetch: ZAEHL.fetch.length, chips: chips()};
ioCb([{isIntersecting: true}]); await ruhe(w);
OUT.sicht_an = {fetch: ZAEHL.fetch.length, chips: chips()};
document.hidden = true; sichtLst(); await ruhe(w);
OUT.sicht_verborgen = {fetch: ZAEHL.fetch.length, chips: chips(), bilder: alle(baum, function (n) { return n.tag === 'img' && /snapshot/.test(String(n.props.src)); }).length};
document.hidden = false; sichtLst(); await ruhe(w);
OUT.sicht_zurueck = {fetch: ZAEHL.fetch.length};
delete globalThis.IntersectionObserver; delete globalThis.document;
React.createElement = echtCE;

// Vollbild
reset({db: {kameras: KAMS4}, fein: true, fetch: {status: 200, json: W}});
w = wurzel('admin'); await ruhe(w);
const vb = alle(baum, function (n) { return n.tag === 'button' && n.props['aria-label'] === 'Vollbild verkauf02'; })[0];
OUT.voll_knopf = !!vb && vb.props.style.minHeight >= 44;
vb.props.onClick({}); await ruhe(w);
const dlg = alle(baum, function (n) { return n.props && n.props.role === 'dialog'; })[0];
OUT.voll = {dialog: !!dlg, label: dlg ? dlg.props['aria-label'] : '', videos: alle(baum, function (n) { return n.tag === 'video'; }).length,
  zu: alle(baum, function (n) { return n.tag === 'button' && n.props['aria-label'] === 'Vollbild schließen'; }).map(function (n) { return n.props.style.minHeight; })};
dlg.props.onKeyDown({key: 'Escape'}); await ruhe(w);
OUT.voll_esc = {dialog: alle(baum, function (n) { return n.props && n.props.role === 'dialog'; }).length, videos: alle(baum, function (n) { return n.tag === 'video'; }).length};

// ── C: Ansicht ──
OUT.C = {};
for (const ww of [390, 800, 1440]) { reset({db: {kameras: KAMS4}, fein: ww >= 1200, fetch: {status: 503, json: {}}}); w = wurzel('admin', ww); await ruhe(w); OUT.C['r' + ww] = raster(); }
reset({db: {kameras: KAMS4}, fein: true, fetch: {status: 503, json: {}}});
w = wurzel('admin', 1440); await ruhe(w); await klick(w, '3×3');
OUT.C.r3x3 = raster();
OUT.C.admin = {knoepfe: knoepfe(), text: text(baum)};
await klick(w, 'Verwaltung');
OUT.C.verw = text(baum);
reset({db: {kameras: KAMS4}, fein: true, fetch: {status: 503, json: {}}});
w = wurzel('buero', 1440); await ruhe(w);
OUT.C.buero = {knoepfe: knoepfe(), text: text(baum)};

// ── D: Demo ──
function demoZaehl() { return ZAEHL.get.length + ZAEHL.fetch.length + ZAEHL.pruef.length + ZAEHL.post.length + ZAEHL.upsert.length + ZAEHL.del.length; }
function demoBild() { const t = text(baum); return {an: alle(baum, function (n) { return n.props && n.props['data-kam-demo'] === 'an'; }).length,
  kacheln: alle(baum, function (n) { return n.props && n.props['data-kam-kachel'] === 'demo'; }).length,
  banner: (t.match(/DEMO – kein echtes Kamerabild/g) || []).length, chips: chips(), abrufe: demoZaehl(), text: t}; }
reset({db: {kameras: KAMS}, fein: true, fetch: {status: 200, json: W}, search: '?kameras_demo=1'});
w = wurzel('admin'); await ruhe(w);
OUT.D = {admin: demoBild(), ls: LS[KAMERA_DEMO_LS] || ''};
const dv = alle(baum, function (n) { return n.tag === 'button' && n.props['aria-label'] === 'Vollbild Hochregal 01'; })[0];
dv.props.onClick({}); await ruhe(w);
OUT.D.voll = demoBild();
const ddlg = alle(baum, function (n) { return n.props && n.props.role === 'dialog'; })[0];
ddlg.props.onKeyDown({key: 'Escape'}); await ruhe(w);
await klick(w, 'Demo beenden');
OUT.D.beendet = {ls: LS[KAMERA_DEMO_LS] || '', demo: alle(baum, function (n) { return n.props && n.props['data-kam-demo'] === 'an'; }).length};
for (const rolle of ['buero', 'projektleiter', 'lagerleitung', 'monteur']) {
  reset({db: {kameras: KAMS}, fein: true, fetch: {status: 403, json: {error: 'kein_zugriff'}}, search: '?kameras_demo=1'});
  LS[KAMERA_DEMO_LS] = '1';
  w = wurzel(rolle); await ruhe(w);
  OUT.D[rolle] = demoBild();
}
reset({db: {kameras: KAMS}, fein: true, fetch: {status: 503, json: {}}});
LS[KAMERA_DEMO_LS] = '1';
w = wurzel('admin'); await ruhe(w);
OUT.D.gemerkt = demoBild();
reset({db: {kameras: KAMS}, fein: true, fetch: {status: 503, json: {}}, search: '?kameras_demo=0'});
LS[KAMERA_DEMO_LS] = '1';
w = wurzel('admin'); await ruhe(w);
OUT.D.aus = {bild: demoBild(), ls: LS[KAMERA_DEMO_LS] || ''};
reset({db: {kameras: KAMS}, fein: true, fetch: {status: 503, json: {}}});
w = wurzel('admin'); await ruhe(w);
OUT.D.standard = demoBild();
// Schalter "Demo-Ansicht" nur, solange keine Kamera angelegt ist
reset({db: {kameras: []}, fein: true, einrichtung: {status: 200, json: {einrichtung: true, secret: false, basis: ''}}});
w = wurzel('admin'); await ruhe(w);
OUT.D.schalter_leer = knoepfe().indexOf('Demo-Ansicht') >= 0;
await klick(w, 'Demo-Ansicht');
OUT.D.schalter_an = {an: alle(baum, function (n) { return n.props && n.props['data-kam-demo'] === 'an'; }).length, ls: LS[KAMERA_DEMO_LS] || ''};
reset({db: {kameras: KAMS}, fein: true, fetch: {status: 503, json: {}}});
w = wurzel('admin'); await ruhe(w);
OUT.D.schalter_mit_kamera = knoepfe().indexOf('Demo-Ansicht') >= 0;
"""


def _lauf(node_exe, block=None):
    return _render_lauf(node_exe, block if block is not None else _block(), SZENEN)


@pytest.fixture(scope="module")
def U(node_exe):
    return _lauf(node_exe)


# ── A ──
def test_statuschip_je_fall(U):
    A = U["A"]
    assert A["status"] == ["live", "verbindet", "verbindet", "kein_zugriff", "server", "server", "offline", "offline", "server"]
    assert A["ausHttp"] == ["kein_zugriff", "kein_zugriff", "server", "server", "server"]
    assert A["txt"]["kein_zugriff"] == "kein Zugriff jetzt (Zeitfenster)" and A["txt"]["server"] == "Server nicht erreichbar"
    assert A["txt"]["offline"] == "Kamera nicht erreichbar" and A["txt"]["verbindet"] == "verbindet"


def test_wiederholung_spalten_erneuerung(U):
    A = U["A"]
    assert A["backoff"] == [2000, 5000, 10000, None, None]
    assert A["spalten"] == [1, 1, 2, 1, 2, 3, 2, 3, 1]
    assert A["stufe"] == ["schmal", "mittel", "breit", "breit"]
    # Token lebt <= 120 s: Erneuerung 20 s vor Ablauf, nie unter 5 s, nie ueber 120 s
    assert A["refresh"] == [70000, 5000, 120000]


# ── B ──
def test_403_kein_zugriff_ohne_wiederholung(U):
    k = U["k403"]
    assert k["chips"] == ["kein_zugriff"] and k["fetch"] == 1


def test_503_server_nicht_erreichbar(U):
    k = U["k503"]
    assert k["chips"] == ["server"] and k["fetch"] == 1 and k["neu"] is True


def test_netzfehler_wiederholt_dann_neu_laden(U):
    assert U["netz_erst"]["chips"] == ["verbindet"] and U["netz_erst"]["fetch"] == 1
    e = U["netz_ende"]
    assert e["fetch"] == 4, "1 Versuch + 3 Wiederholungen"
    assert e["chips"] == ["server"] and e["neu"] is True and "Server nicht erreichbar" in e["text"]


def test_strom_nur_sichtbar_und_stopp_bei_verborgen(U):
    assert U["sicht_vorher"]["fetch"] == 0 and U["sicht_vorher"]["chips"] == ["verbindet"]
    assert U["sicht_an"]["fetch"] == 1
    v = U["sicht_verborgen"]
    assert v["fetch"] == 1 and v["chips"] == ["verbindet"] and v["bilder"] == 0
    assert U["sicht_zurueck"]["fetch"] == 2


def test_vollbild_auf_und_zu(U):
    assert U["voll_knopf"] is True
    v = U["voll"]
    assert v["dialog"] and v["label"] == "Vollbild verkauf02" and v["videos"] == 1, "nur die eine Kachel laeuft"
    assert v["zu"] == [44]
    assert U["voll_esc"] == {"dialog": 0, "videos": 4}


# ── C ──
def test_spalten_je_stufe(U):
    C = U["C"]
    assert C["r390"] == ["repeat(1,minmax(0,1fr))"]
    assert C["r800"] == ["repeat(2,minmax(0,1fr))"]
    assert C["r1440"] == ["repeat(2,minmax(0,1fr))"] and C["r3x3"] == ["repeat(3,minmax(0,1fr))"]


def test_aufzeichnungen_aus_hinweis_nur_admin(U):
    C = U["C"]
    assert "Aufzeichnungen" not in C["admin"]["knoepfe"] and "Aufzeichnungen" not in C["buero"]["knoepfe"]
    assert "Surveillance Station" in C["admin"]["text"] and "Surveillance Station" not in C["buero"]["text"]
    assert "Einrichtungs-Skript" in C["verw"]


# ── D ──
def test_demo_admin_mit_schalter(U):
    a = U["D"]["admin"]
    assert a["an"] == 1 and a["kacheln"] == 9 and a["abrufe"] == 0
    assert a["banner"] >= a["kacheln"] + 1, "Banner auf jeder Kachel und im Kopf"
    for z in ("live", "verbindet", "kein_zugriff", "offline", "spaeter"):
        assert z in a["chips"], z
    for n in ("Hochregal 01", "Verkauf 02", "Elektrolager 03", "Kamera .39", "Mobotix .32"):
        assert n in a["text"], n
    assert U["D"]["ls"] == "1"


def test_demo_vollbild_und_beenden(U):
    v = U["D"]["voll"]
    assert v["kacheln"] == 1 and v["banner"] >= 2 and v["abrufe"] == 0
    assert U["D"]["beendet"] == {"ls": "", "demo": 0}


def test_demo_nie_fuer_andere_rollen(U):
    for rolle in ("buero", "projektleiter", "lagerleitung", "monteur"):
        d = U["D"][rolle]
        assert d["an"] == 0 and d["kacheln"] == 0 and d["banner"] == 0, rolle


def test_demo_gemerkt_aus_und_standard(U):
    D = U["D"]
    assert D["gemerkt"]["an"] == 1 and D["gemerkt"]["abrufe"] == 0
    assert D["aus"]["bild"]["an"] == 0 and D["aus"]["ls"] == ""
    assert D["standard"]["an"] == 0 and D["standard"]["banner"] == 0
    assert D["schalter_leer"] is True and D["schalter_an"] == {"an": 1, "ls": "1"}
    assert D["schalter_mit_kamera"] is False


# ── Umkehrproben ──
def _mut(b, alt, neu):
    assert b.count(alt) == 1, alt
    return b.replace(alt, neu, 1)


def test_umkehrprobe_demo_ohne_adminsperre(node_exe):
    b = _mut(_block(), "if(!user||_kamRolle(user)!=='admin')return false;", "")
    b = _mut(b, "var demo=isAdmin&&demoAn===true;", "var demo=demoAn===true;")
    assert _lauf(node_exe, b)["D"]["buero"]["an"] == 1, "Umkehrprobe: Rollensperre der Demo waere blind"


def test_umkehrprobe_demo_ohne_banner(node_exe):
    b = _mut(_block(), ",h('div',{style:{position:'absolute',top:8,left:8,right:8}},_kamDemoBanner(h))", "")
    a = _lauf(node_exe, b)["D"]["admin"]
    assert a["banner"] < a["kacheln"] + 1, "Umkehrprobe: fehlendes Banner waere blind"


def test_umkehrprobe_demo_mit_abruf(node_exe):
    b = _mut(_block(), "if(demo)return function(){alive=false;};/* Demo: kein Abruf */", "")
    assert _lauf(node_exe, b)["D"]["admin"]["abrufe"] > 0, "Umkehrprobe: Abrufzaehler waere blind"


def test_umkehrprobe_403_wuerde_wiederholt(node_exe):
    b = _mut(_block(), "if(!a.ok&&a.grund==='netz'){nochmal();return;}", "if(!a.ok&&a.grund!=='x'){nochmal();return;}")
    assert _lauf(node_exe, b)["k403"]["chips"] != ["kein_zugriff"]


def test_umkehrprobe_ohne_sichtbarkeit(node_exe):
    b = _mut(_block(), "if(!aktiv){setSt({phase:'laedt',grund:'wartet'});setBild({modus:'',url:''});return function(){alive=false;};}", "")
    assert _lauf(node_exe, b)["sicht_vorher"]["fetch"] > 0
