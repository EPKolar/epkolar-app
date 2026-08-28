"""v3.9.140 — Plan-Viewer Lade-Fehler-Fallback (kein schwarzer Viewer mehr)."""


def test_load_error_state(index_html):
    assert "const [loadError, setLoadError] = _react.useState.call(void 0, null);" in index_html
    # Fehler in beiden Effekt-catches gesetzt + bei Neustart zurückgesetzt
    #
    # v3.9.890 NACHGEZOGEN - nicht abgeschwaecht: der Ladefehler unterscheidet jetzt
    # zwischen offline und echtem Fehler. "Failed to fetch" sagt dem Monteur im Keller
    # nichts - und weil die Plan-Kachel offline sichtbar ist (planData liegt im ODB),
    # fuehlte es sich wie ein Absturz an statt wie fehlendes Netz. Die EIGENSCHAFT,
    # die dieser Riegel seit v3.9.140 sichert (im catch wird ein Fehlerzustand
    # gesetzt statt schwarz zu bleiben), gilt unveraendert.
    assert 'navigator.onLine===false' in index_html, (
        "Der Ladefehler unterscheidet nicht mehr zwischen offline und echtem "
        "Fehler - dann steht im Keller wieder 'Failed to fetch'."
    )
    assert '"PDF konnte nicht geladen werden: "+(e&&e.message||e)' in index_html, (
        "Der technische Fehlertext ist weg - online braucht man ihn zur Diagnose."
    )
    assert 'nicht mitgenommen' in index_html, (
        "Die Offline-Meldung nennt nicht mehr, WAS zu tun ist."
    )
    assert 'setLoadError("Plan-Render fehlgeschlagen: "+(e&&e.message||e));' in index_html
    assert "setLoadError(null); setLoading(true);" in index_html


def test_error_overlay_with_link(index_html):
    assert '"Plan konnte nicht angezeigt werden"' in index_html
    assert '"📄 Plan im neuen Tab öffnen"' in index_html
