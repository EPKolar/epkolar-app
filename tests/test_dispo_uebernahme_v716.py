# -*- coding: utf-8 -*-
"""v3.9.716 — Dispo E4b Übernahme: Chip -> regulärer updAs-Edit (terminBestaetigt+monteur+dauer) -> OFFA-Push.

Byte-gleich zu einem manuellen Büro-Edit derselben Felder (derselbe updAs-Pfad) -> löst push_pending +
den bestehenden Juprowa/OFFA-Push aus. fz_bedarf wird NICHT geschrieben (kein Push).
"""


def _dispopanel(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    return index_html[start:end]


def test_minutes_to_hhmm_helper(index_html):
    assert "function _dispoMinToHHMM(m)" in index_html


def test_chip_button_calls_onuebernehmen(index_html):
    body = _dispopanel(index_html)
    assert "onUebernehmen?h('button'" in body
    # v3.9.733 #20: 4. Arg = effektive Dauer (_eff), 5. Arg = Startzeit (HH:MM aus _dispoAblauf) -> terminZeit.
    assert "onUebernehmen(c.scheinId,m.id,t.iso,_eff,_dispoMinToHHMM(_win.startMin))" in body
    # Übernahme-Button nur wenn Callback da (read-only bleibt möglich)
    # Pin nachgezogen 24.11.2026 (Dispo mobil, Weg B): neue Prop onBestaetigen (Termin bestaetigen). Alt: ...onToggleBlock,onRefreshScheine})
    assert "function DispoPanel({arbeitsscheine,monteure,wpHistory,abs,onUebernehmen,onOpenSchein,onDrop,onToggleBlock,onRefreshScheine,onBestaetigen})" in index_html


def test_uebernahme_uses_regular_updAs(index_html):
    # Pin nachgezogen 24.11.2026 (GF-Entscheid Weg B): alt updAs(scheinId,{terminBestaetigt:iso,monteur:monteurId,...}).
    # neu: Planung ueber dispoPlanen; der einzige Weg zu den Terminfeldern ist "Termin bestaetigen" (updAs, ein Push).
    i = index_html.index("onUebernehmen: (scheinId,monteurId,iso,dauerMin,startHHMM)=>{")
    seg = index_html[i:index_html.index("}, onOpenSchein:", i)]
    assert "dispoPlanen(scheinId," in seg and "updAs(" not in seg
    # KEIN eigener SQ.push/Bulk-Sonderpfad im Callback
    assert "SQ.push" not in seg
    assert "const terminBestaetigen=(id)=>{const s=arbeitsscheine.find(x=>x.id===id);const r=_asTerminBestaetigen(s,curUser.role,updAs);" in index_html


def test_fz_bedarf_not_written_on_uebernahme(index_html):
    # Übernahme schreibt fz_bedarf NICHT (bleibt App-only, nie im Push).
    seg = index_html.split("onUebernehmen: (scheinId,monteurId,iso,dauerMin,startHHMM)=>{", 1)[1][:320]
    assert "fz_bedarf" not in seg and "fzBedarf" not in seg
