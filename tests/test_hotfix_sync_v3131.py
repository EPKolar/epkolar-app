"""v3.9.131 — Hotfix: Sync-Banner steckt am Handy + #310-Diagnose + Teilzeit-no-op."""


def test_http_status_in_throws(index_html):
    # Diagnose: alle non-auth Throws tragen den HTTP-Status
    assert 'throw new Error("HTTP"+r.status+" "+e);' in index_html
    # v3.9.187: +1 durch _sbDeleteWhere (Projekt-Lösch-Kaskade) → 8
    assert index_html.count('throw new Error("HTTP"+r.status+" "+e);') == 8


def test_sync_transient_vs_permanent(index_html):
    # Banner-steckt-Fix: nur transiente Fehler behalten die Queue; 4xx/online-TypeError droppen nach Retries
    # v3.9.149: 408/429 ergänzt (retrybar)
    assert 'const _transient=!navigator.onLine||_st>=500||_st===408||_st===429||e.message===' in index_html
    assert "if(_transient){fail++;break;}" in index_html
    # die alte "jeder TypeError = network = break"-Logik ist weg
    assert "const isNetwork=!navigator.onLine||e.message==='Failed to fetch'||e.name==='TypeError';" not in index_html


def test_failed_banner_dismiss_button(index_html):
    # Banner verschwindet: "Verwerfen" leert syncQueueFailed
    assert 'const _clearFailed=async()=>{try{await ODB.save("syncQueueFailed",[]);}catch(_e){}setFailedCount(0);' in index_html
    assert '"✕ Verwerfen"' in index_html


def test_sync_drop_diagnostic_log(index_html):
    assert '"[sq] DROP nach 5 Fehlversuchen:"' in index_html
    assert "_bodyKeys:_bodyKeys" in index_html
