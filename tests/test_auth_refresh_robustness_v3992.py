"""v3.9.102 — Monteur-Session-Stabilität: Auth-Refresh Robustheit (Wurzel-Fix).

Behebt den Monteur-Logout bei mobilem Netz / Tab-Switch / Hintergrund. Kernursache war
NICHT ein fehlender Refresh-Lock (Single-Flight `_authRefreshInflight` existiert seit
v3.5.112), sondern:
  1. 4xx auf /token (rotierter, toter refresh_token) → _silentReAuth → sofortiger Logout,
     OHNE vorher den evtl. schon rotierten Token aus Storage neu zu lesen.
  2. Kein Offline-Guard: Refresh-Versuch bei navigator.onLine===false.
  3. Proaktiver Timer erst bei exp-60s statt ~80% Lifetime.

Diese Suite testet die Wurzel-Fixes:
  - STATIC: Offline-Guard, Storage-Reread+Retry, 80%-Timer, Single-Flight erhalten.
  - BEHAVIORAL (Node): Doppel-Refresh→1 /token-Call; Offline→0 Calls, Token behalten;
    4xx+rotierter-Storage-Token→1 Retry, KEIN Logout; 4xx+keine-Rotation→Logout.

H1-Zone (_OFFPW.verify / SyncQueue / IndexedDB) bleibt unangetastet.
"""
import json
import re
import pytest
from conftest import run_node_snippet


# ───────────────────────── Extraction helper ─────────────────────────

