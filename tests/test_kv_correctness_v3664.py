"""v3.9.664 KV-Correctness (Bug-Hunt-Subagent) — 3 eindeutige Fixes.

#1 _kvDienstjahre kalendergenau (statt 365.25-Naeherung): am exakten 1./15./25.-Jahrestag
   lieferte die Division eine EFZG-Stufe zu wenig.
#2 EFZG-Verbrauchsanzeige: aus ALLEN Krankdaten (nicht dem gefilterten Block-Set),
   nur im laufenden Arbeitsjahr, volle Wochen abrunden statt jeden Tag aufrunden.
#7 _kvLoadRules coerct numerische kv_rules-Felder (Komma->Punkt), NaN -> Fallback.
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


# ── #1 Dienstjahre kalendergenau ──
def test_dienstjahre_exakter_jahrestag(node_exe, index_html):
    # exakt 15 Jahre -> 15 (nicht 14 wie bei der 365.25-Naeherung)
    assert _eval(node_exe, index_html, "_kvDienstjahre('2011-03-15', Date.UTC(2026,2,15,12))") == 15
    # einen Tag vor dem Jahrestag -> 14
    assert _eval(node_exe, index_html, "_kvDienstjahre('2011-03-15', Date.UTC(2026,2,14,12))") == 14
    # exakt 1 Jahr -> 1
    assert _eval(node_exe, index_html, "_kvDienstjahre('2025-03-15', Date.UTC(2026,2,15,12))") == 1


def test_dienstjahre_altbestand_unveraendert(node_exe, index_html):
    # Regression gegen v3.9.651-Test
    assert _eval(node_exe, index_html, "_kvDienstjahre('2020-01-01', Date.UTC(2026,0,1,12))") == 6
    assert _eval(node_exe, index_html, "_kvDienstjahre('', Date.UTC(2026,0,1))") == 0
    assert _eval(node_exe, index_html, "_kvDienstjahre('2030-01-01', Date.UTC(2026,0,1))") == 0


# ── #2 Arbeitsjahr-Start ──
def test_arbeitsjahr_start_vor_jahrestag(node_exe, index_html):
    # Stichtag Maerz 2026, Eintritt 10.5. -> laufendes Arbeitsjahr begann 10.5.2025
    expr = ("(function(){var s=_efzgArbeitsjahrStartMs('2020-05-10',Date.UTC(2026,2,1,12));"
            "var d=new Date(s);return d.getFullYear()===2025&&d.getMonth()===4&&d.getDate()===10;})()")
    assert _eval(node_exe, index_html, expr) is True


def test_arbeitsjahr_start_nach_jahrestag(node_exe, index_html):
    # Stichtag Juni 2026 -> begann 10.5.2026
    expr = ("(function(){var s=_efzgArbeitsjahrStartMs('2020-05-10',Date.UTC(2026,5,1,12));"
            "var d=new Date(s);return d.getFullYear()===2026&&d.getMonth()===4&&d.getDate()===10;})()")
    assert _eval(node_exe, index_html, expr) is True


def test_arbeitsjahr_start_null(node_exe, index_html):
    assert _eval(node_exe, index_html, "_efzgArbeitsjahrStartMs('', Date.now())") is None


# ── UI-Wiring #2 ──
def test_efzg_display_arbeitsjahr_scoped(index_html):
    assert "var _ajStart=_efzgArbeitsjahrStartMs(_ein,Date.now());" in index_html
    # Verbrauch aus _krAll (unfiltered), nur im Arbeitsjahr, floor
    assert "var _td=_krAll.reduce(function(s,x){if(x.name!==b.name)return s;" in index_html
    assert "return (_ajStart==null||_dm>=_ajStart)?s+1:s;" in index_html
    assert "var _gen=Math.min(_voll,Math.floor(_td/5));" in index_html
    # altes ceil-ueber-Blockset weg
    assert "Math.min(_voll,Math.ceil(_td/5))" not in index_html


# ── UI-Wiring #7 ──
def test_rules_numeric_sanitization(index_html):
    assert "if(typeof KV_RULES_FALLBACK[_kk]==='number'){var _rv=rules[_kk];if(typeof _rv==='string')_rv=_rv.replace(',','.');" in index_html
    assert "rules[_kk]=isNaN(_nv)?KV_RULES_FALLBACK[_kk]:_nv;" in index_html
