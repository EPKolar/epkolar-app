# -*- coding: utf-8 -*-
"""v3.9.810 — AS-Freitext-Suche findet zusaetzlich Sachbearbeiter + Monteur-Name (Sebastian).

v801 hatte _hay um Prio-Label + Auftragstyp-Label erweitert. v810 haengt additiv an:
  - Sachbearbeiter (a.sachbearbeiter, String, wie in der Liste)
  - Monteur-NAME via monteure-Lookup auf a.monteur -> Feld .n (deutscher Anzeigename, NICHT die id;
    kein optional chaining, Guard ueber (((monteure||[]).find(...)||{}).n||"")).
Token-Logik (_toks.every), Filter-Dropdowns, Sortierung bleiben byte-identisch. monteure ist jetzt in
den useMemo-Deps (sonst rechnet die Suche bei Monteur-Wechsel nicht neu).
"""
from conftest import run_node_snippet


def _const(index_html, name):
    a = index_html.index("const " + name + "=")
    return index_html[a:index_html.index("\n", a)]


def test_haystack_v801_unveraendert_static(index_html):
    line_a = index_html.index("if(search){const _hay=")
    line = index_html[line_a:index_html.index("\n", line_a)]
    # v801-Bestand bleibt.
    assert "(AS_PRIO[a.prioritaet]&&AS_PRIO[a.prioritaet].l)||a.prioritaet" in line, "Prio-Label fehlt"
    assert "(AS_ART[a.scheinart]&&AS_ART[a.scheinart].l)" in line, "Auftragstyp-Label fehlt"
    assert "_toks.every(t=>_hay.includes(t))" in line, "Token-Logik veraendert"


def test_haystack_v810_sb_und_monteur_static(index_html):
    line_a = index_html.index("if(search){const _hay=")
    line = index_html[line_a:index_html.index("\n", line_a)]
    assert '(a.sachbearbeiter||"")' in line, "Sachbearbeiter fehlt im Haystack"
    assert '(((monteure||[]).find(m=>m.id===a.monteur)||{}).n||"")' in line, "Monteur-Name-Lookup fehlt/abweichend"
    # Projekt-Verbot optional chaining nicht eingeschleppt.
    assert "?." not in line, "optional chaining im Haystack (Projekt-Verbot)"
    # monteure in den useMemo-Deps.
    assert "[arbeitsscheine,monteure,isMonteurRole,isAdmin,curUser.monteurId,filterStatus,filterArt,filterMonteur,filterSB,search,quickFilter,_todayStr]" in index_html, "monteure fehlt in den useMemo-Deps"


def test_suche_trifft_prio_typ_sb_monteur(node_exe, index_html):
    as_prio = _const(index_html, "AS_PRIO")
    as_art = _const(index_html, "AS_ART")
    stub = "const COLORS={ERROR:'#e11'};var monteure=[{id:'m7',n:'Hans Huber'}];"
    hay_expr = ('((a.nummer||"")+" "+(a.kundName||"")+" "+(a.arbeitsanweisungen||"")+" "+(a.projektnr||"")'
                '+" "+((AS_PRIO[a.prioritaet]&&AS_PRIO[a.prioritaet].l)||a.prioritaet||"")'
                '+" "+((AS_ART[a.scheinart]&&AS_ART[a.scheinart].l)||"")'
                '+" "+(a.sachbearbeiter||"")+" "+(((monteure||[]).find(m=>m.id===a.monteur)||{}).n||"")).toLowerCase()')

    def _match(schein, token):
        snip = (stub + as_prio + as_art + f";var a={schein};var _hay={hay_expr};"
                f"process.stdout.write(String(_hay.includes({token!r})))")
        return run_node_snippet(node_exe, snip).strip()

    # v801-Bestand
    assert _match("{scheinart:'garantie'}", "garantie") == "true"
    assert _match("{prioritaet:'hoch'}", "hoch") == "true"
    # v810 neu: Sachbearbeiter + Monteur-Name (Anzeigename, nicht id)
    assert _match("{sachbearbeiter:'SCHOBER'}", "schober") == "true", "SB-Name findet Zeile nicht"
    assert _match("{monteur:'m7'}", "hans huber") == "true", "Monteur-Name findet Zeile nicht"
    # Gegenprobe: unbekannter SB/Monteur -> kein Treffer, kein Wurf (||{}-Guard)
    assert _match("{monteur:'unbekannt',sachbearbeiter:'SCHOBER'}", "hans huber") == "false"
    assert _match("{sachbearbeiter:'SCHOBER'}", "günther") == "false"
