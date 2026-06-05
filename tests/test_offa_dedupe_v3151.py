"""v3.9.151 — OFFA-Import-Dedupe case-insensitiv (Agent-Fund)."""


def test_offa_dedupe_case_insensitive(index_html):
    assert 'const existing=arbeitsscheine.find(a=>(a.nummer||"").toUpperCase()===(parsed.nummer||"").toUpperCase());' in index_html
    assert "const existing=arbeitsscheine.find(a=>a.nummer===parsed.nummer);" not in index_html
