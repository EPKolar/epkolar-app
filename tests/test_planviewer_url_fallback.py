"""v3.8.56: PlanViewerCanvas akzeptiert file_url + _planLoadPdf https-Support."""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'

def test_planLoadPdf_accepts_https():
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'async function _planLoadPdf\(planId,\s*dataUrl\)\s*\{(.*?)\nconst pdf = await window\.pdfjsLib', text, re.DOTALL)
    if not m:
        m = re.search(r'async function _planLoadPdf[^{]*\{((?:[^{}]|\{[^{}]*\})*?)pdfjsLib\.getDocument', text, re.DOTALL)
    assert m
    body = m.group(1)
    assert 'http:' in body or 'https:' in body, '_planLoadPdf muss http(s):-URL akzeptieren'

def test_planviewer_uses_planSrc_resolver():
    text = INDEX.read_text(encoding='utf-8')
    assert '_planSrc' in text, '_planSrc-Resolver muss existieren'
    m = re.search(r'_planSrc\s*=\s*([^;]+);', text)
    assert m
    assert 'file_url' in m.group(1), '_planSrc muss file_url als Fallback haben'
