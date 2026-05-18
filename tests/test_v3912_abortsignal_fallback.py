"""v3.9.12 S15-4: AbortController-Fallback für _fT-Helper.

Sicherstellt, dass _fT(init, ms) zwei Code-Pfade hat:
  1. Bevorzugt: AbortSignal.timeout(ms) — moderne Browser.
  2. Fallback: new AbortController() + setTimeout(...abort) — iOS Safari <15 / alte Chrome.

Verhindert Regression, falls jemand den Fallback-Block versehentlich entfernt
(führt zu hängenden Requests auf älteren Mobile-Browsern).
"""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def _text():
    return INDEX.read_text(encoding='utf-8')


def test_fT_helper_exists():
    """_fT-Timeout-Helper muss als function-Declaration existieren (init, ms)."""
    text = _text()
    # Akzeptiere beide Formen: function _fT(init,ms){...} oder _fT = function(...)
    m = re.search(r'function\s+_fT\s*\(\s*init\s*,?\s*ms\s*\)', text)
    if not m:
        m = re.search(r'_fT\s*=\s*function\s*\(\s*init\s*,?\s*ms\s*\)', text)
    assert m, (
        "v3.9.12 S15-4 Regression: _fT(init, ms) Timeout-Helper nicht gefunden — "
        "weder als function-Declaration noch als function-Expression."
    )


def test_abortcontroller_fallback():
    """Fallback-Block: new AbortController() + setTimeout(...abort) für alte Browser."""
    text = _text()
    # Muster: new AbortController() ... innerhalb 300 chars ... setTimeout(...abort
    m = re.search(
        r'new AbortController\(\)[\s\S]{0,300}?setTimeout\([\s\S]{0,100}?abort',
        text,
    )
    assert m, (
        "v3.9.12 S15-4 Regression: AbortController-Fallback-Block fehlt — "
        "ohne ihn hängen Requests auf iOS Safari <15 / alten Chrome-Versionen "
        "unendlich (kein AbortSignal.timeout-Support)."
    )


def test_abortsignal_timeout_check():
    """Bevorzugter Path: AbortSignal.timeout(...) muss zuerst geprüft werden."""
    text = _text()
    # AbortSignal.timeout muss überhaupt vorkommen (moderner Path)
    assert re.search(r'AbortSignal\.timeout', text), (
        "v3.9.12 S15-4 Regression: AbortSignal.timeout fehlt komplett — "
        "_fT würde immer den Fallback-Pfad nehmen statt den modernen API."
    )
    # AbortSignal.timeout-Check VOR AbortController-Fallback im _fT-Body
    # (non-greedy '}' stoppt sonst beim ersten inner-try — daher Position-Search im Whole-Doc-Window)
    m = re.search(
        r'function\s+_fT\s*\([^)]*\)\s*\{([\s\S]{0,2000}?)return\s+init\s*\|\|\s*\{\}\s*;\s*\}',
        text,
    )
    assert m, "v3.9.12 S15-4 Regression: _fT-Body nicht extrahierbar (bis return init||{})."
    body = m.group(1)
    pos_signal = body.find('AbortSignal.timeout')
    pos_ctrl = body.find('new AbortController')
    assert pos_signal != -1 and pos_ctrl != -1 and pos_signal < pos_ctrl, (
        f"v3.9.12 S15-4 Regression: AbortSignal.timeout muss VOR "
        f"AbortController-Fallback geprüft werden "
        f"(AbortSignal pos={pos_signal}, AbortController pos={pos_ctrl})."
    )
