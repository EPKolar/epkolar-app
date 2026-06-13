"""Regression-Tests fuer v3.9.350 _exportReviewModal Breite.

Sebastian-Befund: 1100px max-width zu schmal — Berichte-bearbeiten mit
Datum/Projekt/Taetigkeit/h/Bemerkung/✕ wurde rechts abgeschnitten,
H-Scroll noetig.

Fix: max-width: min(1600px, 96vw) — Desktop nutzt fast volle Breite,
mobil bleibt 96vw sicher.

NICHT angetastet:
  - Save-Logik / Singleton-Overlay-Fix (v3.9.347)
  - _resolved-Doppel-Guard
  - dbWrite-Option / textarea-Render / addRow-Button
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


def test_app_version_at_least_350():
    m = re.search(r'APP_VERSION="3\.9\.(\d+)-supabase"', INDEX)
    assert m and int(m.group(1)) >= 350


def test_sw_ver_at_least_350():
    m = re.search(r"SW_VER\s*=\s*'epkolar-v3\.9\.(\d+)'", INDEX)
    assert m and int(m.group(1)) >= 350


def test_cache_name_at_least_350():
    sw_js = (ROOT / "sw.js").read_text(encoding="utf-8")
    m = re.search(r'CACHE_NAME\s*=\s*"epkolar-v3\.9\.(\d+)"', sw_js)
    assert m and int(m.group(1)) >= 350


def test_sw_header_at_least_350():
    sw_js = (ROOT / "sw.js").read_text(encoding="utf-8")
    m = re.match(r"//\s*EP Kolar Service Worker v3\.9\.(\d+)", sw_js)
    assert m and int(m.group(1)) >= 350


def test_modal_box_max_width_increased():
    """box.style hat jetzt max-width:min(1600px,96vw)."""
    assert "max-width:min(1600px,96vw)" in INDEX, (
        "Modal-box max-width wurde nicht auf min(1600px,96vw) erhoeht"
    )


def test_modal_box_old_width_gone():
    """Alter max-width:1100px im _exportReviewModal-Block ist weg."""
    # Lokalisiere den _exportReviewModal-Block durch Window-Marker.
    start = INDEX.find("window._exportReviewModal=function(opts)")
    end = INDEX.find("window.", start + 50)
    assert start >= 0 and end > start, "_exportReviewModal-Block nicht abgrenzbar"
    block = INDEX[start:end]
    assert "max-width:1100px" not in block, (
        "Alter max-width:1100px ist noch im _exportReviewModal-Block aktiv"
    )


def test_modal_width_full_preserved():
    """width:100% bleibt im box-Style im _exportReviewModal-Block."""
    start = INDEX.find("window._exportReviewModal=function(opts)")
    end = INDEX.find("window.", start + 50)
    block = INDEX[start:end]
    assert "width:100%" in block, (
        "width:100% fehlt im _exportReviewModal-Block"
    )


def test_overlay_singleton_v347_unchanged():
    """v3.9.347 Singleton-Pattern bleibt unangetastet."""
    assert "data-epk-review-modal" in INDEX
    assert "querySelectorAll('[data-epk-review-modal]')" in INDEX or \
        'querySelectorAll("[data-epk-review-modal]")' in INDEX
    assert "_resolved" in INDEX


def test_addRow_v344_unchanged():
    """v3.9.344 addRow-Pattern bleibt aktiv."""
    assert "if(addRow){" in INDEX
    assert "Buchung hinzufügen" in INDEX


def test_dbWrite_v341_unchanged():
    """v3.9.341 dbWrite-Option bleibt."""
    assert "dbWrite" in INDEX


def test_juprowa_push_unchanged():
    """_juprowaPush HART unangetastet."""
    anchor = "_juprowaPush(editId).then(r=>{if(!r||(!r.ok&&r.error))console.warn"
    assert anchor in INDEX, "_juprowaPush-Anker veraendert"
