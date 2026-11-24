# -*- coding: utf-8 -*-
"""Dispo mobil + "Verschieben ist nicht bestaetigt" (GF 24.11.2026, Weg B).

Was hier AUSGEFUEHRT wird (Node, nicht nur gelesen):
  1. Der Block //@DISPOMOBIL-START..END aus index.html samt der echten _layoutStufe,
     _maIstEhemalig, _nWort, _dauerKurzDE und JUPROWA_PUSH_FIELDS.
  2. _chipDrag aus DispoPanel mit nachgebautem document/window: Finger und Stift starten in der
     Stufe breit KEIN Ziehen (kein Listener, kein onDrop), die Maus zieht wie bisher.
  3. Die echten onDrop/onUebernehmen-Handler aus ArbeitsscheinView, verdrahtet ueber den echten
     _dispoPlanSchreiben: geschrieben werden NUR dispo_*-Spalten, kein updAs, kein Push.
  4. Termin bestaetigen: genau EIN updAs-Aufruf, und der traegt ein Push-Feld (= genau ein Push).
  5. Tageskarten, Monatszahl und Wochenuebersicht gerendert (Mini-React): Monatszahl = Tageszahl,
     Inhaltsschrift >= 13 px, Tippziele >= 44 px.

Jede Pruefung ist eine Funktion pruefe_*(quelle). Die Gegenproben fahren dieselbe Funktion gegen
den Stand vor dem Umbau (origin/main f0c1c86) und verlangen, dass sie dort ROT ist.
"""
import io
import json
import os
import re
import subprocess
import tempfile

import pytest

from conftest import EPK_TEST_TIMEOUT, _extract_fn

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(WURZEL, "index.html")
ALT_REF = "f0c1c86"


