"""Integration Smoke Tests - Tag 6 (Sa 03.05).

Hochgewichtige Sanity-Checks die den App-Bootstrap ganzheitlich prueeb:
- Inline-Script-Bloecke parsen ohne Syntax-Error
- Erwartete globale Konstanten + Helper sind vorhanden
- File-Layout matcht Erwartungen
- v3.8.42 Auto-Push-Pfade vorhanden
- v3.8.41 OFFA-Land-Fix-Pfade vorhanden
"""
import os
import re
import subprocess
from conftest import _find_node


# ────────────────────────────────────────────────────────────
# A · Boot-Konsistenz
# ────────────────────────────────────────────────────────────

def test_boot_iife_present(index_html):
    """The boot watchdog IIFE wraps initial CDN-checks + retry-flow."""
    assert "/* === CDN CHECK + BOOT WATCHDOG === */" in index_html or \
           "CDN CHECK" in index_html or \
           "ep-boot-indicator" in index_html


def test_boot_indicator_div_exists(index_html):
    assert 'id="ep-boot-indicator"' in index_html


def test_boot_watchdog_8s_timeout(index_html):
    """Watchdog soll nach 8 s reagieren wenn React nicht mountet."""
    assert ",8000)" in index_html


# ────────────────────────────────────────────────────────────
# B · React + Service Worker Bootstrap
# ────────────────────────────────────────────────────────────

def test_react_cdn_url_present(index_html):
    # Stand 2026-04-25: React 18.2.0 via cdnjs.cloudflare.com.
    # Akzeptiert auch unpkg falls je migriert.
    assert ("cdnjs.cloudflare.com/ajax/libs/react/" in index_html
            or "unpkg.com/react@" in index_html)


def test_react_dom_cdn_url_present(index_html):
    assert ("cdnjs.cloudflare.com/ajax/libs/react-dom/" in index_html
            or "unpkg.com/react-dom@" in index_html)


def test_serviceworker_register_call(index_html):
    assert "serviceWorker.register" in index_html


def test_app_root_div_present(index_html):
    assert 'id="root"' in index_html or "id='root'" in index_html


# ────────────────────────────────────────────────────────────
# C · Inline-Script-Block-Syntax (per separate file via Node)
# ────────────────────────────────────────────────────────────

