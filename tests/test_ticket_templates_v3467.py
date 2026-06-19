"""v3.9.467 — PlanRadar Ticket-Vorlagen (1-Klick-Prefill).
Statische Quell-Checks gegen index.html (wie die übrige Test-Suite)."""
import re, pathlib

SRC = pathlib.Path(__file__).resolve().parent.parent / "index.html"
HTML = SRC.read_text(encoding="utf-8")


def test_ticket_templates_const_defined():
    assert "const TICKET_TEMPLATES=[" in HTML, "TICKET_TEMPLATES-Konstante fehlt"


def test_apply_template_handler_defined():
    assert "const _applyTpl=(tv)=>{" in HTML, "_applyTpl-Handler fehlt"
    # Position/Plan bleiben (setzt layer+gewerk, behält title bei leer)
    assert "layer:lyr,gewerk:lyr" in HTML


def test_template_chips_rendered_in_new_ticket_form():
    # v3.9.472: Chips rendern jetzt aus tplList (system_config-geladen, Fallback = TICKET_TEMPLATES-Defaults)
    assert "tplList.map((tv,ti)=>React.createElement('button'" in HTML, \
        "Vorlagen-Chips werden im Neu-Ticket-Formular nicht gerendert"
    assert "onClick: ()=>_applyTpl(tv)" in HTML
    assert "const _saveTpl=async(arr)=>" in HTML, "Admin-Save (_saveTpl) fehlt"


def test_template_types_and_prios_valid():
    block = HTML.split("const TICKET_TEMPLATES=[", 1)[1].split("];", 1)[0]
    valid_types = {"mangel", "aufgabe", "regiebericht", "pruefung", "info", "sicherheit"}
    valid_prios = {"kritisch", "hoch", "mittel", "niedrig"}
    types = set(re.findall(r'type:"([a-z]+)"', block))
    prios = set(re.findall(r'priority:"([a-z]+)"', block))
    assert types, "keine type-Felder in TICKET_TEMPLATES"
    assert types <= valid_types, f"ungueltige Ticket-Typen in Vorlagen: {types - valid_types}"
    assert prios <= valid_prios, f"ungueltige Prioritaeten in Vorlagen: {prios - valid_prios}"
