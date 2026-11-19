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
    # v1049 Re-Pin: das HTML-Popup am Marker ist durch die React-Info-Karte ersetzt. Welches
    # Fahrzeug offen ist, steht jetzt im React-State (selFid) und ueberlebt den Marker-Neuaufbau
    # von selbst - der _openFid-Merker fuers Wiederoeffnen ist damit tot und entfernt.
    assert "const [selFid,setSelFid]=_react.useState.call(void 0, null);" in index_html
    assert "_openFid" not in index_html
    assert "const _polling=_react.useRef.call(void 0, false);" in index_html


def test_inflight_guard(index_html):
    assert "function load(){if(_polling.current)return;_polling.current=true;" in index_html


def test_popup_restore(index_html):
    # v1049 Re-Pin (Absicht unveraendert: der 10-s-Poll darf die offene Info nicht schliessen und
    # die Karte nicht verschieben). Das Popup ist jetzt EIN eigenstaendiges L.popup, nicht mehr an
    # den Marker gebunden: der Neuaufbau der Marker beruehrt es nicht, der Poll verankert es nur neu.
    assert "_popRef.current=L.popup({closeButton:false,autoPan:false," in index_html
    assert "_popRef.current.setLatLng([_selLat,_selLon]);if(!map.hasLayer(_popRef.current))_popRef.current.openOn(map);" in index_html
    assert "m.bindPopup(" not in index_html, "Umkehrprobe: das alte, an den Marker gebundene Popup ist zurueck"


def test_compass_inactive_guard(index_html):
    # v1049 Re-Pin: Himmelsrichtung nur in Fahrt (vorher: nur wenn aktiv). Verhalten in
    # test_flotte_karte_busse_v1049.py per Node geprueft (stehend/veraltet -> "—").
    assert "if(_fzKartenZustand(p,nowMs)!=='faehrt')return '—';" in index_html


def test_trail_ondemand(index_html):
    # v1049 Re-Pin: _holeTrack ist der on-demand-Abruf; nur im Admin-Demo kommt die Spur aus dem Speicher.
    assert "_holeTrack(fid).then(function(rows){if(!_map.current)return;" in index_html
    assert "var _holeTrack=function(fid){return _demo?Promise.resolve((_demoDaten&&_demoDaten.tracks[fid])||[]):_flotteFetchTrack(fid);};" in index_html


def test_focus_clears_follow(index_html):
    assert "if(followId&&followId!==row.f.id)setFollowId(null);" in index_html
