"""v3.9.289 (B-011) — ChefDashboard-Widget 'Abwesend naechste Woche' liest die ECHTE flache abs-Form.

Regressions-Schutz: das Widget war vorher kaputt, weil es abs als
    { worker_id: {entries:[{von,bis,typ}]} }
annahm. Die echte Form (Build ~Z.4949 / Set ~Z.14779) ist FLACH:
    { 'Name_Datum': {type, date, status, hours} }   # z.B. 'Pinger_2026-08-21'
Diese Tests fangen ein Zurueckfallen auf die alte kaputte Datenform.
"""


def _nextweekabs_block(index_html):
    """Schneidet exakt den nextWeekAbs-useEffect-Block aus (Kommentar -> setNextWeekAbs(hits))."""
    start = index_html.index("C.4 Abwesend")
    end = index_html.index("setNextWeekAbs(hits)", start) + len("setNextWeekAbs(hits)")
    return index_html[start:end]


def test_nextweekabs_uses_flat_name_date_form(index_html):
    block = _nextweekabs_block(index_html)
    # VORHANDEN: echte flache NAME_DATE-Form
    assert "lastIndexOf('_')" in block, "Name muss aus NAME_DATE-Key abgeleitet werden"
    assert "status==='abgelehnt'" in block, "abgelehnte Eintraege muessen uebersprungen werden"
    assert "e.date" in block, "Datum muss aus dem flachen Objekt (e.date) gelesen werden"


def test_nextweekabs_no_old_broken_form(index_html):
    block = _nextweekabs_block(index_html)
    # ABWESEND: die alte kaputte worker_id->{entries:[]}-Annahme darf NICHT zurueckkommen
    assert "abs[wid].entries" not in block, "alte {entries}-Annahme zurueckgefallen"
    assert "monteure.find(w=>w.id===wid)" not in block, "alte worker_id-Namensaufloesung zurueckgefallen"
