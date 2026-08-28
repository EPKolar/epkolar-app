"""
Nachtlauf-Hunt v3.9.850 — Mängel-Defect-Pin-Nummern on-screen stabil + PDF-deckungsgleich.

Ticket-Pins zeigen die kanonische `_ticketNr` (:17263); Mängel-Defect-Pins hatten
dort keinen Eintrag und fielen auf den gefilterten Loop-Index `g.i` (:17090/:16988)
zurück → bei aktivem Toolbar-Filter änderten sich ihre Nummern und kollidierten mit
Ticket-Nummern; zudem wich die On-Screen-Nummer von der Plan-Report-PDF ab (die
nummeriert stabil über `planTickets.concat(_defectPins)` :16433). Fix: `_ticketNr`
nummeriert Defect-Pins NACH den planTickets.

v3.9.877 NACHGEZOGEN — nicht abgeschwaecht: Die Nummernbasis heisst jetzt `_nrBase`
statt `planTickets`, weil `planTickets` fuer Feldrollen auf die EIGENEN Tickets
gefiltert war (allTickets -> t.assignee===_vpMid). Der Monteur zaehlte 1..k ueber
seine Tickets, das Buero 1..N ueber alle - dieselbe "Pin 14" meinte zwei verschiedene
Pins. Diese drei Riegel pruefen weiterhin genau dasselbe Verhalten (Defect-Pins nach
den Ticket-Pins, useMemo-Abhaengigkeit, 1..N-Nummerierung), nur gegen die neue,
rollenunabhaengige Basis. Sie hatten den alten WORTLAUT festgeschrieben, nicht die
Eigenschaft - genau das Muster, das in diesem Repo schon dreimal einen Fehler
konserviert hat.
"""


def test_ticketnr_nummeriert_defectpins(index_html):
    assert "_defectPins.forEach((d,i)=>{if(m[d.id]==null)m[d.id]=_nrBase.length+i+1;});" in index_html


def test_ticketnr_hat_defectpins_dependency(index_html):
    # der useMemo muss auf _defectPins reagieren, sonst stale Nummern
    assert "return m;},[_nrBase,_defectPins]);" in index_html


def test_ticket_nummerierung_unveraendert(index_html):
    # planTickets werden weiterhin 1..N nummeriert (Ticket-Nummern byte-identisch)
    assert "_nrBase.forEach((t,i)=>{m[t.id]=i+1;});" in index_html


def test_pdf_nummerierung_bleibt_quelle(index_html):
    # die PDF-Nummerierung (Deckungs-Referenz) bleibt: Index ueber die uebergebenen platzierten Pins
    assert "const _nrById={};_pins.forEach((t,i)=>{_nrById[t.id]=i+1;});" in index_html
