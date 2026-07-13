"""v3.9.678 Flotte-Status-Modell — pure Status-/Dauer-Helper (Node-eval).

Extrahiert die Funktionen aus dem Sentinel-Block //@FLOTTE-STATUS-START..END in
index.html und evaluiert sie isoliert in Node. Abhaengigkeiten, die ausserhalb des
Blocks leben, werden mitgeliefert:
  - TIME_MINUTE / TIME_HOUR / TIME_DAY  (index.html Z. 671-674, App-Scope-Globals)
  - _flotteInactive                     (//@FLOTTE-HELPERS-Block)

NaN ist in JSON nicht darstellbar: der Snippet serialisiert NaN bewusst als null,
die Tests pruefen entsprechend auf None.
"""
import json
import re

from conftest import run_node_snippet, _extract_fn

# Exakt wie in index.html (Z. 671-674).
_TIME_CONSTS = (
    "const TIME_SECOND=1000;"
    "const TIME_MINUTE=60*TIME_SECOND;"
    "const TIME_HOUR=60*TIME_MINUTE;"
    "const TIME_DAY=24*TIME_HOUR;\n"
)

# NaN -> null, damit JSON.stringify nicht still zu null/Fehler kippt und die Tests
# den Unterschied "kein Wert" vs. "0" sehen.
_JSON_HELPER = (
    "function _out(v){process.stdout.write(JSON.stringify(v,function(k,x){"
    "return (typeof x==='number'&&Number.isNaN(x))?null:x;}));}\n"
)

_DEPS = ["_flotteInactive", "_fzFaehrt", "_fzStatusSeit", "_fzStatus", "_fzDauerFmt"]


def _harness(index_html, expr):
    """Baut den lauffaehigen Node-Snippet: Konstanten + alle Helper + Ausgabe von `expr`."""
    parts = [_TIME_CONSTS, _JSON_HELPER]
    for name in _DEPS:
        fn = _extract_fn(index_html, name)
        assert fn, f"function {name} nicht in index.html gefunden"
        parts.append(fn + "\n")
    parts.append("_out(" + expr + ");")
    return "".join(parts)


def _eval(node_exe, index_html, expr):
    return json.loads(run_node_snippet(node_exe, _harness(index_html, expr)))


# Feste Zeitbasis: 2026-01-15T12:00:00Z
NOW = 1768478400000
MIN = 60000
HOUR = 3600000
DAY = 86400000


def _pos(ts_expr, **kw):
    """JS-Objektliteral fuer eine Position bauen (ts_expr ist bereits JS-Code)."""
    fields = ["ts:" + ts_expr]
    for k, v in kw.items():
        fields.append(k + ":" + v)
    return "{" + ",".join(fields) + "}"


def _ts(ms):
    return "new Date(" + str(ms) + ").toISOString()"


# ── _fzStatus: wartet ──
def test_status_ohne_position_wartet(node_exe, index_html):
    res = _eval(node_exe, index_html, f"_fzStatus(null,{NOW})")
    assert res == {"code": "wartet", "seit": None, "dauerMin": 0}


def test_status_ts_fehlend_wartet(node_exe, index_html):
    # ts komplett abwesend / undefined -> new Date(undefined) = Invalid Date -> NaN
    for latest in ("{speed:50}", "{ts:undefined,speed:50}"):
        res = _eval(node_exe, index_html, f"_fzStatus({latest},{NOW})")
        assert res == {"code": "wartet", "seit": None, "dauerMin": 0}, latest


def test_status_ts_muell_wartet(node_exe, index_html):
    for latest in ("{ts:'kein-datum',speed:50}", "{ts:'',speed:50}", "{ts:'2026-13-45',speed:0}"):
        res = _eval(node_exe, index_html, f"_fzStatus({latest},{NOW})")
        assert res["code"] == "wartet", latest
        assert res["seit"] is None


def test_status_ts_null_ist_wartet_nicht_epoch(node_exe, index_html):
    """JS-Falle: `new Date(null).getTime()` ist 0 (Epoch), NICHT NaN.

    Ohne expliziten null-Guard rutscht ein ts:null durch den isNaN-Check und landet als
    "inaktiv seit 1.1.1970" in der Liste. _fzStatus faengt das seit v3.9.678 ab und liefert
    'wartet' — ein Datensatz ohne Zeitstempel ist kein Zustand, ueber den man etwas weiss.
    """
    for ts in ("null", "undefined", "''"):
        res = _eval(node_exe, index_html, f"_fzStatus({{ts:{ts},speed:50}},{NOW})")
        assert res["code"] == "wartet", f"ts={ts} muss 'wartet' ergeben, nicht {res['code']}"
        assert res["dauerMin"] == 0


# ── _fzStatus: inaktiv (>24h) ──
def test_status_aelter_24h_inaktiv(node_exe, index_html):
    ts = NOW - (DAY + HOUR)  # 25h alt
    p = _pos(_ts(ts), speed="0", ignition="false")
    res = _eval(node_exe, index_html, f"_fzStatus({p},{NOW})")
    assert res["code"] == "inaktiv"
    assert res["seit"] == ts
    assert res["dauerMin"] == 25 * 60


