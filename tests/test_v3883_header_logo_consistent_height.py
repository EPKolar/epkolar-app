"""v3.8.83 Quality Q-3: Header-Logo cross-Breakpoint konsistente Höhe (24px).

In v3.8.81 wurde Logo auf 26px gesetzt (Mobile @600px), aber tieferes
Breakpoint @380px nutzte 24px → inkonsistent. Q-3 vereinheitlicht auf 24px
in BEIDEN Breakpoints für vertikalen Sparplatz + visuelle Konsistenz.
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
    return '\n/* ---- */\n'.join(blocks)


def test_mq600_header_logo_height_24px():
    """v3.8.83 Q-3: `header img[alt="EP Kolar"] { height: 24px !important; }` in @media(max-width:600px)."""
    text = INDEX.read_text(encoding='utf-8')
    block = _extract_mq_block(text, 600)
    assert block, '@media(max-width:600px) Block muss existieren'
    assert re.search(
        r'header\s+img\[alt="EP Kolar"\]\s*\{[^}]*height:\s*24px\s*!important',
        block,
    ), (
        'v3.8.83 Quality Q-3 Regression: `header img[alt="EP Kolar"] '
        '{ height: 24px !important; }` muss in @media(max-width:600px) '
        'existieren (Konsistenz mit 380er-Breakpoint).'
    )


def test_no_header_logo_26px_anywhere():
    """v3.8.83 Q-3 Negativ-Guard: KEIN `header img[alt="EP Kolar"]` darf 26px nutzen (cross-Breakpoint)."""
    text = INDEX.read_text(encoding='utf-8')
    # Suche header img[alt="EP Kolar"]-Selektor mit height: 26px in seinem Body
    forbidden = re.search(
        r'header\s+img\[alt="EP Kolar"\]\s*\{[^}]*height:\s*26px',
        text,
    )
    assert not forbidden, (
        'v3.8.83 Quality Q-3 Regression: `header img[alt="EP Kolar"]` '
        'darf nirgendwo mehr height: 26px haben (cross-Breakpoint-'
        'Konsistenz auf 24px — siehe Q-3, ehemals v3.8.81 26px-Wert).'
    )
