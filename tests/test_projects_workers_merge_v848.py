"""
Nachtlauf-Hunt v3.9.848 — Reload-Merge vervollständigt (Projekte + Mitarbeiter).

Die letzten beiden editierbaren globalen Boot-Consumer waren noch Voll-Overwrite:
setProjects(:7795) + setMonteure(:7796). Gleiche Datenverlust-Klasse wie v847.
Projekte: POST /api/projects, PUT/DELETE /api/projects/<id> (häufige PUTs:
Status/Dispo/Details). Mitarbeiter: POST /api/workers + PUT /api/workers/<id>
(kein SQ-DELETE — delMonteur läuft server-seitig/fail-closed).
"""


def test_pending_sets_deklariert(index_html):
    for s in ("_v848PendingProjPosts", "_v848PendingProjPuts", "_v848PendingProjDeletes",
              "_v848PendingWorkerPosts", "_v848PendingWorkerPuts", "_v848PendingWorkerDeletes"):
        assert "let " + s + "=new Set();" in index_html, f"{s} fehlt"


def test_sq_scan_erfasst_projects_workers(index_html):
    assert '_u==="/api/projects"&&_m==="POST"&&it.body&&it.body.id) _v848PendingProjPosts.add(it.body.id)' in index_html
    assert '_u.startsWith("/api/projects/")&&_m==="PUT"' in index_html
    assert '_u.startsWith("/api/projects/")&&_m==="DELETE"' in index_html
    assert '_u==="/api/workers"&&_m==="POST"&&it.body&&it.body.id) _v848PendingWorkerPosts.add(it.body.id)' in index_html
    assert '_u.startsWith("/api/workers/")&&_m==="PUT"' in index_html


def test_projects_consumer_merged(index_html):
    assert 'setProjects(fzg.map' not in index_html
    assert 'setProjects(prj.map(_mapProject));' not in index_html
    assert "_v848PendingProjPuts.has(x.id)&&_prevById.has(x.id)" in index_html
    assert "prj.filter(x=>!_v848PendingProjDeletes.has(x.id))" in index_html
    assert "_localPending=(prev||[]).filter(x=>x&&x.id&&!_srvIds.has(x.id)&&_v848PendingProjPosts.has(x.id))" in index_html


def test_workers_consumer_merged(index_html):
    assert 'setMonteure(wk.map(_mapWorker));' not in index_html
    assert "wk.filter(x=>!_v848PendingWorkerDeletes.has(x.id))" in index_html
    assert "_v848PendingWorkerPuts.has(x.id)&&_prevById.has(x.id)" in index_html
    # der else-Zweig (Cache-Fallback-Hinweis v3.9.822) muss erhalten bleiben
    assert "der Cache bleibt Fallback" in index_html
