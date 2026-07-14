"""v3.9.684 Reverse-Geocoding (Phase F3) — Nominatim mit Pflicht-Cache und Drossel.

Nominatims Nutzungspolitik ist keine Empfehlung: max. 1 Request/Sekunde, kein Bulk-Geocoding.
Wer sie verletzt, faengt sich eine IP-Sperre ein — und zwar fuer die ganze Firma.

Die Guards hier sichern genau die Eigenschaften ab, die das verhindern. Die Drossel ist als
pure Funktion (_geoWartezeit) gebaut, damit sie GETESTET und nicht nur behauptet werden kann.

fz_positions ist leer (Tracker nicht bestellt) — alles laeuft gegen Mock-Daten.
"""
import json

from conftest import run_node_snippet, _extract_fn

TIME = "const TIME_SECOND=1000;const TIME_MINUTE=60*TIME_SECOND;const TIME_HOUR=60*TIME_MINUTE;const TIME_DAY=24*TIME_HOUR;"


def _harness(index_html, *names):
    """Pure Functions + ihre Abhaengigkeiten in einen Node-Snippet packen."""
    teile = [
        TIME,
        "const GEO_RUNDUNG=3;",
        "const GEO_MIN_ABSTAND_MS=1100;",
        _extract_fn(index_html, "_n"),
    ]
    for n in names:
        fn = _extract_fn(index_html, n)
        assert fn, f"{n} nicht gefunden"
        teile.append(fn)
    return "\n".join(teile) + "\n"


def _eval(node_exe, index_html, ausdruck, *names):
    snip = _harness(index_html, *names) + f"process.stdout.write(JSON.stringify({ausdruck}));"
    return json.loads(run_node_snippet(node_exe, snip))


# ── Rundungs-Key ─────────────────────────────────────────────────────────────

def test_geo_key_rundet_auf_drei_stellen(node_exe, index_html):
    """3 Dezimalstellen ~ 110 m. Zwei Punkte im selben 110-m-Feld teilen sich EINEN Lookup."""
    r = _eval(node_exe, index_html, "[_geoKey(48.45678,16.00712), _geoKey(48.4569,16.0072)]", "_geoKey")
    assert r[0] == "48.457,16.007"
    assert r[0] == r[1], "Punkte im selben 110-m-Feld muessen denselben Cache-Key ergeben"


def test_geo_key_verwirft_muell(node_exe, index_html):
    # Null-Island = Tracker ohne GPS-Fix. Den zu geocoden waere ein verschenkter Request.
    r = _eval(
        node_exe, index_html,
        "[_geoKey(0,0), _geoKey(NaN,16.0), _geoKey(48.4,'abc'), _geoKey(null,null)]",
        "_geoKey",
    )
    assert r == ["", "", "", ""]


def test_geo_key_negative_koordinaten(node_exe, index_html):
    r = _eval(node_exe, index_html, "_geoKey(-33.8688,151.2093)", "_geoKey")
    assert r == "-33.869,151.209"


# ── Drossel (die eigentliche Schutzmauer) ────────────────────────────────────

def test_drossel_kein_zweiter_request_unter_einer_sekunde(node_exe, index_html):
    """Direkt nach einem Request muss gewartet werden — mindestens bis 1100 ms um sind."""
    r = _eval(
        node_exe, index_html,
        "[_geoWartezeit(10000,10000), _geoWartezeit(10000,10500), _geoWartezeit(10000,11099)]",
        "_geoWartezeit",
    )
    assert r[0] == 1100, "sofort nach einem Request: volle Wartezeit"
    assert r[1] == 600, "nach 500ms: noch 600ms warten"
    assert r[2] == 1, "1ms vor Ablauf: noch 1ms warten"
    for w in r:
        assert w > 0, "es darf NIE 0 Wartezeit sein, solange die Sekunde nicht um ist"


def test_drossel_gibt_frei_wenn_abstand_erreicht(node_exe, index_html):
    r = _eval(
        node_exe, index_html,
        "[_geoWartezeit(10000,11100), _geoWartezeit(10000,20000), _geoWartezeit(0,5000)]",
        "_geoWartezeit",
    )
    assert r == [0, 0, 0]  # genau erreicht / lange her / noch nie angefragt


def test_drossel_robust_gegen_muell(node_exe, index_html):
    # Kaputte Uhr darf nicht dazu fuehren, dass die Drossel AUSFAELLT (= Request-Sturm).
    r = _eval(
        node_exe, index_html,
        "[_geoWartezeit(10000,NaN), _geoWartezeit(NaN,10000), _geoWartezeit(-5,10000)]",
        "_geoWartezeit",
    )
    assert r[0] == 1100, "unbrauchbare Jetzt-Zeit -> lieber voll warten als losstuermen"
    assert r[1] == 0
    assert r[2] == 0


# ── Adress-Formatierung ──────────────────────────────────────────────────────

def test_ort_format_wie_fink(node_exe, index_html):
    j = {"address": {"village": "Kirchberg am Wagram", "road": "Marktplatz", "house_number": "7"}}
    r = _eval(node_exe, index_html, f"_geoOrtAus({json.dumps(j)})", "_geoOrtAus")
    assert r == "Kirchberg am Wagram, Marktplatz 7"


