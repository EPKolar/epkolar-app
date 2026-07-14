"""v3.9.650 KV-V4 — Zulagen (Taggeld/Montagezulage), pure Funktionen (Node-eval).

Taggeld je Tag: >11h -> 30,00; >6h -> 11,94; sonst 0. Montagezulage = Baustellen-Std
* 1,155. NUR Auswertung/Anspruchsfuehrung — Lohnverrechner massgeblich, keine Verbuchung.
"""
import re
import json
from conftest import run_node_snippet

_R = "{taggeldAb6h:11.94,taggeldAb11h:30.00,montagezulageStd:1.155}"


def _block(index_html):
    m = re.search(r"//@KV-ZULAGEN-START(.*?)//@KV-ZULAGEN-END", index_html, re.S)
    assert m, "KV-ZULAGEN-Block nicht gefunden"
    return m.group(1)


def _eval(node_exe, index_html, expr):
    snippet = _block(index_html) + "\nprocess.stdout.write(JSON.stringify((" + expr + ")))"
    return json.loads(run_node_snippet(node_exe, snippet))


def test_taggeld_stufen(node_exe, index_html):
    expr = ("_kvTaggeldTag(12," + _R + ")===30"
            " && _kvTaggeldTag(11.5," + _R + ")===30"
            " && _kvTaggeldTag(11," + _R + ")===11.94"      # >6 aber nicht >11
            " && _kvTaggeldTag(8," + _R + ")===11.94"
            " && _kvTaggeldTag(6," + _R + ")===0"           # nicht >6
            " && _kvTaggeldTag(5," + _R + ")===0")
    assert _eval(node_exe, index_html, expr) is True


def test_montagezulage(node_exe, index_html):
    assert abs(_eval(node_exe, index_html, "_kvMontagezulage(10," + _R + ")") - 11.55) < 1e-9
    assert _eval(node_exe, index_html, "_kvMontagezulage(0," + _R + ")") == 0


def test_zulagen_monat_aggregat(node_exe, index_html):
    # Tage [8,12,5,6.5]: Taggeld 11,94+30+0+11,94 = 53,88 ; Baustelle 40h -> 46,20 ; gesamt 100,08
    r = _eval(node_exe, index_html, "_kvZulagenMonat([8,12,5,6.5],40," + _R + ")")
    assert r["tage6"] == 2 and r["tage11"] == 1
    assert abs(r["taggeldSum"] - 53.88) < 1e-9
    assert abs(r["montageSum"] - 46.2) < 1e-9
    assert abs(r["gesamt"] - 100.08) < 1e-9


def test_zulagen_monat_leer(node_exe, index_html):
    r = _eval(node_exe, index_html, "_kvZulagenMonat([],0," + _R + ")")
    assert r["gesamt"] == 0 and r["tage6"] == 0 and r["tage11"] == 0


# ── UI-Wiring ──
def test_report_component(index_html):
    assert "function KVZulagenReport(props)" in index_html


def test_report_in_bueroportal(index_html):
    # v3.9.685: curUser kam dazu (created_by bei der Tages-Vergabe). Assertion nicht mehr auf die
    # komplette Props-Liste im Wortlaut — sie bricht sonst bei jedem neuen Prop, ohne dass sich am
    # geprueften Verhalten (Report haengt im Buero-Portal) etwas aendert.
    assert "React.createElement(KVZulagenReport, { entries: entries, monteure: monteure, ww: ww" in index_html


def test_csv_export(index_html):
    assert "'KV-Zulagen_'+ym+'.csv'" in index_html


def test_report_lohnverrechner_hinweis(index_html):
    assert "Lohnverrechner maßgeblich" in index_html
    assert "KEINE automatische Verbuchung" in index_html
