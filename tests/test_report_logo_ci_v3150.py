"""v3.9.150 — CI: echtes EP-Kolar-Logo im Bericht-Export (RB/Regiebericht + Formulare)."""


def test_report_header_uses_logo_image(index_html):
    # Header zeigt das Logo-Bild (LOGO_MD), nicht nur grünen Text
    assert '<div class="hdr"><div class="logo"><img src="${LOGO_MD}" alt="EP: Kolar & Sohn"/><small>' in index_html
    # CSS für das Logo-Bild
    assert ".logo img{height:46px;width:auto;display:block;margin-bottom:3px}" in index_html


def test_old_text_only_logo_gone(index_html):
    # die reine Text-Variante im Header ist weg
    assert '<div class="logo">EP: Kolar &amp; Sohn<small>Der Haustechnikprofi' not in index_html
