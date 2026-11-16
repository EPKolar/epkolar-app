"""v3.9.138 — PlanRadar Phase 2: Quick-Edit-Popup beim Pin-Klick.

Plaene Stufe 1 NACHGEZOGEN: der Auftrag ersetzt Schnellfenster + Detail-Blatt durch EIN Unterblatt
(QuickEditPin bleibt der Name). Weggefallen sind genau die Dinge, die der Auftrag aendert: die
Auswahlliste "Status" + "Speichern"-Knopf (jetzt Status-Knoepfe, die sofort speichern), die Emoji
"📋 Öffnen"/"💾 Speichern" (jetzt "Ganzes Ticket", Linien-Ikone) und das Schliessen nach dem Speichern
(das Blatt bleibt offen). Geprueft wird weiterhin: Felder Status/Zustaendig/Frist/Prioritaet, Speichern
ueber onSave -> updateTicket, "Ganzes Ticket" oeffnet das volle Ticket und schliesst das Blatt.
"""


def test_quickedit_component_exists(index_html):
    # v3.9.180: onComment (Journal) + v3.9.181: onPhotos (Foto-Grid) ergänzt
    # v3.9.410: isAdmin/isMtField/vpMid für Self-Assign-Klemme ergänzt
    # v3.9.829: statusOptions/hideJournal ergänzt
    # Stufe 1: nr (Pin-Nummer) + layers (Ebenenname) nur zur Anzeige
    assert "function QuickEditPin({ticket, monteure, isAdmin, isMtField, vpMid, onSave, onOpen, onClose, onComment, onPhotos, statusOptions, hideJournal, nr, layers}) {" in index_html
    # Schnellbearbeitungs-Felder: Status als Knoepfe, Zustaendig/Frist/Prioritaet als Zeilen
    assert "'aria-label':\"Status – speichert sofort\"" in index_html
    assert '_zeile("Zuständig",' in index_html
    assert '_zeile("Frist",' in index_html
    assert '_zeile("Priorität",' in index_html
    # Sofort-Speichern: Aenderung zaehlt hoch, der Effekt ruft _save; ohne Aenderung nie
    assert "_react.useEffect.call(void 0, () => { if(_sp) _save(); }, [_sp]);" in index_html
    assert "const _setz = (setter, wert, alt) => { if(wert === alt) return; setter(wert); _setSp(n => n + 1); };" in index_html
    # "Ganzes Ticket" statt "📋 Öffnen"; kein "💾 Speichern"-Knopf mehr im Blatt
    assert 'hideJournal ? "Im Mängel-Reiter bearbeiten" : "Ganzes Ticket"' in index_html


def test_quickedit_wired(index_html):
    assert "const [quickTicket,setQuickTicket]=_react.useState.call(void 0, null);" in index_html
    # Pin-Klick öffnet das Blatt (Ticket-Pins); Defect-Pins oeffnen dasselbe Blatt mit 3 Status.
    assert "setSelTicket(t);setQuickTicket(t);" in index_html
    assert "onPinClick: t=>{" in index_html
    # Speichern geht ueber updateTicket; das Blatt bleibt offen und folgt dem Datenstand
    assert "React.createElement(QuickEditPin, { ticket: quickTicket, monteure: monteure, isAdmin: isAdmin, isMtField: _vpIsField, vpMid: _vpMid," in index_html
    assert "onSave: u=>{updateTicket(u);}" in index_html
    assert "if(_l&&_l!==quickTicket)setQuickTicket(_l);},[planData.tickets]);" in index_html
    assert 'onOpen: ()=>{setSelTicket(quickTicket);setSideMode("detail");setShowSidebar(true);setQuickTicket(null);}' in index_html
