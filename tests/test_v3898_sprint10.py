"""v3.8.98 Sprint 10-N: Notification-Permission-Cache + Swipe-Mouse-Fallback Regression."""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
INDEX = ROOT / 'index.html'
SW = ROOT / 'sw.js'


def _read_sources():
    parts = []
    if INDEX.exists():
        parts.append(INDEX.read_text(encoding='utf-8'))
    if SW.exists():
        parts.append(SW.read_text(encoding='utf-8'))
    return '\n'.join(parts)


def test_notification_request_permission_state_cached():
    text = _read_sources()
    m = re.search(r'_p\.then\(perm=>\{window\._cachedNotifPerm=perm', text)
    assert m, (
        'v3.8.98 S10-N Regression: Notification.requestPermission() muss '
        'das Ergebnis in window._cachedNotifPerm cachen '
        '(Pattern `_p.then(perm=>{window._cachedNotifPerm=perm` fehlt).'
    )


def test_notification_permission_cache_check():
    text = _read_sources()
    m = re.search(r'window\._cachedNotifPerm\|\|Notification\.permission', text)
    assert m, (
        'v3.8.98 S10-N Regression: Permission-Check muss zuerst den Cache '
        'lesen (Pattern `window._cachedNotifPerm||Notification.permission` '
        'fehlt) — sonst triggert iOS-Safari erneute Prompts.'
    )


def test_swipe_mouse_fallback():
    text = _read_sources()
    m = re.search(r'e\.type[\s\S]{0,40}?startsWith\("mouse"\)', text)
    assert m, (
        'v3.8.98 S10-N Regression: Swipe-End-Handler muss Maus-Events als '
        'Fallback erkennen (Pattern `e.type … startsWith("mouse")` fehlt) — '
        'sonst funktioniert Swipe-Back nicht auf Desktop.'
    )
