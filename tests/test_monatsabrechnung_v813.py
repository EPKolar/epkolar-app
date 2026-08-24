# -*- coding: utf-8 -*-
"""v3.9.813 — Monatsabrechnung (StundenzettelView) Monteur-Eigensicht.

Neu: Monats-Navigation (Vor/Zurueck) + Freigabe-Status-Badge + Karte "Meine Monatssumme"
(Ist-Stunden aus time_entries + Entfernungszulage). Die EZ MUSS autoritativ ueber _ezEffTage/
_ezFetch/_ezSaetze/_ezAbsSet laufen (nicht selbst nachgerechnet) — das pinnt dieser Test, damit
kein spaeterer Edit die Lohn-Rechnung dupliziert/verfaelscht. abs/approvals werden als neue Props
in die View gereicht (fuer _ezAbsSet, v783-Abwesenheits-Ausschluss).
"""


def test_props_durchgereicht(index_html):
    assert "function StundenzettelView({monteure,ww,curUser,users,entries,projects,abs,approvals}){" in index_html, \
        "abs/approvals fehlen in der StundenzettelView-Signatur"
    # v3.9.864 KORRIGIERT: hier stand bis v3.9.863 als Wert der nackte Name `approvals`.
    # Der Test war gruen — er hat den WORTLAUT der Callsite geprueft, nicht ob der Wert
    # aufloest. Eine Bindung dieses Namens gibt es im App-Render nicht (der State heisst
    # absApprovals, :7348) -> beim Oeffnen des Tabs "Monatsabrechnung" ReferenceError im
    # Render von App, und die GANZE App fiel auf die Fehlerseite. Ein String-Match kann
    # einen ReferenceError festschreiben; deshalb prueft tests/test_stunden_approvals_prop_v864.py
    # zusaetzlich die QUELLE (nur absApprovals erlaubt) statt nur den Text.
    assert ("StundenzettelView, { monteure: monteure, ww: ww, curUser: curUser, users: users, "
            "entries: entries, projects: projects, abs: abs, approvals: absApprovals}" in index_html), \
        "abs/approvals werden am Render-Ort nicht durchgereicht"


def test_ez_autoritativ_verdrahtet(index_html):
    # Die Monatssumme nutzt die AUTORITATIVEN EZ-Helfer (kein hand-gerechnetes EZ).
    assert "_ezFetch(_ymSel)" in index_html, "EZ-Flags werden nicht via _ezFetch geladen"
    assert "_ezEffTage(days,ezFlags,_myWid," in index_html, "EZ nicht ueber _ezEffTage berechnet"
    assert "_ezAbsSet(abs||{},approvals,_myName)" in index_html, "v783-Abwesenheits-Ausschluss (_ezAbsSet) fehlt"
    assert "_ezSaetze(_kvR)" in index_html, "EZ-Saetze nicht ueber _ezSaetze(kv) bezogen"
    # kv aus der globalen Quelle (window.KV_RULES), wie KVZulagenReport.
    assert "window.KV_RULES)?window.KV_RULES:" in index_html, "kv-Quelle weicht vom Bestand ab"


def test_monatssumme_block_und_nav(index_html):
    assert "Meine Monatssumme" in index_html, "Eigene-Monatssumme-Karte fehlt"
    assert "_mySummary&&_mySummary.ist>0" in index_html, "Monatssumme-Gate (nur mit eigenen Stunden) fehlt"
    # Monats-Navigation Vor/Zurueck (Jahr-Rollover).
    assert "if(m<0){m=11;y--;}setSelMonat(m);setSelJahr(y);" in index_html, "Monat-Zurueck-Navigation fehlt"
    assert "if(m>11){m=0;y++;}setSelMonat(m);setSelJahr(y);" in index_html, "Monat-Vor-Navigation fehlt"


def test_kein_juprowa(index_html):
    # Die neue Sektion darf keinen Juprowa/Push-Bezug haben (reine Lese-/Anzeige-Sicht).
    a = index_html.index("Monteur-Eigensicht: EZ-Flags des Monats")
    b = index_html.index("_myName]);", a) + len("_myName]);")  # nur mein State-/EZ-Block, nicht die bestehenden setFink*-Writes
    block = index_html[a:b]
    assert "juprowa" not in block.lower(), "Monatssummen-Sektion darf keinen Juprowa-Bezug haben"
    assert "SQ.push" not in block, "Monatssummen-Sektion schreibt (SQ.push) — darf reine Anzeige sein"
