"""v3.9.121 — in_bearbeitung darf direkt nach abgerechnet/bar_bezahlt.

Sebastian 04.06.2026: "hat schon funktioniert" — vor dem v3.8.92-Transitions-Guard war der
Direktwechsel am Formular nie geprüft und gängige Büro-Praxis. Der Guard blockte ihn dann
mit "Ungültiger Status-Wechsel von in_bearbeitung → abgerechnet".
"""
import json
import re
from conftest import run_node_snippet


def _extract_machine(index_html):
    m = re.search(r"const AS_TRANSITIONS=\{[\s\S]*?\};\s*\nconst _isLegalAsTransition=[^\n]+;", index_html)
    assert m, "AS_TRANSITIONS + _isLegalAsTransition nicht gefunden"
    return m.group(0)


def test_direct_billing_transitions_allowed(node_exe, index_html):
    code = _extract_machine(index_html)
    snippet = (
        code.replace("const _isLegalAsTransition", "globalThis._t") +
        "process.stdout.write(JSON.stringify(["
        "_t('in_bearbeitung','abgerechnet'),"   # Sebastian-Fall: jetzt erlaubt
        "_t('in_bearbeitung','bar_bezahlt'),"   # Pendant: erlaubt
        "_t('in_bearbeitung','erledigt'),"      # weiterhin erlaubt
        "_t('aufgenommen','abgerechnet'),"      # weiterhin verboten (nie in Bearbeitung gewesen)
        "_t('abgerechnet','in_bearbeitung'),"   # Endzustand bleibt final
        "_t('storniert','abgerechnet')"         # Endzustand bleibt final
        "]));"
    )
    res = json.loads(run_node_snippet(node_exe, snippet))
    assert res == [True, True, True, False, False, False], f"Transition-Verhalten falsch: {res}"
