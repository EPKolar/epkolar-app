"""v3.8.91 Sprint-6 UX regression tests.

Coverage:
- PhotoQ-Panel stopPropagation (verhindert dass Klick im Panel das Backdrop schliesst)
- Search-Modal Escape-Keydown (Esc schliesst Modal)
- PhotoQ ClearAll nutzt _confirmModal statt nativem confirm()
- PhotoQ ClearAll handler ist async (await _confirmModal)
"""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def test_photoq_panel_stoppropagation():
    """v3.8.91 S6-N Regression: showPhotoQ-Panel-Wrapper muss onClick stopPropagation haben,
    sonst schliesst jeder Klick im Panel ueber das Backdrop (zIndex 299) das Panel selbst."""
    text = INDEX.read_text(encoding='utf-8')
    # Panel ist das ZWEITE showPhotoQ&&React.createElement('div', ...) — direkt nach dem Backdrop.
    # Suche nach Panel-Wrapper mit zIndex:300 (Backdrop hat zIndex:299).
    m = re.search(
        r"showPhotoQ&&\(React\.createElement\('div',\s*\{[\s\S]{0,400}?onClick:\s*e\s*=>\s*e\.stopPropagation\(\)[\s\S]{0,400}?zIndex:\s*300",
        text,
    )
    assert m, (
        "v3.8.91 S6-N Regression: showPhotoQ-Panel (zIndex:300) muss "
        "onClick:e=>e.stopPropagation() haben — sonst bubbled Klick zum Backdrop."
    )


def test_search_modal_escape_keydown():
    """v3.8.91 S6-N Regression: Search-Modal-Wrapper muss onKeyDown haben das Escape abfaengt
    und setShowSearch(false) aufruft."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(
        r"onKeyDown:\s*e\s*=>\s*\{\s*if\s*\(\s*e\.key\s*===\s*['\"]Escape['\"]\s*\)\s*\{\s*setShowSearch\(false\)",
        text,
    )
    assert m, (
        "v3.8.91 S6-N Regression: Search-Modal muss onKeyDown mit "
        "if(e.key==='Escape'){setShowSearch(false);} haben."
    )


def test_photoq_clearall_uses_confirmmodal():
    """v3.8.91 S6-N Regression: PhotoQ ClearAll-Button muss _confirmModal nutzen
    (a11y/i18n-conform) statt nativem confirm(). Native confirm() ist legacy."""
    text = INDEX.read_text(encoding='utf-8')
    # Suche Header-PhotoQ-Panel ClearAll-Button: await _confirmModal(...) gefolgt von PhotoQ.clear()
    m = re.search(
        r"await\s+_confirmModal\([\s\S]{0,200}?Warteschlange[\s\S]{0,400}?PhotoQ\.clear\(\)",
        text,
    )
    assert m, (
        "v3.8.91 S6-N Regression: PhotoQ ClearAll im Header-Panel muss "
        "'await _confirmModal(...)' statt 'confirm(...)' verwenden."
    )


def test_photoq_clearall_handler_is_async():
    """v3.8.91 S6-N Regression: PhotoQ ClearAll-Button onClick muss async arrow-fn sein
    (Voraussetzung fuer 'await _confirmModal'). Sliding-window 400 Zeichen vor _confirmModal."""
    text = INDEX.read_text(encoding='utf-8')
    # Sliding-window: onClick: async ()=>{ ... await _confirmModal( ... ) ... PhotoQ.clear()
    m = re.search(
        r"onClick:\s*async\s*\(\s*\)\s*=>\s*\{[\s\S]{0,400}?await\s+_confirmModal[\s\S]{0,400}?PhotoQ\.clear\(\)",
        text,
    )
    assert m, (
        "v3.8.91 S6-N Regression: PhotoQ ClearAll onClick muss als "
        "'async ()=>{...await _confirmModal...}' deklariert sein."
    )
