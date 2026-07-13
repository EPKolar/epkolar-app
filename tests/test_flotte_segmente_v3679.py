"""v3.9.679 Flotte-Fahrt-Segmentierung — Engine-Tests (Node-eval).

Testet den Sentinel-Block //@FLOTTE-SEGMENTE-START..END aus index.html:
  _fzHaversine(lat1,lon1,lat2,lon2)  -> Meter
  _fzOdo(p)                          -> Tachostand (odometer | raw.odometer) oder null
  _fzNormPos(positions)              -> saubere, aufsteigend sortierte Punktliste
  _fzSegmente(positions,opts)        -> [{beginn,ende,dauerMin,km,startPos,endPos,tachoVon,tachoBis}]

Die Funktionen werden per _extract_fn aus index.html geschnitten und isoliert in Node
ausgefuehrt. Externe Abhaengigkeit: TIME_MINUTE (index.html Z. 671-674).

Signal-Hierarchie laut Engine:
  ZUENDUNG primaer  — ignition===false beendet die Fahrt sofort; ignition===true haelt sie offen.
  SPEED Fallback    — fehlt das ignition-Feld, traegt speed>3 die Segmentierung allein.
  In BEIDEN Pfaden beendet ein Stillstand > opts.stillMin (default 5) die Fahrt beim LETZTEN
  Bewegungspunkt (deckt Signal-Luecken und Uebernacht mit ab).
  Segmente < opts.minFahrtM (default 200 m) oder < 2 Punkte werden verworfen.

Koordinaten: Weinviertel/NOe um 48.5 N / 16.3 E.
"""
import json
import math

import pytest

from conftest import run_node_snippet, _extract_fn

# Exakt wie in index.html (Z. 671-674).
_TIME_CONSTS = (
    "const TIME_SECOND=1000;"
    "const TIME_MINUTE=60*TIME_SECOND;"
    "const TIME_HOUR=60*TIME_MINUTE;"
    "const TIME_DAY=24*TIME_HOUR;\n"
)

# NaN ist in JSON nicht darstellbar -> bewusst als null serialisieren, damit die Tests
# "kein Wert" von "0" unterscheiden koennen.
_JSON_HELPER = (
    "function _out(v){process.stdout.write(JSON.stringify(v,function(k,x){"
    "return (typeof x==='number'&&Number.isNaN(x))?null:x;}));}\n"
)

_DEPS = ["_fzHaversine", "_fzOdo", "_fzNormPos", "_fzSegmente"]


def _harness(index_html, expr):
    """Konstanten + alle Engine-Funktionen + Ausgabe von `expr` als JSON."""
    parts = [_TIME_CONSTS, _JSON_HELPER]
    for name in _DEPS:
        fn = _extract_fn(index_html, name)
        assert fn, f"function {name} nicht in index.html gefunden"
        parts.append(fn + "\n")
    parts.append("_out(" + expr + ");")
    return "".join(parts)


def _eval(node_exe, index_html, expr):
    return json.loads(run_node_snippet(node_exe, _harness(index_html, expr)))


def _segs(node_exe, index_html, points, opts=None):
    arr = _arr(points)
    return _eval(node_exe, index_html, f"_fzSegmente({arr},{opts or 'undefined'})")


# ── Zeitbasis: 2026-01-15T00:00:00Z ──
DAY0 = 1768435200000
MIN = 60000
SEC = 1000
DAY = 86400000

LAT0 = 48.500
LON0 = 16.300

# Meter pro Grad Breite bei R=6371000 (identisch zur Engine-Konstante).
M_PER_DEG_LAT = math.pi / 180 * 6371000


def T(h, m, s=0, day=0):
    """Epoch-ms fuer Uhrzeit am Tag DAY0+day (UTC)."""
    return DAY0 + day * DAY + h * 3600000 + m * MIN + s * SEC


