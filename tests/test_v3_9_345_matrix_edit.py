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


# 7) setTimeout(loadAll(true),1000) im Matrix-Save-Pfad ------------------------

def test_save_matrix_cell_settimeout_1000(index_html):
    """Nach SQ.push muss setTimeout(()=>loadAll(true),1000) stehen — konsistent
    mit v3.9.342 Refresh-Automatik."""
    block = _save_matrix_block(index_html)
    m = re.search(
        r"setTimeout\(\s*(?:\(\s*\)|_)\s*=>\s*loadAll\(\s*true\s*\)\s*,\s*1000\s*\)",
        block,
    )
    assert m, (
        "saveMatrixCell hat kein setTimeout(()=>loadAll(true),1000) — Refresh-Automatik fehlt."
    )


# 8) generateBWB unveraendert (editTaet[kwKey]-Fallback bleibt) ----------------

def test_generateBWB_editTaet_fallback_unchanged(index_html):
    """Anker auf das editTaet[kwKey]-Fallback-Pattern in generateBWB —
    DARF NICHT geaendert werden in v3.9.345."""
    # Zwei Stellen: KW-Sheet + Summenblatt. Mind. eine Anker-Stelle pruefen.
    assert "useFilters&&editTaet[kwKey]!==undefined?editTaet[kwKey]" in index_html, (
        "generateBWB editTaet[kwKey]-Fallback wurde geaendert — Excel-Generator-Regression."
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
    assert app_version == "3.9.345-supabase", (
        f"APP_VERSION nicht 3.9.345-supabase — aktuell: {app_version}"
    )


def test_cache_name_345(cache_name):
    assert cache_name == "epkolar-v3.9.345", (
        f"CACHE_NAME nicht epkolar-v3.9.345 — aktuell: {cache_name}"
    )


def test_sw_ver_345(index_html):
    assert "SW_VER='epkolar-v3.9.345'" in index_html, (
        "SW_VER im IIFE nicht epkolar-v3.9.345."
    )


def test_sw_header_345(sw_js):
    assert sw_js.startswith("// EP Kolar Service Worker v3.9.345"), (
        "SW-Header-Kommentar nicht v3.9.345."
    )
