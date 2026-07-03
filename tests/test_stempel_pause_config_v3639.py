"""v3.9.639 Stempel-Pausenregeln-Konfig — strukturelle Verifikation.

Reine Struktur-Checks am Quelltext (die Netto-Logik selbst ist in
test_stempel_netto_v3638.py abgedeckt; hier nur die UI-Verdrahtung).
"""
import re


def test_component_defined(index_html):
    assert "function StempelPauseConfig(props)" in index_html


def test_gated_by_iswadm_not_isadmin(index_html):
    # Render nur fuer echtes Admin (isWAdm), NICHT isAdmin (schliesst PL/Buero ein).
    assert "isWAdm&&React.createElement(StempelPauseConfig" in index_html


def test_upsert_system_config_key(index_html):
    # Speichern nach ticket_templates-Muster: _sbUpsert system_config, key stempel_pause_rules
    m = re.search(r'_sbUpsert\("system_config",\{key:"stempel_pause_rules"', index_html)
    assert m, "Upsert auf system_config/stempel_pause_rules fehlt"


def test_roles_from_workers_role(index_html):
    # Rollen-Domaene = workers.role (gleiche Domaene wie _stTagNetto-Lookup)
    assert "_sbGet('workers','select=role')" in index_html


def test_hint_abgrenzung_manuelle_zeiterfassung(index_html):
    assert "nicht für die manuelle Zeiterfassung" in index_html


def test_number_input_clamped_0_120(index_html):
    # StempelPauseConfig-Input min 0 / max 120
    assert re.search(r"type:\"number\",min:0,max:120", index_html)
