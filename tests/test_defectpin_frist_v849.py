"""
Nachtlauf-Hunt v3.9.849 — Defect-Pin-Schnellbearbeitung löschte Frist + Monteur
(DATENVERLUST, Regression aus v3.9.829).

`_defectPins`(:17262) projizierte den Mangel aufs Pin-Shape OHNE dueDate/assignee.
QuickEditPin seedt aber `due=ticket.dueDate` (:17124) und `asg=ticket.assignee`
(:17123) → beide leer → onSave(:17400) schrieb `frist:""`/`zugewiesen:""` zurück.
Ein platzierter Mangel MIT Frist/Monteur verlor beide, sobald jemand den Pin
antippte und nur den Status änderte. Fix: _defectPins reicht die Felder durch.
"""
import re


def test_defectpins_reicht_frist_und_zugewiesen_durch(index_html):
    # die Projektion traegt jetzt dueDate + assignee aus den Mangel-Feldern
    assert 'dueDate:m.frist||"",assignee:m.zugewiesen||m.worker||"",_isDefectPin:true' in index_html


def test_quickeditpin_seed_unveraendert(index_html):
    # QuickEditPin seedt weiterhin aus ticket.dueDate/ticket.assignee — jetzt gefuellt
    assert "useState.call(void 0, ticket.assignee || \"\")" in index_html
    assert 'useState.call(void 0, ticket.dueDate || ticket.due_date || "")' in index_html


def test_onsave_schreibt_weiterhin_kanonische_felder(index_html):
    # onSave-Verhalten bleibt (schreibt frist/zugewiesen aus dem — jetzt korrekt geseedeten — Formular)
    assert 'method:"PUT",body:{status:_dst,prio:_prio,frist:_frist,zugewiesen:_zug}' in index_html
    assert 'const _frist=u.dueDate||"";const _zug=u.assignee||"";' in index_html
