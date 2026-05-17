"""v3.8.72 Hunt B-010: Alerts-Expanded-Lookup über Composite-Key statt Array-Index.

Array-Indizes kollidieren wenn Alerts dynamisch hinzukommen/wegfallen; deshalb
wird der Alert über einen stabilen `_alertKey(a)` = icon+'|'+text identifiziert.
"""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'


def test_alertKey_helper_exists():
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'_alertKey\s*=\s*\(a\)\s*=>', text)
    assert m, (
        'v3.8.72 Hunt B-010 Regression: _alertKey=(a)=> Helper fehlt — '
        'Alerts-Expanded-State würde wieder über Array-Index identifiziert (instabil).'
    )


def test_alertKey_lookup_uses_composite_key():
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(
        r'alerts\.find\(\s*a\s*=>\s*_alertKey\(a\)\s*===\s*alertsExpanded\s*\)',
        text,
    )
    assert m, (
        'v3.8.72 Hunt B-010 Regression: alerts.find(a=>_alertKey(a)===alertsExpanded) '
        'Composite-Key-Lookup fehlt — Expand-Panel zeigt ggf. falschen Alert.'
    )
