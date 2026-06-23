import re, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
def _v(text, pat):
    m = re.search(pat, text); assert m, f"not found: {pat}"; return m.group(1)
def test_version_triple_sync():
    idx = (ROOT/"index.html").read_text(encoding="utf-8")
    sw  = (ROOT/"sw.js").read_text(encoding="utf-8")
    sw_ver = _v(idx, r"var SW_VER='epkolar-v(3\.9\.\d+)'")
    app    = _v(idx, r'const APP_VERSION="(3\.9\.\d+)-supabase"')
    cache  = _v(sw,  r'const CACHE_NAME = "epkolar-v(3\.9\.\d+)"')
    assert sw_ver == app == cache, f"VERSION DRIFT: SW_VER={sw_ver} APP={app} CACHE={cache}"