def test_status_inaktiv_ignoriert_seitMs(node_exe, index_html):
    # inaktiv "seit" = letzte Lebensmeldung, NICHT der uebergebene Zustandswechsel.
    ts = NOW - 2 * DAY
    p = _pos(_ts(ts), speed="80", ignition="true")
    seit_ms = NOW - 5 * DAY
    res = _eval(node_exe, index_html, f"_fzStatus({p},{NOW},{seit_ms})")
    assert res["code"] == "inaktiv"
    assert res["seit"] == ts
    assert res["dauerMin"] == 2 * 24 * 60


# ── _fzStatus: faehrt / steht ──
def test_status_speed_50_faehrt(node_exe, index_html):
    p = _pos(_ts(NOW - 5 * MIN), speed="50", ignition="false")
    res = _eval(node_exe, index_html, f"_fzStatus({p},{NOW})")
    assert res["code"] == "faehrt"
    assert res["seit"] == NOW - 5 * MIN
    assert res["dauerMin"] == 5


def test_status_speed_0_zuendung_aus_steht(node_exe, index_html):
    p = _pos(_ts(NOW - 30 * MIN), speed="0", ignition="false")
    res = _eval(node_exe, index_html, f"_fzStatus({p},{NOW})")
    assert res["code"] == "steht"
    assert res["dauerMin"] == 30


def test_status_speed_0_zuendung_an_faehrt(node_exe, index_html):
    # Zuendung an zaehlt als Fahrt, auch bei speed 0 (Ampel, Stau, Ladevorgang).
    p = _pos(_ts(NOW - MIN), speed="0", ignition="true")
    res = _eval(node_exe, index_html, f"_fzStatus({p},{NOW})")
    assert res["code"] == "faehrt"


def test_status_speed_3_ist_noch_kein_fahren(node_exe, index_html):
    # Schwelle ist strikt > 3 (GPS-Rauschen im Stand).
    p = _pos(_ts(NOW - MIN), speed="3", ignition="false")
    assert _eval(node_exe, index_html, f"_fzStatus({p},{NOW})")["code"] == "steht"


def test_status_kaputte_speed_werte_stehen(node_exe, index_html):
    for speed in ("NaN", "'abc'", "null", "undefined"):
        p = _pos(_ts(NOW - MIN), speed=speed, ignition="false")
        res = _eval(node_exe, index_html, f"_fzStatus({p},{NOW})")
        assert res["code"] == "steht", f"speed={speed}"


def test_faehrt_speed_als_string_zahl(node_exe, index_html):
    assert _eval(node_exe, index_html, "_fzFaehrt({speed:'42'})") is True
    assert _eval(node_exe, index_html, "_fzFaehrt({speed:'2'})") is False
    assert _eval(node_exe, index_html, "_fzFaehrt(null)") is False


# ── _fzStatus: seitMs ──
def test_status_mit_seitMs(node_exe, index_html):
    p = _pos(_ts(NOW - 2 * MIN), speed="60", ignition="true")
    seit_ms = NOW - 90 * MIN  # faehrt schon seit 1,5h
    res = _eval(node_exe, index_html, f"_fzStatus({p},{NOW},{seit_ms})")
    assert res["code"] == "faehrt"
    assert res["seit"] == seit_ms
    assert res["dauerMin"] == 90


def test_status_seitMs_nan_faellt_auf_ts_zurueck(node_exe, index_html):
    ts = NOW - 10 * MIN
    p = _pos(_ts(ts), speed="0", ignition="false")
    res = _eval(node_exe, index_html, f"_fzStatus({p},{NOW},NaN)")
    assert res["seit"] == ts
    assert res["dauerMin"] == 10


def test_status_zukunfts_ts_dauer_nicht_negativ(node_exe, index_html):
    p = _pos(_ts(NOW + 5 * MIN), speed="0", ignition="false")
    res = _eval(node_exe, index_html, f"_fzStatus({p},{NOW})")
    assert res["dauerMin"] == 0


# ── _fzStatusSeit ──
def _hist(*entries):
    return "[" + ",".join(entries) + "]"


def test_statusseit_zustandswechsel_begrenzt(node_exe, index_html):
    # desc: faehrt(12:00) faehrt(11:30) steht(11:00) -> seit = 11:30
    h = _hist(
        _pos(_ts(NOW), speed="50"),
        _pos(_ts(NOW - 30 * MIN), speed="40"),
        _pos(_ts(NOW - 60 * MIN), speed="0", ignition="false"),
    )
    assert _eval(node_exe, index_html, f"_fzStatusSeit({h})") == NOW - 30 * MIN


def test_statusseit_alle_gleich_aeltester_punkt(node_exe, index_html):
    h = _hist(
        _pos(_ts(NOW), speed="0", ignition="false"),
        _pos(_ts(NOW - HOUR), speed="0", ignition="false"),
        _pos(_ts(NOW - 3 * HOUR), speed="1", ignition="false"),
    )
    assert _eval(node_exe, index_html, f"_fzStatusSeit({h})") == NOW - 3 * HOUR


