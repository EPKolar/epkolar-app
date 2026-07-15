# -*- coding: utf-8 -*-
"""Perf-Fix 1 (PERF_BASELINE_2026-07-15) — tank_log-Base64 raus aus dem fahrzeuge-Store.

Umgesetzt: **Fix 1a** — Zulauf stoppen. addTank legt das Tankbeleg-Foto NICHT mehr als
Base64 (data:-URL) in tank_log ab, sondern laedt es via _sbUploadFile nach Storage und
speichert nur die URL (exakt das Muster des AS-Foto-Editors _addAsFotos). Offline/Fehler:
Eintrag ohne Foto + Hinweis (kein Base64-Fallback).

NICHT umgesetzt: **Fix 1b** (Migration — Sebastian-Gate) und **Fix 1c** (Boot-Diaet). 1c wurde
BEWUSST nicht ausgerollt: es gibt mehrere CROSS-Fahrzeug-Aggregations-Lesestellen auf
fahrzeuge[].tankLog aus dem gemeinsamen Boot-State (Buero-Tank-Kontrolle :11058,
Dashboard-Tankkosten :12666/:12805/:12820, Auswertung :21381/:21899). Die lassen sich NICHT
auf ein Nachladen pro geoeffnetem Fahrzeug umstellen, ohne die Kosten-/Kontroll-Ansichten leer
zu ziehen oder die 15-MB-Fetch nur zu verschieben. Off-Ramp der Aufgabe -> 1c geskippt.
Dieser Test pinnt den 1a-Speicherweg und die tank_log-Toleranz von _mapFahrzeug.
"""
import re
import subprocess

import pytest

try:
    from conftest import _extract_fn
except Exception:  # pragma: no cover
    _extract_fn = None


def _addtank_block(index_html):
    start = index_html.index("const addTank=async")
    end = index_html.index("const addSchaden=", start)
    return index_html[start:end]


# ── Fix 1a: Foto -> Storage-URL statt Base64 ────────────────────────────────

def test_addtank_uploads_via_sbuploadfile(index_html):
    blk = _addtank_block(index_html)
    # Upload nach Storage, Pfad-Schema wie _migrateTankFotos (fahrzeuge/<id>/tank/<eid>.jpg)
    assert '_sbUploadFile("fahrzeuge/"+fzId+"/tank/"+_eid+".jpg",tankFoto)' in blk


def test_addtank_no_base64_inflow(index_html):
    blk = _addtank_block(index_html)
    # Der alte Base64-Zulauf (foto:tankFoto...) darf NICHT mehr im tank_log-Eintrag landen.
    assert "foto:tankFoto" not in blk
    # Nur der hochgeladene URL-Wert (_foto) wird gespeichert.
    assert "foto:_foto" in blk


def test_addtank_only_uploads_dataurls(index_html):
    blk = _addtank_block(index_html)
    # Nur echte Base64-Belege (data:) werden hochgeladen — bereits-URLs unveraendert durchreichen.
    assert 'tankFoto.indexOf("data:")===0' in blk


def test_addtank_offline_entry_without_foto(index_html):
    blk = _addtank_block(index_html)
    # Offline / Upload-Fehler: Eintrag ohne Foto + Hinweis (kein Base64-Fallback, wie AS-Editor).
    assert "navigator.onLine" in blk
    assert "Offline" in blk
    assert "Tankfoto-Upload fehlgeschlagen" in blk


def test_addtank_no_optional_chaining_in_new_block(index_html):
    blk = _addtank_block(index_html)
    # Harte Regel: kein optional chaining. Der eingefuegte Foto-Upload-Block nutzt a&&a.b.
    seg = blk.split("Perf-Fix 1a", 1)[1].split("const data=", 1)[0]
    assert "?." not in seg


def test_addtank_still_pushes_column_scoped_diff(index_html):
    blk = _addtank_block(index_html)
    # Kontroll-/Sync-Semantik unveraendert: weiterhin column-scoped Diff-PUT (tank_log + km_stand).
    assert "u=>({tankLog:u.tankLog,kmStand:u.kmStand})" in blk


# ── _mapFahrzeug toleriert fehlendes tank_log (Vorbedingung fuer 1c/Migration) ──

def test_mapfahrzeug_survives_missing_tanklog(index_html, node_exe, tmp_path):
    assert _extract_fn is not None, "conftest._extract_fn nicht importierbar"
    fn = _extract_fn(index_html, "_mapFahrzeug")
    assert fn, "_mapFahrzeug nicht gefunden"
    js = (
        "const _jp=s=>{if(!s)return[];if(typeof s==='string'){try{return JSON.parse(s)}catch(e){return[]}}return s;};\n"
        "const _jo=s=>{if(!s)return{};if(typeof s==='string'){try{return JSON.parse(s)}catch(e){return{}}}return s;};\n"
        + fn + "\n"
        # Boot-Row OHNE tank_log (so wuerde 1c liefern) darf NICHT crashen und ergibt tankLog=[]
        "var r=_mapFahrzeug({id:'fz1',kennzeichen:'TU-1',km_stand:'100',km_log:'[]',schaeden:'[]'});\n"
        "if(!Array.isArray(r.tankLog)||r.tankLog.length!==0){console.error('tankLog nicht []:',JSON.stringify(r.tankLog));process.exit(1);}\n"
        "if(r.kmStand!==100){console.error('kmStand kaputt:',r.kmStand);process.exit(1);}\n"
        # null tank_log ebenfalls tolerant
        "var r2=_mapFahrzeug({id:'fz2',kennzeichen:'TU-2',tank_log:null});\n"
        "if(!Array.isArray(r2.tankLog)){console.error('null tank_log kaputt');process.exit(1);}\n"
        "console.log('OK');\n"
    )
    f = tmp_path / "mapfz.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


# ── 1c-Deferral-Marker: Boot-Fetch laedt weiterhin volle Rows (kein select=-Projekt) ──

def test_boot_fetch_unchanged_1c_deferred(index_html):
    # 1c nicht ausgerollt -> getFahrzeuge zieht weiterhin volle Rows (kein select= ohne tank_log).
    assert 'getFahrzeuge: function() { return _sbGetOrder("fahrzeuge","kennzeichen.asc"); }' in index_html


def test_cross_vehicle_tanklog_reads_still_present(index_html):
    # Begruendung der 1c-Deferral: diese Cross-Fahrzeug-Aggregationen lesen tankLog aus dem
    # gemeinsamen Boot-State. Solange sie existieren, wuerde ein tank_log-loser Boot sie leer ziehen.
    assert "(fahrzeuge||[]).flatMap(f=>(f.tankLog||[])" in index_html  # Buero-Tank-Kontrolle
