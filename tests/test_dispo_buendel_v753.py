# -*- coding: utf-8 -*-
"""v3.9.753 — Register #30e: Bündel sind ATOMAR — ein Block, eine Anfahrt, eine Entscheidung.

Sebastian (Repro): gebündelte Scheine (gleiche Adresse) müssen als EIN virtueller Chip eingereiht werden —
Summendauer, Partner DIREKT hintereinander in EINER zusammenhängenden Lücke (eine Anfahrt). Findet der Tag
keine Lücke >= Summendauer, wandert das GANZE Bündel auf den nächsten Tag — nie getrennt, nie ein Partner
um 00:00. Reihenfolge im Block: lang -> kurz.

PURER Kern (node-eval): _dispoAblaufBuendel(entries,startMin,pufferMin,taktMin,opts) mit entries[i].buendelKey.
"""
import subprocess


def _block(index_html):
    start = index_html.index("var DISPO_RESERVE_MIN=60;")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    return index_html[start:end]


_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"


def _run(node_exe, tmp_path, js):
    f = tmp_path / "buendel753.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_buendel_zusammen_konsekutiv(index_html, node_exe, tmp_path):
    """Bündel A(3h)+B(1,5h), Tag mit Anker 07:00-11:00 (Lücken 11-12=1h, 13-Ende): das Bündel liegt am Stück
    ab 13:00, Partner direkt hintereinander (lang->kurz), keiner um 00:00."""
    js = _block(index_html) + _OK + u"""
var entries=[{buendelKey:'X',fahrtMin:0,dauerMin:180},{buendelKey:'X',fahrtMin:0,dauerMin:90}];
var anchors=[{startMin:420,endMin:660}]; // 07:00-11:00 belegt
var r=_dispoAblaufBuendel(entries,420,10,15,{anchors:anchors,endMin:1080});
ok(r[0].startMin!=null && r[1].startMin!=null,'beide Partner haben einen Slot (keiner 00:00/null)');
ok(r[0].startMin>=780,'Block startet nach der Pause (>=13:00, denn 4,5h passen nicht in die 1h-Luecke)');
ok(r[1].startMin===r[0].endMin,'Partner B beginnt direkt am Ende von A (eine Anfahrt, konsekutiv)');
ok(r[0].dauerMin===undefined || r[0].endMin-r[0].startMin===180,'A = 3h');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_buendel_reihenfolge_lang_kurz(index_html, node_exe, tmp_path):
    """Innerhalb des Blocks: laengster Schein zuerst."""
    js = _block(index_html) + _OK + u"""
var entries=[{buendelKey:'X',fahrtMin:0,dauerMin:60,id:'kurz'},{buendelKey:'X',fahrtMin:0,dauerMin:180,id:'lang'}];
var r=_dispoAblaufBuendel(entries,420,10,15,{endMin:990});
// r ist in Eingabe-Reihenfolge; der 'lang' (180) muss frueher starten als 'kurz' (60)
ok(r[1].startMin<r[0].startMin,'laenger (lang) startet vor kuerzer (kurz)');
ok(r[0].startMin===r[1].endMin,'kurz direkt nach lang');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_buendel_overflow_beide_null(index_html, node_exe, tmp_path):
    """Passt das Bündel nirgends in den Tag -> BEIDE Partner ohne Slot (null), nie getrennt/00:00."""
    js = _block(index_html) + _OK + u"""
var entries=[{buendelKey:'X',fahrtMin:0,dauerMin:240},{buendelKey:'X',fahrtMin:0,dauerMin:240}];
var r=_dispoAblaufBuendel(entries,420,10,15,{endMin:690}); // Tag endet 11:30, 8h Buendel passt nie
ok(r[0].startMin===null && r[1].startMin===null,'ganzes Buendel overflow (beide null)');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_einzel_wie_ablauf(index_html, node_exe, tmp_path):
    """Einzel-Chips (kein/eigener buendelKey) verhalten sich wie das normale First-Fit."""
    js = _block(index_html) + _OK + u"""
var entries=[{buendelKey:null,fahrtMin:0,dauerMin:90},{buendelKey:null,fahrtMin:5,dauerMin:60}];
var r=_dispoAblaufBuendel(entries,420,10,15,{endMin:990});
ok(r[0].startMin===420 && r[0].endMin===510,'Einzel A 07:00-08:30');
ok(r[1].startMin>=520,'Einzel B danach');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)
