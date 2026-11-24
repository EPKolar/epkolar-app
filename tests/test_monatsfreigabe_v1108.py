# -*- coding: utf-8 -*-
"""Monatsfreigabe (GF 24.11.2026) - Riegel fuer den Block //@MONATSFREIGABE-START..END in index.html
und fuer die gestaffelte SQL (sql/MONATSFREIGABE_v1_*). Jeder Test ist auf dem alten Stand rot (Block fehlt).

Teil A  reine Logik in Node, mit den ECHTEN Helfern aus index.html (_ezDayEff, _ezEffTage, _ezMonthGrid ...):
        Summen Tag/Woche/Monat gleich, Zaehlung gleich _ezEffTage, Fristregel, Erinnerungen, Sammel-Auswahl,
        Meldungs-Ziele (nie fremder Monteur, nie falsche Rolle) samt Umkehrproben.
Teil B  Ansichten gegen eine Mini-React-Attrappe: Monteur (Freigeben nur mit Unterschrift, Stimmt nicht nur mit
        Begruendung, nichts vor der Admin-Freigabe), Chef-Portal (nur Admin, Freigabe in der geoeffneten
        Abrechnung, Sammel-Freigabe nur geoeffnete), Buero-Liste.
Teil C  SQL-Dateien: Policies TO authenticated, Probe = Entwurf woertlich + Abbruch, Ruecknahme vollstaendig.
Fakes only - es wird nie an echte Benutzer gemeldet.
"""
import io
import json
import os
import re
import subprocess
import tempfile

import pytest

from conftest import EPK_TEST_TIMEOUT

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(WURZEL, "index.html")
SQLD = os.path.join(WURZEL, "sql")


def _lies(p):
    return io.open(p, encoding="utf-8", newline="").read().replace("\r\n", "\n")


@pytest.fixture(scope="module")
def src():
    return _lies(INDEX)


def _block(s):
    i = s.index("//@MONATSFREIGABE-START")
    j = s.index("//@MONATSFREIGABE-END", i)
    return s[i:j]


def _fn(s, name):
    """Quelltext von function NAME(...){...} - Klammern zaehlen, Strings und Kommentare ueberspringen."""
    m = re.search(r"(?:^|[;\s}])(function " + re.escape(name) + r"\()", s, re.M)
    assert m, name
    i = m.start(1)
    k = s.index("{", i)
    tiefe, p, n = 0, k, len(s)
    while p < n:
        c = s[p]
        if c in "\"'":
            q = c
            p += 1
            while p < n and s[p] != q:
                p += 2 if s[p] == "\\" else 1
        elif s.startswith("/*", p):
            p = s.index("*/", p) + 1
        elif s.startswith("//", p) and s[p - 1] != ":":
            p = s.index("\n", p)
        elif c == "{":
            tiefe += 1
        elif c == "}":
            tiefe -= 1
            if tiefe == 0:
                return s[i:p + 1]
        p += 1
    raise AssertionError("Ende nicht gefunden: " + name)


ECHT = ["_ezWtag", "_ezKey", "_ezMonthGrid", "_ezKW", "_ezDayEff", "_ezEffTage", "_ezStufeMeta", "_easterSunday",
        "_isATFeiertag", "_pzeFmtHm", "_zeMonatName", "_vrDE", "_nWort", "_bxMonatPlus", "_bxVormonat", "_ezHeuteISO", "_bxMaListe"]


def _layout(s):
    m = re.search(r"const BP_BREIT=\d+;const BP_QUER=\d+;function _layoutStufe\(w,h\)\{.*?return \"mittel\";\}", s, re.S)
    assert m
    return m.group(0).replace("const ", "var ")


