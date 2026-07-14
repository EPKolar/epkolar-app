"""v3.9.691 Flotte-Live-Poll (10s statt 60s) + Segment-Engine bei 10s-Punktdichte.

FLOTTE_POLL_MS (Z.21975) beschleunigt NUR den Live-Poll der Karte (setInterval(load,
FLOTTE_POLL_MS) im Positions-Effect der Flotte-Karte, Z.23313). Fahrtenbuch- und
Analyse-Fetches (_flotteFetchTrack, FahrtenbuchView) bleiben bewusst unangetastet — das
sind teure Einmal-Abfragen beim Oeffnen, kein Live-Ticker.

Zweiter Teil: die Segment-Engine (//@FLOTTE-SEGMENTE-START..END, unveraendert seit
v3.9.679) muss bei einer 10-Sekunden-Punktdichte (statt der bisher ueblichen 30s/1min-
Traccar-Takte) weiterhin EINE zusammenhaengende Fahrt liefern statt sie in Mikro-Segmente
zu zerhacken.
"""
import re
import json
import datetime
import pytest
from conftest import run_node_snippet, _extract_fn


# ═══════════════════════════════════════════════════════════════════
# 1) FLOTTE_POLL_MS — Wiring (String-Asserts)
# ═══════════════════════════════════════════════════════════════════
def test_flotte_poll_ms_konstante_ist_10_sekunden(index_html):
    assert "const FLOTTE_POLL_MS=10*TIME_SECOND;" in index_html


def test_live_poll_nutzt_flotte_poll_ms(index_html):
    assert "var iv=setInterval(load,FLOTTE_POLL_MS);" in index_html


def test_flotte_poll_haengt_nicht_mehr_auf_60s(index_html):
    """Der Flotte-Live-Poll darf keinen 60s-Takt mehr haben.

    ACHTUNG, bewusst eng geprueft: es gibt einen ZWEITEN `setInterval(load,60000)` in
    `WochenplanTafel` (Lager-Kiosk, kiosk_week_absences-RPC). Der ist NICHT gemeint und
    bleibt ausdruecklich bei 60s — Sebastians Vorgabe galt nur dem GPS-Poll der Flotte
    ("Fahrtenbuch-/Analyse-Fetches NICHT mitbeschleunigen"). Ein `not in index_html` ueber
    die ganze Datei wuerde diesen fremden Kiosk-Poll faelschlich mitreissen.
    """
    import re
    m = re.search(r"/\* Positionen laden \+ Live-Poll.*?\},\[\]\);", index_html, re.S)
    assert m, "Flotte-Live-Poll-Block nicht gefunden"
    block = m.group(0)
    assert "setInterval(load,FLOTTE_POLL_MS)" in block
    assert "60000" not in block


def test_wochenplantafel_poll_bleibt_bei_60s(index_html):
    """Gegenprobe: der Kiosk-Abwesenheits-Poll wurde NICHT mitbeschleunigt."""
    assert "setInterval(load,60000)" in index_html


def test_flotte_poll_ms_wird_nur_fuer_live_poll_referenziert(index_html):
    """FLOTTE_POLL_MS taucht im ganzen File nur 3x auf: die Konstante selbst, ein
    erklaerender Kommentar direkt davor, und der eine setInterval-Aufruf der Live-Karte.
    Kein Fahrtenbuch-/Analyse-Fetch referenziert sie."""
    assert index_html.count("FLOTTE_POLL_MS") == 3


def test_fahrtenbuch_fetch_haengt_nicht_an_flotte_poll_ms(index_html):
    """_flotteFetchTrack (Fahrtenbuch-Datenzugriff) und FahrtenbuchView (Fahrtenliste)
    bleiben bewusst langsam/on-demand — sie duerfen FLOTTE_POLL_MS nicht referenzieren."""
    for name in ("_flotteFetchTrack", "FahrtenbuchView"):
        src = _extract_fn(index_html, name)
        assert src, f"function {name} nicht gefunden"
        assert "FLOTTE_POLL_MS" not in src


