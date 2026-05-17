"""v3.8.94 Agent TT: Mitarbeiter-View useMemo-Wraps.

Re-Render-Sparplatz: roleKpis und activeProjectsCount in MitarbeiterView
muessen in _react.useMemo gewrappt sein, sonst Re-Allocation pro Render.

* **roleKpis:** Aggregation ueber monteure[] — Deps [monteure].
* **activeProjectsCount:** Filter ueber projects[] aktiv-Zaehlung — Deps [projects].
"""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def test_role_kpis_usememo():
    """v3.8.94 TT: `const _roleKpis=_react.useMemo.call(void 0, ()=> ..., [monteure])`."""
    text = INDEX.read_text(encoding='utf-8')
    pattern = (
        r'_roleKpis=_react\.useMemo\.call\(void 0,\s*\(\)=>'
        r'[\s\S]{0,800}?\[monteure\]\)'
    )
    matches = re.findall(pattern, text)
    assert len(matches) >= 1, (
        'v3.8.94 Agent TT Regression: roleKpis useMemo-Wrap fehlt. '
        'Erwartet: `_roleKpis=_react.useMemo.call(void 0, ()=> ..., [monteure])` '
        'in MitarbeiterView — sonst Re-Allocation pro Render. '
        'Siehe Hunt-Sprint v3.8.94 Agent TT.'
    )


def test_active_projects_count_usememo():
    """v3.8.94 TT: `_activeProjectsCount=_react.useMemo(... , [projects])`."""
    text = INDEX.read_text(encoding='utf-8')
    pattern = (
        r'_activeProjectsCount=_react\.useMemo[\s\S]{0,400}?\[projects\]\)'
    )
    matches = re.findall(pattern, text)
    assert len(matches) >= 1, (
        'v3.8.94 Agent TT Regression: activeProjectsCount useMemo-Wrap fehlt. '
        'Erwartet: `_activeProjectsCount=_react.useMemo(...,[projects])` '
        'in MitarbeiterView — sonst Filter-Re-Run pro Render. '
        'Siehe Hunt-Sprint v3.8.94 Agent TT.'
    )
