"""v3.9.151 — OFFA-Import-Dedupe case-insensitiv (Agent-Fund).

v3.9.780: Der manuelle OFFA-PDF-Import (importOffa) wurde als toter Code entfernt
(v698-Muster). Der case-insensitive Dedupe-Check lebte in genau diesem Handler und
ist damit weg. Removal-Pin statt Presence-Pin.
"""


def test_offa_dedupe_removed_v780(index_html):
    assert 'const existing=arbeitsscheine.find(a=>(a.nummer||"").toUpperCase()===(parsed.nummer||"").toUpperCase());' not in index_html, (
        "v3.9.780: OFFA-Import-Dedupe-Check gehoerte zum entfernten importOffa-Handler"
    )
    # Die alte case-sensitive Variante darf ebenfalls nicht (wieder) auftauchen.
    assert "const existing=arbeitsscheine.find(a=>a.nummer===parsed.nummer);" not in index_html
