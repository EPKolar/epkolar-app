"""v3.9.143 — Plan-Viewer: PDF-ready Render-Trigger (1-Seiten-PDFs rendern jetzt)."""


def test_pdf_ready_trigger(index_html):
    assert "const [_pdfReady, _setPdfReady] = _react.useState.call(void 0, 0);" in index_html
    assert "_setPdfReady(t=>t+1);/* v3.9.143" in index_html
    assert "}, [plan && plan.id, pageNum, scale, _isPdf, _pdfReady]);" in index_html
