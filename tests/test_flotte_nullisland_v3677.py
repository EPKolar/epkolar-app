"""v3.9.677 Flotte — Null-Island/NaN-Guards auf der Geo-Achse.

Eingefrorener WIP aus docs/wip/FLOTTE_GPS_WIP_2026-07.patch, jetzt angewandt.

Problem: die Koordinaten-Pruefungen deckten nur null/undefined ab. Ein Tracker ohne
GPS-Fix liefert 0/0 (Traccar-Default bei valid=false) — das ist Null-Island im Golf von
Guinea und zieht fitBounds quer ueber den Atlantik. NaN/Infinity wiederum lassen
L.marker([NaN,NaN]) werfen. Genau der Pilot-Fall: Tracker bootet, hat noch keinen Fix.

Die Zeitachse war laengst gegen NaN abgesichert (ts-Guards), die Geo-Achse nicht.
"""


def test_marker_verwirft_nullisland_und_nan(index_html):
    assert "if(!isFinite(_la)||!isFinite(_lo)||(_la===0&&_lo===0))return;" in index_html, (
        "Marker-Schleife muss 0/0 und NaN/Infinity verwerfen"
    )
    assert "var _la=Number(p.lat),_lo=Number(p.lon);" in index_html


def test_follow_zentriert_nicht_auf_muell(index_html):
    assert (
        "isFinite(Number(_fp.lat))&&isFinite(Number(_fp.lon))"
        "&&!(Number(_fp.lat)===0&&Number(_fp.lon)===0)"
    ) in index_html, "Live-Follow darf nicht auf Null-Island/NaN zentrieren"


def test_leer_banner_nennt_richtige_view(index_html):
    # Gelesen wird aus der View fz_latest (v3.9.663) — der Banner nannte noch fz_positions
    # und schickte den Leser damit zum falschen SQL-Skript.
    assert "View fz_latest fehlt — sql/GPS_LATEST_v1.sql" in index_html
    assert "fz_positions fehlt — sql/GPS_v1.sql ausführen" not in index_html
