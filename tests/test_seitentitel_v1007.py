# -*- coding: utf-8 -*-
"""v3.9.1007 - Seitentitel einheitlich gross (UI.fSeiteMob/UI.fSeite).

Gemessen 412 px ueber alle 18 Reiter: 14 Titel standen auf 18 px, Chef-Portal
und Bauprovisorien auf 20 px. Jetzt alle Emoji-Titel 18 px. Ausnahme bleibt
bewusst die Projektliste (eigene CI-Gestaltung seit v3.9.933, ohne Emoji).
Die Emoji der Titel folgen dem Reiter (Abwesenheiten 🏖️, Einstellungen 🔌).
v3.9.1010: statt Emoji tragen Titel und Reiter denselben IKON-Schluessel
(_ikT("sonne",...) / {l:"Abwesenheiten",ik:"sonne"}). Die Eigenschaft bleibt:
der Titel zeigt das Zeichen seines Reiters.
Fussleiste gemessen: 5 Knoepfe, Symbol 20 px, Text 12 px, gleiche Lage - kein Eingriff.
"""


def test_chef_und_bauprovisorien_nutzen_die_titelgroesse(index_html):
    assert 'fontSize:isMob?UI.fSeiteMob:UI.fSeite,fontWeight:800,margin:0}},_ikT("krone","Chef-Portal")' in index_html
    assert "h('h2',{style:{fontSize:window.innerWidth<BP_MOB?UI.fSeiteMob:UI.fSeite,fontWeight:800,color:V.tx,margin:0}" in index_html
    assert "h('h2',{style:{fontSize:20," not in index_html


def test_titel_emoji_wie_der_reiter(index_html):
    assert '{l:"Abwesenheiten",ik:"sonne"' in index_html and '_ikT("sonne","Abwesenheiten")' in index_html
    assert '_ikT("kalender","Abwesenheiten")' not in index_html
    assert '{l:"Einstellungen",ik:"regler"' in index_html and '_ikT("regler","Einstellungen")' in index_html
    assert '_ikT("schild","Einstellungen")' not in index_html
