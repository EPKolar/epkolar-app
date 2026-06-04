"""v3.9.112 — Bug-Hunt Welle 2c: Übernacht-von/bis + Logout-Token-Fenster."""
import re
import json
from conftest import run_node_snippet


def _extract_fn(src, name):
    sig = "function " + name + "("
    start = src.index(sig)
    i = src.index("{", start)
    depth = 0
    while i < len(src):
        c = src[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return src[start:i + 1]
        i += 1
    raise AssertionError(name + " not found")


def test_wraphrs_behavior(node_exe, index_html):
    fn = _extract_fn(index_html, "_wrapHrs")
    snippet = fn + (
        "process.stdout.write(JSON.stringify(["
        "_wrapHrs('08:00','16:30'),"   # same-day 8.5h
        "_wrapHrs('22:00','06:00'),"   # overnight 8h
        "_wrapHrs('07:00','07:00'),"   # 0
        "_wrapHrs('06:00','14:30')"    # 8.5
        "]));"
    )
    res = json.loads(run_node_snippet(node_exe, snippet))
    assert res == [8.5, 8.0, 0.0, 8.5], f"_wrapHrs falsch: {res}"


def test_wraphrs_used_six_times(index_html):
    # 1 Definition + 6 Call-Sites = 7 Vorkommen von "_wrapHrs("
    assert index_html.count("_wrapHrs(") == 7, "alle 6 von/bis-Stunden-Berechnungen müssen _wrapHrs nutzen"
    assert 'new Date("2000-01-01T"+addBis)' not in index_html, "kein inline-Übernacht-bug-Pattern mehr"


def test_logout_nulls_token_before_fetch(index_html):
    body = _extract_fn(index_html, "_sbAuthLogout")
    # Token wird in _tok gekapselt und _authToken SOFORT genullt, DANN fetch mit _tok.
    i_capture = body.index("const _tok=_authToken;_authToken=null")
    i_fetch = body.index('fetch(_SB_AUTH+"/logout"')
    assert i_capture < i_fetch, "Token muss VOR dem Logout-fetch synchron genullt werden"
    assert '"Bearer "+_tok' in body, "Logout-fetch muss den gekapselten _tok nutzen"
