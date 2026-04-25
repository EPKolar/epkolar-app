"""v3.8.55: TicketListItem braucht monteure als Prop (App-Crash-Fix)."""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'

def test_ticketlistitem_signature_has_monteure():
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'function TicketListItem\(\{([^}]+)\}\)', text)
    assert m, 'TicketListItem-Definition nicht gefunden'
    params = m.group(1)
    assert 'monteure' in params, f'monteure muss in TicketListItem-Props sein, ist aber nur: {params}'

def test_ticketlistitem_callers_pass_monteure():
    text = INDEX.read_text(encoding='utf-8')
    calls = re.findall(r"React\.createElement\(TicketListItem,\s*\{([^}]+)\}", text)
    assert len(calls) >= 1, 'Keine TicketListItem-Calls gefunden'
    for c in calls:
        assert 'monteure' in c, f'TicketListItem-Caller uebergibt monteure nicht: {c[:200]}'
