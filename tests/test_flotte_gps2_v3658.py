"""v3.9.658 Flotte GPS-Ausbau Teil 2 — Heading-Pfeil + Karten-Controls.

Marker-Label mit nach Fahrtrichtung rotiertem Pfeil (raw.course/heading), Karten-
Controls "Alle einpassen" + "Verlauf loeschen".
"""


def test_heading_arrow(index_html):
    assert "var _arrow=(_head!==null&&_head!==''&&!inactive)?('<span style=\"display:inline-block;transform:rotate('+Math.round(_head)+'deg)" in index_html
    # Pfeil kommt vor das Kennzeichen ins Label
    assert "nowrap\">'+_arrow+_esc(f.kennzeichen||'?')" in index_html


def test_trail_state(index_html):
    assert "const [trailFid,setTrailFid]=_react.useState.call(void 0, null)" in index_html
    # _showTrail merkt sich das Fahrzeug (seit v3.9.663 async, setTrailFid am Anfang vor dem on-demand-Fetch)
    assert "typeof L==='undefined')return;setTrailFid(fid);" in index_html


def test_clear_trail(index_html):
    assert "var _clearTrail=function(){" in index_html
    # v3.9.678: raeumt zusaetzlich das exakte "Status seit" weg — sonst zeigte die Liste
    # weiter den Zustandsbeginn aus einer Historie, die gar nicht mehr angezeigt wird.
    # v3.9.683: raeumt auch den Einzel-Fahrt-Trail weg — bewusst DERSELBE Aufraeum-Pfad,
    # damit es nicht zwei Wege gibt, die Karte in einen sauberen Zustand zu bringen.
    assert "setTrailFid(null);setTrailSeit(null);setFahrtTrail(false);};" in index_html


def test_fit_all(index_html):
    assert "var _fitAll=function(){var ap=fleet.filter(function(r){return r.p;})" in index_html


def test_controls_render(index_html):
    assert "h('button',{onClick:_fitAll," in index_html
    assert "'⌖ Alle'" in index_html
    # v3.9.683: der Button raeumt jetzt auch den Einzel-Fahrt-Trail weg und heisst dann "Fahrt ✕".
    assert "(trailFid||fahrtTrail)?h('button',{onClick:_clearTrail" in index_html
    assert "'Verlauf ✕'" in index_html
