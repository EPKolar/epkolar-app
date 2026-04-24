"""Behavior tests for _juprowaReversMap (v3.8.40 Adress-Block-Fix).

Ensures the push payload contains the required LKZ + address fields
verified against real juprowa_raw response (S075295, juprowa_id=5085210).
"""
import json
import pytest
from conftest import run_node_snippet


def _call(node_exe, fn_bundle, schein_js):
    """Run the bundle and JSON-stringify _juprowaReversMap(schein)."""
    snippet = (
        fn_bundle
        + f";process.stdout.write(JSON.stringify(_juprowaReversMap({schein_js})))"
    )
    raw = run_node_snippet(node_exe, snippet)
    return json.loads(raw)


def _full_mock():
    """Return a JS-literal string for a fully-populated Mock-Schein."""
    return (
        "{"
        "juprowa_id:'5085210',"
        "nummer:'S075295',"
        "durchgefuehrte:'Fehler behoben',"
        "notizen:'Kunde informiert',"
        "arbeitsanweisungen:'Sicherung pruefen',"
        "monteur:'w1',"
        "terminBestaetigt:'2026-04-25',"
        "terminZeit:'08:30',"
        "dauer:'2',"
        "prioritaet:'normal',"
        "scheinstatus:'in_bearbeitung',"
        "kundStr:'Teststrasse 1',"
        "kundPlz:'3400',"
        "kundOrt:'Klosterneuburg',"
        "kundName:'Huber GmbH'"
        "}"
    )


def test_push_contains_all_new_address_keys(node_exe, fn_juprowa_reverse_map):
    out = _call(node_exe, fn_juprowa_reverse_map, _full_mock())
    for key in ("AK_BAUADR_STR", "AK_BAUADR_PLZ", "AK_BAUADR_ORT",
                "AK_BAUADR_LKZ", "AK_BAUADR_NAM1",
                "RE_ADR_STR", "RE_ADR_PLZ", "RE_ADR_ORT",
                "RE_ADR_LKZ", "RE_ADR_NAM1"):
        assert key in out, f"Push payload missing {key}"


def test_ak_bauadr_lkz_hardcoded_A(node_exe, fn_juprowa_reverse_map):
    out = _call(node_exe, fn_juprowa_reverse_map, _full_mock())
    assert out["AK_BAUADR_LKZ"] == "A"


def test_re_adr_lkz_hardcoded_A(node_exe, fn_juprowa_reverse_map):
    out = _call(node_exe, fn_juprowa_reverse_map, _full_mock())
    assert out["RE_ADR_LKZ"] == "A"


def test_empty_kundstr_becomes_empty_string(node_exe, fn_juprowa_reverse_map):
    schein = (
        "{juprowa_id:'X',nummer:'Y',durchgefuehrte:'',notizen:'',"
        "arbeitsanweisungen:'',prioritaet:'keine',"
        "kundStr:'',kundPlz:'',kundOrt:'',kundName:''}"
    )
    out = _call(node_exe, fn_juprowa_reverse_map, schein)
    for key in ("AK_BAUADR_STR", "AK_BAUADR_PLZ", "AK_BAUADR_ORT",
                "AK_BAUADR_NAM1", "RE_ADR_STR", "RE_ADR_PLZ",
                "RE_ADR_ORT", "RE_ADR_NAM1"):
        assert out[key] == "", f"{key} should be empty string, got {out[key]!r}"
    # LKZ stays hardcoded
    assert out["AK_BAUADR_LKZ"] == "A"
    assert out["RE_ADR_LKZ"] == "A"


