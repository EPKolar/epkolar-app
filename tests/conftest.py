"""Shared fixtures for EPKolar static tests."""
import os
import re
import subprocess
import shutil
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

NODE_CANDIDATES = [
    r"C:\Program Files\nodejs\node.exe",
    r"C:\Program Files\nodejs\node.cmd",
    "node",
]


def _find_node():
    for c in NODE_CANDIDATES:
        if os.path.isfile(c):
            return c
    found = shutil.which("node")
    return found


@pytest.fixture(scope="session")
def node_exe():
    exe = _find_node()
    if not exe:
        pytest.skip("Node.js executable not found")
    return exe


@pytest.fixture(scope="session")
def repo_root():
    return REPO_ROOT


@pytest.fixture(scope="session")
def index_html(repo_root):
    with open(os.path.join(repo_root, "index.html"), "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="session")
def sw_js(repo_root):
    with open(os.path.join(repo_root, "sw.js"), "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="session")
def app_version(index_html):
    m = re.search(r'const\s+APP_VERSION\s*=\s*"([^"]+)"', index_html)
    assert m, "APP_VERSION constant not found"
    return m.group(1)


@pytest.fixture(scope="session")
def cache_name(sw_js):
    m = re.search(r'const\s+CACHE_NAME\s*=\s*"([^"]+)"', sw_js)
    assert m, "CACHE_NAME constant not found"
    return m.group(1)


def _extract_fn(index_html, name, signature_regex=None):
    """Extract a top-level `function NAME(...)` definition (including body)."""
    # Find start position
    if signature_regex is None:
        signature_regex = rf"function\s+{re.escape(name)}\s*\("
    m = re.search(signature_regex, index_html)
    if not m:
        return None
    start = m.start()
    i = index_html.find("{", start)
    if i < 0:
        return None
    depth = 0
    while i < len(index_html):
        c = index_html[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return index_html[start : i + 1]
        i += 1
    return None


@pytest.fixture(scope="session")
def fn_n(index_html):
    fn = _extract_fn(index_html, "_n")
    assert fn, "function _n not found"
    return fn


@pytest.fixture(scope="session")
def fn_juprowa_sanitize(index_html):
    fn = _extract_fn(index_html, "_juprowaSanitize")
    assert fn, "function _juprowaSanitize not found"
    return fn


@pytest.fixture(scope="session")
def fn_juprowa_reverse_map(index_html):
    """Extract _juprowaReversMap + needed dependencies as runnable JS bundle.

    Depends on: _juprowaSanitize, _juprowaWorkerToCode, JUPROWA_PRIO_REV,
    JUPROWA_STATUS_REV. For test harness we stub the globals and inline
    _juprowaSanitize (we already extract it).
    """
    sanitize = _extract_fn(index_html, "_juprowaSanitize")
    reverse_map = _extract_fn(index_html, "_juprowaReversMap")
    assert sanitize and reverse_map
    stubs = (
        "const JUPROWA_PRIO_REV={keine:'0',niedrig:'1',normal:'2',hoch:'3'};\n"
        "const JUPROWA_STATUS_REV={aufgenommen:'1',in_bearbeitung:'2',"
        "erledigt:'3',abgerechnet:'4',storniert:'5'};\n"
        "function _juprowaWorkerToCode(id){return null;}\n"
    )
    return stubs + sanitize + "\n" + reverse_map


def run_node_snippet(node_exe, snippet):
    """Run a JS snippet in Node and return stdout stripped.

    Note: `encoding='utf-8'` is critical on Windows. Without it, subprocess
    decodes stdout via the system active codepage (cp1252), which
    double-mangles any non-ASCII bytes emitted by Node.
    """
    result = subprocess.run(
        [node_exe, "-e", snippet],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(f"node failed: {result.stderr}")
    return result.stdout.strip()
