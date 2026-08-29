"""v3.9.129 — Welle 7 (Finder O Modal-Keyboard/Scroll + P Rechen-P3). Finder N: keine Funde (Code defensiv)."""
from _hilfen import nur_code


def test_qr_popup_esc_scrolllock(index_html):
    # O-P2: QR-Popup war Fullscreen-Overlay ohne Esc/Scroll-Lock
    assert 'if(!asShowQR)return;try{_scrollLock.acquire();}catch(_){}const _h=e=>{if(e.key==="Escape")setAsShowQR(null);}' in index_html


def test_vzeit_addday_esc_scrolllock(index_html):
    # O-P2: VZeit-Eintrag-Modal hatte keinen Esc-Handler (16285-Effect gehört zu anderem addDay)
    assert 'if(!addDay)return;try{_scrollLock.acquire();}catch(_){}const _h=e=>{if(e.key==="Escape")setAddDay(null);}' in index_html


def test_pvorder_and_zeit_scrolllock(index_html):
    """v3.9.905 NACHGEZOGEN. Hier stand:

        assert index_html.count('O-P3: Scroll-Lock') == 2

    Eine Zaehlung auf einem KOMMENTAR. Sie waere angeschlagen, sobald jemand den
    Erklaertext umformuliert - und gruen geblieben, wenn jemand den Scroll-Lock
    entfernt und den Kommentar stehenlaesst. Genau die falsche Richtung.

    Gemessen wird jetzt kommentarblind der Code selbst, je Modal die ganze Kette
    aus Sperre und Esc-Behandlung. Damit ist zusaetzlich belegt, dass die Sperre
    VOR dem richtigen Handler sitzt und nicht irgendwo sonst in der Datei."""
    code = nur_code(index_html)
    ketten = {
        "Preisvergleich":
            'try{_scrollLock.acquire();}catch(_){}const _h=e=>{'
            'if(e.key==="Escape"){e.preventDefault();'
            'setPvOrder(null);setPvPositionen([]);}};',
        "Zeit-Eintrag":
            'try{_scrollLock.acquire();}catch(_){}const _h=e=>{'
            'if(e.key==="Escape"){e.preventDefault();setAddDay(null);}};',
    }
    for name, kette in ketten.items():
        n = code.count(kette)
        assert n == 1, (
            "Das %s-Modal sperrt das Hintergrund-Scrollen nicht mehr unmittelbar "
            "vor seiner Esc-Behandlung (%d Treffer statt 1)." % (name, n)
        )


def test_absview_monthstat_local_parse(index_html):
    # P-P3: UTC-Parse kippte Monatsersten in den Vormonat
    assert 'const d=new Date(dateStr+"T00:00:00");/* v3.9.129 P-P3' in index_html


def test_dashboard_hours_stunden_fallback(index_html):
    # P-P3: Dashboard unterzählte Projektstunden bei .stunden-only-Shape
    assert 's+(parseFloat(x.hours||x.stunden)||0),0);/* v3.9.129 P-P3' in index_html
