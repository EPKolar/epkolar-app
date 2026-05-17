"""v3.8.92: AS-Status-Transitions Map + Legal-Transition-Guards Regression."""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'

AS_STATUS_KEYS = [
    'aufgenommen',
    'freigegeben',
    'in_bearbeitung',
    'aufgeschoben',
    'erledigt',
    'abgerechnet',
    'bar_bezahlt',
    'storniert',
]


def test_as_transitions_map_defined():
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'const\s+AS_TRANSITIONS\s*=\s*\{([\s\S]*?)\}\s*;', text)
    assert m, 'v3.8.92 AS-Trans-1 Regression: const AS_TRANSITIONS={...} Map fehlt'
    body = m.group(1)
    for key in AS_STATUS_KEYS:
        assert re.search(r'\b' + re.escape(key) + r'\s*:', body), (
            f'v3.8.92 AS-Trans-1 Regression: AS_TRANSITIONS Key "{key}" fehlt'
        )


def test_as_transitions_final_states_empty():
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'const\s+AS_TRANSITIONS\s*=\s*\{([\s\S]*?)\}\s*;', text)
    assert m, 'v3.8.92 AS-Trans-2 Regression: AS_TRANSITIONS Map nicht gefunden'
    body = m.group(1)
    for final_state in ['abgerechnet', 'bar_bezahlt', 'storniert']:
        assert re.search(re.escape(final_state) + r'\s*:\s*\[\s*\]', body), (
            f'v3.8.92 AS-Trans-2 Regression: Endstate "{final_state}" muss leeres Array haben'
        )


def test_isLegalAsTransition_helper_defined():
    text = INDEX.read_text(encoding='utf-8')
    pattern = r'(?:const|let|var|function)\s+_isLegalAsTransition\b'
    assert re.search(pattern, text), (
        'v3.8.92 AS-Trans-3 Regression: _isLegalAsTransition Helper-Funktion fehlt'
    )


def test_at_least_3_guards_in_source():
    text = INDEX.read_text(encoding='utf-8')
    # Pattern `_isLegalAsTransition(` zählt NUR call-sites (Definition als arrow-fn
    # `const X = (from,to)=>` hat KEIN `(` direkt nach Namen, daher kein false-positive).
    call_sites = re.findall(r'_isLegalAsTransition\s*\(', text)
    assert len(call_sites) >= 3, (
        f'v3.8.92 AS-Trans-4 Regression: mindestens 3 Status-Update-Guards '
        f'mit _isLegalAsTransition(...) erwartet (swipe L5560, dropdown L6143, form L6380), '
        f'gefunden: {len(call_sites)}'
    )
