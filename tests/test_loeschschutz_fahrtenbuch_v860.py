"""
v3.9.860 — Mitarbeiter-Löschschutz: fahrtenbuch + entfernungszulage_tage ergänzt
(Personal-Agent, P2 Löschschutz-Lücke).

`_WORKER_REF_DEFS` (:1961) zählte nur 5 Tabellen; das manuelle Fahrtenbuch
(worker-basiert) fehlte → ein MA mit NUR Fahrtenbuch-Einträgen war löschbar, die
legal/steuerlich relevanten Zeilen verwaisen. Fix: fahrtenbuch + entfernungszulage_tage
(lohnrelevant) an den Referenzsatz appenden (res[0]=time_entries bleibt für entriesH).
"""
import re
import json
from conftest import run_node_snippet


def test_fahrtenbuch_und_ez_im_referenzsatz(index_html):
    assert '{k:"fahrtenbuch",tab:"fahrtenbuch",col:"worker_id"' in index_html
    assert '{k:"ez",     tab:"entfernungszulage_tage",col:"worker_id"' in index_html
    # time_entries bleibt der ERSTE Eintrag (res[0] speist entriesH)
    m = re.search(r"const _WORKER_REF_DEFS=Object\.freeze\(\[\s*\{k:\"([a-z]+)\"", index_html)
    assert m and m.group(1) == "entries", "erster Ref-Def muss entries (time_entries) bleiben"


def test_workerRefSumme_zaehlt_fahrtenbuch(index_html, node_exe):
    defs = re.search(r"const _WORKER_REF_DEFS=Object\.freeze\(\[.*?\]\);", index_html, re.S)
    summe = re.search(r"function _workerRefSumme\(c\)\{.*?return s\+\(n>0\?n:0\);\},0\);\}", index_html, re.S)
    assert defs and summe, "Referenzsatz/Summe nicht gefunden"
    harness = (
        defs.group(0) + "\n" + summe.group(0) + "\n"
        "const out={nurFahrtenbuch:_workerRefSumme({fahrtenbuch:3}),"
        "nurEz:_workerRefSumme({ez:2}),"
        "leer:_workerRefSumme({})};console.log(JSON.stringify(out));"
    )
    out = json.loads(run_node_snippet(node_exe, harness))
    # ein MA mit NUR Fahrtenbuch-Eintraegen ergibt jetzt refSumme>0 -> Loeschblock feuert
    assert out["nurFahrtenbuch"] == 3, "Fahrtenbuch-Eintraege zaehlen nicht in die Loeschschutz-Summe"
    assert out["nurEz"] == 2, "EZ-Tage zaehlen nicht in die Loeschschutz-Summe"
    assert out["leer"] == 0
