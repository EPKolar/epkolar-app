"""v3.8.85 Agent X: AS-Edit Polish (Time-Input + Signature-Grid) regressions."""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def test_time_input_mobile_full_width():
    """X: Mindestens 2x width:isMob?"100%":90 (Time-Input Mobile-Full-Width)."""
    text = INDEX.read_text(encoding='utf-8')
    pattern = r'width\s*:\s*isMob\s*\?\s*"100%"\s*:\s*90'
    matches = re.findall(pattern, text)
    assert len(matches) >= 2, (
        'v3.8.85 Polish-X Regression: AS-Edit Time-Input braucht mindestens '
        f'2x width:isMob?"100%":90 — gefunden: {len(matches)}.'
    )


def test_signature_grid_mobile_stack():
    """X: SignaturePad-Grid muss auf Mobile single-column stacken."""
    text = INDEX.read_text(encoding='utf-8')
    pattern = r'gridTemplateColumns\s*:\s*isMob\s*\?\s*"1fr"\s*:\s*"1fr 1fr"'
    # Verifiziere im SignaturePad-Kontext (nahes Umfeld muss SignaturePad oder
    # Signatur enthalten)
    found = False
    for m in re.finditer(pattern, text):
        window = text[max(0, m.start() - 800): m.end() + 800]
        if 'SignaturePad' in window or 'ignatur' in window:
            found = True
            break
    assert found, (
        'v3.8.85 Polish-X Regression: SignaturePad-Grid braucht '
        'gridTemplateColumns:isMob?"1fr":"1fr 1fr" (Mobile-Stack).'
    )
