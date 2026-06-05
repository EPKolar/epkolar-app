"""v3.9.132 — PlanRadar Phase 1: is_pdf-Upload + gewerk/assignee-Konsolidierung (layer deprecated-kompat)."""


def test_is_pdf_on_upload(index_html):
    assert "uploaded_by:curUser.name,is_pdf:true}/* v3.9.132 P1a" in index_html
    assert "uploaded_by:curUser.name,is_pdf:false}/* v3.9.132 P1a" in index_html


def test_ticket_writer_populates_gewerk(index_html):
    # gewerk kanonisch zusätzlich befüllt; layer bleibt für Ebenen-Toggle-Kompat
    assert 'gewerk:ticket.gewerk||ticket.layer||"maengel"' in index_html
    assert 'layer:ticket.layer||"maengel"' in index_html  # layer NICHT entfernt


def test_readers_use_gewerk_fallback(index_html):
    # alle Layer-Reader nutzen gewerk||layer (alte + neue Tickets konsistent)
    assert "visibleLayers.includes(t.gewerk||t.layer)" in index_html
    assert "layers.find(l=>l.id===(ticket.gewerk||ticket.layer))" in index_html
    assert "(layers || []).find(l => l.id === (ticket.gewerk||ticket.layer))" in index_html
    assert index_html.count("layers.find(x=>x.id===(t.gewerk||t.layer))") == 2
