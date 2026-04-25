"""v3.8.59: tickets-Schema bleibt x/y (Pixel) — Component konvertiert beim Render."""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'

def test_no_xPct_yPct_write_to_tickets():
    text = INDEX.read_text(encoding='utf-8')
    matches = re.findall(r"_sbPatch\(\s*['\"]tickets['\"][^)]+\{([^}]+)\}", text)
    for m in matches:
        assert 'xPct' not in m, f'_sbPatch tickets darf kein xPct schreiben: {m[:100]}'
        assert 'yPct' not in m, f'_sbPatch tickets darf kein yPct schreiben: {m[:100]}'

def test_pin_render_uses_x_y():
    text = INDEX.read_text(encoding='utf-8')
    assert 't.x != null' in text or 't.x !== null' in text
