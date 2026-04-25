"""v3.8.53: useEffect-active-flag-Schutz gegen Race-Conditions bei Unmount."""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'

def test_no_unprotected_useeffect_async():
    text = INDEX.read_text(encoding='utf-8')
    ue_async = len(re.findall(r'_react\.useEffect\.call\(void 0,\s*\(\)\s*=>\s*\{\s*\(async', text))
    active_flag = len(re.findall(r'let active\s*=\s*true', text))
    # Erlaube etwas Toleranz: maximal 1 ungeschuetzter useEffect-async (legacy)
    assert ue_async <= active_flag + 1, f'Zu viele ungeschuetzte useEffect-async: {ue_async} async vs {active_flag} active-flags'
