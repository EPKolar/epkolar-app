"""v3.9.656 Flotte GPS-Ausbau — strukturelle Verifikation.

Fahrer-Name je Fahrzeug (aus fahrzeuge.fahrer -> Monteur), angereichertes Popup
(Fahrer + Richtung/Heading aus raw), Verlaufs-Trail beim Klick. Render-Erweiterung.
"""


def test_monteure_prop(index_html):
    # v3.9.681: projects kam dazu (Projekt-Zuordnung im Fahrtenbuch). Assertion nicht mehr auf
    # die komplette Props-Liste im Wortlaut — sie bricht sonst bei jedem neuen Prop, ohne dass
    # sich am geprueften Verhalten etwas aendert.
    # v3.9.689: setFahrzeuge kam dazu (IMEI-Zuordnung inline im Fleet-Panel).
    # v3.9.1059: Flotte bekommt die Liste OHNE archivierte Fahrzeuge (fahrzeugeAktiv), setFahrzeuge bleibt der volle Zustand.
    # v3.9.1062: zusaetzlich fahrzeugeAlle - nur fuer das Fahrtenbuch (vergangene Fahrten archivierter Fahrzeuge)
    assert "React.createElement(FlotteView, { fahrzeuge: fahrzeugeAktiv, fahrzeugeAlle: fahrzeuge, setFahrzeuge: setFahrzeuge" in index_html
    assert "const monteure=props.monteure||[];" in index_html


def test_fahrer_helper(index_html):
    assert "const _fahrerName=f=>{if(!f||!f.fahrer)return '';var m=monteure.find(" in index_html


def test_fahrer_in_fleetliste(index_html):
    assert "_fahrerName(row.f)?h('div'" in index_html


def test_kompass_helper(index_html):
    # v1049 Re-Pin: der Kompass ist als pure Funktion _fzRichtung in //@FLOTTE-KARTE gewandert
    # (Node-getestet), der lokale _kompass in FlotteView ist entfernt.
    assert "var dirs=['N','NO','O','SO','S','SW','W','NW'];" in index_html
    assert "function _fzRichtung(grad){" in index_html


def test_popup_heading(index_html):
    # Heading/course aus raw in die Info-Karte (v1049: _fzHeading/_fzRichtungText)
    assert "_raw.course" in index_html and "FZ_RICHTUNG_LANG[_fzRichtung(g)]" in index_html
    assert "_infoZeile('Richtung',_fzRichtungText(p,now),'ri')" in index_html


def test_trail_polyline(index_html):
    assert "var _showTrail=function(fid){" in index_html
    assert "L.polyline(tp,{color:'#0ea5e9'" in index_html
    # Trail wird beim Fokus gezeichnet
    assert "_showTrail(row.f.id);_map.current.setView" in index_html
