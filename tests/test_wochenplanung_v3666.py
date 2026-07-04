"""v3.9.666 Wochenplanung/Dispo — 2 P2-Fixes (Bug-Hunt-Subagent).

#1 flush() (beforeunload/unmount) rief das saveDirty aus dem ERSTEN Render → stale
   rows/kw/yr → Last-Second-Zuordnungen (<800ms vor Close) gingen verloren. Jetzt ueber
   _wpSaveDirtyRef die aktuelle Closure.
#2 "Naechste Woche"-Button war ungeklammert → in 52-Wochen-Jahren KW53-Misfile.
   switchKw kappt jetzt zentral via _getMaxKW(yr).
"""


def test_savedirty_ref(index_html):
    assert "const _wpSaveDirtyRef=_react.useRef.call(void 0, saveDirty);_wpSaveDirtyRef.current=saveDirty;" in index_html


def test_flush_uses_current_savedirty(index_html):
    assert "wpSaveTimer.current=null;try{_wpSaveDirtyRef.current();" in index_html
    # alte stale-Variante weg
    assert "wpSaveTimer.current=null;try{saveDirty();/* v3.9.500: pre-unmount" not in index_html


def test_switchkw_capped(index_html):
    assert "const switchKw=(newKw)=>{\n    newKw=Math.max(1,Math.min(_getMaxKW(yr),newKw));" in index_html
