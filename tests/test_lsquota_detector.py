"""v3.8.54: localStorage-Quota-Detector"""
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'

def test_lsquota_function_exists():
    assert 'function _checkLocalStorageQuota' in INDEX.read_text(encoding='utf-8')

def test_lsquota_uses_window_toast():
    text = INDEX.read_text(encoding='utf-8')
    assert "window.__toast(" in text  # general check
    import re
    m = re.search(r'function _checkLocalStorageQuota\(\).*?\n\}', text, re.DOTALL)
    assert m
    assert 'window.__toast' in m.group(0)

def test_lsquota_interval_registered():
    assert 'setInterval(_checkLocalStorageQuota' in INDEX.read_text(encoding='utf-8')
