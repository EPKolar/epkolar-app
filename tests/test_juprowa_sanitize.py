"""Behavior tests for _juprowaSanitize - Latin-1 clean-up for Juprowa-Push.

All non-ASCII test inputs use explicit uXXXX escape sequences. Python
source itself is ASCII-only to avoid Windows encoding pitfalls.
"""
import json
import pytest
from conftest import run_node_snippet


def _call(node_exe, fn, arg):
    snippet = f"{fn};process.stdout.write(JSON.stringify(_juprowaSanitize({json.dumps(arg)})))"
    raw = run_node_snippet(node_exe, snippet)
    return json.loads(raw)


def test_sanitize_empty_string(node_exe, fn_juprowa_sanitize):
    assert _call(node_exe, fn_juprowa_sanitize, "") == ""


def test_sanitize_null_returns_null(node_exe, fn_juprowa_sanitize):
    snippet = f"{fn_juprowa_sanitize};process.stdout.write(JSON.stringify(_juprowaSanitize(null)))"
    assert run_node_snippet(node_exe, snippet) == "null"


def test_sanitize_em_dash(node_exe, fn_juprowa_sanitize):
    # U+2014 em dash -> --
    assert _call(node_exe, fn_juprowa_sanitize, "foo \u2014 bar") == "foo -- bar"


def test_sanitize_en_dash(node_exe, fn_juprowa_sanitize):
    # U+2013 en dash -> -
    assert _call(node_exe, fn_juprowa_sanitize, "foo \u2013 bar") == "foo - bar"


def test_sanitize_smart_single_quotes(node_exe, fn_juprowa_sanitize):
    # U+2018 / U+2019 -> \x27
    assert _call(node_exe, fn_juprowa_sanitize, "\u2018x\u2019") == "\x27x\x27"


def test_sanitize_smart_double_quotes(node_exe, fn_juprowa_sanitize):
    # U+201C / U+201D -> \x22
    assert _call(node_exe, fn_juprowa_sanitize, "\u201Cx\u201D") == '"x"'


def test_sanitize_euro_sign(node_exe, fn_juprowa_sanitize):
    # U+20AC -> EUR
    assert _call(node_exe, fn_juprowa_sanitize, "100 \u20AC") == "100 EUR"


def test_sanitize_ellipsis(node_exe, fn_juprowa_sanitize):
    # U+2026 -> ...
    assert _call(node_exe, fn_juprowa_sanitize, "warten\u2026") == "warten..."


def test_sanitize_nbsp(node_exe, fn_juprowa_sanitize):
    # U+00A0 -> regular space
    assert _call(node_exe, fn_juprowa_sanitize, "a\u00A0b") == "a b"


def test_sanitize_umlauts_preserved(node_exe, fn_juprowa_sanitize):
    # U+00E4/F6/FC/DF - standard Latin-1 umlauts - not replaced
    arg = "St\u00F6rung Installateur \u00E4 \u00F6 \u00FC \u00DF"
    assert _call(node_exe, fn_juprowa_sanitize, arg) == arg


def test_sanitize_combined(node_exe, fn_juprowa_sanitize):
    # Mix: em-dash + ellipsis + euro
    inp = "Fehler\u2014Strom\u2026 100 \u20AC"
    assert _call(node_exe, fn_juprowa_sanitize, inp) == "Fehler--Strom... 100 EUR"
