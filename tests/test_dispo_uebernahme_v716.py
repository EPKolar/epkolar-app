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
    assert "function DispoPanel({arbeitsscheine,monteure,wpHistory,abs,onUebernehmen,onOpenSchein})" in index_html


def test_uebernahme_uses_regular_updAs(index_html):
    # Der Callback in ArbeitsscheinView schreibt via updAs (byte-gleich zu manuell), Felder termin/monteur/dauer + (v733) terminZeit.
    assert "onUebernehmen: (scheinId,monteurId,iso,dauerMin,startHHMM)=>{" in index_html
    assert 'updAs(scheinId,{terminBestaetigt:iso,monteur:monteurId,dauer:_dispoMinToHHMM(dauerMin),terminZeit:startHHMM||""})' in index_html
    # KEIN eigener SQ.push/Bulk-Sonderpfad im Callback (nur updAs)
    seg = index_html.split("onUebernehmen: (scheinId,monteurId,iso,dauerMin,startHHMM)=>{", 1)[1][:320]
    assert "SQ.push" not in seg


def test_fz_bedarf_not_written_on_uebernahme(index_html):
    # Übernahme schreibt fz_bedarf NICHT (bleibt App-only, nie im Push).
    seg = index_html.split("onUebernehmen: (scheinId,monteurId,iso,dauerMin,startHHMM)=>{", 1)[1][:320]
    assert "fz_bedarf" not in seg and "fzBedarf" not in seg
