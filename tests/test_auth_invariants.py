"""Regression tests for long-standing auth invariants.

Protects behavior that was easy to accidentally break across refactors:
- Singleton-guards (_authRefreshInflight, _sbHLastRefreshAt throttle)
- Timer lifecycle (_authRefreshTimer cleared on logout)
- Storage-key consistency (login sets 3 keys, logout removes them)
- Bootstrap invocation (_restoreAuth called at module-load)
- JWT-shape validation before Bearer injection
"""
import re


# ═════════════════════ Singleton-Guards ═════════════════════

def test_auth_refresh_inflight_singleton_declared(index_html):
    assert "let _authRefreshInflight=null" in index_html, (
        "_authRefreshInflight singleton state must exist "
        "(prevents thundering-herd on parallel 401-refresh-retries)"
    )


def test_auth_refresh_inflight_used_as_guard(index_html):
    start = index_html.index("async function _sbAuthRefresh()")
    # v3.9.102: Fenster vergrößert — _sbAuthRefresh wuchs um Offline-Guard + 4xx-Rotation-Retry;
    # der finally-Block (_authRefreshInflight=null) sitzt jetzt weiter hinten. Invariante unverändert.
    body = index_html[start:start + 4500]
    assert "if(_authRefreshInflight)return _authRefreshInflight" in body, (
        "_sbAuthRefresh entry must early-return if an inflight promise exists"
    )
    assert "_authRefreshInflight=null" in body, (
        "_sbAuthRefresh must clear _authRefreshInflight in finally block"
    )


def test_sbh_anon_throttle_exists(index_html):
    assert "let _sbHLastRefreshAt=0" in index_html, (
        "_sbHLastRefreshAt throttle state must exist "
        "(5s-debounce for anon-JWT auto-refresh in _sbH)"
    )


def test_sbh_respects_throttle(index_html):
    start = index_html.index("function _sbH(extra)")
    body = index_html[start:start + 800]
    assert "Date.now()-_sbHLastRefreshAt>5000" in body, (
        "_sbH must throttle anon-detect-refresh at 5s interval"
    )


# ═════════════════════ Timer-Lifecycle ═════════════════════

def test_auth_refresh_timer_declared(index_html):
    assert "_authRefreshTimer" in index_html, (
        "_authRefreshTimer handle must exist (one-shot 60s-before-exp refresh)"
    )


def test_logout_clears_refresh_timer(index_html):
    start = index_html.index("async function _sbAuthLogout()")
    body = index_html[start:start + 800]
    assert "clearTimeout(_authRefreshTimer)" in body, (
        "_sbAuthLogout must clearTimeout(_authRefreshTimer) to prevent "
        "stale refresh firing with next-user's context"
    )
    assert "_authRefreshTimer=null" in body, (
        "_sbAuthLogout must reset _authRefreshTimer handle"
    )


def test_store_auth_reschedules_timer(index_html):
    start = index_html.index("function _storeAuth(d)")
    # v3.9.107: Fenster vergrößert — _storeAuth bekam reauth-counter-reset + Konsistenz-Kommentare.
    body = index_html[start:start + 2200]
    assert "if(_authRefreshTimer)clearTimeout(_authRefreshTimer)" in body, (
        "_storeAuth must clear old timer before scheduling new one"
    )
    assert "setTimeout(()=>_sbAuthRefresh()" in body, (
        "_storeAuth must schedule next _sbAuthRefresh via setTimeout"
    )


# ═════════════════════ Storage-Key Lifecycle ═════════════════════

def test_store_auth_writes_three_keys(index_html):
    start = index_html.index("function _storeAuth(d)")
    # v3.9.102: Fenster vergrößert — _storeAuth bekam Storage-Konsistenz-Kommentar + Reorder.
    body = index_html[start:start + 1400]
    # All three storage keys must be written by _storeAuth
    assert 'localStorage.setItem("epkolar_auth"' in body, (
        "_storeAuth must write epkolar_auth blob"
    )
    assert 'localStorage.setItem("epkolar_token"' in body, (
        "_storeAuth must write epkolar_token (raw access_token for debug)"
    )
    assert 'localStorage.setItem("epkolar_refresh"' in body, (
        "_storeAuth must write epkolar_refresh (raw refresh_token)"
    )


