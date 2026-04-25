"""v3.8.53: PDF-Blob-URL Helper (Chrome-Block-Workaround)."""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'

def test_pdf_helper_exists():
    assert 'function _pdfDataUrlToBlobUrl' in INDEX.read_text(encoding='utf-8')

def test_pdf_helper_uses_blob_api():
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'function _pdfDataUrlToBlobUrl\(dataUrl\)\{(.*?)\n\}', text, re.DOTALL)
    assert m
    body = m.group(1)
    assert 'URL.createObjectURL' in body
    assert 'new Blob' in body
    assert 'atob' in body

def test_plan_viewer_uses_blob_helper():
    assert '_pdfBlobUrlForPlan(plan)' in INDEX.read_text(encoding='utf-8')

def test_blob_cache_revoked_on_unmount():
    text = INDEX.read_text(encoding='utf-8')
    assert 'URL.revokeObjectURL' in text
    assert '_pdfBlobCache' in text
