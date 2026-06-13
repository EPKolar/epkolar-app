"""Regression-Tests fuer v3.9.340 Werkzeug-Labels Gate + Status-Filter + Toggle.

Verhindert dass:
  1. Der Werkzeug-Labels-Button wieder ALLE 298 Werkzeuge ungated fuer JEDEN
     druckt (vor v3.9.340 war das so).
  2. Der Render-Gate (Admin/PL/Buero/Lagerleitung) wegfaellt.
  3. Toggle-Checkbox-State / Label entfernt wird.
  4. Fahrzeug-Labels-Stelle versehentlich mit-geaendert wird.
  5. Der QR-Einzel-Label-Button versehentlich mit-geaendert wird.
"""
import re


# 1) Status-Filter in der Werkzeug-Labels-Onclick-Stelle ----------------------

def test_werkzeug_labels_button_has_status_filter(index_html):
    """Der Werkzeug-Labels-Button muss die Filter-Liste
    ["stillgelegt","verloren"] explizit ausschliessen (default-Pfad)."""
    # Pattern: filter(w=>!["stillgelegt","verloren"].includes(w.status))
    m = re.search(
        r'werkzeuge\.filter\(\s*w\s*=>\s*!\["stillgelegt","verloren"\]\.includes\(\s*w\.status\s*\)\s*\)',
        index_html,
    )
    assert m, (
        "Werkzeug-Labels-Button hat keinen Status-Filter mehr — "
        "Bug-Regression v3.9.340. Stillgelegte/verlorene wurden wieder reingenommen."
    )


# 2) useState fuer Toggle ----------------------------------------------------

def test_wz_show_decommissioned_useState(index_html):
    """useState [wzShowDecommissioned,setWzShowDecommissioned] muss existieren."""
    m = re.search(
        r'\[\s*wzShowDecommissioned\s*,\s*setWzShowDecommissioned\s*\]\s*=\s*_react\.useState',
        index_html,
    )
    assert m, (
        "wzShowDecommissioned useState fehlt — Toggle-State weg, "
        "Bug-Regression v3.9.340."
    )


# 3) Render-Gate isVAdmin / lokale Variante (_isVAdminWz) am Labels-Button ---

def test_werkzeug_labels_button_has_render_gate(index_html):
    """Der 🏷️ Werkzeug-Labels-Button muss durch _isVAdminWz gerendert werden
    (Render-Gate analog Fahrzeug-isVAdmin Z.18368)."""
    # Pattern: _isVAdminWz&&React.createElement('button', { onClick: ()=>... printLabels ... "Werkzeug-Labels"
    m = re.search(
        r"_isVAdminWz\s*&&\s*React\.createElement\(\s*'button'[\s\S]{0,400}?printLabels[\s\S]{0,300}?\"Werkzeug-Labels\"",
        index_html,
    )
    assert m, (
        "Werkzeug-Labels-Button hat keinen Render-Gate (_isVAdminWz) mehr — "
        "Bug-Regression v3.9.340."
    )


def test_isVAdminWz_local_definition(index_html):
    """Die lokale Variante _isVAdminWz muss admin/projektleiter/buero/lagerleitung
    pruefen (analog Z.18368)."""
    # Pattern: const _isVAdminWz=...isAdmin... "projektleiter","buero","lagerleitung"
    m = re.search(
        r'const\s+_isVAdminWz\s*=\s*[\s\S]{0,400}?isAdmin[\s\S]{0,400}?"projektleiter"[\s\S]{0,100}?"buero"[\s\S]{0,100}?"lagerleitung"',
        index_html,
    )
    assert m, (
        "_isVAdminWz-Definition fehlt oder enthaelt nicht alle 4 Rollen "
        "(admin/projektleiter/buero/lagerleitung)."
    )


# 4) Checkbox + Label "Stillgelegte/verlorene einblenden" ----------------------

def test_toggle_checkbox_render(index_html):
    """Der Render muss eine <input type=checkbox> mit dem Label
    'Stillgelegte/verlorene einblenden' enthalten — gebunden an
    wzShowDecommissioned."""
    # 1) Label-Text vorhanden
    assert "Stillgelegte/verlorene einblenden" in index_html, (
        "Toggle-Label 'Stillgelegte/verlorene einblenden' fehlt — "
        "Bug-Regression v3.9.340."
    )
    # 2) Checkbox-Input mit checked: wzShowDecommissioned + onChange-Setter
    m = re.search(
        r"React\.createElement\(\s*'input'\s*,\s*\{\s*type:\s*\"checkbox\"[\s\S]{0,200}?checked:\s*wzShowDecommissioned[\s\S]{0,200}?setWzShowDecommissioned",
        index_html,
    )
    assert m, (
        "Checkbox-Input fuer wzShowDecommissioned fehlt — "
        "Bug-Regression v3.9.340."
    )


# 5) Fahrzeug-Labels-Stelle UNVERAENDERT -------------------------------------

def test_fahrzeug_labels_unchanged(index_html):
    """Fahrzeug-Labels-Stelle (~Z.18724) muss weiterhin visibleFz + stillgelegt-Filter
    + Fahrzeug-Labels-Titel + Toast-title nutzen — v3.9.107/v3.9.338-Snapshot."""
    # Pattern: visibleFz.filter(f=>f.status!=="stillgelegt") ... "Fahrzeug-Labels"
    m = re.search(
        r'visibleFz\.filter\(\s*f\s*=>\s*f\.status\s*!==\s*"stillgelegt"\s*\)[\s\S]{0,500}?"Fahrzeug-Labels"',
        index_html,
    )
    assert m, (
        "Fahrzeug-Labels-Stelle wurde geaendert — v3.9.340 darf NUR den "
        "Werkzeug-Pfad anfassen!"
    )


# 6) QR-Einzel-Button UNVERAENDERT -------------------------------------------

def test_qr_einzel_label_button_unchanged(index_html):
    """QR-Einzel-Button (~Z.19925) muss weiterhin printLabels mit Single-Item-Array
    + Werkzeug-Label-Titel nutzen — Snapshot."""
    # Pattern: printLabels([{name:scannedWz.name,code:scannedWz.inventarnr ... "Werkzeug-Label"
    m = re.search(
        r'printLabels\(\s*\[\s*\{\s*name:\s*scannedWz\.name\s*,\s*code:\s*scannedWz\.inventarnr[\s\S]{0,200}?"Werkzeug-Label"',
        index_html,
    )
    assert m, (
        "QR-Einzel-Label-Button wurde geaendert — v3.9.340 darf NUR den "
        "Mass-Labels-Button anfassen!"
    )
