"""v3.9.13: bracket-checker baseline + diagnose + pattern-order regression."""
import re
from pathlib import Path

BRACKET_CHECK = Path(__file__).parent.parent / 'scripts' / '_bracket_check.py'


def test_bracket_baseline_is_minus_one():
    text = BRACKET_CHECK.read_text(encoding='utf-8')
    m = re.search(r'Baseline\s*\(v3\.9\.12\):\s*\(\s*\)\s*-1', text)
    assert m, (
        'v3.9.13 bracket-baseline Regression: docstring muss '
        '"Baseline (v3.9.12): ( ) -1" enthalten (siehe scripts/_bracket_check.py)'
    )


def test_bracket_baseline_documented():
    text = BRACKET_CHECK.read_text(encoding='utf-8')
    m = re.search(r'NOT\s+a\s+stripper\s+artifact', text)
    assert m, (
        'v3.9.13 bracket-baseline Regression: docstring muss Diagnose '
        '"NOT a stripper artifact" enthalten (Investigations-Note 2026-05-18)'
    )


def test_pattern_order_strings_first():
    text = BRACKET_CHECK.read_text(encoding='utf-8')
    # Non-greedy `]` stoppt am ersten inneren `]` (z.B. `[^"\\]`) → greedy + anchor auf `^stripped`
    m = re.search(r'patterns\s*=\s*\[([\s\S]+?)\]\s*\nstripped', text)
    assert m, (
        'v3.9.13 bracket-baseline Regression: patterns-Liste nicht gefunden '
        'in scripts/_bracket_check.py'
    )
    body = m.group(1)
    entries = [line.strip().rstrip(',') for line in body.splitlines() if line.strip() and not line.strip().startswith('#')]
    assert len(entries) >= 3, (
        'v3.9.13 bracket-baseline Regression: erwarten >=3 pattern-eintraege, '
        f'gefunden {len(entries)}'
    )
    first_three = entries[:3]
    for idx, entry in enumerate(first_three):
        assert ('"' in entry and entry.startswith(('r"', "r'"))) or entry.startswith(('r"', "r'")), (
            f'v3.9.13 bracket-baseline Regression: pattern[{idx}] muss quote-string '
            f'sein (strings-first vor comments), gefunden: {entry!r}'
        )
    joined = ' '.join(first_three)
    assert '"' in joined and "'" in joined and '`' in joined, (
        'v3.9.13 bracket-baseline Regression: erste 3 patterns muessen '
        'double-quote + single-quote + backtick strings sein '
        '(strings-first-order kritisch fuer //-in-URLs)'
    )
