"""v3.8.56: PlanViewerCanvas akzeptiert file_url + _planLoadPdf https-Support."""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'

def test_planLoadPdf_accepts_https():
    text = INDEX.read_text(encoding='utf-8')
    # v3.9.890: Beide bisherigen Ausdruecke waren sproede. Der erste verlangte
    # "\nconst pdf" OHNE Einrueckung und hat deshalb nie getroffen; gegriffen hat
    # immer der Rueckfall - und der erlaubt nur EINE Klammerebene, scheiterte also,
    # sobald der Rumpf ein if/else bekam. Jetzt strukturell: vom Funktionsanfang bis
    # zum ersten getDocument, ohne Laengen- und ohne Klammergrenze. Die Aussage des
    # Riegels (der Rumpf akzeptiert http(s)) ist unveraendert.
    m = re.search(r'async function _planLoadPdf[^{]*\{([\s\S]*?)pdfjsLib\.getDocument', text)
    assert m, "_planLoadPdf oder sein getDocument-Aufruf nicht gefunden"
    assert 'async function' not in m.group(1), (
        "Der Fang reicht ueber das Funktionsende hinaus - _planLoadPdf ruft "
        "getDocument dann gar nicht mehr selbst auf."
    )
    body = m.group(1)
    assert 'http:' in body or 'https:' in body, '_planLoadPdf muss http(s):-URL akzeptieren'

def test_planviewer_uses_planSrc_resolver():
    text = INDEX.read_text(encoding='utf-8')
    assert '_planSrc' in text, '_planSrc-Resolver muss existieren'
    m = re.search(r'_planSrc\s*=\s*([^;]+);', text)
    assert m
    assert 'file_url' in m.group(1), '_planSrc muss file_url als Fallback haben'
