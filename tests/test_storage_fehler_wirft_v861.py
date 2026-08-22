"""
v3.9.861 — Storage-Upload-Fehler wirft, statt mit Multi-MB-Base64 weiter-zu-inserten
(Fotos/Storage-Agent, P1 SQ-Wedge/stiller-Drop).

Die Storage-Interception (:2687) lädt file_data (Plan/Dokument/Attest) nach Storage
und löscht die Base64 aus dem Body. Schlug der Upload fehl, schluckte der catch
(:2704) den Fehler und fuhr mit `_sbInsertIfAbsent` fort — mit der kompletten
Multi-MB-Base64 im Body → (a) 20-MB-Row-POST → Failed to fetch → Queue-Wedge, oder
(b) 400 → stiller Drop nach 5 Retries. Fix: den Storage-Fehler werfen.
"""


def test_catch_wirft_statt_schlucken(index_html):
    # der alte schluckende catch ist weg
    assert 'catch(storageErr){console.warn("[api] Storage upload failed, keeping file_data in DB:",storageErr);}' not in index_html
    # jetzt wird der Fehler propagiert (kein DB-Insert mit rohem file_data)
    assert 'throw storageErr;}' in index_html
    assert '[api] Storage upload failed, propagating (kein DB-Insert mit rohem file_data)' in index_html


def test_intention_dont_store_base64(index_html):
    # Gegenprobe: die Absicht "Base64 nicht in die DB" bleibt (delete file_data im Erfolgsfall)
    assert "delete mapped.file_data; // Don't store base64 in DB" in index_html
