"""v3.9.148 — Agententeam-Review-Fixes (P1 Zentrierung + P3 Layer-Filter)."""


def test_p1_centering_uses_basewidth(index_html):
    # flexOffset-korrekte Zentrierung: baseWidth/2 statt vw/2
    assert "setPan({x: pageDims.baseWidth/2 - nx*pageDims.baseWidth*zoom, y: pageDims.baseHeight/2 - ny*pageDims.baseHeight*zoom});" in index_html
    assert "vw/2 - nx*pageDims.baseWidth*zoom" not in index_html


def test_p3_filtered_tickets_gewerk(index_html):
    # Sidebar-Liste-Filter nutzt gewerk||layer
    assert 'if(filterLayer!=="alle"&&(t.gewerk||t.layer)!==filterLayer)return false;' in index_html


def test_p3_mx_baseline_gewerk(index_html):
    # Layer-Stat Balken-Baseline nutzt gewerk||layer
    assert "allTickets.filter(t=>(t.gewerk||t.layer)===x.id).length" in index_html
    assert "allTickets.filter(t=>t.layer===x.id).length" not in index_html
