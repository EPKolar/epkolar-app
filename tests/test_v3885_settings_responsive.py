"""v3.8.85 Agent Z: Settings Responsive (Mein Profil + Passwort) regressions."""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def test_mein_profil_grid_mobile():
    """Z: Mein-Profil-Grid muss window.innerWidth<600?"1fr":"120px 1fr" sein."""
    text = INDEX.read_text(encoding='utf-8')
    pattern = (
        r'window\.innerWidth\s*<\s*600\s*\?\s*"1fr"\s*:\s*"120px 1fr"'
    )
    assert re.search(pattern, text), (
        'v3.8.85 Polish-Z Regression: Mein-Profil-Grid braucht '
        'window.innerWidth<600?"1fr":"120px 1fr" (Mobile-Stack).'
    )


def test_passwort_form_mobile_full():
    """Z: Passwort-Form-maxWidth muss window.innerWidth<400?"100%":320 sein."""
    text = INDEX.read_text(encoding='utf-8')
    pattern = (
        r'maxWidth\s*:\s*window\.innerWidth\s*<\s*400\s*\?\s*"100%"\s*:\s*320'
    )
    assert re.search(pattern, text), (
        'v3.8.85 Polish-Z Regression: Passwort-Form braucht '
        'maxWidth:window.innerWidth<400?"100%":320 (Mobile-Full).'
    )
