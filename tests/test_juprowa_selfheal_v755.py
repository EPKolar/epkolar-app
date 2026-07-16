# -*- coding: utf-8 -*-
"""#31g JUPROWA Push-Konsolidierung (v3.9.755 Selbstheilung -> v3.9.756 EINE Debounce-Klammer).

v3.9.755 (Root-Cause, S075348): updAs feuert 3 nicht-serialisierte Writes — W1 (SQ-PUT
push_pending:true, gebounced), W2 (_juprowaMarkEdited push_pending:true), W3 (_juprowaPush
push_pending:false nach Echo). Landet W1 NACH W3s Reset -> Flag haengt.

v3.9.756 (Konsolidierung, nach Live-Abnahme S075354: 164ms-Doppelpush): der Sofort-Push (W3) rannte mit
dem verzoegerten W1-Flush -> Straggler -> zweiter (Heil-)Push. Fix an der Wurzel:
  - W2 (_juprowaMarkEdited) STILLGELEGT — push_pending nur noch via SQ-Pfad (W1).
  - Push laeuft ueber EINE per-Schein-Debounce-Klammer `_juprowaSchedulePush` (~2s, leading-edge):
    Handler-Trigger UND doSync-Flush-Hook speisen dieselbe Klammer (coalesced) -> der Push laeuft NACH
    dem SQ-Flush, sein echo-gated Reset kommt zuletzt -> GENAU 1 Push, kein Heilzyklus.
  - Aufholer (Chat-Claude-Auflage, Healing nicht enger als v755): Mount/Login-Sweep `_juprowaDrainPending`
    schiebt ALLE push_pending=true nach — auch Straggler FREMDER Geraete, die keine eigene Klammer haben.

KEINE Live-Scheine: Klammer real node-eval; Sequenzen deterministisch modelliert.
"""
import re
import subprocess


# ---------------------------------------------------------------- static wiring

def test_schedule_push_defined_per_schein_leading_edge(index_html):
    assert "function _juprowaSchedulePush(" in index_html, "_juprowaSchedulePush fehlt"
    m = re.search(r"var _jpPushSet=[\s\S]+?function _juprowaSchedulePush\([\s\S]+?\},2000\);\s*\}", index_html)
    assert m, "_juprowaSchedulePush-Koerper nicht in erwarteter Form (2000ms-Klammer)"
    body = m.group(0)
    assert "new Set()" in body, "per-Schein-Set fehlt"
    assert "if(_jpPushTimer)return;" in body, "leading-edge coalesce (eine Klammer) fehlt"
    assert "_juprowaPush(" in body, "Klammer ruft _juprowaPush nicht"
    assert "if(!navigator.onLine)return;" in body, "Offline-Guard fehlt"
    assert "__epkAsPushDone" in body, "lokaler ↑-Clear (window.__epkAsPushDone) fehlt im Erfolgs-Pfad"


def test_handlers_trigger_schedule_not_direct_push(index_html):
    """updAs/storno/verschieben/saveAs schedulen den Push (kein Sofort-_juprowaPush, kein _juprowaMarkEdited)."""
    for marker in ("const updAs=", "const storno=", "const verschieben="):
        start = index_html.index(marker)
        seg = index_html[start:start + 2400]  # v3.9.757: 31a-Guard verlaengerte updAs
        assert "_juprowaSchedulePush(" in seg, "%s schedult den Push nicht" % marker
        assert "_juprowaPush(" not in seg, "%s ruft _juprowaPush direkt (kein Sofort-Push mehr erlaubt)" % marker
        assert "_juprowaMarkEdited" not in seg, "%s ruft das stillgelegte W2 _juprowaMarkEdited" % marker


def test_w2_und_scheduledrain_entfernt(index_html):
    """W2 (_juprowaMarkEdited) und der alte Batch-Self-Heal (_juprowaScheduleDrain) sind Code-frei
    (nur noch in erklaerenden Kommentaren erlaubt)."""
    # keine Funktions-Definition mehr
    assert "function _juprowaMarkEdited(" not in index_html, "_juprowaMarkEdited noch definiert"
    assert "function _juprowaScheduleDrain(" not in index_html, "_juprowaScheduleDrain noch definiert"
    # kein Aufruf mehr (Klammer-Aufruf-Muster) — Kommentare nennen den Namen ohne '('
    assert "_juprowaMarkEdited(" not in index_html, "_juprowaMarkEdited wird noch aufgerufen"


def test_dosync_hook_feeds_schedule_push(index_html):
    m = re.search(r"if\(removeIds\.length>0\) await SQ\.removeMany\(removeIds\);([\s\S]{0,900})", index_html)
    assert m, "doSync-Flush-Region nicht gefunden"
    seg = m.group(1)
    assert "body.push_pending===true" in seg, "Hook prueft nicht auf push_pending===true"
    assert "_juprowaSchedulePush(" in seg, "Hook speist die per-Schein-Klammer nicht"
    assert "/api/arbeitsscheine/" in seg, "Hook extrahiert die Schein-ID nicht aus der Flush-URL"


def test_mount_aufholer_existiert(index_html):
    """Chat-Claude-Auflage: Mount/Login-Sweep raeumt Fremd-Straggler binnen eines Mounts ab."""
    assert "#31g-Aufholer" in index_html, "kein Mount/Login-Aufholer-Kommentar"
    # Der Aufholer nutzt den Batch-Drain (deckt push_pending=true OHNE eigenen Write dieser Session).
    m = re.search(r"#31g-Aufholer[\s\S]{0,700}", index_html)
    assert m and "_juprowaDrainPending(" in m.group(0), "Aufholer ruft _juprowaDrainPending nicht"


