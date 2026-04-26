"""v3.8.62 Bugfix-Tests (Live-Audit Sa 26.04.2026)."""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'


# ═══ Bug-1: SW_VER-Scope + Banner-Hide ═══

def test_sw_ver_window_scoped():
    """SW_VER muss ins window-scope exposed sein (sonst window.SW_VER === undefined)."""
    text = INDEX.read_text(encoding='utf-8')
    assert 'window.SW_VER=SW_VER' in text or 'window.SW_VER = SW_VER' in text, \
        'SW_VER muss als window.SW_VER exposed sein'


def test_doSwUpdate_clears_banner_state():
    """doSwUpdate muss setSwUpdate(false) aufrufen damit Banner sofort verschwindet."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'const doSwUpdate\s*=\s*async\s*\(\s*\)\s*=>\s*\{([^}]+)\}', text)
    assert m, 'doSwUpdate-Definition nicht gefunden'
    assert 'setSwUpdate(false)' in m.group(1), \
        'doSwUpdate muss setSwUpdate(false) aufrufen (Banner-Hide-UX)'


def test_self_heal_iife_writes_localstorage_after_clear():
    """Self-Heal IIFE muss epk_sw_ver=SW_VER schreiben nach Cache-Clear."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'var SW_VER[\s\S]{0,1500}?localStorage\.setItem\([\'"]epk_sw_ver[\'"]\s*,\s*SW_VER', text)
    assert m, 'Self-Heal IIFE muss localStorage.setItem(epk_sw_ver, SW_VER) machen'


# ═══ Bug-2: Kontrast WCAG-AA ═══

def test_krankenstand_button_uses_pastel_color():
    """Krankenstand-Button (L13022) muss helleres rot (#fca5a5) statt #ef4444 nutzen."""
    text = INDEX.read_text(encoding='utf-8')
    # Pattern: button für 'Krankmeldung' mit color #fca5a5
    assert re.search(r'Krankmeldung[\s\S]{0,200}#fca5a5', text) or \
           re.search(r'#fca5a5[\s\S]{0,500}Krankmeldung', text), \
        'Krankmeldung-Button muss #fca5a5 nutzen (WCAG-AA pastel)'


def test_zeitausgleich_button_uses_pastel_color():
    """Zeitausgleich-Button (L13023) muss helleres lila (#d8b4fe) statt #a855f7 nutzen."""
    text = INDEX.read_text(encoding='utf-8')
    assert re.search(r'Zeitausgleich[\s\S]{0,200}#d8b4fe', text) or \
           re.search(r'#d8b4fe[\s\S]{0,500}Zeitausgleich', text), \
        'Zeitausgleich-Button muss #d8b4fe nutzen (WCAG-AA pastel)'


# ═══ Bug-3: Urlaub-Tabelle Header-Klarheit ═══

def test_urlaub_table_header_rest_explicit():
    """Header 'Rest' wurde zu 'Rest Urlaub' (eindeutig: nur Urlaub abgezogen)."""
    text = INDEX.read_text(encoding='utf-8')
    # Pattern: th mit "Rest Urlaub" und color #22c55e
    assert re.search(r'#22c55e[^}]{0,200}\}\s*,\s*title:[^,]{0,200}Resturlaub', text), \
        'Rest-Urlaub-Header muss tooltip mit "Resturlaub"-Erklaerung haben'
    assert '"Rest Urlaub"' in text or "'Rest Urlaub'" in text, \
        'Header-Label muss "Rest Urlaub" sein (nicht nur "Rest")'


def test_urlaub_table_header_urlaub_has_tooltip():
    """Urlaub-Header muss Tooltip haben (zeigt ALLE inkl. ausstehend, nur genehmigte abgezogen)."""
    text = INDEX.read_text(encoding='utf-8')
    # th mit color #3b82f6 und title-Property mit "ausstehend" o.ä.
    assert re.search(r'#3b82f6[^}]{0,200}\}\s*,\s*title:\s*[\'"][^\'"]*ausstehend', text), \
        'Urlaub-Header muss Tooltip mit "ausstehend"-Erklaerung haben'


def test_urlaub_resturlaub_formula_unchanged():
    """resturlaub-Formel selbst wurde NICHT geändert (nur Header-Label)."""
    text = INDEX.read_text(encoding='utf-8')
    # Suche resturlaub-Body, prüfe dass Formel-Tokens stunden/vorjahr/urlaubStdGen vorkommen
    m = re.search(r'const resturlaub\s*=\s*m\s*=>[\s\S]{0,400}?ys\.urlaubStdGen', text)
    assert m, 'resturlaub-Funktion mit ys.urlaubStdGen-Referenz nicht gefunden'
    body = m.group(0)
    assert 'ks.stunden' in body, 'resturlaub muss ks.stunden referenzieren'
    assert 'ks.vorjahr' in body, 'resturlaub muss ks.vorjahr referenzieren'
