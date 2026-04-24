"""Behavior tests for _juprowaReversMap v3.8.41."""
import json
import pytest
from conftest import run_node_snippet


def _call(node_exe, fn_bundle, schein_js):
    snippet = fn_bundle + f";process.stdout.write(JSON.stringify(_juprowaReversMap({schein_js})))"
    raw = run_node_snippet(node_exe, snippet)
    return json.loads(raw)


NO_RAW = (
    "{juprowa_id:'5085210',nummer:'S075295',"
    "durchgefuehrte:'Fehler behoben',notizen:'Kunde informiert',"
    "arbeitsanweisungen:'Sicherung pruefen',prioritaet:'normal',"
    "scheinstatus:'in_bearbeitung',dauer:'2',"
    "terminBestaetigt:'2026-04-25',terminZeit:'08:30',"
    "kundStr:'Teststrasse 1',kundPlz:'3400',kundOrt:'Klosterneuburg',"
    "kundName:'Huber GmbH'}"
)

WITH_RAW = (
    "{juprowa_id:'5085210',nummer:'S075295',"
    "durchgefuehrte:'Fehler behoben',notizen:'',arbeitsanweisungen:'',"
    "prioritaet:'normal',scheinstatus:'in_bearbeitung',dauer:'2',"
    "terminBestaetigt:'',"
    "kundStr:'Monteur-Edit 9',kundPlz:'3401',kundOrt:'Zeiselmauer',"
    "kundName:'Huber GmbH',"
    "juprowa_raw:{AK_BAUADR_NUMMER:'K-207341',"
    "RE_ADR_STR:'Rechnungsgasse 5',RE_ADR_PLZ:'1010',RE_ADR_ORT:'Wien',"
    "RE_ADR_LKZ:'A',RE_ADR_NAM1:'Huber Verwaltung GmbH'}}"
)


def test_ak_bauadr_all_keys_always_present(node_exe, fn_juprowa_reverse_map):
    out = _call(node_exe, fn_juprowa_reverse_map, NO_RAW)
    for k in ("AK_BAUADR_STR", "AK_BAUADR_PLZ", "AK_BAUADR_ORT",
              "AK_BAUADR_LKZ", "AK_BAUADR_NAM1"):
        assert k in out


def test_ak_bauadr_values_from_kundstr(node_exe, fn_juprowa_reverse_map):
    out = _call(node_exe, fn_juprowa_reverse_map, NO_RAW)
    assert out["AK_BAUADR_STR"] == "Teststrasse 1"
    assert out["AK_BAUADR_PLZ"] == "3400"
    assert out["AK_BAUADR_ORT"] == "Klosterneuburg"
    assert out["AK_BAUADR_NAM1"] == "Huber GmbH"


def test_ak_bauadr_lkz_hardcoded_A(node_exe, fn_juprowa_reverse_map):
    out = _call(node_exe, fn_juprowa_reverse_map, NO_RAW)
    assert out["AK_BAUADR_LKZ"] == "A"


def test_ak_bauadr_umlauts_pass_through(node_exe, fn_juprowa_reverse_map):
    # Umlauts U+00F6, U+00FC are Latin-1 native, pass through unchanged
    schein = (
        "{juprowa_id:'X',nummer:'Y',"
        "durchgefuehrte:'',notizen:'',arbeitsanweisungen:'',"
        "prioritaet:'keine',"
        "kundStr:'Sch\u00F6ngasse 5',"
        "kundPlz:'5020',"
        "kundOrt:'M\u00FCnchen',"
        "kundName:'Gr\u00FCn e.U.'}"
    )
    out = _call(node_exe, fn_juprowa_reverse_map, schein)
    assert out["AK_BAUADR_STR"] == "Sch\u00F6ngasse 5"
    assert out["AK_BAUADR_ORT"] == "M\u00FCnchen"


def test_ak_bauadr_em_dash_sanitized(node_exe, fn_juprowa_reverse_map):
    schein = (
        "{juprowa_id:'X',nummer:'Y',"
        "durchgefuehrte:'',notizen:'',arbeitsanweisungen:'',"
        "prioritaet:'keine',"
        "kundStr:'Foo \u2014 Bar',"
        "kundPlz:'0',kundOrt:'',kundName:''}"
    )
    out = _call(node_exe, fn_juprowa_reverse_map, schein)
    assert out["AK_BAUADR_STR"] == "Foo -- Bar"