def _iso(ms):
    """ISO-String wie ihn Supabase/Traccar liefert."""
    import datetime

    return (
        datetime.datetime.fromtimestamp(ms / 1000, datetime.timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


class Raw(str):
    """Marker: Inhalt wortwoertlich als JS-Code einsetzen (undefined, NaN, ...)."""


MISSING = object()


def _js(v):
    if isinstance(v, Raw):
        return str(v)
    if v is None:
        return "null"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, str):
        return json.dumps(v)
    if isinstance(v, dict):
        return "{" + ",".join(k + ":" + _js(x) for k, x in v.items()) + "}"
    return repr(v)


def P(ts, lat=LAT0, lon=LON0, speed=MISSING, ignition=MISSING, odometer=MISSING, raw=MISSING):
    """Position-Literal. `ts` als epoch-ms (-> ISO) oder Raw/str fuer kaputte Faelle."""
    fields = {}
    fields["ts"] = ts if isinstance(ts, (Raw, str)) else _iso(ts)
    fields["lat"] = lat
    fields["lon"] = lon
    for k, v in (("speed", speed), ("ignition", ignition), ("odometer", odometer), ("raw", raw)):
        if v is not MISSING:
            fields[k] = v
    return "{" + ",".join(k + ":" + _js(v) for k, v in fields.items()) + "}"


def _arr(points):
    return "[" + ",".join(points) + "]"


def _hav(a1, o1, a2, o2):
    """Referenz-Haversine in Python (gleiche Erdradius-Annahme wie die Engine)."""
    r = 6371000.0
    rad = math.pi / 180
    d_lat = (a2 - a1) * rad
    d_lon = (o2 - o1) * rad
    s1 = math.sin(d_lat / 2)
    s2 = math.sin(d_lon / 2)
    x = s1 * s1 + math.cos(a1 * rad) * math.cos(a2 * rad) * s2 * s2
    return 2 * r * math.asin(math.sqrt(max(0.0, min(1.0, x))))


def _km(latlons):
    """Erwartete km-Summe ueber eine Punktkette [(lat,lon),...]."""
    m = 0.0
    for i in range(1, len(latlons)):
        m += _hav(latlons[i - 1][0], latlons[i - 1][1], latlons[i][0], latlons[i][1])
    return m / 1000.0


# ═══════════════════════════════════════════════════════════════════
# 1) Realbeispiel: Barger-Tag, drei Fahrten mit Zuendungssignal
# ═══════════════════════════════════════════════════════════════════
def test_barger_tag_drei_fahrten(node_exe, index_html):
    """Typischer Monteurstag: 3 Fahrten, dazwischen jeweils Motor aus + Pause > 5 Min."""
    pts = [
        # Fahrt 1: 06:47 -> 06:56 (Motor aus bei 06:56)
        P(T(6, 47), 48.500, LON0, speed=25, ignition=True),
        P(T(6, 49), 48.505, LON0, speed=60, ignition=True),
        P(T(6, 52), 48.512, LON0, speed=70, ignition=True),
        P(T(6, 55), 48.518, LON0, speed=20, ignition=True),
        P(T(6, 56), 48.518, LON0, speed=0, ignition=False),
        # Pause: abgestellt, Motor aus -> darf keine Fahrt eroeffnen
        P(T(7, 0), 48.518, LON0, speed=0, ignition=False),
        P(T(7, 5), 48.518, LON0, speed=0, ignition=False),
        # Fahrt 2: 07:09 -> 07:19
        P(T(7, 9), 48.520, LON0, speed=30, ignition=True),
        P(T(7, 12), 48.527, LON0, speed=50, ignition=True),
        P(T(7, 16), 48.534, LON0, speed=45, ignition=True),
        P(T(7, 18), 48.540, LON0, speed=10, ignition=True),
        P(T(7, 19), 48.540, LON0, speed=0, ignition=False),
        P(T(7, 22), 48.540, LON0, speed=0, ignition=False),
        # Fahrt 3: 07:24 -> 07:40
        P(T(7, 24), 48.542, LON0, speed=20, ignition=True),
        P(T(7, 28), 48.548, LON0, speed=50, ignition=True),
        P(T(7, 32), 48.556, LON0, speed=60, ignition=True),
        P(T(7, 36), 48.562, LON0, speed=55, ignition=True),
        P(T(7, 38), 48.566, LON0, speed=40, ignition=True),
        P(T(7, 40), 48.566, LON0, speed=0, ignition=False),
    ]
    segs = _segs(node_exe, index_html, pts)
    assert len(segs) == 3, segs

    assert segs[0]["beginn"] == T(6, 47)
    assert segs[0]["ende"] == T(6, 56)
    assert segs[0]["dauerMin"] == 9
    assert segs[0]["startPos"] == {"lat": 48.500, "lon": LON0}
    assert segs[0]["endPos"] == {"lat": 48.518, "lon": LON0}
    assert segs[0]["km"] == pytest.approx(
        _km([(48.500, LON0), (48.505, LON0), (48.512, LON0), (48.518, LON0), (48.518, LON0)]),
        abs=0.02,
    )

    assert segs[1]["beginn"] == T(7, 9)
    assert segs[1]["ende"] == T(7, 19)
    assert segs[1]["dauerMin"] == 10

    assert segs[2]["beginn"] == T(7, 24)
    assert segs[2]["ende"] == T(7, 40)
    assert segs[2]["dauerMin"] == 16

    # Kein Tacho im Datensatz -> beide Felder null, km trotzdem gerechnet.
    for s in segs:
        assert s["tachoVon"] is None and s["tachoBis"] is None
        assert s["km"] > 1.5


# ═══════════════════════════════════════════════════════════════════
# 2)-4) Degenerierte Eingaben
# ═══════════════════════════════════════════════════════════════════
def test_leere_eingabe(node_exe, index_html):
    assert _eval(node_exe, index_html, "_fzSegmente([])") == []
    assert _eval(node_exe, index_html, "_fzSegmente(null)") == []
    assert _eval(node_exe, index_html, "_fzSegmente(undefined)") == []


def test_nur_ein_punkt(node_exe, index_html):
    """Ein einzelner Punkt ist keine Fahrt — auch nicht bei 80 km/h."""
    pts = [P(T(8, 0), 48.500, LON0, speed=80, ignition=True)]
    assert _segs(node_exe, index_html, pts) == []


def test_fahrzeug_steht_ganzen_tag(node_exe, index_html):
    """Speed 0, Zuendung aus (bzw. Feld gar nicht da) -> keine einzige Fahrt."""
    mit_ign = [P(T(h, 0), 48.500, LON0, speed=0, ignition=False) for h in range(6, 19)]
    assert _segs(node_exe, index_html, mit_ign) == []

    ohne_ign = [P(T(h, 0), 48.500, LON0, speed=0) for h in range(6, 19)]
    assert _segs(node_exe, index_html, ohne_ign) == []

    # GPS-Rauschen im Stand (speed <= 3) eroeffnet ebenfalls keine Fahrt.
    rauschen = [P(T(9, m), 48.500, LON0, speed=3, ignition=False) for m in range(0, 30, 5)]
    assert _segs(node_exe, index_html, rauschen) == []


# ═══════════════════════════════════════════════════════════════════
# 5)-6) Zuendungs-Pfad
# ═══════════════════════════════════════════════════════════════════
def test_zuendung_aus_beendet_fahrt_sofort(node_exe, index_html):
    """ignition===false schliesst die Fahrt exakt beim false-Punkt (Motor aus = Fahrt zu Ende)."""
    pts = [
        P(T(9, 0), 48.500, LON0, speed=30, ignition=True),
        P(T(9, 2), 48.508, LON0, speed=50, ignition=True),
        P(T(9, 4), 48.516, LON0, speed=50, ignition=True),
        P(T(9, 6), 48.522, LON0, speed=10, ignition=True),
        P(T(9, 7), 48.522, LON0, speed=0, ignition=False),  # Motor aus
        # danach abgestellt — eroeffnet keine neue Fahrt
        P(T(9, 9), 48.522, LON0, speed=0, ignition=False),
        P(T(9, 20), 48.522, LON0, speed=0, ignition=False),
    ]
    segs = _segs(node_exe, index_html, pts)
    assert len(segs) == 1
    assert segs[0]["beginn"] == T(9, 0)
    assert segs[0]["ende"] == T(9, 7)  # der false-Punkt selbst ist das Ende
    assert segs[0]["dauerMin"] == 7
    assert segs[0]["endPos"] == {"lat": 48.522, "lon": LON0}


def test_zuendung_an_aber_stillstand_beendet_fahrt(node_exe, index_html):
    """Motor laeuft, Fahrzeug steht (Baustelle): > stillMin ohne Bewegung beendet die Fahrt
    trotzdem — und zwar beim LETZTEN Bewegungspunkt, nicht beim aktuellen Punkt."""
    pts = [
        P(T(8, 0), 48.500, LON0, speed=30, ignition=True),
        P(T(8, 1), 48.505, LON0, speed=40, ignition=True),
        P(T(8, 2), 48.512, LON0, speed=40, ignition=True),
        P(T(8, 3), 48.520, LON0, speed=20, ignition=True),  # letzter Bewegungspunkt
    ]
    # Motor laeuft weiter, Fahrzeug ruehrt sich nicht (Standheizung / Ladevorgang / Baustelle)
    pts += [P(T(8, m), 48.520, LON0, speed=0, ignition=True) for m in range(4, 13)]

    segs = _segs(node_exe, index_html, pts)
    assert len(segs) == 1, segs
    assert segs[0]["beginn"] == T(8, 0)
    assert segs[0]["ende"] == T(8, 3)  # NICHT 08:12 — die Standzeit gehoert nicht zur Fahrt
    assert segs[0]["dauerMin"] == 3
    assert segs[0]["km"] == pytest.approx(
        _km([(48.500, LON0), (48.505, LON0), (48.512, LON0), (48.520, LON0)]), abs=0.02
    )


# ═══════════════════════════════════════════════════════════════════
# 7) Speed-Fallback (kein ignition-Feld)
# ═══════════════════════════════════════════════════════════════════
def test_speed_fallback_ohne_ignition_feld(node_exe, index_html):
    """Aelterer Tracker ohne Zuendungssignal: speed>3 traegt die Segmentierung allein."""
    pts = [
        P(T(10, 0), 48.500, LON0, speed=0),  # steht -> keine Fahrt
        P(T(10, 2), 48.502, LON0, speed=40),  # Fahrt 1 beginnt
        P(T(10, 4), 48.510, LON0, speed=50),
        P(T(10, 6), 48.518, LON0, speed=45),  # letzte Bewegung
        P(T(10, 8), 48.520, LON0, speed=0),  # angekommen
        P(T(10, 20), 48.520, LON0, speed=0),  # > 5 Min Stillstand -> schliesst Fahrt 1
        P(T(10, 30), 48.530, LON0, speed=60),  # Fahrt 2 beginnt
        P(T(10, 33), 48.545, LON0, speed=60),
        P(T(10, 36), 48.560, LON0, speed=5),  # 5 > 3 -> noch Bewegung
    ]
    segs = _segs(node_exe, index_html, pts)
    assert len(segs) == 2, segs
    assert segs[0]["beginn"] == T(10, 2)
    assert segs[0]["ende"] == T(10, 6)  # Ende = letzter Bewegungspunkt
    assert segs[1]["beginn"] == T(10, 30)
    assert segs[1]["ende"] == T(10, 36)
    assert segs[0]["km"] == pytest.approx(
        _km([(48.502, LON0), (48.510, LON0), (48.518, LON0)]), abs=0.02
    )
    assert segs[1]["km"] == pytest.approx(
        _km([(48.530, LON0), (48.545, LON0), (48.560, LON0)]), abs=0.02
    )


def test_speed_schwelle_ist_strikt_groesser_3(node_exe, index_html):
    """speed==3 ist Rauschen, speed==4 ist Fahrt (gleiche Schwelle wie _fzFaehrt)."""
    strecke = [(48.500, LON0), (48.505, LON0), (48.510, LON0)]
    drei = [P(T(11, i), la, lo, speed=3) for i, (la, lo) in enumerate(strecke)]
    vier = [P(T(11, i), la, lo, speed=4) for i, (la, lo) in enumerate(strecke)]
    assert _segs(node_exe, index_html, drei) == []
    assert len(_segs(node_exe, index_html, vier)) == 1


# ═══════════════════════════════════════════════════════════════════
# 8)-9) Signal-Luecke & Uebernacht
# ═══════════════════════════════════════════════════════════════════
def test_signal_luecke_splittet(node_exe, index_html):
    """Grosses ts-Loch (Tunnel, Tracker offline): die Stillstand-Regel greift und splittet.
    Die 'Luftlinie' ueber das Loch darf in KEINE der beiden km-Summen einfliessen."""
    pts = [
        P(T(11, 0), 48.500, LON0, speed=50),
        P(T(11, 2), 48.505, LON0, speed=50),
        P(T(11, 4), 48.510, LON0, speed=50),
        # ---- 26 Min Funkstille, Fahrzeug taucht 5,5 km weiter wieder auf ----
        P(T(11, 30), 48.560, LON0, speed=50),
        P(T(11, 32), 48.565, LON0, speed=50),
        P(T(11, 34), 48.570, LON0, speed=50),
    ]
    segs = _segs(node_exe, index_html, pts)
    assert len(segs) == 2, segs
    assert segs[0]["beginn"] == T(11, 0) and segs[0]["ende"] == T(11, 4)
    assert segs[1]["beginn"] == T(11, 30) and segs[1]["ende"] == T(11, 34)
    erwartet = _km([(48.500, LON0), (48.505, LON0), (48.510, LON0)])  # ~1,11 km
    assert segs[0]["km"] == pytest.approx(erwartet, abs=0.02)
    assert segs[1]["km"] == pytest.approx(erwartet, abs=0.02)
    # Die 5,5 km Luecke sind nirgends gelandet.
    assert segs[0]["km"] < 2 and segs[1]["km"] < 2


def test_uebernacht_zwei_segmente(node_exe, index_html):
    """Fahrt am Abend, Nacht ohne Positionen, Fahrt am Morgen -> ZWEI Fahrten, nicht eine
    12-Stunden-Riesenfahrt."""
    # Ping-Takt bewusst < stillMin (der Tracker funkt in Bewegung im Minutentakt) —
    # sonst wuerde schon die Ping-Luecke selbst als Stillstand gelten.
    pts = [
        P(T(18, 0), 48.500, LON0, speed=60),
        P(T(18, 2), 48.510, LON0, speed=60),
        P(T(18, 4), 48.520, LON0, speed=60),
        P(T(18, 6), 48.530, LON0, speed=50),
        P(T(18, 8), 48.540, LON0, speed=40),
        # Nacht: Tracker schweigt
        P(T(6, 0, day=1), 48.540, LON0, speed=30),
        P(T(6, 3, day=1), 48.555, LON0, speed=60),
        P(T(6, 6, day=1), 48.570, LON0, speed=60),
        P(T(6, 9, day=1), 48.585, LON0, speed=50),
    ]
    segs = _segs(node_exe, index_html, pts)
    assert len(segs) == 2, segs
    assert segs[0]["beginn"] == T(18, 0) and segs[0]["ende"] == T(18, 8)
    assert segs[0]["dauerMin"] == 8
    assert segs[1]["beginn"] == T(6, 0, day=1) and segs[1]["ende"] == T(6, 9, day=1)
    assert segs[1]["dauerMin"] == 9
    # Keine Fahrt darf ueber die Nacht gespannt sein.
    for s in segs:
        assert s["dauerMin"] < 60


# ═══════════════════════════════════════════════════════════════════
# 10) Mini-Rangieren (minFahrtM)
# ═══════════════════════════════════════════════════════════════════
def test_mini_rangieren_verworfen(node_exe, index_html):
    """~150 m Umparken auf dem Hof: default (200 m) verwirft, minFahrtM=0 behaelt."""
    ziel = LAT0 + 0.00135  # ~150 m
    pts = [
        P(T(12, 0), LAT0, LON0, speed=5),
        P(T(12, 1), ziel, LON0, speed=5),
        P(T(12, 2), ziel, LON0, speed=0),
    ]
    assert _segs(node_exe, index_html, pts) == []  # default minFahrtM=200
    assert _segs(node_exe, index_html, pts, "{minFahrtM:200}") == []

    behalten = _segs(node_exe, index_html, pts, "{minFahrtM:0}")
    assert len(behalten) == 1
    assert behalten[0]["beginn"] == T(12, 0)
    assert behalten[0]["ende"] == T(12, 1)
    assert behalten[0]["km"] == pytest.approx(_km([(LAT0, LON0), (ziel, LON0)]), abs=0.02)
    assert 0.10 < behalten[0]["km"] < 0.20

    # Eine echte Fahrt im selben Datensatz bleibt unabhaengig davon erhalten.
    lang = pts + [
        P(T(13, 0), 48.510, LON0, speed=50),
        P(T(13, 5), 48.530, LON0, speed=50),
    ]
    segs = _segs(node_exe, index_html, lang)
    assert len(segs) == 1
    assert segs[0]["beginn"] == T(13, 0)


# ═══════════════════════════════════════════════════════════════════
# 11)-12) Tacho (odometer)
# ═══════════════════════════════════════════════════════════════════
def test_tacho_aus_odometer_feld(node_exe, index_html):
    pts = [
        P(T(14, 0), 48.500, LON0, speed=40, odometer=120500),
        P(T(14, 3), 48.512, LON0, speed=60, odometer=120501),
        P(T(14, 6), 48.524, LON0, speed=60, odometer=120503),
        P(T(14, 9), 48.536, LON0, speed=30, odometer=120504),
    ]
    segs = _segs(node_exe, index_html, pts)
    assert len(segs) == 1
    assert segs[0]["tachoVon"] == 120500
    assert segs[0]["tachoBis"] == 120504


def test_tacho_aus_raw_odometer(node_exe, index_html):
    """Teltonika/Traccar packt den OBD-Tacho oft nur ins raw-Attribut-Blob."""
    pts = [
        P(T(15, 0), 48.500, LON0, speed=40, raw={"odometer": 88000}),
        P(T(15, 3), 48.512, LON0, speed=60, raw={"odometer": 88001}),
        P(T(15, 6), 48.524, LON0, speed=30, raw={"odometer": "88002"}),  # String -> Number
    ]
    segs = _segs(node_exe, index_html, pts)
    assert len(segs) == 1
    assert segs[0]["tachoVon"] == 88000
    assert segs[0]["tachoBis"] == 88002


def test_tacho_fehlt_null_km_trotzdem(node_exe, index_html):
    """Ohne OEM-Tacho bleiben tachoVon/tachoBis null — die km kommen IMMER aus Haversine."""
    strecke = [(48.500, LON0), (48.515, LON0), (48.530, LON0), (48.545, LON0)]
    pts = [P(T(16, i * 3), la, lo, speed=55) for i, (la, lo) in enumerate(strecke)]
    segs = _segs(node_exe, index_html, pts)
    assert len(segs) == 1
    assert segs[0]["tachoVon"] is None
    assert segs[0]["tachoBis"] is None
    assert segs[0]["km"] == pytest.approx(_km(strecke), abs=0.02)
    assert segs[0]["km"] > 4.9  # 0,045 Grad Breite ~ 5,0 km


def test_fzOdo_direkt(node_exe, index_html):
    cases = {
        "{odometer:5}": 5,
        "{odometer:0}": 0,  # 0 km ist ein Wert, nicht "fehlt"
        "{odometer:'123.5'}": 123.5,
        "{odometer:''}": None,
        "{odometer:null,raw:{odometer:77}}": 77,  # Fallback auf raw
        "{odometer:undefined,raw:{odometer:77}}": 77,
        "{odometer:'abc'}": None,
        "{raw:{}}": None,
        "{}": None,
        "null": None,
        "undefined": None,
    }
    expr = "[" + ",".join("_fzOdo(" + k + ")" for k in cases) + "]"
    assert _eval(node_exe, index_html, expr) == list(cases.values())


# ═══════════════════════════════════════════════════════════════════
# 13) Robustheit: Muell in der Eingabe
# ═══════════════════════════════════════════════════════════════════
def test_fzNormPos_verwirft_muell_und_sortiert(node_exe, index_html):
    raw_pts = [
        P(T(9, 5), 48.510, LON0, speed=50),  # gueltig, aber unsortiert (spaeter)
        P(T(9, 0), 48.500, LON0, speed=0, ignition=True),  # gueltig
        P("kein-datum", 48.520, LON0, speed=50),  # kaputte ts
        P(Raw("undefined"), 48.520, LON0, speed=50),  # ts fehlt
        P(T(9, 3), 0, 0, speed=80),  # Null-Island (Tracker ohne Fix)
        P(T(9, 4), Raw("NaN"), LON0, speed=50),  # nicht-endliche Koordinate
        P(T(9, 6), Raw("'nord'"), LON0, speed=50),  # unbrauchbare Koordinate
        "null",
    ]
    out = _eval(node_exe, index_html, f"_fzNormPos({_arr(raw_pts)})")
    assert len(out) == 2, out
    assert [p["t"] for p in out] == [T(9, 0), T(9, 5)]  # aufsteigend sortiert
    assert out[0]["mv"] is False and out[0]["ign"] is True
    assert out[1]["mv"] is True and out[1]["ign"] is None  # ignition-Feld fehlt -> null
    assert out[0]["odo"] is None


def test_segmente_robust_gegen_muell(node_exe, index_html):
    """Unsortiert + NaN-Speed + Null-Island + kaputte ts: darf nicht crashen, und der
    Null-Island-Punkt darf NIEMALS in die km-Summe (das waeren ~5400 km nach Afrika)."""
    sauber = [
        P(T(9, 0), 48.500, LON0, speed=50),
        P(T(9, 2), 48.508, LON0, speed=Raw("NaN")),  # gueltige Position, kaputter Tacho-Speed
        P(T(9, 4), 48.516, LON0, speed=50),
        P(T(9, 6), 48.524, LON0, speed=50),
    ]
    ref = _segs(node_exe, index_html, sauber)
    assert len(ref) == 1

    dreck = [
        sauber[2],  # unsortiert
        P(T(9, 3), 0, 0, speed=80),  # Null-Island mitten in der Fahrt
        sauber[0],
        "null",
        P("2026-13-45T99:99:99Z", 48.600, LON0, speed=50),  # kaputte ts
        sauber[3],
        P(T(9, 5), Raw("Infinity"), LON0, speed=50),  # nicht-endliche Koordinate
        sauber[1],
        P(Raw("''"), 48.700, LON0, speed=50),  # leere ts
    ]
    segs = _segs(node_exe, index_html, dreck)
    assert segs == ref, "Muellpunkte veraendern das Ergebnis"
    assert segs[0]["beginn"] == T(9, 0) and segs[0]["ende"] == T(9, 6)
    assert segs[0]["km"] == pytest.approx(
        _km([(48.500, LON0), (48.508, LON0), (48.516, LON0), (48.524, LON0)]), abs=0.02
    )
    assert segs[0]["km"] < 5  # kein Ausflug nach Null-Island


def test_kaputte_opts_fallen_auf_defaults_zurueck(node_exe, index_html):
    """NaN/negative opts duerfen die Engine nicht kippen -> Defaults 5 Min / 200 m."""
    pts = [
        P(T(12, 0), LAT0, LON0, speed=5),
        P(T(12, 1), LAT0 + 0.00135, LON0, speed=5),  # ~150 m -> unter default-Schwelle
    ]
    for opts in ("{stillMin:NaN,minFahrtM:NaN}", "{stillMin:-1,minFahrtM:-5}", "{}", "null"):
        assert _segs(node_exe, index_html, pts, opts) == [], opts


# ═══════════════════════════════════════════════════════════════════
# 14) _fzHaversine
# ═══════════════════════════════════════════════════════════════════
def test_haversine_bekannte_distanzen(node_exe, index_html):
    # 0,009 Grad Breite ~ 1000,8 m
    nord = _eval(node_exe, index_html, "_fzHaversine(48.5,16.3,48.509,16.3)")
    assert nord == pytest.approx(0.009 * M_PER_DEG_LAT, rel=0.02)
    assert 980 < nord < 1020

    # ~1 km nach Osten auf 48,5 Grad Breite (Laengengrade schrumpfen mit cos(lat))
    ost = _eval(node_exe, index_html, "_fzHaversine(48.5,16.3,48.5,16.3136)")
    assert ost == pytest.approx(1000, rel=0.02)

    # gleicher Punkt -> 0
    assert _eval(node_exe, index_html, "_fzHaversine(48.5,16.3,48.5,16.3)") == 0

    # Strings werden gecastet (Supabase liefert numeric gern als String)
    assert _eval(node_exe, index_html, "_fzHaversine('48.5','16.3','48.509','16.3')") == pytest.approx(
        nord, rel=1e-9
    )


def test_haversine_nicht_endliche_eingaben_sind_null(node_exe, index_html):
    for args in (
        "NaN,16.3,48.5,16.3",
        "48.5,undefined,48.5,16.3",
        "48.5,16.3,null,16.3",  # Number(null)===0 -> endlich, aber Distanz real
        "48.5,16.3,48.5,Infinity",
        "'nord',16.3,48.5,16.3",
    ):
        v = _eval(node_exe, index_html, f"_fzHaversine({args})")
        assert isinstance(v, (int, float)), args
        assert math.isfinite(v), args
    # Explizit: kaputte Zahl -> exakt 0 (kein NaN, das die km-Summe vergiftet)
    assert _eval(node_exe, index_html, "_fzHaversine(NaN,16.3,48.5,16.3)") == 0
    assert _eval(node_exe, index_html, "_fzHaversine(48.5,16.3,48.5,'xx')") == 0


# ═══════════════════════════════════════════════════════════════════
# 15) opts.stillMin konfigurierbar
# ═══════════════════════════════════════════════════════════════════
def _pausen_datensatz():
    """Fahrt - 3 Min Pause (Ampel/Kunde) - Fahrt, 30-Sekunden-Ping-Takt."""
    return [
        P(T(13, 0, 0), 48.500, LON0, speed=40),
        P(T(13, 0, 30), 48.505, LON0, speed=40),
        P(T(13, 1, 0), 48.510, LON0, speed=40),  # letzte Bewegung vor der Pause
        P(T(13, 1, 30), 48.510, LON0, speed=0),
        P(T(13, 2, 0), 48.510, LON0, speed=0),
        P(T(13, 2, 30), 48.510, LON0, speed=0),
        P(T(13, 3, 0), 48.510, LON0, speed=0),
        P(T(13, 3, 30), 48.510, LON0, speed=0),
        P(T(13, 4, 0), 48.515, LON0, speed=40),  # es geht weiter
        P(T(13, 4, 30), 48.520, LON0, speed=40),
        P(T(13, 5, 0), 48.525, LON0, speed=40),
    ]


def test_stillMin_konfigurierbar(node_exe, index_html):
    pts = _pausen_datensatz()

    fein = _segs(node_exe, index_html, pts, "{stillMin:1}")
    grob = _segs(node_exe, index_html, pts, "{stillMin:30}")
    default = _segs(node_exe, index_html, pts)

    assert len(fein) > len(grob), (fein, grob)
    assert len(fein) == 2
    assert len(grob) == 1
    assert len(default) == 1  # 3-Min-Pause < default 5 Min -> eine Fahrt

    # stillMin=1: Pause zerschneidet die Fahrt beim letzten Bewegungspunkt.
    assert fein[0]["beginn"] == T(13, 0, 0) and fein[0]["ende"] == T(13, 1, 0)
    assert fein[1]["beginn"] == T(13, 4, 0) and fein[1]["ende"] == T(13, 5, 0)

    # stillMin=30: alles eine Fahrt, die Pause zaehlt zur Fahrtdauer.
    assert grob[0]["beginn"] == T(13, 0, 0) and grob[0]["ende"] == T(13, 5, 0)
    assert grob[0]["dauerMin"] == 5
    assert grob[0]["km"] == pytest.approx(default[0]["km"], abs=0.01)

    # Die Summe der Teil-km liegt unter der Gesamt-km (die Pause-Strecke ist 0, aber der
    # Sprung 48.510 -> 48.515 faellt beim Split heraus).
    assert fein[0]["km"] + fein[1]["km"] < grob[0]["km"] + 0.001
