"""v3.9.127 — Flagged-Funde F2/F5/F6/F7 + AdminPanel-Statistik client-seitig (statt admin_stats-RPC)."""
import json
import re
from conftest import run_node_snippet


def test_as_art_wartung_regie(index_html):
    # F5: parseVoice setzte "wartung"/"regie" — Keys existierten nicht → "?"-Rendering
    assert 'wartung:{l:"Wartung",i:"🔩"}' in index_html
    assert 'regie:{l:"Regie",i:"📋"}' in index_html


def test_iso_week_year_helper(node_exe, index_html):
    # F2: isoWY liefert das ISO-Wochen-Jahr (Donnerstags-Regel) — getFullYear() war Ende Dez falsch
    m = re.search(r"const isoWY=\(\)=>\{[^\n]+\};", index_html)
    assert m, "isoWY-Helper fehlt"
    code = m.group(0).replace("new Date()", "new Date(D)")
    snippet = (
        "globalThis.D='2025-12-29T10:00:00';" + code.replace("const isoWY","globalThis.isoWY") +
        "const a=isoWY();globalThis.D='2027-01-01T10:00:00';const b=isoWY();"
        "globalThis.D='2026-06-04T10:00:00';const c=isoWY();"
        "process.stdout.write(JSON.stringify([a,b,c]));"
    )
    res = json.loads(run_node_snippet(node_exe, snippet))
    # 29.12.2025 (Mo) = KW1/2026 → 2026 (getFullYear wäre 2025!); 01.01.2027 (Fr) = KW53/2026 → 2026
    # (getFullYear wäre 2027!); Juni normal. Hinweis: 2026 startet am Do → 53 ISO-Wochen.
    assert res == [2026, 2026, 2026], f"isoWY falsch: {res}"
    assert index_html.count("const yr=isoWY();") == 3, "alle 3 KW-Views müssen isoWY nutzen"


def test_menge_decimal_comma(index_html):
    # F7: Dezimal-Mengen (2,5m) + Komma-Norm; parseInt schnitt ab
    assert 'const n=Math.max(0,parseFloat(String(val).replace(",","."))||0);' in index_html
    assert index_html.count('min: "0", step: "any", placeholder: (lastQtyByArtNr') == 3
    assert 'min: "0.01", step: "any", value: pos.menge' in index_html


def test_odb_purge_on_user_switch(index_html):
    # F6: Session-Ablauf umgeht Logout-Cleanup → Purge bei Login mit anderem User
    assert "const _USER_SCOPED_ODB_STORES=[" in index_html
    assert "epk_last_login_uid" in index_html
    assert "for(const _s of _USER_SCOPED_ODB_STORES){try{await ODB.del(_s,'data');}" in index_html
    # Purge passiert VOR setCurUser (async-Handler)
    assert "onLogin: async u=>{/* v3.9.127 F6" in index_html


def test_admin_stats_client_side(index_html):
    # Statistik-Tab: byUser/topModules/byAction/daily/userStatus aus activity_log (30d) statt RPC
    assert 'const byUser=Object.entries(_byU).map' in index_html
    assert 'const userStatus=(users||[]).map(u=>({id:u.id,name:u.name' in index_html
    assert 'total:actRows.length,today,logins30d,failedLogins30d,userStatus,byUser,topModules,byAction,daily' in index_html
    assert 'sub: "letzte 30 Tage"' in index_html  # ehrliches Label
