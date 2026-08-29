# -*- coding: utf-8 -*-
"""v3.9.901 Befund 1+2 - "Kalibrierung faellig" hatte SECHS Stellen und DREI Antworten.

    KPI-Kachel      L29172  _isValidKalibDate(d) && d<=td2()          Datum, mit Junk-Riegel
    Chip-Filter     L29186  dito                                      Datum, mit Junk-Riegel
    Chip-Zaehler    L29197  dito                                      Datum, mit Junk-Riegel
    Scan-Karte      L29437  naechsteKalib<=td2()                      Datum, OHNE Junk-Riegel
    Kartenzeile     L29604  naechsteKalib && naechsteKalib<=td2()     Datum, OHNE Junk-Riegel
    Tabellenzeile   L29628  dito                                      Datum, OHNE Junk-Riegel
    Abzeichen       L4311   WZ_STATUS[w.status].kalibrierung          STATUS

Der Status "kalibrierung" wird nirgends im Code GESCHRIEBEN - nur von Hand im
Formular (L29748) oder ueber die Sammelaenderung (L29540). Er wurde also nur
gelesen, und zwar von genau einer der sieben Stellen.

An gestellten Geraeten gemessen (29.08.2026, Europe/Vienna), VOR dem Fix:

    KPI                = 2
    Zeilenfaerbung rot = Geraet 1, 3, 4, 6
    Ausgabeliste       = 1, 3, 4, 5, 6, 7

    Geraet 2 (Status "kalibrierung", Datum 2027-01-15): NICHT gezaehlt, Zeile
      weiss - und trug daneben das gelbe Abzeichen "Kalibrierung faellig".
    Geraet 3/4 (naechste_kalib "0000-00-00" bzw. "1970-01-01"): Zeile ROT und
      Scan-Karte "FAELLIG!" - aber KPI 0 und Chip (0). Klick auf den Chip:
      "Keine Werkzeuge gefunden", waehrend die Zeile darunter rot leuchtet.
    Geraet 1 (Datum 2026-06-30 ueberfaellig, Status "verfuegbar"): gezaehlt,
      GRUENES Abzeichen "Verfuegbar" - und stand in "Werkzeug ausgeben".
      Das ist der teure Fall: ein unkalibriertes Messgeraet geht auf die Baustelle.

Nach dem Fix ist _wzKalibFaellig(w) die einzige Quelle. Dieser Riegel misst nicht,
DASS der Name vorkommt (das waere die Form statt der Eigenschaft), sondern laesst
die echten Ausdruecke aus index.html in Node gegen gestellte Geraete laufen und
verlangt, dass alle vier dieselbe Menge nennen.
"""
import json
import os
import re
import subprocess

import pytest

from conftest import EPK_TEST_TIMEOUT
from _hilfen import nur_code, fundstellen


# ---------------------------------------------------------------- Hilfen ----

def _zeile_mit(index_html, nadel):
    """Die EINE Codezeile aus index.html, die `nadel` enthaelt - woertlich.

    KOMMENTARBLIND ueber nur_code(): die Erklaerkommentare zu diesem Fix nennen
    die alten Ausdruecke, die sie erklaeren. Beim ersten Lauf der Schwesterdatei
    sind zwei Riegel genau daran angeschlagen."""
    treffer = [z for z in nur_code(index_html).splitlines() if nadel in z]
    assert len(treffer) == 1, (
        "Erwartet genau eine Codezeile mit %r, gefunden %d.%s"
        % (nadel, len(treffer), chr(10) + chr(10).join(treffer[:3]))
    )
    return treffer[0]


def _zeile_regex(index_html, muster):
    """Wie _zeile_mit, aber mit Zeilenanfang-Anker: den Namen _ymd gibt es auch
    eingerueckt in zwei Komponenten (L6953, L7469); nur die Modulebene ist gemeint."""
    treffer = [z for z in nur_code(index_html).splitlines() if re.match(muster, z)]
    assert len(treffer) == 1, "Erwartet genau eine Zeile fuer %r, gefunden %d" % (muster, len(treffer))
    return treffer[0]


