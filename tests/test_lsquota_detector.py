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
    # v3.9.439: Intervall ruft jetzt LS-Check UND IDB-Estimate-Check (storage.estimate) im selben Tick.
    text = INDEX.read_text(encoding='utf-8')
    assert "setInterval(()=>{_checkLocalStorageQuota();_checkStorageEstimate();},LS_QUOTA_CHECK_INTERVAL_MS);" in text, \
        'v3.9.439: 5-min-Timer muss _checkLocalStorageQuota() + _checkStorageEstimate() aufrufen'
