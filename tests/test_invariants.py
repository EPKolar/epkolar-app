"""Static invariants about the index.html shape."""


def test_index_exists(index_html):
    assert len(index_html) > 0


def test_index_size_plausible(index_html):
    # Single-file app, expected ~16k+ lines
    lines = index_html.count("\n")
    assert 10_000 < lines < 50_000, f"index.html has {lines} lines, expected 10k-50k"


def test_index_doctype(index_html):
    assert index_html.lstrip().startswith("<!DOCTYPE html>")


def test_index_german_lang(index_html):
    assert 'lang="de"' in index_html[:500]


def test_bracket_baseline(index_html):
    opens = {"(": 0, "{": 0, "[": 0}
    closes = {")": 0, "}": 0, "]": 0}
    for c in index_html:
        if c in opens:
            opens[c] += 1
        elif c in closes:
            closes[c] += 1
    paren = opens["("] - closes[")"]
    brace = opens["{"] - closes["}"]
    bracket = opens["["] - closes["]"]
    # Baseline per project convention: () -2 from JSX-ish string content
    assert (paren, brace, bracket) == (-2, 0, 0), f"bracket drift: ()={paren} {{}}={brace} []={bracket}"
