"""App-Render-Safety — verhindert Regression von React-#310 (v3.8.50 Hotfix).

Zwei kritische Invarianten der App-Komponente werden statisch gegen die
gebundelte index.html geprueft:

1. Initial-State: `appLoading` startet `true`, `curUser` startet `null`.
   Wenn jemand den Default kippt (z.B. `appLoading=false`), wird die
   Login-Phase uebersprungen und nachgelagerte Tabs rendern, bevor curUser
   gesetzt ist -> Cascade-NPE oder Hook-Order-Drift.

2. `tabs`-Definition ist null-safe: `const tabs = curUser ? _allTabs.filter(...)`
   Wenn der `curUser ?` -Guard verschwindet, faellt `_allTabs.filter` ueber
   `curUser.role` etc., bevor curUser gesetzt ist -> #310-Risiko.
"""

from __future__ import annotations

import re
from pathlib import Path

INDEX = Path(__file__).resolve().parent.parent / "index.html"

APP_LOADING_RE = re.compile(
    r"\[appLoading,setAppLoading\]=_react\.useState\.call\(void 0, true\)"
)
CUR_USER_RE = re.compile(
    r"\[curUser,setCurUser\]=_react\.useState\.call\(void 0, null\)"
)
TABS_GUARD_RE = re.compile(r"const\s+tabs\s*=\s*curUser\s*\?\s*_allTabs\.filter")


def test_app_initial_state() -> None:
    text = INDEX.read_text(encoding="utf-8")
    assert APP_LOADING_RE.search(text), (
        "appLoading-useState-Default ist nicht mehr 'true' — Login-Phase wird "
        "uebersprungen und nachgelagerte Tabs rendern vor curUser-Init."
    )
    assert CUR_USER_RE.search(text), (
        "curUser-useState-Default ist nicht mehr 'null' — verletzt Annahme von "
        "tabs-Guard und kann zu Cascade-NPE fuehren."
    )


def test_tabs_curUser_null_safe() -> None:
    text = INDEX.read_text(encoding="utf-8")
    assert TABS_GUARD_RE.search(text), (
        "tabs-Definition ist nicht mehr 'curUser ? _allTabs.filter(...)' — "
        "ohne curUser-Guard greift _allTabs.filter auf curUser.role zu, bevor "
        "curUser gesetzt ist (React-#310-Risiko)."
    )
