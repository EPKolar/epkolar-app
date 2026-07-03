"""v3.9.648 KV-V2 — kontingent.urlaub (Tage) sanft stillgelegt.

Resturlaub laeuft ausschliesslich in Stunden (_resturlaubK). Save serialisiert das
Feld nicht mehr, Load uebernimmt es nicht mehr; DB-Spalte bleibt (kein DDL).
Das lebendige Verbrauchs-Aggregat (_absStats.urlaub / yearSt-urlaubStd*) bleibt.
"""


def test_save_payload_ohne_urlaub(index_html):
    # Der urlaubskontingent-POST-Body serialisiert kontingent.urlaub NICHT mehr
    assert "urlaub:ks.urlaub" not in index_html


def test_load_uebernimmt_kein_urlaub(index_html):
    # Load-Map liest k.urlaub nicht mehr -> Row ohne Spalte crasht nicht
    assert "urlaub:parseInt(k.urlaub)" not in index_html


def test_deprecation_kommentar(index_html):
    assert "urlaub-Spalte DEPRECATED seit v3.9.647" in index_html


def test_resturlaub_nutzt_stunden(index_html):
    # Einzige Wahrheit: _resturlaubK rechnet mit ks.stunden + vorjahr - Verbrauch
    assert "function _resturlaubK(abs,approvals,kontingent,m,yr){" in index_html
    assert "(ks.stunden||192.5)+(ks.vorjahr||0)-ys.urlaubStdGen" in index_html


def test_lebendiges_aggregat_unangetastet(index_html):
    # _absStats.urlaub (Verbrauchs-Tage aus absences) bleibt erhalten
    assert "s.urlaub+=dayUnit" in index_html
    assert "urlaubStdGen" in index_html
