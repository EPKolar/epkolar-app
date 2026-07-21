# -*- coding: utf-8 -*-
"""v3.9.805 — Dispo 3A: Auftragstyp-Rang als Gleichstand-Brecher NACH der Prio-Feinstufe (Sebastian).

Prio FUEHRT, der Typ bricht nur den Gleichstand. Neue PURE _dispoTypRang:
mangelbehebung 0 < garantie 1 < reparatur 2 < montage 3 < lieferung 4 < kein/rest 5.
Greedy-Sort: _dispoPrioRang -> _dispoTypRang -> ueberfaelligTage desc -> Alter.
Stoerung/SAT (Topf 0) bleiben ganz vorne; der Typ-Rang bricht NIE die Topf-0-/Prio-Logik.
"""
from conftest import run_node_snippet


def _fns(index_html):
    out = ""
    for name in ("_dispoTopf", "_dispoPrioRang", "_dispoTypRang"):
        a = index_html.index("function " + name + "(")
        out += index_html[a:index_html.index("\n}", a) + 2] + "\n"
    return out


CMP = ("function cmp(a,b){var ta=_dispoPrioRang(a),tb=_dispoPrioRang(b);if(ta!==tb)return ta-tb;"
       "var xa=_dispoTypRang(a),xb=_dispoTypRang(b);if(xa!==xb)return xa-xb;"
       "var ua=a.ueberfaelligTage||0,ub=b.ueberfaelligTage||0;if(ua!==ub)return ub-ua;"
       "return (a.alterMs||0)-(b.alterMs||0);}")


def _typrang(node_exe, index_html, art):
    a = index_html.index("function _dispoTypRang(")
    fn = index_html[a:index_html.index("\n}", a) + 2]
    return int(run_node_snippet(node_exe, fn + f";process.stdout.write(String(_dispoTypRang({{scheinart:{art!r}}})))").strip())


def _cmp_sign(node_exe, index_html, a_js, b_js):
    snip = _fns(index_html) + CMP + f";process.stdout.write(String(Math.sign(cmp({a_js},{b_js}))))"
    return int(run_node_snippet(node_exe, snip).strip())


def test_typrang_alle_typen(node_exe, index_html):
    t = lambda art: _typrang(node_exe, index_html, art)
    assert t("mangelbehebung") == 0
    assert t("garantie") == 1
    assert t("reparatur") == 2
    assert t("montage") == 3
    assert t("lieferung") == 4
    assert t("kein") == 5
    # Nicht gelistet / leer -> 5 (wie kein).
    assert t("wartung") == 5
    assert t("regie") == 5
    assert t("") == 5


def test_typ_bricht_gleichstand_bei_gleicher_prio(node_exe, index_html):
    # Gleiche Prio (normal) -> mangelbehebung vor montage.
    assert _cmp_sign(node_exe, index_html,
                     "{scheinart:'mangelbehebung',prioritaet:'normal'}",
                     "{scheinart:'montage',prioritaet:'normal'}") == -1
    # garantie vor reparatur (Default-Reihung).
    assert _cmp_sign(node_exe, index_html,
                     "{scheinart:'garantie',prioritaet:'normal'}",
                     "{scheinart:'reparatur',prioritaet:'normal'}") == -1


def test_typ_bricht_NIE_die_prio(node_exe, index_html):
    # hoch+kein muss VOR normal+mangelbehebung stehen: die hoehere Prio (hoch, Rang 1.6) schlaegt
    # normal (2.0), der Typ-Rang wird gar nicht erst konsultiert.
    assert _cmp_sign(node_exe, index_html,
                     "{scheinart:'kein',prioritaet:'hoch'}",
                     "{scheinart:'mangelbehebung',prioritaet:'normal'}") == -1
    # Stoerung (Topf 0) vor allem, egal welcher Typ/Prio der andere hat.
    assert _cmp_sign(node_exe, index_html,
                     "{scheinart:'stoerung',prioritaet:'niedrig'}",
                     "{scheinart:'mangelbehebung',prioritaet:'fixtermin'}") == -1


def test_ueberfaellig_nur_innerhalb_gleicher_prio_und_typ(node_exe, index_html):
    # Gleiche Prio + gleicher Typ -> ueberfaellig desc entscheidet.
    assert _cmp_sign(node_exe, index_html,
                     "{scheinart:'kein',prioritaet:'normal',ueberfaelligTage:10}",
                     "{scheinart:'kein',prioritaet:'normal',ueberfaelligTage:2}") == -1


def test_sort_zeile_reihenfolge_pin(index_html):
    assert ("var ta=_dispoPrioRang(a),tb=_dispoPrioRang(b);if(ta!==tb)return ta-tb;" in index_html)
    assert ("var xa=_dispoTypRang(a),xb=_dispoTypRang(b);if(xa!==xb)return xa-xb;" in index_html)
    # Typ steht NACH Prio und VOR Ueberfaellig.
    i_prio = index_html.index("if(ta!==tb)return ta-tb;")
    i_typ = index_html.index("if(xa!==xb)return xa-xb;")
    i_ueb = index_html.index("var ua=a.ueberfaelligTage||0,ub=b.ueberfaelligTage||0;")
    assert i_prio < i_typ < i_ueb, "Reihenfolge Prio -> Typ -> Ueberfaellig verletzt"
