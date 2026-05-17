"""v3.8.73 Hunt B-015: Kpi-Komponente A11y — Keyboard-Navigation für klickbare Tiles.

Klickbare Kpi-Kacheln müssen für Screen-Reader/Keyboard-User als Buttons erkennbar
sein: role="button", tabIndex=0, onKeyDown handler (Enter+Space).
"""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'


def _kpi_body() -> str:
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(
        r'function\s+Kpi\(\s*\{[^}]*\}\s*\)\s*\{([\s\S]{0,2500}?)\n\}\s*\n',
        text,
    )
    assert m, 'v3.8.73 Hunt B-015: function Kpi({...}) Body nicht auffindbar'
    return m.group(1)


def test_kpi_role_button_when_clickable():
    body = _kpi_body()
    m = re.search(r'role:\s*onClick\s*\?\s*"button"\s*:\s*undefined', body)
    assert m, (
        'v3.8.73 Hunt B-015 Regression: Kpi muss role:onClick?"button":undefined setzen '
        '(Screen-Reader-A11y für klickbare Tiles).'
    )


def test_kpi_tabIndex_when_clickable():
    body = _kpi_body()
    m = re.search(r'tabIndex:\s*onClick\s*\?\s*0\s*:\s*undefined', body)
    assert m, (
        'v3.8.73 Hunt B-015 Regression: Kpi muss tabIndex:onClick?0:undefined setzen '
        '(Keyboard-Navigation für klickbare Tiles).'
    )


def test_kpi_onKeyDown_handler_exists():
    body = _kpi_body()
    m = re.search(r'onKeyDown:', body)
    assert m, (
        'v3.8.73 Hunt B-015 Regression: Kpi muss onKeyDown-Handler haben '
        '(Enter+Space sollen onClick triggern).'
    )
