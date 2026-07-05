"""v3.9.672 HOTFIX ProjList TDZ — "Tab Projekte lud nicht".

const _gridCols=isMob?... stand VOR const isMob=ww<600; in ProjList
-> ReferenceError "Cannot access 'isMob' before initialization" (TDZ),
von ViewBoundary:projekte gefangen -> Tab zeigte Fehler statt Liste.

Guard: ProjList-spezifisch — die `const isMob=ww<600;`-Deklaration muss VOR
der ersten Verwendung (`_gridCols=isMob`) stehen.

Hinweis: Ein breiterer Scan ueber alle `function`-Bloecke wurde erprobt, aber
wieder entfernt — die naive Brace-Extraktion zieht bei grossen Komponenten (App)
verschachtelte innere Funktionen mit eigener isMob-Deklaration mit rein und
meldet dadurch False Positives. Ein sauberer Scope-Scan braucht einen echten
JS-Parser; hier reicht der ProjList-Regression-Guard fuer den konkreten Bug.
"""
from conftest import _extract_fn


def test_projlist_ismob_vor_gridcols(index_html):
    body = _extract_fn(index_html, "ProjList")
    assert body, "ProjList nicht gefunden"
    i_decl = body.find("const isMob=ww<600;")
    i_use = body.find("_gridCols=isMob")
    assert i_decl >= 0, "isMob-Deklaration in ProjList nicht gefunden"
    assert i_use >= 0, "_gridCols in ProjList nicht gefunden"
    assert i_decl < i_use, "TDZ: isMob muss VOR _gridCols deklariert sein"
