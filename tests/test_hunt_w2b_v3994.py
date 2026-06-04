"""v3.9.111 — Bug-Hunt Welle 2b: OFFA-Re-Import-Preserve + Server-Approval-Bridge."""


def test_offa_reimport_preserves_workflow_fields(index_html):
    # commitImport-Update darf scheinstatus/notizen/termine NICHT clobbern.
    assert "const upd={...as};" in index_html, "Re-Import muss eine reduzierte upd-Kopie bauen"
    for f in ["'scheinstatus'", "'prioritaet'", "'notizen'", "'terminBestaetigt'", "'durchgefuehrte'"]:
        assert f in index_html, f"{f} muss aus dem Re-Import-Update-Patch entfernt werden (Datenverlust-Schutz)"
    # Der Update-PUT muss upd nutzen, nicht das volle as
    assert 'method:"PUT",body:upd}' in index_html, "Re-Import-PUT muss upd (reduziert) senden, nicht as"


def test_absences_loader_bridges_approval_status(index_html):
    assert "const absMap={},apprMap={};" in index_html, "Loader muss apprMap aus Server-Status bauen"
    assert 'apprMap[k]=a.status==="genehmigt"?"genehmigt":a.status==="abgelehnt"?"abgelehnt":"ausstehend"' in index_html, (
        "Server-Status muss auf client-Approval gemappt werden"
    )
    # local optimistisch gewinnt (prev nach apprMap)
    assert "setAbsApprovals(prev=>({...apprMap,...prev}))" in index_html, (
        "Merge: Server als Basis, lokale Werte überschreiben (kein Revert optimistischer Approvals)"
    )
