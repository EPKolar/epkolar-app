"""v3.9.122 — ALLE AS-Statuswechsel frei (Sebastian 04.06.2026).

Historie: v3.8.92 führte eine Status-Maschine ein (39/56 Übergänge verboten). v3.9.121 öffnete
in_bearbeitung→abgerechnet. Sebastian: "es gehen nicht alle wechsel" → v3.9.122 öffnet ALLE
(Verhalten wie vor v3.8.92, als das Formular nie prüfte). Guard-Infrastruktur bleibt verdrahtet.
"""
import json
import re
from conftest import run_node_snippet

STATES = ["aufgenommen", "freigegeben", "in_bearbeitung", "aufgeschoben",
          "erledigt", "abgerechnet", "bar_bezahlt", "storniert"]


def _extract_machine(index_html):
    m = re.search(r"const _AS_ALL_STATES=\[[\s\S]*?\];\s*\nconst AS_TRANSITIONS=\{[\s\S]*?\};\s*\nconst _isLegalAsTransition=[^\n]+;", index_html)
    assert m, "_AS_ALL_STATES + AS_TRANSITIONS + _isLegalAsTransition nicht gefunden"
    return m.group(0)


def test_all_56_transitions_allowed(node_exe, index_html):
    code = _extract_machine(index_html)
    snippet = (
        code.replace("const _isLegalAsTransition", "globalThis._t") +
        "const S=" + json.dumps(STATES) + ";"
        "const blocked=[];S.forEach(f=>S.forEach(t=>{if(f!==t&&!_t(f,t))blocked.push(f+'->'+t);}));"
        "process.stdout.write(JSON.stringify(blocked));"
    )
    blocked = json.loads(run_node_snippet(node_exe, snippet))
    assert blocked == [], f"v3.9.122: ALLE Wechsel müssen erlaubt sein, blockiert: {blocked}"


def test_guards_still_wired(index_html):
    # Die 3 Guard-Stellen bleiben verdrahtet (Re-Einschränkung später = nur Map reduzieren)
    assert len(re.findall(r"_isLegalAsTransition\s*\(", index_html)) >= 3, (
        "Guard-Aufrufe (Swipe/Dropdown/Formular) müssen verdrahtet bleiben"
    )
