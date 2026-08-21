# -*- coding: utf-8 -*-
"""v3.9.822 — EIN Worker-Mapper für beide Ladewege + kein stiller workers-Fetch-Fehler.

BUG: `monteure` wurde auf ZWEI Wegen gesetzt, aber nur einer mappte. Der IndexedDB-Cache-Pfad
übernahm die Objekte ROH -> Felder wie `austritt` fehlten bzw. lagen in Roh-Form vor -> der (korrekte)
v821-Austritts-Filter `(!w.austritt||...)` war fälschlich WAHR -> ausgetretene Mitarbeiter (Cracana,
Aliti) blieben in "Mitarbeiter ohne Login" & Co. sichtbar. Beim Start gewinnt der Cache.

FIX: PURE, idempotenter `_mapWorker` — von BEIDEN Ladewegen genutzt.
"""
import json
from conftest import run_node_snippet, _extract_fn


def _map(node_exe, index_html, obj_js, twice=False):
    fn = _extract_fn(index_html, "_mapWorker")
    assert fn, "_mapWorker nicht gefunden"
    call = "_mapWorker(_mapWorker(" + obj_js + "))" if twice else "_mapWorker(" + obj_js + ")"
    return json.loads(run_node_snippet(node_exe, fn + ";process.stdout.write(JSON.stringify(" + call + "))"))


# ── 1) Mapper füllt aus ROH-Form und aus bereits gemappter Form ──────────────
def test_rohform_wird_gemappt(node_exe, index_html):
    roh = "{id:'w3',name:'Cracana',vorname:'Sorin',role:'Monteur',phone:'0664',geb_dat:'1990-01-01',fs_nr:'X1',austritt:'2026-07-22',eintritt:'2020-05-01',stundensatz:'42,5'}"
    r = _map(node_exe, index_html, roh)
    assert r["n"] == "Cracana" and r["r"] == "Monteur" and r["tel"] == "0664"
    assert r["gebDat"] == "1990-01-01" and r["fsNr"] == "X1"
    assert r["austritt"] == "2026-07-22", "austritt aus Roh-Form nicht uebernommen — genau der Ur-Bug"
    assert r["eintritt"] == "2020-05-01"
    # '42,5' ist keine gueltige Float-Notation -> parseFloat liefert 42 (Bestandsverhalten, byte-identisch)
    assert isinstance(r["stundensatz"], (int, float))


def test_bereits_gemappte_form(node_exe, index_html):
    gemappt = "{id:'w3',n:'Cracana',vorname:'Sorin',r:'Monteur',tel:'0664',gebDat:'1990-01-01',fsNr:'X1',austritt:'2026-07-22',eintritt:'2020-05-01',stundensatz:42.5}"
    r = _map(node_exe, index_html, gemappt)
    assert r["n"] == "Cracana" and r["r"] == "Monteur" and r["tel"] == "0664"
    assert r["austritt"] == "2026-07-22" and r["stundensatz"] == 42.5


def test_idempotenz(node_exe, index_html):
    """Der Cache kann bereits gemappte Objekte enthalten -> doppelte Anwendung muss stabil sein."""
    for obj in ("{id:'w3',name:'Cracana',role:'Monteur',phone:'0664',austritt:'2026-07-22',stundensatz:42.5}",
                "{id:'w9',n:'Riedmann',r:'Monteur',tel:'',austritt:'',stundensatz:0}"):
        einmal = _map(node_exe, index_html, obj)
        zweimal = _map(node_exe, index_html, obj, twice=True)
        assert einmal == zweimal, "_mapWorker ist nicht idempotent: " + json.dumps(einmal) + " != " + json.dumps(zweimal)


def test_leerer_austritt_bleibt_leer(node_exe, index_html):
    r = _map(node_exe, index_html, "{id:'w1',name:'Paschinger',role:'Monteur'}")
    assert r["austritt"] == "", "fehlender austritt muss zu '' werden (Filter-Semantik: aktiv)"


# ── 2) BEIDE Ladewege nutzen den Mapper (Regressionsschutz gegen den Ur-Bug) ──
def test_beide_ladewege_mappen(index_html):
    assert "setMonteure(mt.map(_mapWorker))" in index_html, "Cache-Pfad mappt nicht (Ur-Bug)"
    # v3.9.848: Server-Pfad ist jetzt ein Reload-Merge (setMonteure(prev=>...)) — mappt aber
    # weiterhin ueber _mapWorker (nur nicht mehr als wk.map(_mapWorker)). Intent unveraendert.
    assert "?_prevById.get(x.id):_mapWorker(x)" in index_html, "Server-Pfad (v848-Merge) nutzt nicht _mapWorker"
    assert "setMonteure(mt);" not in index_html, "rohes setMonteure(mt) noch vorhanden — Ur-Bug zurueck"
    assert "setMonteure(wk);" not in index_html, "roher (ungemappter) Server-Pfad setMonteure(wk) — Ur-Bug zurueck"
    assert "window._mapWorker=_mapWorker" in index_html, "_mapWorker nicht window-exportiert"


# ── 3) workers-Fetch scheitert nicht mehr still ──────────────────────────────
def test_workers_fetch_nicht_still(index_html):
    i = index_html.index("API.getWorkers().catch(")
    seg = index_html[i:i + 320]
    assert "()=>null" not in seg, "nacktes catch(()=>null) am workers-Fetch — Fehler wird still verschluckt"
    assert "console.error" in seg, "workers-Fetch loggt den Fehler nicht"
    assert "__epkWorkerLoadErr" in seg, "Fehlerart wird nicht fuer die Diagnose hinterlegt"


def test_stale_hinweis_einmalig(index_html):
    assert "__epkWorkerStaleWarned" in index_html, "kein Einmal-Guard fuer den Veraltet-Hinweis"
    assert "konnte nicht aktualisiert werden" in index_html, "kein Hinweis-Toast bei Fehler/leerer Antwort"
    i = index_html.index("__epkWorkerStaleWarned")
    seg = index_html[i - 400:i + 400]
    assert '"warn"' in seg, "Hinweis muss warn sein (nicht error) — App bleibt benutzbar"