GESTELLTE_GERAETE = [
    {"id": 1, "status": "verfuegbar", "naechsteKalib": "2026-06-30"},   # ueberfaellig
    {"id": 2, "status": "kalibrierung", "naechsteKalib": "2027-01-15"},  # Hand-Status
    {"id": 3, "status": "verfuegbar", "naechsteKalib": "0000-00-00"},   # Junk
    {"id": 4, "status": "verfuegbar", "naechsteKalib": "1970-01-01"},   # Junk
    {"id": 5, "status": "verfuegbar", "naechsteKalib": ""},             # leer
    {"id": 6, "status": "verfuegbar", "naechsteKalib": "2026-08-29"},   # heute
    {"id": 7, "status": "verfuegbar", "naechsteKalib": "2027-03-01"},   # gut
]
# Ohne Geraet 2 und 3/4 waere der Aufbau gruen und nutzlos - genau die
# Testkrankheit aus der Sitzung 2026-08-25 (nur leichte Faelle gemessen).

ERWARTET = [1, 2, 6]


def _messe(node_exe, tmp_path, index_html, heute="2026-08-29T09:00:00+02:00"):
    js = chr(10).join([
        "const GER=" + json.dumps(GESTELLTE_GERAETE) + ";",
        "const R=Date;",
        "global.Date=class extends R{constructor(...a){if(a.length===0)super("
        + json.dumps(heute) + ");else super(...a);}"
        "static now(){return new R(" + json.dumps(heute) + ").getTime();}};",
        _zeile_regex(index_html, r"^const _ymd=d=>"),
        _zeile_regex(index_html, r"^const td2=\(\)="),
        _zeile_mit(index_html, "function _isValidKalibDate(s){"),
        _zeile_mit(index_html, "function _wzKalibFaellig(w){"),
        # KPI-Kachel: der echte Ausdruck, nur die Quelle umbenannt
        "const werkzeuge=GER;",
        _zeile_mit(index_html, "const kalibFaellig=werkzeuge.filter("),
        # Chip-Zaehler: der echte Rumpf
        "const cnt={kalib_faellig:0};for(const w of GER){"
        + _zeile_mit(index_html, "cnt.kalib_faellig++").strip() + "}",
        # Zeilenfaerbung Karte + Tabelle: die echten kalFaellig-Zuweisungen
        "const rowKarte=GER.filter(w=>{"
        + re.search(r"(const kalFaellig=[^;]+;)",
                    _zeile_mit(index_html, "const lastMaint=")).group(1)
        + "return !!kalFaellig;}).map(w=>w.id);",
        "const rowTab=GER.filter(w=>{"
        + re.search(r"(const kalFaellig=[^;]+;)",
                    _zeile_mit(index_html, "React.createElement('tbody', {}, sorted.map(w=>{const st=WZ_STATUS")).group(1)
        + "return !!kalFaellig;}).map(w=>w.id);",
        "const chip=GER.filter(w=>_wzKalibFaellig(w)).map(w=>w.id);",
        "console.log(JSON.stringify({kpi:kalibFaellig,chipZahl:cnt.kalib_faellig,"
        "chip:chip,rowKarte:rowKarte,rowTab:rowTab}));",
    ])
    p = tmp_path / "kalib.js"
    p.write_text(js, encoding="utf-8")
    env = dict(os.environ, TZ="Europe/Vienna")
    r = subprocess.run([node_exe, str(p)], capture_output=True, text=True,
                       timeout=EPK_TEST_TIMEOUT, env=env)
    assert r.returncode == 0, "Node brach ab:" + chr(10) + r.stderr
    assert r.stdout.strip(), "Node lieferte NICHTS - ein leerer Lauf ist kein gruener Lauf."
    return json.loads(r.stdout.strip().splitlines()[-1])


# == 1 - die vier Zaehler nennen dieselbe Menge ==============================

