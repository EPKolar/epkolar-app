"""Regression-Tests fuer v3.9.341 Berichte-Bearbeiten-Modal:
  - Textarea fuer Taetigkeit + Bemerkung (lange Texte vorher abgeschnitten).
  - whiteSpace:normal + word-break:break-word in den Modal-Zellen.
  - Spalten-minWidth lockerer (Taetigkeit 320, Bemerkung 240, Projekt 240).
  - DB-Hinweis-Korrektur via dbWrite:true. Falscher Text "NUR im Export" steht
    NUR noch im default-Pfad (Excel-only-Aufrufer); editMonteurEntries zeigt
    "direkt in der Datenbank gespeichert".
  - Speicher-Pfad (SQ.push PUT /api/entries/<id>) unveraendert.
"""
import re


# 1) _exportReviewModal kennt 'textarea'-Typ -----------------------------------

def test_modal_supports_textarea_type(index_html):
    """In _exportReviewModal muss ein Render-Pfad fuer col.type==='textarea' existieren,
    der ein <textarea>-Element erzeugt mit rows-Default + resize:vertical."""
    m = re.search(
        r"col\.type\s*===\s*['\"]textarea['\"][\s\S]{0,400}?createElement\(\s*['\"]textarea['\"]\s*\)",
        index_html,
    )
    assert m, (
        "_exportReviewModal hat keinen textarea-Render-Pfad mehr — "
        "Regression v3.9.341."
    )


def test_modal_textarea_has_resize_vertical(index_html):
    """Der textarea-Pfad muss resize:vertical erlauben (Hoehe vom User anpassbar)."""
    # Suche das textarea-Block im Modal: createElement('textarea')...resize:vertical
    m = re.search(
        r"createElement\(\s*['\"]textarea['\"]\s*\)[\s\S]{0,800}?resize:vertical",
        index_html,
    )
    assert m, (
        "Textarea im Modal hat kein resize:vertical mehr — "
        "User kann Hoehe nicht mehr anpassen, Regression v3.9.341."
    )


# 2) editMonteurEntries nutzt textarea fuer taetigkeit + bemerkung -------------

def test_edit_monteur_entries_taetigkeit_is_textarea(index_html):
    """editMonteurEntries-Spalten-Def muss taetigkeit als type:'textarea' rendern."""
    m = re.search(
        r'key:\s*["\']taetigkeit["\']\s*,\s*label:\s*["\'][^"\']*?Tätigkeit[^"\']*?["\']\s*,\s*type:\s*["\']textarea["\']',
        index_html,
    )
    assert m, (
        "editMonteurEntries: taetigkeit ist nicht mehr type:'textarea' — "
        "Regression v3.9.341 (Sebastian-Befund: einzeilige inputs schnitten Texte ab)."
    )


def test_edit_monteur_entries_bemerkung_is_textarea(index_html):
    """editMonteurEntries-Spalten-Def muss bemerkung als type:'textarea' rendern."""
    m = re.search(
        r'key:\s*["\']bemerkung["\']\s*,\s*label:\s*["\'][^"\']*?Bemerkung[^"\']*?["\']\s*,\s*type:\s*["\']textarea["\']',
        index_html,
    )
    assert m, (
        "editMonteurEntries: bemerkung ist nicht mehr type:'textarea' — "
        "Regression v3.9.341."
    )


# 3) word-break in Zell-Style des Modals ---------------------------------------

def test_modal_cells_have_word_break(index_html):
    """Die td-Style-Definition im Modal muss word-break:break-word + white-space:normal
    enthalten, damit lange Texte umbrechen statt abgeschnitten werden."""
    # Pattern: td.style.cssText='...word-break:break-word...'
    m = re.search(
        r"td\.style\.cssText\s*=\s*['\"][^'\"]*?word-break\s*:\s*break-word",
        index_html,
    )
    assert m, (
        "td-Style im _exportReviewModal hat kein word-break:break-word mehr — "
        "lange Texte werden wieder abgeschnitten, Regression v3.9.341."
    )


def test_modal_cells_have_whitespace_normal(index_html):
    """Die td-Style-Definition muss white-space:normal haben (sonst kein Umbruch)."""
    m = re.search(
        r"td\.style\.cssText\s*=\s*['\"][^'\"]*?white-space\s*:\s*normal",
        index_html,
    )
    assert m, (
        "td-Style im _exportReviewModal hat kein white-space:normal mehr — "
        "Regression v3.9.341."
    )


# 4) "NUR im Export"-String ist NICHT mehr im editMonteurEntries-Aufruf -------

def test_edit_monteur_entries_uses_dbWrite_flag(index_html):
    """editMonteurEntries muss dbWrite:true an _exportReviewModal uebergeben — damit
    der korrekte DB-Hinweis statt des Excel-Hinweises angezeigt wird."""
    # Such die editMonteurEntries-Funktion und prueft auf dbWrite:true
    m = re.search(
        r"const\s+editMonteurEntries\s*=[\s\S]{0,3000}?dbWrite\s*:\s*true",
        index_html,
    )
    assert m, (
        "editMonteurEntries setzt dbWrite:true nicht mehr — Hinweis im Modal "
        "wuerde falsch sein ('NUR im Export' statt DB-Write). Regression v3.9.341."
    )


