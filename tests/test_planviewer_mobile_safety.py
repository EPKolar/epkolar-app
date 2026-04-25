"""v3.8.57: Plan-Viewer Mobile-Touch-Smoke."""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'

def test_pinch_logic_uses_pointers_map():
    text = INDEX.read_text(encoding='utf-8')
    assert 'pointersRef' in text, 'Pinch-Zoom braucht Pointer-Map fuer Multi-Touch'
    assert '.size === 2' in text or '.size==2' in text, '2-Finger-Detection muss existieren'

def test_pinch_clamps_scale():
    text = INDEX.read_text(encoding='utf-8')
    # scale muss Math.max(0.5, Math.min(4, ...)) clamps haben
    m = re.search(r'setScale\(s\s*=>\s*Math\.max\(([\d.]+),\s*Math\.min\(([\d.]+),\s*s\s*\*\s*ratio\)', text)
    assert m, 'Pinch-Scale muss geclamp sein zwischen min und max'
    minVal, maxVal = float(m.group(1)), float(m.group(2))
    assert minVal >= 0.1 and minVal <= 1.0
    assert maxVal >= 2.0 and maxVal <= 10.0
