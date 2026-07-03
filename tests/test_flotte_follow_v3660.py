"""v3.9.660 Flotte Live-Follow — Karte re-zentriert auf ein verfolgtes Fahrzeug.

Follow-Toggle je Fleet-Zeile (⌖), Marker-Effect zentriert bei jedem Poll auf das
followId-Fahrzeug (statt fitBounds-Alle), "folgt: KZ ✕"-Indikator in den Controls.
"""


def test_follow_state(index_html):
    assert "const [followId,setFollowId]=_react.useState.call(void 0, null)" in index_html


def test_marker_effect_recenter(index_html):
    assert "if(followId){var _fp=byId[followId];if(_fp&&_fp.lat!=null&&_fp.lon!=null){try{_map.current.setView([_fp.lat,_fp.lon]);}" in index_html
    # sonst fitBounds-Alle
    assert "else if(pts.length){try{_map.current.fitBounds(pts," in index_html


def test_followId_in_deps(index_html):
    assert "},[st.positions,fahrzeuge.length,monteure.length,followId]);" in index_html


def test_row_follow_toggle(index_html):
    assert "setFollowId(function(cur){return (cur===row.f.id)?null:row.f.id;});" in index_html
    # stopPropagation, damit der Zeilen-Klick (_focus) nicht mitfeuert
    assert "ev.stopPropagation();" in index_html


def test_follow_indicator(index_html):
    assert "'⌖ folgt: '+((fahrzeuge.find(function(x){return x.id===followId;})||{}).kennzeichen||'?')" in index_html
