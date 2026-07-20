"""v3.9.699 — die zwei Betriebstag-Blocker des Stempel-Terminals (Bug-Hunt Befund 1 + 2 + Auflage 1b).

Beide müssen weg, BEVOR das Terminal an die Wand geht — sonst ist der erste Betriebstag ein
Datenschutzvorfall (Befund 1) mit 0-Stunden-Schichten (Befund 2) und grün-lügendem Feedback (1b).

Diese Datei ist zugleich der Beweis für die neue Hausregel „behauptet ein Kommentar eine
Eigenschaft, muss ein Test sie beweisen" — hier für Auflage 1b (Erfolg nur nach Persistenz).
"""
import re
import pytest


# ══════════════════════════════════════════════════════════════════════════════
# Befund 1 — Wandpanel lädt keine Belegschaftsdaten mehr
# ══════════════════════════════════════════════════════════════════════════════
def _bootstrap(index_html):
    m = re.search(r"const _isST=.*?API\.getChecklists\(\)\.catch", index_html, re.S)
    assert m, "Bootstrap-Promise.all mit _isST nicht gefunden"
    return m.group(0)


def test_stempel_terminal_wird_im_bootstrap_erkannt(index_html):
    assert "const _isST=!!(curUser&&curUser.role==='stempel_terminal');" in index_html


def test_terminal_laedt_keinen_der_13_fetches(index_html):
    """Für stempel_terminal muss JEDER der 13 Bootstrap-Fetches ein leeres Array liefern —
    keine projects/time_entries/fahrzeuge im Speicher oder IndexedDB eines öffentlichen Panels."""
    block = _bootstrap(index_html)
    # 13 Fetch-Zeilen, jede muss den _isST-Kurzschluss auf _E (Promise.resolve([])) tragen.
    assert block.count("_isST?_E") >= 11, \
        "Nicht alle Bootstrap-Fetches sind für stempel_terminal auf leer kurzgeschlossen"
    # time_entries + forms sind zusätzlich für BEIDE Kiosk-Rollen leer (auch lager_display).
    assert "_noKioskEnt?_E:API.getEntries" in block
    assert "_noKioskEnt?_E:API.getForms" in block


def test_time_entries_leck_auch_bei_lager_display_geschlossen(index_html):
    """Das schlimmste Leck (Stunden aller MA) darf auch der ältere Lager-Kiosk nicht mehr laden."""
    assert "const _noKioskEnt=_isLD||_isST;" in index_html


def test_sql_sperrt_time_entries_forms_bautagebuch_fuer_kiosk():
    with open("sql/KIOSK_RESTRICTIVE_FIX_v1.sql", encoding="utf-8") as f:
        sql = f.read()
    for tbl in ("time_entries_no_kiosk", "forms_no_kiosk", "bautagebuch_no_kiosk"):
        assert tbl in sql, f"RESTRICTIVE-Sperre {tbl} fehlt"
    # fahrzeuge/projects bewusst NICHT — die Lager-Tafeln brauchen sie (Client-Scoping schützt dort).
    assert "fahrzeuge_no_kiosk" not in sql
    assert "projects_no_kiosk" not in sql


# ══════════════════════════════════════════════════════════════════════════════
# Befund 2 — _sbGet-403-Swallow im Richtungs-Lesepfad
# ══════════════════════════════════════════════════════════════════════════════
def test_stReadLog_entfernt_v782(index_html):
    # v3.9.782: _stReadLog entfernt (0 Aufrufer seit v769 -> Scan via RPC stempel_terminal_stempel).
    # Removal-Regression-Pin: die tote Funktion darf nicht zurueckkehren.
    assert "async function _stReadLog(" not in index_html, "_stReadLog wieder da (tot seit v769)"

@pytest.mark.skip(reason="v769/v782: Scan laeuft ueber RPC stempel_terminal_stempel, nicht mehr ueber _stReadLog; _stReadLog in v782 entfernt.")
def test_process_liest_stempel_log_ueber_stReadLog(index_html):
    """Der Tages-Read im Scan darf NICHT mehr über das auth-schluckende _sbGet laufen."""
    m = re.search(r"async function _process\(uid\)\{.*?_busy\.current=false;", index_html, re.S)
    assert m, "_process nicht gefunden"
    proc = m.group(0)
    # Der Tages-Read (mit ts=gte Tagesstart) läuft über _stReadLog:
    assert "_stReadLog('worker_id=eq." in proc


