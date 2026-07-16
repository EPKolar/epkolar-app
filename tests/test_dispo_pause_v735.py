# -*- coding: utf-8 -*-
"""v3.9.735 — Dispo-Startzeiten beruecksichtigen Mittagspause (12:00-13:00) und Freitag-Ende (11:30).

Sebastian (16.07., live): "dispo muss auch beruecksichtigen, dass 12 bis 13 uhr mittagspause ist und
freitag um 11.30 uhr alle ins wochenende gehen." -> _dispoAblauf:
  * Mo-Do: 12:00-13:00 ist Pause. Ein Stopp, dessen START in die Pause faellt, rutscht auf 13:00; ein Stopp,
    der die Pause KREUZT (Start vor 12:00, Ende nach 12:00), bekommt die 60-min-Pause eingeschoben (Ende +60).
  * Freitag: keine Mittagspause (um 11:30 ist Feierabend, vor 12:00) -> opts.noLunch, kein Pausen-Einschub.
Reine Zeit-Rechnung; die Kapazitaets-Wand (norm-min) bleibt unveraendert.

PURER Kern (node-eval): _dispoAblauf(items,startMin,pufferMin,taktMin,opts) mit Pausen-Logik.
"""
import subprocess


def _block(index_html):
    start = index_html.index("var DISPO_RESERVE_MIN=60;")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    return index_html[start:end]


_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"


def _run(node_exe, tmp_path, js):
    f = tmp_path / "pause735.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_pausen_konstanten(index_html, node_exe, tmp_path):
    js = _block(index_html) + _OK + u"""
ok(DISPO_LUNCH_START===720,'Mittagspause Beginn 12:00 (720)');
ok(DISPO_LUNCH_END===780,'Mittagspause Ende 13:00 (780)');
ok(DISPO_FR_END_MIN===690,'Freitag Feierabend 11:30 (690)');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_stopp_kreuzt_pause_ende_plus60(index_html, node_exe, tmp_path):
    """Start 11:30, Dauer 60 -> kreuzt 12:00 -> Pause eingeschoben, Ende 13:30 (810) statt 12:30."""
    js = _block(index_html) + _OK + u"""
var r=_dispoAblauf([{fahrtMin:0,dauerMin:60}],690,10,15,{});
ok(r[0].startMin===690,'Start 11:30 (690)');
ok(r[0].endMin===810,'Ende 13:30 (810) — 60-min-Pause eingeschoben');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_start_in_pause_rutscht_auf_1300(index_html, node_exe, tmp_path):
    """Start faellt auf 12:00 (in der Pause) -> rutscht auf 13:00 (780)."""
    js = _block(index_html) + _OK + u"""
var r=_dispoAblauf([{fahrtMin:0,dauerMin:30}],720,10,15,{});
ok(r[0].startMin===780,'Start rutscht aus der Pause auf 13:00 (780)');
ok(r[0].endMin===810,'Ende 13:30 (810)');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_freitag_keine_pause(index_html, node_exe, tmp_path):
    """Freitag (noLunch): Start 11:30, Dauer 60 -> KEIN Pausen-Einschub (Ende 12:30)."""
    js = _block(index_html) + _OK + u"""
var r=_dispoAblauf([{fahrtMin:0,dauerMin:60}],690,10,15,{noLunch:true});
ok(r[0].startMin===690,'Start 11:30 (690)');
ok(r[0].endMin===750,'Ende 12:30 (750) — Freitag keine Pause');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_vormittag_unberuehrt(index_html, node_exe, tmp_path):
    """Ein Stopp klar vor der Pause bleibt unveraendert (Regression zur v733-Rechnung)."""
    js = _block(index_html) + _OK + u"""
var r=_dispoAblauf([{fahrtMin:0,dauerMin:90}],420,10,15,{});
ok(r[0].startMin===420 && r[0].endMin===510,'07:00-08:30 unveraendert');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_panel_pause_struktur(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    body = index_html[start:end]
    # _zelle uebergibt noLunch je nach Wochentag (Freitag) an _dispoAblauf
    assert "noLunch" in body, "Zelle uebergibt die Freitag-Ausnahme (noLunch) nicht"
    assert 'wtag' in body, "Wochentag (Fr) wird fuer die Pausen-Ausnahme nicht ausgewertet"
