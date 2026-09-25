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
import re

from conftest import _extract_fn


def test_projlist_ismob_vor_gridcols(index_html):
    """Gemessen wird die REIHENFOLGE, nicht die Schreibweise der Schwelle.

    v3.9.932: der Riegel suchte woertlich `const isMob=ww<600;`. Mit der
    Einfuehrung von BP_MOB heisst dieselbe Zeile `const isMob=ww<BP_MOB;`,
    und der Riegel wurde rot, obwohl die Eigenschaft, die er sichert - die
    Deklaration steht VOR der Verwendung - unveraendert erfuellt ist.

    Das ist die haeufigste Krankheit der Riegel in diesem Bestand: sie
    pinnen eine SCHREIBWEISE statt einer EIGENSCHAFT und werden rot, wenn
    der Code besser wird. Das Muster nimmt jetzt jede Schwelle an; die
    Reihenfolge-Aussage bleibt woertlich dieselbe.

    Fail-closed bleibt es auch: verschwindet die Deklaration ganz, ist der
    Riegel rot und nicht etwa gruen.
    """
    body = _extract_fn(index_html, "ProjList")
    assert body, "ProjList nicht gefunden"
    m = re.search(r"const isMob\s*=\s*ww\s*<\s*[A-Za-z0-9_]+\s*;", body)
    assert m, ("isMob-Deklaration in ProjList nicht gefunden - weder mit "
               "Zahl noch mit Konstante. Das ist rot, nicht gruen.")
    i_decl = m.start()
    i_use = body.find("_gridCols=isMob")
    assert i_use >= 0, "_gridCols in ProjList nicht gefunden"
    assert i_decl < i_use, "TDZ: isMob muss VOR _gridCols deklariert sein"