# ══════════════════════════════════════════════════════════════════════════════
# Auflage 1b — Erfolg NUR nach bestätigter Persistenz (Beweis der Kommentar-Behauptung)
# ══════════════════════════════════════════════════════════════════════════════
def _process(index_html):
    m = re.search(r"async function _process\(uid\)\{.*?_busy\.current=false;", index_html, re.S)
    assert m, "_process nicht gefunden"
    return m.group(0)


@pytest.mark.skip(reason="v3.9.769 Stufe 1 Weg B: der alte Client-INSERT-Scanpfad (Lookup+Read+direkter stempel_log-POST, evCache, SQ.push-Offline-Puffer, Client-Cooldown/Uebernacht/Netto am Panel) ist durch den SECURITY-DEFINER-RPC stempel_terminal_stempel ersetzt. Richtung/Doppel-Scan/Uebernacht leben jetzt im RPC (sql/STEMPEL_TERMINAL_RPC_v3.sql, gepinnt in test_stempel_terminal_rpc_v769), kein-falsches-gruen + Client-Cooldown + unknown-Chip im neuen App-Pfad (ebd.). Dieser Pin testet toten Code.")
def test_online_stempel_ist_ein_awaited_post(index_html):
    proc = _process(index_html)
    assert "await _authRetry(()=>fetch(SB_REST+'/stempel_log'" in proc, \
        "Der Online-Stempel wird nicht als bestätigter POST geschrieben"


@pytest.mark.skip(reason="v3.9.769 Stufe 1 Weg B: der alte Client-INSERT-Scanpfad (Lookup+Read+direkter stempel_log-POST, evCache, SQ.push-Offline-Puffer, Client-Cooldown/Uebernacht/Netto am Panel) ist durch den SECURITY-DEFINER-RPC stempel_terminal_stempel ersetzt. Richtung/Doppel-Scan/Uebernacht leben jetzt im RPC (sql/STEMPEL_TERMINAL_RPC_v3.sql, gepinnt in test_stempel_terminal_rpc_v769), kein-falsches-gruen + Client-Cooldown + unknown-Chip im neuen App-Pfad (ebd.). Dieser Pin testet toten Code.")
def test_harter_fehler_zeigt_nie_gruen_und_queued_nicht(index_html):
    """Ein 403/RLS/Constraint darf NIE grün zeigen und darf NICHT in die Queue (Retry hilft nicht)."""
    proc = _process(index_html)
    # Der Nicht-Netz-Fehlerzweig zeigt error UND returnt (kein Weiterlauf zu grün):
    assert "else{_showFb({kind:'error',name:worker.name});return;}" in proc
    # Nur der Netzfehler queued:
    assert "if(_stErrKind(e)==='net'){SQ.push(" in proc


def test_kein_blindes_sq_push_mehr_vor_dem_gruen(index_html):
    """Regression gegen den alten Zustand: unbedingtes SQ.push direkt gefolgt von grünem Feedback."""
    proc = _process(index_html)
    # Das alte Muster (SQ.push als einzige, bedingungslose Schreibaktion) darf nicht mehr existieren:
    assert "SQ.push({url:'/api/stempel-log',method:'POST',body:row});/* INSERT via SyncQueue" not in proc


@pytest.mark.skip(reason="v3.9.769 Stufe 1 Weg B: der alte Client-INSERT-Scanpfad (Lookup+Read+direkter stempel_log-POST, evCache, SQ.push-Offline-Puffer, Client-Cooldown/Uebernacht/Netto am Panel) ist durch den SECURITY-DEFINER-RPC stempel_terminal_stempel ersetzt. Richtung/Doppel-Scan/Uebernacht leben jetzt im RPC (sql/STEMPEL_TERMINAL_RPC_v3.sql, gepinnt in test_stempel_terminal_rpc_v769), kein-falsches-gruen + Client-Cooldown + unknown-Chip im neuen App-Pfad (ebd.). Dieser Pin testet toten Code.")
def test_feedback_haengt_an_queued_nicht_an_offline(index_html):
    """Die Offline-Quittung greift jetzt bei _queued (offline ODER net-Fallback), nicht nur _offline."""
    proc = _process(index_html)
    assert "if(_queued){netto=null;sub=" in proc
