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
    # v3.9.435: Merge verfeinert — nur DEFINITIVE lokale Entscheidung (genehmigt/abgelehnt) gewinnt;
    # stale lokales 'ausstehend' weicht dem Server-Status (Fix Phantom-"X Anträge zur Genehmigung").
    # Optimistische ECHTE Approvals (genehmigt/abgelehnt) werden weiterhin NICHT revertiert.
    assert "for(const k in apprMap){const pv=m[k];if(pv!=='genehmigt'&&pv!=='abgelehnt')m[k]=apprMap[k];}return m;" in index_html, (
        "Merge: Server gewinnt, AUSSER prev hat eine definitive lokale Entscheidung"
    )
    assert "setAbsApprovals(prev=>({...apprMap,...prev}))" not in index_html, (
        "alter prev-wins-Merge (stale 'ausstehend' gewinnt ueber Server-genehmigt) darf nicht zurueckkehren"
    )
