# -*- coding: utf-8 -*-
"""DAUERRIEGEL gegen FREIE VARIABLEN in index.html  (v3.9.914)

Fehlerklasse: ein Rueckruf war als `tf` deklariert und als `f` gelesen -
ReferenceError im Render, weisser Schirm, live am 2026-08-29 durch alle drei
Tore gekommen.  Vier weitere Faelle derselben Art fanden sich danach.

Gemessen wird mit einem ECHTEN Parser (espree) und einer ECHTEN
Sichtbarkeitsanalyse (eslint-scope) - dieselbe Maschine wie hinter ESLints
no-undef.  Die drei npm-Pakete sind MITVERSIONIERT unter
scripts/freivar/node_modules/ (25 Dateien, 511 KB).  Kein `npm install`
noetig - und wo sie doch fehlen, ist der Ausgang ROT, nie ein skip.

ES GIBT HIER KEIN pytest.skip.  Ein uebersprungener Riegel meldet gruen,
obwohl niemand gemessen hat - genau die Krankheit, gegen die er antritt.

FUENF Tests, und erst alle fuenf zusammen sind eine Messung:
  1. Werkzeugkette da            - sonst ROT
  2. fehlende Werkzeugkette      - ROT, belegt (Code 4), nicht "sauber"
  3. Gegenprobe am ECHTEN index  - eingebauter Fehler MUSS gefunden werden
  4. kaputte Datei               - EIGENER Ausgang (Code 3), nicht "sauber"
  5. der Riegel selbst           - keine neuen freien Namen

Laufzeit: rund 5 s (3 Vollscans a ~1,4 s ueber 3,5 MB index.html).
"""
import json
import os
import re
import shutil
import subprocess
import tempfile

from conftest import EPK_TEST_TIMEOUT, REPO_ROOT, _find_node

INDEX = os.path.join(REPO_ROOT, "index.html")
FREIVAR_DIR = os.path.join(REPO_ROOT, "scripts", "freivar")
SCANNER = os.path.join(FREIVAR_DIR, "freivar.js")
PAKETE = ("espree", "eslint-scope", "globals")

# ---------------------------------------------------------------------------
# BASISLINIE - Altbestand, jeder Eintrag einzeln nachgesehen und BELEGT.
# Wird einer repariert, MUSS er hier raus (Test 5 erzwingt das), sonst deckt
# die Liste kuenftige Rueckfaelle zu.
#
#   (leer - der einzige Altfund `table` ist seit v3.9.914 repariert)
#
#     Er stand seit v3.9.910 in `_sbGetUsersSafe(filter)`: der aus einem
#     generischen Schnipsel kopierte Ausdruck
#       (typeof table!=='undefined' && table) ? table : 'users'
#     Die Funktion hat keinen Parameter `table`, die URL ist fest "/users";
#     der typeof-Waechter griff, der Ausdruck fiel IMMER auf 'users'. Ein
#     toter Zweig, dessen Ergebnis zufaellig richtig war - meine eigene
#     Hinterlassenschaft aus v910, entfernt in v914.
#
#     Eine LEERE Basislinie ist der Zustand, den dieser Riegel anstrebt. Sie
#     zu behalten, nur weil einmal etwas darin stand, waere ein Denkmal: ab
#     jetzt ist JEDER freie Name in index.html ein Fehler, und genau das soll
#     der naechste Lauf sagen.
# ---------------------------------------------------------------------------
BASISLINIE = {}

# Unter so vielen Zeichen JS kann index.html gar nicht liegen. Der Riegel
# meldet sonst "nichts gefunden", weil er nichts GESEHEN hat - dieselbe
# Krankheit wie ein gruener Lauf ohne Messung.
MINDEST_ZEICHEN = 1_000_000


def _node():
    exe = _find_node()
    # kein skip: ohne node ist der Riegel BLIND, und blind ist rot.
    assert exe, "node fehlt - der Riegel kann NICHTS messen (kein skip erlaubt)"
    return exe


