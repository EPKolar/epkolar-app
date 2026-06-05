"""v3.9.144 — Notification-Klick navigiert (n.link ODER aus NOTIF_TYPES[type].cat abgeleitet)."""


def test_notif_click_navigates_by_cat(index_html):
    assert 'const _catTab={projekte:"projekte",arbeitsscheine:"arbeitsscheine",urlaub:"urlaub",werkzeuge:"werkzeuge",material:"projekte",kunden:"arbeitsscheine"};' in index_html
    # v3.9.149: _typeTab-Override (deadline_fz) vor cat-Lookup
    assert 'const _tgt=n.link||_typeTab[n.type]||((NOTIF_TYPES[n.type]||{}).cat&&_catTab[(NOTIF_TYPES[n.type]||{}).cat]);' in index_html
    assert "if(_tgt){const ti=tabs.findIndex(t=>t.perm===_tgt);if(ti>=0)setKat(ti);" in index_html
