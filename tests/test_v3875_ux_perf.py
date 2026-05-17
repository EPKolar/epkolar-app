"""v3.8.75: UX-Perf-Fixes — myProjects more-indicator + Weather AbortController."""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'


def test_myprojects_more_indicator():
    """v3.8.75: myProjects.length>8 Conditional + 'weitere Projekte'-Hinweis."""
    text = INDEX.read_text(encoding='utf-8')
    cond_pattern = r'myProjects\.length>8\s*&&'
    assert re.search(cond_pattern, text), \
        'v3.8.75 Regression: myProjects.length>8-Conditional für More-Indicator fehlt'
    assert 'weitere Projekte' in text, \
        'v3.8.75 Regression: "weitere Projekte"-Label-String fehlt'


def test_weather_abort_controller():
    """v3.8.75: HomeView weather useEffect nutzt AbortController + cleanup + signal-Param."""
    text = INDEX.read_text(encoding='utf-8')
    # 1) AbortController instanziiert
    assert re.search(r'new AbortController\(\)', text), \
        'v3.8.75 Regression: new AbortController() im Weather-useEffect fehlt'
    # 2) Cleanup ruft _wCtrl.abort()
    assert re.search(r'_wCtrl\.abort\(\)', text), \
        'v3.8.75 Regression: _wCtrl.abort()-Cleanup im Weather-useEffect fehlt'
    # 3) fetchWeatherData hat signal-Parameter
    assert re.search(r'const fetchWeatherData\s*=\s*\(lat,\s*lon,\s*signal\)\s*=>', text), \
        'v3.8.75 Regression: fetchWeatherData(lat,lon,signal)-Signatur fehlt (signal-Param)'
