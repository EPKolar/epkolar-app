"""v3.9.141 — loadError: Render-Erfolg löscht Fehler + transientes 'not loaded' ignoriert."""


def test_render_success_clears_error(index_html):
    assert "setLoading(false);\n      setLoadError(null);/* v3.9.141" in index_html


def test_transient_not_loaded_ignored(index_html):
    assert 'if(!/not loaded/i.test(String(e&&e.message||e))) setLoadError("Plan-Render fehlgeschlagen: "+(e&&e.message||e));' in index_html
