"""
v3.9.862 — Checklisten-Owner-Delete-Gate nach Reload (Checklisten-Agent P2, wie v845).

`_vcIsMineCl` (:15727) verglich den Ersteller-NAMEN `c.by`; der wird aber nie
persistiert (POST sendet `created_by`=monteur_id, Load :7926/:6214 ließ `by` UND
`created_by` fallen) → nach Reload `c.by` undefined → Gate false → Monteure konnten
eigene Checklisten NICHT löschen. Fix: created_by durchreichen + Gate auf
created_by===monteurId (wie v845 Forms).
"""


def test_load_reicht_created_by_durch(index_html):
    # beide Checklisten-Load-Pfade tragen jetzt created_by
    assert index_html.count(',status:c.status||"offen",created_by:c.created_by') == 2


def test_gate_vergleicht_created_by(index_html):
    assert "return!!(c&&c.created_by&&curUser&&curUser.monteurId&&c.created_by===curUser.monteurId);" in index_html
    # die alte Namensvergleich-Logik ist weg
    assert "return!!(_by&&_vcMyName&&_by===_vcMyName);" not in index_html


def test_lokale_objekte_tragen_created_by(index_html):
    # createFromTemplate + createCustom setzen created_by lokal (In-Session-Gate)
    assert index_html.count(',status:"offen",created_by:(curUser&&curUser.monteurId)||""};') == 2
