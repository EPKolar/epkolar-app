"""
Bug-Hunt-Fix v3.9.832 — Checklisten-Reload-Merge (Datenverlust-Schutz).

Checklisten waren die EINZIGE Kollektion ohne Pending-Schutz im Boot-Merge: der
chkl-Consumer war ein Voll-Overwrite aus dem Server. Eine frisch angelegte, noch
nicht gedrainte Checkliste (SQ-POST /api/checklists) verschwand beim nächsten
loadAll aus der UI. Fix: Merge wie entries (v491) / AS (v544) — pending
POST/PUT/DELETE über den SQ-Scan schützen.
"""
import re


def test_pending_sets_deklariert(index_html):
    for s in ("_v832PendingChklPosts", "_v832PendingChklPuts", "_v832PendingChklDeletes"):
        assert "let " + s + "=new Set();" in index_html, f"{s} nicht deklariert"


def test_sq_scan_erfasst_checklisten(index_html):
    assert '_u==="/api/checklists"&&_m==="POST"&&it.body&&it.body.id) _v832PendingChklPosts.add(it.body.id)' in index_html, "POST-Scan fehlt"
    assert '_u.startsWith("/api/checklists/")&&_m==="PUT"' in index_html, "PUT-Scan fehlt"
    assert '_u.startsWith("/api/checklists/")&&_m==="DELETE"' in index_html, "DELETE-Scan fehlt"
    # PUT/DELETE dekodieren die encodeURIComponent-URL
    assert index_html.count('_v832PendingChklPuts.add(_id)') == 1


def test_consumer_merged_statt_overwrite(index_html):
    # der Boot-Consumer darf kein reiner Voll-Overwrite mehr sein
    assert "const _localPending=_prevCl.filter(c=>!_srvIds.has(c.id)&&_v832PendingChklPosts.has(c.id));" in index_html, (
        "lokal-pending POSTs werden nicht erhalten"
    )
    assert "chkl.filter(c=>!_v832PendingChklDeletes.has(c.id))" in index_html, "pending DELETEs werden nicht gefiltert"
    assert "_v832PendingChklPuts.has(c.id)&&_prevById.has(c.id)" in index_html, "pending PUTs behalten die lokale Version nicht"


def test_kundenportal_pfad_bleibt_overwrite(index_html):
    """Der anonyme Kundenportal-Checklisten-Load (kein eingeloggter Pending-State)
    bleibt bewusst Voll-Overwrite — nicht versehentlich mitgemergt."""
    # der Kundenportal-Load nutzt keinen Pending-Merge (kein _v832 in seiner Nähe)
    i = index_html.find('[kundenportal] data load')
    assert i != -1
    portal_block = index_html[max(0, i - 900):i]
    assert "_v832PendingChkl" not in portal_block, (
        "Kundenportal-Pfad wurde faelschlich mit dem Boot-Merge vermischt"
    )
