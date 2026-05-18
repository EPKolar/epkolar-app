"""v3.9.11 Round-4: Modal-Migration native confirm → _confirmModal (7 sites).

Sicherstellt, dass Round-4-Konvertierungen in folgenden Lösch-Pfaden persistieren:
deleteEntry (Zeiterfassung), Fahrzeug-del, delWzPhoto.
Pattern: re.search/findall auf index.html — Body- bzw. Proximitäts-Matches.
"""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def _text():
    return INDEX.read_text(encoding='utf-8')


def test_confirmmodal_count_at_least_32():
    """Round-4 hob _confirmModal-Calls von ~25 (Round-3) auf >=32 (7 neue Sites)."""
    text = _text()
    count = len(re.findall(r'_confirmModal\(', text))
    assert count >= 32, (
        f"v3.9.11 Round-4 Regression: _confirmModal(-Calls = {count}, "
        f"erwartet >= 32 nach Round-4 (7 neue Sites)."
    )


def test_deleteentry_zeit_uses_confirmmodal():
    """deleteEntry (Zeiterfassung — Lösch-Pfad für Tageseintrag) muss _confirmModal nutzen."""
    text = _text()
    # deleteEntry-Body (async) bis schließendes }; — ~1500 chars reichen
    m = re.search(
        r'const deleteEntry\s*=\s*async[\s\S]{0,1500}?\};',
        text,
    )
    assert m, "v3.9.11 Round-4 Regression: deleteEntry-Definition nicht gefunden."
    body = m.group(0)
    assert '_confirmModal(' in body, (
        "v3.9.11 Round-4 Regression: deleteEntry (Zeiterfassung) muss "
        "_confirmModal(...) im Body haben (native confirm() entfernt)."
    )


def test_del_fahrzeug_uses_confirmmodal():
    """Fahrzeug-del (kurze inline arrow) muss _confirmModal nutzen — Proximitäts-Match."""
    text = _text()
    # Inline-del-Pattern: const del = (async)? in Proximität zu "Fahrzeug" und _confirmModal
    # Round-4 konvertierte Fahrzeug-Lösch-Pfad — suche im Body nach 'Fahrzeug' + _confirmModal
    pattern = (
        r'const del\s*=\s*(?:async)?[\s\S]{0,400}?'
        r'(?:Fahrzeug|fahrzeug)[\s\S]{0,200}?_confirmModal\('
    )
    m = re.search(pattern, text)
    if not m:
        # Alternative: _confirmModal-Text enthält "Fahrzeug" direkt in Lösch-Prompt
        pattern_alt = (
            r'const del\s*=\s*(?:async)?[\s\S]{0,400}?'
            r'_confirmModal\(\s*["\'][^"\']*Fahrzeug'
        )
        m = re.search(pattern_alt, text)
    assert m, (
        "v3.9.11 Round-4 Regression: Fahrzeug-del muss _confirmModal aufrufen — "
        "weder Proximity-Match (Fahrzeug...modal) noch Prompt-Text-Match gefunden."
    )


def test_delwzphoto_uses_confirmmodal():
    """delWzPhoto (Werkzeug-Foto löschen) muss _confirmModal nutzen."""
    text = _text()
    m = re.search(
        r'const delWzPhoto\s*=\s*async[\s\S]{0,800}?_confirmModal\(',
        text,
    )
    assert m, (
        "v3.9.11 Round-4 Regression: delWzPhoto muss _confirmModal aufrufen — "
        "native confirm() für Werkzeug-Foto-Löschung muss ersetzt sein."
    )
