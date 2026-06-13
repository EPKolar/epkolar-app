"""Regression-Tests fuer v3.9.344 Berichte-Bearbeiten-Modal:
  - '➕ Buchung hinzufügen'-Button im editMonteurEntries-Modal.
  - Neue Zeilen (_isNew/keine id) → SQ.push POST /api/entries mit worker_id=Monteur.
  - Projekt-Dropdown für neue Zeilen via selectOptionsFor (active projects).
  - Validierung: Stunden + Datum Pflicht — sonst Skip + Hinweis.
  - Split-Use-Case: PUT + POST in derselben forEach-Schleife.
  - Bestehende PUT-Save-Logik UNVERAENDERT.
  - Bestehende DELETE-Logik (✕-Button) UNVERAENDERT.
  - Hinweistext im dbWrite:true-Branch zeigt KEIN 'NUR im Export'.
"""
import re


# 1) '➕ Buchung hinzufügen'-Button-String im editMonteurEntries-Kontext --------

def test_add_buchung_button_label_in_edit_monteur_block(index_html):
    """In editMonteurEntries muss das Label '➕ Buchung hinzufügen' irgendwo im
    Aufruf-Block vorkommen (entweder addRow.label oder direkt als Button-Text)."""
    m_edit = re.search(
        r"const\s+editMonteurEntries\s*=[\s\S]{0,8000}?\}\s*;\s*/\*",
        index_html,
    )
    assert m_edit, "editMonteurEntries-Block nicht gefunden"
    block = m_edit.group(0)
    assert "➕ Buchung hinzufügen" in block, (
        "Button-Label '➕ Buchung hinzufügen' fehlt im editMonteurEntries-Block — "
        "Regression v3.9.344."
    )


def test_modal_addRow_option_rendered_as_button(index_html):
    """_exportReviewModal muss optional einen addRow-Button rendern wenn opts.addRow
    gesetzt ist (build()-Callback). Pattern: opts.addRow + addRow.build()."""
    # opts.addRow wird in der Modal-Body deklariert/extrahiert
    assert re.search(
        r"opts\.addRow",
        index_html,
    ), "opts.addRow fehlt im _exportReviewModal — addRow-Option nicht unterstützt."
    # build() wird aufgerufen
    assert re.search(
        r"addRow\.build\s*\(\s*\)",
        index_html,
    ), "addRow.build()-Aufruf fehlt — neuer Row wird nicht angelegt."


# 2) _isNew-Marker fuer neue Zeilen --------------------------------------------

def test_new_row_marker_isNew_used(index_html):
    """Neue Zeilen müssen ein _isNew-Marker tragen, damit der Save-Pfad sie als
    INSERT erkennt."""
    assert "_isNew" in index_html, (
        "_isNew-Marker fehlt — Save-Pfad kann neue Zeilen nicht von Updates unterscheiden."
    )


# 3) SQ.push mit method:"POST" + url:"/api/entries" im Save-Pfad ---------------

def test_save_path_posts_to_entries_for_new_rows(index_html):
    """Im editMonteurEntries-Save-Block muss ein POST /api/entries fuer neue Zeilen
    sein (worker_id = ms.id)."""
    m_edit = re.search(
        r"const\s+editMonteurEntries\s*=[\s\S]{0,8000}?\}\s*;\s*/\*",
        index_html,
    )
    assert m_edit, "editMonteurEntries-Block nicht gefunden"
    block = m_edit.group(0)
    # SQ.push mit POST + /api/entries
    assert re.search(
        r'SQ\.push\s*\(\s*\{\s*url\s*:\s*["\']/api/entries["\']\s*,\s*method\s*:\s*["\']POST["\']',
        block,
    ), "POST /api/entries fehlt im editMonteurEntries-Save-Pfad — Regression v3.9.344."


# 4) Body enthält worker_id + date + hours + taetigkeit ------------------------

