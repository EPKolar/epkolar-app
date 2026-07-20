# -*- coding: utf-8 -*-
"""v3.9.773 — Zulagen-Vergabe-Kacheln FinkZeit-lesbar (Wochentag + Datum + Stunden).

NUR Kachel-Layout — die angezeigte Stundenzahl (gebuchte Projektstunde/IST) und die Rechnung
bleiben unverändert. Wochentag via _mzWtag (Intl Europe/Vienna, nie rohes getDay).
"""
import re
import subprocess


def test_mzwtag_existiert_und_exportiert(index_html):
    assert "function _mzWtag(iso){" in index_html, "_mzWtag-Helper fehlt"
    assert "window._mzWtag=_mzWtag;" in index_html, "_mzWtag nicht window-exportiert"
    assert "timeZone:'Europe/Vienna'" in index_html, "_mzWtag nutzt nicht Europe/Vienna"


def test_kachel_zeigt_wochentag_und_datum(index_html):
    a = index_html.index("const _tagBtn=function(wid,d,std){")
    btn = index_html[a:a + 1200]
    assert "_mzWtag(d)" in btn, "Kachel leitet den Wochentag nicht ab"
    assert "String(d).slice(8,10)+'.'+String(d).slice(5,7)+'.'" in btn, "Kachel zeigt kein TT.MM.-Datum"
    # Stundenzahl bleibt (std, gebucht) — nicht durch Soll ersetzt
    assert "_n(std,1)" in btn, "Stundenzahl (std) nicht mehr angezeigt"


def test_wochentag_node_eval(index_html, tmp_path):
    m = re.search(r"function _mzWtag\(iso\)\{.*?\n\}", index_html, re.S)
    assert m, "_mzWtag-Rumpf nicht lesbar"
    js = m.group(0) + """
var out=[];
out.push(_mzWtag('2026-07-06')); // Mo
out.push(_mzWtag('2026-07-08')); // Mi
out.push(_mzWtag('2026-07-10')); // Fr
out.push(_mzWtag('2026-07-11')); // Sa
out.push(_mzWtag('2026-07-12')); // So
console.log(JSON.stringify(out));
"""
    f = tmp_path / "wtag.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run(["node", str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    got = r.stdout.strip().splitlines()[-1]
    assert got == '["Mo","Mi","Fr","Sa","So"]', \
        "Wochentag-Ableitung falsch (Vienna-TZ). Erwartet Mo/Mi/Fr/Sa/So für 06.-12.07.2026. Bekommen: " + got


def test_rechnung_unberuehrt(index_html):
    assert "taggeldAb6h:11.71," in index_html
    assert "montagezulageStd:1.13," in index_html
    for fn in ("function _kvMontagezulageTag(", "function _kvTaggeldTag(", "function _pzeTagRow("):
        assert fn in index_html, "Rechenfunktion versehentlich entfernt: " + fn
