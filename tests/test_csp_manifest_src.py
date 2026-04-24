"""Static tests for CSP manifest-src directive (v3.8.48 hotfix).

Verifies the PWA manifest can be loaded via blob: URL without CSP violation.
"""
import re


def test_csp_meta_tag_exists(index_html):
    assert 'http-equiv="Content-Security-Policy"' in index_html, (
        "CSP meta tag must be present"
    )


def test_csp_has_manifest_src(index_html):
    m = re.search(
        r'<meta\s+http-equiv="Content-Security-Policy"\s+content="([^"]+)"',
        index_html,
    )
    assert m, "CSP meta tag content not parseable"
    content = m.group(1)
    assert "manifest-src" in content, (
        "CSP must declare manifest-src directive (was falling back to default-src)"
    )
    assert "manifest-src 'self' blob:" in content, (
        "manifest-src must allow 'self' and blob: for PWA install manifest"
    )


def test_csp_manifest_src_not_duplicated(index_html):
    count = index_html.count("manifest-src")
    assert count == 1, (
        f"manifest-src should appear exactly once in CSP, found {count}"
    )
