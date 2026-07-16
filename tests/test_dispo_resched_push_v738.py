# -*- coding: utf-8 -*-
"""Regressions-Guard: Reschedule (fixen Termin verschieben) pusht Datum+Zeit+Dauer zu OFFA.

Sebastian: "wenn termine in der dispo verschoben werden muss der AS aktualisiert werden mit datum zeit
und dauer und auch ein push ausgeloest werden zu offa." Review (16.07.) belegte: das ist bereits erfuellt.
onReschedule schreibt terminBestaetigt (Datum) via updAs; terminBestaetigt ist ein JUPROWA_PUSH_FIELD ->
updAs setzt push_pending -> _juprowaPush laedt den Schein FRISCH und baut einen VOLL-ROW-Payload (kein
Diff) -> AK_TERMIN (Datum+terminZeit) + AK_DAUER reiten automatisch mit. Ein explizites Nachschreiben von
dauer waere sogar riskant (Dispo HH:MM vs. Formular-Dezimal). Dieser Guard sichert die Push-Kette ab.
"""


def test_reschedule_schreibt_via_updAs_terminBestaetigt(index_html):
    i = index_html.index("onReschedule:")
    seg = index_html[i:i + 260]
    assert "updAs(" in seg and "terminBestaetigt" in seg, "Reschedule schreibt nicht terminBestaetigt via updAs"
    assert "SQ.push" not in seg, "Reschedule darf keinen eigenen SQ.push-Sonderpfad haben"


def test_terminBestaetigt_und_dauer_sind_push_felder(index_html):
    start = index_html.index("const JUPROWA_PUSH_FIELDS={")
    end = index_html.index("}", start)
    block = index_html[start:end]
    assert "terminBestaetigt:" in block, "terminBestaetigt ist kein Push-Feld -> Reschedule wuerde nicht pushen"
    assert "dauer:" in block, "dauer ist kein Push-Feld"


def test_juprowapush_baut_vollrow_aus_frischem_schein(index_html):
    # _juprowaPush laedt den Schein frisch (_sbGet) und baut den Payload voll -> AK_TERMIN kombiniert Datum+Zeit.
    assert "json.AK_TERMIN=schein.terminBestaetigt" in index_html, "AK_TERMIN kombiniert Datum+Zeit nicht (Voll-Row-Push)"
