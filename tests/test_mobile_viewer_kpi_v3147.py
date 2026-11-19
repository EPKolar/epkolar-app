"""v3.9.165 — KPI-Karten im Plan-Viewer (Desktop+Mobile) ausblenden → Plan dominiert immersiv (PlanRadar-Benchmark).
(vorher v3.9.147: nur Mobile-Viewer; jetzt der ganze Viewer-Subview.)"""


def test_kpi_hidden_in_viewer(index_html):
    # v1066 Stufe Planung: die Kacheln haengen zusaetzlich an der Breitenstufe (schmal: aufklappbar hinter
    # einer Zeile, mittel: kompakt). Die Aussage dieses Riegels bleibt: im Plan-Viewer gibt es KEINE Kacheln -
    # weder den Kachelblock noch die Aufklappzeile.
    assert 'subView!=="viewer"&&(!isMob||_plKpiAuf)&&React.createElement(\'div\', { className: "kpi-grid"+(_plStufe==="breit"?"":' in index_html
    assert 'subView!=="viewer"&&isMob&&React.createElement(\'button\', { type: "button", onClick: ()=>_plSetKpiAuf(v=>!v)' in index_html
