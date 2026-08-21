"""
Swipe im Browser — overscroll-behavior-x (v3.9.834, KORREKTUR zu v825).

Reproduktions-Harnisch: die useSwipe-Logik feuert bei sauberen Touch-Events
korrekt. Der Fehler lag in der Event-Zustellung — im Browser-Tab fing die
horizontale Browser-„Wisch-zurück"-Navigation die Geste ab (touchcancel statt
touchend). Diese Geste steuert `overscroll-behavior-x`, NICHT `touch-action`.
html/body hatten nur `overscroll-behavior-y:contain`; jetzt beide Achsen.
"""


def test_html_overscroll_beide_achsen(index_html):
    assert "html { overscroll-behavior: contain; }" in index_html, (
        "html overscroll-behavior nicht auf beide Achsen (x fehlt -> Browser-Wisch-Navigation fängt die Geste)"
    )


def test_body_overscroll_beide_achsen(index_html):
    assert "body{overscroll-behavior:contain;" in index_html, (
        "body overscroll-behavior nicht auf beide Achsen"
    )


def test_kein_nur_y_mehr_auf_den_wurzeln(index_html):
    # die frühere -y-only-Form darf auf html/body nicht mehr stehen
    assert "html { overscroll-behavior-y: contain; }" not in index_html
    assert "body{overscroll-behavior-y:contain;" not in index_html


def test_touch_action_pan_y_bleibt(index_html):
    # v825 touch-action bleibt (Scroll-Hijack-Schutz), war aber nicht die Ursache
    assert "touchAction:\"pan-y\"" in index_html or "touch-action:pan-y" in index_html
