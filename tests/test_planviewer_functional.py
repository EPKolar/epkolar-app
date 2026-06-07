"""v3.8.61 MEGA-C Phase 7.2: Plan-Viewer-Funktionalitaet."""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'


def test_planLoadPdf_accepts_data_blob_http():
    """_planLoadPdf muss data:/blob:/http(s):-URLs akzeptieren."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'async function _planLoadPdf[\s\S]{0,1500}?pdfjsLib\.getDocument', text)
    assert m
    body = m.group(0)
    assert 'data:' in body
    assert 'blob:' in body
    assert 'http:' in body or 'https:' in body


def test_planSrc_resolver_order():
    """_planSrc-Resolver muss Reihenfolge dataUrl → data_url → file_url haben."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'_planSrc\s*=\s*([^;]+);', text)
    assert m
    expr = m.group(1)
    # alle 3 müssen vorkommen, dataUrl vor file_url
    assert 'dataUrl' in expr
    assert 'data_url' in expr
    assert 'file_url' in expr
    assert expr.find('dataUrl') < expr.find('file_url'), 'dataUrl muss VOR file_url im Resolver kommen'


def test_isPdf_detection_handles_filename_and_url():
    """_isPdf detection muss filename ODER URL-Suffix prüfen."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'_isPdf\s*=\s*([^;]+);', text)
    assert m
    expr = m.group(1)
    assert 'application/pdf' in expr
    assert '.pdf' in expr  # filename oder URL-Suffix-Check


def test_planviewer_canvas_has_pageNum_state():
    text = INDEX.read_text(encoding='utf-8')
    assert '[pageNum, setPageNum]' in text


def test_planviewer_canvas_has_pinMode_prop():
    """PlanViewerCanvas muss pinMode als Prop nehmen."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'function PlanViewerCanvas\(\{([^}]+)\}\)', text)
    assert m
    assert 'pinMode' in m.group(1)


def test_ticketsOnPage_filters_plan_id_snake():
    """ticketsOnPage muss plan_id (snake) als Fallback haben."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'const ticketsOnPage[\s\S]{0,800}?\}\);', text)
    assert m
    body = m.group(0)
    assert 'plan_id' in body, 'snake-case plan_id Fallback muss existieren'


def test_ticketsOnPage_filters_page_with_default():
    """ticketsOnPage filtert page mit default 1 (für legacy tickets ohne page)."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'const ticketsOnPage[\s\S]{0,800}?\}\);', text)
    assert m
    body = m.group(0)
    assert '(t.page || 1)' in body or 'page||1' in body.replace(' ',''), 'page muss default 1 haben'


def test_pendingPin_uses_ternary_not_and_anti_pattern():
    """v3.8.56 Lehre: pendingPin-Render muss Ternary nutzen (kein && Anti-Pattern)."""
    text = INDEX.read_text(encoding='utf-8')
    # pendingPin-Confirm-Render muss Ternary (?...:null) nutzen, kein && -Anti-Pattern.
    # v3.9.168: Gate ist jetzt `pendingPin&&!newTicket?React.createElement` (Direkt-Flow blendet die Confirm-Bar
    # aus, sobald das Ticket-Formular offen ist) — weiterhin ein Ternary, daher Regex um die Bedingung erweitert.
    assert re.search(r'pendingPin(?:&&[^?{}]+)?\?React\.createElement', text), \
        'pendingPin-Render muss Ternary nutzen, kein &&-Anti-Pattern'
