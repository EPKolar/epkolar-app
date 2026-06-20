"""v3.9.479 — Bug-Hunt-Folgefixes: Formular/Regie-Löschen Owner-Gate, RLS-Label plans, _jp/_jo-Warn."""
import pathlib

SRC = pathlib.Path(__file__).resolve().parent.parent / "index.html"
HTML = SRC.read_text(encoding="utf-8")


def test_useeditable_del_owner_gate():
    assert "Monteure können nur eigene Formulare löschen" in HTML, "useEditable.del Owner-Gate fehlt"


def test_fregie_dele_owner_gate_and_created_by():
    assert "Monteure können nur eigene Regieberichte löschen" in HTML, "FRegie.delE Owner-Gate fehlt"
    # Regie-POST muss created_by mitschreiben, sonst kann nicht gegated werden
    assert 'form_type:"regie",project_id:p.id,data:entry,created_by:' in HTML, "Regie-POST schreibt created_by nicht"


def test_rls_label_plans_added():
    assert 'plans:"Plan-Änderung"' in HTML, "plans-RLS-Label fehlt"
    # Begründung dokumentiert, warum defects/tickets bewusst NICHT gelistet sind (UPDATE=authenticated)
    assert "bewusst NICHT gelistet" in HTML


def test_jp_jo_warn_on_corrupt_json():
    assert "[_jp] korruptes JSON" in HTML, "_jp warnt nicht bei Parse-Fehler"
    assert "[_jo] korruptes JSON" in HTML, "_jo warnt nicht bei Parse-Fehler"
