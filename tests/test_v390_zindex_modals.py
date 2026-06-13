"""v3.9.0 Sprint 11 N3+N5: Z-Index-Hygiene Backdrop/Panel/Lightbox.

Sicherstellt, dass Modal-Layer in korrekter Stacking-Order liegen:

* **NotifPanel:** Panel `zIndex:200`, Backdrop `zIndex:199` (UNTER dem Panel — v3.9.123:
  Gleichstand + Backdrop später im DOM legte den Backdrop ÜBER die Einträge und schluckte
  alle Klicks; die alte ==-Invariante war das Antimuster).
* **PhotoQ:** Panel `zIndex:300`, Backdrop `zIndex:299` (v3.9.124 defensiv).
* **Voice-Modal:** Backdrop `zIndex:1500` + Panel `zIndex:1501` < Lightbox 2000
  (Lightbox-Priority, S11-N5).
* **Lightbox:** `zIndex:2000` (Top-Layer, S11-N5).
"""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def test_notif_backdrop_zindex_matches_panel():
    """v3.9.123: NotifPanel Panel=200, Backdrop=199 (Backdrop UNTER Panel)."""
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
    # v3.9.123: Backdrop MUSS UNTER dem Panel liegen (199 < 200) — Gleichstand schluckte Klicks.
    backdrop_matches = re.findall(
        r'setShowNotifPanel\(false\)[\s\S]{0,400}?zIndex:199',
        text,
    )
    assert len(backdrop_matches) >= 1, (
        'v3.9.123 Regression: NotifPanel-Backdrop muss zIndex:199 haben (UNTER dem Panel 200). '
        'Backdrop==Panel + spaetere DOM-Position legte den Backdrop UEBER die Eintraege -> '
        'alle Klicks wurden geschluckt (Sebastian-Bug 04.06.2026).'
    )


def test_photoq_backdrop_zindex_matches_panel():
    """v3.9.124: PhotoQ Panel=300, Backdrop=299 (Backdrop UNTER Panel)."""
    text = INDEX.read_text(encoding='utf-8')
    # Backdrop: onClick=setShowPhotoQ(false) + zIndex:300
    backdrop_matches = re.findall(
        r'setShowPhotoQ\(false\)[\s\S]{0,400}?zIndex:299',
        text,
    )
    assert len(backdrop_matches) >= 1, (
        'v3.9.124 Regression: PhotoQ-Backdrop muss zIndex:299 haben (UNTER dem Panel 300, '
        'defensiv gegen das Glocken-Antimuster).'
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
    """v3.9.346: Voice-Modal komplett entfernt — Scheine kommen IMMER aus OFFA, kein
    UI-Anlege-Einstieg (Voice-Button + Modal) mehr. Frueher (v3.9.0 S11-N5): Voice-Modal
    (1500/1501) < Lightbox (2000). Test pruefte Z-Index-Hygiene; jetzt: Voice-Modal-Code
    darf NICHT mehr im Render existieren (Negativ-Assert)."""
    text = INDEX.read_text(encoding='utf-8')
    # Voice-Backdrop darf NICHT mehr existieren (Modal entfernt)
    voice_backdrop = re.findall(
        r'voiceStop\(\);\s*setShowVoice\(false\)',
        text,
    )
    assert len(voice_backdrop) == 0, (
        'v3.9.346 Regression: Voice-Modal-Anker (voiceStop+setShowVoice(false)) '
        'darf NICHT mehr existieren — Voice-Anlege-Pfad ist entfernt.'
    )
    # showVoice State-Setter darf nicht mehr im Render-Code stehen (Modal raus)
    show_voice_matches = re.findall(r'showVoice', text)
    assert len(show_voice_matches) == 0, (
        'v3.9.346 Regression: showVoice-State (Voice-Modal) muss komplett entfernt sein. '
        f'Gefunden: {len(show_voice_matches)} Vorkommen.'
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
