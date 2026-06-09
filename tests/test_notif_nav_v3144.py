"""v3.9.144 — Notification-Klick navigiert (n.link ODER aus NOTIF_TYPES[type].cat abgeleitet)."""


def test_notif_click_navigates_by_cat(index_html):
    assert 'const _catTab={projekte:"projekte",arbeitsscheine:"arbeitsscheine",urlaub:"urlaub",werkzeuge:"werkzeuge",material:"projekte",kunden:"arbeitsscheine"};' in index_html
    # v3.9.220 #4: _typeTab ZUERST (deadline_fz→fahrzeuge), dann _catTab[n.link] (material→projekte, kunden→arbeitsscheine),
    # dann NOTIF_TYPES.cat, dann n.link als letzter Fallback. Vorher short-circuitete n.link="system" den Fahrzeug-Sprung.
    assert 'const _tgt=_typeTab[n.type]||_catTab[n.link]||((NOTIF_TYPES[n.type]||{}).cat&&_catTab[(NOTIF_TYPES[n.type]||{}).cat])||n.link;' in index_html
    assert "if(_tgt){const ti=tabs.findIndex(t=>t.perm===_tgt);if(ti>=0)setKat(ti);" in index_html