def test_logout_removes_auth_storage_keys(index_html):
    start = index_html.index("async function _sbAuthLogout()")
    # v3.9.112: Fenster vergrößert — _sbAuthLogout bekam Token-Kapselung + Kommentar.
    body = index_html[start:start + 1200]
    for key in ("epkolar_auth", "epkolar_token", "epkolar_refresh", "epkolar_gc"):
        assert f'localStorage.removeItem("{key}")' in body, (
            f"_sbAuthLogout must remove {key}"
        )


def test_store_auth_json_shape(index_html):
    # The epkolar_auth blob must carry at, rt, exp
    start = index_html.index('localStorage.setItem("epkolar_auth"')
    body = index_html[start:start + 300]
    assert "at:d.access_token" in body, "epkolar_auth blob must carry at:access_token"
    assert "rt:d.refresh_token" in body, "epkolar_auth blob must carry rt:refresh_token"
    assert "exp:Date.now()+(d.expires_in*1000)" in body, (
        "epkolar_auth blob must carry exp as absolute-ms timestamp"
    )


# ═════════════════════ Bootstrap ═════════════════════

def test_restore_auth_invoked_at_module_load(index_html):
    # _restoreAuth() must be called once at the bottom of auth-definition
    # block (not inside a function body)
    assert re.search(r"^\s*_restoreAuth\(\);", index_html, re.MULTILINE), (
        "_restoreAuth() must be invoked at module-load (bootstrap)"
    )


# ═════════════════════ JWT Shape Validation ═════════════════════

def test_is_jwt_shape_helper_exists(index_html):
    assert "function _isJwtShape(t)" in index_html, (
        "_isJwtShape JWT-shape validator must exist"
    )


def test_sbh_validates_jwt_before_bearer(index_html):
    start = index_html.index("function _sbH(extra)")
    body = index_html[start:start + 800]
    assert "_isJwtShape(_authToken)" in body, (
        "_sbH must validate JWT-shape before Bearer injection "
        "(prevents PGRST301 'Expected 3 parts in JWT' for legacy tokens)"
    )


def test_store_auth_guards_against_non_jwt(index_html):
    start = index_html.index("function _storeAuth(d)")
    body = index_html[start:start + 400]
    assert "_isJwtShape(d.access_token)" in body, (
        "_storeAuth must reject non-JWT access_tokens to prevent "
        "downstream poisoning with garbage Bearer tokens"
    )


# ═════════════════════ Security: 401-Retry-Chain ═════════════════════

def test_auth_retry_uses_isautherr_predicate(index_html):
    start = index_html.index("async function _authRetry(fn)")
    body = index_html[start:start + 800]
    assert "_isAuthErr(r.status)" in body, (
        "_authRetry must use _isAuthErr predicate (401/403)"
    )


def test_is_auth_err_covers_401_and_403(index_html):
    start = index_html.index("function _isAuthErr(status)")
    body = index_html[start:start + 200]
    assert "status===401" in body, "_isAuthErr must cover 401"
    assert "status===403" in body, "_isAuthErr must cover 403"


def test_auth_fail_flag_prevents_toast_spam(index_html):
    assert "let _authFailShown=false" in index_html, (
        "_authFailShown flag must exist to prevent toast-spam"
    )
    start = index_html.index("function _onAuthFail()")
    body = index_html[start:start + 400]
    assert "if(_authFailShown)return" in body, (
        "_onAuthFail must early-return on repeat calls"
    )
    assert "_authFailShown=false" in body, (
        "_onAuthFail must eventually reset the flag (timeout in same fn)"
    )
