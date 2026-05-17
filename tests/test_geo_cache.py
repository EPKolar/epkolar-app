"""v3.8.71 Hunt B-018: Geolocation sessionStorage-Cache (epk_geo).

Vermeidet Geo-Re-Prompt + 4s-Timeout pro HomeView-Mount.
Cache muss sowohl gelesen (getItem) als auch geschrieben (setItem) werden.
"""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'


def test_geo_cache_getItem_exists():
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'sessionStorage\.getItem\(\s*"epk_geo"\s*\)', text)
    assert m, (
        'v3.8.71 Hunt B-018 Regression: sessionStorage.getItem("epk_geo") fehlt — '
        'Geo-Cache wird nicht gelesen, jeder HomeView-Mount triggert Geo-Re-Prompt.'
    )


def test_geo_cache_setItem_exists():
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'sessionStorage\.setItem\(\s*"epk_geo"\s*,', text)
    assert m, (
        'v3.8.71 Hunt B-018 Regression: sessionStorage.setItem("epk_geo", ...) fehlt — '
        'Geo-Cache wird nicht geschrieben, Lookup ist sinnlos.'
    )
