"""v3.8.90: KPI-Tiles im Dashboard-Block (L8210-8255) mit a11y-Attributen.

Agent GG hat 7 KPI-Tiles mit role="button" + tabIndex=0 + aria-label + onKeyDown
(Enter/Space → onNav) ausgestattet. Diese Tests sichern die Regression ab.
"""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def _proximity(pattern_left: str, pattern_right: str, text: str, max_gap: int = 500):
    """Sucht pattern_left gefolgt von pattern_right innerhalb max_gap Zeichen."""
    return re.search(pattern_left + r'[\s\S]{0,' + str(max_gap) + r'}?' + pattern_right, text)


def test_kpi_tile_projekte_aktiv_role():
    text = INDEX.read_text(encoding='utf-8')
    m = _proximity(r'onNav\("projekte"\)', r'role:\s*"button"', text)
    assert m, 'v3.8.90 KPI-Tile-1 Regression: Projekte-aktiv Tile braucht role:"button" in Nähe von onNav("projekte")'
    m2 = _proximity(r'onNav\("projekte"\)', r'tabIndex:\s*0', text)
    assert m2, 'v3.8.90 KPI-Tile-1 Regression: Projekte-aktiv Tile braucht tabIndex:0'


def test_kpi_tile_arbeitsscheine_role():
    text = INDEX.read_text(encoding='utf-8')
    m = _proximity(r'__asFilter', r'onNav\("arbeitsscheine"\)', text)
    assert m, 'v3.8.90 KPI-Tile-2 Regression: Arbeitsscheine-Tile braucht __asFilter vor onNav("arbeitsscheine")'
    m2 = _proximity(r'__asFilter', r'role:\s*"button"', text)
    assert m2, 'v3.8.90 KPI-Tile-2 Regression: Arbeitsscheine-Tile braucht role:"button"'
    m3 = _proximity(r'__asFilter', r'tabIndex:\s*0', text)
    assert m3, 'v3.8.90 KPI-Tile-2 Regression: Arbeitsscheine-Tile braucht tabIndex:0'


def test_kpi_tile_fahrzeuge_role():
    text = INDEX.read_text(encoding='utf-8')
    # Es gibt mehrere onNav("fahrzeuge") (QR/Tankbeleg/km-Stand-Buttons in L8200-8202),
    # daher prüfen wir, dass mindestens EIN Vorkommen unmittelbar von role:"button" gefolgt wird.
    matches = list(re.finditer(r'onNav\("fahrzeuge"\)[\s\S]{0,500}?role:\s*"button"[\s\S]{0,200}?tabIndex:\s*0', text))
    assert len(matches) >= 1, 'v3.8.90 KPI-Tile-3 Regression: Fahrzeuge-Tile braucht role:"button" + tabIndex:0 in Nähe von onNav("fahrzeuge")'


def test_kpi_tile_werkzeuge_role():
    text = INDEX.read_text(encoding='utf-8')
    m = _proximity(r'onNav\("werkzeuge"\)', r'role:\s*"button"', text)
    assert m, 'v3.8.90 KPI-Tile-4 Regression: Werkzeuge-Tile braucht role:"button" in Nähe von onNav("werkzeuge")'
    m2 = _proximity(r'onNav\("werkzeuge"\)', r'tabIndex:\s*0', text)
    assert m2, 'v3.8.90 KPI-Tile-4 Regression: Werkzeuge-Tile braucht tabIndex:0'


def test_kpi_tile_urlaub_role():
    text = INDEX.read_text(encoding='utf-8')
    m = _proximity(r'onNav\("urlaub"\)', r'role:\s*"button"', text)
    assert m, 'v3.8.90 KPI-Tile-5 Regression: Urlaub-Tile braucht role:"button" in Nähe von onNav("urlaub")'
    m2 = _proximity(r'onNav\("urlaub"\)', r'tabIndex:\s*0', text)
    assert m2, 'v3.8.90 KPI-Tile-5 Regression: Urlaub-Tile braucht tabIndex:0'


def test_kpi_tile_stunden_role():
    text = INDEX.read_text(encoding='utf-8')
    m = _proximity(r'onNav\("stunden"\)', r'role:\s*"button"', text)
    assert m, 'v3.8.90 KPI-Tile-6 Regression: Stunden-Tile braucht role:"button" in Nähe von onNav("stunden")'
    m2 = _proximity(r'onNav\("stunden"\)', r'tabIndex:\s*0', text)
    assert m2, 'v3.8.90 KPI-Tile-6 Regression: Stunden-Tile braucht tabIndex:0'


def test_kpi_tile_keyboard_handler_count():
    text = INDEX.read_text(encoding='utf-8')
    # Sliding-window: Anzahl Enter-Keyboard-Handler im gesamten Body — >= 7 für 7 KPI-Tiles.
    matches = re.findall(r"onKeyDown:\s*e=>\{if\(e\.key===['\"]Enter['\"]", text)
    assert len(matches) >= 7, (
        f'v3.8.90 KPI-Tile-7 Regression: Erwartet >= 7 Enter-Keyboard-Handler '
        f'für KPI-Tiles, gefunden: {len(matches)}'
    )
