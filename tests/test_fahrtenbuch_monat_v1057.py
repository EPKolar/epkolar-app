# -*- coding: utf-8 -*-
"""v1057 Bughunt: FahrtenbuchPanel.save haengte die neue Fahrt immer an die
Liste des ANGEZEIGTEN Monats - auch wenn ihr Datum in einem anderen Monat lag.
Summen und XLS-Export ('Fahrtenbuch <Monat>') zaehlten sie dann mit. Leere
RETURNING-Antwort (undefined) machte die Liste kaputt.

Echte Funktion _fbNachSpeichern aus index.html in node + Summenrechnung wie im
Panel; Umkehrprobe mit dem alten Updater [created,...prev].
"""
import json

from conftest import _extract_fn, run_node_snippet


def _summe_js():
    # identisch zur Panel-Rechnung totalKm
    return "const total=l=>l.reduce((s,e)=>s+((e.km_ende||0)-(e.km_start||0)),0);\n"


def test_fahrt_aus_anderem_monat_zaehlt_nicht_mit(node_exe, index_html):
    fn = _extract_fn(index_html, "_fbNachSpeichern")
    assert fn
    js = fn + "\n" + _summe_js() + (
        "const prev=[{id:'a',datum:'2026-11-03',km_start:100,km_ende:150}];\n"
        "const okt={id:'b',datum:'2026-10-31',km_start:150,km_ende:400};\n"
        "const nov={id:'c',datum:'2026-11-05',km_start:400,km_ende:420};\n"
        "const r1=_fbNachSpeichern(prev,okt,okt,'2026-11');\n"
        "const r2=_fbNachSpeichern(prev,nov,nov,'2026-11');\n"
        "const r3=_fbNachSpeichern(prev,undefined,nov,'2026-11');\n"
        "console.log(JSON.stringify({k1:total(r1),n1:r1.length,k2:total(r2),n2:r2.length,"
        "r3ok:r3.every(e=>e&&e.id),n3:r3.length}));"
    )
    out = json.loads(run_node_snippet(node_exe, js))
    assert out == {"k1": 50, "n1": 1, "k2": 70, "n2": 2, "r3ok": True, "n3": 2}, out


def test_umkehrprobe_alter_updater(node_exe):
    js = _summe_js() + (
        "const prev=[{id:'a',datum:'2026-11-03',km_start:100,km_ende:150}];\n"
        "const okt={id:'b',datum:'2026-10-31',km_start:150,km_ende:400};\n"
        "const alt=(p,created)=>[created,...p];\n"
        "const r1=alt(prev,okt);let crash=false;try{alt(prev,undefined).map(e=>e.fahrzeug_id);}catch(e){crash=true;}\n"
        "console.log(JSON.stringify({k1:total(r1),crash:crash}));"
    )
    out = json.loads(run_node_snippet(node_exe, js))
    # alte Logik: November-Summe enthaelt die Oktober-Fahrt (300 statt 50) und undefined stuerzt ab
    assert out == {"k1": 300, "crash": True}, out


def test_panel_nutzt_helfer(index_html):
    st = index_html.index("function FahrtenbuchPanel(")
    seg = index_html[st:st + 12000]
    assert "setEntries(prev=>_fbNachSpeichern(prev,created,item,month));" in seg
    assert "setEntries(prev=>[created,...prev]);" not in seg
