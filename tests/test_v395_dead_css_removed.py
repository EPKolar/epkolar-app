"""v3.9.5 Agent OOO: Dead-CSS-Cleanup — 5 ungenutzte Klassen entfernt,
3 aktive Klassen bleiben (Regression-Guard gegen Re-Add)."""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def _read_source() -> str:
    return INDEX.read_text(encoding='utf-8')


# -------------------- NEGATIVE: 5 dead classes MUST be gone --------------------

def test_login_container_class_gone():
    """v3.9.5 Regression: .login-container { ... } Rule darf NICHT mehr
    existieren (0 className-uses → dead-CSS entfernt)."""
    text = _read_source()
    m = re.search(r'\.login-container\s*\{', text)
    assert m is None, (
        "v3.9.5 Regression: .login-container { ... } Rule wieder aufgetaucht "
        f"(Position={m.start() if m else '?'}) — dead-CSS soll entfernt bleiben."
    )


def test_mob_table_wrap_gone():
    """v3.9.5 Regression: .mob-table-wrap { ... } Rule darf NICHT mehr
    existieren (0 className-uses → dead-CSS entfernt)."""
    text = _read_source()
    m = re.search(r'\.mob-table-wrap\s*\{', text)
    assert m is None, (
        "v3.9.5 Regression: .mob-table-wrap { ... } Rule wieder aufgetaucht "
        f"(Position={m.start() if m else '?'}) — dead-CSS soll entfernt bleiben."
    )


def test_nav_bar_class_gone():
    """v3.9.5 Regression: .nav-bar { ... } Rule darf NICHT mehr
    existieren (0 className-uses → dead-CSS entfernt)."""
    text = _read_source()
    m = re.search(r'\.nav-bar\s*\{', text)
    assert m is None, (
        "v3.9.5 Regression: .nav-bar { ... } Rule wieder aufgetaucht "
        f"(Position={m.start() if m else '?'}) — dead-CSS soll entfernt bleiben."
    )


def test_touch_btn_gone():
    """v3.9.5 Regression: .touch-btn { ... } Rule darf NICHT mehr
    existieren (0 className-uses → dead-CSS entfernt)."""
    text = _read_source()
    m = re.search(r'\.touch-btn\s*\{', text)
    assert m is None, (
        "v3.9.5 Regression: .touch-btn { ... } Rule wieder aufgetaucht "
        f"(Position={m.start() if m else '?'}) — dead-CSS soll entfernt bleiben."
    )


def test_plan_grid_gone():
    """v3.9.5 Regression: .plan-grid { ... } Rule darf NICHT mehr
    existieren (0 className-uses → dead-CSS entfernt)."""
    text = _read_source()
    m = re.search(r'\.plan-grid\s*\{', text)
    assert m is None, (
        "v3.9.5 Regression: .plan-grid { ... } Rule wieder aufgetaucht "
        f"(Position={m.start() if m else '?'}) — dead-CSS soll entfernt bleiben."
    )


# -------------------- POSITIVE: 3 alive classes MUST remain --------------------

def test_kept_alive_classes():
    """v3.9.5 Regression: .ep-spin, .tab-bar, .header-row sind aktive
    Klassen mit className-uses — müssen erhalten bleiben (sonst UI broken:
    Loading-Spinner, Tab-Leiste, Page-Header)."""
    text = _read_source()
    required = [
        (r'\.ep-spin\s*\{', '.ep-spin (Loading-Spinner)'),
        (r'\.tab-bar\s*\{', '.tab-bar (Tab-Leiste)'),
        (r'\.header-row\s*\{', '.header-row (Page-Header)'),
    ]
    missing = []
    for pat, label in required:
        if not re.search(pat, text):
            missing.append(label)
    assert not missing, (
        "v3.9.5 Regression: Aktive CSS-Klassen fehlen — "
        f"Cleanup hat zu viel entfernt: {missing}"
    )
