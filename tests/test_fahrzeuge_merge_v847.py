"""
Nachtlauf-Hunt v3.9.847 — Fahrzeug-Reload-Merge (Datenverlust-Schutz).

Gleiche Klasse wie Werkzeuge v842 / Checklisten v832 / Forms v833: der Fahrzeug-
Boot-Consumer (:7863) war Voll-Overwrite OHNE Pending-Schutz. Ein noch nicht
gedrainter PUT (km/Tank/Schaden via upd()+qDoTank, /api/fahrzeuge/<id>) sprang
beim nächsten (Hintergrund-)loadAll auf den Serverstand zurück; ein frisch
angelegtes Fahrzeug (POST /api/fahrzeuge) verschwand.
"""


def test_pending_sets_deklariert(index_html):
    for s in ("_v847PendingFzgPosts", "_v847PendingFzgPuts", "_v847PendingFzgDeletes"):
        assert "let " + s + "=new Set();" in index_html, f"{s} fehlt"


def test_sq_scan_erfasst_fahrzeuge(index_html):
    assert '_u==="/api/fahrzeuge"&&_m==="POST"&&it.body&&it.body.id) _v847PendingFzgPosts.add(it.body.id)' in index_html
    assert '_u.startsWith("/api/fahrzeuge/")&&_m==="PUT"' in index_html
    assert '_u.startsWith("/api/fahrzeuge/")&&_m==="DELETE"' in index_html


def test_consumer_merged(index_html):
    assert "const _localPending=(prev||[]).filter(f=>f&&f.id&&!_srvIds.has(f.id)&&_v847PendingFzgPosts.has(f.id));" in index_html
    assert "fzg.filter(f=>!_v847PendingFzgDeletes.has(f.id))" in index_html
    assert "_v847PendingFzgPuts.has(f.id)&&_prevById.has(f.id)" in index_html
    # ODB-Cache speichert das gemergte Ergebnis (nicht den rohen Serverstand)
    assert 'ODB.save("fahrzeuge",_merged)' in index_html


def test_kein_voll_overwrite_mehr(index_html):
    # der alte Voll-Overwrite-Einzeiler darf nicht mehr da sein
    assert 'setFahrzeuge(fzg.map(_mapFahrzeug));ODB.save("fahrzeuge",fzg.map(_mapFahrzeug));' not in index_html
