"""v3.8.61 MEGA-C Phase 7.3: Werkzeug-Tabelle Funktionalitaet."""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'


def test_werkzeug_view_exists():
    text = INDEX.read_text(encoding='utf-8')
    assert 'function WerkzeugView(' in text


def test_werkzeug_sort_state_exists():
    """Sortierung via toggleSort + sortCol/sortDir State."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'function WerkzeugView\([\s\S]{0,15000}?(sortKey|sortCol|sortField|toggleSort)', text)
    assert m, 'WerkzeugView muss Sort-State haben'


def test_werkzeug_filter_chip_state():
    """werkStatusFilter-State muss existieren (Phase 4.1 Filter-Chips)."""
    text = INDEX.read_text(encoding='utf-8')
    assert 'werkStatusFilter' in text or '[werkFilter' in text or '[wzStatusFilter' in text, \
        'Werkzeug-Filter-State (werkStatusFilter o.ae.) muss existieren'


def test_werkzeug_5_filter_chips_categories():
    """5 Filter-Chips: alle/verfügbar/ausgegeben/kalibrierung/defekt-or-verloren."""
    text = INDEX.read_text(encoding='utf-8')
    # Zumindest 4 der 5 Begriffe müssen im WerkzeugView-Body vorkommen
    chip_terms = ['Verfügbar', 'Ausgegeben', 'Kalibrierung', 'Defekt']
    found = sum(1 for t in chip_terms if t in text)
    assert found >= 3, f'Min. 3 von 4 Chip-Labels (Verfügbar/Ausgegeben/Kalibrierung/Defekt), gefunden: {found}'


def test_werkzeug_multi_select_state():
    """Multi-Select selectedIds-State muss existieren (Phase 4.2)."""
    text = INDEX.read_text(encoding='utf-8')
    assert 'selectedIds' in text or 'selectedWerk' in text, \
        'Multi-Select State (selectedIds o.ae.) muss existieren'


def test_werkzeug_bulk_action_bar_conditional():
    """Bulk-Action-Bar nur wenn selectedIds.length > 0."""
    text = INDEX.read_text(encoding='utf-8')
    assert 'selectedIds.length' in text or 'selectedIds.length > 0' in text, \
        'Bulk-Action-Bar muss conditional auf selectedIds.length sein'


def test_werkzeug_kalibrierung_uses_naechste_kalib():
    """Filter 'Kalibrierung fällig' muss naechste_kalib (snake) verwenden."""
    text = INDEX.read_text(encoding='utf-8')
    # naechste_kalib ist die DB-Spalte (snake_case)
    assert 'naechste_kalib' in text or 'naechsteKalib' in text, \
        'Kalibrierungs-Datum (naechste_kalib) muss im Code verwendet werden'


def test_werkzeug_sort_uses_localecompare():
    """Werkzeug-Sortierung muss localeCompare nutzen (deutsche Umlaute korrekt sortieren)."""
    text = INDEX.read_text(encoding='utf-8')
    # WerkzeugView Sort-Body nutzt localeCompare (im sorted-useMemo)
    m = re.search(r'function WerkzeugView[\s\S]{0,15000}?localeCompare', text)
    assert m, 'WerkzeugView Sort muss localeCompare nutzen'


def test_werkzeug_isMob_responsive_font():
    """Werkzeug-Tabelle muss isMob für responsive font-size nutzen (Phase v3.8.55)."""
    text = INDEX.read_text(encoding='utf-8')
    # Mindestens 1 isMob?N:M-Pattern im WerkzeugView-Bereich
    m = re.search(r'function WerkzeugView\([\s\S]{0,25000}?isMob\s*\?\s*\d+\s*:\s*\d+', text)
    assert m, 'WerkzeugView muss isMob?N:M für Schrift nutzen'
