"""Regression-Tests fuer v3.9.345 VBueroExport-Bauwochenbericht-Matrix:
  - Title-Rename 'Vorschau:' → 'Bauwochenbericht:' im Preview-Modal-Header.
  - Matrix-Stundenzellen direkt editierbar (canDo zeit_other; inputMode=decimal).
  - 0 Entries → SQ.push POST /api/entries (INSERT-Branch).
  - 1 Entry  → SQ.push PUT /api/entries/{id} (UPDATE-Branch).
  - ≥2 Entries → readonly Summe + ⓘ-Indicator (Mini-Liste via openMultiEntryEdit).
  - setTimeout(loadAll(true),1000) im Matrix-Save-Pfad (konsistent v3.9.342).
  - generateBWB UNVERAENDERT (editTaet[kwKey]-Fallback bleibt).
  - KW-Taetigkeit-rowSpan:7-Textarea unverändert.
  - Version-Sync auf 3.9.345.
"""
import re


def _vbuero_block(index_html):
    start_m = re.search(r"function\s+VBueroExport\s*\(", index_html)
    assert start_m, "VBueroExport-Funktion nicht gefunden"
    end_m = re.search(r"\nfunction\s+V[A-Z]\w*\s*\(", index_html[start_m.end():])
    assert end_m, "Naechste V-Funktion nach VBueroExport nicht gefunden"
    return index_html[start_m.start(): start_m.end() + end_m.start()]


def _save_matrix_block(index_html):
    m = re.search(
        r"const\s+saveMatrixCell\s*=[\s\S]+?\n  \};",
        index_html,
    )
    assert m, "saveMatrixCell-Block nicht gefunden"
    return m.group(0)


# 1) Title-Rename --------------------------------------------------------------

def test_preview_header_says_bauwochenbericht(index_html):
    """Der h3-Modal-Header in renderPreview muss 'Bauwochenbericht: ' statt
    'Vorschau: ' zeigen."""
    block = _vbuero_block(index_html)
    # Wir suchen den h3-Header mit fontWeight:800 und Title-String.
    m = re.search(
        r"createElement\(\s*['\"]h3['\"][^)]*fontWeight\s*:\s*800[^)]*\}\s*\}\s*,\s*['\"]([^'\"]*?)['\"]",
        block,
    )
    assert m, "h3-Modal-Header nicht gefunden"
    title = m.group(1)
    assert "Bauwochenbericht" in title, (
        f"h3-Modal-Header enthaelt 'Bauwochenbericht' nicht — aktuell: {title!r}"
    )
    assert "Vorschau" not in title, (
        f"h3-Modal-Header enthaelt noch 'Vorschau' — Title-Rename unvollstaendig: {title!r}"
    )


# 2) inputMode='decimal' am Matrix-Input ---------------------------------------

def test_matrix_cell_has_inputmode_decimal(index_html):
    """Die editierbare Matrix-Zelle muss ein input mit inputMode='decimal' rendern."""
    block = _vbuero_block(index_html)
    assert re.search(
        r"inputMode\s*:\s*['\"]decimal['\"]",
        block,
    ), "inputMode 'decimal' fehlt in VBueroExport — Matrix-Input nicht editable."


# 3) Render-Gate canDo('zeit_other', curUser) am Matrix-Input -------------------

def test_matrix_cell_canDo_zeit_other_gate(index_html):
    """Das Render des Matrix-Inputs muss durch canDo('zeit_other', curUser) gegated
    sein — Nicht-Berechtigte sehen die alte readonly-Zelle."""
    block = _vbuero_block(index_html)
    # canDo('zeit_other',curUser) muss im VBueroExport-Block vorkommen
    assert re.search(
        r"canDo\(\s*['\"]zeit_other['\"]\s*,\s*curUser\s*\)",
        block,
    ), "canDo('zeit_other',curUser) fehlt im VBueroExport-Block — Render-Gate fehlt."


# 4) SQ.push PUT /api/entries/ im Matrix-Save-Pfad -----------------------------

def test_save_matrix_cell_puts_to_entries(index_html):
    """Der saveMatrixCell-Block muss ein SQ.push PUT auf /api/entries/ enthalten
    (Single-Entry-Update-Pfad)."""
    block = _save_matrix_block(index_html)
    assert re.search(
        r'SQ\.push\(\s*\{\s*url\s*:\s*["\']/api/entries/["\']?\s*\+\s*ent\.id\s*,\s*method\s*:\s*["\']PUT["\']',
        block,
    ), "PUT /api/entries/{id} fehlt im saveMatrixCell-Pfad — Single-Entry-Update fehlt."


