"""v3.9.138 — PlanRadar Phase 2: Quick-Edit-Popup beim Pin-Klick."""


def test_quickedit_component_exists(index_html):
    # v3.9.180: onComment (Journal) + v3.9.181: onPhotos (Foto-Grid) ergänzt
    assert "function QuickEditPin({ticket, monteure, onSave, onOpen, onClose, onComment, onPhotos}) {" in index_html
    # Schnellbearbeitungs-Felder
    assert 'React.createElement(\'label\', {style:LL()}, "Status")' in index_html
    assert 'React.createElement(\'label\', {style:LL()}, "Zuständig")' in index_html
    assert 'React.createElement(\'label\', {style:LL()}, "Erledigen bis")' in index_html
    assert 'React.createElement(\'label\', {style:LL()}, "Priorität")' in index_html
    # Öffnen + Speichern Buttons
    assert '"📋 Öffnen"' in index_html and '"💾 Speichern"' in index_html


def test_quickedit_wired(index_html):
    assert "const [quickTicket,setQuickTicket]=_react.useState.call(void 0, null);" in index_html
    # Pin-Klick öffnet Quick-Popup statt vollem Detail
    assert "onPinClick: t=>{setSelTicket(t);setQuickTicket(t);" in index_html
    # Popup-Render + onSave→updateTicket, onOpen→volles Detail
    assert "React.createElement(QuickEditPin, { ticket: quickTicket, monteure: monteure, onSave: u=>{updateTicket(u);setQuickTicket(null);}" in index_html
    assert 'onOpen: ()=>{setSelTicket(quickTicket);setSideMode("detail");setShowSidebar(true);setQuickTicket(null);}' in index_html
