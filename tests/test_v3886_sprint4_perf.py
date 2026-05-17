"""v3.8.86 Sprint 4 (Agent AA): Fahrtenbuch Month-Picker Padding + Stundenzettel Set-based Dedup."""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def test_fahrtenbuch_month_padding():
    """v3.8.86 S4-N Regression: Fahrtenbuch month-picker muss isMob-padding tragen
    (10px 10px mobile / 4px 8px desktop) damit Tap-Target ≥44px erreicht wird."""
    text = INDEX.read_text(encoding='utf-8')
    pattern = r"padding:window\.innerWidth<600\?'10px 10px':'4px 8px'"
    hits = re.findall(pattern, text)
    assert len(hits) >= 1, (
        "v3.8.86 S4-N Regression: Fahrtenbuch month-picker fehlt isMob-padding "
        "(erwartet: padding:window.innerWidth<600?'10px 10px':'4px 8px')"
    )


def test_stundenzettel_dedup_set_based():
    """v3.8.86 S4-N Regression: Stundenzettel-Dedup muss Set-based laufen
    (O(n) statt O(n²) via .find(z=>z.mitarbeiterId===...))."""
    text = INDEX.read_text(encoding='utf-8')
    # Assert Set-Pattern existiert
    assert re.search(r'_seen\s*=\s*new\s+Set', text), (
        "v3.8.86 S4-N Regression: Stundenzettel-Dedup fehlt `_seen=new Set()` "
        "(Performance-Fix von O(n²).find zu O(n) Set.has/add)"
    )
    assert re.search(r'_seen\.has', text), (
        "v3.8.86 S4-N Regression: Stundenzettel-Dedup fehlt `_seen.has(...)` "
        "(Set-based membership-check)"
    )
    assert re.search(r'_seen\.add', text), (
        "v3.8.86 S4-N Regression: Stundenzettel-Dedup fehlt `_seen.add(...)` "
        "(Set-based insertion)"
    )
