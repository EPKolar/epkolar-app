# -*- coding: utf-8 -*-
"""Buero-Portal > Verrechnung: die echte VerrechnungView in Node gezeichnet (Renderer aus test_kameras_phase1_v1055).

Szenen: Tabelle fehlt (Hinweis, kein Erfassen) - Buero erfasst "verrechnet bis" (schreibt NUR verrechnung) -
Monteur-Rolle ohne Erfassen - Umschalter Nach Monteur - Aufklappen zeigt KW + Monteur.
"""
import io
import json
import os
import shutil

import pytest

from test_kameras_phase1_v1055 import RENDER_PRELUDE, _render_lauf

HIER = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HIER, "..", "index.html")
FN = ("_vrNorm", "_vrBezug", "_vrSatzWirksam", "_vrIstVerrechnet", "_vrKW", "_vrR", "_vrAuswerten", "_vrNachMonteur",
      "_vrKennzahlen", "_vrH", "_vrDE", "_vrZeitraum", "_vrStatusText", "_vrLadeSaetze", "_vrSatzSchreiben", "VerrechnungView")


def _src():
    return io.open(HTML, encoding="utf-8", newline="").read()


def _fn(s, n):
    i = s.index("function " + n + "(") if ("function " + n + "(") in s else s.index("async function " + n + "(")
    if s[i - 6:i] == "async ":
        i -= 6
    j = s.index("\nfunction ", i + 10)
    k = s.find("\nasync function ", i + 10)
    if 0 <= k < j:
        j = k
    v = s.find("\nvar VR_TYP=", i + 10)
    if 0 <= v < j:
        j = v
    return s[i:j]


def _block():
    s = _src()
    i = s.index("var VR_TYP=")
    vr_typ = s[i:s.index("\n", i)]
    # bpS ist in App UND Attrappe ein Objekt - KEINE Ersetzung (die fruehere Ersetzung verdeckte "bpS is not a function", 23.11.)
    return "\n".join(_fn(s, n) for n in FN) + "\n" + vr_typ + "\n"


EXTRA = r"""
_react.useMemo = {call: function (_, f) { return f(); }};
function _layoutStufe(w) { return w < 600 ? 'schmal' : (w < 1100 ? 'mittel' : 'breit'); }
function _lesbar(c) { return c; }
const mono = 'monospace';
function CC() { return {}; } function II() { return {}; }
function xBtn() { return {minHeight: 44}; }
function Kpi(p) { return React.createElement('div', {kpi: p.label}, p.label + ': ' + p.value); }
function _nWort(n, e, m) { return n + ' ' + (n === 1 ? e : m); }
function _ezHeuteISO() { return '2026-11-23'; }
function genXls() {} function _pdfCIKopf() {} function _pdfCIFuss() {} function _pdfStr(x) { return x; }
"""

SZENEN = r"""
const P = [{id: 'p1', nr: 'PA9', name: 'Halle'}];
const M = [{id: 'm1', n: 'Anton'}, {id: 'm2', n: 'Berta'}];
const E = [{datum: '2026-10-12', project_id: 'p1', stunden: 8, worker_id: 'm1'}, {datum: '2026-11-09', project_id: 'p1', stunden: 6, worker_id: 'm2'}];
function wurzel(rolle) { store.clear(); return React.createElement(VerrechnungView, {curUser: {role: rolle, name: 'Lucia'}, entries: E, loaded: true, projects: P, arbeitsscheine: [], monteure: M, ww: 1440}); }
function eingaben() { return alle(baum, function (n) { return n.tag === 'input'; }); }
let w;
// 1) Tabelle fehlt
SZENE = {db: {verrechnung: new Error('HTTP404 {"code":"PGRST205"}')}};
w = wurzel('admin'); await ruhe(w);
OUT.fehlt = {text: text(baum), erfassen: knopfHat(baum, 'Erfassen')};
// 2) Buero erfasst verrechnet bis 31.10.2026
SZENE = {db: {verrechnung: []}}; ZAEHL.upsert = []; ZAEHL.get = [];
w = wurzel('buero'); await ruhe(w);
OUT.vor = text(baum);
await klick(w, 'Erfassen');
eingaben().filter(function (n) { return n.props.type === 'date'; })[0].props.onChange({target: {value: '2026-10-31'}});
await ruhe(w);
await klick(w, 'Speichern');
OUT.upsert = ZAEHL.upsert; OUT.gets = ZAEHL.get.filter(function (g) { return g.indexOf('verrechnung') === 0; }).length;
// 3) Monteur / Projektleitung (Portal per Einzelrecht): nur Hinweis, kein Abruf, kein Erfassen
SZENE = {db: {verrechnung: []}}; ZAEHL.get = [];
w = wurzel('monteur'); await ruhe(w);
OUT.monteur = knopfHat(baum, 'Erfassen'); OUT.monteurText = text(baum); OUT.monteurGets = ZAEHL.get.length;
w = wurzel('projektleiter'); await ruhe(w); OUT.plText = text(baum);
// 4) Aufklappen + Nach Monteur
SZENE = {db: {verrechnung: [{bezug_typ: 'projekt', bezug_ref: 'p1', verrechnet_bis: '2026-10-31', voll: false}]}};
w = wurzel('admin'); await ruhe(w);
OUT.stand = text(baum);
alle(baum, function (n) { return n.tag === 'button' && n.props['aria-label'] === 'Monteur-Aufteilung PA9 · Halle'; })[0].props.onClick({});
await ruhe(w); OUT.auf = text(baum);
await klick(w, 'Nach Monteur'); OUT.monteure = text(baum);
"""


@pytest.fixture(scope="module")
def R():
    node = shutil.which("node")
    assert node
    return _render_lauf(node, EXTRA + _block(), SZENEN)


def test_tabelle_fehlt_hinweis_ohne_erfassen(R):
    assert "noch nicht angelegt" in R["fehlt"]["text"] and R["fehlt"]["erfassen"] is False
    assert "Offen: 14,00 h" in R["fehlt"]["text"]


def test_buero_erfasst_nur_in_verrechnung(R):
    assert "Nach Auftrag" in R["vor"] and "Offen: 14,00 h" in R["vor"]
    assert len(R["upsert"]) == 1
    u = R["upsert"][0]
    assert u["tab"] == "verrechnung"
    assert u["row"]["bezug_typ"] == "projekt" and u["row"]["bezug_ref"] == "p1"
    assert u["row"]["verrechnet_bis"] == "2026-10-31" and u["row"]["voll"] is False and u["row"]["verrechnet_von"] == "Lucia"
    assert R["gets"] == 2, "nach dem Speichern neu gelesen"


def test_monteur_ohne_erfassen(R):
    assert R["monteur"] is False
    assert "nur Büro und Admin" in R["monteurText"] and "Offen" not in R["monteurText"] and R["monteurGets"] == 0
    assert "nur Büro und Admin" in R["plText"]


def test_stand_aufklappen_und_monteursicht(R):
    assert "verrechnet bis 31.10.2026" in R["stand"] and "Offen: 6,00 h" in R["stand"] and "Verrechnet: 8,00 h" in R["stand"]
    assert "KW 42/2026" in R["auf"] and "KW 46/2026" in R["auf"] and "Anton" in R["auf"] and "Berta" in R["auf"]
    assert "Anton" in R["monteure"] and "8,00 h verr." in R["monteure"] and "6,00 h offen" in R["monteure"]
