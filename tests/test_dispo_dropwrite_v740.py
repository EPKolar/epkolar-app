# -*- coding: utf-8 -*-
"""v3.9.740 — Register #22a: EIN Schreibgesetz fuer die Dispo (Drop schreibt, harte Waende gelten der Hand).

Sebastian: jede Termin-Aenderung per Geste (Vorschlags-Chip ziehen, fixen Chip ziehen) schreibt DIESELBEN
Felder ueber DENSELBEN Pfad wie ✓ Uebernehmen: updAs(id,{terminBestaetigt,terminZeit,dauer}). Harte Waende
gelten auch fuer die Hand: Drop ueber Tagesnorm, auf Urlaub/Krank/🚫/vergangen oder in die Mittagspause ->
rot, KEIN Write. Nur der angefasste Chip schreibt (Kaskaden-Push-Verbot: 1 Geste = max 1 Write = 1 Push).

PURER Kern (node-eval): _dispoDropOk(dragMid,cellMid,hardBlock,restMin,dauerMin) -> bool (darf geschrieben
werden?). Die Geste + der updAs-Write + das Kaskaden-Verbot sind struktur-gepinnt.
"""
import subprocess


def _block(index_html):
    start = index_html.index("var DISPO_RESERVE_MIN=60;")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    return index_html[start:end]


_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"


def _run(node_exe, tmp_path, js):
    f = tmp_path / "dropwrite740.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_dropok_fremde_zeile(index_html, node_exe, tmp_path):
    js = _block(index_html) + _OK + u"""
ok(_dispoDropOk('M1','M2',false,999,60)===false,'fremde Monteur-Zeile -> kein Write');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_dropok_hardblock(index_html, node_exe, tmp_path):
    js = _block(index_html) + _OK + u"""
ok(_dispoDropOk('M1','M1',true,999,60)===false,'harte Wand (Urlaub/Krank/gesperrt/vergangen/Pause) -> kein Write');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_dropok_ueber_norm(index_html, node_exe, tmp_path):
    js = _block(index_html) + _OK + u"""
ok(_dispoDropOk('M1','M1',false,60,120)===false,'ueber Tagesnorm (Dauer+Puffer > Rest) -> kein Write');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_dropok_passt(index_html, node_exe, tmp_path):
    js = _block(index_html) + _OK + u"""
ok(_dispoDropOk('M1','M1',false,200,120)===true,'eigene Zeile, frei, passt -> Write erlaubt');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_panel_dropwrite_struktur(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    body = index_html[start:end]
    # Drop nutzt den Write-Guard; beide Chip-Arten schreiben ueber onDrop (ein Schreibweg)
    assert "_dispoDropOk" in body, "Drop prueft die harte Wand nicht (_dispoDropOk)"
    assert "onDrop" in body, "kein einheitlicher Schreibweg onDrop"
    # Zelle exponiert die echte Kapazitaet + Hardblock fuer die Hand-Wand
    assert "data-hardblock" in body, "Zelle exponiert den Hardblock-Status nicht"


def test_callsite_ondrop_ist_updAs_drei_felder(index_html):
    i = index_html.index("onDrop:")
    seg = index_html[i:i + 600]
    assert "updAs(" in seg, "onDrop schreibt nicht via updAs"
    assert "terminBestaetigt" in seg and "terminZeit" in seg and "dauer" in seg, "onDrop schreibt nicht alle 3 Felder"
    assert "SQ.push" not in seg, "onDrop darf keinen eigenen SQ.push-Sonderpfad haben"
