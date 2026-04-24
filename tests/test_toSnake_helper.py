"""Behavior tests for _toSnake (camelCase -> snake_case converter).

Tag 4 / Theme 1: Sanitize-Funktionen. Run via Node subprocess.
"""
import json
import re
import pytest
from conftest import _extract_fn, run_node_snippet


@pytest.fixture(scope="session")
def fn_toSnake(index_html):
    fn = _extract_fn(index_html, "_toSnake")
    assert fn, "_toSnake function not found"
    return fn


def _call(node_exe, fn, arg):
    snippet = f"{fn};process.stdout.write(JSON.stringify(_toSnake({json.dumps(arg)})))"
    return json.loads(run_node_snippet(node_exe, snippet))


def test_simple_camel(node_exe, fn_toSnake):
    assert _call(node_exe, fn_toSnake, "kundName") == "kund_name"


def test_already_snake(node_exe, fn_toSnake):
    assert _call(node_exe, fn_toSnake, "already_snake") == "already_snake"


def test_no_uppercase(node_exe, fn_toSnake):
    assert _call(node_exe, fn_toSnake, "lowercase") == "lowercase"


def test_multiple_camels(node_exe, fn_toSnake):
    assert _call(node_exe, fn_toSnake, "myVeryLongVariableName") == "my_very_long_variable_name"


def test_consecutive_uppercase(node_exe, fn_toSnake):
    # _toSnake naive: each uppercase becomes _<lower>, so "aBC" -> "a_b_c"
    assert _call(node_exe, fn_toSnake, "aBC") == "a_b_c"


def test_empty_string(node_exe, fn_toSnake):
    assert _call(node_exe, fn_toSnake, "") == ""


def test_starts_with_uppercase(node_exe, fn_toSnake):
    # PascalCase: _toSnake will prepend an underscore at position 0
    assert _call(node_exe, fn_toSnake, "MyClass") == "_my_class"


def test_real_usage_pattern_kundeFreigabe(node_exe, fn_toSnake):
    assert _call(node_exe, fn_toSnake, "kundeFreigabe") == "kunde_freigabe"


def test_real_usage_pattern_lastSync(node_exe, fn_toSnake):
    assert _call(node_exe, fn_toSnake, "lastSync") == "last_sync"


def test_with_digit_in_middle(node_exe, fn_toSnake):
    # Digits stay, only uppercase letters get _ prefix
    assert _call(node_exe, fn_toSnake, "field1Name") == "field1_name"
