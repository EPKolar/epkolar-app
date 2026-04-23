"""Core helper functions present and well-formed."""
import re


def test_n_helper_defined(index_html):
    assert re.search(r"\bfunction\s+_n\s*\(v\s*,\s*d\s*\)", index_html), "_n(v,d) helper missing"


def test_n_helper_handles_nan(index_html):
    # Sanity: _n body mentions isNaN
    m = re.search(r"function\s+_n\s*\([^)]*\)\s*\{[^}]+\}", index_html)
    assert m and "isNaN" in m.group(0), "_n() body missing isNaN guard"


def test_cando_defined(index_html):
    assert re.search(r"\bfunction\s+canDo\s*\(\s*action", index_html), "canDo() helper missing"


def test_authretry_defined(index_html):
    assert re.search(r"\b_authRetry\s*=", index_html) or re.search(
        r"\bfunction\s+_authRetry\b", index_html
    ), "_authRetry missing"


def test_offpw_defined(index_html):
    assert "const _OFFPW=" in index_html, "_OFFPW helper missing (v3.8.33 Iter-19c)"


def test_offpw_uses_pbkdf2(index_html):
    assert "PBKDF2" in index_html, "_OFFPW must reference PBKDF2"
    assert '"PBKDF2-SHA256"' in index_html, "algo string missing"


def test_offpw_login_write_uses_helper(index_html):
    # Post-v3.8.33 the login-success path must have _OFFPW.create + write to offlinePwHash
    # within ~200 chars of each other (same try-block).
    m = re.search(
        r'_OFFPW\.create\s*\([^)]+\)[^;]*;[^}]{0,200}ODB\.set\("meta","offlinePwHash"',
        index_html,
    )
    assert m, "_OFFPW.create not wired into login-success offlinePwHash write"


def test_offpw_verify_wired_into_login_fallback(index_html):
    assert "_OFFPW.verify" in index_html, "_OFFPW.verify must be used in offline login fallback"


def test_odb_defined(index_html):
    assert re.search(r"const\s+ODB\s*=\s*\{", index_html), "ODB object missing"


def test_sq_defined(index_html):
    assert re.search(r"const\s+SQ\s*=\s*\{", index_html), "SyncQueue SQ missing"
