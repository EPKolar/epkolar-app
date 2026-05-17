"""v3.8.89 Sprint-5: Timer-Cleanups gegen Memory-Leak bei Tab-Close.
S5-1: _lsQuotaTimer (LocalStorage-Quota-Check, 5min) MUSS beforeunload-cleared werden.
S5-3: Juprowa-AutoSync-Timer MUSS via __epkJuprowaUnloadBound-Flag (double-bind-guard)
      + beforeunload->_juprowaStopAutoSync abgeraeumt werden."""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def test_localstorage_quota_timer_has_beforeunload():
    text = INDEX.read_text(encoding='utf-8')
    # 1) Timer-ID-Variable MUSS deklariert sein (let, nicht plain setInterval ohne Handle)
    decl = re.search(r'let\s+_lsQuotaTimer\s*=\s*setInterval\s*\(', text)
    assert decl, (
        'v3.8.89 S5-1 Regression: let _lsQuotaTimer=setInterval(...) Deklaration fehlt '
        '(ohne Handle kann der Timer beim Tab-Close nicht gecleared werden)'
    )
    # 2) beforeunload-Listener MUSS clearInterval(_lsQuotaTimer) aufrufen
    cleanup = re.search(
        r'addEventListener\(\s*"beforeunload"[\s\S]{0,400}?clearInterval\(\s*_lsQuotaTimer\s*\)',
        text,
    )
    assert cleanup, (
        'v3.8.89 S5-1 Regression: beforeunload-Listener mit clearInterval(_lsQuotaTimer) fehlt'
    )


def test_juprowa_sync_timer_has_beforeunload():
    text = INDEX.read_text(encoding='utf-8')
    # 1) Double-bind-Guard-Flag MUSS gesetzt werden
    flag = re.search(r'window\.__epkJuprowaUnloadBound', text)
    assert flag, (
        'v3.8.89 S5-3 Regression: window.__epkJuprowaUnloadBound Guard-Flag fehlt '
        '(ohne Flag wird Listener bei mehrfachem Init mehrfach registriert)'
    )
    # 2) beforeunload-Listener MUSS _juprowaStopAutoSync aufrufen
    listener = re.search(
        r'addEventListener\(\s*"beforeunload"\s*,\s*_juprowaStopAutoSync\s*\)',
        text,
    )
    assert listener, (
        'v3.8.89 S5-3 Regression: addEventListener("beforeunload", _juprowaStopAutoSync) fehlt'
    )
    # 3) Guard-Flag + Listener MUESSEN im selben if-Block stehen (Schutz vor Doppel-Registrierung)
    combined = re.search(
        r'if\s*\(\s*!\s*window\.__epkJuprowaUnloadBound\s*\)[\s\S]{0,400}?'
        r'addEventListener\(\s*"beforeunload"[\s\S]{0,200}?_juprowaStopAutoSync'
        r'[\s\S]{0,200}?__epkJuprowaUnloadBound\s*=\s*true',
        text,
    )
    assert combined, (
        'v3.8.89 S5-3 Regression: Guard-Flag + beforeunload-Listener nicht im gemeinsamen '
        'if(!__epkJuprowaUnloadBound)-Block (Double-Registration moeglich)'
    )
