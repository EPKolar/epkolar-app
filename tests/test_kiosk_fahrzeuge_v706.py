# -*- coding: utf-8 -*-
"""v3.9.706 — 🚛-Spezialfahrzeuge am lager_display-Kiosk: kontrollierter Lesepfad + Diagnose-Zeile.

Fix dreiteilig, KEINE RLS-Lockerung:
  1. SECURITY-DEFINER-RPC public.kiosk_fahrzeuge() (Hausmuster v695), nur 5 Felder, kein PII.
  2. Client: lager_display laedt via _loadKioskFahrzeuge() -> RPC; Fallback auf rohen Read
     solange RPC fehlt ('missing'); Fehler NIE still zu [] (window.__kioskFzErr).
  3. Diagnose-Zeile im Tafel-Kopf (pure _kioskDiagLine).

Die Diagnose-Zeilen-Ableitung wird per Node WIRKLICH ausgefuehrt (nicht nur strukturell gepinnt).
"""
import os
import re
import subprocess


# ── Teil 1: RPC-SQL ─────────────────────────────────────────────────────────

def _sql(repo_root):
    with open(os.path.join(repo_root, "sql", "KIOSK_FAHRZEUGE_v1.sql"), "r", encoding="utf-8") as f:
        return f.read()


def test_rpc_security_definer_and_gate(repo_root):
    sql = _sql(repo_root)
    assert "CREATE OR REPLACE FUNCTION public.kiosk_fahrzeuge()" in sql
    assert "SECURITY DEFINER" in sql
    # Hausmuster v695: harte Rollenpruefung im Body, is_staff() ODER lager_display
    assert "public.auth_role() = 'lager_display'" in sql
    assert "public.is_staff()" in sql
    assert "42501" in sql  # not authorized


def test_rpc_returns_only_panel_fields_no_pii(repo_root):
    sql = _sql(repo_root)
    # v3.9.708: RETURNS TABLE (flach, benannte Spalten) statt SETOF jsonb — sonst kann PostgREST
    # das Ergebnis unter dem Funktionsnamen verschachteln und f.typ wird undefined (FZ:>0, Spez:0).
    assert "RETURNS TABLE(id text, kennzeichen text, typ text, modell text, status text)" in sql
    assert "SETOF jsonb" not in sql.split("$function$")[1]  # nicht im Funktionskoerper (Kommentar erlaubt)
    for field in ("f.id::text", "f.kennzeichen::text", "f.typ::text", "f.modell::text", "f.status::text"):
        assert field in sql
    # KEIN PII / Fuhrpark-Interna am oeffentlichen Wandpanel. Ein Feld wird nur AUSGEGEBEN, wenn es
    # als quotierter jsonb-Key auftaucht ('feld') — der erklaerende Kommentar nennt die Woerter bewusst.
    for forbidden in ("tank_log", "km_stand", "km_log", "fahrer", "serviceheft", "pickerl"):
        assert ("'%s'" % forbidden) not in sql, "RPC darf %s nicht ausgeben" % forbidden


def test_rpc_grant_and_idempotent_safe(repo_root):
    sql = _sql(repo_root)
    assert "REVOKE ALL   ON FUNCTION public.kiosk_fahrzeuge() FROM public, anon;" in sql
    assert "GRANT EXECUTE ON FUNCTION public.kiosk_fahrzeuge() TO authenticated;" in sql
    # gefahrlos: keine DROP/ALTER auf Fremdobjekte, kein Policy-Eingriff
    assert "DROP POLICY" not in sql
    assert "ALTER TABLE" not in sql
    # $function$ sauber terminiert (die Semikolon-Falle aus TERMINAL_FINAL_v3)
    assert "$function$;" in sql
    assert sql.count("$function$") == 2


# ── Teil 2: Client-Ladeweg + Fallback ───────────────────────────────────────

def test_client_rpc_loader_present(index_html):
    assert 'fetch(SB_REST+"/rpc/kiosk_fahrzeuge"' in index_html
    assert "async function _kioskFahrzeuge()" in index_html
    assert "async function _loadKioskFahrzeuge()" in index_html


def test_client_missing_rpc_fallback_to_raw_read(index_html):
    # bei _stErrKind==='missing' Fallback auf den rohen Read (Push bricht den Kiosk nie)
    seg = index_html.split("async function _loadKioskFahrzeuge()", 1)[1][:900]
    assert "_stErrKind(e)" in seg
    assert "if(kind==='missing')" in seg
    assert "API.getFahrzeuge()" in seg


def test_client_error_not_silently_swallowed(index_html):
    # v699-Lektion: Fehlerart durchreichen, nicht still zu []
    seg = index_html.split("async function _loadKioskFahrzeuge()", 1)[1][:900]
    assert "window.__kioskFzErr=" in seg
    assert "console.error(" in seg


def test_bootstrap_routes_lager_display_via_rpc(index_html):
    assert "_isST?_E:(_isLD?_loadKioskFahrzeuge():API.getFahrzeuge().catch(()=>null))" in index_html


def test_other_roles_load_path_unchanged(index_html):
    # Admin-Preview + alle anderen: weiterhin roher Read (im selben Ternary rechts vom _isLD)
    assert "_isLD?_loadKioskFahrzeuge():API.getFahrzeuge().catch(()=>null)" in index_html


# ── Teil 3: Diagnose-Zeile (pure) — echt ausgefuehrt ────────────────────────

def test_diagline_present_and_exported(index_html):
    assert "function _kioskDiagLine(ver,fzLen,spezLen,errKind)" in index_html
    assert "window._kioskDiagLine=_kioskDiagLine;" in index_html
    # im Tafel-Kopf gerendert
    assert "_diagLine=" in index_html
    assert "window.__kioskFzErr" in index_html


def test_diagline_behavior_executed(index_html, node_exe, tmp_path):
    m = re.search(r"function _kioskDiagLine\(.*?\n\}", index_html, re.S)
    assert m, "_kioskDiagLine nicht gefunden"
    js = m.group(0) + u"""
var cases=[
 [_kioskDiagLine('3.9.706',5,2,null),      'v3.9.706 · FZ:5 · Spez:2'],
 [_kioskDiagLine('3.9.706',0,0,null),      'v3.9.706 · FZ:0 · Spez:0'],
 [_kioskDiagLine('3.9.706',0,0,'missing'), 'v3.9.706 · FZ:Fehler(missing)'],
 [_kioskDiagLine('3.9.706',3,1,'net'),     'v3.9.706 · FZ:Fehler(net)'],
 [_kioskDiagLine('3.9.706',5,2,'ok'),      'v3.9.706 · FZ:5 · Spez:2']
];
for(var i=0;i<cases.length;i++){ if(cases[i][0]!==cases[i][1]){ console.error('FAIL: ['+cases[i][0]+'] != ['+cases[i][1]+']'); process.exit(1);} }
console.log('OK');
"""
    f = tmp_path / "diagline.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout
