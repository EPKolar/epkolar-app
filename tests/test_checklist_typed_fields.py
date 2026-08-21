"""
PlanRadar ③a — typisierte Checklisten-Felder (v3.9.830).

Eine Checklisten-Zeile darf ein `type` tragen: check (Default = Häkchen), number
(Messwert + unit), text, date, select (options). "Erledigt" = Häkchen (check) bzw.
ein nicht-leerer `value` (value-Typen). Additiv, kein DDL (items ist JSON/TEXT);
bestehende String-/Häkchen-Checklisten bleiben unberührt.
"""
import re
import json
from conftest import _extract_fn, run_node_snippet


def test_clItemDone_existiert_und_exportiert(index_html):
    assert "function _clItemDone(" in index_html, "_clItemDone fehlt"
    assert "window._clItemDone=_clItemDone" in index_html, "_clItemDone nicht window-exportiert"


def test_cl_field_types_definiert(index_html):
    m = re.search(r"var CL_FIELD_TYPES=\[(.+?)\];", index_html)
    assert m, "CL_FIELD_TYPES fehlt"
    block = m.group(1)
    for t in ("check", "number", "text", "date", "select"):
        assert '"' + t + '"' in block or "'" + t + "'" in block, f"Feldtyp {t} fehlt"


def test_clItemDone_semantik_via_node(index_html, node_exe):
    src = _extract_fn(index_html, "_clItemDone")
    assert src, "_clItemDone-Quelle nicht extrahierbar"
    cases = [
        ({"type": "check", "done": True}, True),
        ({"type": "check", "done": False}, False),
        ({"done": True}, True),                     # kein type -> check
        ({"done": False}, False),
        ({"type": "number", "value": "3.5"}, True),
        ({"type": "number", "value": ""}, False),
        ({"type": "number", "value": "0"}, True),   # Messwert 0 IST ein Wert
        ({"type": "number", "value": 0}, True),
        ({"type": "text", "value": "   "}, False),  # nur Whitespace = leer
        ({"type": "text", "value": "ok"}, True),
        ({"type": "select", "value": "A"}, True),
        ({"type": "select", "value": ""}, False),
        ({"type": "date", "value": "2026-09-01"}, True),
        (None, False),
        # value-Typ ignoriert ein evtl. gesetztes done-Flag:
        ({"type": "number", "value": "", "done": True}, False),
    ]
    snippet = (
        src
        + "\nconst _cases=" + json.dumps(cases)
        + ";\nconst _out=_cases.map(([it,exp])=>({exp, got:_clItemDone(it)}));"
        + "\nconsole.log(JSON.stringify(_out));"
    )
    out = json.loads(run_node_snippet(node_exe, snippet))
    for row in out:
        assert row["got"] == row["exp"], f"_clItemDone falsch: {row}"


def test_render_hat_typisierte_eingaben(index_html):
    for branch in ('(_ty==="number")?', '(_ty==="text")?', '(_ty==="date")?', '(_ty==="select")?'):
        assert branch in index_html, f"Render-Zweig {branch} fehlt"
    # value wird geschrieben
    assert "_setVal=v=>update(sel," in index_html, "kein value-Schreibpfad (_setVal)"


def test_createcustom_kombiniert_typisierte_felder(index_html):
    assert "const items=[..._plain,...typedItems];" in index_html, (
        "createCustom kombiniert einfache + typisierte Items nicht"
    )
    assert "setTypedItems([]);" in index_html, "typedItems wird nach Erstellen nicht zurückgesetzt"


def test_builder_vorhanden(index_html):
    assert "const _addTyped=" in index_html, "Feld-Builder _addTyped fehlt"
    assert "const [typedItems,setTypedItems]=" in index_html, "typedItems-State fehlt"
