"""A11y htmlFor pilot - Tag 2 (Di 29.04).

Verifiziert dass mindestens 20 Label-Elemente htmlFor + matching id haben
und die IDs eindeutig sind.
"""
import re

ID_RE = re.compile(r'htmlFor:"(lbl_[A-Za-z0-9_]+)"')
INPUT_ID_RE = re.compile(r'id:"(lbl_[A-Za-z0-9_]+)"')
NAME_RE = re.compile(r"^lbl_[a-zA-Z][a-zA-Z0-9]*_[a-zA-Z][a-zA-Z0-9]*$")


def _htmlfor_ids(index_html):
    return ID_RE.findall(index_html)


def _input_ids(index_html):
    return INPUT_ID_RE.findall(index_html)


def test_at_least_20_htmlfor_bindings(index_html):
    found = _htmlfor_ids(index_html)
    assert len(found) >= 20, f"only {len(found)} htmlFor lbl_-bindings, need 20"


def test_pilot_ids_are_unique(index_html):
    found = _htmlfor_ids(index_html)
    counts = {}
    for h in found:
        counts[h] = counts.get(h, 0) + 1
    dupes = {k: v for k, v in counts.items() if v > 1}
    assert not dupes, f"duplicate htmlFor IDs: {dupes}"


def test_each_htmlfor_has_matching_input_id(index_html):
    htmlfors = set(_htmlfor_ids(index_html))
    ids = set(_input_ids(index_html))
    missing = htmlfors - ids
    assert not missing, f"htmlFor without matching input id: {missing}"


def test_pilot_ids_follow_naming_convention(index_html):
    found = _htmlfor_ids(index_html)
    bad = [h for h in found if not NAME_RE.match(h)]
    assert not bad, f"IDs violating lbl_<comp>_<field>: {bad}"


def test_login_form_labels_present(index_html):
    htmlfors = set(_htmlfor_ids(index_html))
    assert "lbl_login_user" in htmlfors
    assert "lbl_login_pw" in htmlfors


def test_monteur_form_core_labels_present(index_html):
    htmlfors = set(_htmlfor_ids(index_html))
    for f in ("name", "vorname", "rolle", "telefon", "email"):
        key = "lbl_monteurNew_" + f
        assert key in htmlfors, f"{key} missing"


def test_asform_address_labels_present(index_html):
    htmlfors = set(_htmlfor_ids(index_html))
    for f in ("kundNr", "kundName", "kundStr", "kundPlz", "kundOrt"):
        key = "lbl_asForm_" + f
        assert key in htmlfors, f"{key} missing"
