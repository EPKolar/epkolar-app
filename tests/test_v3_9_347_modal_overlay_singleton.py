"""Regression-Tests fuer v3.9.347 _exportReviewModal Overlay-Singleton-Fix.

URGENT-Bugfix: Vorher stapelten sich Review-Modal-Overlays bei wiederholtem
Oeffnen (editMonteurEntries / openMultiEntryEdit / Matrix-Zell-Edit nach
v3.9.345). User tippt sichtbar ins oberste Overlay, Eingaben treffen aber
darunterliegende ALTE Instanz mit unveraenderten rows. cleanup() liefert
ALTE Werte zurueck -> changed-Check false -> KEIN SQ.push -> Daten gehen
verloren obwohl Toast "gespeichert" meldet.

Fix:
  1. overlay bekommt data-epk-review-modal-Attribut (Sentinel).
  2. Vor Anlage: querySelectorAll('[data-epk-review-modal]').forEach(remove).
  3. _resolved-Flag im cleanup verhindert Doppel-Resolve (Esc + OK + BG-Klick).
  4. Defensiver Fallback wenn overlay.remove() fehlschlaegt: display:none +
     pointerEvents:none + opacity:0 -> garantiert nicht mehr interaktiv.

NICHT angetastet: SQ.push-Save-Logik in den 3 Aufrufern (editMonteurEntries,
openMultiEntryEdit, Matrix-Zell-Edit) und _juprowaPush.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


def _review_modal_block():
    start_m = re.search(r"window\._exportReviewModal\s*=\s*function\s*\(", INDEX)
    assert start_m, "_exportReviewModal-Funktion nicht gefunden"
    # Naechste top-level window.* Zuweisung als Ende-Anker
    end_m = re.search(r"\nwindow\.\w+\s*=", INDEX[start_m.end():])
    assert end_m, "Naechste window-Zuweisung nach _exportReviewModal nicht gefunden"
    return INDEX[start_m.start(): start_m.end() + end_m.start()]


def test_app_version_at_least_347():
    m = re.search(r'APP_VERSION="3\.9\.(\d+)-supabase"', INDEX)
    assert m, "APP_VERSION nicht gefunden"
    assert int(m.group(1)) >= 347, f"APP_VERSION zu niedrig: 3.9.{m.group(1)}"


def test_sw_ver_at_least_347():
    m = re.search(r"SW_VER\s*=\s*'epkolar-v3\.9\.(\d+)'", INDEX)
    assert m, "SW_VER nicht gefunden"
    assert int(m.group(1)) >= 347, f"SW_VER zu niedrig: 3.9.{m.group(1)}"


def test_cache_name_at_least_347():
    sw_js = (ROOT / "sw.js").read_text(encoding="utf-8")
    m = re.search(r'CACHE_NAME\s*=\s*"epkolar-v3\.9\.(\d+)"', sw_js)
    assert m, "CACHE_NAME nicht gefunden"
    assert int(m.group(1)) >= 347, f"CACHE_NAME zu niedrig: 3.9.{m.group(1)}"


def test_sw_header_at_least_347():
    sw_js = (ROOT / "sw.js").read_text(encoding="utf-8")
    m = re.search(r"//\s*EP Kolar Service Worker v3\.9\.(\d+)", sw_js)
    assert m, "sw.js Header nicht gefunden"
    assert int(m.group(1)) >= 347, f"sw.js Header zu niedrig: 3.9.{m.group(1)}"


def test_overlay_has_data_attribute():
    block = _review_modal_block()
    assert "setAttribute('data-epk-review-modal','1')" in block or \
        'setAttribute("data-epk-review-modal","1")' in block, \
        "data-epk-review-modal-Attribut wird nicht auf overlay gesetzt"


def test_pre_open_singleton_cleanup():
    block = _review_modal_block()
    assert "querySelectorAll('[data-epk-review-modal]')" in block or \
        'querySelectorAll("[data-epk-review-modal]")' in block, \
        "Pre-Open-Singleton-Cleanup via querySelectorAll fehlt"
    # Cleanup muss .forEach + .remove() enthalten
    pattern = re.compile(
        r"querySelectorAll\(\s*['\"]\[data-epk-review-modal\]['\"]\s*\).*?\.forEach.*?remove",
        re.DOTALL,
    )
    assert pattern.search(block), \
        "Pre-Open-Cleanup hat kein forEach(remove())-Pattern"


def test_singleton_cleanup_is_before_overlay_creation():
    """Cleanup MUSS vor createElement('div') fuer overlay laufen."""
    block = _review_modal_block()
    cleanup_pos = block.find("querySelectorAll('[data-epk-review-modal]')")
    if cleanup_pos == -1:
        cleanup_pos = block.find('querySelectorAll("[data-epk-review-modal]")')
    assert cleanup_pos >= 0, "Cleanup-Position nicht gefunden"
    overlay_create_pos = block.find("const overlay=document.createElement")
    if overlay_create_pos == -1:
        overlay_create_pos = block.find("const overlay = document.createElement")
    assert overlay_create_pos >= 0, "overlay-createElement nicht gefunden"
    assert cleanup_pos < overlay_create_pos, \
        "Singleton-Cleanup muss VOR overlay-Anlage stehen (sonst entfernt es das neue Overlay!)"


def test_resolved_double_guard():
    block = _review_modal_block()
    # Lokales Flag _resolved
    assert re.search(r"var\s+_resolved\s*=\s*false", block) or \
        re.search(r"let\s+_resolved\s*=\s*false", block), \
        "_resolved-Doppel-Resolve-Guard-Flag fehlt"
    # cleanup beginnt mit if(_resolved)return;_resolved=true;
    cleanup_m = re.search(r"function\s+cleanup\s*\(\s*answer\s*\)\s*\{([^}]+)", block)
    assert cleanup_m, "cleanup-Funktion nicht gefunden"
    head = cleanup_m.group(1)
    assert "_resolved" in head and "return" in head, \
        "cleanup oeffnet nicht mit _resolved-Guard"


def test_defensive_fallback_when_remove_fails():
    block = _review_modal_block()
    # cleanup hat _removed-Flag oder display:none/pointerEvents-Fallback
    assert ("display='none'" in block or 'display="none"' in block or
            "display:'none'" in block or 'display:"none"' in block), \
        "Defensiver display:none-Fallback fehlt"
    assert ("pointerEvents='none'" in block or 'pointerEvents="none"' in block), \
        "Defensiver pointerEvents:none-Fallback fehlt"


def test_save_logic_editMonteurEntries_unchanged():
    """Anker-Snapshot: editMonteurEntries SQ.push-PUT-Body ist UNVERAENDERT."""
    anchor = (
        'SQ.push({url:"/api/entries/"+r.id,method:"PUT",'
        'body:{date:r.datum,taetigkeit:r.taetigkeit,'
        'hours:r.stunden,bemerkung:r.bemerkung}'
    )
    assert anchor in INDEX, \
        f"editMonteurEntries-Save-Anker veraendert: {anchor!r} nicht gefunden"


def test_juprowa_push_call_unchanged():
    """_juprowaPush-Aufruf ist Phase-2-sensitiv und muss UNVERAENDERT bleiben."""
    anchor = "_juprowaPush(editId).then(r=>{if(!r||(!r.ok&&r.error))console.warn"
    assert anchor in INDEX, \
        f"_juprowaPush-Aufruf veraendert: Anker {anchor!r} nicht gefunden"


def test_review_modal_callers_count():
    """Sanity: mind. 4 Aufrufer von _exportReviewModal existieren (Zeiterfassung-Pilot,
    Wochenplanung, Abwesenheit, BWB, editMonteurEntries, openMultiEntryEdit).
    """
    n = len(re.findall(r"_exportReviewModal\s*\(\s*\{", INDEX))
    assert n >= 4, f"Zu wenige Modal-Aufrufer ({n}); Aufrufer wurden versehentlich entfernt"
