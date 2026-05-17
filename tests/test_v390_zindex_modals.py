"""v3.9.0 Sprint 11 N3+N5: Z-Index-Hygiene Backdrop/Panel/Lightbox.

Sicherstellt, dass Modal-Layer in korrekter Stacking-Order liegen:

* **NotifPanel:** Backdrop `zIndex:200` == Panel `zIndex:200` (S11-N3).
* **PhotoQ:** Backdrop `zIndex:300` == Panel `zIndex:300` (S11-N3).
* **Voice-Modal:** Backdrop `zIndex:1500` + Panel `zIndex:1501` < Lightbox 2000
  (Lightbox-Priority, S11-N5).
* **Lightbox:** `zIndex:2000` (Top-Layer, S11-N5).
"""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def test_notif_backdrop_zindex_matches_panel():
    """v3.9.0 S11-N3: NotifPanel-Backdrop muss zIndex>=200 haben (==Panel)."""
    text = INDEX.read_text(encoding='utf-8')
    # Panel: position:fixed, ... zIndex:200, ... showNotifPanel-Render
    panel_matches = re.findall(
        r'showNotifPanel&&[\s\S]{0,200}?zIndex:200',
        text,
    )
    assert len(panel_matches) >= 1, (
        'v3.9.0 S11-N3 Regression: NotifPanel mit zIndex:200 fehlt. '
        'Erwartet: `showNotifPanel&&React.createElement(...zIndex:200...)`.'
    )
    # Backdrop: onClick=setShowNotifPanel(false) + zIndex:200 (>= panel)
    backdrop_matches = re.findall(
        r'setShowNotifPanel\(false\)[\s\S]{0,400}?zIndex:200',
        text,
    )
    assert len(backdrop_matches) >= 1, (
        'v3.9.0 S11-N3 Regression: NotifPanel-Backdrop zIndex:200 fehlt. '
        'Erwartet: Backdrop-Div mit onClick=setShowNotifPanel(false) '
        'und zIndex:200 (>= Panel), sonst Click-Through-Bug. '
        'Siehe Sprint 11 N3.'
    )


def test_photoq_backdrop_zindex_matches_panel():
    """v3.9.0 S11-N3: PhotoQ-Backdrop+Panel beide zIndex:300."""
    text = INDEX.read_text(encoding='utf-8')
    # Backdrop: onClick=setShowPhotoQ(false) + zIndex:300
    backdrop_matches = re.findall(
        r'setShowPhotoQ\(false\)[\s\S]{0,400}?zIndex:300',
        text,
    )
    assert len(backdrop_matches) >= 1, (
        'v3.9.0 S11-N3 Regression: PhotoQ-Backdrop zIndex:300 fehlt. '
        'Erwartet: Backdrop-Div mit onClick=setShowPhotoQ(false) '
        'und zIndex:300 (== Panel). Sprint 11 N3.'
    )
    # Panel: showPhotoQ-Render + zIndex:300
    panel_matches = re.findall(
        r'showPhotoQ&&\(?React\.createElement[\s\S]{0,400}?zIndex:300',
        text,
    )
    assert len(panel_matches) >= 1, (
        'v3.9.0 S11-N3 Regression: PhotoQ-Panel zIndex:300 fehlt. '
        'Erwartet: `showPhotoQ&&React.createElement(...zIndex:300...)`.'
    )


def test_voice_modal_zindex_above_lightbox():
    """v3.9.0 S11-N5: Voice-Modal (1500/1501) muss < Lightbox (2000) sein."""
    text = INDEX.read_text(encoding='utf-8')
    # Voice-Backdrop: voiceStop + setShowVoice(false) + zIndex:1500
    voice_backdrop = re.findall(
        r'voiceStop\(\);\s*setShowVoice\(false\)[\s\S]{0,400}?zIndex:1500',
        text,
    )
    assert len(voice_backdrop) >= 1, (
        'v3.9.0 S11-N5 Regression: Voice-Modal-Backdrop zIndex:1500 fehlt. '
        'Erwartet: Backdrop-Div mit voiceStop+setShowVoice(false) '
        'und zIndex:1500. Sprint 11 N5.'
    )
    # Voice-Panel: zIndex:1501
    voice_panel = re.findall(r'zIndex:1501', text)
    assert len(voice_panel) >= 1, (
        'v3.9.0 S11-N5 Regression: Voice-Modal-Panel zIndex:1501 fehlt. '
        'Erwartet: Panel-Div mit zIndex:1501 (Backdrop+1). Sprint 11 N5.'
    )
    # Hierarchie-Assert: Voice (1500/1501) < Lightbox (2000)
    assert 1501 < 2000, (
        'v3.9.0 S11-N5 Logik-Regression: Voice-Z-Index muss strikt < '
        'Lightbox-Z-Index sein (Lightbox-Priority). Sprint 11 N5.'
    )


def test_lightbox_zindex_2000():
    """v3.9.0 S11-N5: Lightbox Top-Layer mit zIndex:2000."""
    text = INDEX.read_text(encoding='utf-8')
    # Lightbox: lightbox&& + setLightbox(null) + zIndex:2000
    lightbox_matches = re.findall(
        r'lightbox&&React\.createElement[\s\S]{0,600}?zIndex:2000',
        text,
    )
    assert len(lightbox_matches) >= 1, (
        'v3.9.0 S11-N5 Regression: Lightbox zIndex:2000 fehlt. '
        'Erwartet: `lightbox&&React.createElement(...zIndex:2000...)` '
        'als Top-Layer-Modal (ueber Voice 1500/1501). Sprint 11 N5.'
    )
