"""v3.9.138 — PlanRadar Phase 2: Quick-Edit-Popup beim Pin-Klick."""


def test_quickedit_component_exists(index_html):
    # v3.9.180: onComment (Journal) + v3.9.181: onPhotos (Foto-Grid) ergänzt
    # v3.9.410: isAdmin/isMtField/vpMid für Self-Assign-Klemme ergänzt
    # v3.9.829: statusOptions/hideJournal ergänzt (Defect-Pins wiederverwenden das Popup mit
    #           begrenzter Status-Liste + ohne Journal) — Defaults = unverändertes Ticket-Verhalten.
    assert "function QuickEditPin({ticket, monteure, isAdmin, isMtField, vpMid, onSave, onOpen, onClose, onComment, onPhotos, statusOptions, hideJournal}) {" in index_html
    # Schnellbearbeitungs-Felder
    assert 'React.createElement(\'label\', {style:LL()}, "Status")' in index_html
    assert 'React.createElement(\'label\', {style:LL()}, "Zuständig")' in index_html
    assert 'React.createElement(\'label\', {style:LL()}, "Erledigen bis")' in index_html
    assert 'React.createElement(\'label\', {style:LL()}, "Priorität")' in index_html
    # Öffnen + Speichern Buttons
    assert '"📋 Öffnen"' in index_html and '"💾 Speichern"' in index_html


def test_quickedit_wired(index_html):
    assert "const [quickTicket,setQuickTicket]=_react.useState.call(void 0, null);" in index_html
    # Pin-Klick öffnet Quick-Popup statt vollem Detail (Ticket-Pins).
    # v3.9.280: Defect-Pins (_isDefectPin) werden vorab abgefangen (Info-Toast); die Quick-Edit-
    # Verdrahtung für echte Tickets bleibt erhalten — robust auf die Kern-Verdrahtung prüfen.
    assert "setSelTicket(t);setQuickTicket(t);" in index_html
    assert "onPinClick: t=>{" in index_html
    # Popup-Render + onSave→updateTicket, onOpen→volles Detail
    # v3.9.410: isAdmin/isMtField/vpMid-Props für Self-Assign-Klemme durchgereicht
    assert "React.createElement(QuickEditPin, { ticket: quickTicket, monteure: monteure, isAdmin: isAdmin, isMtField: _vpIsField, vpMid: _vpMid, onSave: u=>{updateTicket(u);setQuickTicket(null);}" in index_html
    assert 'onOpen: ()=>{setSelTicket(quickTicket);setSideMode("detail");setShowSidebar(true);setQuickTicket(null);}' in index_html
