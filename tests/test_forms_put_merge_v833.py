"""
Bug-Hunt-Fix v3.9.833 — Forms-Reload-Merge: Pending-PUT-Schutz.

Der Forms-Merge schützte pending POST/DELETE, aber NICHT PUT: ein editiertes,
noch nicht gedraintes Formular (SF/DH/AH/Abnahme/Regie) wurde beim Reload von der
Server-Altversion überschrieben und sprang in der UI zurück. Fix wie entries
(v598) / AS (v544): pending-PUT-ids behalten die lokale optimistische Version.
"""


def test_pending_form_puts_deklariert(index_html):
    assert "let _v833PendingFormPuts=new Set();" in index_html, "_v833PendingFormPuts nicht deklariert"


def test_sq_scan_erfasst_form_put(index_html):
    assert 'else if(_u.startsWith("/api/forms/")&&_m==="PUT"){const _id=_u.split("/").pop();if(_id) _v833PendingFormPuts.add(_id);}' in index_html, (
        "Forms-PUT-Scan fehlt"
    )


def test_merge_behaelt_lokale_version_bei_pending_put(index_html):
    assert "(_v833PendingFormPuts.has(x.id)&&_prevById.has(x.id))?_prevById.get(x.id):x" in index_html, (
        "Kategorie-Merge behält bei pending PUT nicht die lokale Version"
    )
    # prevById wird im Merge aufgebaut
    assert "const _prevById=new Map((prev[cat]||[]).map(x=>[x&&x.id,x]));" in index_html


def test_post_delete_schutz_bleibt(index_html):
    # der bestehende POST/DELETE-Schutz darf nicht verloren gehen
    assert "!_v496PendingFormDeletes.has(x.id)" in index_html
    assert "_v496PendingFormPosts.has(x.id)" in index_html
