"""
Nachtlauf-Hunt v3.9.851 — KundenPortal stellt beim Unmount den Haupt-doSync wieder her.

Sync-Agent-Fund P3 (Liveness): `KundenPortal` überschrieb `window.__doSync=_portalSync`
und machte beim Unmount `delete window.__doSync` (:6219) statt den verdrängten
Haupt-doSync wiederherzustellen. Da React den Parent-Render (:8381) VOR dem
Child-Cleanup ausführt, blieb `window.__doSync` nach dem Schließen des Kundenportals
gelöscht → der 1,5s-SQ-Auto-Batch (:3186) + SYNC_TRIGGER No-Op bis zum nächsten
Render/Focus. Fix: beim Mount merken, im Cleanup guarded zurücksetzen.
"""


def test_kein_nacktes_delete_mehr(index_html):
    assert "return()=>{active=false;delete window.__doSync;};" not in index_html


def test_prev_dosync_gemerkt_und_guarded_restore(index_html):
    assert "const _prevDoSync=window.__doSync;" in index_html
    assert "if(window.__doSync===_portalSync)window.__doSync=_prevDoSync;" in index_html
