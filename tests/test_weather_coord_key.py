"""v3.8.72 Hunt B-013: Weather-Cache-Key enthält Lat/Lon-Koordinaten.

Vor dem Fix war der Cache-Key statisch — Cache-Hit bei jedem User unabhängig
vom Standort. Jetzt: cKey=`epk_weather_${_cLat}_${_cLon}` (Template-Literal).
"""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'


def test_weather_cKey_includes_lat_lon():
    text = INDEX.read_text(encoding='utf-8')
    # cKey=`epk_weather_${_cLat}_${_cLon}` — Template-Literal mit Koord-Interpolation
    m = re.search(
        r'cKey\s*=\s*`epk_weather_\$\{[^}]+\}_\$\{[^}]+\}`',
        text,
    )
    assert m, (
        'v3.8.72 Hunt B-013 Regression: cKey=`epk_weather_${lat}_${lon}` '
        'Template-Literal mit Koord-Interpolation fehlt — Cache liefert Daten anderer Standorte.'
    )
