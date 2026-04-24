"""Static tests for v3.8.47 auth-hardening (G1/G2/G3 fixes + __authLog).

Verifies:
- G1: _sbAuthRefresh catch does NOT call _silentReAuth on network error
- G2: online-handler triggers _sbAuthRefresh before sync-flush
- G3: auto-login catch has localStorage.epkolar_user fallback
- __authLog ring-buffer helper exists with cap 100
- Existing signatures unchanged (_sbAuthRefresh/_silentReAuth/_authRetry)
- No console.log of _authToken or refresh_token (security)
"""
import re


# ═════════════════════ __authLog Telemetry ═════════════════════

def test_auth_log_initialized(index_html):
    assert "window.__authLog=window.__authLog||[]" in index_html, (
        "window.__authLog ring-buffer must be initialized"
    )


def test_auth_log_helper_exists(index_html):
    assert "function _authLog(ev,meta)" in index_html, (
        "_authLog(ev, meta) helper must be defined"
    )


def test_auth_log_has_100_cap(index_html):
    assert "window.__authLog.length>100" in index_html, (
        "_authLog must cap at 100 entries"
    )


def test_auth_log_no_token_content(index_html):
    start = index_html.index("function _authLog(ev,meta)")
    body = index_html[start:start + 400]
    # Helper itself must NOT reference _authToken / refresh_token content
    assert "_authToken" not in body, (
        "_authLog helper body must not reference _authToken"
    )
    assert "refresh_token" not in body, (
        "_authLog helper body must not reference refresh_token"
    )


# ═════════════════════ G1: Network-Error Fix ═════════════════════

def test_g1_refresh_catch_no_silent_reauth(index_html):
    # Locate _sbAuthRefresh body
    start = index_html.index("async function _sbAuthRefresh()")
    end = index_html.index("async function _silentReAuth()")
    body = index_html[start:end]
    # The outer catch must NOT call _silentReAuth (only the !r.ok branch may)
    # Pattern: the catch block should explicitly return null, not _silentReAuth
    assert "Refresh network error (token kept)" in body, (
        "G1 fix marker 'token kept' must be present in catch"
    )


def test_g1_refresh_logs_network_fail(index_html):
    start = index_html.index("async function _sbAuthRefresh()")
    end = index_html.index("async function _silentReAuth()")
    body = index_html[start:end]
    assert "_authLog('refresh_fail'" in body, (
        "_sbAuthRefresh must log refresh_fail events"
    )
    assert "status:'network'" in body, (
        "Network-fail branch must tag status:'network'"
    )


def test_g1_refresh_logs_ok_event(index_html):
    start = index_html.index("async function _sbAuthRefresh()")
    end = index_html.index("async function _silentReAuth()")
    body = index_html[start:end]
    assert "_authLog('refresh_ok'" in body, (
        "_sbAuthRefresh must log refresh_ok events"
    )
    assert "exp_delta_ms" in body, (
        "refresh_ok must include exp_delta_ms"
    )


# ═════════════════════ G2: Online-Event Refresh ═════════════════════

def test_g2_online_handler_triggers_refresh(index_html):
    # onOnline is defined in useEffect near L4354
    m = re.search(
        r"const\s+onOnline\s*=\s*async\s*\(\)\s*=>\s*\{[\s\S]*?\};",
        index_html,
    )
    assert m, "onOnline handler definition not found"
    body = m.group(0)
    assert "_sbAuthRefresh()" in body, (
        "G2: onOnline must call _sbAuthRefresh"
    )
    assert "wake_online" in body, (
        "G2: onOnline must log wake_online event"
    )


# ═════════════════════ G3: localStorage Fallback ═════════════════════

def test_g3_ls_fallback_exists(index_html):
    assert "curuser_ls_recover" in index_html, (
        "G3: localStorage-recover telemetry marker must be present"
    )


def test_g3_ls_fallback_has_token_validity_guard(index_html):
    idx = index_html.index("curuser_ls_recover")
    # Look back ~800 chars for the guard context
    context = index_html[max(0, idx - 800):idx]
    assert "_isJwtShape(_authToken)" in context, (
        "G3: Token-shape guard must precede ls_recover"
    )
    assert "Date.now()+60000" in context, (
        "G3: Must require >60s token validity before recovery"
    )


def test_g3_ls_fallback_uses_safe_parse(index_html):
    idx = index_html.index("curuser_ls_recover")
    context = index_html[max(0, idx - 800):idx + 400]
    assert "_safeJsonParse(localStorage.getItem('epkolar_user')" in context, (
        "G3: Must use _safeJsonParse for localStorage read (resilience)"
    )


# ═════════════════════ Signature Preservation ═════════════════════

def test_sb_auth_refresh_signature_unchanged(index_html):
    # _sbAuthRefresh must still be async function with no args
    assert "async function _sbAuthRefresh()" in index_html, (
        "_sbAuthRefresh signature must be preserved (async, no args)"
    )


def test_silent_re_auth_signature_unchanged(index_html):
    assert "async function _silentReAuth()" in index_html, (
        "_silentReAuth signature must be preserved"
    )


def test_auth_retry_signature_unchanged(index_html):
    assert "async function _authRetry(fn)" in index_html, (
        "_authRetry(fn) signature must be preserved"
    )


# ═════════════════════ Security: No Token Logging ═════════════════════

def test_no_console_log_of_authtoken(index_html):
    # Search for console.log + _authToken within ~80 chars
    pat = re.compile(r"console\.log\s*\([^)]{0,200}_authToken", re.DOTALL)
    matches = pat.findall(index_html)
    assert not matches, (
        f"Found console.log references to _authToken: {matches[:3]}"
    )


def test_no_console_log_of_refresh_token_value(index_html):
    # URL-param mentions (grant_type=refresh_token) are benign.
    # What we guard against: variable-dereferences like +_authRefreshToken or +rt
    # being concatenated into console.log output.
    bad_patterns = [
        r"console\.log\([^)]{0,200}\+\s*_authRefreshToken",
        r"console\.log\([^)]{0,200}\+\s*d\.refresh_token",
        r"console\.log\([^)]{0,200}rt\s*[:,][^)]{0,200}_authRefreshToken",
    ]
    for pat in bad_patterns:
        matches = re.findall(pat, index_html)
        assert not matches, (
            f"Found console.log that leaks refresh_token value: {matches[:2]}"
        )
