"""Regression-Tests fuer v3.9.346 Arbeitsscheine — Kein App-Anlegen mehr (nur OFFA).

Drei UI-Anlege-Wege wurden entfernt:
  1. Action-Bar-Button '+ Neuer Schein'.
  2. Action-Bar-Button '🎤 Schnellerfassung' (Voice-Anlege) + komplettes Voice-Modal.
  3. Sub-Nav-Tab '✏️ Neu' (id:"form" mit Label 'Neu').

NICHT angetastet:
  - openEdit-Pfad bestehender Scheine (setForm({...a});setEditId(a.id);setSub('form')).
  - saveAs PUT-Branch (editId-Pfad).
  - importOffa / commitImport (OFFA-PDF-Import).
  - exportOffa (OFFA-Excel-Export).
  - _juprowaPush (Phase-2-sensitiv).
  - Status-Setzen, QR-Scan, Liste, Kalender, Vorlagen-Tab.
"""
import re


def _arbeitsschein_view_block(index_html):
    start_m = re.search(r"function\s+ArbeitsscheinView\s*\(", index_html)
    assert start_m, "ArbeitsscheinView-Funktion nicht gefunden"
    # Suche naechste top-level function-Definition nach ArbeitsscheinView
    end_m = re.search(
        r"\nfunction\s+[A-Z]\w*\s*\(",
        index_html[start_m.end():],
    )
    assert end_m, "Naechste top-level-Funktion nach ArbeitsscheinView nicht gefunden"
    return index_html[start_m.start(): start_m.end() + end_m.start()]


# 1) '+ Neuer Schein'-Button entfernt -----------------------------------------

def test_no_neuer_schein_button_in_view(index_html):
    """Der Action-Bar-Button-Text '+ Neuer Schein' darf im ArbeitsscheinView-Render
    nicht mehr vorkommen."""
    block = _arbeitsschein_view_block(index_html)
    assert "+ Neuer Schein" not in block, (
        "v3.9.346 Regression: '+ Neuer Schein'-Button-Text noch in ArbeitsscheinView. "
        "Action-Bar-Button muss entfernt sein."
    )


# 2) '🎤 Schnellerfassung'-Button entfernt ------------------------------------

def test_no_schnellerfassung_button_in_view(index_html):
    """Der Action-Bar-Button-Text 'Schnellerfassung' darf im ArbeitsscheinView-Render
    nicht mehr vorkommen."""
    block = _arbeitsschein_view_block(index_html)
    assert "Schnellerfassung" not in block, (
        "v3.9.346 Regression: 'Schnellerfassung'-Button-Text noch in "
        "ArbeitsscheinView. Voice-Button muss entfernt sein."
    )


# 3) Sub-Nav-Tab id:"form" entfernt -------------------------------------------

def test_no_form_tab_in_subnav(index_html):
    """Das Sub-Nav-Tab-Array darf KEIN {id:"form",...} mehr enthalten —
    Anker: das Label 'Neu' im Tab + id:"form" zusammen."""
    block = _arbeitsschein_view_block(index_html)
    # Wir suchen das alte Pattern explizit
    old_pattern = re.search(
        r'\{\s*id\s*:\s*["\']form["\']\s*,\s*i\s*:\s*["\']✏️["\']\s*,\s*l\s*:\s*editId',
        block,
    )
    assert old_pattern is None, (
        "v3.9.346 Regression: Sub-Nav-Tab {id:'form',i:'✏️',l:editId?...:'Neu'} noch "
        "in ArbeitsscheinView. Tab muss entfernt sein."
    )
    # Sub-Nav-Array muss noch andere Tabs enthalten (liste/qrscan/kalender/vorlagen)
    sub_nav = re.search(
        r'\[\s*\{\s*id\s*:\s*["\']liste["\'][\s\S]{0,400}?\]\.map\(t=>React\.createElement\(\s*[\'\"]button[\'\"]',
        block,
    )
    assert sub_nav, (
        "v3.9.346 Regression: Sub-Nav-Tab-Array (liste/qrscan/kalender/vorlagen) nicht "
        "mehr gefunden — Tab-Bar darf nicht komplett verloren gehen."
    )


# 4) form-View-Render-Block existiert weiterhin (fuer openEdit) ---------------

def test_form_render_block_still_present(index_html):
    """Der `sub==='form'`-Render-Block bleibt — openEdit aktiviert ihn weiterhin."""
    block = _arbeitsschein_view_block(index_html)
    # Klassisches Pattern: sub==="form"&&React.createElement(...
    assert re.search(
        r'sub\s*===?\s*["\']form["\']',
        block,
    ), (
        "v3.9.346 Regression: sub==='form'-Render-Block muss erhalten bleiben "
        "(openEdit-Pfad braucht ihn fuer bestehende Scheine)."
    )


