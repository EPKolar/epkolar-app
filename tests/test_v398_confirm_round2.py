"""v3.9.8 (Agent SSS): Confirm-Migration Round 2 — delM/delE auf _confirmModal."""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def test_confirmmodal_count_at_least_16():
    """v3.9.8 Regression: _confirmModal-Aufruf-Count muss >= 16 sein.

    Vor Round 2 waren es 10 (v3.9.4 Migration). Round 2 ergänzte ~10 weitere
    Call-Sites (delM, delE, Regie-Lösch-Buttons, etc.) — Total >= 16 erwartet.
    """
    text = INDEX.read_text(encoding='utf-8')
    matches = re.findall(r'_confirmModal\(', text)
    assert len(matches) >= 16, (
        f'v3.9.8 Regression: _confirmModal-Count={len(matches)} < 16 — '
        f'Round-2-Migration (delM/delE/Regie) unvollständig oder rückgängig gemacht'
    )


def test_delm_uses_confirmmodal():
    """v3.9.8 Regression: delM (Mangel-Löschen) muss _confirmModal verwenden, kein native confirm()."""
    text = INDEX.read_text(encoding='utf-8')
    # delM-Definition + _confirmModal innerhalb von ~300 Zeichen Proximity
    m = re.search(r'\bdelM\b\s*=[\s\S]{0,300}?_confirmModal\(', text)
    assert m, (
        'v3.9.8 Regression: delM verwendet _confirmModal nicht in Proximity — '
        'Round-2-Migration für Mangel-Delete fehlt oder zurückgerollt'
    )


def test_dele_regie_uses_confirmmodal():
    """v3.9.8 Regression: delE (Regie-Eintrag-Löschen) muss _confirmModal verwenden."""
    text = INDEX.read_text(encoding='utf-8')
    # delE-Definition oder Aufruf + _confirmModal in Proximity
    m = re.search(r'\bdelE\b[\s\S]{0,300}?_confirmModal\(', text)
    assert m, (
        'v3.9.8 Regression: delE verwendet _confirmModal nicht in Proximity — '
        'Round-2-Migration für Regie-Delete fehlt oder zurückgerollt'
    )
