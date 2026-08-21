"""
Bug-Hunt-Fix v3.9.842 — Werkzeuge-Reload-Merge (Datenverlust-Schutz).

Der Werkzeuge-Boot-Consumer war Voll-Overwrite: ein frisch angelegtes Werkzeug
(SQ-POST /api/werkzeuge, Form hat id:uid()) verschwand beim Reload; ungedrainte
PUTs/DELETEs sprangen zurück. Fix wie Checklisten (v832) / Forms (v833).
"""


def test_pending_sets_deklariert(index_html):
    for s in ("_v842PendingWzgPosts", "_v842PendingWzgPuts", "_v842PendingWzgDeletes"):
        assert "let " + s + "=new Set();" in index_html, f"{s} fehlt"


def test_sq_scan_erfasst_werkzeuge(index_html):
    assert '_u==="/api/werkzeuge"&&_m==="POST"&&it.body&&it.body.id) _v842PendingWzgPosts.add(it.body.id)' in index_html
    assert '_u.startsWith("/api/werkzeuge/")&&_m==="PUT"' in index_html
    assert '_u.startsWith("/api/werkzeuge/")&&_m==="DELETE"' in index_html


def test_consumer_merged(index_html):
    assert "const _localPending=(prev||[]).filter(w=>w&&w.id&&!_srvIds.has(w.id)&&_v842PendingWzgPosts.has(w.id));" in index_html
    assert "wzg.filter(w=>!_v842PendingWzgDeletes.has(w.id))" in index_html
    assert "_v842PendingWzgPuts.has(w.id)&&_prevById.has(w.id)" in index_html


def test_kein_voll_overwrite_mehr(index_html):
    # der alte Voll-Overwrite-Einzeiler darf nicht mehr da sein
    assert "if(_optionalChain([wzg, 'optionalAccess', _48 => _48.length])) setWerkzeuge(wzg.map(_mapWerkzeug));" not in index_html
