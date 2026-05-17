"""v3.8.79 + v3.8.80 TOPBAR-MOBILE-HIDE: Photo/Search/User-Info auf isMob ausgeblendet.

Sebastian-Report: "header zu breit, pwa super mobile schlecht".
v3.8.80 erweiterte den Foto-Selector auf `title*="Foto"` (matched
"Foto-Warteschlange" UND "N Fotos ausstehend").
"""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def _extract_mq_block(text: str, max_width: int) -> str:
    """Extrahiert den vollständigen @media(max-width:Npx) Block (alle Vorkommen konkateniert)."""
    blocks = []
    # Toleriere @media( oder @media ( + optional whitespace
    pattern = re.compile(
        r'@media\s*\(\s*max-width\s*:\s*' + str(max_width) + r'px\s*\)\s*\{',
        re.IGNORECASE,
    )
    for m in pattern.finditer(text):
        # Brace-balance vom öffnenden { aus
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


def test_mq600_hides_header_foto_button():
    """v3.8.80: `header button[title*="Foto"]` (broader selector) hidden in @media(max-width:600px)."""
    text = INDEX.read_text(encoding='utf-8')
    block = _extract_mq_block(text, 600)
    assert block, '@media(max-width:600px) Block muss existieren'
    assert re.search(
        r'header\s+button\[title\*="Foto"\]\s*\{[^}]*display:\s*none',
        block,
    ), (
        'v3.8.80 TopBar: `header button[title*="Foto"] { display: none ... }` '
        'muss in @media(max-width:600px) existieren (broader selector — '
        'matched "Foto-Warteschlange" UND "N Fotos ausstehend").'
    )


def test_mq600_hides_header_globale_suche_button():
    """v3.8.79: `header button[title*="Globale Suche"]` hidden in @media(max-width:600px)."""
    text = INDEX.read_text(encoding='utf-8')
    block = _extract_mq_block(text, 600)
    assert block
    assert re.search(
        r'header\s+button\[title\*="Globale Suche"\]\s*\{[^}]*display:\s*none',
        block,
    ), (
        'v3.8.79 TopBar: `header button[title*="Globale Suche"] '
        '{ display: none ... }` muss in @media(max-width:600px) '
        'existieren (Cmd-K Power-User-Feature auf Mobile aus).'
    )


def test_mq600_hides_header_user_info_text_block():
    """v3.8.79: `header > div:last-child > div[style*='textAlign:"right"']` hidden."""
    text = INDEX.read_text(encoding='utf-8')
    block = _extract_mq_block(text, 600)
    assert block
    # Das Selektor-Pattern enthält escaped double-quotes: textAlign:\"right\"
    # In Python-raw-string + regex: `textAlign:\\"right\\"` matched die literal-\".
    assert re.search(
        r'header\s*>\s*div:last-child\s*>\s*div\[style\*="textAlign:\\"right\\""\][\s\S]{0,400}?display:\s*none',
        block,
    ), (
        'v3.8.79 TopBar: User-Info-Text-Block '
        '(`header > div:last-child > div[style*=\'textAlign:"right"\']`) '
        'muss in @media(max-width:600px) ausgeblendet werden '
        '(Name steht schon im Burger-Sidebar).'
    )


def test_mq414_hides_header_modus_button():
    """v3.8.79: `header button[title*="modus"]` (Theme-Toggle) hidden in @media(max-width:414px)."""
    text = INDEX.read_text(encoding='utf-8')
    block = _extract_mq_block(text, 414)
    assert block, '@media(max-width:414px) Block muss existieren'
    assert re.search(
        r'header\s+button\[title\*="modus"\]\s*\{[^}]*display:\s*none',
        block,
    ), (
        'v3.8.79 TopBar: `header button[title*="modus"] { display: none ... }` '
        'muss in @media(max-width:414px) existieren '
        '(Theme-Toggle über Settings erreichbar).'
    )
