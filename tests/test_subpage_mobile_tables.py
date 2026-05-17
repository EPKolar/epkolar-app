"""v3.8.74 Sub-Page CSS: isMob?...:600 patterns for mobile-safe table widths."""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'


def test_material_preisvergleich_mobile_minwidth():
    """Material Preisvergleich: minWidth:isMob?"auto":Math.max(600,300+pvSupplierIds.length*120)."""
    text = INDEX.read_text(encoding='utf-8')
    pattern = r'minWidth:isMob\?"auto":Math\.max\(600,\s*300\+pvSupplierIds\.length\*120\)'
    assert re.search(pattern, text), \
        'v3.8.74 Sub-Page CSS Regression: Material Preisvergleich table minWidth-isMob-guard fehlt'


def test_weekplan_mobile_minwidth():
    """WeekPlan: minWidth:isMob?0:600,fontSize:12."""
    text = INDEX.read_text(encoding='utf-8')
    pattern = r'minWidth:isMob\?0:600,\s*fontSize:12'
    assert re.search(pattern, text), \
        'v3.8.74 Sub-Page CSS Regression: WeekPlan table minWidth-isMob-guard fehlt'


def test_chefdashboard_ampeln_mobile_minwidth():
    """ChefDashboard Projekt-Ampeln: minWidth:isMob?0:600 (pattern occurs >=2x in index.html)."""
    text = INDEX.read_text(encoding='utf-8')
    matches = re.findall(r'minWidth:isMob\?0:600', text)
    assert len(matches) >= 2, \
        f'v3.8.74 Sub-Page CSS Regression: ChefDashboard Projekt-Ampeln minWidth-isMob-guard fehlt ' \
        f'(erwartet >=2 Vorkommen für WeekPlan + ChefDashboard, gefunden: {len(matches)})'
