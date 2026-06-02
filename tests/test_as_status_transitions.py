"""AS-Status: Constants + Group-Membership + Juprowa-Roundtrip.

Tag 4 / Theme 2.
"""
import json
import re
import pytest
from conftest import run_node_snippet


@pytest.fixture(scope="session")
def as_status_obj(node_exe, index_html):
    """Eval AS_STATUS const-decl in Node and return as Python dict.

    v3.9.66 Theme-Token Partial Migration: AS_STATUS.storniert.c now references
    COLORS.ERROR — so we must extract the COLORS const too (or inject a stub).
    We inject a stub so this test stays independent of COLORS-formatting changes.
    """
    m = re.search(r"const AS_STATUS=\{[^;]+\};", index_html)
    assert m
    colors_stub = (
        'const COLORS={EP_GREEN:"#009640",SUCCESS:"#22c55e",ERROR:"#ef4444",'
        'ERROR_DARK:"#ff6b6b",WARNING:"#f97316",INFO:"#3b82f6",NEUTRAL:"#71717a"};'
    )
    snippet = colors_stub + m.group(0) + ";process.stdout.write(JSON.stringify(AS_STATUS))"
    return json.loads(run_node_snippet(node_exe, snippet))


@pytest.fixture(scope="session")
def jp_status_map(node_exe, index_html):
    m = re.search(r"const JUPROWA_STATUS_MAP=\{[^;]+\};", index_html)
    assert m
    snippet = m.group(0) + ";process.stdout.write(JSON.stringify(JUPROWA_STATUS_MAP))"
    return json.loads(run_node_snippet(node_exe, snippet))


@pytest.fixture(scope="session")
def jp_status_rev(node_exe, index_html):
    m = re.search(r"const JUPROWA_STATUS_REV=\{[^;]+\};", index_html)
    assert m
    snippet = m.group(0) + ";process.stdout.write(JSON.stringify(JUPROWA_STATUS_REV))"
    return json.loads(run_node_snippet(node_exe, snippet))


def test_as_status_has_8_states(as_status_obj):
    assert len(as_status_obj) == 8, f"expected 8 states, got {len(as_status_obj)}"


def test_as_status_keys_complete(as_status_obj):
    expected = {"aufgenommen", "freigegeben", "in_bearbeitung", "aufgeschoben",
                "erledigt", "abgerechnet", "bar_bezahlt", "storniert"}
    assert set(as_status_obj.keys()) == expected


def test_as_status_each_has_label_color_icon_grp(as_status_obj):
    for key, val in as_status_obj.items():
        for prop in ("l", "c", "i", "grp"):
            assert prop in val, f"AS_STATUS.{key} missing '{prop}'"


def test_as_status_grp_values_valid(as_status_obj):
    valid = {"offen", "fertig", "storniert"}
    for key, val in as_status_obj.items():
        assert val["grp"] in valid, f"AS_STATUS.{key}.grp = {val['grp']!r} not in {valid}"


def test_as_grp_offen_matches_status(as_status_obj, index_html):
    m = re.search(r'const AS_GRP_OFFEN=\[([^\]]+)\];', index_html)
    arr = re.findall(r'"([^"]+)"', m.group(1))
    for s in arr:
        assert as_status_obj[s]["grp"] == "offen", f"{s} marked offen but AS_STATUS says {as_status_obj[s]['grp']}"


def test_as_grp_fertig_matches_status(as_status_obj, index_html):
    m = re.search(r'const AS_GRP_FERTIG=\[([^\]]+)\];', index_html)
    arr = re.findall(r'"([^"]+)"', m.group(1))
    for s in arr:
        assert as_status_obj[s]["grp"] == "fertig"


def test_juprowa_status_map_to_internal(jp_status_map):
    # All Juprowa-Codes 0-20 sollten auf valid AS_STATUS-Keys mappen
    valid_internal = {"aufgenommen", "freigegeben", "in_bearbeitung",
                      "aufgeschoben", "erledigt", "abgerechnet",
                      "bar_bezahlt", "storniert"}
    for code, internal in jp_status_map.items():
        assert internal in valid_internal, f"{code} -> {internal} (invalid)"


def test_juprowa_status_rev_complete(jp_status_rev):
    expected = {"aufgenommen", "freigegeben", "in_bearbeitung", "aufgeschoben",
                "erledigt", "abgerechnet", "bar_bezahlt", "storniert"}
    assert set(jp_status_rev.keys()) == expected


def test_juprowa_roundtrip_status(jp_status_map, jp_status_rev):
    """Wenn JP-MAP[code]=internal, dann JP-REV[internal] sollte equivalent sein."""
    # Some MAP codes share targets (e.g. 1+4 -> freigegeben). REV picks one.
    # Test: jeder REV-Wert taucht in MAP auf
    map_codes = set(jp_status_map.keys())
    for internal, code in jp_status_rev.items():
        assert code in map_codes, f"REV[{internal}]={code} but MAP has no such code"
        assert jp_status_map[code] == internal, (
            f"REV says {internal}->{code}, but MAP[{code}]={jp_status_map[code]}"
        )
