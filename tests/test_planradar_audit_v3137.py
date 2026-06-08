"""v3.9.137 — Agententeam-Audit-Fixes (Auditor A+B) + Sync-Tier funktional."""


def test_mapplan_passes_intrinsic(index_html):
    # P1 (Auditor B): _mapPlan reicht page_count/intrinsic durch → Backfill-Guard greift nach Pull (kein Spam)
    assert "page_count:p.page_count!=null?p.page_count:1,intrinsic_w:p.intrinsic_w!=null?p.intrinsic_w:null,intrinsic_h:p.intrinsic_h!=null?p.intrinsic_h:null" in index_html


def test_backfill_waits_for_load(index_html):
    # P2: Backfill erst nach Load (pageCount echt, nicht Default 1)
    assert "if(!plan || !plan.id || !_isPdf || loading) return;/* v3.9.137 P2" in index_html


def test_ebene_edit_sets_gewerk(index_html):
    # P1 (Auditor B): Ebene-Edit setzt gewerk (kanonisch) + value gewerk||layer
    assert "value: ed.gewerk||ed.layer, onChange: e=>setEd(p=>({...p,layer:e.target.value,gewerk:e.target.value}))" in index_html
    # updateTicket PUT persistiert gewerk+layer
    # v3.9.180: updateTicket-Rewrite (Journal-Auto-Log) nutzt _u statt u; Ebene wird weiterhin persistiert.
    assert 'gewerk:_u.gewerk||_u.layer||"",layer:_u.layer||""' in index_html


def test_layerbar_count_uses_gewerk(index_html):
    # P2: Layer-Bar-Count konsistent mit Sichtbarkeit (gewerk||layer)
    assert "allTickets.filter(t=>(t.gewerk||t.layer)===l.id).length" in index_html


def test_sync_tier_functional(index_html):
    # "tier anpassen": orange-Stufe echt — Ticket-ID im Sync-Queue → orange Rand
    assert 'const _isUnsynced = (pendingIds && pendingIds.has && pendingIds.has(ticket.id)) || ticket.push_pending || ticket._offline;' in index_html
    assert "const [_pendingTicketIds,_setPendingTicketIds]=_react.useState.call(void 0, ()=>new Set());" in index_html
    assert "pendingIds: _pendingTicketIds," in index_html
    # v3.9.184: Signatur um Pin-Drag-Props erweitert (draggable, pctFromClient, onPinMove)
    assert "function PlanCanvasPinMarker({ticket, idx, isSelected, xPct, yPct, onClick, layers, monteure, zoom, pendingIds, draggable, pctFromClient, onPinMove})" in index_html
