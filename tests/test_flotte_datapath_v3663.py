"""v3.9.663 Flotte-Datenpfad-Hardening (Bug-Hunt-Subagent, Traccar-Vorbereitung).

#1 Marker/Fleet aus View fz_latest (1 Zeile je fahrzeug_id) statt globalem limit=200
   (Fahrzeuge verschwanden sobald mehrere Tracker pingen).
#2 Offenes Popup wird nach dem 60s-Marker-Neuaufbau wiederhergestellt (autoPan aus).
#3 Trail laedt seine Historie on-demand pro Fahrzeug (fz_latest hat je Fahrzeug nur 1 Punkt).
#4 In-Flight-Guard gegen ueberlappende/out-of-order Polls.
#5 Zeilen-Fokus beendet ein laufendes Live-Follow auf ein anderes Fahrzeug.
#7 Himmelsrichtung im Popup nur bei aktivem Fahrzeug.
"""


def test_markers_from_view(index_html):
    assert 'var url=SB_REST+"/fz_latest?select=*";' in index_html
    # alter globaler 200er-Deckel entfernt
    assert 'fz_positions?select=*&order=ts.desc&limit=200' not in index_html


def test_track_fetcher(index_html):
    assert "async function _flotteFetchTrack(fid){" in index_html
    # v3.9.678: speed+ignition kommen mit — _fzStatusSeit braucht sie, um den fahren/stehen-
    # Wechsel in der Historie zu finden. Ohne sie waere jeder Punkt "steht".
    assert (
        '"/fz_positions?select=lat,lon,ts,speed,ignition&fahrzeug_id=eq."'
        '+encodeURIComponent(fid)+"&order=ts.desc&limit=500"'
    ) in index_html


def test_refs(index_html):
    assert "const _openFid=_react.useRef.call(void 0, null);" in index_html
    assert "const _polling=_react.useRef.call(void 0, false);" in index_html


def test_inflight_guard(index_html):
    assert "function load(){if(_polling.current)return;_polling.current=true;" in index_html


def test_popup_restore(index_html):
    assert "m.on('popupopen',function(){_openFid.current=f.id;});" in index_html
    assert "if(_openFid.current&&_markers.current[_openFid.current]){try{_markers.current[_openFid.current].openPopup();}catch(_eo){}}" in index_html
    assert "+_rich,{autoPan:false});" in index_html


def test_compass_inactive_guard(index_html):
    assert "var _rich=(_head!==null&&_head!==''&&!inactive)?" in index_html


def test_trail_ondemand(index_html):
    assert "_flotteFetchTrack(fid).then(function(rows){if(!_map.current)return;" in index_html


def test_focus_clears_follow(index_html):
    assert "if(followId&&followId!==row.f.id)setFollowId(null);" in index_html
