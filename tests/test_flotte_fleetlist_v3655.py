"""v3.9.655 Flotte-Fleet-Liste — strukturelle Verifikation der UI-Verdrahtung.

Panel mit allen Tracker-Fahrzeugen (Status aktiv/inaktiv/wartet), Klick zentriert
die Karte + oeffnet Popup. Reine Render-Erweiterung von FlotteView.
"""


def test_marker_ref_gespeichert(index_html):
    # fahrzeug_id -> Marker fuer den Klick-Fokus
    assert "_markers.current[f.id]=m" in index_html
    assert "_markers.current={}" in index_html


def test_klick_fokus_setview(index_html):
    assert "_map.current.setView([row.p.lat,row.p.lon],15)" in index_html


def test_status_klassifizierung(index_html):
    # v3.9.678: die Inline-Ableitung ('wartet'|'inaktiv'|'aktiv') ist durch das pure
    # Status-Modell ersetzt — vier Zustaende (faehrt/steht/inaktiv/wartet) aus _fzStatus.
    # Die Klassifikation selbst ist jetzt in test_flotte_status_v3678.py getestet.
    assert "var stat=_fzStatus(p,_now2,seitExakt);" in index_html
    assert "status:stat.code,seit:stat.seit,dauerMin:stat.dauerMin" in index_html


def test_status_summary(index_html):
    assert "_nAkt+' fährt · '+_nSteht+' steht · '+_nInakt+' inaktiv · '+_nWart+' wartet'" in index_html


def test_toggle_button(index_html):
    assert "'Fahrzeuge ('+trackerFz.length+')'" in index_html


def test_listOpen_state(index_html):
    # Desktop offen, Handy zu
    assert "const [listOpen,setListOpen]=_react.useState.call(void 0, ww>=600)" in index_html
