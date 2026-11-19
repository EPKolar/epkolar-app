# -*- coding: utf-8 -*-
"""GF 19.11.: KW-Schnellwahl der Planung zeigt nur aktuelle + 8 kommende Wochen (keine Vergangenheit).
Laeuft die ECHTE _wpKwChipListe aus index.html in Node. Pfeile und Vorwoche-Uebernehmen bleiben unberuehrt."""
import io
import json
import os
import re
import subprocess

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")


def _src():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _fn(src, name):
    i = src.index("function %s(" % name)
    j = src.index("\r\n}\r\n", i) + 5
    return src[i:j]


def _lauf(fn_src, faelle):
    js = ("function _getMaxKW(y){return y===2026?53:52;}\n" + fn_src +
          "\nvar F=%s;console.log(JSON.stringify(F.map(function(f){return _wpKwChipListe.apply(null,f);})));" % json.dumps(faelle))
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


SAVED = [27, 30, 35, 40, 44, 45, 46, 47, 48, 50, 52]
FAELLE = [
    [SAVED, 47, 2026, 47, 2026],   # aktuelle Woche angezeigt
    [SAVED, 46, 2026, 47, 2026],   # Vorwoche angezeigt (z. B. ueber Pfeil)
    [SAVED, 30, 2025, 47, 2026],   # Vorjahr
    [[1, 2, 3, 9], 1, 2027, 47, 2026],  # Folgejahr, Fenster reicht bis KW 2/2027
]


def test_nur_aktuelle_und_kommende_wochen():
    r = _lauf(_fn(_src(), "_wpKwChipListe"), FAELLE)
    assert r[0] == [48, 50, 52], r[0]       # 47 angezeigt -> fehlt; gespeichert und bis 47+8=55
    assert r[1] == [47, 48, 50, 52], r[1]   # aktuelle KW immer dabei; keine Vergangenheit (27..46)
    assert all(k >= 47 for k in r[1])
    assert r[2] == [], r[2]                 # Vorjahr: keine Chips
    assert r[3] == [2], r[3]                # Folgejahr: nur im 8-Wochen-Fenster (53-47=6 -> bis KW 2)


def test_alle_vier_stellen_nutzen_die_liste():
    src = _src()
    assert "savedKws.filter(k=>k!==kw)" not in src
    assert src.count("_wpKwChipListe(savedKws,kw,yr,curKw,curYr)") == 4


def test_pfeile_und_uebernehmen_unberuehrt():
    src = _src()
    assert "onClick: ()=>switchKw(kw-1)" in src and "onClick: ()=>switchKw(kw+1)" in src
    assert "onClick: _wpCopyFromPrevWeek" in src and "copyWeek(_wpVorlageKw)" in src


def test_umkehrprobe_alte_logik_zeigt_vergangenheit():
    alt = "function _wpKwChipListe(saved,kw,yr,curKw,curYr){\r\n  return (saved||[]).filter(function(k){return k!==kw;});\r\n}\r\n"
    r = _lauf(alt, FAELLE)
    assert any(k < 47 for k in r[1]), "alte Logik muss Vergangenheit zeigen - sonst misst der Test nichts"
