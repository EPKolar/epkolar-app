# -*- coding: utf-8 -*-
"""v3.9.780 — Manueller "OFFA Import"-Button + toter PDF-Import-Flow entfernt.

v698-Muster (reiner Wegfall, kein Refactoring): der einzige Einstieg in den
manuellen PDF-Import (Button + verstecktes File-Input) wurde entfernt und mit ihm
der komplette tote Flow — importRef, importOffa, commitImport, updPreview,
sub==="import_preview"-Vorschau-Modal, States importPreview/importLoading und der
nur davon genutzte Parser _parseOffaPdf.

Regression-Pin: 0 LEBENDE Referenzen (Erwaehnung in der APP_VERSION-Changelog-Zeile
zaehlt nicht). Der OFFA-EXCEL-EXPORT (exportOffa/setShowExportPicker/"OFFA Excel")
und der allgemeine sub/setSub-Sub-Tab-State bleiben UNBERUEHRT.
"""


def _code_without_changelog(index_html):
    """index.html ohne die (einzige) APP_VERSION-Changelog-Zeile — diese darf die
    entfernten Symbolnamen als Historie nennen, ohne als lebende Referenz zu zaehlen."""
    return "\n".join(
        ln for ln in index_html.split("\n") if "const APP_VERSION=" not in ln
    )


def test_import_flow_symbols_gone_0_living_refs(index_html):
    code = _code_without_changelog(index_html)
    for sym in ("importOffa", "importRef", "commitImport",
                "importPreview", "importLoading", "import_preview"):
        assert sym not in code, (
            f"v3.9.780 Regression: '{sym}' hat noch eine lebende Referenz "
            "(ausserhalb der APP_VERSION-Changelog-Zeile). Der manuelle "
            "OFFA-PDF-Import-Flow muss restlos entfernt sein."
        )


def test_import_flow_code_anchors_gone(index_html):
    """Die konkreten Code-Anker des Flows duerfen nicht mehr existieren."""
    code = _code_without_changelog(index_html)
    for anchor in (
        "const importOffa=async(e)=>{",
        "const commitImport=",
        "const importRef=_react.useRef",
        'sub==="import_preview"',
        "const [importPreview,setImportPreview]",
        "const [importLoading,setImportLoading]",
    ):
        assert anchor not in code, (
            f"v3.9.780 Regression: Code-Anker '{anchor}' noch vorhanden."
        )


def test_offa_pdf_parser_removed(index_html):
    """_parseOffaPdf war NUR vom manuellen Import-Handler genutzt -> mit entfernt."""
    code = _code_without_changelog(index_html)
    assert "async function _parseOffaPdf(file){" not in code, (
        "v3.9.780 Regression: _parseOffaPdf-Funktion noch da — einziger Aufrufer "
        "(manueller OFFA-Import) ist weg, Parser muss mit entfernt sein."
    )


def test_offa_import_button_and_input_gone(index_html):
    assert "\U0001F4E4 OFFA Import" not in _code_without_changelog(index_html), (
        "v3.9.780 Regression: '📤 OFFA Import'-Button-Text noch im Render."
    )
    assert "onChange: importOffa" not in index_html, (
        "v3.9.780 Regression: verstecktes File-Input (onChange: importOffa) noch da."
    )


def test_offa_excel_export_untouched(index_html):
    """Der OFFA-EXCEL-EXPORT bleibt vollstaendig erhalten."""
    assert "const exportOffa=" in index_html, "exportOffa-Funktion fehlt — Export darf NICHT entfernt werden."
    assert "\U0001F4CA OFFA Excel" in index_html, "'📊 OFFA Excel'-Export-Button fehlt."
    assert "setShowExportPicker" in index_html, "Export-Picker-State (setShowExportPicker) fehlt."


def test_sub_subtab_state_untouched(index_html):
    """sub/setSub ist der allgemeine Sub-Tab-State der AS-Ansicht — bleibt intakt.
    Nur der import_preview-Render-Zweig wurde entfernt; andere sub-Zweige bleiben."""
    assert 'setSub("liste")' in index_html, "allgemeiner setSub-State fehlt."
    assert 'sub==="form"' in index_html, "sub==='form'-Render-Zweig (openEdit) fehlt."
    assert 'sub==="dispo"' in index_html, "sub==='dispo'-Render-Zweig fehlt."
