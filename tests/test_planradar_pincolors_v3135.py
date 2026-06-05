"""v3.9.135 — PlanRadar Phase 2: zweistufige Pin-Farben (Body=Status, Rand=Zuweisung)."""


def test_two_stage_colors(index_html):
    # Body-Fill = Status (kein Status → weiß)
    assert 'const _hasStatus = !!(ticket.status && TICKET_STATUS && TICKET_STATUS[ticket.status]);' in index_html
    assert 'const fillColor = ticket.color || (_hasStatus ? ts.c : "#ffffff");' in index_html
    # Border-Ring = Zuweisung (offline=orange, zugewiesen=grün, sonst grau)
    # v3.9.137: _asgColor nutzt _isUnsynced (Sync-Queue) statt totem push_pending
    assert 'const _asgColor = _isUnsynced ? "#f97316" : (ticket.assignee ? "#22c55e" : "#9ca3af");' in index_html
    assert '"3px solid "+_asgColor' in index_html


def test_number_readable_on_white(index_html):
    # Nummer dunkel auf weißem (statuslosem) Pin, sonst weiß
    assert 'color:_hasStatus?"#fff":"#111"' in index_html
