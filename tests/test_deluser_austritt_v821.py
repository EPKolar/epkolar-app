# -*- coding: utf-8 -*-
"""v3.9.821 — delUser ehrlich + Austritts-Filter komplett.

delUser hatte dieselbe Fehlerklasse wie der v820-delMonteur-Bug, nur schlimmer: lokal SOFORT entfernen,
SQ.push(DELETE) fire-and-forget UND ein BEDINGUNGSLOSER Erfolgs-Toast. Bei einer per RLS herausgefilterten
Zeile liefert PostgREST 204/[] = ok mit 0 gelöschten Zeilen -> der Benutzer blieb in der DB, die App
meldete trotzdem "gelöscht".

Austritt filtert jetzt zusätzlich in fieldMA der ZeiterfassungView und in _noLogin (AdminPanel).
"""
from conftest import run_node_snippet


# ── TEIL 1: delUser ──────────────────────────────────────────────────────────
def _du_block(index_html):
    a = index_html.index("const delUser=async(id)=>{")
    return index_html[a:index_html.index("\n  };", a)]


def test_awaited_delete_mit_representation(index_html):
    blk = _du_block(index_html)
    assert '_sbWH("return=representation")' in blk, "DELETE ohne return=representation -> 0-Rows nicht erkennbar"
    assert 'SB_REST+"/users?id=eq."' in blk and 'method:"DELETE"' in blk, "kein direkter awaited users-DELETE"
    assert "SQ.push" not in blk, "Löschen darf NICHT über die Offline-Queue (Fehlschlag würde still geschluckt)"


def test_null_rows_kein_stilles_entfernen_und_kein_erfolgstoast(index_html):
    blk = _du_block(index_html)
    assert "_urows.length!==1" in blk, "1-Zeilen-Check fehlt"
    i_guard = blk.index("_urows.length!==1")
    i_local = blk.index("setUsers(prev=>prev.filter")
    i_ok = blk.index("🗑️ Benutzer gelöscht")
    assert i_guard < i_local, "lokales Entfernen VOR dem 1-Zeilen-Check (stiller Verlust)"
    assert i_guard < i_ok, "Erfolgs-Toast steht VOR dem 1-Zeilen-Check (bedingungsloser Erfolg — der Bug)"
    assert "Löschen abgelehnt" in blk, "RLS-Silent-Denial meldet nicht"
    assert "Löschen fehlgeschlagen" in blk, "Netzfehler meldet nicht"


def test_gates_und_auth_tabu_unveraendert(index_html):
    blk = _du_block(index_html)
    assert 'curUser.role!=="admin"' in blk, "admin-only-Gate fehlt"
    assert "id===curUser.id" in blk, "Selbstschutz (nicht sich selbst löschen) fehlt"
    assert "_confirmModal(" in blk, "Bestätigungsdialog fehlt"
    # AUTH-PFADE TABU: nur public.users
    assert "auth.users" not in blk and "gotrue" not in blk.lower(), "delUser fasst Auth-Pfade an (TABU)"


def test_users_in_rls_silent_denial_labels(index_html):
    a = index_html.index("const _RLS_SILENT_DENIAL_LABELS=Object.freeze({")
    seg = index_html[a:index_html.index("});", a)]
    assert "users:" in seg, "users fehlt in _RLS_SILENT_DENIAL_LABELS"
    assert "workers:" in seg, "workers (v820) darf nicht verloren gehen"


# ── TEIL 2: Austritts-Filter ─────────────────────────────────────────────────
_ZE = ('(function(m,heute){return m.r!=="Backoffice"&&m.r!=="Verkauf/Buchhaltung"'
       '&&(!m.austritt||String(m.austritt).slice(0,10)>=heute);})')
_NL = ('(function(w,users,heute){return !users.some(function(u){return u.monteurId===w.id;})'
       '&&(!w.austritt||String(w.austritt).slice(0,10)>=heute);})')


def test_ze_fieldMA_austritt_logik(node_exe):
    def f(m_js):
        return run_node_snippet(node_exe, "process.stdout.write(String(" + _ZE + "(" + m_js + ",'2026-07-24')))").strip()
    assert f("{r:'Monteur',austritt:'2026-07-23'}") == "false", "ausgetretener MA erscheint noch in der Zeiterfassung"
    assert f("{r:'Monteur'}") == "true"
    assert f("{r:'Backoffice'}") == "false"
    # Geschaeftsfuehrer bleibt bewusst drin (lohnnahe Ansicht, keine Verhaltensaenderung).
    assert f("{r:'Geschäftsführer'}") == "true", "Geschäftsführer darf NICHT zusätzlich ausgeschlossen werden"


def test_nologin_austritt_logik(node_exe):
    def f(w_js, users_js):
        return run_node_snippet(node_exe, "process.stdout.write(String(" + _NL + "(" + w_js + "," + users_js + ",'2026-07-24')))").strip()
    # Ohne Login + aktiv -> Warnung.
    assert f("{id:'w1'}", "[]") == "true"
    # Ohne Login aber ausgetreten -> KEINE Warnung mehr.
    assert f("{id:'w3',austritt:'2026-07-23'}", "[]") == "false"
    # Mit Login -> nie Warnung.
    assert f("{id:'w1'}", "[{monteurId:'w1'}]") == "false"


def test_beide_filter_verdrahtet(index_html):
    assert ('const fieldMA=monteure.filter(m=>m.r!=="Backoffice"&&m.r!=="Verkauf/Buchhaltung"'
            '&&(!m.austritt||String(m.austritt).slice(0,10)>=_hkZE));' in index_html), "ZE-fieldMA ohne Austritts-Filter"
    assert ('const _noLogin=(monteure||[]).filter(w=>!(users||[]).some(u=>u.monteurId===w.id)'
            '&&(!w.austritt||String(w.austritt).slice(0,10)>=_hkNL));' in index_html), "_noLogin ohne Austritts-Filter"
    assert "const _hkZE=_ezHeuteISO();" in index_html and "const _hkNL=_ezHeuteISO();" in index_html, \
        "Wiener-Datum-Helper nicht genutzt (kein rohes new Date())"
