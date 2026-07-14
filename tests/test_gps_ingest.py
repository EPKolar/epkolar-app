"""gps_ingest — die Aufnahme der GPS-Rohpunkte (Traccar -> fz_positions).

Die Edge-Function ist NICHT deployt (wartet auf Sebastians Go) und `fz_positions` ist leer.
Es gibt also keinen einzigen echten Datenpunkt, an dem sich irgendetwas verifizieren liesse.
Umso wichtiger sind diese Tests: sie halten die Entscheidungen fest, die man beim ersten
echten Tracker-Punkt nicht mehr in Ruhe treffen kann.

Die vier Traccar-Eigenheiten, an denen Integrationen reihenweise scheitern:

1. `position.speed` ist in KNOTEN, nicht km/h. Wer das ungerechnet speichert, hat eine Flotte,
   die dauerhaft ~46 % zu langsam faehrt (1 kn = 1,852 km/h) — und niemandem faellt es auf,
   weil 50 statt 93 km/h plausibel aussieht.
2. `device.uniqueId` ist die IMEI und der EINZIGE Schluessel zum Fahrzeug. Fehlt sie am
   Fahrzeug, ist der Punkt nicht zuordenbar — das ist ein Stammdaten-Problem im Buero, kein
   Fehler der Function. Darum 200 statt 500: bei != 2xx wiederholt Traccar den Forward endlos
   und muellt die Queue mit einem Zustand zu, den nur Menschen aufloesen koennen.
3. `fixTime` ist der Zeitpunkt der ORTUNG, `serverTime` nur der des Empfangs. Nimmt man
   serverTime, verschiebt eine Funkloch-Nachlieferung die halbe Fahrt.
4. Traccar WIEDERHOLT fehlgeschlagene Forwards. Ohne Eindeutigkeit legt jede Wiederholung
   denselben Punkt nochmal an und verfaelscht Tageskilometer und Durchschnittsgeschwindigkeit.
"""
import io
import os

import pytest

FN = os.path.join("supabase", "functions", "gps_ingest", "index.ts")


@pytest.fixture(scope="module")
def src():
    with io.open(FN, encoding="utf-8") as f:
        return f.read()


# ── 1) Knoten -> km/h ─────────────────────────────────────────────────────────
def test_knoten_werden_umgerechnet(src):
    assert "KNOTS_TO_KMH = 1.852" in src
    assert "knots * KNOTS_TO_KMH" in src


def test_speed_wird_nicht_roh_gespeichert(src):
    """Ein `speed: p.speed` waere der klassische Traccar-Fehler."""
    assert "speed: p.speed" not in src
    assert "speed: speedKmh" in src


# ── 2) IMEI-Mapping ───────────────────────────────────────────────────────────
def test_imei_kommt_aus_device_uniqueid(src):
    assert "dev.uniqueId" in src


def test_imei_wird_gegen_tracker_imei_aufgeloest(src):
    assert '.eq("tracker_imei", imei)' in src


def test_unbekannte_imei_gibt_200_und_wird_gemeldet(src):
    """NICHT 500: sonst wiederholt Traccar endlos einen Zustand, den nur das Buero
    aufloesen kann (IMEI am Fahrzeug eintragen)."""
    assert "unmapped" in src
    assert 'ok: true' in src


def test_db_fehler_gibt_dagegen_500(src):
    """Hier IST der Retry richtig: ein DB-Ausfall geht vorbei, eine fehlende IMEI nicht."""
    assert '"insert_failed"' in src
    assert "}, 500)" in src


# ── 3) Zeitstempel ────────────────────────────────────────────────────────────
def test_fixtime_hat_vorrang_vor_servertime(src):
    assert "p.fixTime || p.deviceTime || p.serverTime" in src


# ── 4) Idempotenz ─────────────────────────────────────────────────────────────
def test_insert_ist_idempotent(src):
    assert 'onConflict: "fahrzeug_id,ts"' in src
    assert "ignoreDuplicates: true" in src


def test_unique_index_existiert_im_sql(src):
    """Ohne den Index ist das ON CONFLICT oben wirkungslos."""
    with io.open(os.path.join("sql", "GPS_INGEST_v1.sql"), encoding="utf-8") as f:
        sql = f.read()
    assert "CREATE UNIQUE INDEX IF NOT EXISTS fz_positions_fahrzeug_ts_uidx" in sql
    assert "(fahrzeug_id, ts)" in sql


# ── Plausibilitaets-Filter ────────────────────────────────────────────────────
def test_nullinsel_wird_verworfen(src):
    """Ein Tracker ohne Fix meldet gern 0/0 — die Nullinsel im Golf von Guinea. Ein
    einziger solcher Punkt zieht die Kartenansicht nach Afrika und macht jede
    Distanzrechnung der Fahrt kaputt."""
    assert "lat === 0 && lon === 0" in src


def test_ungueltiger_fix_wird_verworfen(src):
    assert "p.valid === false" in src


def test_koordinaten_werden_auf_wertebereich_geprueft(src):
    assert "lat < -90 || lat > 90 || lon < -180 || lon > 180" in src


# ── Sicherheit ────────────────────────────────────────────────────────────────
def test_ohne_token_verweigert_die_function_den_dienst(src):
    """Lieber laut scheitern als ungeschuetzt fremde Positionen annehmen."""
    assert 'Deno.env.get("GPS_INGEST_TOKEN")' in src
    assert '"not_configured"' in src
    assert '"unauthorized"' in src


def test_token_geht_per_header_ODER_query(src):
    """Aeltere Traccar-Versionen koennen keine Custom-Header im Forward — dann bleibt
    nur der Query-Parameter."""
    assert 'req.headers.get("x-gps-token")' in src
    assert 'url.searchParams.get("token")' in src


def test_schreibt_mit_service_role(src):
    """fz_positions hat bewusst KEINE Insert-Policy: nur diese Function darf Rohpunkte
    anlegen, sonst waere das Fahrtenbuch faelschbar."""
    assert 'Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")' in src


def test_rohpunkt_wird_aufgehoben(src):
    """Was wir heute nicht auswerten, wollen wir spaeter nicht neu erfinden muessen."""
    assert "raw: p" in src