def _neu():
    return io.open(INDEX, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def _alt():
    try:
        r = subprocess.run(["git", "-C", WURZEL, "show", ALT_REF + ":index.html"], capture_output=True,
                           timeout=EPK_TEST_TIMEOUT)
    except Exception:
        pytest.skip("git nicht verfuegbar")
    if r.returncode != 0:
        pytest.skip("Altstand %s nicht im Repo" % ALT_REF)
    return r.stdout.decode("utf-8").replace("\r\n", "\n")


def _block(q):
    i = q.index("//@DISPOMOBIL-START")
    j = q.index("//@DISPOMOBIL-END", i)
    return q[i:j]


def _layout(q):
    m = re.search(r"const BP_BREIT=\d+;const BP_QUER=\d+;function _layoutStufe\(w,h\)\{.*?return \"mittel\";\}", q, re.S)
    assert m
    return m.group(0).replace("const ", "var ")


def _push_felder(q):
    i = q.index("const JUPROWA_PUSH_FIELDS={")
    j = q.index("};", i)
    return "var " + q[i + len("const "):j + 2]


PRELUDE = r"""
const FRAG = Symbol('frag');
const React = {Fragment: FRAG, createElement(type, props) { const kinder = Array.prototype.slice.call(arguments, 2); return {type, props: props || {}, children: kinder}; }};
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
  if (el.type === FRAG) return rend(el.children, pfad + '~' + (el.props.key || ''));
  if (typeof el.type === 'function') { const key = pfad + '/' + el.type.name + ':' + (el.props.key === undefined ? '' : el.props.key);
    let st = store.get(key); if (!st) { st = {vals: {}}; store.set(key, st); } st.i = 0; cur = st;
    return rend(el.type(Object.assign({}, el.props, {children: el.children})), key); }
  return {tag: el.type, props: el.props, kinder: rend(el.children, pfad + '>' + el.type)};
}
let baum = null;
function ruhe(w) { for (let n = 0; n < 30; n++) { dirty = false; effects = []; baum = rend(w, 'r'); const ef = effects; effects = []; ef.forEach(function (f) { f(); }); if (!dirty && !ef.length) return baum; } throw new Error('keine Ruhe'); }
function text(t) { if (t === null) return ''; if (typeof t === 'string') return t; if (Array.isArray(t)) return t.map(text).join(' '); return text(t.kinder); }
function alle(t, pred, out) { out = out || []; if (!t || typeof t === 'string') return out; if (Array.isArray(t)) { t.forEach(function (x) { alle(x, pred, out); }); return out; } if (pred(t)) out.push(t); alle(t.kinder, pred, out); return out; }
const UI = {fMeta: 12, fKlein: 13, fText: 14, fTitel: 15, rKarte: 12, rChip: 6, marke: '#009640', markeTxt: '#00722F', markeBg: '#E8F4EC', achtung: '#B4530A', achtungTxt: '#8A3E06', achtungBg: '#FBEDE1', neutralTxt: '#414B45', neutralBg: '#EEF1EF', knopf: '#00843A'};
const V = new Proxy({}, {get: function () { return '#654321'; }});
const _knB = {padding: '9px 18px', borderRadius: 8, fontWeight: 600, fontSize: 13, minHeight: 44};
const bsS = function () { return Object.assign({}, _knB); }; const bpS = Object.assign({}, _knB);
const IKON = {};
function _ik(n, g) { return React.createElement('svg', {ik: n, width: g}); }
const AS_GRP_OFFEN = ["aufgenommen", "freigegeben", "in_bearbeitung", "aufgeschoben"];
function isoWof() { return 48; }
function _dispoAbwLabel(t) { return {icon: 'x', label: String(t) === 'krank' ? 'Krankenstand' : 'Urlaub'}; }
const document = {addEventListener: function () {}, removeEventListener: function () {}};
const window = {innerWidth: 390, innerHeight: 844};
const BP_MOB = 600;
"""


def _node(node_exe, js):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.cjs")
        with io.open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(js)
        r = subprocess.run([node_exe, p], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 0, (r.stderr or r.stdout)[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def _umgebung(q):
    teile = [PRELUDE, _layout(q)]
    for n in ("_maIstEhemalig", "_nWort", "_dauerKurzDE"):
        f = _extract_fn(q, n)
        assert f, n
        teile.append(f)
    teile.append(_push_felder(q))
    teile.append(_block(q))
    return "\n".join(teile)


# ═══ 1. Reine Helfer ═══════════════════════════════════════════════════════
REIN_JS = r"""
const O = {};
const S = function (a) { return _asPlanung(a).stand; };
O.stand = {
  leer: S({}), wunsch: S({terminVorschlag: '2026-11-30'}),
  bestaetigt: S({terminBestaetigt: '2026-11-30', terminZeit: '08:00'}),
  geplant: S({terminVorschlag: '2026-11-30', dispoDatum: '2026-12-01'}),
  gleich: S({terminBestaetigt: '2026-11-30', terminZeit: '08:00', dispoDatum: '2026-11-30', dispoZeit: '08:00'}),
  abweichend: S({terminBestaetigt: '2026-11-30', dispoDatum: '2026-12-02'}),
  abwZeit: S({terminBestaetigt: '2026-11-30', terminZeit: '08:00', dispoDatum: '2026-11-30', dispoZeit: '10:00'}),
  sentinel: S({terminBestaetigt: '0001-01-01'}),
  geleert: S({terminBestaetigt: '2026-11-30', dispoDatum: null, dispo_datum: '2026-12-09'})
};
O.stufe = {handy: _dispoAnsicht(386, 800), handyQuer: _dispoAnsicht(915, 412), handyQuer2: _dispoAnsicht(740, 360),
  tabletHoch: _dispoAnsicht(800, 1280), tabletQuer: _dispoAnsicht(1280, 800), pc: _dispoAnsicht(1440, 900)};
O.drag = {};
['mouse', 'touch', 'pen', ''].forEach(function (pt) { ['schmal', 'mittel', 'breit'].forEach(function (st) { O.drag[pt + '_' + st] = _dispoDragErlaubt({pointerType: pt}, st); }); });
O.body = _dispoPlanBody({datum: '2026-12-01', zeit: '08:00', dauer: '02:00', monteur: 'w1'});
O.bodyLeer = _dispoPlanBody({datum: null, zeit: ''});
const PF = Object.keys(JUPROWA_PUSH_FIELDS);
(async function () {
  const calls = [];
  const patch = async function (t, id, b) { calls.push({t: t, id: id, b: b}); return [{id: id}]; };
  O.schreibBuero = await _dispoPlanSchreiben('A1', {datum: '2026-12-01', zeit: '08:00', dauer: '02:00'}, 'buero', patch);
  O.schreibMonteur = await _dispoPlanSchreiben('A1', {datum: '2026-12-01'}, 'monteur', patch);
  O.schreibTechniker = await _dispoPlanSchreiben('A1', {datum: '2026-12-01'}, 'techniker', patch);
  O.calls = calls;
  O.fehlendeSpalte = await _dispoPlanSchreiben('A1', {datum: '2026-12-01'}, 'admin', async function () { throw new Error('HTTP400 {"code":"PGRST204","message":"Could not find the dispo_datum column"}'); });
  O.offline = await _dispoPlanSchreiben('A1', {datum: '2026-12-01'}, 'admin', async function () { throw new TypeError('Failed to fetch'); });
  O.verweigert = await _dispoPlanSchreiben('A1', {datum: '2026-12-01'}, 'admin', async function () { return []; });
  // Termin bestaetigen
  const upd = [];
  const fakeUpd = function (id, u) { upd.push({id: id, u: u, push: PF.some(function (k) { return k in u; })}); return true; };
  const s = {id: 'A2', monteur: 'w1', dauer: '01:00', terminBestaetigt: '2026-11-30', terminZeit: '08:00', dispoDatum: '2026-12-02', dispoZeit: '09:30', dispoDauer: '02:00', dispoMonteur: 'w4'};
  O.best = _asTerminBestaetigen(s, 'projektleiter', fakeUpd);
  O.bestMonteur = _asTerminBestaetigen(s, 'monteur', fakeUpd);
  O.bestOhnePlan = _asTerminBestaetigen({id: 'A3', terminBestaetigt: '2026-11-30'}, 'admin', fakeUpd);
  O.upd = upd;
  O.nachher = _asPlanung(Object.assign({}, s, O.best.patch)).stand;
  console.log(JSON.stringify(O));
})();
"""


def pruefe_rein(node_exe, q):
    R = _node(node_exe, _umgebung(q) + REIN_JS)
    st = R["stand"]
    assert st == {"leer": "", "wunsch": "wunsch", "bestaetigt": "bestaetigt", "geplant": "geplant", "gleich": "bestaetigt",
                  "abweichend": "abweichend", "abwZeit": "abweichend", "sentinel": "", "geleert": "bestaetigt"}, st
    assert R["stufe"] == {"handy": "schmal", "handyQuer": "schmal", "handyQuer2": "schmal", "tabletHoch": "mittel",
                          "tabletQuer": "breit", "pc": "breit"}, R["stufe"]
    for k, v in R["drag"].items():
        assert v == (k == "mouse_breit"), (k, v)
    assert R["body"] == {"dispo_datum": "2026-12-01", "dispo_zeit": "08:00", "dispo_dauer": "02:00", "dispo_monteur": "w1"}
    assert R["bodyLeer"] == {"dispo_datum": None, "dispo_zeit": None}
    assert R["schreibBuero"]["ok"] is True
    assert R["schreibMonteur"]["ok"] is False and R["schreibTechniker"]["ok"] is False
    assert len(R["calls"]) == 1, R["calls"]
    assert all(k.startswith("dispo_") for k in R["calls"][0]["b"]), R["calls"][0]
    assert R["fehlendeSpalte"]["ok"] is False and "Planungsfelder" in R["fehlendeSpalte"]["text"]
    assert R["offline"]["ok"] is False and "Verbindung" in R["offline"]["text"]
    assert R["verweigert"]["ok"] is False
    assert R["best"]["ok"] is True and R["bestMonteur"]["ok"] is False and R["bestOhnePlan"]["ok"] is False
    assert len(R["upd"]) == 1, R["upd"]
    u = R["upd"][0]["u"]
    assert R["upd"][0]["push"] is True
    assert u["terminBestaetigt"] == "2026-12-02" and u["terminZeit"] == "09:30" and u["monteur"] == "w4" and u["dauer"] == "02:00"
    assert u["dispoDatum"] is None and u["dispoMonteur"] is None
    assert R["nachher"] == "bestaetigt"


def test_reine_helfer(node_exe):
    pruefe_rein(node_exe, _neu())


def test_gegenprobe_reine_helfer_alt_rot(node_exe):
    with pytest.raises((AssertionError, ValueError)):
        pruefe_rein(node_exe, _alt())


# ═══ 2. Ziehen: Finger/Stift nie, Maus schreibt nur Planung ══════════════════
def _chipdrag(q):
    i = q.index("  var _chipDrag=function(scheinId,mid,label,dauerMin,opts){return function(e){")
    j = q.index("  /* v3.9.733 #16b-neu", i)
    return q[i:j]


def _handler(q, name, ende):
    i = q.index(name + ": (")
    j = q.index(ende, i)
    return "var " + name + "=" + q[i + len(name) + 2:j + 1] + ";"


DRAG_JS = r"""
const LOG = {listener: 0, onDrop: [], prevent: 0, updAs: [], plan: [], push: 0, sq: 0, patch: []};
const CELL = {getAttribute: function (k) { return {'data-monteur': 'w1', 'data-iso': '2026-12-02', 'data-hardblock': '0', 'data-norm': '510', 'data-used': '0', 'data-hardlabel': ''}[k]; }};
Object.assign(document, {body: {style: {}, appendChild: function () {}}, addEventListener: function () {}, removeEventListener: function () {},
  createElement: function () { return {style: {}, remove: function () {}}; }, elementFromPoint: function () { return {closest: function () { return CELL; }}; }});
const LIS = {};
Object.assign(window, {innerWidth: 1440, innerHeight: 900, getSelection: function () { return null; }, __toast: function () {},
  addEventListener: function (n, f) { LOG.listener++; LIS[n] = f; }, removeEventListener: function (n) { delete LIS[n]; }});
const DISPO_DRAG_SCHWELLE = 6; const PUFFER_JE_STOPP = 15;
function _dispoDropOk(a, b, hb, frei, d) { return a === b && !hb && (d + 15) <= frei; }
function _dispoAblehnGrund() { return 'x'; }
function _dragSelOff() {} function _dragSelRestore() {} function _setDropFb() {} function _gestureEnd() {}
const _dragRef = {current: null}, _gestureRef = {current: false}, _suppressClickRef = {current: 0}, _kwHoverRef = {current: null};
// echte Handler aus ArbeitsscheinView, verdrahtet ueber den echten _dispoPlanSchreiben
const arbeitsscheine = [{id: 'A1', nummer: 'S1', monteur: 'w1', juprowa_id: 7}];
const monteure = [{id: 'w1', n: 'Eins'}];
function updAs(id, u) { LOG.updAs.push(u); return true; }
function _juprowaSchedulePush() { LOG.push++; }
const SQ = {push: function () { LOG.sq++; }};
function _dispoMinToHHMM(m) { var mm = Math.max(0, Math.round(m || 0)); return String(Math.floor(mm / 60)).padStart(2, '0') + ':' + String(mm % 60).padStart(2, '0'); }
const _sbPatchFake = async function (t, id, b) { LOG.patch.push(b); return [{id: id}]; };
const dispoPlanen = async function (id, plan, was) { LOG.plan.push(plan); if (typeof _dispoPlanSchreiben === 'function') return _dispoPlanSchreiben(id, plan, 'buero', _sbPatchFake); return false; };
const canSync = true; const terminBestaetigen = function () {}; const setArbeitsscheine = function () {};
__HANDLER__
const onDrop = __ONDROP__;
__CHIPDRAG__
(async function () {
  const O = {};
  function geste(pt) {
    LOG.listener = 0; const h = _chipDrag('A1', 'w1', 'S1', 60, {startHHMM: '08:00', srcIso: '2026-12-01'});
    h({pointerType: pt, clientX: 10, clientY: 10, preventDefault: function () { LOG.prevent++; }});
    const lis = LOG.listener;
    if (LIS.pointermove) { LIS.pointermove({clientX: 60, clientY: 60}); LIS.pointerup({clientX: 60, clientY: 60}); }
    return lis;
  }
  O.touch = geste('touch'); O.touchDrop = LOG.onDropN || 0;
  O.pen = geste('pen');
  const vorMaus = {plan: LOG.plan.length, updAs: LOG.updAs.length};
  O.vorMaus = vorMaus;
  O.mouse = geste('mouse');
  await new Promise(function (r) { setTimeout(r, 10); });
  O.log = JSON.parse(JSON.stringify(LOG));
  // Uebernehmen
  if (typeof onUebernehmen === 'function') { onUebernehmen('A1', 'w1', '2026-12-03', 90, '10:00'); }
  await new Promise(function (r) { setTimeout(r, 10); });
  O.log2 = {plan: LOG.plan.length, updAs: LOG.updAs.length, push: LOG.push, sq: LOG.sq, patch: LOG.patch};
  console.log(JSON.stringify(O));
})();
"""


def pruefe_ziehen(node_exe, q):
    uml = _umgebung(q) if "//@DISPOMOBIL-START" in q else (PRELUDE + _layout(q))
    js = DRAG_JS.replace("__CHIPDRAG__", _chipdrag(q))
    js = js.replace("__ONDROP__", _handler(q, "onDrop", "}, onToggleBlock:")[len("var onDrop="):-1])
    js = js.replace("__HANDLER__", _handler(q, "onUebernehmen", "}, onOpenSchein:"))
    # PRELUDE definiert document/window - fuer diesen Lauf ersetzen
    R = _node(node_exe, uml + js)
    L = R["log"]
    assert R["touch"] == 0, "Finger startet ein Ziehen (Listener %s)" % R["touch"]
    assert R["pen"] == 0, "Stift startet ein Ziehen"
    assert R["vorMaus"] == {"plan": 0, "updAs": 0}, R["vorMaus"]
    assert R["mouse"] == 3, "Maus startet kein Ziehen (%s)" % R["mouse"]
    assert len(L["plan"]) == 1, L
    assert L["plan"][0] == {"datum": "2026-12-02", "zeit": "08:00", "dauer": "01:00"}, L["plan"][0]
    assert L["updAs"] == [], "Ziehen schreibt ueber updAs (Terminfelder/Push): %s" % L["updAs"]
    assert L["push"] == 0 and L["sq"] == 0
    assert len(L["patch"]) == 1 and set(L["patch"][0]) == {"dispo_datum", "dispo_zeit", "dispo_dauer"}, L["patch"]
    L2 = R["log2"]
    assert L2["plan"] == 2 and L2["updAs"] == 0 and L2["push"] == 0 and L2["sq"] == 0, L2
    assert set(L2["patch"][1]) == {"dispo_datum", "dispo_zeit", "dispo_dauer", "dispo_monteur"}, L2["patch"]


def test_ziehen_nur_maus_schreibt_nur_planung(node_exe):
    pruefe_ziehen(node_exe, _neu())


def test_gegenprobe_ziehen_alt_rot(node_exe):
    with pytest.raises(AssertionError):
        pruefe_ziehen(node_exe, _alt())


# ═══ 3. Tageskarten / Monat / Woche gerendert ═════════════════════════════
KARTEN_JS = r"""
const H = '2026-11-25';
const M = [{id: 'w1', n: 'Anna', r: 'Monteur'}, {id: 'w2', n: 'Bert', r: 'Monteur'}, {id: 'w3', n: 'Cora', r: 'Monteur'}, {id: 'b1', n: 'Buero', r: 'Backoffice'}];
const A = [
  {id: 'a1', nummer: 'S1', scheinstatus: 'freigegeben', monteur: 'w1', terminBestaetigt: H, terminZeit: '08:00', kundName: 'Kunde Eins', arbeitsort: 'Krems', scheinart: 'stoerung'},
  {id: 'a2', nummer: 'S2', scheinstatus: 'freigegeben', monteur: 'w1', terminVorschlag: '2026-11-20', dispoDatum: H, dispoZeit: '10:00', kundName: 'Kunde Zwei', projektnr: 'PA1'},
  {id: 'a3', nummer: 'S3', scheinstatus: 'freigegeben', monteur: 'w2', terminBestaetigt: '2026-11-26', dispoDatum: H, kundName: 'Kunde Drei'},
  {id: 'a4', nummer: 'S4', scheinstatus: 'aufgenommen', monteur: '', terminVorschlag: H, kundName: 'Kunde Vier'},
  {id: 'a5', nummer: 'S5', scheinstatus: 'storniert', monteur: 'w1', terminBestaetigt: H},
  {id: 'a6', nummer: 'S6', scheinstatus: 'freigegeben', monteur: 'w3', terminBestaetigt: '2026-11-20', kundName: 'Alt'},
  {id: 'a7', nummer: 'S7', scheinstatus: 'freigegeben', monteur: 'w9', terminBestaetigt: H, kundName: 'Fremd'}
];
const ABS = {'Cora_2026-11-25': {type: 'krank', status: 'genehmigt', hours: 8}};
const O = {};
function messen(b) {
  const klein = [], tipp = [];
  alle(b, function (n) { return n.props && n.props.style; }).forEach(function (n) { const fs = n.props.style.fontSize; if (typeof fs === 'number' && fs < 13) klein.push(n.tag + ':' + fs + ':' + text(n).slice(0, 30)); });
  alle(b, function (n) { return n.props && (typeof n.props.onClick === 'function') && n.tag !== 'a'; }).forEach(function (n) {
    const s = n.props.style || {}; if (n.props['data-as-lese']) return; if (n.props.role === 'dialog') return;
    if (!(s.minHeight >= 44)) tipp.push(n.tag + ':' + JSON.stringify(s.minHeight) + ':' + text(n).slice(0, 30)); });
  return {klein: klein, tipp: tipp};
}
let w = React.createElement(DispoTagKarten, {scheine: A, monteure: M, abs: ABS, tagVon: _dkTagDispo, heute: H});
let b = ruhe(w);
O.text = text(b);
O.jobs = alle(b, function (n) { return n.props && n.props['data-dk-job']; }).map(function (n) { return n.props['data-dk-job'] + ':' + n.props['data-stand']; });
O.flags = alle(b, function (n) { return n.props && n.props['data-flag']; }).map(function (n) { return n.props['data-flag']; });
O.abw = alle(b, function (n) { return n.props && n.props['data-dk-frei']; }).map(text);
O.mess = messen(b);
O.wochenTasten = alle(b, function (n) { return n.tag === 'button' && n.props['aria-pressed'] !== undefined; }).length;
// tippen -> Lese-Ansicht, ohne Schreibweg
const j = alle(b, function (n) { return n.props && n.props['data-dk-job'] === 'a3'; })[0]; j.props.onClick({});
b = ruhe(w);
O.blatt = alle(b, function (n) { return n.props && n.props.role === 'dialog'; }).map(text);
O.messBlatt = messen(b);
// Info
const ik = alle(b, function (n) { return n.tag === 'button' && n.props['aria-label'] === 'Erklärung und Legende'; })[0]; ik.props.onClick({});
b = ruhe(w); O.info = alle(b, function (n) { return n.props && n.props['data-dk-info']; }).length;
// Monat: Zahl je Tag = Tagesansicht
store.clear();
const mon = ruhe(React.createElement(KalMonatZahl, {scheine: A, jahr: 2026, monat: 10, tagVon: _dkTagKal, heute: H, onTag: function () {}}));
O.monat = {};
alle(mon, function (n) { return n.props && n.props['data-kal-tag']; }).forEach(function (n) { O.monat[n.props['data-kal-tag']] = n.props['data-anzahl']; });
O.messMonat = messen(mon);
O.tag = {};
Object.keys(O.monat).forEach(function (iso) { store.clear(); const t = ruhe(React.createElement(DispoTagKarten, {scheine: A, monteure: M, tagVon: _dkTagKal, heute: H, iso: iso, setIso: function () {}, mitNav: false}));
  O.tag[iso] = alle(t, function (n) { return n.props && n.props['data-dk-job']; }).length; });
store.clear();
const wo = ruhe(React.createElement(DispoWocheLesen, {scheine: A, monteure: M, abs: ABS, tagVon: _dkTagDispo, heute: H}));
O.woche = alle(wo, function (n) { return n.props && n.props['data-dk-job']; }).map(function (n) { return n.props['data-dk-job']; });
O.messWoche = messen(wo);
store.clear();
const kw = ruhe(React.createElement(KalWocheListe, {scheine: A, monteure: M, iso: H, tagVon: _dkTagKal, heute: H, onTag: function () {}}));
O.messKalWoche = messen(kw);
console.log(JSON.stringify(O));
"""


def pruefe_karten(node_exe, q):
    R = _node(node_exe, _umgebung(q) + KARTEN_JS)
    jobs = sorted(R["jobs"])
    assert jobs == ["a1:bestaetigt", "a2:geplant", "a3:abweichend", "a4:wunsch", "a7:bestaetigt"], jobs
    assert "Anna" in R["text"] and "Bert" in R["text"] and "Ohne Monteur" in R["text"]
    assert "Buero" not in R["text"], "Backoffice als Monteurkarte"
    assert set(R["flags"]) >= {"stoerung", "baustelle", "fix"}, R["flags"]
    assert any("Cora" in t and "Krankenstand" in t for t in R["abw"]), R["abw"]
    assert R["wochenTasten"] >= 5
    for k in ("mess", "messBlatt", "messMonat", "messWoche", "messKalWoche"):
        assert R[k]["klein"] == [], (k, R[k]["klein"][:5])
        assert R[k]["tipp"] == [], (k, R[k]["tipp"][:5])
    assert R["blatt"] and "S3" in R["blatt"][0] and "OFFA hat noch" in R["blatt"][0]
    assert R["info"] == 1
    assert R["monat"]["2026-11-25"] == 4, R["monat"]["2026-11-25"]
    for iso, n in R["monat"].items():
        assert R["tag"][iso] == n, (iso, n, R["tag"][iso])
    assert "a6" not in R["woche"] and set(R["woche"]) >= {"a1", "a2", "a3", "a4"}


def test_tageskarten_monat_woche(node_exe):
    pruefe_karten(node_exe, _neu())


def test_gegenprobe_karten_alt_rot(node_exe):
    with pytest.raises((AssertionError, ValueError)):
        pruefe_karten(node_exe, _alt())


# ═══ 4. Verdrahtung im Quelltext (ergaenzend zu den Laeufen oben) ══════════
def pruefe_verdrahtung(q):
    i = q.index("function DispoPanel(")
    body = _extract_fn(q, "DispoPanel").replace("\r\n", "\n")
    # Mobil-Zweig steht vor dem Raster und nach allen Hooks
    k = body.index('if(_dpAns!=="breit")')
    assert k < body.index("var wochen=_built.wochen")
    assert body.rfind("_react.use", 0, k) < k and body.find("_react.use", k) < 0, "Hook nach dem Mobil-Zweig"
    # kein touchAction none mehr an ziehbaren Flaechen
    assert 'touchAction:o.drag?"none"' not in body and 'touchAction:_wlDrag?"none"' not in body
    assert 'cursor:"ns-resize",touchAction:"none"' not in body
    # Termin bestaetigen nur fuer Buero/PL/Admin verdrahtet
    assert "onBestaetigen: canSync?terminBestaetigen:null" in q
    # Kalender schmal nutzt dieselben Komponenten
    assert "calView===\"monat\"&&_kalMob&&React.createElement(KalMonatZahl" in q
    assert "calView===\"tag\"&&_kalMob&&React.createElement(DispoTagKarten" in q
    # der Mobil-Block schreibt nie selbst (kein updAs/SQ/_sbPatch/Push im Block)
    blk = _block(q)
    for verboten in ("updAs(", "SQ.push", "_sbPatch(", "_juprowaSchedulePush", "_juprowaPush("):
        assert verboten not in blk, verboten
    # Lade-Abbild traegt die Planungsfelder
    assert "dispoDatum:a.dispoDatum||a.dispo_datum||\"\"" in q


def test_verdrahtung():
    pruefe_verdrahtung(_neu())


def test_gegenprobe_verdrahtung_alt_rot():
    with pytest.raises((AssertionError, ValueError)):
        pruefe_verdrahtung(_alt())


# ═══ 5. Gegenproben am NEUEN Stand: genau eine Stelle zurueckgebaut -> rot ═══
def _mutiert(alt, neu_text):
    q = _neu()
    assert q.count(alt) == 1, alt[:80]
    return q.replace(alt, neu_text)


def test_gegenprobe_ohne_zeigerpruefung_rot(node_exe):
    q = _mutiert("    if(!_dispoDragErlaubt(e,_dispoAnsicht()))return;/* Dispo mobil: nur Maus + breit */", "    /* x */")
    with pytest.raises(AssertionError):
        pruefe_ziehen(node_exe, q)


def test_gegenprobe_ziehen_schreibt_termin_rot(node_exe):
    q = _mutiert('dispoPlanen(scheinId,{datum:iso,zeit:startHHMM||"",dauer:_dispoMinToHHMM(dauerMin)},"verschoben");',
                 'updAs(scheinId,{terminBestaetigt:iso,terminZeit:startHHMM||"",dauer:_dispoMinToHHMM(dauerMin)});')
    with pytest.raises(AssertionError):
        pruefe_ziehen(node_exe, q)


def test_gegenprobe_kleine_schrift_rot(node_exe):
    q = _neu()
    blk = _block(q)
    alt = "h('span',{style:{fontSize:UI.fKlein,fontWeight:700}},_DK_WT["
    assert blk.count(alt) == 1
    q = q.replace(alt, "h('span',{style:{fontSize:UI.fMeta,fontWeight:700}},_DK_WT[")
    with pytest.raises(AssertionError):
        pruefe_karten(node_exe, q)


def test_gegenprobe_monatszahl_zaehlt_storno_rot(node_exe):
    q = _mutiert("scheine.forEach(function(a){if(!_dkZaehlt(a)||tagVon(a)!==x)return;n++;", "scheine.forEach(function(a){if(tagVon(a)!==x)return;n++;")
    with pytest.raises(AssertionError):
        pruefe_karten(node_exe, q)


def test_gegenprobe_bestaetigen_doppelt_rot(node_exe):
    q = _mutiert("var r=updAsFn(s.id,u);return r===false", "updAsFn(s.id,u);var r=updAsFn(s.id,u);return r===false")
    with pytest.raises(AssertionError):
        pruefe_rein(node_exe, q)
