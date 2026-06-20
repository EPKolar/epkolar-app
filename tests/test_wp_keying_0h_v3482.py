"""v3.9.482 — Fix 0h-Matrix-Inline (DELETE statt PUT 0) + wpHistory-Jahr-Keying."""
import pathlib

SRC = pathlib.Path(__file__).resolve().parent.parent / "index.html"
HTML = SRC.read_text(encoding="utf-8")


def test_matrix_0h_deletes_existing_entry():
    # bestehender Eintrag auf 0h → DELETE (kein PUT hours:0-Zombie)
    assert 'if(_h<=0){/* v3.9.482:' in HTML, "0h-Lösch-Zweig im Matrix-Handler fehlt"
    assert '🗑️ Eintrag gelöscht (0 h)' in HTML


def test_wphistory_composite_key_helpers():
    assert "const _wpKey=(k)=>yr+'-'+k;" in HTML, "_wpKey-Helper (Schreib-Key) fehlt"
    assert "const _wpGet=(k)=>wpHistory[_wpKey(k)]||wpHistory[k];" in HTML, "_wpGet-Helper (Lesen + Legacy-Fallback) fehlt"


def test_wphistory_load_keys_with_year():
    assert "wpH[(wp.year!=null?wp.year:0)+'-'+wp.week]" in HTML, "Server-Load keyt wpHistory nicht jahr-präfixiert"


def test_wphistory_writes_use_wpkey():
    # saveWeek + switchKw schreiben den composite Key
    assert "setWpHistory(h=>({...h,[_wpKey(kw)]:rows}))" in HTML, "saveWeek/switchKw schreiben nicht den composite Key"


def test_savedkws_parses_current_year_only():
    assert "Object.keys(wpHistory).filter(k=>(k+'').indexOf(yr+'-')===0)" in HTML, "savedKws filtert nicht auf das aktuelle Jahr"


def test_homeview_uses_year_key_with_fallback():
    assert "(wpHistory||{})[yr+'-'+curKw]||(wpHistory||{})[curKw]||[]" in HTML, "HomeView nutzt nicht den jahr-präfixierten Key mit Fallback"