# 5) openEdit unveraendert -----------------------------------------------------

def test_open_edit_unchanged(index_html):
    """openEdit-Pattern (setForm({...a});setEditId(a.id);setSub('form')) muss
    unveraendert vorhanden sein."""
    assert re.search(
        r'const\s+openEdit\s*=\s*a\s*=>\s*\{\s*setForm\(\{\.\.\.a\}\)\s*;\s*setEditId\(a\.id\)\s*;\s*setSub\(\s*["\']form["\']\s*\)\s*;\s*\}',
        index_html,
    ), (
        "v3.9.346 Regression: openEdit-Funktion (setForm/setEditId/setSub('form')) "
        "wurde geaendert — Edit-Pfad bestehender Scheine darf nicht angetastet werden."
    )


# 6) saveAs PUT-Pfad unveraendert ---------------------------------------------

def test_save_as_put_anchor_unchanged(index_html):
    """saveAs-PUT-Pattern (editId-Pfad → SQ.push PUT /api/arbeitsscheine/) bleibt."""
    block = _arbeitsschein_view_block(index_html)
    # editId?"/api/arbeitsscheine/"+editId:"/api/arbeitsscheine" anker
    assert (
        '"/api/arbeitsscheine/"+editId' in block
        and 'method:editId?"PUT":"POST"' in block
    ), (
        "v3.9.346 Regression: saveAs PUT-Anker (editId-PUT auf "
        "/api/arbeitsscheine/+editId) wurde veraendert."
    )


# 7) importOffa unveraendert --------------------------------------------------

def test_import_offa_unchanged(index_html):
    """importOffa-Pfad (OFFA-PDF-Import) muss voll funktionsfaehig bleiben."""
    block = _arbeitsschein_view_block(index_html)
    assert re.search(
        r'const\s+importOffa\s*=\s*async\s*\(\s*e\s*\)',
        block,
    ), "v3.9.346 Regression: importOffa-Funktion fehlt — OFFA-Import darf nicht angetastet werden."
    # commitImport (Insert-Pfad fuer OFFA-Scheine) bleibt
    assert "const commitImport=" in block, (
        "v3.9.346 Regression: commitImport-Funktion fehlt — OFFA-Insert-Pfad muss bleiben."
    )
    # SQ.push POST /api/arbeitsscheine im commitImport (OFFA-Insert-Pfad)
    assert 'url:"/api/arbeitsscheine",method:"POST"' in block, (
        "v3.9.346 Regression: SQ.push POST /api/arbeitsscheine fehlt — "
        "OFFA-Import-Insert-Pfad muss intakt bleiben."
    )


# 8) _juprowaPush-Anker unveraendert (Phase-2-sensitiv) ------------------------

def test_juprowa_push_call_unchanged(index_html):
    """Der Auto-Push-Anker in saveAs (_juprowaPush(editId).then) darf NICHT
    veraendert sein — Phase-2-sensitiver Juprowa-Sync-Bereich."""
    block = _arbeitsschein_view_block(index_html)
    # Anker auf die exakte Aufrufe-Sequenz (v3.8.42 Auto-Push, hat ueberlebt v3.9.346):
    assert (
        '_juprowaPush(editId).then(r=>{if(!r||(!r.ok&&r.error))console.warn'
        in block
    ), (
        "v3.9.346 Regression: _juprowaPush(editId)-Auto-Push-Anker in saveAs wurde "
        "veraendert. Phase-2-Juprowa-Sync darf NICHT angetastet werden!"
    )


# 9) Voice-Anlege-Pfad (setArbeitsscheine + uid + pushNotif as_new) entfernt --

def test_voice_anlege_pfad_entfernt(index_html):
    """Der saveAs-else-Branch mit setArbeitsscheine(prev=>[{..._finalForm,id:uid()},...])
    darf nicht mehr existieren."""
    block = _arbeitsschein_view_block(index_html)
    # Negativ-Assert auf das alte Voice-/Neu-Anlege-Pattern
    assert (
        "setArbeitsscheine(prev=>[{..._finalForm,id:uid()},...prev])" not in block
    ), (
        "v3.9.346 Regression: Voice-/Neu-Anlege-Pfad (setArbeitsscheine prev=>[{..._finalForm,id:uid()},...prev]) "
        "noch im Code — saveAs-else-Branch muss entfernt sein."
    )


# 10) pushNotif('as_new') im Voice-/Anlege-Pfad entfernt ----------------------

