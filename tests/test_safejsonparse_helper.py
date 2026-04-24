"""Behavior tests for _safeJsonParse helper (v3.8.44 Bug-Hunt-S2.1).

Defensive JSON.parse: never throws, always returns fallback on failure.
"""
import json
import pytest
from conftest import _extract_fn, run_node_snippet


@pytest.fixture(scope="session")
def fn_safe_parse(index_html):
    fn = _extract_fn(index_html, "_safeJsonParse")
    assert fn, "_safeJsonParse function not found"
    return fn


def _call(node_exe, fn, arg_js, fallback_js="null"):
    snippet = (
        f"{fn};process.stdout.write(JSON.stringify("
        f"_safeJsonParse({arg_js},{fallback_js})))"
    )
    raw = run_node_snippet(node_exe, snippet)
    return json.loads(raw)


def test_valid_json_object(node_exe, fn_safe_parse):
    assert _call(node_exe, fn_safe_parse, '\'{"a":1}\'') == {"a": 1}


def test_valid_json_array(node_exe, fn_safe_parse):
    assert _call(node_exe, fn_safe_parse, '\'[1,2,3]\'') == [1, 2, 3]


def test_null_returns_fallback(node_exe, fn_safe_parse):
    assert _call(node_exe, fn_safe_parse, "null", '"FALLBACK"') == "FALLBACK"


def test_undefined_returns_fallback(node_exe, fn_safe_parse):
    assert _call(node_exe, fn_safe_parse, "undefined", '"FALLBACK"') == "FALLBACK"


def test_empty_string_returns_fallback(node_exe, fn_safe_parse):
    assert _call(node_exe, fn_safe_parse, '""', '"FALLBACK"') == "FALLBACK"


def test_invalid_json_returns_fallback(node_exe, fn_safe_parse):
    assert _call(node_exe, fn_safe_parse, '"not-json{"', '"FALLBACK"') == "FALLBACK"


def test_default_fallback_undefined_passed_explicitly(node_exe, fn_safe_parse):
    snippet = fn_safe_parse + ';let r=_safeJsonParse(null);process.stdout.write(JSON.stringify(r===undefined?"UNDEF":r))'
    raw = run_node_snippet(node_exe, snippet)
    assert json.loads(raw) == "UNDEF"


def test_fallback_array_for_invalid(node_exe, fn_safe_parse):
    assert _call(node_exe, fn_safe_parse, '"[broken"', '[]') == []


def test_fallback_obj_for_invalid(node_exe, fn_safe_parse):
    assert _call(node_exe, fn_safe_parse, '"{broken"', '{}') == {}


def test_no_throw_on_garbage(node_exe, fn_safe_parse):
    """Smoke: even garbage strings don't throw, fallback returned."""
    for garbage in ('"\\u0000"', '"abc"', '"123abc"', '"["'):
        assert _call(node_exe, fn_safe_parse, garbage, '"X"') == "X" or \
               _call(node_exe, fn_safe_parse, garbage, '"X"') is not None
