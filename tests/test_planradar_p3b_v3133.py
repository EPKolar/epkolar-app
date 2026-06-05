"""v3.9.133 — PlanRadar Phase 3b: Pin-Position kanonisch %% (x_pct/y_pct) mit Pixel-Fallback."""


def test_pin_writes_pct(index_html):
    assert "xPct:pendingPin.xPct,yPct:pendingPin.yPct" in index_html  # confirmPendingPin führt %% mit
    assert "x_pct:(ticket.xPct!=null?ticket.xPct:null),y_pct:(ticket.yPct!=null?ticket.yPct:null)" in index_html  # POST persistiert


def test_render_prefers_pct_with_fallback(index_html):
    # v3.9.134: nx/ny kanonisch vorangestellt; x_pct bleibt Fallback in der Kette
    assert "(t.x_pct!=null)?Number(t.x_pct):(t.xPct!=null?Number(t.xPct):(pageDims && pageDims.baseWidth ? (t.x / pageDims.baseWidth * 100) : 0))" in index_html
    assert "(t.y_pct!=null)?Number(t.y_pct):(t.yPct!=null?Number(t.yPct):(pageDims && pageDims.baseHeight ? (t.y / pageDims.baseHeight * 100) : 0))" in index_html
