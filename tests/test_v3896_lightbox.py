"""v3.8.96 Agent WW: Lightbox useMemo/useCallback-Wraps.

Re-Render-Sparplatz fuer Photo-Lightbox (VFotosView):

* **lbPhoto:** aktuelles Foto-Lookup — Deps [lbIdx, filtered].
* **lbPrev:** Prev-Handler — useCallback.
* **lbNext:** Next-Handler — useCallback.
"""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def test_lightbox_lbphoto_usememo():
    """v3.8.96 WW: `lbPhoto=_react.useMemo(..., [lbIdx, filtered])`."""
    text = INDEX.read_text(encoding='utf-8')
    pattern = (
        r'lbPhoto=_react\.useMemo[\s\S]{0,400}?\[lbIdx,\s*filtered\]\)'
    )
    matches = re.findall(pattern, text)
    assert len(matches) >= 1, (
        'v3.8.96 Agent WW Regression: Lightbox lbPhoto useMemo-Wrap fehlt. '
        'Erwartet: `lbPhoto=_react.useMemo(...,[lbIdx, filtered])` in '
        'VFotosView-Lightbox — sonst Photo-Lookup pro Render neu. '
        'Siehe Hunt-Sprint v3.8.96 Agent WW.'
    )


def test_lightbox_lbprev_usecallback():
    """v3.8.96 WW: `lbPrev=_react.useCallback(...)`."""
    text = INDEX.read_text(encoding='utf-8')
    pattern = r'lbPrev=_react\.useCallback'
    matches = re.findall(pattern, text)
    assert len(matches) >= 1, (
        'v3.8.96 Agent WW Regression: Lightbox lbPrev useCallback-Wrap fehlt. '
        'Erwartet: `lbPrev=_react.useCallback(...)` in VFotosView-Lightbox — '
        'sonst Prev-Handler pro Render neu allokiert. '
        'Siehe Hunt-Sprint v3.8.96 Agent WW.'
    )


def test_lightbox_lbnext_usecallback():
    """v3.8.96 WW: `lbNext=_react.useCallback(...)`."""
    text = INDEX.read_text(encoding='utf-8')
    pattern = r'lbNext=_react\.useCallback'
    matches = re.findall(pattern, text)
    assert len(matches) >= 1, (
        'v3.8.96 Agent WW Regression: Lightbox lbNext useCallback-Wrap fehlt. '
        'Erwartet: `lbNext=_react.useCallback(...)` in VFotosView-Lightbox — '
        'sonst Next-Handler pro Render neu allokiert. '
        'Siehe Hunt-Sprint v3.8.96 Agent WW.'
    )