def test_post_body_contains_required_fields(index_html):
    """Der POST-Body fuer neue Eintraege muss worker_id, date, hours und taetigkeit
    als Body-Keys haben (gleicher Shape wie ZeiterfassungView-POST)."""
    m_edit = re.search(
        r"const\s+editMonteurEntries\s*=[\s\S]{0,8000}?\}\s*;\s*/\*",
        index_html,
    )
    assert m_edit, "editMonteurEntries-Block nicht gefunden"
    block = m_edit.group(0)
    # Suche den POST-Block
    m_post = re.search(
        r'SQ\.push\s*\(\s*\{\s*url\s*:\s*["\']/api/entries["\']\s*,\s*method\s*:\s*["\']POST["\']\s*,\s*body\s*:\s*\{[^}]+\}',
        block,
    )
    assert m_post, "POST-Block fuer /api/entries nicht gefunden."
    body = m_post.group(0)
    for key in ("worker_id", "date", "hours", "taetigkeit"):
        assert key in body, (
            f"POST-Body fuer neuen Eintrag enthaelt nicht '{key}' — Regression v3.9.344."
        )


def test_post_uses_ms_id_as_worker(index_html):
    """worker_id muss ms.id sein (der editierte Monteur, nicht curUser)."""
    m_edit = re.search(
        r"const\s+editMonteurEntries\s*=[\s\S]{0,8000}?\}\s*;\s*/\*",
        index_html,
    )
    assert m_edit, "editMonteurEntries-Block nicht gefunden"
    block = m_edit.group(0)
    assert re.search(
        r'worker_id\s*:\s*ms\.id',
        block,
    ), "worker_id im POST-Body ist nicht ms.id — neue Buchung wuerde dem falschen Monteur zugeordnet."


# 5) Projekt-Dropdown fuer neue Zeilen -----------------------------------------

def test_projects_filter_for_dropdown(index_html):
    """Im editMonteurEntries-Block muss projects gefiltert/gemappt werden, um die
    aktive Projektliste fuer das Dropdown zu generieren."""
    m_edit = re.search(
        r"const\s+editMonteurEntries\s*=[\s\S]{0,8000}?\}\s*;\s*/\*",
        index_html,
    )
    assert m_edit, "editMonteurEntries-Block nicht gefunden"
    block = m_edit.group(0)
    # Entweder projects.filter oder activeProjects.map oder vergleichbares Pattern
    assert re.search(
        r"projects[\s\S]{0,40}\.filter\b",
        block,
    ) or re.search(
        r"activeProjects[\s\S]{0,40}\.map\b",
        block,
    ), "Projekt-Liste fuer Dropdown nicht abgeleitet — Regression v3.9.344."


def test_modal_renders_select_for_new_rows(index_html):
    """Modal muss ein <select>-Element fuer neue Zeilen rendern (Projekt-Wahl)."""
    # Pattern: createElement('select') in einem _isNew-Pfad
    assert re.search(
        r"createElement\(\s*['\"]select['\"]\s*\)",
        index_html,
    ), "<select>-Render fehlt im _exportReviewModal — Projekt-Dropdown nicht moeglich."


# 6) Validierung: Stunden + Datum Pflicht --------------------------------------

def test_skip_when_stunden_or_datum_missing(index_html):
    """Neue Zeile ohne Stunden oder Datum muss skip + Hinweis triggern."""
    m_edit = re.search(
        r"const\s+editMonteurEntries\s*=[\s\S]{0,8000}?\}\s*;\s*/\*",
        index_html,
    )
    assert m_edit, "editMonteurEntries-Block nicht gefunden"
    block = m_edit.group(0)
    # Skip-Pattern: !r.stunden || r.stunden<=0 || !r.datum (oder via parsed _h)
    # Akzeptiere: !r.datum oder !r.stunden Check in der Naehe vom POST
    assert re.search(
        r"!\s*r\.datum",
        block,
    ) or re.search(
        r"!\s*r\.stunden",
        block,
    ) or re.search(
        r"!\s*\(\s*_h\s*>\s*0\s*\)",
        block,
    ), "Validierung Stunden/Datum Pflicht fehlt im POST-Pfad — Regression v3.9.344."


