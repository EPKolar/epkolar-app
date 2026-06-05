"""v3.9.129 — Welle 7 (Finder O Modal-Keyboard/Scroll + P Rechen-P3). Finder N: keine Funde (Code defensiv)."""


def test_qr_popup_esc_scrolllock(index_html):
    # O-P2: QR-Popup war Fullscreen-Overlay ohne Esc/Scroll-Lock
    assert 'if(!asShowQR)return;try{_scrollLock.acquire();}catch(_){}const _h=e=>{if(e.key==="Escape")setAsShowQR(null);}' in index_html


def test_vzeit_addday_esc_scrolllock(index_html):
    # O-P2: VZeit-Eintrag-Modal hatte keinen Esc-Handler (16285-Effect gehört zu anderem addDay)
    assert 'if(!addDay)return;try{_scrollLock.acquire();}catch(_){}const _h=e=>{if(e.key==="Escape")setAddDay(null);}' in index_html


def test_pvorder_and_zeit_scrolllock(index_html):
    # O-P3: Scroll-Lock in die bestehenden Esc-Effekte ergänzt
    assert index_html.count('O-P3: Scroll-Lock') == 2


def test_absview_monthstat_local_parse(index_html):
    # P-P3: UTC-Parse kippte Monatsersten in den Vormonat
    assert 'const d=new Date(dateStr+"T00:00:00");/* v3.9.129 P-P3' in index_html


def test_dashboard_hours_stunden_fallback(index_html):
    # P-P3: Dashboard unterzählte Projektstunden bei .stunden-only-Shape
    assert 's+(parseFloat(x.hours||x.stunden)||0),0);/* v3.9.129 P-P3' in index_html
