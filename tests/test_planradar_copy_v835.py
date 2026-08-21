"""
PlanRadar Freundlichkeit (v3.9.835): interne Sie-Ansprache -> du, einladende Copy.

Der interne PlanRadar-Bereich siezte an drei Stellen, obwohl die App
Monteure/Bauleiter sonst durchgängig duzt. Register-Inkonsistenz behoben.
Das Kundenportal bleibt bewusst formell (Sie).
"""


def test_neue_freundliche_copy_da(index_html):
    assert "Noch kein Plan geöffnet" in index_html
    assert "Wähle oben einen Plan aus" in index_html
    assert "📌 Tippe auf den Plan – genau dort, wo das Ticket sitzen soll" in index_html
    assert "Wähle links ein Ticket – die Details erscheinen hier." in index_html


def test_interne_sie_ansprache_weg(index_html):
    # die konkreten formellen PlanRadar-Strings dürfen nicht mehr da sein
    assert "Bitte laden Sie einen Plan hoch oder wählen Sie einen aus" not in index_html
    assert "Klicken Sie auf den Plan um das Ticket zu platzieren" not in index_html


def test_kundenportal_bleibt_formell(index_html):
    # das Kundenportal spricht Kunden weiter mit Sie an (bewusst, nicht mitgeändert)
    assert "Melden Sie Mängel — wir kümmern uns darum" in index_html
