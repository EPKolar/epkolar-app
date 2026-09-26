"""v3.8.85 Agent Z: Settings Responsive (Mein Profil + Passwort) regressions."""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def test_mein_profil_grid_mobile():
    """Z: Mein-Profil-Grid muss window.innerWidth<600?"1fr":"120px 1fr" sein."""
    text = INDEX.read_text(encoding='utf-8')
    # v3.9.940: die Schwelle heisst jetzt BP_MOB statt der nackten 600. Der
    # Riegel prueft weiterhin GENAU DASSELBE - "1fr" auf dem Handy, "120px 1fr"
    # darueber. Nur die ZIFFERN der Schwelle sind zur Schreibweise geworden,
    # und die war nie die geschuetzte Eigenschaft. Dass BP_MOB gleich 600 ist,
    # haelt tests/test_mobil_fundament_v932.py fest (`const BP_MOB=600;`,
    # genau einmal) - ohne diesen Nachweis waere die Lockerung unzulaessig.
    pattern = (
        r'window\.innerWidth\s*<\s*(?:600|BP_MOB)\s*\?\s*"1fr"\s*:\s*"120px 1fr"'
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
