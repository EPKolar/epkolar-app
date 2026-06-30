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
    # v3.9.596: Merge REDUZIERT auf die frische Server-apprMap (stale 'ausstehend' aus dem
    # IndexedDB-Cache, das der Server nicht bestaetigt, verschwindet → kein Phantom nach Re-Login).
    # AUSGENOMMEN un-gesyncte lokale Entscheidungen (pending SQ POST/PUT in _v544PendingAbsKeep).
    assert "const m={...apprMap};_v544PendingAbsKeep.forEach(k=>{const pv=(prev||{})[k];if(pv!==undefined)m[k]=pv;});return m;" in index_html, (
        "v3.9.596: Merge reduziert auf Server-apprMap (stale ausstehend droppt), pending-keep ausgenommen"
    )
    assert "setAbsApprovals(prev=>({...apprMap,...prev}))" not in index_html, (
        "alter prev-wins-Merge (stale 'ausstehend' gewinnt ueber Server-genehmigt) darf nicht zurueckkehren"
    )
