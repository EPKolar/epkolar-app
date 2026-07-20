"""v3.9.647 KV-V1 — KV-Konstanten-Modul + Konfig-UI.

Node-eval der Fallback-Konstanten (Sentinel //@KV-RULES) + Struktur-Checks der
isWAdm-Konfig-Sektion. NUR Auswertung/Anspruchsfuehrung — Lohnverrechner massgeblich.
"""
import re
import json
from conftest import run_node_snippet


def _block(index_html):
    m = re.search(r"//@KV-RULES-START(.*?)//@KV-RULES-END", index_html, re.S)
    assert m, "KV-RULES-Block nicht gefunden"
    return m.group(1)


def _kv(node_exe, index_html):
    snippet = _block(index_html) + "\nprocess.stdout.write(JSON.stringify(KV_RULES_FALLBACK))"
    return json.loads(run_node_snippet(node_exe, snippet))


def test_kv_kernwerte(node_exe, index_html):
    kv = _kv(node_exe, index_html)
    assert kv["wochenStd"] == 38.5
    assert kv["tagStd"] == 7.7
    assert kv["urlaubStdJahr"] == 192.5
    assert kv["urlaubStdJahr25DJ"] == 231
    # v3.9.768: Lohnzettel EP Kolar LA 2740 "Entfernungszl.kl.fr." — 11,94 war ein KV-Schaetzwert.
    assert kv["taggeldAb6h"] == 11.71
    assert kv["taggeldAb11h"] == 30.0
    # v3.9.774: Montagezulage (montagezulageStd/montagezulage) komplett aus der App entfernt —
    # der Lohnverrechner macht sie. Das Feld darf NICHT mehr im Fallback stehen.
    assert "montagezulageStd" not in kv
    assert kv["kmGeld"] == 0.5
    assert kv["stand"].startswith("Lohnzettel EP Kolar")


def test_kv_zuschlag_faktoren(node_exe, index_html):
    kv = _kv(node_exe, index_html)
    assert kv["zaFaktor50"] == 1.5
    assert kv["zaFaktor100"] == 2.0
    assert kv["zuschlagUeStd"] == 0.5
    assert kv["zuschlagUeStd100"] == 1.0


def test_kv_loader_reads_system_config(index_html):
    assert "_sbGet('system_config','key=eq.kv_rules&select=value')" in index_html


def test_kv_window_global(index_html):
    assert "window.KV_RULES=" in index_html


# ── UI ──
def test_kv_config_component(index_html):
    assert "function KVRulesConfig(props)" in index_html


def test_kv_config_iswadm_gated(index_html):
    assert "isWAdm&&React.createElement(KVRulesConfig" in index_html


def test_kv_config_upsert(index_html):
    assert re.search(r'_sbUpsert\("system_config",\{key:"kv_rules"', index_html)


def test_kv_lohnverrechner_hinweis(index_html):
    assert "Lohnverrechner maßgeblich" in index_html
