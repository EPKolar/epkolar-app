"""
v3.9.858 — Werkzeug-Foto nutzt den gehärteten Foto-Pfad (Fotos/Storage-Agent, P1 SQ-Wedge).

Vorher las `uploadWzPhoto` (:28254) die Datei ROH (readAsDataURL, kein compressPhoto)
und pushte die Multi-MB-Base64 in die HAUPT-SQ (POST /api/photos/werkzeug/<id> umging
die Storage-Interception → rohe Base64 in photos.data_url). Auf flakem Mobilfunk →
'Failed to fetch' → in doSync transient → break → das überfüllte Item wedgte die GANZE
SQ. Fix: compressPhoto + captureAndQueue (Storage-first, isolierte PhotoQ) wie alle
anderen Fotos.
"""


def test_kein_roher_base64_in_haupt_sq(index_html):
    # der alte rohe readAsDataURL->SQ.push-Pfad ist weg
    assert 'SQ.push({url:"/api/photos/werkzeug/"+editId,method:"POST"' not in index_html
    assert "reader.readAsDataURL(f)" not in index_html or "uploadWzPhoto" not in index_html.split("reader.readAsDataURL(f)")[0][-400:]


def test_werkzeug_foto_nutzt_captureAndQueue(index_html):
    assert 'await captureAndQueue(f,"werkzeug",editId,"","Werkzeug-Foto");' in index_html
    # komprimiert vor dem Enqueue (kleiner Vorschau-Thumbnail lokal)
    assert "const ph=await compressPhoto(f,2000,0.85);" in index_html
    # PhotoQ-Flush wird angestossen
    assert "try{PhotoQ.flush();}catch(_f)" in index_html


def test_werkzeug_foto_read_matcht_entity(index_html):
    # Gegenprobe: Werkzeug-Fotos werden ueber entity_type=werkzeug gelesen -> captureAndQueue schreibt genau das
    assert '_sbGet("photos","entity_type=eq.werkzeug&entity_id=eq.' in index_html
