"""v3.8.78 Hunt B-022: Urlaubskontingent Save — ID-Lookup ZUERST, Name-Fallback nur bei Legacy-Daten.

Verhindert Namens-Kollisionen wie "Hans" → "Hans Mueller". Der Fix muss `m.id===worker`
als ersten Treffer-Versuch nutzen und nur dann auf `m.n===worker` (Name) zurückfallen.
"""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def test_kontingent_save_uses_id_first_then_name_fallback():
    """v3.8.78 B-022: Kontingent-Save-Closure muss ID-First-Lookup haben."""
    text = INDEX.read_text(encoding='utf-8')
    # Pattern: monteure.find(m=>m.id===worker)||monteure.find(m=>m.n===worker)
    # Toleriere optional whitespace; akzeptiere ===/== und Quoting-Varianten.
    m = re.search(
        r'monteure\.find\(\s*m\s*=>\s*m\.id\s*===?\s*worker\s*\)'
        r'\s*\|\|\s*'
        r'monteure\.find\(\s*m\s*=>\s*m\.n\s*===?\s*worker\s*\)',
        text,
    )
    assert m, (
        'v3.8.78 Hunt B-022: Kontingent-Save muss '
        '`monteure.find(m=>m.id===worker)||monteure.find(m=>m.n===worker)` '
        'verwenden (ID-First, Name-Fallback). Verhindert Namens-Kollision '
        '"Hans" → "Hans Mueller".'
    )


def test_kontingent_save_does_not_use_legacy_name_only_lookup():
    """Negativ-Guard v3.8.78 B-022: Alte Name-only-Form darf nicht alleine stehen."""
    text = INDEX.read_text(encoding='utf-8')
    # Suche das alte Pattern: monteure.find(m=>m.n===worker);const wid=mon?mon.id:worker
    # OHNE vorangestelltes ID-Lookup (||-Operator).
    # Wenn das Pattern existiert, muss es Teil eines ID-First-||-Konstrukts sein.
    legacy_pattern = re.compile(
        r'monteure\.find\(\s*m\s*=>\s*m\.n\s*===?\s*worker\s*\)\s*;\s*'
        r'const\s+wid\s*=\s*mon\s*\?\s*mon\.id\s*:\s*worker'
    )
    for hit in legacy_pattern.finditer(text):
        # Look backwards up to 300 chars for the ID-First-|| context.
        start = max(0, hit.start() - 300)
        prefix = text[start:hit.start()]
        assert re.search(
            r'monteure\.find\(\s*m\s*=>\s*m\.id\s*===?\s*worker\s*\)\s*\|\|\s*$',
            prefix,
        ), (
            'v3.8.78 Hunt B-022 Regression: Legacy Name-only-Lookup '
            '`monteure.find(m=>m.n===worker);const wid=mon?mon.id:worker` '
            'darf NICHT ohne vorangestellten ID-First-Lookup '
            '`monteure.find(m=>m.id===worker)||` existieren.'
        )
