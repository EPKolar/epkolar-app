"""v3.9.473 (#6) — Plan-Versionierung (Revision-Upload + Pin-Migration + Archiv-Filter).
Statische Quell-Checks gegen index.html."""
import pathlib

SRC = pathlib.Path(__file__).resolve().parent.parent / "index.html"
HTML = SRC.read_text(encoding="utf-8")


def test_mapplan_carries_version_archived():
    assert "version:p.version!=null?p.version:1" in HTML, "_mapPlan trägt version nicht"
    assert "archived:!!(p.archived)" in HTML, "_mapPlan trägt archived nicht"
    assert "replacesPlanId:p.replacesPlanId||p.replaces_plan_id" in HTML


def test_plans_memo_hides_archived_by_default():
    assert "(showArchivedPlans||!pl.archived)" in HTML, "archivierte Pläne werden nicht standardmäßig ausgeblendet"


def test_revision_commit_and_pin_migration():
    assert "const _commitRevision=" in HTML, "_commitRevision fehlt"
    assert "const _migrateRevisionPins=" in HTML, "Pin-Migration fehlt"
    # neue Revision: version+1, verweist auf Vorgänger, alte wird archiviert
    assert "version:(old.version||1)+1" in HTML
    assert "replaces_plan_id:old.id" in HTML
    assert 'method:"PUT",body:{archived:true}' in HTML, "alte Version wird nicht archiviert"
    # Pins (Tickets + Defects) wandern auf die neue plan_id
    assert "/api/tickets/" in HTML and "/api/defects/" in HTML


def test_revision_trigger_button_admin_only():
    assert "const triggerRevision=(pl)=>{if(!isAdmin)return;" in HTML
    assert "🔄 Revision" in HTML
