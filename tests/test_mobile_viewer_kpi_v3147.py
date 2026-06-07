"""v3.9.165 — KPI-Karten im Plan-Viewer (Desktop+Mobile) ausblenden → Plan dominiert immersiv (PlanRadar-Benchmark).
(vorher v3.9.147: nur Mobile-Viewer; jetzt der ganze Viewer-Subview.)"""


def test_kpi_hidden_in_viewer(index_html):
    assert 'subView!=="viewer"&&React.createElement(\'div\', { className: "kpi-grid", style: {marginBottom:14}}' in index_html
