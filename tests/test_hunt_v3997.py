"""v3.9.107 — Bug-Hunt-Welle 1 (Agententeam-Findings, adversarial verifiziert).

Statische Regressions-Guards für die gefixten Bugs. Reine Presence-Checks.
"""


def test_juprowa_scheintyp_string_compare(index_html):
    # AK_SCHEINTYP kommt numerisch (wie AK_AUFART/AK_AUFSTATUS) → String() vor === nötig.
    assert 'String(jws.AK_SCHEINTYP)==="3"' in index_html, (
        "JUPROWA scheintyp muss String(AK_SCHEINTYP) vergleichen (sonst Regie→Service)"
    )
    assert 'jws.AK_SCHEINTYP==="3"?"regie"' not in index_html, "alter numerischer Vergleich darf weg sein"


def test_kontingent_save_gated_isadmin(index_html):
    # Speichern-Button muss isAdmin (admin/PL/urlaub_edit) nutzen, nicht role==="admin".
    assert 'isAdmin&&React.createElement(\'button\', { onClick: ()=>{if(editKontingent)' in index_html, (
        "Kontingent-Speichern muss auf isAdmin gegated sein (sonst PL/urlaub_edit editiert ohne Speichern)"
    )


def test_uebersicht_gated(index_html):
    assert 'subView==="uebersicht"&&isAdmin&&' in index_html, (
        "AbsView-Übersicht (alle MA-Salden) muss isAdmin-gated sein (war per Swipe für Monteure offen)"
    )


def test_abstabids_clamped_for_nonadmin(index_html):
    assert 'const absTabIds=isAdmin?["kalender","antraege","uebersicht","timeline"]:["kalender"]' in index_html, (
        "absTabIds muss für Nicht-Admin auf kalender geklemmt sein (Swipe-Schutz)"
    )


def test_fahrzeug_labels_use_visiblefz(index_html):
    assert 'printLabels(visibleFz.filter(f=>f.status!=="stillgelegt")' in index_html, (
        "Fahrzeug-Labels müssen visibleFz nutzen (Monteur druckte sonst ganze Flotte)"
    )


def test_authretry_offline_guard(index_html):
    assert '_isAuthErr(r.status)&&navigator.onLine!==false' in index_html, (
        "_authRetry darf offline keinen Auth-Fehler/Logout-Toast auslösen"
    )


def test_silent_reauth_counter_reset(index_html):
    assert 'sessionStorage.removeItem("_silent_reauth_count")' in index_html, (
        "_silent_reauth_count muss bei erfolgreichem Login/Refresh zurückgesetzt werden"
    )


def test_deadline_parsed_local(index_html):
    assert 'new Date(f.pickerl+"T00:00:00")' in index_html, "Pickerl-Deadline lokal parsen"
    assert 'new Date(f.naechstService+"T00:00:00")' in index_html, "Service-Deadline lokal parsen"
    assert 'new Date(t.datum+"T00:00:00")' in index_html, "Termin-Deadline lokal parsen"


def test_tog_delete_removes_approval(index_html):
    # Beim Abwählen muss die Approval-Eintragung entfernt werden (kein Orphan).
    assert 'if(isDelete){setApprovals(p=>{const _c={...p};delete _c[k];return _c;});' in index_html, (
        "tog-Delete muss approvals[k] entfernen (sonst Anträge-offen-Zähler zu hoch)"
    )
