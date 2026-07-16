# -*- coding: utf-8 -*-
"""v3.9.747 — Register #1 (P1-e Teil 2): blockierbare Tage in der Dispo.

Sebastian: Buero/PL/Admin kann einen Monteur-Tag sperren (dispo_blocks) -> der Tag zaehlt in der Vorschlags-
planung als Kapazitaet 0 (harte Wand) + Grund-Chip 🚫. _dispoBuildInput nimmt eine blocksMap (Key
worker_id_ISO -> grund) und blockiert die betroffenen Tage. Client liest die Sperren 42P01-tolerant
(Tabelle fehlt -> keine Sperren, Dispo laeuft unveraendert).
"""
import subprocess


def _block(index_html):
    start = index_html.index("var DISPO_RESERVE_MIN=60;")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    return index_html[start:end]


_ISOW = (u"var AS_GRP_OFFEN=['aufgenommen','freigegeben','in_bearbeitung','aufgeschoben'];\n"
         u"const isoWof=(dd)=>{const d=new Date(dd);d.setHours(0,0,0,0);d.setDate(d.getDate()+3-(d.getDay()+6)%7);const w=new Date(d.getFullYear(),0,4);return 1+Math.round(((d-w)/864e5-3+(w.getDay()+6)%7)/7);};\n"
         u"const isoWYof=(dd)=>{const d=new Date(dd);d.setHours(0,0,0,0);d.setDate(d.getDate()+3-(d.getDay()+6)%7);return d.getFullYear();};\n")
_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"


def _run(node_exe, tmp_path, js):
    f = tmp_path / "blocks747.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_gesperrter_tag_kap_0(index_html, node_exe, tmp_path):
    """Ein gesperrter Monteur-Tag: Kapazitaets-Abzug = volle Norm (Kap 0) + Grund-Chip 🚫."""
    js = _ISOW + _block(index_html) + _OK + u"""
var mon=[{id:'m1',n:'Anton',r:'Monteur'}];
var now=new Date('2026-07-16T00:00:00');
var base=_dispoBuildInput([],mon,{},{},now,3);
var iso=base.wochen[1].tage[0].iso; // Folgewoche-Montag (Zukunft)
var blocks={}; blocks['m1_'+iso]='Schulung';
var out=_dispoBuildInput([],mon,{},{},now,3,undefined,undefined,blocks);
ok(out.cfg.kapAbzug['m1'][iso]>=510-60,'gesperrter Tag hat Kap ~0 (Abzug ~volle Norm): '+out.cfg.kapAbzug['m1'][iso]);
var g=out.blockGrund['m1'][iso];
ok(g && g[0].icon==='🚫','Grund-Chip 🚫 gesetzt');
ok(g && /Schulung/.test(g[0].label),'Grund-Text (Schulung) im Chip');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_ohne_blocksmap_unveraendert(index_html, node_exe, tmp_path):
    """Ohne blocksMap (Tabelle fehlt / 42P01) laeuft die Dispo unveraendert — kein 🚫."""
    js = _ISOW + _block(index_html) + _OK + u"""
var mon=[{id:'m1',n:'Anton',r:'Monteur'}];
var now=new Date('2026-07-16T00:00:00');
var out=_dispoBuildInput([],mon,{},{},now,3);
var iso=out.wochen[1].tage[0].iso;
ok(!out.blockGrund['m1'][iso],'ohne Sperren kein Block-Grund');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_signatur_und_load_client(index_html):
    # _dispoBuildInput nimmt blocksMap als letzten Parameter; Client laedt dispo_blocks 42P01-tolerant.
    assert "function _dispoBuildInput(scheine,monteure,wpHistory,absMap,now,horizontWochen,geoMap,distMatrix,blocksMap)" in index_html
    assert "dispo_blocks" in index_html, "Client laedt die Sperren-Tabelle nicht"
