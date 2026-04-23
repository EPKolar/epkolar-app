"""APP_VERSION ↔ CACHE_NAME ↔ sw.js header synchronization."""
import re


def test_app_version_format(app_version):
    # e.g. "3.8.33-supabase"
    assert re.match(r"^\d+\.\d+\.\d+(-\w+)?$", app_version), f"bad APP_VERSION: {app_version!r}"


def test_cache_name_format(cache_name):
    assert re.match(r"^epkolar-v\d+\.\d+\.\d+$", cache_name), f"bad CACHE_NAME: {cache_name!r}"


def test_cache_matches_app(app_version, cache_name):
    app_numeric = app_version.split("-")[0]
    cache_numeric = cache_name.replace("epkolar-v", "")
    assert app_numeric == cache_numeric, (
        f"APP_VERSION {app_version!r} vs CACHE_NAME {cache_name!r} mismatch"
    )


def test_sw_header_comment_matches(sw_js, cache_name):
    # sw.js first line: "// EP Kolar Service Worker v3.8.33"
    header = sw_js.splitlines()[0]
    cache_numeric = cache_name.replace("epkolar-v", "")
    assert cache_numeric in header, f"sw.js header {header!r} missing version {cache_numeric!r}"
