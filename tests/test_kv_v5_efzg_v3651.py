"""v3.9.651 KV-V5 — EFZG (Entgeltfortzahlung), pure Funktionen (Node-eval).

Staffel nach Dienstjahren: <1 J = 6, ab 1 J = 8, ab 15 J = 10, ab 25 J = 12 Wochen
VOLL (+ je 4 Wochen halb). NUR Info-Anzeige — Lohnverrechner massgeblich.
"""
import re
import json
from conftest import run_node_snippet


def _block(index_html):
    m = re.search(r"//@KV-EFZG-START(.*?)//@KV-EFZG-END", index_html, re.S)
    assert m, "KV-EFZG-Block nicht gefunden"
    return m.group(1)


def _eval(node_exe, index_html, expr):
    snippet = _block(index_html) + "\nprocess.stdout.write(JSON.stringify((" + expr + ")))"
    return json.loads(run_node_snippet(node_exe, snippet))


def test_efzg_staffel(node_exe, index_html):
    expr = ("_efzgVollWochen(0)===6 && _efzgVollWochen(0.5)===6"
            " && _efzgVollWochen(1)===8 && _efzgVollWochen(14)===8"
            " && _efzgVollWochen(15)===10 && _efzgVollWochen(24)===10"
            " && _efzgVollWochen(25)===12 && _efzgVollWochen(40)===12")
    assert _eval(node_exe, index_html, expr) is True


def test_dienstjahre(node_exe, index_html):
    # 2020-01-01 -> 2026-01-01 = 6 volle Jahre
    assert _eval(node_exe, index_html, "_kvDienstjahre('2020-01-01', Date.UTC(2026,0,1))") == 6
    # knapp unter 1 Jahr -> 0
    assert _eval(node_exe, index_html, "_kvDienstjahre('2025-06-01', Date.UTC(2026,0,1))") == 0
    # leer / ungueltig -> 0
    assert _eval(node_exe, index_html, "_kvDienstjahre('', Date.UTC(2026,0,1))") == 0


def test_dienstjahre_zukunft_nicht_negativ(node_exe, index_html):
    assert _eval(node_exe, index_html, "_kvDienstjahre('2030-01-01', Date.UTC(2026,0,1))") == 0


# ── UI-Wiring ──
def test_efzg_anzeige_im_krankenstand(index_html):
    assert '"EFZG "+_gen+"/"+_voll+" Wo"' in index_html


def test_efzg_info_hinweis(index_html):
    assert "Lohnverrechner massgeblich" in index_html or "Lohnverrechner maßgeblich" in index_html
