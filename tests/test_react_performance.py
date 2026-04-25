"""v3.8.61 MEGA-C Phase 7.4: React-Performance-Patterns."""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'


def test_useMemo_min_count():
    """Mindestens 5 _react.useMemo-Calls (Code nutzt useMemo aktiv für teure Berechnungen)."""
    text = INDEX.read_text(encoding='utf-8')
    matches = re.findall(r'_react\.useMemo\.call', text)
    assert len(matches) >= 5, f'Min. 5 _react.useMemo-Calls erwartet, gefunden: {len(matches)}'


def test_useCallback_min_count():
    """Mindestens 3 _react.useCallback-Calls (Code nutzt useCallback aktiv)."""
    text = INDEX.read_text(encoding='utf-8')
    matches = re.findall(r'_react\.useCallback\.call', text)
    assert len(matches) >= 3, f'Min. 3 _react.useCallback-Calls erwartet, gefunden: {len(matches)}'


def test_react_memo_for_TicketListItem():
    """TicketListItem ist React.memo-wrapped (Phase 5.3)."""
    text = INDEX.read_text(encoding='utf-8')
    assert 'React.memo(function TicketListItem' in text, \
        'TicketListItem muss React.memo-wrapped sein'


def test_useMemo_calls_have_deps_array():
    """Alle _react.useMemo-Calls müssen ein deps-Array als 2. Arg haben (kein undefined)."""
    text = INDEX.read_text(encoding='utf-8')
    # Pattern: _react.useMemo.call(void 0, fn, [...])
    # OHNE deps-Array würde es enden mit ");"  ohne ", [...])"
    # Suche nach useMemo-Calls und verifiziere dass innerhalb der nächsten ~3000 chars ein "],"-Pattern oder "])" am Ende kommt
    suspicious = []
    for m in re.finditer(r'_react\.useMemo\.call\(void 0,', text):
        pos = m.start()
        # Forward bracket-balance
        depth = 0
        end = pos
        for i in range(pos, min(pos + 5000, len(text))):
            if text[i] == '(':
                depth += 1
            elif text[i] == ')':
                depth -= 1
                if depth == 0:
                    end = i
                    break
        # Tail check: muss `,[..]` oder `,[]` vor end sein
        tail = text[max(end - 300, pos):end + 1]
        if not re.search(r',\s*\[[^\[\]]*\]\s*\)$', tail):
            line = text[:pos].count('\n') + 1
            suspicious.append(line)
    assert not suspicious, f'useMemo ohne deps-Array bei Lines: {suspicious[:5]}'


def test_useCallback_calls_have_deps_array():
    """Alle _react.useCallback-Calls müssen ein deps-Array haben."""
    text = INDEX.read_text(encoding='utf-8')
    suspicious = []
    for m in re.finditer(r'_react\.useCallback\.call\(void 0,', text):
        pos = m.start()
        depth = 0
        end = pos
        for i in range(pos, min(pos + 5000, len(text))):
            if text[i] == '(':
                depth += 1
            elif text[i] == ')':
                depth -= 1
                if depth == 0:
                    end = i
                    break
        tail = text[max(end - 300, pos):end + 1]
        if not re.search(r',\s*\[[^\[\]]*\]\s*\)$', tail):
            line = text[:pos].count('\n') + 1
            suspicious.append(line)
    assert not suspicious, f'useCallback ohne deps-Array bei Lines: {suspicious[:5]}'


def test_useEffect_async_active_flag_count():
    """Mindestens 4 useEffect-Bodies mit active-flag (Race-Schutz, Hunt-Mode + v3.8.53 fixes)."""
    text = INDEX.read_text(encoding='utf-8')
    matches = re.findall(r'let active\s*=\s*true', text)
    assert len(matches) >= 4, f'Min. 4 active-flag-Patterns erwartet, gefunden: {len(matches)}'
