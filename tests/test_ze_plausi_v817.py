# -*- coding: utf-8 -*-
"""v3.9.817 — Zeiterfassung-Plausi (Paket D): nicht-blockierende Warnung gegen Doppelerfassung.

_zeTagPlausi prueft eine neue Buchung gegen die bestehenden Tageseintraege DESSELBEN Monteurs:
over24 = Tagessumme > 24h (physisch unmoeglich -> Doppelerfassung), overlap = Zeit-Ueberlappung
von/bis (nur same-day, Uebernacht uebersprungen -> keine False-Positives). Die Warnung blockt nichts
hart (Warn-Confirm wie die Abwesenheits-Warnung) -> keine legitime Buchung wird verhindert.
"""
import json
from conftest import run_node_snippet, _extract_fn


def _plausi(node_exe, index_html, existing_js, neu_h, von_js, bis_js):
    src = _extract_fn(index_html, "_zeTagPlausi")
    assert src, "_zeTagPlausi nicht gefunden"
    snip = src + ";process.stdout.write(JSON.stringify(_zeTagPlausi(" + existing_js + "," + str(neu_h) + "," + von_js + "," + bis_js + ")))"
    return json.loads(run_node_snippet(node_exe, snip))


def test_over24_ueber_mehrere_eintraege(node_exe, index_html):
    r = _plausi(node_exe, index_html, "[{hours:20}]", 8, "''", "''")
    assert r["over24"] is True and r["overlap"] is False and abs(r["sum"] - 28) < 0.01


def test_overlap_gleicher_tag(node_exe, index_html):
    r = _plausi(node_exe, index_html, "[{hours:8,von:'07:00',bis:'16:00'}]", 8, "'10:00'", "'18:00'")
    assert r["overlap"] is True and r["over24"] is False and abs(r["sum"] - 16) < 0.01


def test_kein_konflikt(node_exe, index_html):
    r = _plausi(node_exe, index_html, "[{hours:8,von:'07:00',bis:'12:00'}]", 4, "'13:00'", "'17:00'")
    assert r["overlap"] is False and r["over24"] is False and abs(r["sum"] - 12) < 0.01


def test_leer(node_exe, index_html):
    r = _plausi(node_exe, index_html, "[]", 8, "''", "''")
    assert r["over24"] is False and r["overlap"] is False and abs(r["sum"] - 8) < 0.01


def test_uebernacht_kein_false_overlap(node_exe, index_html):
    # von>bis (Uebernacht) wird beidseitig uebersprungen -> keine spurious-overlap-Warnung.
    r = _plausi(node_exe, index_html, "[{hours:8,von:'22:00',bis:'06:00'}]", 8, "'23:00'", "'05:00'")
    assert r["overlap"] is False


def test_grenze_genau_24(node_exe, index_html):
    # exakt 24h -> KEINE Warnung (nur echt >24 warnt).
    r = _plausi(node_exe, index_html, "[{hours:16}]", 8, "''", "''")
    assert r["over24"] is False and abs(r["sum"] - 24) < 0.01


def test_verdrahtung(index_html):
    assert "window._zeTagPlausi=_zeTagPlausi" in index_html, "_zeTagPlausi nicht window-exportiert"
    assert "var _plz=_zeTagPlausi(_exTag,h,_rVon,_rBis);" in index_html, "addEntry ruft Plausi nicht auf"
    assert "if(_plz.over24||_plz.overlap){" in index_html, "Warn-Gate fehlt"
    # nicht-blockierend: Abbruch nur wenn User im Confirm ablehnt (Trotzdem buchen).
    assert "Trotzdem buchen" in index_html, "Warn-Confirm (nicht-blockierend) fehlt"
    # Editieren zaehlt den bearbeiteten Eintrag nicht doppelt.
    assert "!editEntry||e.id!==editEntry.id" in index_html, "Edit-Ausschluss im Tages-Set fehlt"
