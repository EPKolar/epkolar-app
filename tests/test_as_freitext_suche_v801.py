# -*- coding: utf-8 -*-
"""v3.9.801 — AS-Freitext-Suche findet Prioritaet + Auftragstyp (Sebastian).

Das "Alle Arten"-Dropdown filtert scheinart bereits; die FREITEXT-Suche (_hay) durchsuchte aber nur
nummer/kundName/arbeitsanweisungen/projektnr. Jetzt zusaetzlich Prio-Label + Auftragstyp-Label (DEUTSCH,
wie in der Spalte), sodass "hoch"/"garantie" die Zeilen finden. Token-Logik unveraendert, nur der
Haystack waechst.
"""
import re
from conftest import run_node_snippet


def _const(index_html, name):
    a = index_html.index("const " + name + "=")
    return index_html[a:index_html.index("\n", a)]


def test_haystack_erweitert_static(index_html):
    line_a = index_html.index("if(search){const _hay=")
    line = index_html[line_a:index_html.index("\n", line_a)]
    assert "(AS_PRIO[a.prioritaet]&&AS_PRIO[a.prioritaet].l)||a.prioritaet" in line, "Prio-Label fehlt im Haystack"
    assert "(AS_ART[a.scheinart]&&AS_ART[a.scheinart].l)" in line, "Auftragstyp-Label fehlt im Haystack"
    # Token-Logik unveraendert.
    assert "_toks.every(t=>_hay.includes(t))" in line, "Token-Logik veraendert"


def test_suche_trifft_garantie_und_hoch(node_exe, index_html):
    # Realer Haystack-Ausdruck mit den ECHTEN AS_PRIO/AS_ART-Labels aus index.html.
    as_prio = _const(index_html, "AS_PRIO")
    as_art = _const(index_html, "AS_ART")
    # COLORS.ERROR etc. in AS_PRIO stubben (nur die Labels zaehlen).
    stub = "const COLORS={ERROR:'#e11'};"
    hay_expr = ('((a.nummer||"")+" "+(a.kundName||"")+" "+(a.arbeitsanweisungen||"")+" "+(a.projektnr||"")'
                '+" "+((AS_PRIO[a.prioritaet]&&AS_PRIO[a.prioritaet].l)||a.prioritaet||"")'
                '+" "+((AS_ART[a.scheinart]&&AS_ART[a.scheinart].l)||"")).toLowerCase()')

    def _match(schein, token):
        snip = (stub + as_prio + as_art + f";var a={schein};var _hay={hay_expr};"
                f"process.stdout.write(String(_hay.includes({token!r})))")
        return run_node_snippet(node_exe, snip).strip()

    assert _match("{scheinart:'garantie'}", "garantie") == "true", "'garantie' findet Garantie-Schein nicht"
    assert _match("{prioritaet:'hoch'}", "hoch") == "true", "'hoch' findet hoch-Prio-Schein nicht"
    assert _match("{scheinart:'stoerung'}", "störung") == "true", "'stoerung' (deutsches Label) trifft nicht"
    # Gegenprobe: ein kein/keine-Schein enthaelt NICHT 'garantie'.
    assert _match("{scheinart:'kein',prioritaet:'normal'}", "garantie") == "false"