def test_skip_toast_message_present(index_html):
    """Ein Toast-Hinweis 'Stunden + Datum sind Pflicht' (oder analog) muss
    bei skip getriggert werden."""
    m_edit = re.search(
        r"const\s+editMonteurEntries\s*=[\s\S]{0,8000}?\}\s*;\s*/\*",
        index_html,
    )
    assert m_edit, "editMonteurEntries-Block nicht gefunden"
    block = m_edit.group(0)
    assert ("Pflicht" in block) or ("übersprungen" in block), (
        "Skip-Hinweis (Pflicht/übersprungen) fehlt im editMonteurEntries-Block — "
        "Regression v3.9.344."
    )


# 7) Bestehende PUT-Logik unveraendert -----------------------------------------

def test_existing_put_logic_unchanged(index_html):
    """Der bestehende PUT-Pfad fuer Updates muss identisch zu v3.9.341/342/343 bleiben."""
    expected = (
        'SQ.push({url:"/api/entries/"+r.id,method:"PUT",'
        'body:{date:r.datum,taetigkeit:r.taetigkeit,hours:r.stunden,bemerkung:r.bemerkung}});'
    )
    assert expected in index_html, (
        "Bestehender PUT-Save-Pfad in editMonteurEntries wurde geaendert — "
        "v3.9.344 darf NUR neue Pfade hinzufuegen, nicht PUT-Logik aendern."
    )


# 8) Bestehende DELETE-Logik (Modal ✕-Button) unveraendert ---------------------

def test_existing_delete_button_unchanged(index_html):
    """Der ✕-Loesch-Button im Modal (Zeile aus Liste entfernen) muss bleiben."""
    # Anker: delBtn.textContent='✕' + rows.splice(rowIdx,1)
    assert "delBtn.textContent='✕'" in index_html, (
        "Modal-Loesch-Button '✕' fehlt — Regression v3.9.344."
    )
    assert "rows.splice(rowIdx,1)" in index_html, (
        "Splice-Logik des Loesch-Buttons fehlt — Regression v3.9.344."
    )


# 9) Hinweistext re-verify: kein 'NUR im Export' im dbWrite:true-Branch --------

def test_dbWrite_branch_does_not_contain_export_only_text(index_html):
    """Der dbWrite-Ternary muss im true-Branch (DB-Write) den DB-Hinweis enthalten
    und den 'NUR im Export'-Text NUR im false-Branch (Excel-only)."""
    # Pattern: dbWrite?'<db-text>':'<export-text>'
    m = re.search(
        r"dbWrite\s*\?\s*(['\"])([^'\"]+?)\1\s*:\s*(['\"])([^'\"]+?)\3",
        index_html,
    )
    assert m, "dbWrite-Ternary fuer Hinweistext nicht gefunden."
    db_text = m.group(2)
    export_text = m.group(4)
    assert "direkt in der Datenbank" in db_text, (
        f"DB-Write-Branch enthaelt nicht 'direkt in der Datenbank' — aktuell: {db_text!r}"
    )
    assert "NUR im Export" not in db_text, (
        f"DB-Write-Branch enthaelt faelschlicherweise 'NUR im Export' — aktuell: {db_text!r}"
    )
    assert "NUR im Export" in export_text, (
        f"Excel-only-Branch enthaelt nicht 'NUR im Export' — aktuell: {export_text!r}"
    )


# 10) Version-Sync --------------------------------------------------------------

def test_app_version_344(app_version):
    assert app_version == "3.9.344-supabase", (
        f"APP_VERSION nicht 3.9.344-supabase — aktuell: {app_version}"
    )


def test_cache_name_344(cache_name):
    assert cache_name == "epkolar-v3.9.344", (
        f"CACHE_NAME nicht epkolar-v3.9.344 — aktuell: {cache_name}"
    )


def test_sw_ver_344(index_html):
    assert "SW_VER='epkolar-v3.9.344'" in index_html, (
        "SW_VER im IIFE nicht epkolar-v3.9.344."
    )


def test_sw_header_344(sw_js):
    assert sw_js.startswith("// EP Kolar Service Worker v3.9.344"), (
        "SW-Header-Kommentar nicht v3.9.344."
    )
