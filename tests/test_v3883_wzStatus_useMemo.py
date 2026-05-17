"""v3.8.83 Quality Q-1: wzStatus useMemo-Wrap.

Re-Render-Sparplatz: wzStatus (Object.entries(WZ_STATUS).map über werkzeuge)
muss in _react.useMemo gewrappt sein — Deps [werkzeuge] —
sonst neu-allocation pro Render in AuswertungView.
"""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def test_wzStatus_useMemo_wrap():
    """v3.8.83 Q-1: `const wzStatus=_react.useMemo.call(void 0, ()=>Object.entries(WZ_STATUS).map(...),[werkzeuge])`."""
    text = INDEX.read_text(encoding='utf-8')
    pattern = (
        r'const wzStatus=_react\.useMemo\.call\(void 0,\s*\(\)=>'
        r'Object\.entries\(WZ_STATUS\)\.map\('
        r'[\s\S]{0,200}?\),\[werkzeuge\]\)'
    )
    m = re.search(pattern, text)
    assert m, (
        'v3.8.83 Quality Q-1 Regression: wzStatus useMemo-Wrap fehlt. '
        'Erwartet: `const wzStatus=_react.useMemo.call(void 0, ()=>'
        'Object.entries(WZ_STATUS).map(...),[werkzeuge])` — sonst '
        'Re-Allocation pro AuswertungView-Render.'
    )


def test_wzStatus_no_unwrapped_form():
    """v3.8.83 Q-1 Negativ-Guard: Alte Form ohne useMemo darf nicht alleine vorhanden sein."""
    text = INDEX.read_text(encoding='utf-8')
    # Suche: `const wzStatus=Object.entries(...)` direkt ohne _react.useMemo davor
    unwrapped = re.search(
        r'const wzStatus=Object\.entries\(WZ_STATUS\)\.map',
        text,
    )
    assert not unwrapped, (
        'v3.8.83 Quality Q-1 Regression: Alte unwrapped Form '
        '`const wzStatus=Object.entries(WZ_STATUS).map(...)` darf NICHT '
        'mehr existieren (muss in useMemo gewrappt sein — siehe Q-1).'
    )