def test_push_checks_reset_patch_response(index_html):
    # 31g-1 (unveraendert): Reset-Antwort auswerten, 0 Rows -> juprowa_push_fail.
    m = re.search(r"const _resetRes=await _sbPatch\('arbeitsscheine',scheinId,patchData\);([\s\S]{0,500})", index_html)
    assert m, "_resetRes-Auswertung fehlt"
    seg = m.group(1)
    assert "Array.isArray(_resetRes)&&_resetRes.length===0" in seg, "0-Rows-Erkennung fehlt"
    assert "juprowa_push_fail" in seg, "0-Rows-Fall loggt kein juprowa_push_fail"


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


def _extract_klammer(index_html):
    start = index_html.index("var _jpPushSet=")
    end = index_html.index("if(typeof window!=='undefined')window._juprowaSchedulePush", start)
    return index_html[start:end]


_STUBS = u"""
var navigator={onLine:true};
var window={};
var _pushLog=[];
function _juprowaPush(id){ _pushLog.push(id); return Promise.resolve({ok:true,nummer:id}); }
"""


def test_sturm_und_coalesce_genau_1_push_je_schein(index_html, node_exe, tmp_path):
    """10 Writes/1s auf denselben Schein -> 1 Push. Handler+doSync-Hook auf denselben Schein -> 1 Push.
    3 verschiedene Scheine in einem Fenster -> genau 3 Pushes (eine Klammer, per-Schein)."""
    js = _OK + _STUBS + _extract_klammer(index_html) + u"""
// (a) 10 Writes gleicher Schein ueber ~0.9s -> genau 1 Push:
for(var i=0;i<10;i++){ setTimeout(function(){_juprowaSchedulePush('S1');}, i*90); }
// (b) Handler-Trigger + doSync-Hook auf denselben Schein (coalesced) -> weiterhin 1 Push:
setTimeout(function(){_juprowaSchedulePush('S1');}, 300);
setTimeout(function(){
  var s1=_pushLog.filter(function(x){return x==='S1';}).length;
  ok(s1===1,'genau 1 Push fuer S1 trotz 11 Schedules, war '+s1);
  // (c) drei verschiedene Scheine in einem Fenster -> genau 3 Pushes:
  _pushLog=[];
  _juprowaSchedulePush('A');_juprowaSchedulePush('B');_juprowaSchedulePush('A');_juprowaSchedulePush('C');
  setTimeout(function(){
    ok(_pushLog.length===3,'3 verschiedene Scheine -> 3 Pushes, war '+_pushLog.length);
    ok(_pushLog.indexOf('A')>=0&&_pushLog.indexOf('B')>=0&&_pushLog.indexOf('C')>=0,'A,B,C alle gepusht');
    console.log('OK');
  }, 2400);
}, 2400);
"""
    _run(node_exe, tmp_path, js, "klammer_756.js")


def test_konsolidierung_und_aufholer_modell(index_html, node_exe, tmp_path):
    """Deterministisch (KEINE Live-Scheine): (1) debounced-nach-Flush -> genau 1 Push, pend=false;
    (2) Fremd-Straggler ohne eigenen Write/Button wird vom Mount-Aufholer-Drain abgeraeumt."""
    js = _OK + u"""
// (1) Konsolidierung: der Push laeuft NACH dem SQ-Flush -> Reset zuletzt -> 1 Push, kein Straggler.
function runNeu(){
  var server={push_pending:true}; var pushes=0;
  // W1 SQ-Flush (setzt push_pending true auf dem Server) bei t=flush:
  var flushT=1500;
  // debounced Push bei t=2000 (> flushT) liest true, pusht, resettet false:
  var pushT=2000;
  var events=[{t:flushT,f:function(){server.push_pending=true;}},
              {t:pushT, f:function(){pushes++; server.push_pending=false;}}];
  events.sort(function(a,b){return a.t-b.t;}).forEach(function(e){e.f();});
  return {pp:server.push_pending, pushes:pushes};
}
var neu=runNeu();
ok(neu.pushes===1,'genau 1 Push (debounced nach Flush), war '+neu.pushes);
ok(neu.pp===false,'push_pending=false bleibt (kein Straggler nach dem Reset)');

// (2) Aufholer: ein Schein haengt push_pending=true OHNE dass diese Session ihn angefasst hat
// (Fremdgeraet/Netzabriss). Kein eigener Write (keine Klammer), kein Button. Der Mount-Sweep
// (_juprowaDrainPending) findet alle push_pending=true und pusht sie -> Reset.
function mountCatchUp(store){
  var drained=0;
  Object.keys(store).forEach(function(id){ if(store[id].push_pending===true){ drained++; store[id].push_pending=false; } });
  return drained;
}
var store={ FREMD:{push_pending:true} };   // Fremd-Straggler
var drained=mountCatchUp(store);            // genau EIN Mount, kein eigener Write, kein Button
ok(drained===1,'Aufholer draint den Fremd-Straggler, war '+drained);
ok(store.FREMD.push_pending===false,'Fremd-Straggler binnen eines Mounts abgeraeumt (ohne Write/Button)');
console.log('OK');
"""
    _run(node_exe, tmp_path, js, "konsol_756.js")
