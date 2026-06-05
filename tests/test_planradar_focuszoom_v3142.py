"""v3.9.142 — PlanRadar Phase 3: Fokuspunkt-Zoom (Pinch-Midpoint fix + Button-Zentrum)."""


def test_pinch_focus_point(index_html):
    # Pinch-Midpoint bleibt fix: panX = fx-(fx-panX)*r
    assert "const _mx=(pts[0].x+pts[1].x)/2, _my=(pts[0].y+pts[1].y)/2;" in index_html
    assert "setPan(pp=>({x:_fx-(_fx-pp.x)*r, y:_fy-(_fy-pp.y)*r}));return nz;});" in index_html


def test_buttons_zoom_center(index_html):
    assert "const _zoomCenter = (delta) => {" in index_html
    assert "const _fx = _vr ? _vr.width/2 : 0, _fy = _vr ? _vr.height/2 : 0;" in index_html
    assert 'onClick: () => _zoomCenter(-0.25), title: "Zoom raus"' in index_html
    assert 'onClick: () => _zoomCenter(0.25), title: "Zoom rein"' in index_html
