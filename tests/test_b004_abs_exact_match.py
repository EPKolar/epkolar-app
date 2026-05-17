"""v3.8.74 Hunt B-004: abs-Lookup verwendet exact-match statt startsWith."""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'


def test_abs_lookup_uses_exact_key_match():
    """Positiv: Object.entries(abs).find(([k])=>k===_absKey) muss existieren."""
    text = INDEX.read_text(encoding='utf-8')
    # Akzeptiere k===_absKey oder k===... (exact match auf den vorberechneten Key)
    pattern = r'Object\.entries\(abs\)\.find\(\(\[k\]\)=>k===_absKey\)'
    assert re.search(pattern, text), \
        'v3.8.74 Hunt B-004 Regression: abs-Lookup exact-match (k===_absKey) fehlt'


def test_abs_lookup_no_startsWith_regression():
    """Negativ-Guard: alte startsWith(m.n+"_"+td2()) Variante darf NICHT zurückkehren."""
    text = INDEX.read_text(encoding='utf-8')
    # Alte Variante: Object.entries(abs).find(([k,v])=>k.startsWith(m.n+"_"+td2()))
    bad_pattern = r'Object\.entries\(abs\)\.find\(\(\[k,v\]\)=>k\.startsWith\(m\.n\+"_"\+td2\(\)\)\)'
    assert not re.search(bad_pattern, text), \
        'v3.8.74 Hunt B-004 Regression: alte startsWith(m.n+"_"+td2()) Variante zurückgekehrt — ' \
        'muss exact-match (k===_absKey) sein'
