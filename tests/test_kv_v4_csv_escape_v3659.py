"""v3.9.659 KV-V4 CSV-Feld-Escaping (Bug-Hunt #3).

Der Zulagen-CSV-Export quotet jetzt Felder mit ; " oder Zeilenumbruch (interne "
verdoppelt) — sonst verschoebe ein ";" im Monteur-Namen die Spalten. Extrahiert die
echte _csvEsc-Funktion aus index.html und testet sie in Node.
"""
import re
import json
from conftest import run_node_snippet


def _csvesc_fn(index_html):
    m = re.search(r"var _csvEsc=function\(v\)\{.*?\};", index_html)
    assert m, "_csvEsc-Funktion nicht gefunden"
    return m.group(0)


def _eval(node_exe, index_html, expr):
    snippet = _csvesc_fn(index_html) + "\nprocess.stdout.write(JSON.stringify((" + expr + ")))"
    return json.loads(run_node_snippet(node_exe, snippet))


def test_kein_special_unveraendert(node_exe, index_html):
    assert _eval(node_exe, index_html, "_csvEsc('Mueller Hans')") == "Mueller Hans"


def test_semikolon_gequotet(node_exe, index_html):
    assert _eval(node_exe, index_html, "_csvEsc('Meier; Co')") == '"Meier; Co"'


def test_quote_verdoppelt(node_exe, index_html):
    assert _eval(node_exe, index_html, "_csvEsc('A\\\"B')") == '"A""B"'


def test_newline_gequotet(node_exe, index_html):
    assert _eval(node_exe, index_html, "_csvEsc('a\\nb')") == '"a\nb"'


def test_null_leer(node_exe, index_html):
    assert _eval(node_exe, index_html, "_csvEsc(null)") == ""


def test_wiring_map_angewandt(index_html):
    # _csvEsc wird auf Kopf + Zeilen angewandt
    assert "head.map(_csvEsc).join(';')" in index_html
    assert "].map(_csvEsc).join(';')" in index_html