def test_modal_dbWrite_branch_has_correct_db_text(index_html):
    """Der korrekte Hinweis-Text muss im dbWrite-Branch des Modal-Notes stehen."""
    # Pattern: dbWrite?'...direkt in der Datenbank...':'...NUR im Export...'
    m = re.search(
        r"dbWrite\s*\?\s*['\"][^'\"]*?direkt in der Datenbank gespeichert",
        index_html,
    )
    assert m, (
        "Korrekter DB-Hinweis 'direkt in der Datenbank gespeichert' fehlt im "
        "dbWrite-Branch — Regression v3.9.341."
    )


def test_modal_default_branch_keeps_export_only_text(index_html):
    """Der default-Branch (dbWrite!=true) muss weiterhin den Excel-only-Hinweis
    enthalten — denn 3 Aufrufer (Zeiterfassung/Wochenplanung/Abwesenheit/BWB)
    schreiben TATSAECHLICH nur ins Excel und nicht in die DB."""
    # Der Text muss als kompletter String-Literal im default-Zweig der dbWrite-Ternary stehen.
    expected = "NUR im Export, die Datenbank bleibt unverändert"
    assert expected in index_html, (
        "Excel-only-Hinweis im default-Branch des Modal-Notes fehlt — "
        "die 3 Excel-Aufrufer wuerden jetzt einen falschen DB-Hinweis sehen, "
        "Regression v3.9.341."
    )


# 5) Speicher-Logik unveraendert ----------------------------------------------

def test_save_path_unchanged_sq_push_put(index_html):
    """Der Save-Pfad in editMonteurEntries muss weiterhin SQ.push mit method:'PUT'
    und url:'/api/entries/'+r.id + Body {date, taetigkeit, hours, bemerkung} sein."""
    # Anker-Snapshot der unveraendert bleiben muss
    expected = (
        'SQ.push({url:"/api/entries/"+r.id,method:"PUT",'
        'body:{date:r.datum,taetigkeit:r.taetigkeit,hours:r.stunden,bemerkung:r.bemerkung}});'
    )
    assert expected in index_html, (
        "Save-Pfad in editMonteurEntries wurde geaendert — "
        "v3.9.341 darf NUR DOM-Render anfassen, nicht die SQ.push-Logik."
    )


# 6) Modal-th-minWidth bleibt aus col.width ableitbar (Spaltenbreiten lockerer) -

def test_modal_uses_min_width_for_th(index_html):
    """Die <th>-Render-Stelle im _exportReviewModal muss col.width auf min-width
    mappen — fixe width wuerde das word-break unwirksam machen."""
    m = re.search(
        r"th\.style\.cssText\s*=[\s\S]{0,400}?col\.width\s*\?\s*['\"]min-width:['\"]",
        index_html,
    )
    assert m, (
        "<th>-Style im Modal nutzt nicht mehr min-width — Spalten sind wieder "
        "fix-breit, Regression v3.9.341."
    )


# 7) Spalten-minWidths in editMonteurEntries: Taetigkeit 320, Bemerkung 240 ---

def test_edit_monteur_entries_column_widths(index_html):
    """editMonteurEntries muss width:320 fuer taetigkeit und width:240 fuer bemerkung
    setzen — Sebastian-Vorgabe wegen langer Texte."""
    # Suche im editMonteurEntries-Block
    m_edit = re.search(
        r"const\s+editMonteurEntries\s*=[\s\S]{0,3000}?confirmLabel",
        index_html,
    )
    assert m_edit, "editMonteurEntries-Block nicht gefunden"
    block = m_edit.group(0)

    # Taetigkeit width:320
    assert re.search(
        r'key:\s*["\']taetigkeit["\'][^}]*?width:\s*320',
        block,
    ), "taetigkeit width!=320 — Regression v3.9.341"

    # Bemerkung width:240
    assert re.search(
        r'key:\s*["\']bemerkung["\'][^}]*?width:\s*240',
        block,
    ), "bemerkung width!=240 — Regression v3.9.341"

    # Projekt readonly bleibt 240
    assert re.search(
        r'key:\s*["\']projekt_name["\'][^}]*?width:\s*240',
        block,
    ), "projekt_name width!=240 — Regression v3.9.341"


# 8) Version-Sync --------------------------------------------------------------

def test_app_version_341(app_version):
    assert app_version == "3.9.341-supabase", (
        f"APP_VERSION nicht auf 3.9.341 — aktuell: {app_version}"
    )


def test_cache_name_341(cache_name):
    assert cache_name == "epkolar-v3.9.341", (
        f"CACHE_NAME nicht auf epkolar-v3.9.341 — aktuell: {cache_name}"
    )


def test_sw_ver_341(index_html):
    assert "SW_VER='epkolar-v3.9.341'" in index_html, (
        "SW_VER im IIFE nicht auf v3.9.341 gebumpt."
    )
