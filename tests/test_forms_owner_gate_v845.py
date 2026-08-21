"""
Nachtlauf-Hunt v3.9.845 — Owner-Delete-Gate für Formulare/Regie reaktiviert.

Die Gates del(:15590)/delE(:15637) lassen Field-User nur EIGENE Einträge löschen
(`tgt.created_by===monteurId`), Staff (admin/PL/Büro) alles. Aber der kanonische
Forms-Load(:7809) pushte nur `{id,pid,...fd}` — `created_by` (die Owner-Spalte)
fiel weg → `_ownF` immer false → Monteure konnten NIE eigene Formulare/Regie-
berichte löschen (fail-safe, aber tote Funktion). Fix: created_by im Load
durchreichen + am lokalen entry beim Anlegen setzen (In-Session; Edit erbt vom
Original → kein Clobber).
"""


def test_load_reicht_created_by_durch(index_html):
    assert 'grouped[t].push({id:f.id,pid:f.project_id,...fd,created_by:f.created_by});' in index_html
    # der alte, created_by-lose Push ist weg
    assert 'grouped[t].push({id:f.id,pid:f.project_id,...fd});' not in index_html


def test_lokales_entry_setzt_created_by_bei_anlegen(index_html):
    # generischer Forms-save UND Regie-saveE: gleicher Guard, kein Clobber auf Edit
    anchor = 'if(!entry.created_by)entry.created_by=_isEdit?((saved[editIdx]&&saved[editIdx].created_by)||""):((window._curUser&&window._curUser()&&window._curUser().monteurId)||"");'
    assert index_html.count(anchor) == 2, "created_by-Guard muss in beiden save-Funktionen (Forms + Regie) stehen"


def test_gates_pruefen_weiterhin_created_by(index_html):
    # die Schutzriegel selbst bleiben unveraendert scharf (verneinender Riegel)
    assert index_html.count('const _ownF=!!(tgt&&tgt.created_by&&_cu.monteurId&&tgt.created_by===_cu.monteurId);') == 2
