# -*- coding: utf-8 -*-
"""v3.9.733 — Register #20: Dispo vergibt Startzeiten (15-min-Taktung, Arbeitsbeginn 07:00).

Sebastian (16.07., live): "dispo vergibt noch keine startzeit ... fix das mit der taktung." Taktung = 15 min
(bestaetigt korrigiert, gleiches Raster wie der Dauer-Griff 16b -> DISPO_ZEITRASTER_MIN). Arbeitszeit:
Beginn 07:00, Norm Mo-Do 510 / Fr 270 min. Jeder Vorschlags-Chip bekommt ein Zeitfenster "07:00-08:30":
ab 07:00 (Firma), kumulativ Fahrzeit (_dispoStrecke().min, nie 0) + Dauer + Puffer je Stopp; der START
wird auf die 15-min-Taktung gerundet (verankert an 07:00, nearest). Uebernahme schreibt die Startzeit als
terminZeit (DB termin_zeit, genau was MonteurTafel v536 liest); kein eigener Push-Key — reitet ueber
terminBestaetigt->AK_TERMIN mit.

PURER Kern (node-eval): _dispoAblauf(items, startMin, pufferMin, taktMin) -> je Item {startMin,endMin}.
Die Mini-Timeline/Chip-Labels/Uebernahme-Startzeit sind struktur-gepinnt.
"""
import subprocess


def _block(index_html):
    start = index_html.index("var DISPO_RESERVE_MIN=60;")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    return index_html[start:end]


_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"


def _run(node_exe, tmp_path, js):
    f = tmp_path / "d20_733.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_arbeitszeit_konstanten(index_html, node_exe, tmp_path):
    js = _block(index_html) + _OK + u"""
ok(DISPO_ZEITRASTER_MIN===15,'Taktung 15 min (Sebastian, korrigiert)');
ok(DISPO_TAG_START_MIN===420,'Arbeitsbeginn 420 min = 07:00');
ok(DISPO_TAG_START==='07:00','Arbeitsbeginn-Label 07:00');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_ablauf_erster_stopp_startet_0700(index_html, node_exe, tmp_path):
    """Erster Stopp ohne Fahrzeit startet 07:00 (420) und endet base+Dauer."""
    js = _block(index_html) + _OK + u"""
var r=_dispoAblauf([{fahrtMin:0,dauerMin:90}],DISPO_TAG_START_MIN,10,DISPO_ZEITRASTER_MIN);
ok(r.length===1,'ein Fenster');
ok(r[0].startMin===420,'Start 07:00 (420)');
ok(r[0].endMin===510,'Ende 08:30 (510)');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_ablauf_kumuliert_mit_fahrt_und_puffer(index_html, node_exe, tmp_path):
    """Zweiter Stopp = erstes Ende + Puffer + Fahrzeit, Start auf 15-min gerundet (Anker 07:00)."""
    js = _block(index_html) + _OK + u"""
var r=_dispoAblauf([{fahrtMin:0,dauerMin:90},{fahrtMin:5,dauerMin:60}],DISPO_TAG_START_MIN,10,DISPO_ZEITRASTER_MIN);
/* Stopp1: 420..510, cursor=510+10=520; Stopp2: 520+5=525, rel=105 -> round(105/15)=7 -> 105 -> 525; 525..585 */
ok(r[1].startMin===525,'Stopp2 Start 08:45 (525)');
ok(r[1].endMin===585,'Stopp2 Ende 09:45 (585)');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_ablauf_snap_naechste_taktung(index_html, node_exe, tmp_path):
    """v3.9.749 #27: Start wird auf die naechste 15-min-Taktung AUFGERUNDET (ceil, Start nie vor Ankunft)."""
    js = _block(index_html) + _OK + u"""
ok(_dispoAblauf([{fahrtMin:0,dauerMin:30}],DISPO_TAG_START_MIN,0,15)[0].startMin===420,'0 min Fahrt -> 07:00 exakt');
ok(_dispoAblauf([{fahrtMin:1,dauerMin:30}],DISPO_TAG_START_MIN,0,15)[0].startMin===435,'1 min Fahrt -> ceil auf 07:15');
ok(_dispoAblauf([{fahrtMin:15,dauerMin:30}],DISPO_TAG_START_MIN,0,15)[0].startMin===435,'15 min Fahrt -> 07:15 exakt');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_panel_startzeit_struktur(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    body = index_html[start:end]
    # Chip-Zeitfenster aus _dispoAblauf, Fahrzeit ueber _dispoStrecke, Uebernahme schreibt die Startzeit
    assert "_dispoAblauf" in body, "Chips bekommen keine Ablauf-/Startzeiten"
    assert "_dispoStrecke" in body, "Fahrzeit-Kette (Firma->Stopps) fehlt fuer die Startzeit"


def test_uebernahme_schreibt_startzeit(index_html):
    # onUebernehmen-Callsite in ArbeitsscheinView schreibt terminZeit (DB termin_zeit) via updAs.
    i = index_html.index("onUebernehmen: (scheinId,monteurId,iso")
    seg = index_html[i:i + 400]
    assert "terminZeit" in seg, "Uebernahme schreibt keine Startzeit (terminZeit) via updAs"
