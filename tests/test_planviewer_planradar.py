"""v3.8.55 PlanRadar-Style Plan-Viewer."""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'

def test_pdf_load_helper_exists():
    assert 'async function _planLoadPdf' in INDEX.read_text(encoding='utf-8')

def test_pdf_render_page_helper_exists():
    assert 'async function _planRenderPage' in INDEX.read_text(encoding='utf-8')

def test_pdf_thumbnail_helper_exists():
    assert 'async function _planRenderThumbnail' in INDEX.read_text(encoding='utf-8')

def test_planviewer_canvas_component_exists():
    assert 'function PlanViewerCanvas(' in INDEX.read_text(encoding='utf-8')

def test_planthumbnail_component_exists():
    assert 'function PlanThumbnail(' in INDEX.read_text(encoding='utf-8')

def test_pinmode_workflow_pendingpin():
    text = INDEX.read_text(encoding='utf-8')
    assert 'pendingPin' in text or 'pendingPosition' in text, 'Pin-Vorschau-State (pendingPin) muss existieren'

def test_pinch_zoom_implementation():
    text = INDEX.read_text(encoding='utf-8')
    assert 'pointersRef' in text or 'pinchDist' in text.lower(), 'Pinch-Zoom-Logik muss existieren'

def test_old_planviewer_not_called():
    """Stellt sicher dass die alte <embed>-basierte PlanViewer-Komponente nicht mehr aus VPlan
    aufgerufen wird (PlanViewerCanvas hat sie ersetzt). Die alte Komponente bleibt als
    dead code im File — Removal ist out-of-scope, riskant. Statt String-Existenz pruefen
    wir dass kein React.createElement(PlanViewer, ...) mehr existiert."""
    text = INDEX.read_text(encoding='utf-8')
    assert 'React.createElement(PlanViewer,' not in text, \
        'Alte <embed>-PlanViewer wird noch aufgerufen — VPlan muss PlanViewerCanvas nutzen'
    assert 'React.createElement(PlanViewerCanvas,' in text, \
        'Neue PlanViewerCanvas-Komponente muss von VPlan aufgerufen werden'

def test_pin_overlay_uses_percentage():
    text = INDEX.read_text(encoding='utf-8')
    assert 'xPct' in text, 'Pin-Position muss in Prozent (xPct) gespeichert werden, scale-unabhaengig'