PRELUDE = r"""
const FRAG = Symbol('frag');
const React = {Fragment: FRAG, createElement(type, props) { return {type, props: props || {}, children: Array.prototype.slice.call(arguments, 2)}; }};
const store = new Map(); let cur = null; let dirty = false; let effects = [];
function useState(init) { const st = cur; const i = st.i++; if (!(i in st.vals)) st.vals[i] = typeof init === 'function' ? init() : init;
  return [st.vals[i], function (v) { const nv = typeof v === 'function' ? v(st.vals[i]) : v; if (nv !== st.vals[i]) { st.vals[i] = nv; dirty = true; } }]; }
function useEffect(fn, deps) { const st = cur; const i = st.i++; const prev = st.vals[i];
  const changed = !prev || !deps || deps.length !== prev.deps.length || deps.some(function (d, k) { return d !== prev.deps[k]; });
  if (!changed) return; const alt = prev ? prev.cleanup : null; st.vals[i] = {deps: deps || [], cleanup: null};
  effects.push(function () { if (alt) alt(); const c = fn(); st.vals[i].cleanup = typeof c === 'function' ? c : null; }); }
function useRef(x) { const st = cur; const i = st.i++; if (!(i in st.vals)) st.vals[i] = {current: x === undefined ? null : x}; return st.vals[i]; }
const _react = {useState: {call: function (_, x) { return useState(x); }}, useEffect: {call: function (_, f, d) { return useEffect(f, d); }}, useRef: {call: function (_, x) { return useRef(x); }}};
function rend(el, pfad) {
  if (el === null || el === undefined || el === false || el === true || el === '') return null;
  if (typeof el === 'string' || typeof el === 'number') return String(el);
  if (Array.isArray(el)) return el.map(function (x, i) { return rend(x, pfad + '.' + i); });
  if (el.type === FRAG) return rend(el.children, pfad + '~');
  if (typeof el.type === 'function') { const key = pfad + '/' + el.type.name + ':' + (el.props.key === undefined ? '' : el.props.key);
    let st = store.get(key); if (!st) { st = {vals: {}}; store.set(key, st); } st.i = 0; cur = st;
    return rend(el.type(Object.assign({}, el.props, {children: el.children})), key); }
  return {tag: el.type, props: el.props, kinder: rend(el.children, pfad + '>' + el.type)};
}
let baum = null;
async function ruhe(w) { for (let n = 0; n < 60; n++) { dirty = false; effects = []; baum = rend(w, 'r'); const ef = effects; effects = [];
  ef.forEach(function (f) { f(); }); for (let k = 0; k < 8; k++) await new Promise(function (r) { setTimeout(r, 0); });
  if (!dirty && !ef.length) return baum; } throw new Error('keine Ruhe'); }
function text(t) { if (t === null) return ''; if (typeof t === 'string') return t; if (Array.isArray(t)) return t.map(text).join(' '); return text(t.kinder); }
function alle(t, pred, out) { out = out || []; if (!t || typeof t === 'string') return out; if (Array.isArray(t)) { t.forEach(function (x) { alle(x, pred, out); }); return out; } if (pred(t)) out.push(t); alle(t.kinder, pred, out); return out; }
function knoepfe(wort) { return alle(baum, function (n) { return n.tag === 'button' && text(n).trim().indexOf(wort) === 0; }); }
function knopf(wort) { const k = knoepfe(wort); if (!k.length) throw new Error('Knopf fehlt: ' + wort); return k[0]; }
async function klick(w, k) { await k.props.onClick({}); for (let i = 0; i < 5; i++) { await new Promise(function (r) { setTimeout(r, 5); }); await ruhe(w); } return baum; }
const NIX = function () {}; const BP_MOB = 600;
const UI = new Proxy({}, {get: function (_, k) { if (k === 'zahlen') return {}; if (typeof k === 'string' && /^f[A-Z]/.test(k)) return 14; return '#123456'; }});
const V = new Proxy({}, {get: function () { return '#654321'; }});
const CC = function () { return {}; }; const II = function () { return {}; };
const bsS = function () { return {minHeight: 44}; }; const bpS = {minHeight: 44}; const bdS = {minHeight: 44};
function _ik(n) { return React.createElement('svg', {ik: n}); }
let SIG_ON = null;
function SignaturePad(p) { SIG_ON = p.onChange; return React.createElement('canvas', {sig: p.value || ''}); }
const LS = {}; const SS = {};
const localStorage = {getItem: function (k) { return k in LS ? LS[k] : null; }, setItem: function (k, v) { LS[k] = String(v); }};
const sessionStorage = {getItem: function (k) { return k in SS ? SS[k] : null; }, setItem: function (k, v) { SS[k] = String(v); }};
function CustomEvent(n) { this.type = n; }
const window = {innerWidth: 1440, innerHeight: 900, __toast: function (t) { TOASTS.push(t); }, dispatchEvent: NIX, open: NIX};
const TOASTS = [];
const SB_REST = 'https://sb.test/rest/v1'; const SB_STORAGE = 'https://sb.test/storage/v1'; const SB_DOCS_BUCKET = 'epkolar-docs';
const STEMPEL_PAUSE_FALLBACK = {default: 30};
function _authRetry(fn) { return fn(); } function _fT(i) { return i; }
function _sbH(x) { return Object.assign({apikey: 'k'}, x || {}); } function _sbWH(p) { return _sbH({Prefer: p}); }
function _dataUrlToBlob(d) { return d ? {size: 10, type: 'image/png'} : null; } function _netzUploadMsFuer() { return 1000; }
async function _sbSignedDocUrl(p) { return 'https://sb.test/sign/' + p; }
async function _confirmModal() { return true; }
function _maIstEhemalig() { return false; }
let DB = []; const LOG = [];
function _filter(q) { const f = {}; q.split('&').forEach(function (t) { const m = /^([a-z_]+)=(eq|in)\.(.*)$/.exec(t); if (m) f[m[1]] = m[2] === 'eq' ? [decodeURIComponent(m[3])] : m[3].replace(/[()]/g, '').split(','); }); return f; }
async function fetch(url, init) {
  const meth = (init && init.method) || 'GET'; const body = init && init.body && typeof init.body === 'string' ? JSON.parse(init.body) : (init && init.body) || null;
  LOG.push({url: url, meth: meth, body: body});
  const antw = function (st, j) { return {ok: st < 300, status: st, json: async function () { return j; }, text: async function () { return JSON.stringify(j || {}); }}; };
  if (url.indexOf('/storage/v1/object/') >= 0) return antw(200, {});
  if (url.indexOf('/monatsfreigabe_einstellungen') >= 0) return antw(200, [{erinnerung_tage: 3}]);
  if (url.indexOf('/finkzeit_verlauf') >= 0) return antw(200, []);
  if (url.indexOf('/finkzeit') >= 0) {
    const q = url.split('?')[1] || ''; const f = _filter(q);
    const passt = function (r) { return Object.keys(f).every(function (k) { return k === 'select' || k === 'order' || k === 'limit' || f[k].indexOf(String(r[k])) >= 0; }); };
    if (meth === 'GET') return antw(200, JSON.parse(JSON.stringify(DB.filter(passt))));
    if (meth === 'PATCH') { DB.filter(passt).forEach(function (r) { Object.assign(r, body); }); return antw(204, null); }
    if (meth === 'POST') { DB.push(Object.assign({}, body)); return antw(201, null); }
  }
  return antw(404, {});
}
const MELD = [];
function pushNotif(type, title, body, ziele, dedup, link) { MELD.push({type: type, title: title, body: body, ziele: ziele, dedup: dedup, link: link}); }
const USERS = [{id: 'u1', role: 'admin', active: 1}, {id: 'u2', role: 'buero', active: 1}, {id: 'u3', role: 'projektleiter', active: 1},
  {id: 'u4', role: 'monteur', active: 1, monteurId: 'w4'}, {id: 'u5', role: 'monteur', active: 1, monteurId: 'w5'}, {id: 'u6', role: 'techniker', active: 1, monteurId: 'w6'}];
function plus(iso, n) { const p = iso.split('-'); const d = new Date(Date.UTC(+p[0], +p[1] - 1, +p[2] + n)); return d.toISOString().slice(0, 10); }
"""


