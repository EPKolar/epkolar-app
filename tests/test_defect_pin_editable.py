"""
PlanRadar ② — VMang-Defect-Pins am Plan editierbar (v3.9.829).

Vorher: Klick auf einen Mängel-Pin (`_isDefectPin`) zeigte nur einen Info-Toast
("Bearbeitung im Mängel-Tab") — der Mangel war am Plan nur ein Lese-Pin, während
Plan-Tickets voll editierbar sind. Das war die auffälligste PlanRadar-UX-Naht.

Jetzt: der Klick öffnet dasselbe QuickEditPin-Popup wie bei Tickets. Speichern
schreibt die KANONISCHEN defects-Felder (status/prio/frist/zugewiesen) und mappt
den Ticket-Status auf MANGEL_ST zurück. QuickEditPin bekam zwei OPTIONALE Props
(statusOptions, hideJournal) mit Defaults = unveraendertes Ticket-Verhalten.
"""
import re


def test_defect_pin_klick_oeffnet_quickedit_statt_toast(index_html):
    # der _isDefectPin-Zweig ruft jetzt setQuickDefect, NICHT mehr nur einen Info-Toast
    assert "if(t&&t._isDefectPin){setQuickDefect(t);return;}" in index_html, (
        "Defect-Pin-Klick öffnet nicht setQuickDefect"
    )


def test_quickdefect_state_existiert(index_html):
    assert "const [quickDefect,setQuickDefect]=" in index_html, "quickDefect-State fehlt"


def test_quickedit_akzeptiert_neue_props(index_html):
    m = re.search(r"function QuickEditPin\(\{([^}]*)\}", index_html)
    assert m, "QuickEditPin-Signatur nicht gefunden"
    sig = m.group(1)
    assert "statusOptions" in sig and "hideJournal" in sig, (
        "QuickEditPin nimmt statusOptions/hideJournal nicht entgegen"
    )
    # Status-Dropdown nutzt die optionale Liste mit Fallback aufs Ticket-Verhalten
    assert "(statusOptions||Object.entries(TICKET_STATUS))" in index_html, (
        "Status-Dropdown nutzt statusOptions-Fallback nicht"
    )
    # Journal wird bei hideJournal ausgeblendet
    assert "(!hideJournal) && React.createElement" in index_html, (
        "hideJournal blendet das Journal nicht aus"
    )


def test_defect_save_schreibt_kanonische_felder(index_html):
    # der quickDefect-onSave schreibt via SQ.push auf /api/defects/ mit den kanonischen Feldern
    i = index_html.find("quickDefect&&subView===")
    assert i != -1, "quickDefect-Render nicht gefunden"
    block = index_html[i:i + 1600]
    assert 'SQ.push({url:"/api/defects/"+u.id,method:"PUT"' in block, "kein defects-PUT im onSave"
    for feld in ("status:_dst", "prio:_prio", "frist:_frist", "zugewiesen:_zug"):
        assert feld in block, f"kanonisches Feld {feld} fehlt im defects-PUT"


def test_status_rueckmap_auf_mangel_st(index_html):
    i = index_html.find("quickDefect&&subView===")
    block = index_html[i:i + 1600]
    # v3.9.831: die Rückmap wurde in die Modul-Konstante _TICKET2MANGEL_ST konsolidiert
    # (war vorher inline `_rev={...}`). Der onSave verweist jetzt darauf; die Korrektheit
    # der Map (sauberer Round-Trip, gültige MANGEL_ST-Werte) prüft test_status_map_consolidation.
    assert "_dst=_TICKET2MANGEL_ST[u.status]||\"offen\"" in block, (
        "Status-Rückmap ticket->mangel (_TICKET2MANGEL_ST) im onSave nicht verdrahtet"
    )


def test_statusoptions_nur_drei_mappbare(index_html):
    i = index_html.find("quickDefect&&subView===")
    block = index_html[i:i + 1600]
    assert 'statusOptions: [["offen",TICKET_STATUS.offen],["in_bearbeitung",TICKET_STATUS.in_bearbeitung],["erledigt",TICKET_STATUS.erledigt]]' in block, (
        "Defect-Popup bietet nicht genau die 3 mappbaren Status an"
    )
    assert "hideJournal: true" in block, "Defect-Popup blendet das Journal nicht aus"
