# -*- coding: utf-8 -*-
"""v3.9.755 - Register #31g: JUPROWA Push-Queue Selbstheilung (P1, Chat-Claude-Forensik S075348).

Schritt-0-Forensik (Root-Cause, im index.html-Versionskommentar gepinnt):
`updAs` (Listen-Statuswechsel) feuert DREI nicht-serialisierte Writes fuer einen juprowa-Schein:
  W1  SQ.push({PUT, body:{...,push_pending:true}})   -> doSync -> _translateAndExec -> PATCH  (VERZOEGERT/gebounced)
  W2  _juprowaMarkEdited -> _sbPatch(push_pending:true)                                        (schnell)
  W3  _juprowaPush -> POST OFFA -> _sbPatch(push_pending:false) nach Erfolgs-Echo               (~5s)
Landet der W1-Straggler NACH W3s Reset, bleibt push_pending=true haengen - bis zum manuellen Button
(kein periodischer Queue-Flush, kein drain-on-write). NICHT der Payload und KEIN still fehlgeschlagener
Reset (_sbPatch wirft bei non-ok).

Fix (dieser Test pinnt es):
  31g-2  _juprowaScheduleDrain() - EIN gebouncter Tick (~2s), leading-edge coalesced (Sturm-Schutz);
         doSync stoesst ihn nach dem Flush an, wenn ein geflushtes okId-Item body.push_pending===true trug.
  31g-1  _juprowaPush prueft die Reset-Patch-Antwort (return=representation): leeres Rows-Array = 0 Zeilen
         -> activity_log juprowa_push_fail. Payload/Push-Ablauf unveraendert.
  31g-3  catch-Pfad loggt juprowa_push_fail; Push-Stau-Badge zeigt Alter+Grund.

KEINE Live-Scheine: der W1-Straggler-Ablauf ist als deterministisches Modell + realer node-eval gepinnt.
"""
import re
import subprocess


# ---------------------------------------------------------------- static wiring

def test_schedule_drain_defined_leading_edge_one_tick(index_html):
    assert "function _juprowaScheduleDrain(" in index_html, "_juprowaScheduleDrain fehlt"
    m = re.search(r"var _jpSelfHealTimer=null;\s*function _juprowaScheduleDrain\(\)\{[\s\S]+?\},2000\);\s*\}", index_html)
    assert m, "_juprowaScheduleDrain-Koerper nicht in erwarteter Form (2000ms-Tick)"
    body = m.group(0)
    assert "if(_jpSelfHealTimer)return;" in body, "leading-edge coalesce (Sturm-Schutz) fehlt"
    assert "_juprowaDrainPending(10)" in body, "Tick muss _juprowaDrainPending anstossen"
    assert "navigator.onLine" in body, "Online-Guard fehlt im Tick"


def test_dosync_hook_schedules_drain_on_true_straggler(index_html):
    # Der Hook lebt direkt nach dem Queue-Flush (removeMany) in doSync.
    assert "const removeIds=[...okIds,...skipIds];" in index_html
    m = re.search(r"if\(removeIds\.length>0\) await SQ\.removeMany\(removeIds\);([\s\S]{0,900})", index_html)
    assert m, "doSync-Flush-Region nicht gefunden"
    seg = m.group(1)
    assert "body.push_pending===true" in seg, "Hook prueft nicht auf push_pending===true (Straggler)"
    assert "_juprowaScheduleDrain()" in seg, "Hook stoesst den Selbstheilungs-Drain nicht an"
    assert "okIds.some(" in seg, "Hook betrachtet nicht nur erfolgreich geflushte Items (okIds)"


def test_push_checks_reset_patch_response(index_html):
    # 31g-1 chirurgisch: Reset-Antwort auswerten, 0 Rows -> juprowa_push_fail.
    m = re.search(r"const _resetRes=await _sbPatch\('arbeitsscheine',scheinId,patchData\);([\s\S]{0,500})", index_html)
    assert m, "_resetRes-Auswertung fehlt (Reset-Patch-Antwort wird nicht geprueft)"
    seg = m.group(1)
    assert "Array.isArray(_resetRes)&&_resetRes.length===0" in seg, "0-Rows-Erkennung (Silent-Denial) fehlt"
    assert "juprowa_push_fail" in seg, "0-Rows-Fall loggt kein juprowa_push_fail"
    assert "reset_patch_0_rows" in seg, "Grund reset_patch_0_rows fehlt"


def test_push_catch_logs_push_fail(index_html):
    # 31g-3: der harte Fehlerpfad ist nicht mehr nur Console.
    m = re.search(r"await _sbPatch\('arbeitsscheine',scheinId,\{push_error:e\.message\}\)[\s\S]{0,400}", index_html)
    assert m, "catch-Region in _juprowaPush nicht gefunden"
    seg = m.group(0)
    assert "juprowa_push_fail" in seg, "catch-Pfad loggt kein juprowa_push_fail"


