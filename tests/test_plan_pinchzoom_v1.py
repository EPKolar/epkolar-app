"""v3.9.708 — Plan-Pinch/Fokus-Zoom: reine Funktion _planZoomAt (state={s,tx,ty}, mid, faktor).

Die Funktion wird per Regex aus index.html extrahiert und mit echtem Node ausgefuehrt.
Geprueft: (1) Zoom auf Punkt P haelt P fix (Plan-Koord unter P vorher==nachher via Inverse-Transform),
(2) Clamp s in [minS,maxS] mit Default [1,5], (3) Inverse-Transform planPx=(client-t)/s.

Modell: world-div hat transform 'translate(tx,ty) scale(s)' mit transformOrigin 0 0.
Screen->Plan (Inverse): planPx = (clientRelativZumUrsprung - t) / s.
"""
import json
import os
import re
import subprocess
import tempfile

import pytest


def _extract_fn(index_html, name):
    m = re.search(r"function " + re.escape(name) + r"\(.*?\n\}", index_html, re.S)
    assert m, name + " nicht in index.html gefunden"
    return m.group(0)


def _run_node(node_exe, index_html, driver):
    """Extrahiert _planZoomAt, haengt Treiber-Code an, fuehrt mit Node aus, gibt JSON zurueck."""
    fn = _extract_fn(index_html, "_planZoomAt")
    src = fn + "\n" + driver
    path = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(src)
            path = f.name
        out = subprocess.run([node_exe, path], capture_output=True, text=True, timeout=30)
        assert out.returncode == 0, "Node-Fehler: " + (out.stderr or out.stdout)
        return json.loads(out.stdout.strip().splitlines()[-1])
    finally:
        if path and os.path.exists(path):
            os.unlink(path)


# Pure Inverse-Transform (screen->plan) — identisch zum Modell in index.html.
_INV = (
    "function _inv(state, pt){var s=(state&&state.s)||1;"
    "return {x:(pt.x-((state&&state.tx)||0))/s, y:(pt.y-((state&&state.ty)||0))/s};}\n"
)


def test_zoom_haelt_punkt_fix(node_exe, index_html):
    # Zoom auf P mit beliebigem Startzustand: der Plan-Punkt unter P ist vorher==nachher.
    driver = _INV + (
        "var st={s:1.5, tx:-40, ty:22};"
        "var P={x:317, y:181};"
        "var before=_inv(st, P);"
        "var st2=_planZoomAt(st, P, 1.7, 0.4, 6);"
        "var after=_inv(st2, P);"
        "console.log(JSON.stringify({before:before, after:after, s2:st2.s}));"
    )
    r = _run_node(node_exe, index_html, driver)
    assert abs(r["before"]["x"] - r["after"]["x"]) < 1e-9, r
    assert abs(r["before"]["y"] - r["after"]["y"]) < 1e-9, r
    # 1.5 * 1.7 = 2.55, innerhalb [0.4,6] -> nicht geclampt
    assert abs(r["s2"] - 2.55) < 1e-9, r


def test_zoom_haelt_punkt_fix_beim_rauszoomen(node_exe, index_html):
    driver = _INV + (
        "var st={s:4.0, tx:120, ty:-300};"
        "var P={x:250, y:410};"
        "var before=_inv(st, P);"
        "var st2=_planZoomAt(st, P, 0.5, 0.4, 6);"
        "var after=_inv(st2, P);"
        "console.log(JSON.stringify({before:before, after:after, s2:st2.s}));"
    )
    r = _run_node(node_exe, index_html, driver)
    assert abs(r["before"]["x"] - r["after"]["x"]) < 1e-9, r
    assert abs(r["before"]["y"] - r["after"]["y"]) < 1e-9, r
    assert abs(r["s2"] - 2.0) < 1e-9, r


def test_clamp_default_1_bis_5(node_exe, index_html):
    # Default-Grenzen (ohne minS/maxS) muessen [1,5] sein.
    driver = (
        "var hi=_planZoomAt({s:4, tx:0, ty:0}, {x:0,y:0}, 100);"   # 4*100 -> clamp 5
        "var lo=_planZoomAt({s:2, tx:0, ty:0}, {x:0,y:0}, 0.001);"  # 2*0.001 -> clamp 1
        "console.log(JSON.stringify({hi:hi.s, lo:lo.s}));"
    )
    r = _run_node(node_exe, index_html, driver)
    assert r["hi"] == 5, r
    assert r["lo"] == 1, r


def test_clamp_custom_bounds(node_exe, index_html):
    # Live-Aufrufer nutzen [0.4, 6] — Grenzen sind parametrierbar.
    driver = (
        "var hi=_planZoomAt({s:5, tx:0, ty:0}, {x:0,y:0}, 100, 0.4, 6);"
        "var lo=_planZoomAt({s:1, tx:0, ty:0}, {x:0,y:0}, 0.0001, 0.4, 6);"
        "console.log(JSON.stringify({hi:hi.s, lo:lo.s}));"
    )
    r = _run_node(node_exe, index_html, driver)
    assert r["hi"] == 6, r
    assert abs(r["lo"] - 0.4) < 1e-9, r


def test_inverse_transform_beispiel(node_exe, index_html):
    # Spez.-Beispiel: s=2, t=(100,50): client(300,150) -> plan(100,50).
    driver = _INV + (
        "var plan=_inv({s:2, tx:100, ty:50}, {x:300, y:150});"
        "console.log(JSON.stringify(plan));"
    )
    r = _run_node(node_exe, index_html, driver)
    assert abs(r["x"] - 100) < 1e-9, r
    assert abs(r["y"] - 50) < 1e-9, r


def test_planzoomat_in_index(index_html):
    # Reine Funktion existiert top-level und wird von den Zoom-Wegen genutzt.
    assert "function _planZoomAt(state, mid, faktor, minS, maxS){" in index_html
    assert index_html.count("_planZoomAt(") >= 4  # Definition + >=3 Aufrufstellen
