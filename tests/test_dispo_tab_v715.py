# -*- coding: utf-8 -*-
"""v3.9.715 — Dispo E4-Tab (minimal, read-only): DispoPanel + _dispoBuildInput + gated Sub-Tab.

Struktur-Pins; die _dispoBuildInput->_dispoPlan-Kette wird im Browser-Smoke ausgefuehrt.
"""


def test_dispopanel_component_present(index_html):
    assert "function DispoPanel({arbeitsscheine,monteure,wpHistory,abs,onUebernehmen,onOpenSchein,onDrop,onToggleBlock})" in index_html
    assert "Vorschlagsplanung" in index_html


def test_buildinput_present_and_exported(index_html):
    assert "function _dispoBuildInput(scheine,monteure,wpHistory,absMap,now,horizontWochen,geoMap,distMatrix,blocksMap)" in index_html
    assert "window._dispoBuildInput=_dispoBuildInput" in index_html
    # v3.9.739 P1: Anker = Montag der AKTUELLEN Woche (KW+0) — die laufende Woche ist sichtbar.
    assert "d.setDate(d.getDate()-(dow-1));" in index_html
    # v3.9.727 #17: Scope = offen (nicht aufgeschoben) UND (kein Termin ODER ueberfaellig termin<heute)
    assert 'if(s.scheinstatus==="aufgeschoben")return false;var t=_termISO(s);return (!t)||(t<_heute);' in index_html


def test_tab_gated_buero_pl_admin(index_html):
    # v3.9.738 #21: Tab heisst jetzt "Dispo" (Gate buero/pl/admin unveraendert).
    assert '...((["admin","buero","projektleiter"].indexOf(curUser.role)>=0)?[{id:"dispo",i:"🗓",l:"Dispo"}]:[])' in index_html


def test_render_wired(index_html):
    assert 'sub==="dispo"&&React.createElement(DispoPanel, {arbeitsscheine: arbeitsscheine, monteure: monteure, wpHistory: wpHistory, abs: abs, onUebernehmen:' in index_html
    # ArbeitsscheinView bekommt jetzt wpHistory + abs
    assert "function ArbeitsscheinView({arbeitsscheine,setArbeitsscheine,monteure,ww,curUser,pushNotif,users,wpHistory,abs})" in index_html


def test_readonly_no_write_in_panel(index_html):
    # DispoPanel darf (Stufe A2) NICHTS schreiben — kein updAs/SQ.push/setArbeitsscheine im Panel-Body.
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    body = index_html[start:end]
    for w in ("updAs(", "SQ.push(", "setArbeitsscheine("):
        assert w not in body, "DispoPanel A2 ist read-only, %s verboten" % w
