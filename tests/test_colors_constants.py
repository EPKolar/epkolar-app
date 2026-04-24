"""Colors-Konstante Refactor - Tag 3 (Mi 30.04).

Verifiziert COLORS-Namespace + ersten 50 Migrationen aus Hex-Hardcodes.
"""
import re

COLORS_RE = re.compile(r'const COLORS=\{([^}]+)\}')


def _colors_body(index_html):
    m = COLORS_RE.search(index_html)
    assert m, "const COLORS not found"
    return m.group(1)


def test_colors_const_defined(index_html):
    assert "const COLORS=" in index_html


def test_colors_has_six_keys(index_html):
    body = _colors_body(index_html)
    for key in ("EP_GREEN", "SUCCESS", "ERROR", "WARNING", "INFO", "NEUTRAL"):
        assert key + ":" in body, f"COLORS.{key} fehlt"


def test_colors_values_are_valid_hex(index_html):
    body = _colors_body(index_html)
    hex_re = re.compile(r'"(#[0-9a-fA-F]{6})"')
    hexes = hex_re.findall(body)
    assert len(hexes) >= 6, "expected at least 6 hex values"
    for h in hexes:
        assert re.match(r"^#[0-9a-fA-F]{6}$", h), f"bad hex {h}"


def test_colors_ep_green_matches_legacy_constant(index_html):
    body = _colors_body(index_html)
    assert 'EP_GREEN:"#009640"' in body


def test_at_least_50_colors_usages_in_styles(index_html):
    """Min 50 inline style values referenzieren COLORS.* (nach 5 Batches)."""
    pattern = re.compile(r'(color|background):COLORS\.(SUCCESS|ERROR|WARNING|INFO|NEUTRAL|EP_GREEN)')
    hits = pattern.findall(index_html)
    assert len(hits) >= 50, f"only {len(hits)} COLORS.* style usages, need >=50"


def test_colors_success_used(index_html):
    assert "COLORS.SUCCESS" in index_html


def test_colors_error_used(index_html):
    assert "COLORS.ERROR" in index_html


def test_colors_warning_used(index_html):
    assert "COLORS.WARNING" in index_html


def test_colors_info_used(index_html):
    assert "COLORS.INFO" in index_html
