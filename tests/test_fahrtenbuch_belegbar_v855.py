"""
v3.9.855 — Fahrtenbuch: Fahrer nur bei belegbarer Quelle (v846-Nachzieher, rechtssicher).

v846 fixte nur die Anzeige; der Snapshot selbst war unzuverlässig (Write-on-Read
nahm den Fahrzeugfahrer zum ANSEH-Zeitpunkt, nicht Fahrt-Zeitpunkt; Alle-Modus
schrieb gar nichts). Regel jetzt: ein Fahrer wird nur geschrieben/angezeigt, wenn
er zeitlich belegbar ist — sonst leer/"—", NIE der aktuelle Fahrzeugfahrer.
"""
import re
import json
from conftest import run_node_snippet


def _fahrervon_src(index_html):
    m = re.search(r"const _fahrerVon=function\(x\)\{.*?return m\?\(m\.n\|\|''\):'';\s*\};", index_html, re.S)
    assert m, "_fahrerVon nicht gefunden / Struktur geaendert"
    return m.group(0)


# (1) keine zeitlich belegbare Quelle -> fahrer_id bleibt null
def test_write_on_read_setzt_fahrer_id_null(index_html):
    # der Snapshot-Write schreibt keinen erfundenen Fahrer mehr
    assert "fahrer_id:(_fz&&_fz.fahrer)?_fz.fahrer:null" not in index_html
    assert "fahrer_id:null/* v3.9.855" in index_html


# (2)+(3) Verhalten von _fahrerVon per node ausgefuehrt:
#   ohne fahrer_id -> '' (NIE der aktuelle Fahrzeugfahrer);  mit fahrer_id -> Name
def test_fahrervon_verhalten(index_html, node_exe):
    src = _fahrervon_src(index_html)
    # Umgebung: ein Fahrzeug v1 hat AKTUELL Fahrer m9 (Max Aktuell). Eine Fahrt ohne
    # Snapshot darf NICHT m9 zurueckgeben. Eine Fahrt mit Snapshot m1 gibt "Erika".
    harness = (
        "const props={monteure:[{id:'m1',n:'Erika Fahrerin'},{id:'m9',n:'Max Aktuell'}]};\n"
        "const fahrzeuge=[{id:'v1',fahrer:'m9'}]; const fid='v1';\n"
        + src + "\n"
        "const out={ohneSnapshot:_fahrerVon({fahrzeug_id:'v1'}), mitSnapshot:_fahrerVon({fahrzeug_id:'v1',fahrer_id:'m1'})};\n"
        "console.log(JSON.stringify(out));"
    )
    out = json.loads(run_node_snippet(node_exe, harness))
    # (2) ohne belegten Fahrer -> leer, NICHT 'Max Aktuell' (der aktuelle Fahrzeugfahrer)
    assert out["ohneSnapshot"] == "", f"ohne Snapshot muss leer sein, war {out['ohneSnapshot']!r}"
    assert out["ohneSnapshot"] != "Max Aktuell"
    # (3) belegter Fahrer wird angezeigt
    assert out["mitSnapshot"] == "Erika Fahrerin"


# (2) Anzeige: leere Fahrer-Spalte zeigt "—", nicht den aktuellen Fahrzeugfahrer
def test_anzeige_zeigt_dash_bei_leer(index_html):
    assert "_fahrerVon(s)||'—'" in index_html
    # der Fallback auf den aktuellen Fahrzeugfahrer ist raus
    assert "(fahrzeuge.find(function(y){return y.id===((x&&x.fahrzeug_id)||fid);})||{}).fahrer)||null" not in index_html
    assert "var _fid=(x&&x.fahrer_id)||null;" in index_html


# Phase-2-Modell ist gestaged, aber NICHT ausfuehrbar markiert (Human-Run-Gate)
def test_phase2_sql_gestaged_human_run_gate():
    import os
    path = os.path.join(os.path.dirname(__file__), "..", "sql", "FAHRER_FAHRZEUG_HISTORIE_v1.sql")
    assert os.path.exists(path), "Phase-2-DDL nicht gestaged"
    with open(path, encoding="utf-8") as f:
        sql = f.read()
    assert "NICHT AUSFUEHREN" in sql or "NICHT AUSFÜHREN" in sql
    assert "CHAT-CLAUDE" in sql.upper() and "SEBASTIAN" in sql.upper()
