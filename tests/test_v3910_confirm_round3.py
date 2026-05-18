"""v3.9.10 Round-3: Modal-Migration native confirm → _confirmModal (10 sites).

Sicherstellt, dass Round-3-Konvertierungen in folgenden Lösch-Pfaden persistieren:
delFolder, delEntry (Bautagebuch + Abwesenheit), deleteOrder, deleteSuppOrd, deleteCatalog.
Pattern: re.search/findall auf index.html — Body- bzw. Proximitäts-Matches.
"""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def _text():
    return INDEX.read_text(encoding='utf-8')


def test_confirmmodal_count_at_least_25():
    """Round-3 hob _confirmModal-Calls von ~19 auf >=25 (10 neue Sites, einige Sites bündeln mehrere Calls)."""
    text = _text()
    count = len(re.findall(r'_confirmModal\(', text))
    assert count >= 25, (
        f"v3.9.10 Round-3 Regression: _confirmModal(-Calls = {count}, "
        f"erwartet >= 25 nach Round-3 (10 neue Sites)."
    )


def test_delfolder_uses_confirmmodal():
    """delFolder muss _confirmModal aufrufen (Ordner+Unterordner rekursiv löschen)."""
    text = _text()
    # Direkt-search: delFolder + _confirmModal in proximity (3000 chars für inner closures)
    m = re.search(
        r'const delFolder\s*=\s*async[\s\S]{0,3000}?_confirmModal\(',
        text,
    )
    assert m, (
        "v3.9.10 Round-3 Regression: delFolder muss _confirmModal aufrufen — "
        "muss _confirmModal(...) im Body haben."
    )


def test_dele_bautagebuch_uses_confirmmodal():
    """delEntry (Bautagebuch / Zeiteintrag) muss _confirmModal nutzen — mindestens ein delEntry-Body."""
    text = _text()
    bodies = re.findall(r'const delEntry\s*=\s*async[\s\S]{0,1500}?\};', text)
    assert bodies, "v3.9.10 Round-3 Regression: keine delEntry-Definition gefunden."
    with_modal = [b for b in bodies if '_confirmModal(' in b]
    assert with_modal, (
        f"v3.9.10 Round-3 Regression: keine delEntry-Variante nutzt _confirmModal "
        f"(gefunden: {len(bodies)} Defs, davon 0 mit Modal)."
    )


def test_deleteorder_uses_confirmmodal():
    """deleteOrder (Material-Bestellung) muss _confirmModal nutzen."""
    text = _text()
    m = re.search(r'const deleteOrder\s*=\s*async[\s\S]{0,1500}?\};', text)
    assert m, "v3.9.10 Round-3 Regression: deleteOrder-Definition nicht gefunden."
    body = m.group(0)
    assert '_confirmModal(' in body, (
        "v3.9.10 Round-3 Regression: deleteOrder muss _confirmModal(...) im Body haben "
        "(native confirm() entfernt)."
    )


def test_deletesupordord_uses_confirmmodal():
    """deleteSuppOrd (Händler-Bestellung) muss _confirmModal nutzen."""
    text = _text()
    m = re.search(r'const deleteSuppOrd\s*=\s*async[\s\S]{0,1500}?\};', text)
    assert m, "v3.9.10 Round-3 Regression: deleteSuppOrd-Definition nicht gefunden."
    body = m.group(0)
    assert '_confirmModal(' in body, (
        "v3.9.10 Round-3 Regression: deleteSuppOrd muss _confirmModal(...) im Body haben."
    )


def test_deletecatalog_uses_confirmmodal():
    """deleteCatalog (Material-Katalog) muss _confirmModal nutzen."""
    text = _text()
    m = re.search(r'const deleteCatalog\s*=\s*async[\s\S]{0,1500}?\};', text)
    assert m, "v3.9.10 Round-3 Regression: deleteCatalog-Definition nicht gefunden."
    body = m.group(0)
    assert '_confirmModal(' in body, (
        "v3.9.10 Round-3 Regression: deleteCatalog muss _confirmModal(...) im Body haben."
    )
