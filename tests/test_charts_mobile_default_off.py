"""v3.8.69 Hunt B-024: Charts default OFF auf Mobile (Perf-Schutz).

dv("charts") muss auf isMob && dashVis[k]===undefined explizit false zurückgeben,
sonst lädt der Chart-Block ungefragt auf jedem Mobile-Device und blockt die UI.
"""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'


def test_dv_function_exists():
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'const\s+dv\s*=\s*\(k\)\s*=>\s*\{', text)
    assert m, 'dv=(k)=>{ helper fehlt — v3.8.69 Hunt B-024 Regression'


def test_dv_charts_mobile_default_off():
    text = INDEX.read_text(encoding='utf-8')
    # dv=(k)=>{ ... if(k==="charts" && dashVis[k]===undefined && isMob) return false; ... }
    m = re.search(
        r'const\s+dv\s*=\s*\(k\)\s*=>\s*\{[\s\S]{0,400}?'
        r'k\s*===\s*"charts"[\s\S]{0,200}?dashVis\[k\]\s*===\s*undefined[\s\S]{0,200}?isMob[\s\S]{0,200}?return\s+false',
        text,
    )
    assert m, (
        'v3.8.69 Hunt B-024 Regression: dv("charts") muss auf Mobile '
        'default false zurückgeben wenn dashVis[k]===undefined (Perf-Schutz, 14k Iterations × 60s-Tick).'
    )
