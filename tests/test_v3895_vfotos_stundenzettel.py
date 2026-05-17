"""v3.8.95 Agent UU: VFotos & Stundenzettel useMemo/useCallback-Wraps.

Re-Render-Sparplatz fuer VFotosView und StundenzettelView:

* **VFotos filtered:** Photo-Filter — Deps [photos, filter].
* **VFotos visibleCats:** Kategorie-Aggregation — Deps [photos].
* **Stundenzettel meineZettel:** Personal-Filter — Deps incl. zettel.
* **Stundenzettel filtered:** Listenfilter — useMemo.
* **Stundenzettel sumHours:** Stunden-Aggregator — useCallback.
"""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def test_vfotos_filtered_usememo():
    """v3.8.95 UU: VFotos `filtered=_react.useMemo(..., [photos, filter])`."""
    text = INDEX.read_text(encoding='utf-8')
    pattern = r'filtered=_react\.useMemo[\s\S]{0,600}?\[photos,\s*filter\]\)'
    matches = re.findall(pattern, text)
    assert len(matches) >= 1, (
        'v3.8.95 Agent UU Regression: VFotos filtered useMemo-Wrap fehlt. '
        'Erwartet: `filtered=_react.useMemo(...,[photos,filter])` in VFotosView — '
        'sonst Photo-Filter-Re-Run pro Render. Siehe Hunt-Sprint v3.8.95 Agent UU.'
    )


def test_vfotos_visiblecats_usememo():
    """v3.8.95 UU: VFotos `_visibleCats=_react.useMemo(..., [photos])`."""
    text = INDEX.read_text(encoding='utf-8')
    pattern = r'_visibleCats=_react\.useMemo[\s\S]{0,600}?\[photos\]\)'
    matches = re.findall(pattern, text)
    assert len(matches) >= 1, (
        'v3.8.95 Agent UU Regression: VFotos visibleCats useMemo-Wrap fehlt. '
        'Erwartet: `_visibleCats=_react.useMemo(...,[photos])` in VFotosView — '
        'sonst Kategorie-Aggregation pro Render neu. '
        'Siehe Hunt-Sprint v3.8.95 Agent UU.'
    )


def test_stundenzettel_meinezettel_usememo():
    """v3.8.95 UU: Stundenzettel `meineZettel=_react.useMemo(..., [...,zettel,...])`."""
    text = INDEX.read_text(encoding='utf-8')
    # Pattern: meineZettel=_react.useMemo(...,[deps incl. zettel])
    pattern = r'meineZettel=_react\.useMemo[\s\S]{0,600}?\[[^\]]*zettel[^\]]*\]\)'
    matches = re.findall(pattern, text)
    assert len(matches) >= 1, (
        'v3.8.95 Agent UU Regression: Stundenzettel meineZettel useMemo-Wrap fehlt. '
        'Erwartet: `meineZettel=_react.useMemo(...,[...,zettel,...])` in '
        'StundenzettelView — Deps muessen `zettel` enthalten. '
        'Siehe Hunt-Sprint v3.8.95 Agent UU.'
    )


def test_stundenzettel_filtered_usememo():
    """v3.8.95 UU: Stundenzettel `filtered=_react.useMemo(...)` (context-frei)."""
    text = INDEX.read_text(encoding='utf-8')
    # filtered=_react.useMemo kommt evtl. mehrfach vor (VFotos + Stundenzettel)
    pattern = r'filtered=_react\.useMemo'
    matches = re.findall(pattern, text)
    assert len(matches) >= 1, (
        'v3.8.95 Agent UU Regression: Stundenzettel filtered useMemo-Wrap fehlt. '
        'Erwartet: `filtered=_react.useMemo(...)` in StundenzettelView-Kontext — '
        'sonst Listenfilter-Re-Run pro Render. '
        'Siehe Hunt-Sprint v3.8.95 Agent UU.'
    )


def test_stundenzettel_sumhours_usecallback():
    """v3.8.95 UU: Stundenzettel `sumHours=_react.useCallback(...)`."""
    text = INDEX.read_text(encoding='utf-8')
    pattern = r'sumHours=_react\.useCallback'
    matches = re.findall(pattern, text)
    assert len(matches) >= 1, (
        'v3.8.95 Agent UU Regression: Stundenzettel sumHours useCallback-Wrap fehlt. '
        'Erwartet: `sumHours=_react.useCallback(...)` in StundenzettelView — '
        'sonst Stunden-Aggregator-Fn pro Render neu allokiert. '
        'Siehe Hunt-Sprint v3.8.95 Agent UU.'
    )