def test_umlauts_stay_intact_latin1_compatible(node_exe, fn_juprowa_reverse_map):
    # Umlauts (\u00E4/F6/FC/DF) are Latin-1 native, _juprowaSanitize
    # does NOT substitute them. They must pass through unchanged.
    schein = (
        "{juprowa_id:'X',nummer:'Y',"
        "durchgefuehrte:'',notizen:'',arbeitsanweisungen:'',"
        "prioritaet:'keine',"
        "kundStr:'Sch\u00F6ngasse 5',"
        "kundPlz:'5020',"
        "kundOrt:'M\u00FCnchen',"
        "kundName:'Gr\u00FCn & Sch\u00F6n e.U.'}"
    )
    out = _call(node_exe, fn_juprowa_reverse_map, schein)
    # Compare Python-decoded strings directly (not JSON-escaped form).
    assert out["AK_BAUADR_STR"] == "Sch\u00F6ngasse 5"
    assert out["AK_BAUADR_ORT"] == "M\u00FCnchen"
    assert out["AK_BAUADR_NAM1"] == "Gr\u00FCn & Sch\u00F6n e.U."
    assert out["RE_ADR_NAM1"] == "Gr\u00FCn & Sch\u00F6n e.U."


def test_em_dash_gets_sanitized_in_address(node_exe, fn_juprowa_reverse_map):
    # Non-Latin1 chars like em-dash get substituted by _juprowaSanitize
    schein = (
        "{juprowa_id:'X',nummer:'Y',"
        "durchgefuehrte:'',notizen:'',arbeitsanweisungen:'',"
        "prioritaet:'keine',"
        "kundStr:'Foo \u2014 Bar',"
        "kundPlz:'0',kundOrt:'',kundName:''}"
    )
    out = _call(node_exe, fn_juprowa_reverse_map, schein)
    assert out["AK_BAUADR_STR"] == "Foo -- Bar"
    assert out["RE_ADR_STR"] == "Foo -- Bar"


def test_legacy_9_ak_fields_still_present(node_exe, fn_juprowa_reverse_map):
    out = _call(node_exe, fn_juprowa_reverse_map, _full_mock())
    # Regression guard: the 9 pre-v3.8.40 fields must still be there
    for key in ("ID", "AK_SCHEINNR", "AK_ARBEITEN", "AK_NOTIZ",
                "AK_DURCHZUFUEHREN", "AK_TERMIN", "AK_DAUER",
                "AK_PRIOR", "AK_AUFSTATUS"):
        assert key in out, f"Legacy field {key} regressed"


def test_payload_key_count_exactly_19_without_monteur(node_exe, fn_juprowa_reverse_map):
    # Without schein.monteur (_juprowaWorkerToCode stubbed to null)
    # AK_MONTEUR is skipped. Count:
    #   base: ID, AK_SCHEINNR (2)
    #   arbeits: AK_ARBEITEN, AK_NOTIZ, AK_DURCHZUFUEHREN (3)
    #   termin+dauer: AK_TERMIN, AK_DAUER (2)
    #   prio+status: AK_PRIOR, AK_AUFSTATUS (2)
    #   adresse neu: AK_BAUADR_{STR,PLZ,ORT,LKZ,NAM1} (5)
    #   rechnung neu: RE_ADR_{STR,PLZ,ORT,LKZ,NAM1} (5)
    #   TOTAL: 19
    out = _call(node_exe, fn_juprowa_reverse_map, _full_mock())
    assert len(out) == 19, f"expected 19 keys, got {len(out)}: {sorted(out.keys())}"


def test_no_titel_fields_in_payload(node_exe, fn_juprowa_reverse_map):
    # AK_BAUADR_TITEL + RE_ADR_TITEL are Pull-Only (v3.8.40 comment explains why).
    # Regression guard: they must NOT appear in push payload.
    out = _call(node_exe, fn_juprowa_reverse_map, _full_mock())
    assert "AK_BAUADR_TITEL" not in out
    assert "RE_ADR_TITEL" not in out


def test_returns_null_without_juprowa_id(node_exe, fn_juprowa_reverse_map):
    # _juprowaReversMap early-exits when schein.juprowa_id is falsy
    snippet = (
        fn_juprowa_reverse_map
        + ";process.stdout.write(JSON.stringify(_juprowaReversMap({nummer:'X'})))"
    )
    raw = run_node_snippet(node_exe, snippet)
    assert raw == "null"
