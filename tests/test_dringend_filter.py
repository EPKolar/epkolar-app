"""v3.8.55: Dringend-Filter präzisiert + Status-Underscore-Match."""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'

def test_AS_GRP_OFFEN_includes_underscore_variant():
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'AS_GRP_OFFEN\s*=\s*\[([^\]]+)\]', text)
    assert m
    body = m.group(1)
    assert 'in_bearbeitung' in body, 'AS_GRP_OFFEN muss in_bearbeitung-Variante enthalten (DB-Schema)'

def test_dringend_filter_uses_priority_or_termin():
    text = INDEX.read_text(encoding='utf-8')
    # v3.8.70: dringendeAS wurde in useMemo-Wrap gepackt — Regex akzeptiert beide Formen
    m = re.search(r'const dringendeAS\s*=\s*(?:_react\.useMemo\.call\(void 0,\s*\(\)\s*=>\s*)?arbeitsscheine\.filter\(([\s\S]{0,800}?)\)\.length', text)
    assert m
    body = m.group(1)
    assert 'prioritaet' in body or 'prio' in body.lower(), 'Dringend-Filter muss Prio prüfen'
    assert '_todayStr' in body or 'termin' in body.lower(), 'Dringend-Filter muss Termin oder Datum prüfen'

def test_dringend_count_below_total():
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'const dringendeAS\s*=', text)
    assert m, 'dringendeAS muss existieren'
