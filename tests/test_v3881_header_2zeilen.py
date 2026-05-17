"""v3.8.81: Header in 2 Zeilen auf Mobile.

Sebastian-Wunsch "header besser machen oder 2 zeilen für mobile":
Zeile 1 = Logo + Branding · Zeile 2 = Sync+Bell+Logout (rechtsbündig).
Logo-Image auf 26px verkleinert (von 32px) für vertikalen Sparplatz.
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


def test_mq600_header_flex_direction_column():
    """v3.8.81: `header { flex-direction: column !important; ... }` in @media(max-width:600px)."""
    text = INDEX.read_text(encoding='utf-8')
    block = _extract_mq_block(text, 600)
    assert block, '@media(max-width:600px) Block muss existieren'
    # Suche header { ... flex-direction: column !important; ... }
    # Block kann andere Properties enthalten — non-greedy [\s\S]{0,400}?
    assert re.search(
        r'(?:^|[^.\w-])header\s*\{[\s\S]{0,400}?flex-direction:\s*column\s*!important',
        block,
    ), (
        'v3.8.81 Header-2-Zeilen: `header { flex-direction: column !important; ... }` '
        'muss in @media(max-width:600px) existieren — Zeile 1 Logo, Zeile 2 Button-Cluster.'
    )


def test_mq600_header_logo_height_26px():
    """v3.8.81: `header img[alt="EP Kolar"] { height: 26px !important; }` in @media(max-width:600px)."""
    text = INDEX.read_text(encoding='utf-8')
    block = _extract_mq_block(text, 600)
    assert block
    assert re.search(
        r'header\s+img\[alt="EP Kolar"\]\s*\{[^}]*height:\s*26px\s*!important',
        block,
    ), (
        'v3.8.81 Header-2-Zeilen: `header img[alt="EP Kolar"] { height: 26px !important; }` '
        'muss in @media(max-width:600px) existieren (Logo 32→26px für vertikalen Sparplatz).'
    )
