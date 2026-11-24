# -*- coding: utf-8 -*-
"""v3.9.1098 (GF 23.11.2026): Lohn-Monatsliste je Mitarbeiter als Excel + PDF fuer Buero/Admin.

Prueft die reine Funktion _zeMonatZeilen in Node (echte Ausfuehrung, kein Textvergleich):
Projekt/Arbeitsschein/Freitext wie die Wochenansicht, nur Zeilen des Monats, Sortierung, Summe,
"7,5"-Fall (hours als Zahl 7.5 bleibt 7.5). Dazu: Bedienung nur fuer Buero/Admin, kein Blatt bei Ladefehler.
"""
import io
import json
import os
import re
import subprocess

HIER = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HIER, "..", "index.html")


def _src():
    return io.open(HTML, encoding="utf-8", newline="").read()


def _fn(src, name):
    i = src.index("function " + name + "(")
    j = src.index("\nfunction ", i + 10)
    return src[i:j]


def _node(js):
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def _lauf(daten, ym):
    s = _src()
    code = _fn(s, "_zeMonatZeilen") + "\n" + _fn(s, "_zeMonatName") + "\n" + _fn(s, "_zeMonatListe")
    projects = [{"id": "p1", "name": "Sparkasse", "nr": "PA1"}]
    scheine = [{"id": "a1", "nummer": "AS-7", "kundName": "Huber"}]
    js = code + "\nconsole.log(JSON.stringify({r:_zeMonatZeilen(%s,%s,%s,%s),n:_zeMonatName(%s),l:_zeMonatListe('2026-01-15')}));" % (
        json.dumps(daten), json.dumps(projects), json.dumps(scheine), json.dumps(ym), json.dumps(ym))
    return _node(js)


DATEN = [
    {"id": "1", "date": "2026-11-05", "project_id": "p1", "hours": 7.5, "von": "07:00", "bis": "15:00", "pause": 0.5, "taetigkeit": "Montage"},
    {"id": "2", "date": "2026-11-03", "taetigkeit": "Lager aufraeumen", "hours": "8", "von": "07:00"},
    {"id": "3", "date": "2026-11-03", "arbeitsschein_id": "a1", "hours": 1.25, "von": "06:00"},
    {"id": "4", "date": "2026-10-31", "taetigkeit": "Oktober", "hours": 9},
    {"id": "5", "date": "2026-12-01", "taetigkeit": "Dezember", "hours": 9},
]


def test_zuordnung_wie_wochenansicht():
    z = _lauf(DATEN, "2026-11")["r"]["zeilen"]
    typen = {x["taetigkeit"] or x["ziel"]: x["typ"] for x in z}
    assert [x["typ"] for x in z] == ["Arbeitsschein", "Freitext", "Projekt"]
    assert z[0]["ziel"] == "AS-7 - Huber"
    assert z[1]["ziel"] == "Lager aufraeumen"
    assert z[2]["ziel"] == "Sparkasse (PA1)"
    assert typen


def test_nur_der_monat_und_sortiert():
    z = _lauf(DATEN, "2026-11")["r"]["zeilen"]
    assert [x["datum"] for x in z] == ["2026-11-03", "2026-11-03", "2026-11-05"]
    assert [x["von"] for x in z[:2]] == ["06:00", "07:00"]


def test_summe_und_komma_stunden():
    r = _lauf(DATEN, "2026-11")["r"]
    assert [x["stunden"] for x in r["zeilen"]] == [1.25, 8, 7.5]
    assert r["summe"] == 16.75
    assert r["zeilen"][2]["pause"] == 0.5


def test_monatsname_und_liste():
    o = _lauf([], "2026-11")
    assert o["n"] == "November 2026"
    assert o["r"] == {"zeilen": [], "summe": 0}
    assert o["l"][0] == "2026-01" and o["l"][1] == "2025-12" and len(o["l"]) == 13


def test_bedienung_nur_buero_admin_und_kein_blatt_bei_ladefehler():
    s = _src()
    ze = _fn(s, "ZeiterfassungView")
    assert "isAdmin&&selWorker&&React.createElement('div',{role:\"group\",\"aria-label\":\"Monatsliste Projektzeit\"" in ze
    holen = ze[ze.index("const _zeMonatHolen=async()=>{"):ze.index("const _zeTagKurz=")]
    assert "if(!isAdmin||!selWorker)return null;" in holen
    assert "_rlsLeer(data)" in holen
    # Ladefehler -> null (kein Blatt), nie ein Rueckfall auf den Geraetespeicher
    assert "entries" not in re.sub(r"getEntriesForWorker", "", holen)
