"""v3.9.656 Flotte GPS-Ausbau — strukturelle Verifikation.

Fahrer-Name je Fahrzeug (aus fahrzeuge.fahrer -> Monteur), angereichertes Popup
(Fahrer + Richtung/Heading aus raw), Verlaufs-Trail beim Klick. Render-Erweiterung.
"""


def test_monteure_prop(index_html):
    # v3.9.681: projects kam dazu (Projekt-Zuordnung im Fahrtenbuch). Assertion nicht mehr auf
    # die komplette Props-Liste im Wortlaut — sie bricht sonst bei jedem neuen Prop, ohne dass
    # sich am geprueften Verhalten etwas aendert.
    # v3.9.689: setFahrzeuge kam dazu (IMEI-Zuordnung inline im Fleet-Panel).
    assert "React.createElement(FlotteView, { fahrzeuge: fahrzeuge, setFahrzeuge: setFahrzeuge" in index_html
    assert "const monteure=props.monteure||[];" in index_html


def test_fahrer_helper(index_html):
    assert "const _fahrerName=f=>{if(!f||!f.fahrer)return '';var m=monteure.find(" in index_html


def test_fahrer_in_fleetliste(index_html):
    assert "_fahrerName(row.f)?h('div'" in index_html


def test_kompass_helper(index_html):
    assert "const _kompass=d=>{var dirs=['N','NO','O','SO','S','SW','W','NW'];" in index_html


def test_popup_heading(index_html):
    # Heading/course aus raw ins Popup
    assert "_raw.course" in index_html and "_kompass(_head)" in index_html


def test_trail_polyline(index_html):
    assert "var _showTrail=function(fid){" in index_html
    assert "L.polyline(tp,{color:'#0ea5e9'" in index_html
    # Trail wird beim Fokus gezeichnet
    assert "_showTrail(row.f.id);_map.current.setView" in index_html
