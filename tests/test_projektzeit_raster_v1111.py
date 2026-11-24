# -*- coding: utf-8 -*-
"""Projektzeit-Erfassung nach GF-Entscheidungen 24.11.2026 (ersetzen alle frueheren Fassungen dazu).

- Keine automatische Rundung von Von/Bis (ZEIT_RASTER_MIN=1: _zeitRundVon/_zeitRundBis normalisieren nur das Format).
- Eingabe nur im 15-min-Raster: Von/Bis in Viertelstunden, Stunden in 0,25-Schritten; krumme Werte werden abgelehnt.
- Alte Eintraege bleiben, wie sie sind: unveraenderte Werte eines alten Eintrags gehen beim Speichern durch, gespeicherte
  Stunden bleiben, Bearbeiten erfindet keine Zeiten (vorher 07:00/16:00 -> Speichern rechnete 8 h).
- Keine Vorbelegung: Von/Bis/Stunden/Pause starten leer; fehlende Angaben -> klare Meldung.
- Stunden-Vorschau exakt (Math.round(d*100)/100), nicht mehr auf 0,5.
- Arbeitsschein: Fahrzeit/Arbeitszeit (Minuten) nur in Viertelstunden; unveraenderte alte krumme Werte bleiben.
- Stempeluhr unberuehrt (5-min-Raster, eigene Entscheidung).
"""
import json
import re

from conftest import run_node_snippet, _extract_fn

FNS = ("_zeitParse", "_zeitFmt", "_zeitRundVon", "_zeitRundBis", "_zeitImRaster", "_stdImRaster", "_zeit5",
       "_zeitPflichtFehler", "_zeitEingabeFehler")


def _js(html, ausdruck):
    teile = [re.search(r"const ZEIT_RASTER_MIN=\d+;", html).group(0),
             re.search(r"const ZEIT_EINGABE_RASTER_MIN=\d+;", html).group(0)]
    for n in FNS:
        f = _extract_fn(html, n)
        assert f, n
        teile.append(f)
    return "\n".join(teile) + "\nprocess.stdout.write(JSON.stringify(%s));" % ausdruck


def _ev(node_exe, html, ausdruck):
    return json.loads(run_node_snippet(node_exe, _js(html, ausdruck)))


FAELLE = ("["
          "_zeitEingabeFehler('07:00','16:15',8.75,null),"          # 0 ok
          "_zeitEingabeFehler('07:05','16:00',8.5,null),"           # 1 krumm von
          "_zeitEingabeFehler('07:00','16:10',8.5,null),"           # 2 krumm bis
          "_zeitEingabeFehler('','',7.6,null),"                     # 3 krumme Stunden
          "_zeitEingabeFehler('','',7.75,null),"                    # 4 ok Stunden
          "_zeitEingabeFehler('07:03','15:52',8.32,{von:'07:03:00',bis:'15:52:00',hours:8.32}),"  # 5 alter Eintrag unveraendert
          "_zeitEingabeFehler('07:05','15:52',8.28,{von:'07:03',bis:'15:52',hours:8.32}),"        # 6 alter Eintrag, von geaendert krumm
          "_zeitEingabeFehler('','',7.6,{hours:7.6}),"              # 7 alte krumme Stunden unveraendert
          "_zeitRundVon('07:03'),_zeitRundBis('15:52'),"            # 8,9 keine Rundung
          "_zeitPflichtFehler('','','','',null),"                   # 10 nichts
          "_zeitPflichtFehler('07:00','','','',null),"              # 11 bis fehlt
          "_zeitPflichtFehler('07:00','16:00','','',null),"         # 12 pause fehlt
          "_zeitPflichtFehler('07:00','16:00',0.5,'',null),"        # 13 ok
          "_zeitPflichtFehler('','','','7,5',null),"                # 14 ok stunden
          "_zeitPflichtFehler('07:00','16:00','','',{von:'07:00',bis:'16:00'})"  # 15 alter Eintrag ohne Pause, Zeiten gleich
          "]")


