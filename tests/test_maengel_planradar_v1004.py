# -*- coding: utf-8 -*-
"""v3.9.1004 - Maengel besser als PlanRadar (erste Ausbaustufe).

A  Mangel per TIPP auf den Plan setzen (vorher blind 50/50 auf den ersten Plan).
B  Foto zuerst: "📷 Mangel per Foto" -> Kamera -> kurzes Formular -> Speichern.
   Das Foto geht NUR ueber captureAndQueue (PhotoQ/Storage), nie als Base64 in
   die Haupt-Warteschlange.
C  Zuweisungs-Nachricht (mangel_assigned) beim Anlegen, Sammel-Zuweisen und am
   Mangel-Pin - eine je Empfaenger, nie an sich selbst.

Jeder Riegel prueft eine Eigenschaft; wo es geht, mit Umkehrprobe.
"""
import io
import json
import re
import sys
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL / "tests"))
from conftest import _extract_fn, run_node_snippet  # noqa: E402


@pytest.fixture(scope="module")
def src():
    return io.open(str(WURZEL / "index.html"), encoding="utf-8", newline="").read()


def _fn(src, name, code_only=False):
    b = _extract_fn(src, name)
    assert b, "%s nicht gefunden - das ist rot, nicht gruen." % name
    if code_only:
        # accept: "image/*" oeffnet fuer einen naiven Filter einen Kommentar und
        # verschluckt Code bis zum naechsten */ - vorher neutralisieren.
        b = b.replace('"image/*"', '"image/STERN"')
        b = re.sub(r"/\*.*?\*/", "", b, flags=re.S)
    return b


def _zwischen(text, anfang, ende):
    i = text.find(anfang)
    assert i >= 0, "Anker fehlt: %s" % anfang
    j = text.find(ende, i + len(anfang))
    assert j > i, "Ende fehlt: %s" % ende
    return text[i:j]


# ── A ─────────────────────────────────────────────────────────────────────

def _setzt_blind_mittig(rumpf):
    return bool(re.search(r"x:\s*50\s*,\s*y:\s*50", rumpf))


def test_a_kein_blindes_50_50_mehr(src):
    vm = _fn(src, "VMang", code_only=True)
    place = _zwischen(vm, "const _placeOnPlan=", "const _mgPosSchreiben=")
    assert not _setzt_blind_mittig(place), "Mangel landet wieder blind mittig auf dem Plan."
    assert "setMgPlanZiel({mid:m.id})" in place


def test_a_umkehrprobe_altes_mittig():
    alt = "{...x,x:50,y:50,planId:_pl.id,plan_id:_pl.id,page:1}"
    assert _setzt_blind_mittig(alt)


def test_a_dialog_nutzt_den_ticket_viewer_im_tippmodus(src):
    dlg = _fn(src, "MangelPlanSetzen", code_only=True)
    assert "React.createElement(PlanViewerCanvas," in dlg, "Kein zweiter Viewer - derselbe wie beim Ticket."
    assert "pinMode: true" in dlg
    assert "onPlanClick: pos=>" in dlg
    assert "ReactDOM.createPortal(" in dlg, "Overlay muss aus sticky/transform-Vorfahren heraus."
    # Bestaetigen liefert Prozent + Seite + Plan
    assert re.search(r"onSetzen\(\{x:pend\.x,y:pend\.y,planId:plan\.id,page:", dlg)


def test_a_position_in_vorhandene_spalten(src):
    vm = _fn(src, "VMang", code_only=True)
    schreib = _zwischen(vm, "const _mgPosSchreiben=", "const _mgVomPlan=")
    assert 'url:"/api/defects/"+mid,method:"PUT"' in schreib
    assert "plan_id:pos.planId" in schreib and "page:pos.page||1" in schreib
    # gespiegeltes Plan-Ticket wandert mit
    assert 'url:"/api/tickets/"+mid,method:"PUT"' in schreib
    # Leser: _mapDefect liefert x/y/plan_id/page zurueck (sonst versagt alles lautlos nach dem Reload)
    md = _fn(src, "_mapDefect", code_only=True)
    for feld in ("x:(d.x==null?null:d.x)", "y:(d.y==null?null:d.y)", "plan_id:d.plan_id", "page:d.page"):
        assert feld in md


def test_a_neuer_mangel_traegt_position_beim_anlegen(src):
    vm = _fn(src, "VMang", code_only=True)
    add = _zwischen(vm, "const add=()=>", "const _DEF2TICKET_ST=")
    assert re.search(r'url:"/api/defects",method:"POST",body:\{[^;]*\(_pos\?\{x:_pos\.x,y:_pos\.y,plan_id:_pos\.planId', add)


def test_a_nur_plaene_dieses_projekts(src):
    vm = _fn(src, "VMang", code_only=True)
    assert "const _mgPlaene=((planData&&planData.plans)||[]).filter(pl=>pl&&pl.pid===p.id&&!pl.archived);" in vm


# ── B ─────────────────────────────────────────────────────────────────────