def test_save_matrix_cell_put_body_has_hours(index_html):
    """Der PUT-Body muss hours (+ Mirror stunden) als Key haben — Schema kann beides."""
    block = _save_matrix_block(index_html)
    m = re.search(
        r'method\s*:\s*["\']PUT["\']\s*,\s*body\s*:\s*\{[^}]+\}',
        block,
    )
    assert m, "PUT-Body-Block nicht gefunden im saveMatrixCell"
    body = m.group(0)
    assert "hours" in body, "PUT-Body enthaelt 'hours' nicht — Mirror-Schreib fehlt."


# 5) SQ.push POST /api/entries fuer 0-Entries-INSERT ---------------------------

def test_save_matrix_cell_posts_for_zero_entries(index_html):
    """0 Entries + Wert > 0 → SQ.push POST /api/entries (Insert)."""
    block = _save_matrix_block(index_html)
    assert re.search(
        r'SQ\.push\(\s*\{\s*url\s*:\s*["\']/api/entries["\']\s*,\s*method\s*:\s*["\']POST["\']',
        block,
    ), "POST /api/entries fehlt im saveMatrixCell-Pfad — 0-Entries-INSERT fehlt."


def test_save_matrix_cell_post_body_has_required(index_html):
    """Der POST-Body muss worker_id, project_id, date, hours, taetigkeit, gewerk enthalten."""
    block = _save_matrix_block(index_html)
    m = re.search(
        r'method\s*:\s*["\']POST["\']\s*,\s*body\s*:\s*\{[^}]+\}',
        block,
    )
    assert m, "POST-Body-Block nicht gefunden im saveMatrixCell"
    body = m.group(0)
    for key in ("worker_id", "project_id", "date", "hours", "taetigkeit", "gewerk"):
        assert key in body, f"POST-Body fehlt Key '{key}' — Regression v3.9.345."


# 6) ≥2 Entries → readonly + ⓘ-Indicator ---------------------------------------

def test_multi_entry_cell_has_info_indicator(index_html):
    """Wenn cellEntries.length>=2 muss die Zelle einen 'ⓘ' (oder data-multi-entry)
    Sentinel zeigen — readonly, klickbar fuer Mini-Liste."""
    block = _vbuero_block(index_html)
    # Sentinel-String 'ⓘ' oder data-multi-entry
    assert ('"data-multi-entry"' in block) or ("ⓘ" in block), (
        "≥2-Entries-Sentinel (ⓘ / data-multi-entry) fehlt — Multi-Entry-Branch nicht implementiert."
    )


def test_open_multi_entry_edit_function_present(index_html):
    """Die openMultiEntryEdit-Funktion (Mini-Liste fuer ≥2-Entries) muss existieren
    und ueber _exportReviewModal arbeiten."""
    block = _vbuero_block(index_html)
    assert re.search(
        r"const\s+openMultiEntryEdit\s*=",
        block,
    ), "openMultiEntryEdit-Funktion fehlt in VBueroExport — Mini-Liste-Branch nicht implementiert."
    assert "_exportReviewModal" in block, (
        "_exportReviewModal-Aufruf fehlt in VBueroExport-Block — Mini-Liste nicht via Modal."
    )


# 7) Refresh nach Matrix-Save: drain-then-reload (v3.9.364) --------------------

def test_save_matrix_cell_sync_then_reload(index_html):
    """v3.9.364: Nach SQ.push muss _syncThenReload() stehen (erst SQ-Queue drainen,
    DANN loadAll) statt des alten blinden setTimeout(loadAll,1000), der den
    optimistischen Wert mit noch-altem DB-Stand überschrieb (State-nach-Write-Bug)."""
    block = _save_matrix_block(index_html)
    assert "_syncThenReload()" in block, (
        "saveMatrixCell ruft kein _syncThenReload() — Refresh-Automatik fehlt."
    )
    # der alte race-anfällige blinde Reload darf nicht mehr im Save-Pfad stehen
    assert not re.search(r"setTimeout\(\s*(?:\(\s*\)|_)\s*=>\s*loadAll\(\s*true\s*\)\s*,\s*1000\s*\)", block), (
        "alter setTimeout(loadAll,1000)-Race noch im saveMatrixCell-Pfad."
    )


