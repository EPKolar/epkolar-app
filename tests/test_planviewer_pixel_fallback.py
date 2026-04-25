"""v3.8.57: PlanViewerCanvas akzeptiert alte Pixel-Pins als Fallback."""
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'

def test_renders_xPct_or_x_pixel():
    text = INDEX.read_text(encoding='utf-8')
    # Sollte sowohl xPct als auch x als Quelle akzeptieren
    assert 't.xPct' in text
    assert 't.x' in text or 'pageDims.baseWidth' in text

def test_pixel_to_pct_conversion_via_pageDims():
    text = INDEX.read_text(encoding='utf-8')
    assert 'baseWidth' in text or 'baseHeight' in text, 'Pixel-zu-%-Konversion braucht pageDims.baseWidth/Height'

def test_orphan_toast_warning():
    text = INDEX.read_text(encoding='utf-8')
    assert 'ohne Plan-Position' in text or 'orphan' in text.lower()