def test_push_notif_as_new_removed_from_voice_path(index_html):
    """pushNotif('as_new'/\"as_new\") darf im ArbeitsscheinView nicht mehr vorkommen
    (war im jetzt entfernten saveAs-else-Branch). OFFA-Import nutzt diesen
    Notifier nicht — commitImport verwendet kein pushNotif."""
    block = _arbeitsschein_view_block(index_html)
    matches = re.findall(r'pushNotif[\s\S]{0,80}?["\']as_new["\']', block)
    assert len(matches) == 0, (
        "v3.9.346 Regression: pushNotif('as_new') noch im ArbeitsscheinView "
        f"(gefunden: {len(matches)}). Voice-/Neu-Anlege-Pfad muss komplett entfernt sein."
    )


# 11) openNew entfernt ---------------------------------------------------------

def test_open_new_function_removed_from_view(index_html):
    """Die openNew-Funktion (setForm(defAs());setEditId(null);setSub('form'))
    darf in ArbeitsscheinView nicht mehr existieren. WzView (Werkzeuge) hat
    ihre eigene gleichnamige openNew-Funktion — die bleibt."""
    block = _arbeitsschein_view_block(index_html)
    assert re.search(
        r'const\s+openNew\s*=\s*\(\s*\)\s*=>\s*\{\s*setForm\(defAs\(\)\)',
        block,
    ) is None, (
        "v3.9.346 Regression: openNew-Funktion in ArbeitsscheinView noch da. "
        "Muss entfernt sein (kein UI-Caller mehr)."
    )


# 12) voiceStart / voiceStop / parseVoice entfernt ----------------------------

def test_voice_helpers_removed(index_html):
    """voiceStart, voiceStop, parseVoice, voiceConfirm, voiceRetry, showVoice
    duerfen NICHT mehr im Code stehen — kein UI-Caller mehr."""
    block = _arbeitsschein_view_block(index_html)
    for ident in ("voiceStart", "voiceStop", "voiceConfirm", "voiceRetry", "parseVoice", "showVoice"):
        assert ident not in block, (
            f"v3.9.346 Regression: '{ident}' noch in ArbeitsscheinView. "
            "Voice-Anlege-Pfad muss komplett entfernt sein."
        )


# 13) canDo('as_create') hat im View keinen UI-Caller mehr --------------------

def test_no_as_create_ui_caller_in_view(index_html):
    """canDo('as_create',...) darf in ArbeitsscheinView nicht mehr aufgerufen werden.
    Die Permission bleibt im Permission-System (canDo-Definition + Defense-in-Depth
    Toast in saveAs)."""
    block = _arbeitsschein_view_block(index_html)
    matches = re.findall(r'canDo\(\s*["\']as_create["\']', block)
    assert len(matches) == 0, (
        f"v3.9.346 Regression: canDo('as_create') noch {len(matches)}x in "
        "ArbeitsscheinView. UI-Einstiege muessen weg, Permission bleibt im "
        "Permission-System (canDo-Definition)."
    )


# 14) Voice-Modal-Render entfernt ---------------------------------------------

def test_voice_modal_render_block_removed(index_html):
    """Das Voice-Modal-Render-Pattern (Sprach-Schnellerfassung Header) darf
    nicht mehr existieren."""
    assert "🎤 Sprach-Schnellerfassung" not in index_html, (
        "v3.9.346 Regression: Voice-Modal-Header 'Sprach-Schnellerfassung' noch "
        "im Render. Modal muss entfernt sein."
    )


# 15) Version-Sync ------------------------------------------------------------

def test_app_version_346(app_version):
    """Forward-Guard: APP_VERSION mindestens 3.9.346 (Arbeitsscheine-Floor)."""
    import re
    m = re.match(r"3\.9\.(\d+)-supabase", app_version)
    assert m and int(m.group(1)) >= 346, (
        f"APP_VERSION unter 3.9.346 — aktuell: {app_version}"
    )


def test_cache_name_346(cache_name):
    """Forward-Guard: CACHE_NAME mindestens 3.9.346."""
    import re
    m = re.match(r"epkolar-v3\.9\.(\d+)", cache_name)
    assert m and int(m.group(1)) >= 346, (
        f"CACHE_NAME unter 3.9.346 — aktuell: {cache_name}"
    )


def test_sw_ver_346(index_html):
    """Forward-Guard: SW_VER im IIFE mindestens 3.9.346."""
    import re
    m = re.search(r"SW_VER='epkolar-v3\.9\.(\d+)'", index_html)
    assert m and int(m.group(1)) >= 346, "SW_VER im IIFE unter 3.9.346."


def test_sw_header_346(sw_js):
    """Forward-Guard: SW-Header mindestens 3.9.346."""
    import re
    m = re.match(r"// EP Kolar Service Worker v3\.9\.(\d+)", sw_js)
    assert m and int(m.group(1)) >= 346, "SW-Header-Kommentar unter 3.9.346."