def test_b_foto_knopf_oeffnet_direkt_die_kamera(src):
    vm = _fn(src, "VMang", code_only=True)
    i = vm.find("\"📷 Mangel per Foto\", React.createElement('input'")
    assert i > 0
    nah = vm[i:i + 400]
    assert 'capture: "environment"' in nah and "onChange: _mgFotoZuerst" in nah
    zuerst = _zwischen(vm, "const _mgFotoZuerst=", "// Load photos from server")
    assert "setMgFotoAuf(true)" in zuerst


def test_b_textfeld_hat_den_fokus_und_speichern_nutzt_add(src):
    vm = _fn(src, "VMang", code_only=True)
    form = _zwischen(vm, ", mgFotoAuf&&React.createElement('div', { style: {...CC()", "React.createElement('span', { style: LL()}, \"Frist\")")
    assert "autoFocus: true" in form
    assert "_mgWerFeld()" in form, "Verantwortlich muss dasselbe Feld sein wie im alten Formular."
    assert "onClick: ()=>{if(mgFotoLaeuft>0)return;add();}" in vm


def test_b_kein_base64_in_der_hauptwarteschlange(src):
    vm = _fn(src, "VMang", code_only=True)
    add = _zwischen(vm, "const add=()=>", "const _DEF2TICKET_ST=")
    assert "images:_ohneVorschau?[]:" in add, "Foto-zuerst schickt wieder Bilddaten in die Defect-Zeile."
    assert "const _ohneVorschau=mgFotoAuf;" in add
    assert 'captureAndQueue(ph.file,"defect",mid,p.id,"Mangel-Foto")' in add


def test_b_frist_vorschlag_sieben_tage(src):
    vm = _fn(src, "VMang", code_only=True)
    zuerst = _zwischen(vm, "const _mgFotoZuerst=", "// Load photos from server")
    assert "setFrist(_mgFristVorschlag())" in zuerst and 'setWorker("")' in zuerst


# ── C ─────────────────────────────────────────────────────────────────────

def _lauf(node_exe, fn_src, users, cur, zuweisungen):
    js = (
        "var window={_allUsers:%s,_curUser:function(){return %s;},calls:[]};"
        "window.__pushNotif=function(t,ti,b,u,k){window.calls.push([t,ti,b,u]);};"
        "%s\nvar n=_mgZuweisungMelden(%s,'Testhaus');"
        "console.log(JSON.stringify({n:n,calls:window.calls}));"
    ) % (json.dumps(users), json.dumps(cur), fn_src, json.dumps(zuweisungen))
    return json.loads(run_node_snippet(node_exe, js))


USERS = [{"id": "u1", "monteurId": "w1"}, {"id": "u2", "monteurId": "w2"}, {"id": "ich", "monteurId": "w9"}]


def test_c_eine_nachricht_je_empfaenger(node_exe, src):
    fn = _fn(src, "_mgZuweisungMelden")
    r = _lauf(node_exe, fn, USERS, {"id": "ich"}, [
        {"wid": "w1", "name": "A"}, {"wid": "w1", "name": "B"}, {"wid": "w1", "name": "C"},
        {"wid": "w2", "name": "D"}])
    assert r["n"] == 2
    empf = sorted(c[3][0] for c in r["calls"])
    assert empf == ["u1", "u2"]
    an_u1 = [c for c in r["calls"] if c[3] == ["u1"]][0]
    assert an_u1[0] == "mangel_assigned"
    assert "3 Mängel" in an_u1[1] and "Testhaus" in an_u1[2]


def test_c_nie_an_sich_selbst_und_nicht_ins_leere(node_exe, src):
    fn = _fn(src, "_mgZuweisungMelden")
    r = _lauf(node_exe, fn, USERS, {"id": "ich"}, [
        {"wid": "w9", "name": "selbst"}, {"wid": "w_unbekannt", "name": "x"}, {"wid": "", "name": "leer"}])
    assert r["n"] == 0 and r["calls"] == []


def test_c_umkehrprobe_ohne_selbstsperre_waere_rot(node_exe, src):
    fn = _fn(src, "_mgZuweisungMelden").replace("||au.id===cu.id", "")
    assert fn != _fn(src, "_mgZuweisungMelden"), "Mutation hat nicht gegriffen."
    r = _lauf(node_exe, fn, USERS, {"id": "ich"}, [{"wid": "w9", "name": "selbst"}])
    assert r["n"] == 1, "Die Selbst-Probe kann nicht anschlagen."


def test_c_alle_zuweisungswege_melden(src):
    vm = _fn(src, "VMang", code_only=True)
    add = _zwischen(vm, "const add=()=>", "const _DEF2TICKET_ST=")
    assert "if(_effWorker)_mgZuweisungMelden(" in add
    bulk = _zwischen(vm, "const _bulkApply=", "const delM=")
    # EIN Aufruf, ausserhalb der Schleife ueber die Maengel
    assert bulk.count("_mgZuweisungMelden(") == 1
    assert bulk.find("_mgZuweisungMelden(") < bulk.find("ids.forEach(id=>{")
    vp = _fn(src, "VPlan", code_only=True)
    qd = _zwischen(vp, "quickDefect&&subView===\"viewer\"", "onOpen:")
    assert "_mgZuweisungMelden(" in qd
