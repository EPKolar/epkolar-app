"""v3.9.502 — Regression-Tests gegen JSONB-Doppel-Serialisierung in weekplan_rows.z.

Bug-Quelle (Chat-Claude live-bewiesen): _mapWpr (Server-Handler ~Z.2255) machte
`JSON.stringify(r.z)` für die JSONB-Spalte z → String-Value landete in JSONB
statt Objekt-Value → Frontend liest r.z als String → r.z.Mo undefined →
hasContent-Checks falsifizieren → Belegung "verschwindet" nach Polling/Reload.

Symptom war "Kopieren / neue Projekte / Freitext werden nicht übernommen".

Tests prüfen statische Code-Properties (analog zu test_wp_keying_0h_v3482).
Runtime-Test via Playwright nicht möglich, da _mapWpr eine lokale const im
Server-Handler-Block ist (nicht window-exposed); pytest gegen index.html
ist der vorhandene Test-Stack.
"""
import pathlib
import re

SRC = pathlib.Path(__file__).resolve().parent.parent / "index.html"
HTML = SRC.read_text(encoding="utf-8")


def _mapwpr_region():
    """Region zwischen `const _mapWpr` und dem darauf folgenden `_sbUpsert("weekplan_rows"`-Aufruf."""
    start = HTML.find("const _mapWpr")
    assert start >= 0, "_mapWpr-Definition fehlt im Server-Handler"
    end = HTML.find('_sbUpsert("weekplan_rows"', start)
    assert end > start, '_sbUpsert("weekplan_rows") nach _mapWpr nicht gefunden'
    return HTML[start:end]


def test_wp502_A_mapwpr_string_input_parsed_to_object():
    """T-WP-502-A: _mapWpr String-Input → Objekt (defensiver Parse).

    Der z-Mapper MUSS einen String-r.z über _safeJsonParse zurück zu einem
    Objekt parsen, statt ihn (wie der v3.9.501-Bug) als String durchzureichen
    oder erneut zu stringifizieren.
    """
    region = _mapwpr_region()
    assert "_safeJsonParse(r.z" in region, (
        "T-WP-502-A FAIL: _mapWpr.z mappt einen String-Input nicht via "
        "_safeJsonParse(r.z, {}) zurück zu einem Objekt — JSONB-Doppel-"
        "Serialisierung würde wieder auftreten."
    )


def test_wp502_B_mapwpr_null_input_safe_default():
    """T-WP-502-B: _mapWpr null/leerer Input → leeres Objekt, kein Crash.

    Wenn r.z undefined/null ist, MUSS der Fallback {} verwendet werden — niemals
    null. PostgREST würde sonst die DEFAULT '{}' der z-Spalte ggf. nicht setzen.
    """
    region = _mapwpr_region()
    # Object-Default `(r.z||{})` muss existieren (für Object-Input + falsy-fallback):
    has_object_default = "(r.z||{})" in region or "(r.z || {})" in region
    # String-Default `_safeJsonParse(r.z, {})` mit fallback {}:
    has_string_default = re.search(r"_safeJsonParse\(r\.z\s*,\s*\{\s*\}\s*\)", region) is not None
    assert has_object_default, (
        "T-WP-502-B FAIL: Objekt-Fallback (r.z||{}) fehlt — null/undefined würde "
        "als z gesendet, PostgREST könnte NOT-NULL-Constraint verletzen."
    )
    assert has_string_default, (
        "T-WP-502-B FAIL: String-Fallback _safeJsonParse(r.z, {}) fehlt — "
        "fehlerhafte/leere String-z würden null statt {} liefern."
    )


def test_wp502_C_mapwpr_object_passthrough_no_restringify():
    """T-WP-502-C: _mapWpr Objekt-Input → Passthrough (kein Re-Stringify).

    Wenn r.z bereits ein Objekt ist (Normalfall ab v3.9.500 saveDirty),
    MUSS es unverändert weitergereicht werden — KEIN JSON.stringify mehr im
    z-Mapping. PostgREST encoded application/json mit Objekt-Werten korrekt
    zu JSONB.
    """
    region = _mapwpr_region()
    # Der Alt-Bug-Branch JSON.stringify(r.z…) MUSS WEG sein im Code (Kommentar OK).
    # Suche nach allen Vorkommen von "JSON.stringify(r.z" und filtere
    # Kommentarzeilen heraus (Zeilen, die mit Leerzeichen+'//' oder '*' beginnen).
    bug_occurrences = []
    for i, line in enumerate(region.split("\n")):
        if "JSON.stringify(r.z" not in line:
            continue
        stripped = line.lstrip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        # Pattern KÖNNTE in einem mehrzeiligen Kommentar stehen — prüfe ob
        # vor dem Match ein '/*' steht und kein '*/' dazwischen.
        before = "\n".join(region.split("\n")[:i + 1])
        last_open = before.rfind("/*")
        last_close = before.rfind("*/")
        if last_open > last_close:
            continue  # mitten in /* ... */ Block-Kommentar
        bug_occurrences.append((i, line.strip()))
    assert not bug_occurrences, (
        f"T-WP-502-C FAIL: alter JSON.stringify(r.z…)-Code noch da: {bug_occurrences}. "
        "JSONB würde wieder String-Value statt Objekt-Value bekommen."
    )


def test_wp502_load_path_defensive_parse_kept():
    """Regression-Gate: Load-Path (_loadWeekplansFromRows) behält defensiven
    String-Parse für DB-Altlasten (Zeilen, die durch den Pre-v3.9.502-Bug als
    String-Value in der JSONB-Spalte gespeichert wurden). Self-Healing-Pfad.
    """
    assert "z:typeof r.z==='string'?_safeJsonParse(r.z,{}):(r.z||{})" in HTML, (
        "Load-Path-Defensive-Parse Z.5335 fehlt — DB-Altlasten mit "
        "String-z würden im Frontend als String hängen bleiben."
    )