# ═══════════════════════════════════════════════════════════════════
# 2) Segment-Engine bei 10s-Punktdichte (Node-Eval)
# ═══════════════════════════════════════════════════════════════════
_TIME_CONSTS = (
    "const TIME_SECOND=1000;"
    "const TIME_MINUTE=60*TIME_SECOND;"
    "const TIME_HOUR=60*TIME_MINUTE;"
    "const TIME_DAY=24*TIME_HOUR;\n"
)


def _flotte_block(index_html):
    m = re.search(r"//@FLOTTE-SEGMENTE-START(.*?)//@FLOTTE-SEGMENTE-END", index_html, re.S)
    assert m, "FLOTTE-SEGMENTE-Block nicht gefunden"
    return m.group(1)


def _eval(node_exe, index_html, expr):
    snippet = _TIME_CONSTS + _flotte_block(index_html) + "\nprocess.stdout.write(JSON.stringify((" + expr + ")))"
    return json.loads(run_node_snippet(node_exe, snippet))


def _iso(ms):
    return (
        datetime.datetime.fromtimestamp(ms / 1000, datetime.timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


DAY0 = int(datetime.datetime(2026, 1, 20, 6, 0, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)
LAT0, LON0 = 48.500, 16.300


def _dense_fahrt_punkte():
    """~20 Minuten Fahrt im 10-Sekunden-Takt (monoton laufende Koordinate, durchgehend
    Bewegung), danach 10 Minuten Stillstand im selben 10-Sekunden-Takt (gleiche Koordinate).
    Realistischer Traccar-Takt bei aktivem FLOTTE_POLL_MS-Intervall."""
    pts = []
    # Bewegung: t=0..1200s (0..20min), Schrittweite 10s -> 121 Punkte, ~11m/Schritt Richtung Norden.
    last_lat = LAT0
    for i in range(0, 1201, 10):
        lat = LAT0 + (i // 10) * 0.0001
        last_lat = lat
        pts.append({"ts": _iso(DAY0 + i * 1000), "lat": lat, "lon": LON0, "speed": 40})
    # Stillstand: t=1210..1800s (weitere 10min), gleiche Koordinate wie letzter Bewegungspunkt.
    for i in range(1210, 1801, 10):
        pts.append({"ts": _iso(DAY0 + i * 1000), "lat": last_lat, "lon": LON0, "speed": 0})
    return pts, last_lat


def test_10s_punktdichte_ergibt_eine_fahrt_kein_mikro_segmente(node_exe, index_html):
    pts, _last_lat = _dense_fahrt_punkte()
    segs = _eval(node_exe, index_html, "_fzSegmente(" + json.dumps(pts) + ")")
    assert len(segs) == 1, (
        f"Erwartet genau 1 Fahrt bei 10s-Punktdichte, bekommen {len(segs)} Segmente -- "
        "die Engine haette die Fahrt in Mikro-Segmente zerhackt."
    )
    seg = segs[0]
    assert seg["beginn"] == DAY0
    assert seg["ende"] == DAY0 + 1200 * 1000  # letzter Bewegungspunkt, NICHT der Stillstand
    assert seg["dauerMin"] == 20
    # ~120 Schritte a ~11.1m Nord-Versatz -> ueber 1 km, deutlich ueber der 200m-Mindeststrecke.
    assert 1.0 < seg["km"] < 2.0


def test_10s_punktdichte_stillstand_wird_nicht_zur_fahrt(node_exe, index_html):
    """Die 10 Minuten Stillstand am Ende duerfen keine eigene (Mikro-)Fahrt eroeffnen —
    speed=0 haelt p.mv auf false, es gibt kein ignition-Feld, das ein Segment eroeffnen
    koennte."""
    pts, last_lat = _dense_fahrt_punkte()
    segs = _eval(node_exe, index_html, "_fzSegmente(" + json.dumps(pts) + ")")
    assert len(segs) == 1
    assert segs[0]["endPos"]["lat"] == pytest.approx(last_lat)
    assert segs[0]["endPos"]["lon"] == LON0
