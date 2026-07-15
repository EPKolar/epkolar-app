"""v3.9.703 — Mitarbeiter-Anlage erzeugt optional automatisch einen Login.

Wiederverwendung von createUser/admin_create_user, KEINE neue Auth-Logik. Die Login-Anlage ist
strikt getrennt von der Worker-Anlage: Worker via SQ (offline-fähig), Login AWAITED, nur online,
grün nur bei r.ok (v3.9.699-Lektion). Die admin_create_user-RPC (trägt das Passwort!) darf NIE in
die SyncQueue.
"""
import re


def _addmonteur(index_html):
    m = re.search(r"const addMonteur=async\(\)=>\{.*?\n  \};", index_html, re.S)
    assert m, "addMonteur (async) nicht gefunden"
    return m.group(0)


# ── Prop-Drilling ─────────────────────────────────────────────────────────────
def test_mitarbeiterview_bekommt_users(index_html):
    assert "function MitarbeiterView({monteure,setMonteure,monteurProjekte,setMonteurProjekte,ww,curUser,projects,fahrzeuge,abs,approvals,entries,arbeitsscheine,onNav,users,setUsers})" in index_html
    assert "React.createElement(MitarbeiterView, {" in index_html and "users: users, setUsers: setUsers }" in index_html


# ── Worker-Anlage unverändert (SQ, offline-fähig) ─────────────────────────────
def test_worker_weiter_ueber_syncqueue(index_html):
    body = _addmonteur(index_html)
    assert 'SQ.push({url:"/api/workers",method:"POST"' in body


# ── Gating: nur echter Admin ──────────────────────────────────────────────────
def test_login_nur_fuer_admin(index_html):
    body = _addmonteur(index_html)
    assert "nf.mkLogin!==false && curUser.role==='admin'" in body
    # Die Login-Sektion im Formular ist ebenfalls admin-gegatet, sonst Hinweis:
    assert "(curUser.role==='admin')" in index_html
    assert "Login-Anlage nur durch Admin" in index_html


# ── RPC awaited, NIE in die SyncQueue ─────────────────────────────────────────
def test_rpc_ist_awaited_nicht_gequeued(index_html):
    body = _addmonteur(index_html)
    assert 'await _authRetry(()=>fetch(SB_REST+"/rpc/admin_create_user"' in body
    # admin_create_user darf NICHT via SQ.push laufen (Passwort in der Queue):
    assert 'SQ.push' in body  # (users-POST schon, RPC nicht)
    assert 'SQ.push({url:"/rpc/admin_create_user"' not in body
    assert '"/api/rpc/admin_create_user"' not in body


def test_offline_legt_keinen_login_an(index_html):
    body = _addmonteur(index_html)
    assert "navigator.onLine===false" in body
    assert "Login nicht angelegt (offline)" in body


def test_kein_gruen_ohne_rpc_ok(index_html):
    """Erfolg (grün) nur bei _ok; sonst 'noch nicht aktiv' als Warnung."""
    body = _addmonteur(index_html)
    assert "if(_ok){_loginMsg=\" + Login '\"+_uName+\"' angelegt\";}" in body
    assert "Login noch nicht aktiv" in body
    # Der Erfolgs-Toast ist nur dann success, wenn keine Warnung gesetzt wurde:
    assert '_warn?"warn":"success"' in body


# ── Dedup (1:1-Anker + Username + E-Mail) ─────────────────────────────────────
def test_dedup_checks(index_html):
    body = _addmonteur(index_html)
    assert "u.username===_uName" in body
    assert "u.monteurId===id" in body       # v3.9.170 1:1-Anker
    assert "(u.email||\"\").trim().toLowerCase()===_uMail.toLowerCase()" in body


# ── Username-Konvention aus dem Bestand (Nachname), kein erfundenes Passwort ───
def test_username_konvention_nachname(index_html):
    assert "const _foldUser=" in index_html
    assert "const _loginVorschlag=" in index_html
    # Umlaut-Faltung + nur a-z0-9:
    assert ".replace(/ä/g,'ae')" in index_html and ".replace(/[^a-z0-9]/g,'')" in index_html


def test_kein_erfundenes_standardpasswort(index_html):
    """Es gibt kein Haus-Initialpasswort im Code — der Admin tippt es (min. 4). Ein vorhersagbares
    Default-Passwort wäre ein Sicherheitsrisiko und wird NICHT eingebaut."""
    body = _addmonteur(index_html)
    assert "nf.loginPw.length<4" in body
    # Kein hartkodiertes Default-Passwort im Login-Zweig:
    for verdacht in ("Willkommen", "start123", "Passwort1", "changeme", "ep-kolar1"):
        assert verdacht not in body


# ── _W2U-Rollenmap ────────────────────────────────────────────────────────────
def test_w2u_map_vorhanden(index_html):
    assert 'const _W2U={"Geschäftsführer":"admin"' in index_html
    body = _addmonteur(index_html)
    assert "_W2U[_wRole]||\"monteur\"" in body
