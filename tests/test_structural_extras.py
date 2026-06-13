"""Structural invariants for specific domain constants + patterns."""
import re


# EP_AUTO_FILTER -----------------------------------------------------------
def _ep_filter_body(index_html):
    m = re.search(r"const EP_AUTO_FILTER=\[([\s\S]*?)\];", index_html)
    assert m, "EP_AUTO_FILTER array not found"
    return m.group(1)


def test_ep_auto_filter_defined(index_html):
    assert "const EP_AUTO_FILTER=[" in index_html


def test_ep_auto_filter_has_77_groups(index_html):
    body = _ep_filter_body(index_html)
    count = len(re.findall(r"\{id:", body))
    assert count == 77, f"EP_AUTO_FILTER count drifted: {count}, expected 77"


def test_ep_auto_filter_has_required_keys_per_entry(index_html):
    body = _ep_filter_body(index_html)
    entries = re.findall(r"\{id:\s*['\"][^'\"]+['\"][^}]+\}", body)[:3]
    for e in entries:
        assert "id:" in e
        assert "l:" in e or "name:" in e or "label:" in e


# TEXT_JSON_FIELDS ---------------------------------------------------------
def test_text_json_fields_present(index_html):
    m = re.search(r"const TEXT_JSON_FIELDS=\[([^\]]+)\]", index_html)
    assert m, "TEXT_JSON_FIELDS not found"


def test_text_json_fields_contains_six_core_fields(index_html):
    m = re.search(r"const TEXT_JSON_FIELDS=\[([^\]]+)\]", index_html)
    body = m.group(1)
    for field in ("perms_override", "tank_log", "km_log", "tags", "config", "order_items"):
        assert "'" + field + "'" in body, f"TEXT_JSON_FIELDS missing {field}"


def test_text_json_fields_has_documentation(index_html):
    assert "v3.8.37 L3-Doku" in index_html


# kunde_freigabe (Integer coercion) ----------------------------------------
def test_kunde_freigabe_coerced_to_integer(index_html):
    assert "d.kunde_freigabe||0" in index_html


def test_kunde_freigabe_write_uses_integer_literal(index_html):
    assert "{kunde_freigabe:0}" in index_html
    assert "{kunde_freigabe:1}" in index_html


def test_kunde_freigabe_no_boolean_writes(index_html):
    assert "kunde_freigabe:true" not in index_html
    assert "kunde_freigabe:false" not in index_html


# 38.5h Basis --------------------------------------------------------------
def test_38_5h_basis_present(index_html):
    assert "38,5h" in index_html or "38.5h" in index_html


def test_38_5h_basis_in_dashboard_text(index_html):
    assert "Basis 38,5h" in index_html


# Datum-Parsing ------------------------------------------------------------
def test_iso_date_parse_pattern(index_html):
    assert "isNaN(dt)" in index_html or "isNaN(diff)" in index_html


def test_german_date_parse_pattern(index_html):
    assert '.split(".")' in index_html


# _juprowaSanitize ---------------------------------------------------------
def test_juprowa_sanitize_defined(index_html):
    assert "function _juprowaSanitize" in index_html


def test_juprowa_sanitize_handles_all_replacements(index_html):
    m = re.search(r"function _juprowaSanitize[\s\S]+?\n\}", index_html)
    assert m
    body = m.group(0)
    # Source-file contains regex patterns with unicode escape sequences.
    # Each escape is 6 chars (backslash + u + 4 hex). Check for each literal.
    for esc in ("\\u2014", "\\u2013", "\\u2018", "\\u2019",
                "\\u201C", "\\u201D", "\\u20AC", "\\u2026", "\\u00A0"):
        assert esc in body, "_juprowaSanitize body missing " + esc


# _mapBody whitelist -------------------------------------------------------
def test_mapbody_defined(index_html):
    assert "function _mapBody" in index_html


def test_mapbody_skips_password_field(index_html):
    m = re.search(r"function _mapBody\([\s\S]+?\n\}", index_html)
    assert m
    body = m.group(0)
    assert "k==='password'" in body or 'k=="password"' in body


