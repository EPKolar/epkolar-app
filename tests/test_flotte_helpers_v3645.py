"""v3.9.645 Flotte-Tab — pure Gruppier-/Relativzeit-Helper (Node-eval).

Extrahiert den Sentinel-Block //@FLOTTE-HELPERS-START..END aus index.html und
evaluiert die reinen Funktionen in Node. TIME_DAY wird im Snippet definiert
(die Helfer referenzieren die globale Konstante).
"""
import re
import json
from conftest import run_node_snippet


def _helpers(index_html):
    m = re.search(r"//@FLOTTE-HELPERS-START(.*?)//@FLOTTE-HELPERS-END", index_html, re.S)
    assert m, "FLOTTE-HELPERS-Block nicht gefunden"
    # TIME_* sind im App-Scope global; im isolierten Snippet selbst definieren.
    return ("const TIME_SECOND=1000,TIME_MINUTE=60*TIME_SECOND,TIME_HOUR=60*TIME_MINUTE,TIME_DAY=24*TIME_HOUR;\n"
            + m.group(1))


def _eval(node_exe, index_html, expr):
    snippet = _helpers(index_html) + "\nprocess.stdout.write(JSON.stringify((" + expr + ")))"
    return json.loads(run_node_snippet(node_exe, snippet))


_POS = ("[{fahrzeug_id:'a',ts:'2026-01-15T10:00:00Z',lat:1,lon:1},"
        "{fahrzeug_id:'a',ts:'2026-01-15T12:00:00Z',lat:2,lon:2},"
        "{fahrzeug_id:'b',ts:'2026-01-15T09:00:00Z',lat:3,lon:3}]")


# ── Gruppierung: neueste Position je Fahrzeug ──
def test_latest_per_vehicle_count(node_exe, index_html):
    assert _eval(node_exe, index_html, "_flotteLatestPerVehicle(" + _POS + ").length") == 2


def test_latest_per_vehicle_picks_newest(node_exe, index_html):
    # 'a' hat 10:00 und 12:00 -> die 12:00-Position (lat:2) gewinnt
    res = _eval(node_exe, index_html, "_flotteLatestPerVehicle(" + _POS + ").map(function(p){return [p.fahrzeug_id,p.lat];}).sort()")
    assert res == [["a", 2], ["b", 3]]


def test_latest_per_vehicle_empty(node_exe, index_html):
    assert _eval(node_exe, index_html, "_flotteLatestPerVehicle([]).length") == 0


def test_latest_per_vehicle_skips_bad(node_exe, index_html):
    bad = "[{fahrzeug_id:'',ts:'2026-01-15T10:00:00Z'},{ts:'2026-01-15T10:00:00Z'},{fahrzeug_id:'x',ts:'nonsense'}]"
    assert _eval(node_exe, index_html, "_flotteLatestPerVehicle(" + bad + ").length") == 0


# ── Relativzeit ──
def test_reltime_gerade_eben(node_exe, index_html):
    assert _eval(node_exe, index_html, "_flotteRelTime(1000000000000-30000, 1000000000000)") == "gerade eben"


def test_reltime_minuten(node_exe, index_html):
    assert _eval(node_exe, index_html, "_flotteRelTime(1000000000000-300000, 1000000000000)") == "vor 5 min"


def test_reltime_stunden(node_exe, index_html):
    assert _eval(node_exe, index_html, "_flotteRelTime(1000000000000-7200000, 1000000000000)") == "vor 2 Std"


def test_reltime_ein_tag(node_exe, index_html):
    assert _eval(node_exe, index_html, "_flotteRelTime(1000000000000-86400000, 1000000000000)") == "vor 1 Tag"


def test_reltime_mehrere_tage(node_exe, index_html):
    assert _eval(node_exe, index_html, "_flotteRelTime(1000000000000-172800000, 1000000000000)") == "vor 2 Tagen"


# ── Inaktiv-Schwelle (>24h) ──
def test_inactive_true_ueber_24h(node_exe, index_html):
    assert _eval(node_exe, index_html, "_flotteInactive(1000000000000-172800000, 1000000000000)") is True


def test_inactive_false_unter_24h(node_exe, index_html):
    assert _eval(node_exe, index_html, "_flotteInactive(1000000000000-3600000, 1000000000000)") is False