def _extract_async_fn(src, name):
    """Extract `async function NAME(){...}` incl. body via brace matching."""
    sig = "async function " + name + "()"
    start = src.index(sig)
    i = src.index("{", start)
    depth = 0
    while i < len(src):
        c = src[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return src[start:i + 1]
        i += 1
    raise AssertionError(name + " body not found")


# Node harness: stubs every dependency of _sbAuthRefresh and exposes counters.
_HARNESS_STUBS = r"""
globalThis.atob = globalThis.atob || (s => Buffer.from(s, 'base64').toString('binary'));
let _authToken = null, _authRefreshToken = null, _authRefreshTimer = null;
let _authRefreshInflight = null;
let logoutCalled = false;
let fetchCount = 0;
const _SB_AUTH = '', SUPABASE_KEY = 'anon';
const _fT = (o, _t) => o;
const _authLog = () => {};
const _lsMap = new Map();
globalThis.localStorage = {
  getItem: k => (_lsMap.has(k) ? _lsMap.get(k) : null),
  setItem: (k, v) => { _lsMap.set(k, String(v)); },
  removeItem: k => { _lsMap.delete(k); },
};
globalThis.navigator = { onLine: true };
// _storeAuth: realitätsnah — RAM + Storage (token zuerst, dann combined), wie der echte Code.
function _storeAuth(d) {
  if (!d || !d.access_token) return;
  _authToken = d.access_token;
  _authRefreshToken = d.refresh_token || null;
  if (d.refresh_token) localStorage.setItem('epkolar_refresh', d.refresh_token);
  localStorage.setItem('epkolar_token', d.access_token);
}
async function _silentReAuth() {
  logoutCalled = true;
  _authToken = null; _authRefreshToken = null;
  return null;
}
// fetch wird pro Szenario von _fetchImpl bereitgestellt.
let _fetchImpl = null;
globalThis.fetch = (...a) => { fetchCount++; return _fetchImpl(...a); };
// dummy access token (kein echtes JWT nötig — exp-parse ist try/catch-gewrappt)
const ACCESS = 'aaa.bbb.ccc';
function okResp(rt) {
  return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ access_token: ACCESS, refresh_token: rt, expires_in: 3600 }) });
}
function badResp(status) {
  return Promise.resolve({ ok: false, status: status, json: () => Promise.resolve({}) });
}
function out(o) { process.stdout.write(JSON.stringify(o)); }
"""


@pytest.fixture(scope="session")
def sb_auth_refresh_src(index_html):
    return _extract_async_fn(index_html, "_sbAuthRefresh")


def _run(node_exe, fn_src, scenario):
    return json.loads(run_node_snippet(node_exe, _HARNESS_STUBS + "\n" + fn_src + "\n" + scenario))


# ───────────────────────── STATIC invariants ─────────────────────────

def test_single_flight_preserved(index_html):
    """Single-Flight-Guard (Wurzel der Serialisierung) muss erhalten bleiben."""
    fn = _extract_async_fn(index_html, "_sbAuthRefresh")
    assert "if(_authRefreshInflight)return _authRefreshInflight;" in fn, (
        "Single-Flight-Guard _authRefreshInflight muss erhalten bleiben"
    )


def test_offline_guard_present(index_html):
    fn = _extract_async_fn(index_html, "_sbAuthRefresh")
    assert "navigator.onLine===false" in fn, "Offline-Guard muss navigator.onLine prüfen"
    assert "reason:'offline'" in fn, "Offline-Skip muss geloggt werden"
    # Offline-Pfad darf NICHT _silentReAuth/nuke auslösen — er behält den Token.
    pre = fn[:fn.index("_authRefreshInflight=(async")]
    assert "_silentReAuth" not in pre, "Offline-Guard darf KEIN _silentReAuth triggern"


def test_storage_reread_on_4xx(index_html):
    fn = _extract_async_fn(index_html, "_sbAuthRefresh")
    # Storage-Reread beim Start UND im 4xx-Zweig
    assert fn.count('localStorage.getItem("epkolar_refresh")') >= 2, (
        "epkolar_refresh muss bei Start UND im 4xx-Retry-Zweig gelesen werden"
    )
    assert "refresh_retry" in fn, "4xx-Retry muss als refresh_retry geloggt werden"


def test_refresh_token_not_jwt_validated(index_html):
    """Opaker refresh_token darf NICHT mit _isJwtShape() validiert werden (würde RT verwerfen).

    Geprüft wird der CALL (_isJwtShape(...) ohne Space) — ein erklärender Kommentar, der den
    Namen erwähnt, ist erlaubt.
    """
    fn = _extract_async_fn(index_html, "_sbAuthRefresh")
    assert "_isJwtShape(" not in fn, (
        "refresh_token ist opak (kein JWT) — _isJwtShape() würde gültige Tokens verwerfen"
    )
    assert ".length>10" in fn, "RT-Guard muss längen-basiert sein"


def test_proactive_80pct_timer(index_html):
    # _storeAuth ist KEINE async fn → eigene Brace-Extraktion
    m = re.search(r"function _storeAuth\(d\)\{", index_html)
    assert m
    start = m.start(); i = index_html.index("{", start); depth = 0
    while i < len(index_html):
        if index_html[i] == "{": depth += 1
        elif index_html[i] == "}":
            depth -= 1
            if depth == 0: break
        i += 1
    body = index_html[start:i + 1]
    assert "expSec*0.8" in body, "Proaktiver Refresh muss bei ~80% Lifetime feuern"


# ───────────────────────── BEHAVIORAL (Node) ─────────────────────────

def test_double_refresh_single_token_call(node_exe, sb_auth_refresh_src):
    """Pflicht-Test: 2x _sbAuthRefresh gleichzeitig → nur 1 /token-Call, kein Logout."""
    scenario = r"""
    (async () => {
      navigator.onLine = true;
      _authRefreshToken = 'rt_one_aaaaaaaaaa';
      localStorage.setItem('epkolar_refresh', 'rt_one_aaaaaaaaaa');
      // langsamer fetch, damit beide Aufrufer überlappen
      _fetchImpl = () => new Promise(res => setTimeout(() => res({ ok: true, status: 200, json: () => Promise.resolve({ access_token: ACCESS, refresh_token: 'rt_two_bbbbbbbbbb', expires_in: 3600 }) }), 25));
      const p1 = _sbAuthRefresh();
      const p2 = _sbAuthRefresh();
      await Promise.all([p1, p2]);
      out({ fetchCount, logoutCalled, samePromise: p1 === p2, rt: _authRefreshToken });
    })();
    """
    r = _run(node_exe, sb_auth_refresh_src, scenario)
    # Kern-Garantie der Single-Flight: 2 gleichzeitige Aufrufer ⇒ exakt 1 /token-Call.
    # (samePromise wird NICHT geprüft: _sbAuthRefresh ist `async` → jeder Aufruf liefert
    #  einen eigenen Wrapper-Promise; das eliminiert den Fetch-Race trotzdem, fetchCount==1.)
    assert r["fetchCount"] == 1, f"Doppel-Refresh muss exakt 1 /token-Call ergeben, war {r['fetchCount']}"
    assert r["logoutCalled"] is False, "Doppel-Refresh darf KEINEN Logout auslösen"
    assert r["rt"] == "rt_two_bbbbbbbbbb", "Token muss auf den rotierten Wert aktualisiert sein"


def test_offline_no_call_token_kept(node_exe, sb_auth_refresh_src):
    """Pflicht-Test: offline → 0 /token-Calls, Token bleibt erhalten, kein Logout."""
    scenario = r"""
    (async () => {
      navigator.onLine = false;
      _authToken = 'at1'; _authRefreshToken = 'rt1';
      _fetchImpl = () => { throw new Error('should not fetch offline'); };
      const ret = await _sbAuthRefresh();
      out({ fetchCount, logoutCalled, authToken: _authToken, retHasToken: !!(ret && ret.access_token) });
    })();
    """
    r = _run(node_exe, sb_auth_refresh_src, scenario)
    assert r["fetchCount"] == 0, "Offline darf KEINEN /token-Call machen"
    assert r["logoutCalled"] is False, "Offline darf KEINEN Logout auslösen"
    assert r["authToken"] == "at1", "Offline muss den Access-Token behalten"
    assert r["retHasToken"] is True, "Offline-Return muss den vorhandenen Token zurückgeben"


def test_4xx_with_rotated_storage_retries_no_logout(node_exe, sb_auth_refresh_src):
    """Pflicht-Test: 4xx weil RT parallel rotiert → 1 Retry mit Storage-Token, KEIN Logout."""
    scenario = r"""
    (async () => {
      navigator.onLine = true;
      _authRefreshToken = 'rt_old_aaaaaaaaaa';
      localStorage.setItem('epkolar_refresh', 'rt_old_aaaaaaaaaa');  // start: in sync
      _fetchImpl = (url, opt) => {
        const body = (opt && opt.body) || '';
        if (body.indexOf('rt_old_aaaaaaaaaa') >= 0) {
          // Simuliert: WÄHREND unseres Calls hat ein Parallel-Context rotiert + Storage geschrieben.
          localStorage.setItem('epkolar_refresh', 'rt_new_bbbbbbbbbb');
          return badResp(400);
        }
        if (body.indexOf('rt_new_bbbbbbbbbb') >= 0) return okResp('rt_newer_cccccccccc');
        return badResp(401);
      };
      await _sbAuthRefresh();
      out({ fetchCount, logoutCalled, rt: _authRefreshToken });
    })();
    """
    r = _run(node_exe, sb_auth_refresh_src, scenario)
    assert r["fetchCount"] == 2, f"Erwartet 1 Fehlversuch + 1 Retry = 2 Calls, war {r['fetchCount']}"
    assert r["logoutCalled"] is False, "Rotation-Race darf KEINEN Logout auslösen"
    assert r["rt"] == "rt_newer_cccccccccc", "Nach erfolgreichem Retry muss der neueste Token aktiv sein"


def test_4xx_genuine_expiry_logs_out(node_exe, sb_auth_refresh_src):
    """4xx OHNE frischeren Storage-Token (echter Ablauf) → _silentReAuth (Logout)."""
    scenario = r"""
    (async () => {
      navigator.onLine = true;
      _authRefreshToken = 'rt_dead';
      localStorage.setItem('epkolar_refresh', 'rt_dead');  // Storage bleibt = RAM (keine Rotation)
      _fetchImpl = () => badResp(400);
      await _sbAuthRefresh();
      out({ fetchCount, logoutCalled });
    })();
    """
    r = _run(node_exe, sb_auth_refresh_src, scenario)
    assert r["fetchCount"] == 1, "Ohne frischeren Storage-Token darf KEIN Retry erfolgen"
    assert r["logoutCalled"] is True, "Echter Token-Ablauf muss zu _silentReAuth führen"
