"""
Freundlichkeit / Copy-Audit (v3.9.838): interne Sie-Ansprache -> du + Leerzustände.

Die App duzt Monteure/Bauleiter durchgängig; einige interne Stellen siezten noch
(Bautagebuch, Fotos, Monatszettel, DATANORM, PWA-Install, Passwort-Reset). Zwei
Sackgassen-Leerzustände wurden zu Einladungen. Das Kundenportal bleibt formell.
"""


def test_du_ansprache_da(index_html):
    for s in [
        "Dokumentiere die Tagesarbeit auf der Baustelle.",
        "Erstelle den ersten Tagesbericht für dieses Projekt.",
        "Nutze den Button oben, um Fotos aufzunehmen.",
        "Gib deinen Benutzernamen ein.",
        "Installiere EP Kolar als App auf deinem Handy",
        "Installiere EP Kolar als eigenständige App",
    ]:
        assert s in index_html, f"du-Form fehlt: {s!r}"


def test_leerzustaende_einladend(index_html):
    assert "Noch keine Bauprovisorien erfasst. Lege oben das erste an." in index_html
    assert "Noch keine Zeiten erfasst. Sobald du Stunden buchst, erscheinen sie hier." in index_html


def test_cache_jargon_weg(index_html):
    # "Cache leeren empfohlen" (Toast) -> "Speicher freigeben empfohlen"
    assert "Speicher freigeben empfohlen" in index_html
    assert "Cache leeren empfohlen" not in index_html


def test_kundenportal_bleibt_formell(index_html):
    # Kundenportal-Hilfetexte siezen bewusst weiter (nicht mitgeändert)
    assert "Melden Sie Mängel — wir kümmern uns darum" in index_html
    assert "Bei Fragen erreichen Sie uns jederzeit unter dem Reiter " in index_html