def test_mapbody_uses_text_json_fields_check(index_html):
    m = re.search(r"function _mapBody\([\s\S]+?\n\}", index_html)
    assert m
    body = m.group(0)
    assert "TEXT_JSON_FIELDS.includes" in body


# MONT / Monteure ----------------------------------------------------------
def test_mont_constants_table_present(index_html):
    assert re.search(r"\bMONT\s*=\s*\[", index_html), "MONT-Tabelle fehlt"


# Fix-B Pre-Wipe-Drain-Guard (v3.9.352) ------------------------------------
def test_fixb_drain_guard_before_idb_wipe(index_html):
    """Vor indexedDB.deleteDatabase('epkolar_offline') (Lokale-Daten-loeschen-Button)
    muss ein SQ.count()-Check + Drain/Warnung stehen — sonst gehen ungesyncte
    Tickets/Eintraege/Fotos beim Wipe verloren (Ursache Sparkasse-Tickets)."""
    # Marker-Kommentar vorhanden
    assert "Fix-B Pre-Wipe-Drain-Guard" in index_html, "Fix-B-Marker fehlt"
    # Der Guard-Block muss VOR dem deleteDatabase-Aufruf des Buttons SQ.count + PhotoQ.count nutzen
    m = re.search(
        r"Fix-B Pre-Wipe-Drain-Guard[\s\S]{0,3000}?deleteDatabase\(\"epkolar_offline\"\)",
        index_html,
    )
    assert m, "Fix-B-Block nicht vor deleteDatabase gefunden"
    body = m.group(0)
    assert "await SQ.count()" in body, "Guard prueft SQ.count() nicht"
    assert "PhotoQ.count()" in body, "Guard prueft PhotoQ.count() nicht"
    assert "window.__doSync" in body, "Guard versucht keinen Drain via __doSync"
    assert "UNWIEDERBRINGLICH" in body, "harte Warnung mit Verlust-Hinweis fehlt"


def test_fixb_logout_guard_untouched(index_html):
    """Die bestehende Logout-Absicherung (Vorlage) muss unveraendert bleiben."""
    assert "const cnt=await SQ.count();const _pcnt=await PhotoQ.count()" in index_html
    assert "werden VERWORFEN. Trotzdem abmelden" in index_html


# 0-rows-Safeguard (v3.9.306 #3) — RLS-Silent-Denial bei Fahrzeug-/Tank-Save -
def test_fahrzeug_patch_captures_result(index_html):
    """Generischer PATCH muss das _sbPatch-Ergebnis erfassen (für 0-rows-Check)."""
    assert "const _patchRes=await _sbPatch(table,idOrSub,patchData);" in index_html


def test_fahrzeug_zero_rows_safeguard_present(index_html):
    """Bei 0 betroffenen Zeilen (RLS-Denial) muss eine Warnung statt stillem Verlust feuern.

    v3.9.323: fahrzeuge-Hardcode-Check durch _RLS_SILENT_DENIAL_LABELS-Map-Lookup ersetzt
    (Defense-in-Depth fuer RLS-Welle-1). Test verifiziert jetzt das generalisierte Pattern.
    """
    assert "_RLS_SILENT_DENIAL_LABELS=Object.freeze" in index_html, (
        "_RLS_SILENT_DENIAL_LABELS-Map fehlt"
    )
    assert "fahrzeuge:" in index_html, "fahrzeuge-Eintrag in RLS-Label-Map fehlt"
    m = re.search(
        r"if\(_RLS_SILENT_DENIAL_LABELS\[table\]\s*&&\s*Array\.isArray\(_patchRes\)\s*&&\s*_patchRes\.length===0\)\{([\s\S]{0,300}?)\}",
        index_html,
    )
    assert m, "0-rows-Safeguard mit Map-Lookup fehlt (v3.9.323-Form)"
    body = m.group(1)
    assert "window.__toast" in body, "Safeguard muss den User per Toast warnen"
    assert "_RLS_SILENT_DENIAL_LABELS[table]" in body, "Toast muss Label aus Map interpolieren"
