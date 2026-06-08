"""v3.9.136 — PlanRadar Phase 2: Liste↔Plan-Sync (Auswahl zentriert Plan auf Pin)."""


def test_viewport_ref_and_centering_effect(index_html):
    assert "const viewportRef = _react.useRef.call(void 0, null);/* v3.9.136" in index_html
    assert "if(_lastCenteredRef.current === selectedTicket.id) return;" in index_html
    # v3.9.148 P1-Fix: flexOffset-korrekt → panX = baseWidth/2 - nx*W*zoom (war vw/2, miszentriert bei Zoom)
    assert "setPan({x: pageDims.baseWidth/2 - nx*pageDims.baseWidth*zoom, y: pageDims.baseHeight/2 - ny*pageDims.baseHeight*zoom});" in index_html
    # Seiten-Wechsel zuerst (v3.9.183: Seite auf [1, pageCount] geclampt — Ticket.page > pageCount zentrierte sonst leer)
    assert "const _pg = Math.min(Math.max(1, selectedTicket.page || 1), pageCount || 1);" in index_html
    assert "if(_pg !== pageNum) { setPageNum(_pg); return; }" in index_html
    # Effekt-Deps: ID/pageDims/pageNum + pageCount (v3.9.183: Clamp re-evaluiert sobald PDF-Seitenzahl bekannt)
    assert "}, [selectedTicket && selectedTicket.id, pageDims, pageNum, pageCount]);" in index_html


def test_viewport_ref_attached(index_html):
    assert 'React.createElement(\'div\', {ref: viewportRef, style: {flex: 1, position: "relative", overflow: "hidden"' in index_html
