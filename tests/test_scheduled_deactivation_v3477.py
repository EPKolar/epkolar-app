"""v3.9.477 — Geplante Deaktivierung (Kündigungsfrist).
DB-seitig: users.deactivate_at + login_lookup sperrt ab dem Termin (nicht statisch testbar).
Hier: Frontend-Quell-Checks."""
import pathlib

SRC = pathlib.Path(__file__).resolve().parent.parent / "index.html"
HTML = SRC.read_text(encoding="utf-8")


def test_schedule_handler_defined():
    assert "const scheduleDeactivation=(id,date)=>" in HTML
    assert "deactivate_at:d||null" in HTML, "Termin wird nicht (mit NULL-Aufhebung) persistiert"


def test_mapuser_carries_deactivate_at():
    assert "deactivateAt:((u.deactivateAt||u.deactivate_at" in HTML


def test_reactivate_clears_schedule():
    # Beim Reaktivieren muss deactivate_at=null mitgehen (sonst sperrt login_lookup weiter)
    assert "{active:1,deactivate_at:null}" in HTML, "Reaktivieren löscht den geplanten Termin nicht"


def test_auto_flip_effect_present():
    assert "wegen erreichtem Kündigungstermin deaktiviert" in HTML, "Auto-Deaktivierungs-Effect fehlt"


def test_ui_date_input_and_plan_button():
    assert 'id: "_deactAt_"+selU.id' in HTML, "Datums-Input fehlt im Benutzer-Detail"
    assert "📅 Geplante Deaktivierung (Kündigungsfrist)" in HTML
