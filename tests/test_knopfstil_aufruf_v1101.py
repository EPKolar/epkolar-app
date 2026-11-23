# -*- coding: utf-8 -*-
"""v3.9.1101 Hotfix: bpS und bdS sind OBJEKTE (const bpS={...}), bsS/btS dagegen _mkS-Funktionen.

1099 rief im Kamera-Anordnen bpS() auf -> "bpS is not a function" -> KameraView stuerzte ab, sobald der Admin
"Anordnung aendern" tippte (ViewBoundary). Gefunden 23.11. im Browser-Lauf des Verrechnungs-Reiters (derselbe Fehler).
Der Render-Test der Anordnung hatte den Fehler verdeckt: dort war bpS in der Attrappe aufrufbar.
Riegel: kein Aufruf eines Objekt-Stils, und die Definitionen bleiben, wie die Aufrufer sie erwarten.
"""
import io
import os
import re

HIER = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HIER, "..", "index.html")


def _src():
    return io.open(HTML, encoding="utf-8", newline="").read()


def _objekt_stile(s):
    return set(re.findall(r"^const (b[a-z]S)=\{", s, re.M))


def _aufrufe(s, namen):
    code = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return {n: len(re.findall(r"(?<![A-Za-z0-9_$.])" + n + r"\(", code)) for n in namen}


def test_objektstile_bekannt():
    s = _src()
    assert {"bpS", "bdS"} <= _objekt_stile(s)
    assert re.search(r"^const bsS=_mkS\(", s, re.M) and re.search(r"^const btS=_mkS\(", s, re.M)


def test_kein_aufruf_eines_objektstils():
    s = _src()
    a = _aufrufe(s, _objekt_stile(s))
    assert a and all(v == 0 for v in a.values()), a


def test_umkehrprobe_altstand_1099_faellt_durch():
    s = _src()
    alt = s.replace("disabled:ordnen.busy,style:bpS},", "disabled:ordnen.busy,style:bpS()},", 1)
    assert alt != s
    assert _aufrufe(alt, {"bpS"})["bpS"] == 1
