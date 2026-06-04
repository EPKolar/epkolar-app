"""v3.9.113 — Mobile: WeekPlan KW-Navigationszeile bricht die Seite nicht mehr quer auf.

Die KW-Sprung-Buttons (savedKws) lagen in einer nicht-umbrechenden flex-Zeile → bei vielen
gespeicherten KWs lief die Zeile über den Viewport hinaus (671px @ 390 Viewport) und brach
die ganze Planung-Seite horizontal auf. Fix: flexWrap auf der KW-Nav-Zeile.
"""
import re


def test_weekplan_kw_nav_row_wraps(index_html):
    # Die flex-Zeile direkt vor dem switchKw(kw-1)-Button muss flexWrap:"wrap" haben
    # (Kommentar + Zeilenumbruch zwischen Style und Button erlaubt).
    m = re.search(
        r'\{display:"flex",alignItems:"center",gap:8,flexWrap:"wrap"\}\}[\s\S]{0,400}?switchKw\(Math\.max\(1,kw-1\)\)',
        index_html,
    )
    assert m, (
        "WeekPlan KW-Navigationszeile muss flexWrap:'wrap' haben (KW-Sprung-Buttons brachen sonst "
        "die Seite quer auf)"
    )
