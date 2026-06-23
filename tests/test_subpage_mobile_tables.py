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
    """v3.9.523: WeekPlan-Planungs-Streifen (Abwesenheiten + SpezFz) wurden vom
    minWidth:isMob?0:600-Tabellenlayout auf das Wetter/Tabellen-Flex-Grid (minWidth:800,
    overflowX:auto) umgestellt. Mobile-Safety jetzt über Desktop-Gate (!isMob) + Tages-Karten
    statt der alten isMob?0:600-Tabelle. Test prüft beide Pfade."""
    text = INDEX.read_text(encoding='utf-8')
    # SpezFz-Übersichtsstreifen ist Desktop-only → kein Mobile-Table-Overflow
    assert 'spezFz.length>0&&!isMob' in text, \
        'WeekPlan SpezFz-Streifen nicht mehr !isMob-gated (Mobile-Safety-Regression)'
    # Mobile-Pfad existiert als Card-Block (v3.9.505)
    assert 'spezFz.length>0&&isMob' in text, \
        'WeekPlan SpezFz Mobile-Card-Block fehlt'


def test_chefdashboard_ampeln_mobile_minwidth():
    """ChefDashboard Projekt-Ampeln: minWidth:isMob?0:600.
    v3.9.523: Das 2. Vorkommen (WeekPlan SpezFz-Streifen) wurde auf das Flex-Grid umgestellt,
    daher bleibt nur noch das ChefDashboard-Vorkommen (>=1)."""
    text = INDEX.read_text(encoding='utf-8')
    matches = re.findall(r'minWidth:isMob\?0:600', text)
    assert len(matches) >= 1, \
        f'ChefDashboard Projekt-Ampeln minWidth-isMob-guard fehlt (gefunden: {len(matches)})'
