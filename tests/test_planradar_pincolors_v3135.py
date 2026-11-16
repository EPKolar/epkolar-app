"""v3.9.135 — PlanRadar Phase 2: zweistufige Pin-Farben (Body=Status, Rand=Zuweisung)."""


def test_two_stage_colors(index_html):
    # Body-Fill = Status (kein Status → weiß)
    assert 'const _hasStatus = !!(ticket.status && TICKET_STATUS && TICKET_STATUS[ticket.status]);' in index_html
    assert 'const fillColor = ticket.color || (_hasStatus ? ts.c : "#ffffff");' in index_html
    # Plaene Stufe 1 NACHGEZOGEN: der Rand war Zuweisung (gruen/grau) bzw. Sync (orange). Der Auftrag
    # verlangt CI-Statusfarben ohne Gruen-als-Status und ohne orangen Rahmen; Gruen hiess am selben Pin
    # zweierlei. Jetzt: Rand weiss bzw. dunkel (ausgewaehlt), "noch nicht synchronisiert" bleibt sichtbar -
    # als GESTRICHELTER Rand. Geprueft wird weiterhin, dass Sync-Zustand und Auswahl am Rand ablesbar sind.
    assert 'const _asgColor = isSelected ? "#141A16" : "#ffffff";' in index_html
    assert '"3px solid "+_asgColor' in index_html
    assert 'borderStyle:_isUnsynced?"dashed":"solid"' in index_html
    assert '"#f97316" : (ticket.assignee ? "#22c55e"' not in index_html


def test_number_readable_on_white(index_html):
    # Nummer dunkel auf weißem (statuslosem) Pin, sonst weiß
    assert 'color:_hasStatus?"#fff":"#111"' in index_html
