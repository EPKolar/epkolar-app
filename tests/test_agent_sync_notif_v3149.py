"""v3.9.149 — Agententeam-Welle-2: Sync 408/429 + Retry-Count + Notif deadline_fz."""


def test_sync_408_429_transient(index_html):
    assert "const _transient=!navigator.onLine||_st>=500||_st===408||_st===429||e.message==='Failed to fetch';" in index_html


def test_retry_count_persists_with_sibling_drop(index_html):
    assert 'if(fail>0){await SQ._serial(async()=>{const q=await ODB.load("syncQueue")||[];' in index_html
    assert "if(fail>0&&skipIds.length===0){await SQ._serial" not in index_html


def test_notif_deadline_fz_navigates(index_html):
    assert 'const _typeTab={deadline_fz:"fahrzeuge"};' in index_html
    assert "const _tgt=n.link||_typeTab[n.type]||((NOTIF_TYPES[n.type]||{}).cat&&_catTab[(NOTIF_TYPES[n.type]||{}).cat]);" in index_html
