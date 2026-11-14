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
    # v3.9.142 Fokuspunkt-Zoom: Pinch-Clamp jetzt in setZoom(z=>{const nz=Math.max(0.4,Math.min(6,z*ratio));...})
    # Maengel Stufe 2 (1): umgestellt - min ist zMinRef.current (Start 0.4). Dessen Werte kommen
    # nur aus _planEinpassen (zMin in [0.02, 0.4]) oder dem Start 0.4; beides wird hier geprueft.
    m = re.search(r'const nz\s*=\s*Math\.max\((zMinRef\.current),\s*Math\.min\(([\d.]+),\s*z\s*\*\s*ratio\)', text)
    assert m, 'Pinch-Zoom muss geclamp sein zwischen min und max'
    maxVal = float(m.group(2))
    assert maxVal >= 2.0 and maxVal <= 10.0
    s = re.search(r'const zMinRef = _react\.useRef\.call\(void 0, ([\d.]+)\);', text)
    assert s and 0.1 <= float(s.group(1)) <= 1.0
    assert 'var zMin=Math.max(0.02,Math.min(0.4,z*0.5));' in text