def test_each_inline_script_block_node_check_clean(node_exe, repo_root, tmp_path):
    """Extract <script> blocks and run node --check on each separately.

    A passing run means the JS surface that React+Sucrase consume parses.
    Sucrase-output (var App=... twice) only fails if all blocks are merged;
    we test each in isolation.
    """
    src_path = os.path.join(repo_root, "index.html")
    with open(src_path, "r", encoding="utf-8") as f:
        src = f.read()
    blocks = re.findall(r"<script(?![^>]*src=)[^>]*>([\s\S]*?)</script>", src)
    assert blocks, "no inline script blocks found"
    for i, blk in enumerate(blocks):
        tmpfile = tmp_path / f"epk_block_{i}.cjs"
        tmpfile.write_text(blk, encoding="utf-8")
        result = subprocess.run(
            [node_exe, "--check", str(tmpfile)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        assert result.returncode == 0, (
            f"Block #{i} node --check failed:\n{result.stderr}"
        )


# ────────────────────────────────────────────────────────────
# D · Critical Helpers Present
# ────────────────────────────────────────────────────────────

CRITICAL_HELPERS = (
    "_n", "canDo", "_authRetry", "_OFFPW",
    "_juprowaSanitize", "_juprowaReversMap",
    "_juprowaPush", "_juprowaSync", "_juprowaDrainPending",
    "_mapBody", "_toSnake",
)


def test_all_critical_helpers_defined(index_html):
    for name in CRITICAL_HELPERS:
        # function NAME(...) or const NAME=... or var NAME=
        pattern = re.compile(
            r"(?:function\s+|const\s+|var\s+|let\s+)" + re.escape(name) + r"\b"
        )
        assert pattern.search(index_html), f"Critical helper {name} missing"


# ────────────────────────────────────────────────────────────
# E · v3.8.41 + v3.8.42 Acceptance
# ────────────────────────────────────────────────────────────

def test_v3841_lkz_in_juprowa_push(index_html):
    """OFFA-Land-Fix v3.8.41: AK_BAUADR_LKZ + RE_ADR_LKZ Pfade vorhanden."""
    assert "AK_BAUADR_LKZ" in index_html
    assert "RE_ADR_LKZ" in index_html


def test_v3841_re_adr_passthrough_from_raw(index_html):
    """RE_ADR_* darf nur aus juprowa_raw kommen (Sebastian-Policy 24.04)."""
    # Look for the policy comment marker
    assert "Pull-Only" in index_html
    # Verify _raw guard exists in _juprowaReversMap
    m = re.search(r"function _juprowaReversMap[\s\S]+?return json;\s*\}", index_html)
    assert m, "_juprowaReversMap function body not found"
    body = m.group(0)
    assert "schein.juprowa_raw" in body
    assert "_raw.RE_ADR_STR" in body or "_raw.RE_ADR_LKZ" in body


def test_v3842_autopush_marker_present(index_html):
    assert "[AUTOPUSH]" in index_html
    assert "[AUTOPUSH-EXC]" in index_html


def test_v3842_drain_pending_function(index_html):
    assert "async function _juprowaDrainPending" in index_html


def test_v3842_drain_called_from_sync(index_html):
    m = re.search(r"async function _juprowaSync[\s\S]+?^\}", index_html, re.M)
    assert m
    body = m.group(0)
    assert "_juprowaDrainPending" in body


# ────────────────────────────────────────────────────────────
# F · Repo-Layout Sanity
# ────────────────────────────────────────────────────────────

EXPECTED_TOP_LEVEL = (
    "index.html", "sw.js", "README.md",
    "ARCHITECTURE.md", "RUNBOOK.md", "ROADMAP.md",
    "tests", "sql", "preview", "_archiv",
)


def test_expected_top_level_paths_exist(repo_root):
    for entry in EXPECTED_TOP_LEVEL:
        path = os.path.join(repo_root, entry)
        assert os.path.exists(path), f"Expected top-level entry missing: {entry}"


def test_handoffs_present(repo_root):
    for fn in ("HANDOFF_SESSION_2026-04-23.md", "HANDOFF_OVERNIGHT_25042026.md",
               "HANDOFF_OVERNIGHT2_25042026.md", "HANDOFF_PHASE2_v3840.md",
               "HANDOFF_v3842.md"):
        assert os.path.isfile(os.path.join(repo_root, fn)), f"missing {fn}"


def test_audit_docs_present(repo_root):
    for fn in ("CANDO_MATRIX.md", "_authretry_gaps.md", "XSS_AUDIT.md",
               "LOCALSTORAGE_AUDIT.md", "CODE_DEBT.md", "A11Y_AUDIT.md",
               "BUGHUNT_REPORT_20260428.md", "AUTOPUSH_ANALYSIS.md",
               "OFFA_LAND_REGRESSION_ANALYSIS.md"):
        assert os.path.isfile(os.path.join(repo_root, "sql", fn)), f"missing sql/{fn}"


# ────────────────────────────────────────────────────────────
# G · Version Sanity
# ────────────────────────────────────────────────────────────

def test_app_version_is_3_8_42_or_newer(app_version):
    """Stand der Urlaubs-Woche: APP_VERSION bleibt v3.8.42 (H4 kein Bump)."""
    m = re.match(r"(\d+)\.(\d+)\.(\d+)", app_version)
    assert m, f"APP_VERSION ungueltig: {app_version}"
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    assert (major, minor, patch) >= (3, 8, 42), f"version regress: {app_version}"
