"""v3.8.82: Cascade-Consistency — 380er-Block-font-size MUSS kleiner als 414er-Block sein.

Vor v3.8.82 war .header-row .mob-stack button im 380px-Block mit `font-size: 11px`
größer als im 414px-Block (10px) — das verletzte die Cascade-Logik (kleineres
Endgerät → kompakteres Layout). Fix: 380er auf 9px (kleiner als 414er-10px).
Plus: KPI-Grid wird single-column auf small-Phone.
"""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def _extract_mq_block(text: str, max_width: int) -> str:
    """Extrahiert den vollständigen @media(max-width:Npx) Block (alle Vorkommen konkateniert)."""
    blocks = []
    pattern = re.compile(
        r'@media\s*\(\s*max-width\s*:\s*' + str(max_width) + r'px\s*\)\s*\{',
        re.IGNORECASE,
    )
    for m in pattern.finditer(text):
        depth = 1
        i = m.end()
        while i < len(text) and depth > 0:
            ch = text[i]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
            i += 1
        blocks.append(text[m.end():i])
    return '\n/* ──── */\n'.join(blocks)


def _font_size_for_mob_stack_button(block: str):
    """Liefert font-size (int px) für `.header-row .mob-stack button` im gegebenen Block, oder None."""
    m = re.search(
        r'\.header-row\s+\.mob-stack\s+button\s*\{[\s\S]{0,800}?font-size:\s*(\d+)px',
        block,
    )
    return int(m.group(1)) if m else None


def test_cascade_380_font_size_le_414_font_size():
    """v3.8.82: font-size im 380er-Block ≤ font-size im 414er-Block (numeric cascade)."""
    text = INDEX.read_text(encoding='utf-8')
    block_414 = _extract_mq_block(text, 414)
    block_380 = _extract_mq_block(text, 380)
    assert block_414, '@media(max-width:414px) Block muss existieren'
    assert block_380, '@media(max-width:380px) Block muss existieren'

    fs_414 = _font_size_for_mob_stack_button(block_414)
    fs_380 = _font_size_for_mob_stack_button(block_380)
    assert fs_414 is not None, (
        'v3.8.82 Cascade: `.header-row .mob-stack button { font-size: Npx ... }` '
        'muss in @media(max-width:414px) existieren.'
    )
    assert fs_380 is not None, (
        'v3.8.82 Cascade: `.header-row .mob-stack button { font-size: Npx ... }` '
        'muss in @media(max-width:380px) existieren.'
    )
    assert fs_380 <= fs_414, (
        f'v3.8.82 Cascade-Fix: font-size im 380px-Block ({fs_380}px) MUSS '
        f'kleiner-gleich 414px-Block ({fs_414}px) sein — kleineres Endgerät → '
        f'kompakteres Layout. Vor v3.8.82 war 380=11px > 414=10px (Bug).'
    )


def test_cascade_380_does_not_contain_legacy_11px_for_mob_stack_button():
    """Negativ-Guard v3.8.82: `font-size: 11px` darf in 380-Block NICHT für .header-row .mob-stack button vorkommen."""
    text = INDEX.read_text(encoding='utf-8')
    block_380 = _extract_mq_block(text, 380)
    assert block_380, '@media(max-width:380px) Block muss existieren'
    # Suche .header-row .mob-stack button { ... font-size: 11px ... }
    legacy = re.search(
        r'\.header-row\s+\.mob-stack\s+button\s*\{[\s\S]{0,800}?font-size:\s*11px',
        block_380,
    )
    assert not legacy, (
        'v3.8.82 Cascade-Regression: `.header-row .mob-stack button { font-size: 11px ... }` '
        'darf in @media(max-width:380px) NICHT vorkommen — würde Cascade-Logik brechen '
        '(414er ist 10px, also 380er muss ≤10px sein).'
    )


def test_cascade_380_kpi_grid_single_column():
    """v3.8.82: @media(max-width:380px) hat `.kpi-grid { grid-template-columns: 1fr ... }`."""
    text = INDEX.read_text(encoding='utf-8')
    block_380 = _extract_mq_block(text, 380)
    assert block_380, '@media(max-width:380px) Block muss existieren'
    assert re.search(
        r'\.kpi-grid\s*\{[^}]*grid-template-columns:\s*1fr',
        block_380,
    ), (
        'v3.8.82: `.kpi-grid { grid-template-columns: 1fr ... }` muss in '
        '@media(max-width:380px) existieren — 2-Spalten-KPIs quetschen zu '
        'schmal auf small Phone (iPhone SE/Mini).'
    )
