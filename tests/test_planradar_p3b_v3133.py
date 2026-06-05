"""v3.9.133 — PlanRadar Phase 3b: Pin-Position kanonisch %% (x_pct/y_pct) mit Pixel-Fallback."""


def test_pin_writes_pct(index_html):
    assert "xPct:pendingPin.xPct,yPct:pendingPin.yPct" in index_html  # confirmPendingPin führt %% mit
    assert "project_id:p.id,x:ticket.x||0,y:ticket.y||0/* v3.9.136" in index_html  # POST: x/y sind %


def test_render_prefers_pct_with_fallback(index_html):
    # v3.9.136: x/y SIND Prozent (Chat-Claude live-DB) — direkt als %
    assert "const _xPct = (t.x!=null)?Number(t.x):0;" in index_html
    assert "const _yPct = (t.y!=null)?Number(t.y):0;" in index_html
