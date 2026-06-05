"""v3.9.147 — Mobil-UX: KPI-Karten im Plan-Viewer ausblenden (Plan war unter dem Fold)."""


def test_kpi_hidden_on_mobile_viewer(index_html):
    assert '!(isMob&&subView==="viewer")&&React.createElement(\'div\', { className: "kpi-grid", style: {marginBottom:14}}' in index_html