def test_sync_then_reload_drains_before_reload(index_html):
    """_syncThenReload muss erst __doSync/SQ.count drainen, dann loadAll(true)."""
    m = re.search(r"const _syncThenReload=async\(\)=>\{([\s\S]{0,600}?)\n  \};", index_html)
    assert m, "_syncThenReload-Helfer fehlt"
    body = m.group(1)
    assert "window.__doSync" in body, "drainet nicht via __doSync"
    assert "SQ.count()" in body, "wartet nicht auf leere Queue (SQ.count)"
    assert "loadAll(true)" in body, "lädt am Ende nicht neu"


# 8) generateBWB unveraendert (editTaet[kwKey]-Fallback bleibt) ----------------

def test_generateBWB_editTaet_fallback_unchanged(index_html):
    """Anker auf das editTaet-Fallback-Pattern in generateBWB.
    v3.9.362: editTaet ist jetzt projekt-skopiert (proj.id+"|"+kwKey) — der
    useFilters-Fallback auf BT/Entries-Tätigkeit bleibt erhalten."""
    # Zwei Stellen: KW-Sheet + Summenblatt. Mind. eine Anker-Stelle pruefen.
    assert 'useFilters&&editTaet[proj.id+"|"+kwKey]!==undefined?editTaet[proj.id+"|"+kwKey]' in index_html, (
        "generateBWB editTaet-Fallback (projekt-skopiert) wurde geaendert — Excel-Generator-Regression."
    )


def test_generateBWB_signature_unchanged(index_html):
    """Anker auf die generateBWB-Signatur und Header-Konstante CF_HTML_NAME."""
    assert "const generateBWB=(proj,useFilters)=>{" in index_html, (
        "generateBWB-Signatur wurde geaendert — v3.9.345 darf Generator NICHT anfassen."
    )


# 9) KW-Tätigkeit rowSpan:7 Textarea unverändert -------------------------------

def test_kw_taetigkeit_textarea_rowspan7_unchanged(index_html):
    """Anker auf rowSpan:7 + Textarea mit setEditTaet onChange — bleibt unveraendert."""
    block = _vbuero_block(index_html)
    assert "rowSpan: 7" in block, (
        "KW-Taetigkeit-Textarea rowSpan:7 fehlt — Anker-Regression v3.9.345."
    )
    # Die Textarea mit setEditTaet onChange muss vorhanden sein.
    assert re.search(
        r"createElement\(\s*['\"]textarea['\"][^)]*setEditTaet",
        block,
    ), "KW-Taetigkeit-Textarea mit setEditTaet-onChange fehlt — Regression v3.9.345."


# 10) editMonteurEntries-Modal UNVERAENDERT ------------------------------------

def test_edit_monteur_entries_unchanged_put_anchor(index_html):
    """Der bestehende PUT-Save-Pfad im editMonteurEntries-Modal (v3.9.337/341/344)
    bleibt unveraendert."""
    expected = (
        'SQ.push({url:"/api/entries/"+r.id,method:"PUT",'
        'body:{date:r.datum,taetigkeit:r.taetigkeit,hours:r.stunden,bemerkung:r.bemerkung}});'
    )
    assert expected in index_html, (
        "editMonteurEntries-PUT-Save-Anker veraendert — Regression v3.9.345 darf "
        "die ✏️-Monteur-Liste NICHT anfassen."
    )


# 11) Version-Sync -------------------------------------------------------------

def test_app_version_345(app_version):
    """Forward-Guard: APP_VERSION mindestens 3.9.345 (Matrix-Edit-Floor)."""
    import re
    m = re.match(r"3\.9\.(\d+)-supabase", app_version)
    assert m and int(m.group(1)) >= 345, (
        f"APP_VERSION unter 3.9.345 — aktuell: {app_version}"
    )


def test_cache_name_345(cache_name):
    """Forward-Guard: CACHE_NAME mindestens 3.9.345."""
    import re
    m = re.match(r"epkolar-v3\.9\.(\d+)", cache_name)
    assert m and int(m.group(1)) >= 345, (
        f"CACHE_NAME unter 3.9.345 — aktuell: {cache_name}"
    )


def test_sw_ver_345(index_html):
    """Forward-Guard: SW_VER im IIFE mindestens 3.9.345."""
    import re
    m = re.search(r"SW_VER='epkolar-v3\.9\.(\d+)'", index_html)
    assert m and int(m.group(1)) >= 345, "SW_VER im IIFE unter 3.9.345."


def test_sw_header_345(sw_js):
    """Forward-Guard: SW-Header mindestens 3.9.345."""
    import re
    m = re.match(r"// EP Kolar Service Worker v3\.9\.(\d+)", sw_js)
    assert m and int(m.group(1)) >= 345, "SW-Header-Kommentar unter 3.9.345."