def test_vier_stellen_eine_menge(index_html, node_exe, tmp_path):
    """Der Riegel, der den Fehler gefunden haette.

    UMKEHRPROBE: eine der vier Stellen auf den alten Ausdruck zuruecksetzen -
    KPI auf `_isValidKalibDate(w.naechsteKalib)&&w.naechsteKalib<=td2()` oder
    die Zeilenfaerbung auf `w.naechsteKalib&&w.naechsteKalib<=td2()`. Dann
    weicht die Menge fuer Geraet 2 bzw. 3/4 ab und der Test faellt.
    Nachgemessen: mit dem Stand 808e58f ist er ROT (KPI 2, Karte [1,3,4,6]).
    """
    m = _messe(node_exe, tmp_path, index_html)
    assert m["chip"] == ERWARTET, "Chip-Menge: " + repr(m)
    assert m["kpi"] == len(ERWARTET), "KPI-Kachel weicht ab: " + repr(m)
    assert m["chipZahl"] == len(ERWARTET), "Chip-Zaehler weicht ab: " + repr(m)
    assert m["rowKarte"] == ERWARTET, "Kartenzeilen-Faerbung weicht ab: " + repr(m)
    assert m["rowTab"] == ERWARTET, "Tabellenzeilen-Faerbung weicht ab: " + repr(m)


# == 2 - der Junk-Riegel sitzt an ALLEN Stellen ==============================

def test_junkdatum_nirgends_faellig(index_html, node_exe, tmp_path):
    """"0000-00-00" und "1970-01-01" duerfen an KEINER Stelle faellig heissen.

    UMKEHRPROBE: `_isValidKalibDate` aus `_wzKalibFaellig` entfernen -> Geraet 3
    und 4 tauchen in allen fuenf Zahlen auf, der Test faellt.
    """
    m = _messe(node_exe, tmp_path, index_html)
    for feld in ("chip", "rowKarte", "rowTab"):
        assert 3 not in m[feld] and 4 not in m[feld], (
            "Junk-Datum gilt in %s als faellig: %r" % (feld, m))


# == 3 - kein siebter Nachbau ===============================================

def test_nur_eine_datumsrechnung(index_html):
    """KOMMENTARBLIND (der Erklaerkommentar zum Umbau nennt die alten Ausdruecke
    selbst - ein rohes `not in index_html` haette an MEINEM Kommentar
    angeschlagen; das ist im Repo der elfte Fall dieser Art).

    Erlaubt sind genau ZWEI Datumsvergleiche auf naechsteKalib:
      - `_wzKalibFaellig`      (die eine Quelle)
      - die Tages-Benachrichtigung `overdue` (L9044) - andere Bedeutung:
        UEBERfaellig = strikt vor heute, ohne den Hand-Status, damit ein Geraet
        ohne Datum nicht taeglich pusht. Bewusst nicht zusammengelegt.

    UMKEHRPROBE: irgendwo `w.naechsteKalib<=td2()` neu einbauen -> 3 Treffer, rot.
    """
    code = nur_code(index_html)
    treffer = re.findall(r"naechsteKalib\s*<=?[^=]", code)
    assert len(treffer) == 2, (
        "Erwartet 2 Datumsvergleiche auf naechsteKalib (Helfer + overdue-Push), "
        "gefunden %d.%s%s" % (len(treffer), chr(10), fundstellen(code, "naechsteKalib<")))
    assert "function _wzKalibFaellig(w){" in code, "Die eine Quelle fehlt."
    assert "w.status==='kalibrierung'" in code.split("function _wzKalibFaellig(w){")[1][:200], \
        "Der Helfer liest den von Hand gesetzten Status nicht mehr."


# == 4 - die Ausgabe warnt ==================================================

def test_ausgabe_warnt_bei_faelliger_kalibrierung(index_html):
    """"Werkzeug ausgeben" filtert nur auf status==="verfuegbar". Ein
    ueberfaelliges Messgeraet hat genau diesen Status.

    UMKEHRPROBE: die Rueckfrage aus dem onClick entfernen -> rot.
    """
    code = nur_code(index_html)
    zeile = _zeile_mit(index_html, 'document.getElementById("co_"+w.id)')
    assert "_wzKalibFaellig(w)" in zeile, (
        "Der Ausgabe-Knopf fragt nicht nach der Kalibrierung:" + chr(10) + zeile)
    assert 'React.createElement(\'div\', { style: {fontSize:10,color:"#eab308"' in code, \
        "Der sichtbare Hinweis in der Ausgabeliste fehlt."