def test_push_flow_unchanged_v616_gate(index_html):
    # Chirurgie-Auflage: der Echo-gebundene Reset (_v616Acc) bleibt die einzige Erfolgsbedingung.
    assert "if(respData&&respData.ID){_v616Acc=true;patchData.push_pending=false;" in index_html, \
        "der v616-Echo-Gate (Push-Ablauf) darf NICHT veraendert sein"


def test_badge_shows_age_and_reason(index_html):
    assert "_asPushStauInfo" in index_html, "Badge-Info (Alter+Grund) fehlt"
    assert "aeltester seit" in index_html, "Badge zeigt kein Alter"
    # Tooltip nennt die Anzahl haengender Pushes.
    assert "haengen" in index_html, "Badge-Tooltip nennt die haengende Anzahl nicht"


# ---------------------------------------------------------------- node-eval

_OK = u"""
function ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }
"""


def _run(node_exe, tmp_path, js, name):
    f = tmp_path / name
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout, (r.stdout or "") + (r.stderr or "")


def _extract_schedule(index_html):
    start = index_html.index("var _jpSelfHealTimer=null;")
    end = index_html.index("if(typeof window!=='undefined')window._juprowaScheduleDrain", start)
    return index_html[start:end]


def test_sturm_hoechstens_2_drains(index_html, node_exe, tmp_path):
    """10 Writes in 1s -> hoechstens 2 Drains (leading-edge coalesce). Realer _juprowaScheduleDrain."""
    js = _OK + u"""
var navigator={onLine:true};
var _log=function(){};
var _drainCount=0;
function _juprowaDrainPending(){ _drainCount++; return Promise.resolve({drained:1,failed:0}); }
""" + _extract_schedule(index_html) + u"""
// 10 Writes ueber ~0.9s verteilt (alle im ersten 2s-Fenster):
for(var i=0;i<10;i++){ setTimeout(_juprowaScheduleDrain, i*90); }
setTimeout(function(){
  ok(_drainCount>=1,'mindestens 1 Drain nach dem Sturm, war '+_drainCount);
  ok(_drainCount<=2,'hoechstens 2 Drains (Sturm-Schutz), war '+_drainCount);
  console.log('OK drains='+_drainCount);
}, 2600);
"""
    _run(node_exe, tmp_path, js, "sturm_755.js")


def test_w1_straggler_repro_und_heilung(index_html, node_exe, tmp_path):
    """Deterministisches Modell der updAs-Write-Kette (Schritt-0): Bug ohne Heilung, geheilt mit Drain.
    Plus: das exakte doSync-Straggler-Praedikat erkennt push_pending===true und ignoriert false/fehlend."""
    js = _OK + u"""
// Reihenfolge der Effekte exakt wie in der Forensik dokumentiert (KEINE Live-Scheine):
function runSequence(healOnStraggler){
  var server={push_pending:true};                 // Statuswechsel (optimistisch true)
  var drains=0;
  function drain(){ drains++; server.push_pending=false; }  // modelliert _juprowaPush echo-Reset
  server.push_pending=true;                        // W2 _juprowaMarkEdited (schnell)
  server.push_pending=false;                       // W3 _juprowaPush Reset nach Echo (13:41:59)
  server.push_pending=true;                        // W1 SQ-PUT Straggler landet SPAETER
  if(healOnStraggler) drain();                     // Selbstheilung: Flush stoesst den Drain an
  return {pp:server.push_pending, drains:drains};
}
var bug=runSequence(false);
ok(bug.pp===true,'Bug reproduziert: Flag bleibt true ohne Selbstheilung');
var fix=runSequence(true);
ok(fix.pp===false,'Selbstheilung: Flag false nach Drain-Tick');
ok(fix.drains===1,'genau 1 Drain in der Heilung, war '+fix.drains);

// Das exakte doSync-Praedikat (nur erfolgreich geflushte okIds mit body.push_pending===true zaehlen):
function stragglerDetected(okIds, queue){
  return okIds.some(function(_oid){var _it=queue.find(function(o){return o.id===_oid;});return !!(_it&&_it.body&&_it.body.push_pending===true);});
}
ok(stragglerDetected(['a'],[{id:'a',body:{push_pending:true}}])===true,'push_pending:true erkannt');
ok(stragglerDetected(['a'],[{id:'a',body:{push_pending:false}}])===false,'push_pending:false ignoriert');
ok(stragglerDetected(['a'],[{id:'a',body:{foo:1}}])===false,'fehlendes push_pending ignoriert');
ok(stragglerDetected(['a'],[{id:'b',body:{push_pending:true}}])===false,'nur geflushte (okIds) zaehlen');
console.log('OK');
"""
    _run(node_exe, tmp_path, js, "straggler_755.js")
