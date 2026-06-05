"""v3.9.130 — Teilzeit: stdVonTag woche-aware. BEWEIS: Vollzeit (38,5/fehlend) = identisch zu v3.9.129."""
import json
import re
from conftest import run_node_snippet


def _extract(index_html):
    es = re.search(r"function _easterSunday\(y\)\{[\s\S]*?\n\}", index_html).group(0)
    fe = re.search(r"function _isATFeiertag\(d\)\{[\s\S]*?\n\}", index_html).group(0)
    sv = re.search(r"const stdVonTag=\(d,woche\)=>\{[^\n]*?\};", index_html).group(0)
    return es + "\n" + fe + "\n" + sv.replace("const stdVonTag", "globalThis.stdVonTag")


def test_fulltime_is_noop(node_exe, index_html):
    code = _extract(index_html)
    # 2026-06-09 = Dienstag (kein Feiertag), 2026-06-12 = Freitag, 2026-06-13 = Samstag, 2026-06-04 = Fronleichnam
    snippet = code + (
        "const di=new Date(2026,5,9),fr=new Date(2026,5,12),sa=new Date(2026,5,13),fl=new Date(2026,5,4);"
        "process.stdout.write(JSON.stringify({"
        "di_undef:stdVonTag(di),di_385:stdVonTag(di,38.5),"
        "fr_undef:stdVonTag(fr),fr_385:stdVonTag(fr,38.5),"
        "sa:stdVonTag(sa,38.5),feiertag:stdVonTag(fl,38.5),"
        "di_tz:Math.round(stdVonTag(di,20)*10000)/10000,fr_tz:Math.round(stdVonTag(fr,20)*10000)/10000"
        "}));"
    )
    r = json.loads(run_node_snippet(node_exe, snippet))
    # Vollzeit + fehlend = exakt 8,5 / 4,5 / 0 (no-op-Beweis)
    assert r["di_undef"] == 8.5 and r["di_385"] == 8.5
    assert r["fr_undef"] == 4.5 and r["fr_385"] == 4.5
    assert r["sa"] == 0 and r["feiertag"] == 0
    # Teilzeit 20h: proportional (8,5*20/38,5=4,4156 ; 4,5*20/38,5=2,3377)
    assert r["di_tz"] == 4.4156 and r["fr_tz"] == 2.3377


def test_callers_pass_woche(index_html):
    # Writer + yearSt-Fallback + EntryRow nutzen _wocheOf
    assert "const _wocheOf=nm=>{const ks=kontingent[nm];const w=ks&&ks.woche;return (w&&w>0)?w:38.5;};" in index_html
    assert "hours:stdVonTag(d,_wocheOf(sel))" in index_html
    assert "parseFloat(v.hours)||stdVonTag(d,_wocheOf(m))" in index_html
