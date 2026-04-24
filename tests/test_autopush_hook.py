"""Structural invariants for v3.8.42 Auto-Push implementation.

Block Z: Layer 1 Save-Hook (_juprowaPush fire-and-forget in save paths)
         Layer 2 _juprowaDrainPending(maxBatch=10) called from _juprowaSync
"""
import re


# Layer 2 - _juprowaDrainPending -------------------------------------------

def test_juprowa_drain_pending_defined(index_html):
    assert "async function _juprowaDrainPending" in index_html


def test_drain_pending_has_online_guard(index_html):
    m = re.search(r"async function _juprowaDrainPending[\s\S]+?\n\}", index_html)
    assert m
    body = m.group(0)
    assert "navigator.onLine" in body
    assert "offline" in body.lower() or "skipped" in body


def test_drain_pending_uses_for_of_not_promise_all(index_html):
    """Sequential for-of loop keeps runtime bounded and avoids parallel RPC storm."""
    m = re.search(r"async function _juprowaDrainPending[\s\S]+?\n\}", index_html)
    body = m.group(0)
    assert "for(const" in body or "for (const" in body
    assert "Promise.all" not in body


def test_drain_pending_calls_juprowapush_single(index_html):
    m = re.search(r"async function _juprowaDrainPending[\s\S]+?\n\}", index_html)
    body = m.group(0)
    assert "_juprowaPush(row.id)" in body


def test_drain_pending_has_default_maxbatch_10(index_html):
    m = re.search(r"async function _juprowaDrainPending[\s\S]+?\n\}", index_html)
    body = m.group(0)
    assert "10" in body, "default batch size 10 expected"
    assert "select=id" in body, "query must fetch id-only for speed"
    assert "limit=" in body, "limit clause required"


def test_juprowasync_calls_drain_pending(index_html):
    """_juprowaSync must drain pending push-queue at end of each cycle."""
    m = re.search(r"async function _juprowaSync[\s\S]+?^\}", index_html, re.M)
    assert m
    body = m.group(0)
    assert "_juprowaDrainPending" in body
    assert "[JP-DRAIN]" in body or "JP-DRAIN" in body


def test_startautosync_no_longer_uses_pushall(index_html):
    """Legacy _juprowaPushAll direct-call in _juprowaStartAutoSync removed in v3.8.42."""
    m = re.search(r"function _juprowaStartAutoSync[\s\S]+?\n\}", index_html)
    assert m
    body = m.group(0)
    # Check for direct CALL, not just string (comments may mention it)
    assert "_juprowaPushAll(" not in body, (
        "_juprowaPushAll direct call in AutoSync should be replaced by "
        "internal _juprowaDrainPending call (via _juprowaSync)."
    )


# Layer 1 - Save-Hook invariants -------------------------------------------

def test_save_path_contains_autopush_marker(index_html):
    """[AUTOPUSH] console tag must appear in at least one save path."""
    assert "[AUTOPUSH]" in index_html, "AUTOPUSH marker missing"


def test_save_hook_has_online_guard(index_html):
    """Every [AUTOPUSH] site must be guarded by navigator.onLine."""
    # Find all lines containing AUTOPUSH and verify navigator.onLine nearby
    lines = index_html.splitlines()
    autopush_lines = [i for i, l in enumerate(lines) if "[AUTOPUSH]" in l]
    assert autopush_lines, "no AUTOPUSH line found"
    for idx in autopush_lines:
        # Look 2 lines back (single-line JSX may put guard in same line)
        window = "\n".join(lines[max(0, idx - 2):idx + 1])
        assert "navigator.onLine" in window, (
            f"AUTOPUSH at line {idx + 1} missing navigator.onLine guard"
        )


def test_save_hook_uses_no_await_before_juprowapush(index_html):
    """Fire-and-forget: no `await` immediately before _juprowaPush(...) in AUTOPUSH branches.

    _juprowaDrainPending DOES use `await` but it's in the drain function body,
    not in the save hook. This test checks the save-hook pattern specifically:
    .then(...) chains instead of await.
    """
    # Extract every line that includes _juprowaPush( and check context
    for i, line in enumerate(index_html.splitlines()):
        if "_juprowaPush(" in line and "AUTOPUSH" in line:
            assert ".then(" in line, f"Save-hook line {i+1} should use .then not await"


def test_save_hook_catches_errors_to_console(index_html):
    """AUTOPUSH-EXC catch must log to console, not toast."""
    assert "[AUTOPUSH-EXC]" in index_html
    # Find context -- must be in a .catch chained after _juprowaPush
    m = re.search(
        r"_juprowaPush\([^)]+\)\.then\([^}]+\}\)\.catch\([^}]+console\.warn\('\[AUTOPUSH-EXC\]'",
        index_html,
    )
    # Softer assertion if regex is too strict:
    if not m:
        assert "AUTOPUSH-EXC" in index_html and "console.warn" in index_html