def _lauf(pfad, cwd=None, scanner=None):
    """Ruft den Scanner. Gibt (rc, treffer_liste, stderr) zurueck."""
    p = subprocess.run(
        [_node(), scanner or SCANNER, pfad.replace("\\", "/"), "--json"],
        capture_output=True, text=True, timeout=EPK_TEST_TIMEOUT,
        cwd=cwd or FREIVAR_DIR,
    )
    treffer = None
    if p.returncode in (0, 1) and p.stdout.strip():
        treffer = json.loads(p.stdout)
    return p.returncode, treffer, p.stderr


def _scan(pfad):
    """Vollscan mit allen Ausgaengen sauber getrennt. -> {name: anzahl}, liste"""
    rc, treffer, err = _lauf(pfad)
    if rc == 4:
        raise AssertionError(
            "WERKZEUGKETTE FEHLT - der Riegel misst nichts:" + chr(10) + err[:900])
    if rc == 5:
        raise AssertionError(
            "EIGENPROBE GESCHEITERT - der Riegel findet seinen eigenen "
            "eingebauten Fehler nicht:" + chr(10) + err[:900])
    if rc == 3:
        raise AssertionError(
            "KONNTE NICHT MESSEN (kein 'nichts gefunden'!):" + chr(10) + err[:900])
    if rc not in (0, 1):
        raise AssertionError("Scanner abgestuerzt (rc=%s): %s" % (rc, err[:900]))
    # "leere Ausgabe" darf NIE als "nichts gefunden" durchgehen - genau so
    # las ein frueherer Mantel eine kaputte Datei als sauber.
    if rc == 1 and treffer is None:
        raise AssertionError("Scanner meldete Fund ohne Ausgabe: %s" % err[:900])

    m = re.search(r"# GEMESSEN bloecke=(\d+) zeichen=(\d+)", err)
    assert m, ("Der Scanner hat seine Messmenge nicht gemeldet - ohne die ist "
               "'0 Treffer' wertlos. stderr: %s" % err[:400])
    bloecke, zeichen = int(m.group(1)), int(m.group(2))
    assert bloecke >= 1, "0 <script>-Bloecke gemessen - hier wurde NICHTS geprueft"
    assert zeichen >= MINDEST_ZEICHEN, (
        "nur %d Zeichen JS gemessen (erwartet >= %d) - der Riegel hat den "
        "Grossteil von index.html gar nicht gesehen" % (zeichen, MINDEST_ZEICHEN))

    aus = {}
    for t in (treffer or []):
        aus[t["name"]] = aus.get(t["name"], 0) + 1
    return aus, (treffer or [])


# --------------------------------------------------------------------------
# 1. Werkzeugkette
# --------------------------------------------------------------------------
def test_1_werkzeugkette_ist_mitversioniert():
    assert _find_node(), "node fehlt - der Riegel kann nicht messen"
    assert os.path.isfile(SCANNER), "freivar.js fehlt: %s" % SCANNER
    for mod in PAKETE:
        p = os.path.join(FREIVAR_DIR, "node_modules", mod)
        assert os.path.isdir(p), (
            "mitversioniertes Paket %s fehlt (%s). Die Arbeitskopie ist "
            "unvollstaendig: git checkout -- scripts/freivar/node_modules" % (mod, p))


# --------------------------------------------------------------------------
# 2. Fehlende Werkzeugkette ist ROT - gemessen, nicht behauptet
# --------------------------------------------------------------------------
def test_2_ohne_werkzeugkette_rot_statt_gruen():
    """Der schlechteste denkbare Ausgang waere: Pakete weg -> Riegel still
    gruen.  Also wird genau das hier PROBIERT: der Scanner allein, ohne
    node_modules daneben.  Er muss mit Code 4 und klarer Meldung sterben."""
    with tempfile.TemporaryDirectory() as d:
        allein = os.path.join(d, "freivar.js")
        shutil.copyfile(SCANNER, allein)
        rc, treffer, err = _lauf(INDEX, cwd=d, scanner=allein)
    assert rc == 4, (
        "Ohne Werkzeugkette lieferte der Riegel rc=%s statt 4. Bei rc in (0,1) "
        "wuerde er ohne jede Messung GRUEN melden - der gefaehrlichste aller "
        "Ausgaenge.%sstderr: %s" % (rc, chr(10), err[:600]))
    assert "WERKZEUGKETTE FEHLT" in err, "Meldung unklar: %s" % err[:400]


