"""v3.8.84 Agent T: VBueroExport Selector Mobile-Width regression."""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def test_selector_mobile_minwidth():
    """T: Selector-Area (L6765) muss minWidth:isMob?120:200 sein."""
    text = INDEX.read_text(encoding='utf-8')
    pattern = r'minWidth\s*:\s*isMob\s*\?\s*120\s*:\s*200'
    assert re.search(pattern, text), (
        'v3.8.84 T Regression: VBueroExport-Selector braucht '
        'minWidth:isMob?120:200 (Mobile-Layout, L6765 area).'
    )
