"""v3.9.0 Sprint 11 N6: Mangel-Submit Double-Click-Guard.

Verhindert doppelte Mangel-Inserts bei schnellem Doppelklick:

* **State:** `const [submittingMangel,setSubmittingMangel]=useState(false)`.
* **Handler-Guard:** `if(submittingMangel)return;` + `setSubmittingMangel(true)`.
* **Button-Prop:** `disabled:submittingMangel` am Submit-Button.
"""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def test_submitting_mangel_state_exists():
    """v3.9.0 S11-N6: useState fuer submittingMangel muss existieren."""
    text = INDEX.read_text(encoding='utf-8')
    pattern = r'submittingMangel\s*,\s*setSubmittingMangel'
    matches = re.findall(pattern, text)
    assert len(matches) >= 1, (
        'v3.9.0 S11-N6 Regression: useState-Destructuring '
        '`[submittingMangel,setSubmittingMangel]` fehlt. '
        'Erwartet: `const [submittingMangel,setSubmittingMangel]='
        'useState(false)` — sonst kein Double-Click-Guard moeglich. '
        'Sprint 11 N6.'
    )


def test_mangel_submit_handler_has_guard():
    """v3.9.0 S11-N6: Handler muss Early-Return + State-Set haben."""
    text = INDEX.read_text(encoding='utf-8')
    # Early-Return-Guard: if(submittingMangel)return
    guard_pattern = r'if\s*\(\s*submittingMangel\s*\)\s*return'
    guard_matches = re.findall(guard_pattern, text)
    assert len(guard_matches) >= 1, (
        'v3.9.0 S11-N6 Regression: Early-Return-Guard '
        '`if(submittingMangel)return` fehlt im Submit-Handler. '
        'Ohne Guard koennen schnelle Doppelklicks 2 Mangel-Inserts '
        'erzeugen. Sprint 11 N6.'
    )
    # State-Set: setSubmittingMangel(true)
    set_pattern = r'setSubmittingMangel\(\s*true\s*\)'
    set_matches = re.findall(set_pattern, text)
    assert len(set_matches) >= 1, (
        'v3.9.0 S11-N6 Regression: `setSubmittingMangel(true)` fehlt '
        'im Submit-Handler — Guard wird sonst nie aktiv. Sprint 11 N6.'
    )


def test_mangel_submit_button_disabled_prop():
    """v3.9.0 S11-N6: Submit-Button muss disabled:submittingMangel haben."""
    text = INDEX.read_text(encoding='utf-8')
    pattern = r'disabled:\s*submittingMangel'
    matches = re.findall(pattern, text)
    assert len(matches) >= 1, (
        'v3.9.0 S11-N6 Regression: Button-Prop `disabled:submittingMangel` '
        'fehlt. Erwartet: Submit-Button mit `disabled:submittingMangel` '
        '— sonst visueller Double-Click-Hint fehlt (UX). Sprint 11 N6.'
    )
