"""v3.9.134 — PlanRadar World-Container: CSS-Zoom statt pdf-Re-Render → Pins GPU-tracken, kein Drift."""


def test_css_zoom_state(index_html):
    assert "const [zoom, setZoom] = _react.useState.call(void 0, 1);/* v3.9.134 World-Container" in index_html


def test_world_div_transform(index_html):
    # translate(pan) scale(zoom) + transform-origin 0 0 → Pins (Kinder) GPU-getrackt
    assert 'transform: "translate(" + pan.x + "px, " + pan.y + "px) scale(" + zoom + ")", transformOrigin: "0 0"' in index_html


def test_pinch_and_buttons_use_css_zoom(index_html):
    # Pinch + Buttons ändern CSS-zoom, NICHT den pdf-Render-scale (kein async-Render-Drift)
    assert "setZoom(z => Math.max(0.4, Math.min(6, z * ratio)));" in index_html
    assert "setZoom(z => Math.max(0.4, z - 0.25))" in index_html
    assert "setZoom(z => Math.min(6, z + 0.25))" in index_html
    # die alte pdf-rerender-zoom-Logik ist weg
    assert "setScale(s => Math.max(0.5, Math.min(4, s * ratio)));" not in index_html
    assert 'Math.round(zoom * 100) + "%"' in index_html


def test_canvas_fixed_css_size(index_html):
    # Canvas auf feste CSS-Größe (baseWidth/baseHeight) → CSS-Zoom statt Bitmap-Größe
    assert 'width: (pageDims&&pageDims.baseWidth?pageDims.baseWidth+"px":"auto"), height: (pageDims&&pageDims.baseHeight?pageDims.baseHeight+"px":"auto")' in index_html


def test_nx_ny_canonical(index_html):
    # nx/ny ∈ 0..1 kanonisch (Brief): Writer persistiert, Render bevorzugt ×100
    assert "nx:(ticket.xPct!=null?ticket.xPct/100:null),ny:(ticket.yPct!=null?ticket.yPct/100:null)" in index_html
    assert "const _xPct = (t.nx!=null)?Number(t.nx)*100:" in index_html
    assert "const _yPct = (t.ny!=null)?Number(t.ny)*100:" in index_html


def test_pin_constant_screen_size(index_html):
    # scale(1/zoom) am Pin-Anker (Bottom-Center) → konstante Bildschirmgröße
    assert 'transform:"scale("+(1/(zoom||1))+")", transformOrigin:"50% 100%"' in index_html
    assert "function PlanCanvasPinMarker({ticket, idx, isSelected, xPct, yPct, onClick, layers, monteure, zoom})" in index_html


def test_pin_filter_not_pixel_only(index_html):
    # Pixel nicht mehr Pflicht: nx/ny ODER x_pct ODER Pixel
    assert "return (t.nx != null && t.ny != null) || (t.x_pct != null && t.y_pct != null) || (t.x != null && t.y != null);" in index_html