# --------------------------------------------------------------------------
# 3. Gegenprobe am ECHTEN index.html
# --------------------------------------------------------------------------
def test_3_gegenprobe_riegel_kann_rot_werden():
    """Baut den bekannten Fehler kuenstlich in eine KOPIE des echten
    index.html ein: ein Rueckruf-Parameter wird umbenannt, eine Verwendung
    bleibt stehen.  Ohne diesen Test beweist ein gruener Riegel gar nichts."""
    with open(INDEX, encoding="utf-8") as fh:
        roh = fh.read()
    m = re.search(r"\.map\(function\(([A-Za-z_$][\w$]*)\)\{", roh)
    assert m, "kein .map(function(x){ gefunden - Gegenprobe nicht baubar"
    name = m.group(1)
    stelle = roh.find(name + ".", m.end())
    assert stelle > 0, "keine Verwendung von %s. gefunden" % name
    mutiert = roh[:stelle] + "zZmutiertQ" + roh[stelle + len(name):]

    fd, tmp = tempfile.mkstemp(suffix=".html")
    os.close(fd)
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(mutiert)
        gefunden, _ = _scan(tmp)
    finally:
        os.unlink(tmp)
    assert "zZmutiertQ" in gefunden, (
        "GEGENPROBE GESCHEITERT: der Riegel sieht einen eingebauten freien "
        "Namen im echten index.html nicht. Er misst NICHTS. Gefunden: %s"
        % sorted(gefunden))


# --------------------------------------------------------------------------
# 4. Parsefehler ist ein EIGENER Ausgang
# --------------------------------------------------------------------------
def test_4_kaputte_datei_ist_nicht_sauber():
    """Ein frueherer Mantel meldete eine syntaktisch kaputte Datei als SAUBER.
    'Konnte nicht messen' und 'nichts gefunden' muessen unterscheidbar sein."""
    with open(INDEX, encoding="utf-8") as fh:
        roh = fh.read()
    m = re.search(r"function\s+[A-Za-z_$][\w$]*\s*\(", roh)
    assert m, "keine Funktionsdeklaration gefunden"
    kaputt = roh[:m.start()] + "function )){{ " + roh[m.end():]

    fd, tmp = tempfile.mkstemp(suffix=".html")
    os.close(fd)
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(kaputt)
        rc, treffer, err = _lauf(tmp)
    finally:
        os.unlink(tmp)
    assert rc == 3, (
        "Kaputte Datei lieferte rc=%s statt 3. rc=0 hiesse 'sauber' - genau "
        "der Irrtum vom 2026-08-29.%sstderr: %s" % (rc, chr(10), err[:600]))
    assert "KONNTE NICHT MESSEN" in err, "Meldung unklar: %s" % err[:400]


# --------------------------------------------------------------------------
# 5. Der Riegel
# --------------------------------------------------------------------------
def test_5_keine_neuen_freien_variablen():
    gefunden, treffer = _scan(INDEX)
    neu = {k: v for k, v in gefunden.items() if k not in BASISLINIE}
    mehr = {k: (BASISLINIE[k], v) for k, v in gefunden.items()
            if k in BASISLINIE and v > BASISLINIE[k]}
    weg = {k: v for k, v in BASISLINIE.items() if k not in gefunden}

    if neu or mehr:
        zeilen = set()
        for t in treffer:
            if t["name"] in neu or t["name"] in mehr:
                zeilen.add("  %s  index.html:%s" % (t["name"], t["zeile"]))
        raise AssertionError(
            "NEUE freie Variable(n) - ReferenceError, sobald der Pfad laeuft:"
            + chr(10) + chr(10).join(sorted(zeilen)))
    assert not weg, (
        "Altfund(e) %s sind repariert - BASISLINIE in dieser Datei kuerzen, "
        "sonst deckt sie kuenftige Rueckfaelle zu." % sorted(weg))
