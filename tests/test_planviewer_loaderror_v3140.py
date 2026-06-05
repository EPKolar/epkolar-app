"""v3.9.140 — Plan-Viewer Lade-Fehler-Fallback (kein schwarzer Viewer mehr)."""


def test_load_error_state(index_html):
    assert "const [loadError, setLoadError] = _react.useState.call(void 0, null);" in index_html
    # Fehler in beiden Effekt-catches gesetzt + bei Neustart zurückgesetzt
    assert 'setLoadError("PDF konnte nicht geladen werden: "+(e&&e.message||e));' in index_html
    assert 'setLoadError("Plan-Render fehlgeschlagen: "+(e&&e.message||e));' in index_html
    assert "setLoadError(null); setLoading(true);" in index_html


def test_error_overlay_with_link(index_html):
    assert '"Plan konnte nicht angezeigt werden"' in index_html
    assert '"📄 Plan im neuen Tab öffnen"' in index_html