def test_ak_bauadr_empty_inputs_become_empty_strings(node_exe, fn_juprowa_reverse_map):
    schein = (
        "{juprowa_id:'X',nummer:'Y',durchgefuehrte:'',notizen:'',"
        "arbeitsanweisungen:'',prioritaet:'keine',"
        "kundStr:'',kundPlz:'',kundOrt:'',kundName:''}"
    )
    out = _call(node_exe, fn_juprowa_reverse_map, schein)
    for k in ("AK_BAUADR_STR", "AK_BAUADR_PLZ", "AK_BAUADR_ORT", "AK_BAUADR_NAM1"):
        assert out[k] == ""
    assert out["AK_BAUADR_LKZ"] == "A"


def test_re_adr_absent_without_juprowa_raw(node_exe, fn_juprowa_reverse_map):
    out = _call(node_exe, fn_juprowa_reverse_map, NO_RAW)
    for k in ("RE_ADR_STR", "RE_ADR_PLZ", "RE_ADR_ORT",
              "RE_ADR_LKZ", "RE_ADR_NAM1"):
        assert k not in out


def test_ak_bauadr_nummer_absent_without_juprowa_raw(node_exe, fn_juprowa_reverse_map):
    out = _call(node_exe, fn_juprowa_reverse_map, NO_RAW)
    assert "AK_BAUADR_NUMMER" not in out


def test_re_adr_passed_through_from_juprowa_raw(node_exe, fn_juprowa_reverse_map):
    out = _call(node_exe, fn_juprowa_reverse_map, WITH_RAW)
    assert out["RE_ADR_STR"] == "Rechnungsgasse 5"
    assert out["RE_ADR_PLZ"] == "1010"
    assert out["RE_ADR_ORT"] == "Wien"
    assert out["RE_ADR_LKZ"] == "A"
    assert out["RE_ADR_NAM1"] == "Huber Verwaltung GmbH"


def test_ak_bauadr_nummer_passed_through_from_juprowa_raw(node_exe, fn_juprowa_reverse_map):
    out = _call(node_exe, fn_juprowa_reverse_map, WITH_RAW)
    assert out["AK_BAUADR_NUMMER"] == "K-207341"


def test_re_adr_not_derived_from_kundstr(node_exe, fn_juprowa_reverse_map):
    out = _call(node_exe, fn_juprowa_reverse_map, WITH_RAW)
    assert out["AK_BAUADR_STR"] == "Monteur-Edit 9"
    assert out["RE_ADR_STR"] == "Rechnungsgasse 5"


def test_legacy_9_ak_fields_still_present(node_exe, fn_juprowa_reverse_map):
    out = _call(node_exe, fn_juprowa_reverse_map, NO_RAW)
    for k in ("ID", "AK_SCHEINNR", "AK_ARBEITEN", "AK_NOTIZ",
              "AK_DURCHZUFUEHREN", "AK_TERMIN", "AK_DAUER",
              "AK_PRIOR", "AK_AUFSTATUS"):
        assert k in out


def test_payload_key_count_14_without_raw(node_exe, fn_juprowa_reverse_map):
    out = _call(node_exe, fn_juprowa_reverse_map, NO_RAW)
    assert len(out) == 14


def test_payload_key_count_19_with_full_raw(node_exe, fn_juprowa_reverse_map):
    out = _call(node_exe, fn_juprowa_reverse_map, WITH_RAW)
    assert len(out) == 19


def test_no_titel_fields_in_payload(node_exe, fn_juprowa_reverse_map):
    out = _call(node_exe, fn_juprowa_reverse_map, WITH_RAW)
    assert "AK_BAUADR_TITEL" not in out
    assert "RE_ADR_TITEL" not in out


def test_returns_null_without_juprowa_id(node_exe, fn_juprowa_reverse_map):
    snippet = fn_juprowa_reverse_map + ";process.stdout.write(JSON.stringify(_juprowaReversMap({nummer:'X'})))"
    raw = run_node_snippet(node_exe, snippet)
    assert raw == "null"
