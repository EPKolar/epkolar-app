"""v3.9.671 Montagezulage Phase 1 — manuelle Vergabe pro MA-Tag.

Sebastian-Entscheid (KV Metallgewerbe Abschn. VIII Pkt. 5): Zulage wird MANUELL
pro Mitarbeiter-Tag vergeben (kein Auto-Erkennung), App rechnet Tagesstunden x Satz.

Pure Functions im //@KV-ZULAGEN-Block:
  _kvMontagezulageSatz(datum, satzQuelle)  -> Satz nach JAHR DES EINTRAGS-DATUMS
  _kvMontagezulageTag(stdOhnePause, datum, satzQuelle, flag) -> flag? std*satz : 0

Deckt ab: Jahreswechsel 2026/2027, flag=false, 0h, unbekanntes Jahr (Fallback),
deutsches Komma-Coercion (Muster v664).
"""
import re
import json
import pytest
from conftest import run_node_snippet


RULES = "{montagezulage:{2026:1.155,2027:1.178},montagezulageStd:1.155}"


def _block(index_html):
    m = re.search(r"//@KV-ZULAGEN-START(.*?)//@KV-ZULAGEN-END", index_html, re.S)
    assert m, "KV-ZULAGEN-Block nicht gefunden"
    return m.group(1)


def _eval(node_exe, index_html, expr):
    snippet = _block(index_html) + "\nprocess.stdout.write(JSON.stringify((" + expr + ")))"
    return json.loads(run_node_snippet(node_exe, snippet))


# ── Jahreswechsel: Satz nach Jahr des Eintrags-Datums ──
def test_jahreswechsel_2026_vs_2027(node_exe, index_html):
    # 31.12.2026 -> 1.155, 01.01.2027 -> 1.178 (8h Tag)
    assert _eval(node_exe, index_html, "_kvMontagezulageTag(8,'2026-12-31'," + RULES + ",true)") == pytest.approx(9.24)
    assert _eval(node_exe, index_html, "_kvMontagezulageTag(8,'2027-01-01'," + RULES + ",true)") == pytest.approx(9.424)


def test_satz_direkt(node_exe, index_html):
    assert _eval(node_exe, index_html, "_kvMontagezulageSatz('2026-03-15'," + RULES + ")") == pytest.approx(1.155)
    assert _eval(node_exe, index_html, "_kvMontagezulageSatz('2027-07-01'," + RULES + ")") == pytest.approx(1.178)


# ── flag falsy -> 0 ──
def test_flag_false_null_zero(node_exe, index_html):
    assert _eval(node_exe, index_html, "_kvMontagezulageTag(8,'2026-06-01'," + RULES + ",false)") == 0
    assert _eval(node_exe, index_html, "_kvMontagezulageTag(8,'2026-06-01'," + RULES + ",0)") == 0
    assert _eval(node_exe, index_html, "_kvMontagezulageTag(8,'2026-06-01'," + RULES + ",undefined)") == 0


# ── 0h -> 0 (auch bei flag=true) ──
def test_null_stunden(node_exe, index_html):
    assert _eval(node_exe, index_html, "_kvMontagezulageTag(0,'2026-06-01'," + RULES + ",true)") == 0
    assert _eval(node_exe, index_html, "_kvMontagezulageTag(-3,'2026-06-01'," + RULES + ",true)") == 0


# ── Unbekanntes Jahr -> Fallback montagezulageStd ──
def test_unbekanntes_jahr_fallback(node_exe, index_html):
    # 2030 nicht in der Map -> Fallback 1.155
    assert _eval(node_exe, index_html, "_kvMontagezulageSatz('2030-05-05'," + RULES + ")") == pytest.approx(1.155)
    assert _eval(node_exe, index_html, "_kvMontagezulageTag(10,'2030-05-05'," + RULES + ",true)") == pytest.approx(11.55)
    # leeres/kaputtes Datum -> Fallback
    assert _eval(node_exe, index_html, "_kvMontagezulageSatz(''," + RULES + ")") == pytest.approx(1.155)


# ── Deutsches Komma-Coercion (Muster v664) ──
def test_komma_coercion(node_exe, index_html):
    # Jahres-Satz als String mit Komma
    assert _eval(node_exe, index_html, "_kvMontagezulageSatz('2026-01-01',{montagezulage:{2026:'1,155'},montagezulageStd:1.155})") == pytest.approx(1.155)
    # Fallback-Satz als String mit Komma (unbek. Jahr)
    assert _eval(node_exe, index_html, "_kvMontagezulageSatz('2030-01-01',{montagezulageStd:'1,20'})") == pytest.approx(1.20)
    # kaputter Satz -> Fallback-Default (v3.9.768: 1,13 statt 1,155)
    assert _eval(node_exe, index_html, "_kvMontagezulageSatz('2030-01-01',{montagezulageStd:'abc'})") == pytest.approx(1.13)


# ── UI-Wiring / Regression-Guards ──
def test_kv_rules_map_present(index_html):
    # v3.9.768: Satz 2026 = 1,13 (Lohnzettel LA 4060). 2027 BEWUSST nicht hinterlegt —
    # der frueher gepinnte Wert 1,178 war unbelegt und ist jetzt Lohnverrechner-Pruefpunkt.
    assert "montagezulage:{2026:1.13}" in index_html


def test_save_handles_object_field(index_html):
    # KVRulesConfig._save darf Objekt-Felder nicht via String(obj) zerstoeren
    assert "else if(fv&&typeof fv==='object'){" in index_html
    assert "om[yy]=isNaN(nn)?fv[yy]:nn;" in index_html


def test_window_exports(index_html):
    assert "window._kvMontagezulageTag=_kvMontagezulageTag;" in index_html
    assert "window._kvMontagezulageSatz=_kvMontagezulageSatz;" in index_html
