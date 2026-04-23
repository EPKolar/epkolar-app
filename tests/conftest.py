"""Shared fixtures for EPKolar static tests."""
import os
import re
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


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