def test_statusseit_leere_liste_nan(node_exe, index_html):
    assert _eval(node_exe, index_html, "_fzStatusSeit([])") is None
    assert _eval(node_exe, index_html, "_fzStatusSeit(null)") is None
    assert _eval(node_exe, index_html, "Number.isNaN(_fzStatusSeit([]))") is True


def test_statusseit_nur_kaputte_ts_nan(node_exe, index_html):
    # ts:null waere NICHT "kaputt" (= Epoch 0, siehe test_status_ts_null_wird_zu_epoch...),
    # deshalb hier nur echte Invalid-Date-Faelle.
    h = "[{ts:'quatsch',speed:50},{ts:undefined,speed:0},{ts:'',speed:0},null]"
    assert _eval(node_exe, index_html, f"_fzStatusSeit({h})") is None


def test_statusseit_unsortiert_wird_sortiert(node_exe, index_html):
    # Gleiche Daten wie test_statusseit_zustandswechsel_begrenzt, aber aufsteigend.
    h = _hist(
        _pos(_ts(NOW - 60 * MIN), speed="0", ignition="false"),
        _pos(_ts(NOW - 30 * MIN), speed="40"),
        _pos(_ts(NOW), speed="50"),
    )
    assert _eval(node_exe, index_html, f"_fzStatusSeit({h})") == NOW - 30 * MIN


def test_statusseit_kaputte_eintraege_uebersprungen(node_exe, index_html):
    h = _hist(
        _pos(_ts(NOW), speed="50"),
        "{ts:'nonsense',speed:0,ignition:false}",  # wuerde sonst den Zustand kippen
        "null",
        _pos(_ts(NOW - 45 * MIN), speed="55"),
        _pos(_ts(NOW - 90 * MIN), speed="0", ignition="false"),
    )
    assert _eval(node_exe, index_html, f"_fzStatusSeit({h})") == NOW - 45 * MIN


def test_statusseit_uebernacht_wechsel(node_exe, index_html):
    # steht seit 22:40 des Vortags, Wechsel ueber Mitternacht hinweg gefunden.
    now = 1768478400000  # 2026-01-15 12:00Z
    steht_seit = 1768430400000  # 2026-01-14 22:40Z
    h = _hist(
        "{ts:'2026-01-15T08:00:00Z',speed:0,ignition:false}",
        "{ts:'2026-01-15T02:00:00Z',speed:0,ignition:false}",
        "{ts:'2026-01-14T22:40:00Z',speed:0,ignition:false}",
        "{ts:'2026-01-14T22:30:00Z',speed:70,ignition:true}",
        "{ts:'2026-01-14T21:00:00Z',speed:65,ignition:true}",
    )
    assert _eval(node_exe, index_html, f"_fzStatusSeit({h})") == steht_seit
    # ... und der Status-Aufruf setzt das konsistent um:
    latest = "{ts:'2026-01-15T08:00:00Z',speed:0,ignition:false}"
    res = _eval(node_exe, index_html, f"_fzStatus({latest},{now},_fzStatusSeit({h}))")
    assert res["code"] == "steht"
    assert res["seit"] == steht_seit
    assert res["dauerMin"] == (now - steht_seit) // 60000


def test_statusseit_einzelner_punkt(node_exe, index_html):
    h = _hist(_pos(_ts(NOW - 7 * MIN), speed="80"))
    assert _eval(node_exe, index_html, f"_fzStatusSeit({h})") == NOW - 7 * MIN


# ── _fzDauerFmt ──
def test_dauer_fmt(node_exe, index_html):
    cases = {
        "0": "00:00",
        "5": "00:05",
        "65": "01:05",
        "59": "00:59",
        "600": "10:00",
        "6000": "100:00",  # jenseits 99h NICHT abgeschnitten
        "-3": "00:00",
        "NaN": "00:00",
        "Infinity": "00:00",
        "'abc'": "00:00",
        "90.7": "01:30",  # Nachkommastellen werden abgeschnitten
    }
    expr = "[" + ",".join("_fzDauerFmt(" + k + ")" for k in cases) + "]"
    assert _eval(node_exe, index_html, expr) == list(cases.values())


# ── Label-/Farb-Maps decken alle Codes ab ──
def test_status_maps_vollstaendig(index_html):
    """Jeder von _fzStatus erzeugte code braucht Label UND Farbe — sonst rendert die Liste leer."""
    for var in ("FZ_STATUS_LABEL", "FZ_STATUS_COLOR"):
        m = re.search(r"var\s+" + var + r"\s*=\s*\{([^}]*)\}", index_html)
        assert m, var + " nicht gefunden"
        body = m.group(1)
        for code in ("faehrt", "steht", "inaktiv", "wartet"):
            assert re.search(r"\b" + code + r"\s*:", body), f"{code} fehlt in {var}"