def test_ort_format_robust_bei_luecken(node_exe, index_html):
    faelle = [
        ({"address": {"town": "Tulln", "road": "Hauptstraße"}}, "Tulln, Hauptstraße"),
        ({"address": {"city": "Wien"}}, "Wien"),
        ({"address": {"road": "Feldweg"}}, "Feldweg"),
        ({"address": {}, "display_name": "Acker, Gemeinde X, Bezirk Y, Österreich"}, "Acker, Gemeinde X"),
        ({}, ""),
    ]
    for j, erwartet in faelle:
        r = _eval(node_exe, index_html, f"_geoOrtAus({json.dumps(j)})", "_geoOrtAus")
        assert r == erwartet, f"{j} -> {r!r}, erwartet {erwartet!r}"


def test_ort_format_kein_crash_bei_null(node_exe, index_html):
    r = _eval(node_exe, index_html, "[_geoOrtAus(null), _geoOrtAus(undefined)]", "_geoOrtAus")
    assert r == ["", ""]


# ── Fallback ────────────────────────────────────────────────────────────────

def test_koordinaten_fallback(node_exe, index_html):
    r = _eval(node_exe, index_html, "[_geoFallback(48.45678,16.00712), _geoFallback(NaN,1)]",
              "_geoFallback", "_n")
    assert r[0] == "48.45678, 16.00712"
    assert r[1] == "—"


# ── Struktur-Guards (was Node nicht pruefen kann) ────────────────────────────

def test_csp_erlaubt_nominatim(index_html):
    # Ohne CSP-Eintrag wird jeder Lookup vom Browser geblockt — und zwar still.
    assert "connect-src 'self' https://jiggujpruejkaomgxarp.supabase.co" in index_html
    assert "https://nominatim.openstreetmap.org;" in index_html


def test_429_setzt_lookups_fuer_die_session_aus(index_html):
    # Kein Retry-Sturm. Ein 429 heisst: aufhoeren, nicht nochmal versuchen.
    assert "if(r.status===429){_geoDisabled=true;" in index_html
    assert "if(_geoIstAus())break;" in index_html


def test_serielle_queue_kein_parallel_fetch(index_html):
    # Eine einzige Kette. Parallel-Fetch wuerde die 1-req/s-Regel sofort brechen.
    assert "var _geoChain=Promise.resolve();" in index_html
    assert "_geoChain=_geoChain.then(async function(){" in index_html
    assert "const w=_geoWartezeit(_geoLastMs,Date.now());" in index_html


def test_timeout_statt_spinner_haenger(index_html):
    assert "ctl.abort();}catch(_e){}},8000);" in index_html


def test_cache_vor_dem_netz(index_html):
    # Reihenfolge: an der Fahrt gespeichert -> geo_cache (EIN Batch) -> Nominatim.
    assert "async function _geoCacheGet(keys){" in index_html
    assert "const ausDb=await _geoCacheGet(keys);" in index_html
    assert "async function _geoCacheSet(key,ort,lat,lon){" in index_html
    assert "_geoCacheSet(k,ort,c.lat,c.lon);" in index_html
    # Treffer wandert an die Fahrt -> beim naechsten Mal gar kein Lookup mehr.
    assert "patch.start_ort=_geoMem[ka];" in index_html
    assert "patch.ziel_ort=_geoMem[kb];" in index_html


def test_kein_bulk_geocoding(index_html):
    # Deckel pro Ladevorgang, und die Kuerzung wird GENANNT statt verschwiegen.
    assert "const GEO_MAX_PRO_LADEN=25;" in index_html
    assert "keys=keys.slice(0,GEO_MAX_PRO_LADEN);" in index_html
    assert "kein Bulk-Geocoding, Nominatim-Policy" in index_html


def test_leerzustand_kein_lookup(index_html):
    # fz_positions ist leer -> keine Segmente -> kein einziger Request.
    assert "if(!sList||!sList.length)return;" in index_html


def test_export_zeigt_denselben_ort_wie_der_bildschirm(index_html):
    # Exportkonsistenz Bildschirm = Datei (v3.9.676). Der Export ruft dasselbe _ort auf.
    fb = index_html[index_html.index("function FahrtenbuchView(props){"):]
    fb = fb[: fb.index("\nfunction FlotteView(props){")]
    assert fb.count("_ort(row,'start_ort',") >= 3, "Desktop, Mobile und Export muessen _ort nutzen"
    assert fb.count("_ort(row,'ziel_ort',") >= 3


def test_sql_gestaged(index_html):
    from pathlib import Path

    p = Path(__file__).parent.parent / "sql" / "GEO_CACHE_v1.sql"
    assert p.exists()
    sql = p.read_text(encoding="utf-8")
    assert "HUMAN-RUN-GATE" in sql
    assert "CREATE TABLE IF NOT EXISTS public.geo_cache" in sql
    assert "geo_key    text PRIMARY KEY" in sql
    # RLS: lesen fuer authenticated, lager_display RESTRICTIVE geblockt
    assert "FOR SELECT TO authenticated USING (true)" in sql
    assert "AS RESTRICTIVE" in sql and "lager_display" in sql
    # Ortsspalten an der Fahrt, idempotent
    assert "ADD COLUMN IF NOT EXISTS start_ort text" in sql
    assert "ADD COLUMN IF NOT EXISTS ziel_ort  text" in sql
