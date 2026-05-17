"""v3.8.74 Hunt B-023: AuswertungView useMemo-Wraps (5 expensive computations)."""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'


def _assert_useMemo(name: str, deps: str, hunt_label: str):
    text = INDEX.read_text(encoding='utf-8')
    # Pattern: const NAME=_react.useMemo.call(void 0, ()=>...,[DEPS])
    # Non-greedy body up to 800 chars, then ,[DEPS])
    pattern = (
        r'const ' + re.escape(name) +
        r'=_react\.useMemo\.call\(void 0, ?\(\)=>[\s\S]{0,800}?,\s*\[' +
        re.escape(deps) + r'\]\)'
    )
    m = re.search(pattern, text)
    assert m, f'v3.8.74 Hunt B-023 Regression: {name} useMemo wrapper fehlt (deps [{deps}]) — {hunt_label}'


def test_asArt_useMemo_wrap():
    _assert_useMemo('asArt', 'arbeitsscheine', 'asArt over arbeitsscheine')


def test_absPerName_useMemo_wrap():
    _assert_useMemo('absPerName', 'monteure,abs', 'absPerName over monteure+abs')


def test_wzWert_useMemo_wrap():
    _assert_useMemo('wzWert', 'werkzeuge', 'wzWert over werkzeuge')


def test_fzTankProFz_useMemo_wrap():
    _assert_useMemo('fzTankProFz', 'fahrzeuge', 'fzTankProFz over fahrzeuge')


def test_last7_useMemo_wrap():
    _assert_useMemo('last7', 'entries', 'last7 over entries')
