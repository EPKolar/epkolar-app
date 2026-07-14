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
    # v3.9.689: Die Ableitung liegt jetzt in der pure Funktion _fzFleetZeilen (Sentinel
    # //@FLOTTE-ROLLOUT) und zeigt ALLE Fahrzeuge, nicht nur die mit IMEI. In der Liste ist der
    # Status vierstufig (aktiv/inaktiv/wartet/kein_tracker) — faehrt/steht bleiben fuers Popup.
    assert "var fleet=_fzFleetZeilen(fahrzeuge,byId,_now2);" in index_html
    assert "var code=(st.code==='faehrt'||st.code==='steht')?'aktiv':st.code;" in index_html


def test_status_summary(index_html):
    # v3.9.689: vierstufig + "ohne Tracker"
    assert "_nAkt+' aktiv · '+_nInakt+' inaktiv · '+_nWart+' wartet'" in index_html


def test_toggle_button(index_html):
    # v3.9.689: zaehlt den ganzen Fuhrpark — vorher stand hier "Fahrzeuge (0)" neben 21 Autos.
    # v3.9.690: nur noch mobil (Desktop hat das Dreifenster-Layout ohne Toggle).
    assert "'🚐 Fahrzeuge ('+fahrzeuge.length+')'" in index_html


def test_listOpen_state(index_html):
    # Desktop offen, Handy zu
    assert "const [listOpen,setListOpen]=_react.useState.call(void 0, ww>=600)" in index_html
