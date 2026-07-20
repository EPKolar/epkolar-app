import pytest
"""v3.9.662 Stempeluhr-Hardening (Bug-Hunt-Subagent) — 3 Edge-Case-Datenkorruptions-Pfade.

#1 Doppel-Scan-Sperre: HID-Wedge/Doppel-Chip kippte die Tagesparitaet (kommen->gehen
   in derselben Minute) -> Schicht zaehlte 0. 12s Cooldown je worker.id.
#2 Uebernacht-Richtung: Gehen nach Mitternacht wurde als neues Kommen erfasst (heutiges
   Event-Fenster leer) -> Schicht 0. Jetzt Frischstart-Guard via letztem Stempel (18h).
#4 WakeLock: vorheriges Sentinel wird vor Neu-Anforderung freigegeben.
"""


def test_lastscan_ref(index_html):
    assert "const _lastScan=_react.useRef.call(void 0, {});" in index_html


@pytest.mark.skip(reason="v3.9.769 Stufe 1 Weg B: der alte Client-INSERT-Scanpfad (Lookup+Read+direkter stempel_log-POST, evCache, SQ.push-Offline-Puffer, Client-Cooldown/Uebernacht/Netto am Panel) ist durch den SECURITY-DEFINER-RPC stempel_terminal_stempel ersetzt. Richtung/Doppel-Scan/Uebernacht leben jetzt im RPC (sql/STEMPEL_TERMINAL_RPC_v3.sql, gepinnt in test_stempel_terminal_rpc_v769), kein-falsches-gruen + Client-Cooldown + unknown-Chip im neuen App-Pfad (ebd.). Dieser Pin testet toten Code.")
def test_cooldown_guard(index_html):
    assert "const _nowMs=Date.now();const _prevScan=_lastScan.current[worker.id];" in index_html
    assert "if(_prevScan&&(_nowMs-_prevScan)<12000){_showFb({kind:'dup',name:worker.name});return;}" in index_html
    assert "_lastScan.current[worker.id]=_nowMs;" in index_html


def test_dup_feedback_case(index_html):
    assert "else if(fb.kind==='dup')" in index_html


@pytest.mark.skip(reason="v3.9.769 Stufe 1 Weg B: der alte Client-INSERT-Scanpfad (Lookup+Read+direkter stempel_log-POST, evCache, SQ.push-Offline-Puffer, Client-Cooldown/Uebernacht/Netto am Panel) ist durch den SECURITY-DEFINER-RPC stempel_terminal_stempel ersetzt. Richtung/Doppel-Scan/Uebernacht leben jetzt im RPC (sql/STEMPEL_TERMINAL_RPC_v3.sql, gepinnt in test_stempel_terminal_rpc_v769), kein-falsches-gruen + Client-Cooldown + unknown-Chip im neuen App-Pfad (ebd.). Dieser Pin testet toten Code.")
def test_overnight_direction_guard(index_html):
    # Heute leer -> letztes Event (desc,limit 1) mit 18h-Fenster entscheidet
    assert "'worker_id=eq.'+encodeURIComponent(worker.id)+'&order=ts.desc&limit=1'" in index_html
    assert "const _openK=_latest&&_latest.direction==='kommen'&&((Date.now()-new Date(_latest.ts).getTime())<18*TIME_HOUR);" in index_html
    assert "dir=_openK?'gehen':'kommen';" in index_html


@pytest.mark.skip(reason="v3.9.769 Stufe 1 Weg B: der alte Client-INSERT-Scanpfad (Lookup+Read+direkter stempel_log-POST, evCache, SQ.push-Offline-Puffer, Client-Cooldown/Uebernacht/Netto am Panel) ist durch den SECURITY-DEFINER-RPC stempel_terminal_stempel ersetzt. Richtung/Doppel-Scan/Uebernacht leben jetzt im RPC (sql/STEMPEL_TERMINAL_RPC_v3.sql, gepinnt in test_stempel_terminal_rpc_v769), kein-falsches-gruen + Client-Cooldown + unknown-Chip im neuen App-Pfad (ebd.). Dieser Pin testet toten Code.")
def test_netto_overnight_note(index_html):
    # Netto nur wenn heutige Events ein Kommen enthalten, sonst Uebernacht-Hinweis
    assert "if(events.some(x=>x.direction==='kommen')){" in index_html
    assert "Übernacht-Schicht — Netto im Büro" in index_html


def test_wakelock_release_before_reacquire(index_html):
    assert "if(lock){try{await lock.release();}catch(_r){}}lock=await navigator.wakeLock.request('screen');" in index_html
