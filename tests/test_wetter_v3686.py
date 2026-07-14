"""v3.9.686 Wetter — Planungs-Wetterzeile zeigte HARTCODIERTE Demo-Daten.

Live-Befund 14.07.2026: Die Planung zeigte fuer KW29 (13.–18.07.) 4°/2°/7°/5°/6°/3° —
Wintertemperaturen im Hochsommer, waehrend das Home-Widget daneben korrekt 32° meldete.

Root Cause war NICHT ein Feld- oder Index-Fehler, sondern eine Attrappe: der Streifen las ein
statisches Array ("network disabled — static plausible data for current week") und hat nie eine
API aufgerufen. Die Zahlen 4/2/7/5/6/3 standen so im Quelltext.

Diese Guards sichern das ab:
  1. Die Demo-Daten sind weg und kommen nicht zurueck.
  2. Es gibt EINE Wettercode-Tabelle, nicht zwei driftende Kopien.
  3. Die Zuordnung Tag -> Wert laeuft ueber das ISO-DATUM, nicht ueber den Array-Index.
     Ein Off-by-one ist damit strukturell unmoeglich — und genau das war der erste Verdacht.
  4. Fehlt ein Tag (Open-Meteo liefert nur ein begrenztes Fenster), erscheint "—" statt einer
     erfundenen Zahl.
"""
import json

from conftest import run_node_snippet, _extract_fn


def _harness(index_html):
    """WMO_ICON/WMO_TEXT sind plain Objekt-Konstanten.

    conftest._extract_fn kann die NICHT extrahieren: seit dem Parameterlisten-Fix sucht er erst
    eine geschlossene `(...)`, und ein Objekt-Literal hat keine — er greift dann eine weit
    entfernte Klammer und schneidet den falschen Block heraus. Darum hier zeilenweise per Regex.
    """
    import re

    teile = []
    for name in ("WMO_ICON", "WMO_TEXT"):
        m = re.search(rf"^const {name}=\{{.*?\}};$", index_html, re.M)
        assert m, f"{name} nicht gefunden"
        teile.append(m.group(0))
    fn = _extract_fn(index_html, "_wetterMap")
    assert fn, "_wetterMap nicht gefunden"
    teile.append(fn)
    return "\n".join(teile) + "\n"


def _eval(node_exe, index_html, ausdruck):
    snip = _harness(index_html) + f"process.stdout.write(JSON.stringify({ausdruck}));"
    return json.loads(run_node_snippet(node_exe, snip))


# Mock-Antwort von Open-Meteo fuer KW29/2026 (Mo 13.07. – Sa 18.07.), Sommerwerte.
MOCK = {
    "time": ["2026-07-13", "2026-07-14", "2026-07-15", "2026-07-16", "2026-07-17", "2026-07-18"],
    "temperature_2m_max": [32.1, 30.4, 29.8, 32.0, 26.3, 24.7],
    "temperature_2m_min": [18.0, 17.2, 16.9, 18.5, 15.1, 14.0],
    "weather_code": [0, 1, 2, 3, 61, 95],
}


def test_mapping_tag_auf_wert(node_exe, index_html):
    """Mo–Sa muessen exakt ihre eigenen Werte bekommen — kein Verrutschen um einen Tag."""
    m = _eval(node_exe, index_html, f"_wetterMap({json.dumps(MOCK)})")
    assert m["2026-07-13"]["tmax"] == 32.1
    assert m["2026-07-14"]["tmax"] == 30.4
    assert m["2026-07-15"]["tmax"] == 29.8
    assert m["2026-07-16"]["tmax"] == 32.0
    assert m["2026-07-17"]["tmax"] == 26.3
    assert m["2026-07-18"]["tmax"] == 24.7
    assert len(m) == 6


