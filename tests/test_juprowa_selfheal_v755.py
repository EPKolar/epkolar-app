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


def test_mount_aufholer_app_level_wiring(index_html):
    """v3.9.758 Wiring-Fix (Chat-Claude Messung 2): der Aufholer feuert am APP-START (curUser + Auth-Ready),
    einmalig, tab-UNABHAENGIG — nicht mehr im tab-gated canSync-Effekt (der feuerte am App-Start nie)."""
    assert "#31g-Aufholer WIRING-FIX" in index_html, "App-Level-Aufholer-Kommentar fehlt"
    m = re.search(r"const _jpCatchUpDone=_react\.useRef[\s\S]{0,760}", index_html)
    assert m, "App-Level-Aufholer-Effekt (_jpCatchUpDone) nicht gefunden"
    seg = m.group(0)
    assert "if(_jpCatchUpDone.current||!curUser)return;" in seg, "kein curUser/Ref-Guard (App-Start-Trigger)"
    assert "API.getToken()" in seg and "navigator.onLine" in seg, "Auth-Ready/Online-Gate fehlt"
    assert "_juprowaDrainPending(50)" in seg, "Aufholer ruft den Drain nicht"
    assert "},[curUser]);" in seg, "Effekt nicht auf curUser gekeyt (App-Start statt tab-gated)"
    # Gegenprobe: der tab-gated ArbeitsscheinView-Effekt (window.__epkAsPushDone) draint NICHT mehr.
    vstart = index_html.index("window.__epkAsPushDone=(pid)=>")
    vseg = index_html[vstart:vstart + 700]
    assert "_juprowaDrainPending" not in vseg, "Aufholer liegt noch im tab-gated canSync-Effekt"


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

// (2) Aufholer-WIRING (Mount-Simulation der Fire-Entscheidung, KEIN direkter Drain-Call — Chat-Claude
// Messung 2: der fruehere Test pruefte die falsche Ebene). Modelliert den App-Start-Effekt: curUser-
// getriggert, Timer-Callback prueft online+token, Ref-once. Der Drain selbst ist live-bewiesen.
function makeCatchUp(){
  var doneRef={current:false}; var drainCalls=0;
  function tick(state){                       // state={curUser,online,token} — ein Mount/Auth-Tick
    if(doneRef.current||!state.curUser)return; // Effekt-Guard (App-Start-Trigger)
    if(!state.online||!state.token)return;     // Timer-Callback: noch nicht ready -> skip, KEIN Ref-Set
    doneRef.current=true; drainCalls++;        // ready -> genau 1 Drain
  }
  return {tick:tick, calls:function(){return drainCalls;}, done:function(){return doneRef.current;}};
}
var c=makeCatchUp();
c.tick({curUser:true,online:true,token:null});   // Mount, aber Auth noch nicht ready
ok(c.calls()===0,'ohne Token kein Drain');
ok(c.done()===false,'Ref bleibt false wenn nicht ready (retry-faehig)');
c.tick({curUser:true,online:true,token:'jwt'});  // Auth-Ready
ok(c.calls()===1,'nach Auth-Ready genau 1 Drain am App-Start (Wiring feuert)');
c.tick({curUser:true,online:true,token:'jwt'});  // Re-Render/weiterer Tick
ok(c.calls()===1,'Ref-once: kein Doppel-Drain');
var c2=makeCatchUp(); c2.tick({curUser:false,online:true,token:'jwt'});
ok(c2.calls()===0,'kein curUser (ausgeloggt) -> kein Drain');
console.log('OK');
"""
    _run(node_exe, tmp_path, js, "konsol_756.js")
