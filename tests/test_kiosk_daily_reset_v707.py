# -*- coding: utf-8 -*-
"""v3.9.707 — Kiosk taeglicher Hard-Reset um 03:00 Wiener Zeit.

Jedes stille Kiosk-Panel heilt sich einmal/Tag selbst (SW+Caches loeschen + Reload) im
bestehenden v705-Poll-Takt. Einmal-pro-Tag-Marker; Erst-Lauf ohne Sofort-Reload; DST-sicher.

Die PURE Ableitung _kioskDailyShouldReset(datum,stunde,marker) wird per Node WIRKLICH ausgefuehrt.
"""
import re
import subprocess


def test_reset_hour_constant_and_vienna_tz(index_html):
    assert "var KIOSK_DAILY_RESET_HOUR=3;" in index_html          # nicht magisch inline
    # Wiener Zeit ZWINGEND via Intl/Europe/Vienna (DST-sicher, kein getHours/UTC-Offset)
    assert "function _kioskWienNow()" in index_html
    assert "timeZone:'Europe/Vienna'" in index_html
    m = re.search(r"function _kioskWienNow\(.*?\n\}", index_html, re.S)
    assert m and "getHours(" not in m.group(0), "Wiener Stunde darf nicht via getHours()"


def test_scope_gate_silent_panels_only(index_html):
    assert "function _kioskIsSilentPanel()" in index_html
    seg = index_html.split("function _kioskIsSilentPanel()", 1)[1][:400]
    assert "lager_display" in seg and "stempel_terminal" in seg


def test_daily_tick_first_run_and_marker_before_reload(index_html):
    seg = index_html.split("function _kioskDailyTick()", 1)[1][:900]
    assert "if(!_kioskIsSilentPanel())return;" in seg              # Scope-Gate
    # Erst-Lauf: leerer Marker -> nur setzen, KEIN Reload
    assert "if(!marker){" in seg and "return;" in seg
    # Marker VOR dem Reload setzen, dann Guard mit eigenem Key 'daily-'
    assert "_kioskReloadGuard('daily-'+w.datum)" in seg
    assert "window._forceCacheClear(true)" in seg
    # Reihenfolge: setItem(marker) steht vor _forceCacheClear
    assert seg.index("localStorage.setItem('epk_kiosk_daily_reset',w.datum)") < seg.index("_forceCacheClear(true)")


def test_wired_into_existing_poller_no_new_timer(index_html):
    # Aufruf im bestehenden v705-Poller-_check (kein neuer setInterval fuer den Daily-Reset)
    assert "if(typeof _kioskDailyTick==='function')_kioskDailyTick();" in index_html
    assert "window._kioskDailyShouldReset=_kioskDailyShouldReset;" in index_html


def test_should_reset_behavior_executed(index_html, node_exe, tmp_path):
    m = re.search(r"function _kioskDailyShouldReset\(.*?\n\}", index_html, re.S)
    assert m, "_kioskDailyShouldReset nicht gefunden"
    # KIOSK_DAILY_RESET_HOUR muss fuer die pure Fn im Scope sein
    js = "var KIOSK_DAILY_RESET_HOUR=3;\n" + m.group(0) + u"""
function eq(g,e,n){ if(g!==e){ console.error('FAIL '+n+': '+g+' != '+e); process.exit(1);} }
eq(_kioskDailyShouldReset('2026-07-15',2,'2026-07-14'), false, '02:59 vor Reset');
eq(_kioskDailyShouldReset('2026-07-15',3,'2026-07-14'), true,  '03:00 neuer Tag');
eq(_kioskDailyShouldReset('2026-07-15',4,'2026-07-14'), true,  '04:00 neuer Tag');
eq(_kioskDailyShouldReset('2026-07-15',3,'2026-07-15'), false, '03:00 Marker=heute');
eq(_kioskDailyShouldReset('2026-07-15',14,''),          false, '14:00 ohne Marker (Erst-Lauf)');
eq(_kioskDailyShouldReset('2026-07-15',14,'2026-07-15'),false, '14:00 heute schon');
eq(_kioskDailyShouldReset('',3,'2026-07-14'),           false, 'Zeit-Ableitung fehlgeschlagen');
// DST-Umstellung (29.03.2026 spring-forward): genau EIN Reset
eq(_kioskDailyShouldReset('2026-03-29',3,'2026-03-28'), true,  'DST-Tag erster Reset');
eq(_kioskDailyShouldReset('2026-03-29',3,'2026-03-29'), false, 'DST-Tag kein Doppel');
console.log('OK');
"""
    f = tmp_path / "daily.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout
