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
def test_as_prio_has_7_levels(node_exe, index_html):
    # v3.9.548: 7 OFFA-Stufen (vorher 5; "dringend" raus, +aufgeschoben/sehr hoch/FIXTERMIN)
    obj = _extract_const_obj(node_exe, index_html, "AS_PRIO")
    assert len(obj) == 7
    assert set(obj.keys()) == {"keine", "aufgeschoben", "niedrig", "normal", "hoch", "sehr hoch", "FIXTERMIN"}


def test_as_prio_each_has_label_color(node_exe, index_html):
    obj = _extract_const_obj(node_exe, index_html, "AS_PRIO")
    for k, v in obj.items():
        assert "l" in v and "c" in v


# ----- AS_ART -----
def test_as_art_has_9_types(node_exe, index_html):
    # v3.9.127 F5: +wartung+regie (parseVoice setzte sie, Keys fehlten -> "?"-Rendering)
    obj = _extract_const_obj(node_exe, index_html, "AS_ART")
    assert len(obj) == 9
    assert "wartung" in obj and "regie" in obj


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
def test_juprowa_prio_map_offa_codes(node_exe, index_html):
    # v3.9.548: OFFA-Codes 1-7 (1=keine ... 5=hoch ... 7=FIXTERMIN); 0=keine
    obj = _extract_const_obj(node_exe, index_html, "JUPROWA_PRIO_MAP")
    assert obj["0"] == "keine"
    assert obj["1"] == "keine"
    assert obj["3"] == "niedrig"
    assert obj["5"] == "hoch"
    assert obj["6"] == "sehr hoch"
    assert obj["7"] == "FIXTERMIN"


# ----- JUPROWA_PRIO_REV -----
def test_juprowa_prio_rev_offa_codes(node_exe, index_html):
    # v3.9.548: Label->OFFA-Code 1-7 (keine->1, hoch->5, FIXTERMIN->7)
    obj = _extract_const_obj(node_exe, index_html, "JUPROWA_PRIO_REV")
    assert obj.get("keine") == "1"
    assert obj.get("hoch") == "5"
    assert obj.get("FIXTERMIN") == "7"


def test_juprowa_prio_rev_full_7_stages(node_exe, index_html):
    # v3.9.548: REV = exakt die 7 OFFA-Stufen, Codes 1-7, Keys == AS_PRIO-Keys
    obj = _extract_const_obj(node_exe, index_html, "JUPROWA_PRIO_REV")
    assert obj == {"keine": "1", "aufgeschoben": "2", "niedrig": "3", "normal": "4", "hoch": "5", "sehr hoch": "6", "FIXTERMIN": "7"}


# ----- WZ_STATUS (Werkzeug) -----
def test_wz_status_has_states(node_exe, index_html):
    obj = _extract_const_obj(node_exe, index_html, "WZ_STATUS")
    assert "verfuegbar" in obj
    assert "ausgegeben" in obj
    assert "reparatur" in obj
