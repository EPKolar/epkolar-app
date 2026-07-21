# -*- coding: utf-8 -*-
"""v3.9.804 — KV-Zuschlags-Report: raus aus der Auswertung -> Chef-Portal/Personal (Sebastian).

Zuschlags-Aequivalente/Ueber-Mehrarbeit je Person sind lohnsensibel — Monteure UND Angestellte
(auch Buero/PL) duerfen sie in der Auswertung nicht sehen. Verschoben ins ChefDashboard/Personal-
Sub-Tab; das Chef-Portal ist bereits admin/GF-only (Sebastian ist GF). REINE Platzierung, keine
Rechenaenderung — der Report-Code bleibt byte-identisch.
"""


def test_zuschlag_raus_aus_auswertung(index_html):
    # Der Auswertungs-Render (_canSeeVolume && KVZuschlagReport) ist ENTFERNT.
    assert "_canSeeVolume && React.createElement(KVZuschlagReport" not in index_html, \
        "KVZuschlagReport haengt noch in der Auswertung (_canSeeVolume)"


def test_zuschlag_im_chef_personal(index_html):
    # Jetzt im ChefDashboard/Personal-Sub-Tab.
    assert "_cdTab==='personal' && React.createElement(KVZuschlagReport, { entries: entries, monteure: monteure, ww: ww} )" in index_html, \
        "KVZuschlagReport nicht im Chef-Personal-Tab (oder Props veraendert)"


def test_kein_extra_gate_aber_chef_portal_admin_gf(index_html):
    # Kein zusaetzliches Gate am Report (das _chef-Portal-Gate deckt es ab).
    assert '_cdTab===\'personal\' && curUser.role==="admin" && React.createElement(KVZuschlagReport' not in index_html, \
        "unnoetiges Extra-Gate wieder da (wuerde GF-Sebastian aussperren)"
    # Der _chef-Portal-Gate (admin ODER Geschaeftsfuehrer) bleibt die Zugangsschranke.
    assert 'return curUser.role==="admin"||_isGF;' in index_html, "_chef-Portal-Gate (admin ODER GF) veraendert"


def test_rechenkern_und_auftragsvolumen_unberuehrt(index_html):
    # KV-Zuschlag-Rechenkern-Marker unangetastet.
    assert "//@KV-ZUSCHLAG" in index_html, "KV-Zuschlag-Rechenkern-Marker verschwunden"
    # Report-Funktion existiert weiter (nur Ort geaendert).
    assert "function KVZuschlagReport(props){" in index_html, "KVZuschlagReport-Funktion veraendert/entfernt"
    # Das _canSeeVolume-Auftragsvolumen-KPI in der Auswertung bleibt (nur der Report ging).
    assert "v3.9.385: Auftragsvolumen nach Geschäftsjahr" in index_html, "Auftragsvolumen-KPI in der Auswertung veraendert"
