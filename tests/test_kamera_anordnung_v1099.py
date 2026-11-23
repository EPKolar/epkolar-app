# -*- coding: utf-8 -*-
"""v3.9.1099 (GF 23.11.2026): Kameras - Standardansicht "Alle" und Anordnung durch den Admin.

Reihenfolge = JSON-Liste der Kamera-IDs in system_config.kameras_reihenfolge (keine Tabellen-Aenderung;
lesen alle, schreiben nur Admin per RLS). Reine Funktionen in Node ausgefuehrt.
"""
import io
import json
import os
import subprocess

HIER = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HIER, "..", "index.html")


def _src():
    return io.open(HTML, encoding="utf-8", newline="").read()


def _fn(src, name):
    i = src.index("function " + name + "(")
    j = src.index("\nfunction ", i + 10)
    return src[i:j]


def _node(ausdruck):
    s = _src()
    code = "\n".join(_fn(s, n) for n in ("_kamOrdnungLesen", "_kamSortiere", "_kamVerschiebe"))
    r = subprocess.run(["node", "-e", code + "\nconsole.log(JSON.stringify(" + ausdruck + "));"],
                       capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


ROWS = '[{"id":"a","name":"A"},{"id":"b","name":"B"},{"id":"c","name":"C"},{"id":"d","name":"D"}]'


def test_ordnung_lesen_robust():
    assert _node('_kamOrdnungLesen(\'["c","a","c",5,""]\')') == ["c", "a"]
    assert _node("_kamOrdnungLesen('kaputt')") == []
    assert _node("_kamOrdnungLesen(null)") == []
    assert _node("_kamOrdnungLesen('{\"a\":1}')") == []


def test_sortiere_nach_ordnung_rest_nach_name():
    ids = _node('_kamSortiere(' + ROWS + ',["c","x","a"]).map(function(r){return r.id;})')
    assert ids == ["c", "a", "b", "d"]          # unbekannte ID x ignoriert, neue b/d hinten in Namensfolge
    assert _node('_kamSortiere(' + ROWS + ',[]).map(function(r){return r.id;})') == ["a", "b", "c", "d"]


def test_verschiebe_grenzen():
    assert _node('_kamVerschiebe(["a","b","c"],1,-1)') == ["b", "a", "c"]
    assert _node('_kamVerschiebe(["a","b","c"],1,1)') == ["a", "c", "b"]
    assert _node('_kamVerschiebe(["a","b","c"],0,-1)') == ["a", "b", "c"]
    assert _node('_kamVerschiebe(["a","b","c"],2,1)') == ["a", "b", "c"]


def test_standard_ist_alle():
    kv = _fn(_src(), "KameraView")
    assert "var _a=_react.useState.call(void 0,'alle');var ansicht=_a[0],setAnsicht=_a[1];" in kv
    assert "useState.call(void 0,'2x2')" not in kv


def test_laden_wendet_ordnung_an_und_schreiben_nur_admin():
    s = _src()
    lade = _fn(s, "_kamLadeKameras")
    assert "var ord=await _kamLadeReihenfolge();" in lade
    assert "rows:_kamSortiere(Array.isArray(rows)?rows:[],ord)" in lade
    schreib = _fn(s, "_kamReihenfolgeSchreiben")
    assert "key:'kameras_reihenfolge'" in schreib and "JSON.stringify(ids||[])" in schreib
    kv = _fn(s, "KameraView")
    assert "isAdmin&&!demo&&aktive.length>1?h('button'" in kv
    assert "else if(ordnen&&isAdmin){" in kv
    # Lesefehler der Ordnung -> leere Liste (Namensfolge), nie ein Abbruch des Kamera-Ladens
    assert "catch(e){return [];}" in _fn(s, "_kamLadeReihenfolge")
