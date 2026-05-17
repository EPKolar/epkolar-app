"""v3.8.88 Agent BB-Retry: a11y-Fixes — Modal-Backdrops + Lightbox + ChefDashboard-Alert-Tiles
bekommen role="button" + tabIndex:0 + onKeyDown (Enter/Space) für Keyboard-Bedienung."""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def test_modal_backdrop_notif_has_role():
    text = INDEX.read_text(encoding='utf-8')
    # Backdrop-Div ruft setShowNotifPanel(false) und MUSS role:"button" + tabIndex:0 tragen
    m = re.search(
        r'role:\s*"button"[\s\S]{0,400}?tabIndex:\s*0[\s\S]{0,400}?setShowNotifPanel\(false\)',
        text,
    )
    if not m:
        m = re.search(
            r'setShowNotifPanel\(false\)[\s\S]{0,400}?role:\s*"button"[\s\S]{0,400}?tabIndex:\s*0',
            text,
        )
    assert m, 'v3.8.88 A11Y-1 Regression: Notif-Panel-Backdrop fehlt role="button"+tabIndex:0 nahe setShowNotifPanel(false)'


def test_modal_backdrop_photoq_has_role():
    text = INDEX.read_text(encoding='utf-8')
    # PhotoQ-Backdrop schließt via setShowPhotoQ(false) und MUSS a11y-Attribute tragen
    m = re.search(
        r'setShowPhotoQ\(false\)[\s\S]{0,400}?role:\s*"button"[\s\S]{0,400}?tabIndex:\s*0',
        text,
    )
    if not m:
        m = re.search(
            r'role:\s*"button"[\s\S]{0,400}?tabIndex:\s*0[\s\S]{0,400}?setShowPhotoQ\(false\)',
            text,
        )
    assert m, 'v3.8.88 A11Y-2 Regression: PhotoQ-Backdrop fehlt role="button"+tabIndex:0 nahe setShowPhotoQ(false)'


def test_modal_backdrop_sync_has_role():
    text = INDEX.read_text(encoding='utf-8')
    # Sync-Panel-Backdrop schließt via setShowSyncPanel(false) und MUSS a11y-Attribute tragen
    m = re.search(
        r'setShowSyncPanel\(false\)[\s\S]{0,400}?role:\s*"button"[\s\S]{0,400}?tabIndex:\s*0',
        text,
    )
    if not m:
        m = re.search(
            r'role:\s*"button"[\s\S]{0,400}?tabIndex:\s*0[\s\S]{0,400}?setShowSyncPanel\(false\)',
            text,
        )
    assert m, 'v3.8.88 A11Y-3 Regression: Sync-Panel-Backdrop fehlt role="button"+tabIndex:0 nahe setShowSyncPanel(false)'


def test_lightbox_close_has_role():
    text = INDEX.read_text(encoding='utf-8')
    # Es gibt mindestens 2 Lightbox-Backdrops (setLightbox(null) UND setLbIdx(-1)) —
    # jeder einzelne MUSS role="button"+tabIndex:0 tragen.
    m1 = re.search(
        r'setLightbox\(null\)[\s\S]{0,400}?role:\s*"button"[\s\S]{0,400}?tabIndex:\s*0',
        text,
    )
    if not m1:
        m1 = re.search(
            r'role:\s*"button"[\s\S]{0,400}?tabIndex:\s*0[\s\S]{0,400}?setLightbox\(null\)',
            text,
        )
    assert m1, 'v3.8.88 A11Y-4a Regression: Lightbox(null)-Close fehlt role="button"+tabIndex:0'

    m2 = re.search(
        r'setLbIdx\(-1\)[\s\S]{0,400}?role:\s*"button"[\s\S]{0,400}?tabIndex:\s*0',
        text,
    )
    if not m2:
        m2 = re.search(
            r'role:\s*"button"[\s\S]{0,400}?tabIndex:\s*0[\s\S]{0,400}?setLbIdx\(-1\)',
            text,
        )
    assert m2, 'v3.8.88 A11Y-4b Regression: LbIdx(-1)-Close fehlt role="button"+tabIndex:0'


def test_dashboard_clickable_tiles_have_role():
    """v3.8.88+90: KPI-Tiles und Alert-Tiles in Dashboards haben role="button" für a11y.

    Agent BB+GG haben in mehreren Sweeps Dashboard-clickable-Tiles mit role+kbd ausgestattet.
    Wir prüfen dass im Body insgesamt eine ausreichende Anzahl `role:"button"` mit `onNav(`
    Pattern existiert (Dashboard-Tiles + Sidebar-Items + Alert-Boxen).
    """
    text = INDEX.read_text(encoding='utf-8')
    # Suche `role:"button"` mit nähergelegen onNav( oder __asFilter
    role_with_nav = len(re.findall(
        r'role:\s*"button"[\s\S]{0,500}?onNav\(',
        text,
    ))
    assert role_with_nav >= 4, (
        f'v3.8.88/90 a11y Regression: <div onClick={{onNav(...)}}> Tiles benoetigen role="button" '
        f'für WCAG-Keyboard-Nav — Anzahl mit role+onNav-Proximity: {role_with_nav}'
    )
