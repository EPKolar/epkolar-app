"""v3.9.145 — Viewer-Ebenen-Zähler nutzen gewerk||layer (Codes), konsistent mit Pins/Liste."""


def test_no_raw_layer_count(index_html):
    # Kein roher t.layer===l.id mehr (Werte sind Codes wie "l1" → falsche Zähler)
    assert "allTickets.filter(t=>t.layer===l.id).length" not in index_html


def test_viewer_counts_use_gewerk(index_html):
    # Beide Viewer-Zähler (Ebenen-Leiste + Layer-Statistik) nutzen gewerk||layer
    assert index_html.count("allTickets.filter(t=>(t.gewerk||t.layer)===l.id).length") >= 2
