"""v3.9.6 Sprint 14 (Agent PPP): prefers-reduced-motion + _scrollLock helper."""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def test_prefers_reduced_motion_rule():
    """v3.9.6 Regression: CSS muss @media (prefers-reduced-motion: reduce) Block enthalten (WCAG 2.3.3)."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'@media\s*\(\s*prefers-reduced-motion:\s*reduce\s*\)', text)
    assert m, (
        'v3.9.6 Regression: prefers-reduced-motion media-query fehlt im CSS — '
        'a11y WCAG 2.3.3 Animation-Respect verletzt'
    )


def test_scrolllock_helper_exists():
    """v3.9.6 Regression: _scrollLock-Helper mit acquire()-Methode muss existieren."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'_scrollLock\s*=\s*\{[\s\S]{0,200}?acquire\(\)', text)
    assert m, (
        'v3.9.6 Regression: _scrollLock-Helper mit acquire()-Methode fehlt — '
        'Body-Scroll-Lock-Pattern für Modals nicht verfügbar'
    )


def test_scrolllock_release_method():
    """v3.9.6 Regression: _scrollLock muss release()-Methode enthalten (Counter-Decrement)."""
    text = INDEX.read_text(encoding='utf-8')
    # Direkt-search statt blockes-Capture (non-greedy stoppte am ersten inner `}`):
    # Pattern: `_scrollLock` Deklaration + nähergelegen `release(`-Method.
    m = re.search(
        r'_scrollLock\s*=\s*\{[\s\S]{0,800}?release\s*\(\s*\)',
        text,
    )
    assert m, (
        'v3.9.6 Regression: release()-Methode fehlt in _scrollLock-Block — '
        'Body-Overflow-Restore nach Modal-Close unmöglich'
    )