def _pruefe(r):
    f = []
    if r[0] is not None: f.append("Raster-Wert abgelehnt")
    if not (r[1] and "Von" in r[1]): f.append("krummes Von angenommen")
    if not (r[2] and "Bis" in r[2]): f.append("krummes Bis angenommen")
    if not (r[3] and "0,25" in r[3]): f.append("krumme Stunden angenommen")
    if r[4] is not None: f.append("0,25-Stunden abgelehnt")
    if r[5] is not None: f.append("alter krummer Eintrag laesst sich nicht unveraendert speichern")
    if not r[6]: f.append("geaenderter krummer Wert am alten Eintrag angenommen")
    if r[7] is not None: f.append("alte krumme Stunden abgelehnt")
    if r[8] != "07:03" or r[9] != "15:52": f.append("automatische Rundung aktiv")
    if not (r[10] and "Stunden" in r[10]): f.append("leer gespeichert")
    if not (r[11] and "Bis" in r[11]): f.append("Bis fehlt nicht gemeldet")
    if not (r[12] and "Pause" in r[12]): f.append("Pause fehlt nicht gemeldet")
    if r[13] is not None or r[14] is not None: f.append("vollstaendige Angabe abgelehnt")
    if r[15] is not None: f.append("alter Eintrag mit gleichen Zeiten braucht Pause")
    return f


def test_regeln(node_exe, index_html):
    assert _pruefe(_ev(node_exe, index_html, FAELLE)) == []


def test_mutationsproben(node_exe, index_html):
    m1 = index_html.replace("const ZEIT_EINGABE_RASTER_MIN=15;", "const ZEIT_EINGABE_RASTER_MIN=5;", 1)
    assert m1 != index_html and "krummes Von angenommen" in _pruefe(_ev(node_exe, m1, FAELLE))
    m2 = index_html.replace("if(von&&!(o&&_zeit5(o.von)===_zeit5(von))&&!_zeitImRaster(von))", "if(von&&!_zeitImRaster(von))", 1)
    assert m2 != index_html and "alter krummer Eintrag laesst sich nicht unveraendert speichern" in _pruefe(_ev(node_exe, m2, FAELLE))
    m3 = index_html.replace("const ZEIT_RASTER_MIN=1;", "const ZEIT_RASTER_MIN=5;", 1)
    assert m3 != index_html and "automatische Rundung aktiv" in _pruefe(_ev(node_exe, m3, FAELLE))


def test_keine_vorbelegung_und_keine_erfundenen_zeiten(index_html):
    assert 'useState.call(void 0, "07:00")' not in index_html and 'useState.call(void 0, "16:00")' not in index_html
    assert 'setAddVon("07:00")' not in index_html and 'setAddBis("16:00")' not in index_html and "setAddHours(8)" not in index_html
    assert "entry.von||'07:00'" not in index_html and 'entry.von||"07:00"' not in index_html
    assert index_html.count('const [addHours,setAddHours]=_react.useState.call(void 0, "")') == 2
    assert index_html.count("React.createElement('option',{value:\"\"},\"Pause wählen\")") == 2
    assert index_html.count("_zeitPflichtFehler(_rVon,_rBis,addPause,addHours,") == 2


def test_vorschau_exakt_und_alte_stunden_bleiben(index_html):
    assert "setAddHours(d>0?Math.round(d*2)/2:0)" not in index_html
    assert index_html.count("if(_oh>0)_h2=_oh;") == 2


def test_arbeitsschein_minuten_im_raster(index_html):
    assert "Number(v)%ZEIT_EINGABE_RASTER_MIN!==0" in index_html
    assert "if(Number(_asAlt[f[0]]||0)===Number(v||0))return false;" in index_html


def test_stempeluhr_unberuehrt(index_html):
    assert "const STEMPEL_ROUND_MIN=5;" in index_html
    assert "function _stRoundKommen(ts){var ms=STEMPEL_ROUND_MIN*60000;return Math.ceil(ts/ms)*ms;}" in index_html
    assert "function _stRoundGehen(ts){var ms=STEMPEL_ROUND_MIN*60000;return Math.floor(ts/ms)*ms;}" in index_html