def test_tagesmax_nicht_nachttemperatur(node_exe, index_html):
    """Der urspruengliche Verdacht war "liest tmin statt tmax". Hier festgenagelt."""
    m = _eval(node_exe, index_html, f"_wetterMap({json.dumps(MOCK)})")
    assert m["2026-07-13"]["tmax"] == 32.1
    assert m["2026-07-13"]["tmin"] == 18.0
    assert m["2026-07-13"]["tmax"] != m["2026-07-13"]["tmin"]


def test_wettercode_zu_icon_und_text(node_exe, index_html):
    m = _eval(node_exe, index_html, f"_wetterMap({json.dumps(MOCK)})")
    assert m["2026-07-13"]["text"] == "Klar"
    assert m["2026-07-16"]["text"] == "Bedeckt"
    assert m["2026-07-17"]["text"] == "L. Regen"
    assert m["2026-07-18"]["text"] == "Gewitter"
    assert m["2026-07-13"]["icon"] != ""


def test_luecken_und_muell(node_exe, index_html):
    """Fehlende/kaputte Werte -> null, nicht NaN und nicht 0. Die UI zeigt dann '—'."""
    kaputt = {
        "time": ["2026-07-13", "2026-07-14"],
        "temperature_2m_max": [None, "abc"],
        "temperature_2m_min": [None, None],
        "weather_code": [None, 999],
    }
    m = _eval(node_exe, index_html, f"_wetterMap({json.dumps(kaputt)})")
    assert m["2026-07-13"]["tmax"] is None
    assert m["2026-07-14"]["tmax"] is None, "'abc' darf nicht als 0 durchrutschen"
    assert m["2026-07-13"]["icon"] == ""
    assert m["2026-07-14"]["icon"] == "", "unbekannter WMO-Code -> kein Icon, kein Absturz"


def test_leere_antwort(node_exe, index_html):
    for a in ("_wetterMap(null)", "_wetterMap({})", "_wetterMap({time:[]})"):
        assert _eval(node_exe, index_html, a) == {}


# ── Struktur-Guards ─────────────────────────────────────────────────────────

def test_demo_daten_sind_weg(index_html):
    assert "const weatherDemo=[" not in index_html, "die Attrappe ist zurueck"
    assert "network disabled — static plausible data" not in index_html
    # Die konkreten Fantasiewerte duerfen nirgends mehr stehen.
    assert 'temp:4,desc:"bewölkt"' not in index_html


def test_planung_nutzt_echte_daten(index_html):
    assert "const w=wetter[dk(dayDate(i))]||null;" in index_html, (
        "Zuordnung muss ueber das ISO-Datum laufen, nicht ueber den Array-Index"
    )
    assert "fetch(_wetterUrl(WETTER_LAT,WETTER_LON,von,bis)" in index_html
    # Der Abruf haengt an der ANGEZEIGTEN KW, nicht an "heute".
    assert "},[kw,yr]);" in index_html


def test_fehlender_tag_zeigt_strich(index_html):
    assert '(w&&w.tmax!==null)?(Math.round(w.tmax)+"°"):"—"' in index_html


def test_eine_wettercode_tabelle(index_html):
    """Home hatte eine eigene Kopie. Zwei Tabellen driften unweigerlich auseinander."""
    assert "const WMO=WMO_ICON;" in index_html
    assert "const WMO_D=WMO_TEXT;" in index_html
    assert index_html.count('const WMO_ICON={0:"☀️"') == 1
    assert index_html.count('const WMO={0:"☀️"') == 0


def test_vienna_zeitzone(index_html):
    # Ohne timezone-Parameter liefert Open-Meteo UTC-Tage — der Tageswechsel laege dann falsch.
    assert "&timezone=Europe%2FVienna" in index_html


def test_mausrad_zoomt_nicht_sofort(index_html):
    # v3.9.686 Block B: Zoom erst nach Klick in die Karte.
    assert "L.map(_mapEl.current,{zoomControl:true,scrollWheelZoom:false})" in index_html
    assert "map.on('click',function(){try{map.scrollWheelZoom.enable();}catch(_e){}});" in index_html
    assert "map.on('mouseout',function(){try{map.scrollWheelZoom.disable();}catch(_e){}});" in index_html
