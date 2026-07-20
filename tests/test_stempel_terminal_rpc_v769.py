# -*- coding: utf-8 -*-
"""v3.9.769 — Stempeluhr Stufe 1, Weg B: SECURITY-DEFINER-RPC statt direktem stempel_log-INSERT.

Modell (Sebastian): Das Wandpanel ist NICHT eingeloggt. Chip-Scan → Panel liest nfc_uid → ruft
den RPC `stempel_terminal_stempel(p_nfc_uid)`. Der RPC schlägt den Worker nach, bestimmt die
Richtung server-seitig und bucht in stempel_log. Das Panel bekommt nur {worker_name, richtung, ts}.

Diese Tests prüfen die APP-Seite statisch (der RPC selbst ist SQL/Human-Run-Gate, seine Härte wird
im Endreport Zeile für Zeile belegt). Zusätzlich: der SQL-File-Vertrag (die Härte-Auflagen als
Text-Pins, damit der committete RPC-Body nicht unbemerkt aufweicht).
"""
import re
import os


def _tafel(index_html):
    start = index_html.index("function StempelTafel(")
    end = index_html.index("\n}", index_html.index("return h('div'", start))
    return index_html[start:end]


def _process(index_html):
    """Der Scan-Handler _process innerhalb StempelTafel."""
    t = _tafel(index_html)
    i = t.index("if(_amodeRef.current)return;")
    return t[i:i + 3500]


# ============================================================ App: RPC statt INSERT

def test_scan_ruft_rpc(index_html):
    proc = _process(index_html)
    assert "rpc/stempel_terminal_stempel" in proc, "Scan-Handler ruft den Stempel-RPC nicht"
    assert "p_nfc_uid:clean" in proc, "die rohe nfc_uid wird nicht an den RPC uebergeben"


def test_kein_direkter_insert_mehr_im_scan(index_html):
    """Der Scan-Handler darf stempel_log nicht mehr direkt beschreiben (kein Login am Terminal)."""
    proc = _process(index_html)
    assert "SB_REST+'/stempel_log'" not in proc, \
        "Scan-Handler schreibt noch direkt in stempel_log statt ueber den RPC"
    assert "_wkRef.current.find" not in proc, \
        "Scan-Handler macht noch einen Client-Worker-Lookup — im Weg B macht das der RPC"


def test_nur_name_richtung_ts_zurueck(index_html):
    """Panel liest nur {worker_name, richtung, ts} — keine Loehne/Projekte/Netto am Wandpanel."""
    proc = _process(index_html)
    assert "_res.worker_name" in proc and "_res.richtung" in proc, "Feedback nutzt nicht die RPC-Felder"
    assert "_stTagNetto" not in proc, "Netto wird noch am Panel gerechnet — gehoert nicht ans Terminal"
    assert "netto=_stTagNetto" not in proc


def test_b1a_doppelscan_client_cooldown(index_html):
    proc = _process(index_html)
    assert "_lastScan.current[clean]" in proc, "kein Client-Cooldown per UID"
    assert "<12000" in proc, "12s-Cooldown (v662) nicht verdrahtet"


def test_b1b_ehrlich_kein_falsches_gruen(index_html):
    proc = _process(index_html)
    assert "if(!_rpcOk||!_res){_showFb({kind:'error'" in proc, \
        "kein Erfolg muss zu 'error' fuehren — kein falsches gruen (B1b)"
    assert "_res.error==='unknown_chip'" in proc, "unbekannter Chip nicht auf 'unknown' gemappt"
    # kein Offline-Puffer/Queue mehr im Scan-Pfad (Stufe 1: RPC braucht Netz)
    assert "SQ.push" not in proc, "Stufe 1 hat keinen Offline-Puffer im Scan-Pfad (RPC-only)"


def test_b1c_feedback_kinds(index_html):
    """kommen/gehen/unknown/dup existieren als Vollbild-kinds."""
    tafel = _tafel(index_html)
    for k in ("fb.kind==='kommen'", "fb.kind==='gehen'", "fb.kind==='dup'", "fb.kind==='unknown'"):
        assert k in tafel, "Feedback-kind fehlt: " + k


def test_terminal_ueberspringt_worker_load(index_html):
    tafel = _tafel(index_html)
    assert "if(props.terminal){return ()=>{alive=false;};}" in tafel, \
        "das echte Terminal laedt weiter die Worker-Liste (toter stempel_terminal_workers-Call + Banner)"


# ============================================================ SQL-File-Vertrag (Härte-Pins)

def _sql(index_html_path=None):
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(here, "sql", "STEMPEL_TERMINAL_RPC_v3.sql")
    with open(p, encoding="utf-8") as f:
        return f.read()


def test_sql_datei_existiert():
    assert _sql(), "sql/STEMPEL_TERMINAL_RPC_v3.sql fehlt"


def test_sql_haerte_definer_searchpath():
    sql = _sql()
    assert "SECURITY DEFINER" in sql, "RPC ist nicht SECURITY DEFINER"
    assert "SET search_path = public" in sql, "search_path nicht fest gesetzt (DEFINER-Hijack-Schutz)"


def test_sql_grant_eng():
    sql = _sql()
    assert "REVOKE ALL ON FUNCTION public.stempel_terminal_stempel(text) FROM PUBLIC;" in sql, \
        "kein REVOKE FROM PUBLIC"
    assert "GRANT EXECUTE ON FUNCTION public.stempel_terminal_stempel(text) TO anon, authenticated;" in sql, \
        "GRANT nicht eng auf anon+authenticated"


def test_sql_unknown_chip_ohne_leak():
    sql = _sql()
    assert "'unknown_chip'" in sql, "unbekannter Chip nicht als definierter Fehler"
    # kein Zugriff auf sensible Tabellen — nur die CODE-Zeilen prüfen (Kommentare nennen sie bewusst)
    code = "\n".join(z for z in sql.split("\n") if not z.lstrip().startswith("--")).lower()
    for verboten in ("public.users", "projects", "time_entries", "svnr"):
        assert verboten not in code, "RPC-Code greift auf verbotene Quelle zu: " + verboten
    # gelesen/geschrieben werden darf NUR workers + stempel_log
    assert "public.workers" in code and "public.stempel_log" in code


def test_sql_doppelscan_und_richtung():
    sql = _sql()
    assert "interval '12 seconds'" in sql, "kein 12s-Doppel-Scan-Schutz im RPC"
    assert "interval '18 hours'" in sql, "kein 18h-Uebernacht-Fenster im RPC"
    assert "gen_random_uuid()" in sql, "id wird nicht server-seitig erzeugt"
    assert "'terminal:rpc'" in sql, "device-Kennung fehlt"


def test_sql_keine_neue_anon_insert_policy():
    sql = _sql()
    assert "CREATE POLICY" not in sql.upper(), \
        "SQL legt eine Policy an — der DEFINER-RPC soll der EINZIGE Schreibweg sein, keine anon-INSERT-Policy"