def _lauf(node_exe, s, szenen, mutation=None):
    blk = _block(s)
    if mutation:
        alt, neu = mutation
        assert blk.count(alt) == 1, alt
        blk = blk.replace(alt, neu)
    echt = "\n".join(_fn(s, n) for n in ECHT)
    js = PRELUDE + "\n" + _layout(s) + "\n" + echt + "\n" + blk + "\n(async function(){const OUT={};\n" + szenen + \
        "\nconsole.log(JSON.stringify(OUT));process.exit(0);})().catch(function(e){console.error(e&&e.stack||e);process.exit(3);});\n"
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "mf.cjs")
        io.open(p, "w", encoding="utf-8", newline="\n").write(js)
        r = subprocess.run([node_exe, p], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


# ── Teil A: Logik ─────────────────────────────────────────────────────────────
DATEN = r"""
const YM = '2026-10'; const WID = 'w4';
const H = {'2026-10-01': 8.5, '2026-10-02': 5.5, '2026-10-05': 9, '2026-10-06': 6.01, '2026-10-07': 7, '2026-10-26': 8, '2026-10-30': 10};
const ROWS = Object.keys(H).map(function (d) { return {datum: d, stempelAnzahl: 2, nettoMin: Math.round(H[d] * 60)}; });
const FLAGS = {}; FLAGS[_ezKey(WID, '2026-10-05')] = {stufe: 'mittel'}; FLAGS[_ezKey(WID, '2026-10-07')] = {stufe: 'gross'};
FLAGS[_ezKey(WID, '2026-10-30')] = {stufe: null}; FLAGS[_ezKey(WID, '2026-10-15')] = {stufe: 'klein'};
FLAGS[_ezKey('w9', '2026-10-01')] = {stufe: 'gross'};
const ABS = {'2026-10-26': true};
const SNAP = _mfSnapshot(WID, YM, ROWS, H, FLAGS, ABS);
"""


def test_zaehlung_gleich_ez_eff_tage_und_ansichten_gleich(node_exe, src):
    R = _lauf(node_exe, src, DATEN + r"""
const ez = _ezEffTage(H, FLAGS, WID, {klein: 1, mittel: 1, gross: 1}, ABS);
OUT.ez = [ez.tageKlein, ez.tageMittel, ez.tageGross];
OUT.snap = [SNAP.summe.z.klein, SNAP.summe.z.mittel, SNAP.summe.z.gross, SNAP.summe.min, SNAP.summe.arbeitstage];
const w = _mfWochen(SNAP);
OUT.tag = _mfZaehlen(_mfTagListe(SNAP)); OUT.woche = _mfSummeWochen(w); OUT.monat = _mfSummeMonat(w); OUT.summe = SNAP.summe;
OUT.json = JSON.stringify(SNAP);
""")
    assert R["ez"] == R["snap"][:3]
    # 01 (8,5 h -> klein), 05 mittel, 06 (6,01 -> klein), 07 gross, 15 klein (nur Flag), 26 Abwesenheit -> keine, 30 Flag keine
    assert R["snap"][:3] == [3, 1, 1]
    assert R["snap"][3] == int(round(60 * (8.5 + 5.5 + 9 + 6.01 + 7 + 8 + 10)))
    assert R["snap"][4] == 7
    assert R["tag"] == R["woche"] == R["monat"] == R["summe"]
    for verboten in ("sum", "satz", "eur"):
        assert '"' + verboten + '"' not in R["json"].lower()


def test_fristregel_wie_im_trigger(node_exe, src):
    R = _lauf(node_exe, src, r"""
const h = '2026-11-24';
OUT.r = [_mfFristStand(plus(h, -1), h, 3), _mfFristStand(h, h, 3), _mfFristStand(plus(h, 2), h, 3), _mfFristStand(plus(h, 3), h, 3), _mfFristStand('', h, 3), _mfFristStand(h, h, 0)];
""")
    assert R["r"] == ["abgelaufen", "zu_knapp", "zu_knapp", "ok", "fehlt", "ok"]


def test_erinnerungen_stoppen_nach_freigabe_und_beanstandung(node_exe, src):
    R = _lauf(node_exe, src, r"""
const h = '2026-11-24';
const rows = [{id: 'a', status: 'zur_freigabe', freigabe_bis: plus(h, 3)}, {id: 'b', status: 'zur_freigabe', freigabe_bis: plus(h, 4)},
  {id: 'c', status: 'zur_freigabe', freigabe_bis: h}, {id: 'd', status: 'freigegeben', freigabe_bis: plus(h, 1)},
  {id: 'e', status: 'in_arbeit', freigabe_bis: plus(h, 1)}, {id: 'f', status: 'zur_freigabe', freigabe_bis: plus(h, -1)}];
OUT.e = _mfErinnerungen(rows, h, 3).map(function (x) { return x.row.id + ':' + x.art; });
OUT.ab = _mfFristAbgelaufen(rows, h).map(function (x) { return x.id; });
""")
    assert R["e"] == ["a:erinnerung", "c:letzter_tag"]
    assert R["ab"] == ["f"]


SAMMEL = r"""
const h = '2026-11-24';
const rows = [{id: 'a', status: 'zur_admin_freigabe', freigabe_bis: plus(h, 10)}, {id: 'b', status: 'zur_admin_freigabe', freigabe_bis: plus(h, 10)},
  {id: 'c', status: 'zur_admin_freigabe', freigabe_bis: plus(h, 1)}, {id: 'd', status: 'zur_freigabe', freigabe_bis: plus(h, 10)}];
OUT.ids = _mfSammelAuswahl(rows, {a: true, b: true, c: true, d: true}, {a: 1, c: 1, d: 1}, h, 3);
"""


def test_sammel_nur_geoeffnete(node_exe, src):
    assert _lauf(node_exe, src, SAMMEL)["ids"] == ["a"]


def test_sammel_umkehrprobe_ohne_geoeffnet_waere_rot(node_exe, src):
    R = _lauf(node_exe, src, SAMMEL, mutation=("return r&&g[r.id]&&o[r.id]&&", "return r&&g[r.id]&&"))
    assert R["ids"] != ["a"]


MELDUNG = r"""
const row = {id: 'mf_w4_2026-10', worker_id: 'w4', period: '2026-10', freigabe_bis: '2026-12-05', worker_name: 'Max'};
function z(t, prefs) { const m = _mfMeldung(t, row, {users: USERS, prefs: prefs || null, grund: 'Tag 3 fehlt', stempel: 1}); return m; }
OUT.m = {};
['mf_admin_bereit','mf_beanstandet_admin','mf_monteur_bereit','mf_erinnerung','mf_letzter_tag','mf_zurueck_buero','mf_freigegeben','mf_beanstandet','mf_frist_abgelaufen'].forEach(function (t) {
  const m = z(t); OUT.m[t] = {ziele: m.ziele, text: m.title + ' ' + m.body, link: m.link, dedup: m.dedup}; });
OUT.aus = z('mf_monteur_bereit', {u4: {mf_monteur_bereit: false}}).ziele;
OUT.fremd = _mfMeldung('mf_monteur_bereit', Object.assign({}, row, {worker_id: 'w99'}), {users: USERS}).ziele;
"""


def test_meldungen_nur_an_betroffene(node_exe, src):
    R = _lauf(node_exe, src, MELDUNG)
    m = R["m"]
    for t in ("mf_admin_bereit", "mf_beanstandet_admin"):
        assert m[t]["ziele"] == ["u1"] and m[t]["link"].startswith("mf|_chef|")
    for t in ("mf_monteur_bereit", "mf_erinnerung", "mf_letzter_tag"):
        assert m[t]["ziele"] == ["u4"] and m[t]["link"].startswith("mf|stunden|")
    for t in ("mf_zurueck_buero", "mf_freigegeben", "mf_beanstandet", "mf_frist_abgelaufen"):
        assert m[t]["ziele"] == ["u2"] and m[t]["link"].startswith("mf|bueroexport|")
    assert R["aus"] == []          # Admin-Schalter aus -> keine Meldung
    assert R["fremd"] == []        # kein Benutzer zu dieser Abrechnung -> niemand (nie ein anderer Monteur)
    for t, v in m.items():         # kein Inhalt der Abrechnung im Text
        assert not re.search(r"\d+:\d\d", v["text"]) and "€" not in v["text"]
        assert not re.search(r"\b(klein|mittel|groß|Stunden)\b", v["text"]), (t, v["text"])
    assert len({v["dedup"] for v in m.values()}) == 9


@pytest.mark.parametrize("alt,neu", [
    ("if(rolle===\"monteur\"){var mu=_mfMonteurUser(users,row.worker_id);kand=mu?[mu]:[];}",
     "if(rolle===\"monteur\"){kand=(users||[]).filter(function(u){return u.role===\"monteur\";});}"),
    ('mf_freigegeben:"buero"', 'mf_freigegeben:"monteur"'),
])
def test_meldungen_umkehrprobe_falsches_ziel_waere_rot(node_exe, src, alt, neu):
    R = _lauf(node_exe, src, MELDUNG, mutation=(alt, neu))
    m = R["m"]
    falsch = m["mf_monteur_bereit"]["ziele"] != ["u4"] or m["mf_admin_bereit"]["ziele"] != ["u1"] or m["mf_freigegeben"]["ziele"] != ["u2"]
    assert falsch


# ── Teil B: Ansichten ────────────────────────────────────────────────────────
MONTEUR = DATEN + r"""
const heute = _ezHeuteISO();
function neu(rows) { DB = rows; store.clear(); LOG.length = 0; MELD.length = 0; SIG_ON = null; }
const W = React.createElement(MonatsfreigabeMonteur, {curUser: {id: 'u4', role: 'monteur', monteurId: 'w4', name: 'Max'}, users: USERS, pushNotif: pushNotif, ww: 1440});
// 1) nichts sichtbar (RLS liefert vor der Admin-Freigabe nichts) -> wird noch erstellt
neu([]); await ruhe(W);
OUT.leer = text(baum);
// 2) zur_freigabe
neu([{id: 'mf_w4_2026-10', worker_id: 'w4', period: '2026-10', status: 'zur_freigabe', freigabe_bis: plus(heute, 10), snapshot: SNAP, worker_name: 'Max'}]);
await ruhe(W);
OUT.offen = text(baum);
OUT.freigebenAus = knopf('Freigeben').props.disabled;
await klick(W, knopf('Freigeben'));
OUT.ohneSigPatch = LOG.filter(function (l) { return l.meth !== 'GET'; }).length;
// Stimmt nicht: Senden erst mit Begruendung
await klick(W, knopf('Stimmt nicht'));
OUT.sendenAus = knopf('An das Büro senden').props.disabled;
// Ansichten: Tag/Woche/Monat zeigen dieselbe Summe
function hm(s) { const m = /(\d+):(\d\d)/.exec(s); return m ? (+m[1]) * 60 + (+m[2]) : 0; }
const tagMin = alle(baum, function (n) { return n.props && n.props['data-mf-tag']; }).reduce(function (s, n) { return s + hm(text(n.kinder[1])); }, 0);
await klick(W, knopf('Monat'));
const monMin = alle(baum, function (n) { return n.props && n.props['data-mf-mtag']; }).reduce(function (s, n) { return s + hm(text(n.kinder[1])); }, 0);
await klick(W, knopf('Woche'));
let wMin = 0; const gesehen = {};
for (let i = 0; i < 8; i++) { const wk = alle(baum, function (n) { return n.props && n.props['data-mf-woche']; })[0]; const kw = wk.props['data-mf-woche'];
  if (!gesehen[kw]) { gesehen[kw] = 1; wMin += hm(text(alle(baum, function (n) { return n.props && n.props['data-mf-wsumme']; })[0])); }
  const vor = alle(baum, function (n) { return n.tag === 'button' && n.props['aria-label'] === 'Woche vor'; })[0]; if (vor.props.disabled) break; await klick(W, vor); }
OUT.summen = [tagMin, monMin, wMin, SNAP.summe.min];
// Unterschrift -> Freigeben frei -> Upload VOR dem Statuswechsel, Meldung nur ans Buero
SIG_ON('data:image/png;base64,AAAA'); await ruhe(W);
OUT.freigebenMitSig = knopf('Freigeben').props.disabled;
await klick(W, knopf('Freigeben'));
OUT.schreib = LOG.filter(function (l) { return l.meth !== 'GET'; }).map(function (l) { return l.meth + ' ' + (l.url.indexOf('/storage/') >= 0 ? 'storage:' + l.url.split('epkolar-docs/')[1].split('/').slice(0, 2).join('/') : 'finkzeit') + ' ' + JSON.stringify(l.body && l.body.status ? {status: l.body.status, sig: !!l.body.signatur_pfad} : {}); });
OUT.meld = MELD.map(function (m) { return m.type + '>' + m.ziele.join(','); });
OUT.nach = text(baum);
"""


def test_monteur_ansicht(node_exe, src):
    R = _lauf(node_exe, src, MONTEUR)
    assert "wird noch erstellt" in R["leer"] and "Freigeben" not in R["leer"]
    assert "Freigabe bis spätestens" in R["offen"] and "Stempelstunden gesamt" in R["offen"]
    assert "€" not in R["offen"] and "EUR" not in R["offen"]
    assert R["freigebenAus"] is True and R["ohneSigPatch"] == 0
    assert R["sendenAus"] is True
    assert R["summen"][0] == R["summen"][1] == R["summen"][2] == R["summen"][3]
    assert R["freigebenMitSig"] is False
    assert R["schreib"][0].startswith("POST storage:monatsfreigabe/w4")
    assert R["schreib"][1] == 'PATCH finkzeit {"status":"freigegeben","sig":true}'
    assert R["meld"] == ["mf_freigegeben>u2"]


def test_monteur_umkehrprobe_freigeben_ohne_unterschrift_waere_rot(node_exe, src):
    R = _lauf(node_exe, src, MONTEUR.split("// Stimmt nicht")[0], mutation=('disabled:!sig||busy,onClick:freigeben', 'disabled:busy,onClick:freigeben'))
    assert R["freigebenAus"] is False


CHEF = r"""
const heute = _ezHeuteISO();
const S = {v: 1, ym: '2026-10', tage: [{d: '2026-10-01', min: 480, st: 'klein'}], summe: {min: 480, arbeitstage: 1, z: {klein: 1, mittel: 0, gross: 0}}};
function neu() { DB = [{id: 'A', worker_id: 'w4', period: '2026-10', status: 'zur_admin_freigabe', freigabe_bis: plus(heute, 10), snapshot: S, worker_name: 'Max'},
  {id: 'B', worker_id: 'w5', period: '2026-10', status: 'zur_admin_freigabe', freigabe_bis: plus(heute, 10), snapshot: S, worker_name: 'Moritz'},
  {id: 'C', worker_id: 'w6', period: '2026-10', status: 'zur_admin_freigabe', freigabe_bis: plus(heute, 1), snapshot: S, worker_name: 'Tom'}];
  store.clear(); LOG.length = 0; MELD.length = 0; for (const k in SS) delete SS[k]; }
const MON = [{id: 'w4', n: 'Max'}, {id: 'w5', n: 'Moritz'}, {id: 'w6', n: 'Tom'}];
neu(); let W = React.createElement(MonatsfreigabeChef, {curUser: {id: 'u2', role: 'buero'}, users: USERS, monteure: MON, pushNotif: pushNotif, ww: 1440});
await ruhe(W); OUT.buero = text(baum); OUT.bueroGet = LOG.length;
neu(); W = React.createElement(MonatsfreigabeChef, {curUser: {id: 'u1', role: 'admin'}, users: USERS, monteure: MON, pushNotif: pushNotif, ww: 1440});
await ruhe(W);
OUT.liste = text(baum);
const boxen = function () { return alle(baum, function (n) { return n.tag === 'input' && n.props.type === 'checkbox'; }); };
OUT.boxAnfangs = boxen().map(function (b) { return b.props.disabled; });
OUT.freigebenVorOeffnen = knoepfe('Freigeben').length;
await klick(W, knopf('Öffnen'));
OUT.freigebenNachOeffnen = knoepfe('Freigeben').map(function (k) { return k.props['data-mf-chef-freigeben']; });
// Haken bei A (geoeffnet) und B (NICHT geoeffnet - Haken per Hand erzwungen)
boxen()[0].props.onChange({target: {checked: true}}); await ruhe(W);
boxen()[1].props.onChange({target: {checked: true}}); await ruhe(W);
OUT.sammelText = text(alle(baum, function (n) { return n.props && n.props['data-mf-sammel']; })[0]);
await klick(W, alle(baum, function (n) { return n.props && n.props['data-mf-sammel']; })[0]);
OUT.patches = LOG.filter(function (l) { return l.meth === 'PATCH'; }).map(function (l) { return l.url.split('id=eq.')[1] + ':' + l.body.status; });
OUT.meld = MELD.map(function (m) { return m.type + '>' + m.ziele.join(','); });
// C: Frist zu knapp -> Freigeben gesperrt
neu(); SS['epk_mf_geoeffnet'] = JSON.stringify({C: 1}); store.clear(); await ruhe(W);
const oeffnenC = knoepfe('Öffnen')[2]; await klick(W, oeffnenC);
OUT.cGesperrt = alle(baum, function (n) { return n.props && n.props['data-mf-chef-freigeben'] === 'C'; })[0].props.disabled;
OUT.cText = text(baum);
"""


def test_chef_portal(node_exe, src):
    R = _lauf(node_exe, src, CHEF)
    assert R["buero"] == "" and R["bueroGet"] == 0
    assert "Monatsabrechnungen zur Freigabe" in R["liste"] and "8:00 h" in R["liste"] and "€" not in R["liste"]
    assert R["boxAnfangs"] == [True, True, True]
    assert R["freigebenVorOeffnen"] == 0
    assert R["freigebenNachOeffnen"] == ["A"]
    assert "(1)" in R["sammelText"]
    assert R["patches"] == ["A:zur_freigabe"]
    assert R["meld"] == ["mf_monteur_bereit>u4"]
    assert R["cGesperrt"] is True and "zu knapp" in R["cText"]


BUERO = r"""
const heute = _ezHeuteISO();
DB = [{id: 'mf_w4_2026-10', worker_id: 'w4', period: '2026-10', status: 'in_arbeit', beanstandung: 'Am 3. fehlt eine Stunde', snapshot: null, worker_name: 'Max'},
      {id: 'mf_w5_2026-10', worker_id: 'w5', period: '2026-10', status: 'zur_freigabe', freigabe_bis: plus(heute, -2), snapshot: null, worker_name: 'Moritz'}];
const W = React.createElement(MonatsfreigabeBuero, {ym: '2026-10', monteure: [{id: 'w4', n: 'Max'}, {id: 'w5', n: 'Moritz'}, {id: 'w6', n: 'Tom'}], users: USERS, curUser: {id: 'u2', role: 'buero'}, abs: {}, approvals: {}, pushNotif: pushNotif, ww: 1440});
await ruhe(W);
OUT.t = text(baum);
OUT.ohne = knoepfe('Ohne Monteur-Freigabe freigeben').length;
OUT.meld = MELD.map(function (m) { return m.type + '>' + m.ziele.join(','); });
"""


def test_buero_liste(node_exe, src):
    R = _lauf(node_exe, src, BUERO)
    assert "Monteur: Am 3. fehlt eine Stunde" in R["t"]
    assert "Noch nicht angelegt" in R["t"] and "Abrechnung anlegen" in R["t"]
    assert "Erinnerung an den Monteur: 3 Tage" in R["t"]
    assert R["ohne"] == 1
    assert R["meld"] == ["mf_frist_abgelaufen>u2"]


def test_verdrahtung(src):
    assert 'mf_monteur_bereit:{l:"Monatsabrechnung liegt bereit"' in src
    assert src.count('const _typeTab={deadline_fz:"fahrzeuge"};Object.assign(_typeTab,_mfNotifTab(n));') == 2
    assert '["freigabe","Monatsfreigabe"]' in src
    assert "React.createElement(MonatsfreigabeChef" in src and "React.createElement(MonatsfreigabeMonteur" in src
    assert "if(tab===\"freigabe\")inhalt=h(MonatsfreigabeBuero" in src
    assert "'&status=not.in.(genehmigt,freigegeben)&select=worker_id,monat,status'" in src
    assert "data.filter(d=>!_mfIstNeu(d.status))" in src
    blk = _block(src)
    for verboten in ("_ezSaetze", "_ezEffTage(", "KV_RULES", "€", "pdf_data:ev", "SQ.push"):
        assert verboten not in blk, verboten


# ── Teil C: SQL ──────────────────────────────────────────────────────────────
def test_sql_entwurf_probe_ruecknahme():
    e = _lies(os.path.join(SQLD, "MONATSFREIGABE_v1_ENTWURF.sql"))
    p = _lies(os.path.join(SQLD, "MONATSFREIGABE_v1_PROBE.sql"))
    r = _lies(os.path.join(SQLD, "MONATSFREIGABE_v1_RUECKNAHME.sql"))
    pol = re.findall(r"CREATE POLICY (\w+) ON ([\w.]+) FOR \w+ TO (\w+)", e)
    assert len(pol) == 11 and all(x[2] == "authenticated" for x in pol)
    assert "DROP POLICY finkzeit_staff_all" in e and "projektleiter" not in re.search(r"CREATE POLICY finkzeit_buero_admin.*?;", e, re.S).group(0)
    assert e in p and p.rstrip().endswith("ROLLBACK;") and "RAISE EXCEPTION 'PROBE_ERGEBNIS" in p
    assert "set_config('request.jwt.claims', '', true)" not in p
    for name in [x[0] for x in pol]:
        if name.startswith("epkolar_docs") or name in ("finkzeit_buero_admin", "finkzeit_monteur_select", "finkzeit_monteur_update", "monatsfreigabe_monteur_insert"):
            assert ("DROP POLICY IF EXISTS " + name) in r, name
    assert "CREATE POLICY finkzeit_staff_all" in r and "DROP TABLE IF EXISTS public.finkzeit_verlauf" in r
    assert "nur der Admin gibt an den Monteur frei" in e
