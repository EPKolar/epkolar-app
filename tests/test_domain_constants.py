"""Domain-Konstanten Smoke: AS_PRIO, AS_ART, AS_VERRECH, JUPROWA_PRIO_*, JUPROWA_ART_MAP.

Tag 4 / Theme 4. Strukturelle Verifikation via Node-eval.
"""
import json
import re
import pytest
from conftest import run_node_snippet


def _extract_const_obj(node_exe, index_html, name):
    pattern = r"const " + re.escape(name) + r"=\{[^;]+\};"
    m = re.search(pattern, index_html)
    assert m, f"const {name} not found"
    # v3.9.66 Theme-Token Partial Migration: several maps reference COLORS.ERROR
    # (AS_PRIO, AS_VERRECH, WZ_STATUS, ...). Inject a COLORS stub so node-eval
    # of the isolated const-snippet still resolves.
    colors_stub = (
        'const COLORS={EP_GREEN:"#009640",SUCCESS:"#22c55e",ERROR:"#ef4444",'
        'ERROR_DARK:"#ff6b6b",WARNING:"#f97316",INFO:"#3b82f6",NEUTRAL:"#71717a"};'
    )
    snippet = colors_stub + m.group(0) + f";process.stdout.write(JSON.stringify({name}))"
    return json.loads(run_node_snippet(node_exe, snippet))


# ----- AS_PRIO -----
def test_as_prio_has_5_levels(node_exe, index_html):
    obj = _extract_const_obj(node_exe, index_html, "AS_PRIO")
    assert len(obj) == 5
    assert set(obj.keys()) == {"keine", "niedrig", "normal", "hoch", "dringend"}


def test_as_prio_each_has_label_color(node_exe, index_html):
    obj = _extract_const_obj(node_exe, index_html, "AS_PRIO")
    for k, v in obj.items():
        assert "l" in v and "c" in v


# ----- AS_ART -----
def test_as_art_has_7_types(node_exe, index_html):
    obj = _extract_const_obj(node_exe, index_html, "AS_ART")
    assert len(obj) == 7


def test_as_art_kein_present(node_exe, index_html):
    obj = _extract_const_obj(node_exe, index_html, "AS_ART")
    assert "kein" in obj
    assert obj["kein"]["l"] == "kein"


def test_as_art_stoerung_has_lightning(node_exe, index_html):
    obj = _extract_const_obj(node_exe, index_html, "AS_ART")
    assert obj["stoerung"]["i"]  # icon set


# ----- AS_VERRECH -----
def test_as_verrech_has_3_modes(node_exe, index_html):
    obj = _extract_const_obj(node_exe, index_html, "AS_VERRECH")
    assert set(obj.keys()) == {"verrechenbar", "nicht_verrechenbar", "garantie"}


def test_as_verrech_each_has_label_color(node_exe, index_html):
    obj = _extract_const_obj(node_exe, index_html, "AS_VERRECH")
    for k, v in obj.items():
        assert "l" in v and "c" in v


# ----- JUPROWA_ART_MAP -----
def test_juprowa_art_map_codes_0_to_6(node_exe, index_html):
    obj = _extract_const_obj(node_exe, index_html, "JUPROWA_ART_MAP")
    expected_codes = {"0", "1", "2", "3", "4", "5", "6"}
    assert set(obj.keys()) == expected_codes


def test_juprowa_art_map_targets_in_as_art(node_exe, index_html):
    art_map = _extract_const_obj(node_exe, index_html, "JUPROWA_ART_MAP")
    as_art = _extract_const_obj(node_exe, index_html, "AS_ART")
    for code, art in art_map.items():
        assert art in as_art, f"JUPROWA_ART_MAP[{code}]={art} not in AS_ART"


# ----- JUPROWA_PRIO_MAP -----
def test_juprowa_prio_map_minimal(node_exe, index_html):
    obj = _extract_const_obj(node_exe, index_html, "JUPROWA_PRIO_MAP")
    assert obj["0"] == "keine"
    assert obj["1"] == "hoch"


# ----- JUPROWA_PRIO_REV -----
def test_juprowa_prio_rev_keine_to_zero(node_exe, index_html):
    obj = _extract_const_obj(node_exe, index_html, "JUPROWA_PRIO_REV")
    assert obj.get("keine") == "0"
    assert obj.get("hoch") == "1"


def test_juprowa_prio_rev_legacy_keys_present(node_exe, index_html):
    # Bekannter Befund: REV hat Legacy-Keys "niedig" (typo!), "aufgeschoben"
    # die in AS_PRIO nicht existieren - dokumentiert aber nicht aktiv genutzt.
    obj = _extract_const_obj(node_exe, index_html, "JUPROWA_PRIO_REV")
    # Mindestens die echten 5 + alte sollten alle "0" oder "1" sein
    for k, v in obj.items():
        assert v in ("0", "1"), f"REV[{k}]={v} not 0/1"


# ----- WZ_STATUS (Werkzeug) -----
def test_wz_status_has_states(node_exe, index_html):
    obj = _extract_const_obj(node_exe, index_html, "WZ_STATUS")
    assert "verfuegbar" in obj
    assert "ausgegeben" in obj
    assert "reparatur" in obj
