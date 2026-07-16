# -*- coding: utf-8 -*-
"""v3.9.715 — Dispo E4-Tab (minimal, read-only): DispoPanel + _dispoBuildInput + gated Sub-Tab.

Struktur-Pins; die _dispoBuildInput->_dispoPlan-Kette wird im Browser-Smoke ausgefuehrt.
"""


def test_dispopanel_component_present(index_html):
    assert "function DispoPanel({arbeitsscheine,monteure,wpHistory,abs})" in index_html
    assert "Vorschlagsplanung" in index_html


def test_buildinput_present_and_exported(index_html):
    assert "function _dispoBuildInput(scheine,monteure,wpHistory,absMap,now)" in index_html
    assert "window._dispoBuildInput=_dispoBuildInput" in index_html
    # Folgewoche Mo-Fr, Prio-1 (Termin+Monteur) als Kapazitaets-Abzug
    assert "d.setDate(d.getDate()-(dow-1)+7)" in index_html
    assert "AS_GRP_OFFEN.indexOf(s.scheinstatus)>=0 && (!s.terminBestaetigt||!s.monteur)" in index_html


def test_tab_gated_buero_pl_admin(index_html):
    assert '...((["admin","buero","projektleiter"].indexOf(curUser.role)>=0)?[{id:"dispo",i:"🗓",l:"Vorschlag"}]:[])' in index_html


def test_render_wired(index_html):
    assert 'sub==="dispo"&&React.createElement(DispoPanel, {arbeitsscheine: arbeitsscheine, monteure: monteure, wpHistory: wpHistory, abs: abs})' in index_html
    # ArbeitsscheinView bekommt jetzt wpHistory + abs
    assert "function ArbeitsscheinView({arbeitsscheine,setArbeitsscheine,monteure,ww,curUser,pushNotif,users,wpHistory,abs})" in index_html


def test_readonly_no_write_in_panel(index_html):
    # DispoPanel darf (Stufe A2) NICHTS schreiben — kein updAs/SQ.push/setArbeitsscheine im Panel-Body.
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    body = index_html[start:end]
    for w in ("updAs(", "SQ.push(", "setArbeitsscheine("):
        assert w not in body, "DispoPanel A2 ist read-only, %s verboten" % w
