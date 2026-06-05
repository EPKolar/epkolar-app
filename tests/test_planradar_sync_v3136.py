"""v3.9.136 — PlanRadar Phase 2: Liste↔Plan-Sync (Auswahl zentriert Plan auf Pin)."""


def test_viewport_ref_and_centering_effect(index_html):
    assert "const viewportRef = _react.useRef.call(void 0, null);/* v3.9.136" in index_html
    assert "if(_lastCenteredRef.current === selectedTicket.id) return;" in index_html
    # Zentrierungs-Formel: panX = vw/2 - nx*W*zoom
    assert "setPan({x: vw/2 - nx*pageDims.baseWidth*zoom, y: vh/2 - ny*pageDims.baseHeight*zoom});" in index_html
    # Seiten-Wechsel zuerst
    assert "if(_pg !== pageNum) { setPageNum(_pg); return; }" in index_html
    # Effekt-Deps: nur bei ID/pageDims/pageNum-Wechsel (nicht bei jedem zoom/pan)
    assert "}, [selectedTicket && selectedTicket.id, pageDims, pageNum]);" in index_html


def test_viewport_ref_attached(index_html):
    assert 'React.createElement(\'div\', {ref: viewportRef, style: {flex: 1, position: "relative", overflow: "hidden"' in index_html
