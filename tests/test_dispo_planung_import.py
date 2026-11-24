# -*- coding: utf-8 -*-
"""Dispo mobil (GF 24.11.2026, Weg B): der Abgleich aus der Auftragsverwaltung ueberschreibt die
Planungsfelder (dispo_datum, dispo_zeit, dispo_dauer, dispo_monteur) NIE.

Am Import-Code wird nichts geaendert - hier wird nur gemessen:
  1. Die echte Abbildungsfunktion (_juprowaMapWorksheet) laeuft in Node gegen einen vollen
     Beispielsatz: kein Ergebnisschluessel heisst dispo*, auch nach _mapBody nicht.
  2. Der Aktualisierungsweg fuer bestehende Scheine in _juprowaSync setzt NUR benannte Felder
     (upd.X=...); keines davon ist ein Planungsfeld. Ein bestehender Schein mit Planung behaelt sie
     nach Anwendung des Patches.
  3. Ein neuer Schein entsteht aus {...mapped} - also ohne Planung.
Die serverseitige Abgleichfunktion juprowa_apply_worksheets ist in sql/DISPO_PLANUNG_v1_PROBE.sql
im zurueckgerollten Lauf auf der Datenbank geprueft (Ergebniszeile dort).
Gegenprobe: eine eingeschleuste Zeile upd.dispoDatum=... macht die Pruefung rot.
"""
import io
import json
import os
import re
import subprocess
import tempfile

import pytest

from conftest import EPK_TEST_TIMEOUT, _extract_fn

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(WURZEL, "index.html")


def _q():
    return io.open(INDEX, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def _const(q, name):
    i = q.index("const " + name + "=")
    j = q.index(";", i)
    return "var " + q[i + 6:j + 1]


JS = r"""
function _juprowaResolveWorker(code) { return code === 'P011' ? 'w1' : ''; }
const JWS = {AK_SCHEINNR: 'S075999', ID: 4711, AK_AUFSTATUS: 1, AK_MONTEUR: 'P011', AK_MONTEUR_TEXT: 'Eins', AK_AUFART: 1,
  AK_WUNDAT: '2026-12-01 00:00:00', AK_WUNZEIT: '08:00:00', AK_TERMIN: '2026-12-02 00:00:00', AK_ANLAGE_DATZEIT: '2026-11-20 10:00:00',
  AK_BAUADR_NUMMER: '1', AK_BAUADR_NAM1: 'Kunde', AK_BAUADR_STR: 'Gasse 1', AK_BAUADR_PLZ: '3500', AK_BAUADR_ORT: 'Krems',
  AK_KONTAKT_TELEFON1: '0664', AK_KONTAKT_EMAIL: 'a@b', AK_PROJEKTNR: 'P1', AK_SCHEINTYP: 3, AK_PRIOR: 4, AK_DAUER: '02:00:00',
  AK_DURCHZUFUEHREN: 'Arbeit', AK_KONTAKT_NAME: 'Hr X', AK_SCHEINTYP_TEXT: 'Regie',
  dispo_datum: '2099-01-01', dispoDatum: '2099-01-01'};
const m = _juprowaMapWorksheet(JWS, []);
const b = _mapBody(Object.assign({}, m));
console.log(JSON.stringify({map: Object.keys(m), body: Object.keys(b)}));
"""


def _node(node_exe, js):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.cjs")
        with io.open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(js)
        r = subprocess.run([node_exe, p], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 0, (r.stderr or r.stdout)[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def pruefe_abbildung(node_exe, q):
    teile = [_const(q, n) for n in ("JUPROWA_STATUS_MAP", "JUPROWA_ART_MAP", "JUPROWA_PRIO_MAP")]
    for n in ("_juprowaMapWorksheet", "_toSnake", "_mapBody"):
        f = _extract_fn(q, n)
        assert f, n
        teile.append(f)
    R = _node(node_exe, "\n".join(teile) + JS)
    assert "nummer" in R["map"] and "terminBestaetigt" in R["map"], R["map"]
    for k in R["map"] + R["body"]:
        assert not k.lower().startswith("dispo"), "Abbildung traegt Planungsfeld %s" % k


def pruefe_abgleich(q):
    sync = _extract_fn(q, "_juprowaSync")
    assert sync
    i = sync.index("const upd={juprowa_id:mapped.juprowa_id")
    j = sync.index("const newAs={...mapped,id:uid()};", i)
    teil = sync[i:j]
    gesetzt = set(re.findall(r"\bupd\.([A-Za-z_]+)\s*=", teil))
    start = set(re.findall(r"([A-Za-z_]+):", teil[:teil.index("};")]))
    assert gesetzt, "keine upd-Zuweisung gefunden - die Pruefung misst nichts"
    for k in gesetzt | start:
        assert not k.lower().startswith("dispo"), "Abgleich setzt Planungsfeld %s" % k
    assert "{...existing" not in teil and "Object.assign(existing" not in teil, "Abgleich kopiert die ganze Zeile"
    # Anwendung: ein Schein mit Planung behaelt sie nach jedem moeglichen upd
    vorher = {"dispoDatum": "2026-12-05", "dispoZeit": "09:00", "dispoDauer": "02:00", "dispoMonteur": "w4"}
    patch = {k: "X" for k in gesetzt | start}
    nach = dict(vorher)
    nach.update(patch)
    for k, v in vorher.items():
        assert nach[k] == v, k


def test_abbildung_ohne_planungsfeld(node_exe):
    pruefe_abbildung(node_exe, _q())


def test_abgleich_laesst_planung_stehen():
    pruefe_abgleich(_q())


def test_gegenprobe_abgleich_mit_planungsfeld_rot():
    q = _q()
    alt = "if(mapped.juprowa_raw)upd.juprowa_raw=mapped.juprowa_raw;"
    assert q.count(alt) == 1
    q = q.replace(alt, alt + "upd.dispoDatum=mapped.terminBestaetigt;")
    with pytest.raises(AssertionError):
        pruefe_abgleich(q)


def test_gegenprobe_abbildung_mit_planungsfeld_rot(node_exe):
    q = _q()
    alt = "    juprowa_raw:jws,\n"
    assert q.count(alt) == 1
    q = q.replace(alt, alt + "    dispo_datum:jws.dispo_datum||\"\",\n")
    with pytest.raises(AssertionError):
        pruefe_abbildung(node_exe, q)
