"""v3.9.667 AS-Eskalation NaN-Guard (Bug-Hunt-Subagent).

War a.aufgenommen leer (JUPROWA-Zeile mit leerem AK_ANLAGE_DATZEIT), ergab
new Date("T08:00") ein Invalid Date (NaN) → hAlt/dAlt NaN → Eskalation + 24h-Reminder
fuer den dringenden Schein feuerten NIE (still). Fallback auf created_at, sonst skip.
"""


def test_ts_fallback(index_html):
    assert 'const _asTsRaw=(a.aufgenommen&&String(a.aufgenommen).trim())?(a.aufgenommen+"T"+(a.aufgZeit||"08:00")):(a.created_at||a.createdAt||"");' in index_html


def test_nan_guard_skips(index_html):
    assert "const aufg=new Date(_asTsRaw).getTime();\n      if(isNaN(aufg))return;" in index_html


def test_alte_ungeschuetzte_variante_weg(index_html):
    assert 'const aufg=new Date(a.aufgenommen+"T"+(a.aufgZeit||"08:00")).getTime();' not in index_html
