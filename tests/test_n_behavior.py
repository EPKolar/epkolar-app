"""Behavior tests for the _n() NaN-safe numeric formatter.

Extracts _n from index.html and runs via Node subprocess.
"""
import json
import pytest
from conftest import run_node_snippet


def _eval(node_exe, fn_n, call):
    """Eval `<fn_n>; process.stdout.write(JSON.stringify(<call>))`."""
    snippet = f"{fn_n};process.stdout.write(JSON.stringify({call}))"
    raw = run_node_snippet(node_exe, snippet)
    return json.loads(raw)


def test_n_null_returns_zero_string(node_exe, fn_n):
    assert _eval(node_exe, fn_n, "_n(null, 2)") == "0.00"


def test_n_undefined_returns_zero_string(node_exe, fn_n):
    assert _eval(node_exe, fn_n, "_n(undefined, 1)") == "0.0"


def test_n_nan_returns_zero_string(node_exe, fn_n):
    assert _eval(node_exe, fn_n, "_n(NaN, 3)") == "0.000"


def test_n_zero_with_decimals(node_exe, fn_n):
    assert _eval(node_exe, fn_n, "_n(0, 2)") == "0.00"


def test_n_negative_number(node_exe, fn_n):
    assert _eval(node_exe, fn_n, "_n(-5.27, 1)") == "-5.3"


def test_n_string_dot_number(node_exe, fn_n):
    assert _eval(node_exe, fn_n, '_n("1.5", 1)') == "1.5"


def test_n_german_decimal_limitation(node_exe, fn_n):
    # Documents known limitation: `_n("1,5", 1)` returns "1.0" because
    # parseFloat stops at "," — comma-decimal is NOT parsed as German.
    # This is existing behavior; callers must normalize input upstream.
    assert _eval(node_exe, fn_n, '_n("1,5", 1)') == "1.0"


def test_n_infinity_returns_zero(node_exe, fn_n):
    assert _eval(node_exe, fn_n, "_n(Infinity, 2)") == "0.00"


def test_n_without_decimals_returns_number(node_exe, fn_n):
    # When d is undefined, function returns numeric (not string)
    # so JSON.stringify yields the number form.
    assert _eval(node_exe, fn_n, "_n(3.14)") == 3.14


def test_n_without_decimals_nan_returns_zero(node_exe, fn_n):
    assert _eval(node_exe, fn_n, "_n(NaN)") == 0
