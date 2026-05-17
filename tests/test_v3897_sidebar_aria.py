"""v3.8.97 Agent XX: Sidebar aria-current Accessibility.

A11y-Anforderung: Sidebar/Nav-Items muessen `aria-current="page"`
(oder vergleichbar) auf dem aktiv selektierten Eintrag tragen, damit
Screen-Reader die aktuelle Seite ansagen koennen.

Mindestens 4 `aria-current`-Occurrences erwartet (Sidebar Desktop +
Mobile-Nav + ggf. Sub-Nav-Sektionen).
"""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def test_sidebar_aria_current_count():
    """v3.8.97 XX: `aria-current` Pattern mindestens 4x im Body."""
    text = INDEX.read_text(encoding='utf-8')
    matches = re.findall(r'aria-current', text)
    assert len(matches) >= 4, (
        f'v3.8.97 Agent XX Regression: aria-current Count zu niedrig '
        f'(gefunden: {len(matches)}, erwartet >= 4). '
        'Sidebar/Nav muss aria-current="page" auf aktivem Eintrag tragen '
        '(Desktop-Sidebar + Mobile-Nav + ggf. Sub-Nav), damit '
        'Screen-Reader die aktuelle Seite ansagen. '
        'Siehe Hunt-Sprint v3.8.97 Agent XX.'
    )
