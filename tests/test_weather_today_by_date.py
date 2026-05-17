"""v3.8.72 Hunt B-002: Wetter-"Heute"-Markierung über Datum statt Index.

Vor dem Fix wurde isToday über i===0 bestimmt — bei API-Antworten die nicht mit
heute starten (z.B. nach Mitternacht / Cache-Stale) wurde der falsche Tag markiert.
Jetzt: isToday=d===_todayStr (echter Datums-Vergleich).
"""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'


def test_weather_isToday_uses_date_compare():
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'isToday\s*=\s*d\s*===\s*_todayStr', text)
    assert m, (
        'v3.8.72 Hunt B-002 Regression: isToday=d===_todayStr fehlt — '
        '"Heute"-Markierung im Wetter-Strip basiert wieder auf Array-Index (i===0) '
        'und ist nach Mitternacht / Cache-Stale falsch.'
    )


def test_weather_isToday_not_via_index_zero_in_live_render():
    """Negativ-Guard: isToday im LIVE-Wetter-Render darf nicht via i===0.

    Hinweis: Der Offline-Fallback `wFallback` darf weiterhin `i===0` nutzen,
    weil er die 7 Tage SELBST ab `new Date()` generiert (Index 0 = wirklich Heute).
    Daher prüfen wir nur den Block der `weather.daily.time` mappt.
    """
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(
        r'weather\.daily,\s*\'optionalAccess\',\s*_\d+\s*=>\s*_\d+\.time\][\s\S]{0,400}?isToday\s*=\s*i\s*===\s*0',
        text,
    )
    assert not m, (
        'v3.8.72 Hunt B-002 Regression: isToday=i===0 ist im LIVE Wetter-Render zurück — '
        'muss Datum (d===_todayStr) statt Array-Index nutzen.'
    )
