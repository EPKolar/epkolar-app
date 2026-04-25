"""v3.8.53: Dashboard-Reminders kompakt + Monatsabrechnung-Detail."""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'

def test_finkstats_pending_details_default():
    text = INDEX.read_text(encoding='utf-8')
    assert re.search(r'\[finkStats,setFinkStats\]=_react\.useState\.call\(void 0,\s*\{[^}]*pendingDetails\s*:\s*\[\]', text)

def test_pickerl_aggregated():
    text = INDEX.read_text(encoding='utf-8')
    assert 'if(pickerFaellig.length>0)' in text
    assert not re.search(r'pickerFaellig\.forEach\(f=>alerts\.push', text)

def test_service_aggregated():
    text = INDEX.read_text(encoding='utf-8')
    assert 'if(serviceFaellig.length>0)' in text
    assert not re.search(r'serviceFaellig\.forEach\(f=>alerts\.push', text)

def test_monatsabrechnung_has_details():
    text = INDEX.read_text(encoding='utf-8')
    block = re.search(r'finkStats\.offen>0&&isAdmin\)\{(.*?)(?=\n  [a-zA-Z])', text, re.DOTALL)
    assert block
    assert 'pendingDetails' in block.group(1)

def test_alertsExpanded_state():
    assert '[alertsExpanded,setAlertsExpanded]' in INDEX.read_text(encoding='utf-8')
