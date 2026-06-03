"""Sprint 50-72 helper-coverage tests.

Covers helpers added/refined in recent sprints that previously lacked tests:
  _fmtTimeAgo  (Sprint-62.2 / v3.9.83)
  _fmtDateGroup (Sprint-62.2 / v3.9.83)
  _pickerlStatus (B-014 / v3.9.18)
  _Skeleton    (Sprint-52 / v3.9.73)
  _safeJsonParse (long-standing)
  _jp / _jo    (reverse mapper helpers)

Static-only assertions. Tier-1 regression-guards.
"""
import re


def test_fmttimeago_defined(index_html):
    assert re.search(r"\bfunction\s+_fmtTimeAgo\s*\(\s*ts\s*\)", index_html), \
        "_fmtTimeAgo(ts) helper missing"


def test_fmttimeago_exposed_on_window(index_html):
    assert "window._fmtTimeAgo=_fmtTimeAgo" in index_html, \
        "_fmtTimeAgo must be exposed on window"


def test_fmttimeago_branches(index_html):
    m = re.search(r"function\s+_fmtTimeAgo\s*\([^)]*\)\s*\{(.*?)\n\}", index_html, re.S)
    assert m, "_fmtTimeAgo body not extractable"
    body = m.group(1)
    assert "gerade eben" in body, "missing 'gerade eben' branch"
    assert "Gestern" in body, "missing 'Gestern' branch"


def test_fmttimeago_uses_de_at_locale(index_html):
    m = re.search(r"function\s+_fmtTimeAgo\s*\([^)]*\)\s*\{(.*?)\n\}", index_html, re.S)
    assert m and '"de-AT"' in m.group(1), \
        "_fmtTimeAgo must use de-AT locale"


def test_fmtdategroup_defined(index_html):
    assert re.search(r"\bfunction\s+_fmtDateGroup\s*\(\s*ts\s*\)", index_html), \
        "_fmtDateGroup(ts) helper missing"


def test_fmtdategroup_branches(index_html):
    m = re.search(r"function\s+_fmtDateGroup\s*\([^)]*\)\s*\{(.*?)\n\}", index_html, re.S)
    assert m, "_fmtDateGroup body not extractable"
    body = m.group(1)
    for label in ("Heute", "Gestern", "Diese Woche", "Diesen Monat"):
        assert label in body, f"_fmtDateGroup missing branch label: {label}"


def test_pickerlstatus_defined_on_window(index_html):
    assert "window._pickerlStatus=" in index_html, \
        "window._pickerlStatus arrow assignment missing"


def test_pickerlstatus_returns_three_states_plus_null(index_html):
    line = next(
        (ln for ln in index_html.splitlines() if "window._pickerlStatus=" in ln),
        "",
    )
    assert line, "_pickerlStatus line not found"
    for state in ("'overdue'", "'warn'", "'ok'"):
        assert state in line, f"_pickerlStatus missing state {state}"
    assert "return null" in line, "_pickerlStatus must return null for invalid input"


def test_pickerlstatus_default_warndays_is_30(index_html):
    line = next(
        (ln for ln in index_html.splitlines() if "window._pickerlStatus=" in ln),
        "",
    )
    assert "30" in line, "_pickerlStatus default warnDays=30 must be present"


def test_skeleton_helper_defined(index_html):
    assert re.search(r"\bfunction\s+_Skeleton\s*\(\s*rows\s*\)", index_html), \
        "_Skeleton(rows) helper missing"


def test_skeleton_uses_aria_busy(index_html):
    line = next(
        (ln for ln in index_html.splitlines() if "function _Skeleton(rows)" in ln),
        "",
    )
    assert line and "aria-busy" in line, "_Skeleton must set aria-busy for a11y"


def test_skeleton_pulse_animation(index_html):
    line = next(
        (ln for ln in index_html.splitlines() if "function _Skeleton(rows)" in ln),
        "",
    )
    assert line and "pulse" in line, "_Skeleton must reference pulse animation keyframe"


def test_safejsonparse_defined(index_html):
    assert re.search(r"\bfunction\s+_safeJsonParse\s*\(\s*s\s*,\s*fallback\s*\)", index_html), \
        "_safeJsonParse(s,fallback) helper missing"


def test_safejsonparse_handles_null_and_throws(index_html):
    m = re.search(r"function\s+_safeJsonParse\s*\([^)]*\)\s*\{(.*?)\n\}", index_html, re.S)
    assert m, "_safeJsonParse body not extractable"
    body = m.group(1)
    assert "fallback" in body, "must return fallback"
    assert "JSON.parse" in body, "must call JSON.parse"
    assert "catch" in body, "must catch parse errors"


def test_jp_jo_defined(index_html):
    assert re.search(r"const\s+_jp\s*=\s*s\s*=>", index_html), "_jp arrow missing"
    assert re.search(r"const\s+_jo\s*=\s*s\s*=>", index_html), "_jo arrow missing"


def test_jp_returns_array_jo_returns_object(index_html):
    jp_line = next(
        (ln for ln in index_html.splitlines() if re.match(r"\s*const\s+_jp\s*=", ln)),
        "",
    )
    jo_line = next(
        (ln for ln in index_html.splitlines() if re.match(r"\s*const\s+_jo\s*=", ln)),
        "",
    )
    assert jp_line and "return[]" in jp_line.replace(" ", ""), "_jp must default to []"
    assert jo_line and "return{}" in jo_line.replace(" ", ""), "_jo must default to {}"
