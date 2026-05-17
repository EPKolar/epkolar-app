"""v3.8.84 Agent U: F3 Touch-Target & Memoization regressions."""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def test_f31_kundenportal_close_touch():
    """F3-1: KundenPortal close-Button muss 44x44 Touch-Target haben."""
    text = INDEX.read_text(encoding='utf-8')
    # Suche nach Pattern minHeight:44 + minWidth:44 (Reihenfolge egal) in nahem Umfeld
    found = False
    for m in re.finditer(r'minHeight\s*:\s*44[\s,]', text):
        window = text[max(0, m.start() - 300): m.end() + 300]
        if re.search(r'minWidth\s*:\s*44[\s,}]', window):
            found = True
            break
    assert found, (
        'v3.8.84 F3-1 Regression: KundenPortal close-Button braucht '
        'minHeight:44 + minWidth:44 (44x44 Touch-Target).'
    )


def test_f32_ticketdetail_photo_del_28px():
    """F3-2: TicketDetail Photo-Delete-Button muss 28x28 (statt 14x14) sein."""
    text = INDEX.read_text(encoding='utf-8')
    # Suche nach Pattern width:28 + height:28 in nahem Umfeld
    found = False
    for m in re.finditer(r'width\s*:\s*28[\s,]', text):
        window = text[max(0, m.start() - 200): m.end() + 200]
        if re.search(r'height\s*:\s*28[\s,}]', window):
            found = True
            break
    assert found, (
        'v3.8.84 F3-2 Regression: TicketDetail Photo-Delete-Button muss '
        'width:28,height:28 sein (statt 14x14).'
    )


def test_f36_kundenport_object_entries_memo():
    """F3-6: KundenPortal Object.entries(KUNDE_ST) muss useMemo-gewrappt sein."""
    text = INDEX.read_text(encoding='utf-8')
    pattern = r'_react\.useMemo\.call\(\s*void 0\s*,\s*\(\s*\)\s*=>\s*Object\.entries\s*\(\s*KUNDE_ST\s*\)\.map'
    assert re.search(pattern, text), (
        'v3.8.84 F3-6 Regression: Object.entries(KUNDE_ST).map muss in '
        '_react.useMemo.call(void 0, ()=>...) gewrappt sein (Render-Perf).'
    )


def test_f37_ticketdetail_comment_input():
    """F3-7: TicketDetail Comment-Input muss kompaktes padding/font/minHeight haben."""
    text = INDEX.read_text(encoding='utf-8')
    # Suche nach Cluster padding:"8px 10px" + fontSize:12 + minHeight:40 im nahen Umfeld
    found = False
    for m in re.finditer(r'padding\s*:\s*"8px 10px"', text):
        window = text[max(0, m.start() - 400): m.end() + 400]
        if (re.search(r'fontSize\s*:\s*12[\s,}]', window)
                and re.search(r'minHeight\s*:\s*40[\s,}]', window)):
            found = True
            break
    assert found, (
        'v3.8.84 F3-7 Regression: TicketDetail Comment-Input braucht '
        'padding:"8px 10px",fontSize:12,minHeight:40 (Mobile-Compact).'
    )
